# YouTube Highlight Clipper

YouTube link (jumladan uzun strimlar, 1-6 soat) beriladi → dastur:
1. Videoni yuklab oladi (`yt-dlp`)
2. Ovozni matnga o'giradi, vaqt belgilari bilan (`faster-whisper`)
3. Matnni Claude AI'ga yuborib, eng qiziqarli 10-20 soniyalik joyni topadi
4. `ffmpeg` bilan o'sha joyni kesib, **vertikal (9:16) format + subtitr** bilan
   zamonaviy Reels/Shorts ko'rinishida chiqaradi

## 1. Talab qilinadigan dasturlar

- Python 3.10+
- `ffmpeg` (kompyuteringizda o'rnatilgan bo'lishi kerak)
  - Windows: https://ffmpeg.org/download.html dan yuklab, PATH ga qo'shing
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- Anthropic API kaliti (https://console.anthropic.com dan olinadi)

## 2. O'rnatish

```bash
cd yt_highlight_clipper
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. API kalitni sozlash

```bash
export ANTHROPIC_API_KEY="sk-ant-..."      # Mac/Linux
set ANTHROPIC_API_KEY=sk-ant-...           # Windows (cmd)
```

## 4. Ishga tushirish

```bash
python app.py
```

Brauzerda oching: **http://localhost:5000**

Havolani kiriting, kesim uzunligini tanlang (10/15/20 soniya) va tugmani bosing.
Video qancha uzun bo'lsa, transkript va tahlil shuncha ko'proq vaqt oladi
(6 soatlik strim — kompyuter quvvatiga qarab 15-40 daqiqa cho'zilishi mumkin).

## 5. Sozlash imkoniyatlari

- `WHISPER_MODEL` muhit o'zgaruvchisi orqali Whisper modeli hajmini
  o'zgartirish mumkin: `tiny`, `base`, `small` (standart), `medium`, `large-v3`.
  Kattaroq model — aniqroq, lekin sekinroq.
- `app.py` ichidagi `cut_and_edit()` funksiyasida subtitr shrifti, rangi,
  fon effekti (blur/qora fon) kabi narsalarni o'zgartirishingiz mumkin.

## 6. Muhim eslatmalar

- Faqat o'zingizga tegishli yoki foydalanish huquqiga ega bo'lgan videolar
  bilan ishlating — mualliflik huquqi qoidalariga rioya qiling.
- Juda uzun (soatlab) videolarni yuklab olish diskda ko'p joy talab qilishi
  mumkin; `work/` papkasini vaqti-vaqti bilan tozalab turing.
- Bu loyiha lokal foydalanish uchun mo'ljallangan asos (prototip) — real
  foydalanuvchilarga ochiq saytga chiqarishdan oldin xavfsizlik, navbat
  tizimi (queue) va xatoliklarni boshqarishni kuchaytirish tavsiya etiladi.
