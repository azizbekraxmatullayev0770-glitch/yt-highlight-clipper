# -*- coding: utf-8 -*-
"""
YouTube Highlight Clipper
==========================
YouTube linkini oladi -> videoni yuklaydi -> transkript qiladi (Whisper)
-> Claude AI orqali eng qiziqarli 10-20 soniyalik joyni topadi
-> ffmpeg bilan o'sha joyni kesib, vertikal (9:16) formatga o'tkazadi
-> pastki qismiga so'zma-so'z subtitr (captions) yopishtiradi (zamonaviy reels/shorts uslubi)

ISHGA TUSHIRISH (README.md ga qarang):
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="sk-ant-..."
    python app.py
    -> brauzerda http://localhost:5000 ni oching
"""

import os
import re
import json
import uuid
import subprocess
import traceback

from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, "work")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 1-QADAM: YouTube videoni yuklab olish (yt-dlp orqali)
# ---------------------------------------------------------------------------
def download_video(youtube_url: str, job_id: str) -> str:
    out_path = os.path.join(WORK_DIR, f"{job_id}.mp4")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", out_path,
        youtube_url,
    ]
    subprocess.run(cmd, check=True)
    return out_path


# ---------------------------------------------------------------------------
# 2-QADAM: Audio -> matn (so'z darajasidagi vaqt belgilari bilan) - Whisper
# ---------------------------------------------------------------------------
def transcribe_video(video_path: str):
    """
    faster-whisper yordamida transkript qilamiz.
    Har bir segment: {"start": sek, "end": sek, "text": "..."}
    """
    from faster_whisper import WhisperModel

    model_size = os.environ.get("WHISPER_MODEL", "small")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, _info = model.transcribe(video_path, word_timestamps=False)
    result = []
    for seg in segments:
        result.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
    return result


# ---------------------------------------------------------------------------
# 3-QADAM: Claude AI orqali eng qiziqarli lahzani topish
# ---------------------------------------------------------------------------
def find_best_highlight(segments, clip_len_hint=15):
    """
    Transkriptni Claude'ga yuboramiz va eng "viral" bo'lishga loyiq
    10-20 soniyalik oraliqni so'raymiz. Javob JSON: {start, end, reason, title}
    """
    import anthropic

    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY env orqali olinadi

    # Transkriptni vaqt belgilari bilan matn ko'rinishiga o'tkazamiz
    lines = []
    for s in segments:
        lines.append(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}")
    transcript_text = "\n".join(lines)

    # Juda uzun bo'lsa (masalan 6 soatlik strim), bo'laklarga bo'lib,
    # avval har bir bo'lakdan nomzod topamiz, keyin eng zo'rini tanlaymiz.
    CHUNK_CHAR_LIMIT = 12000
    chunks = []
    cur = []
    cur_len = 0
    for line in lines:
        cur.append(line)
        cur_len += len(line)
        if cur_len > CHUNK_CHAR_LIMIT:
            chunks.append("\n".join(cur))
            cur, cur_len = [], 0
    if cur:
        chunks.append("\n".join(cur))

    candidates = []
    system_prompt = (
        "Sen video-kontent muharrirsan. Senga vaqt belgilari bilan video transkripti "
        "beriladi. Vazifang: shu qismdan eng qiziqarli, kulgili, hissiyotli, "
        "shov-shuvli yoki 'aha!' effektiga ega bo'lgan, ijtimoiy tarmoqlarda (Reels/"
        "Shorts/TikTok) viral bo'lishga eng loyiq bitta lahzani topish. "
        f"Tanlangan oraliq {clip_len_hint} soniyaga yaqin (10-20 soniya) bo'lishi kerak "
        "va mustaqil holda tushunarli bo'lishi, ya'ni boshida va oxirida gap bo'linib "
        "qolmasligi kerak. Faqat quyidagi JSON formatida javob ber, boshqa hech narsa yozma:\n"
        '{"start": <soniya>, "end": <soniya>, "score": <1-10>, "title": "<qisqa sarlavha>", '
        '"reason": "<nega qiziqarli, 1 gap>"}'
    )

    for i, chunk in enumerate(chunks):
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": chunk}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            continue
        try:
            data = json.loads(m.group(0))
            candidates.append(data)
        except json.JSONDecodeError:
            continue

    if not candidates:
        raise RuntimeError("AI hech qanday qiziqarli joy topa olmadi.")

    best = max(candidates, key=lambda c: c.get("score", 0))
    return best


# ---------------------------------------------------------------------------
# 4-QADAM: ffmpeg bilan kesish + vertikal format + subtitr (zamonaviy montaj)
# ---------------------------------------------------------------------------
def build_srt(segments, clip_start, clip_end, srt_path):
    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

    idx = 1
    with open(srt_path, "w", encoding="utf-8") as f:
        for seg in segments:
            if seg["end"] < clip_start or seg["start"] > clip_end:
                continue
            start = max(seg["start"], clip_start) - clip_start
            end = min(seg["end"], clip_end) - clip_start
            if end <= start:
                continue
            f.write(f"{idx}\n{fmt(start)} --> {fmt(end)}\n{seg['text'].strip()}\n\n")
            idx += 1


def cut_and_edit(video_path, segments, highlight, job_id):
    start = float(highlight["start"])
    end = float(highlight["end"])
    duration = max(1.0, end - start)

    srt_path = os.path.join(WORK_DIR, f"{job_id}.srt")
    build_srt(segments, start, end, srt_path)

    out_path = os.path.join(OUTPUT_DIR, f"{job_id}_highlight.mp4")

    # Vertikal (9:16) formatga o'tkazish: markazdan crop qilib, keyin
    # blur qilingan fon ustiga joylashtiramiz - zamonaviy Reels ko'rinishi.
    vf = (
        "split[bg][fg];"
        "[bg]scale=1080:1920,boxblur=20:1,setsar=1[bgblur];"
        "[fg]scale=1080:-1,setsar=1[fgscaled];"
        "[bgblur][fgscaled]overlay=(W-w)/2:(H-h)/2,"
        f"subtitles='{srt_path}':force_style='FontName=Arial,FontSize=16,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,"
        "Outline=2,Alignment=2,MarginV=80'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", video_path, "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process():
    data = request.get_json(force=True)
    youtube_url = data.get("url", "").strip()
    clip_len = int(data.get("clip_len", 15))

    if not youtube_url:
        return jsonify({"error": "YouTube link kiritilmadi."}), 400

    job_id = uuid.uuid4().hex[:10]
    try:
        video_path = download_video(youtube_url, job_id)
        segments = transcribe_video(video_path)
        highlight = find_best_highlight(segments, clip_len_hint=clip_len)
        out_path = cut_and_edit(video_path, segments, highlight, job_id)

        return jsonify({
            "job_id": job_id,
            "title": highlight.get("title"),
            "reason": highlight.get("reason"),
            "score": highlight.get("score"),
            "start": highlight.get("start"),
            "end": highlight.get("end"),
            "download_url": f"/download/{job_id}_highlight.mp4",
        })
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Video yuklash/kesishda xatolik: {e}"}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
