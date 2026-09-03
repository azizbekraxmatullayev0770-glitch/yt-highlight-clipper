# Saytni jonli qilish — Render.com orqali (bepul, ~15 daqiqa)

Bu qadamlarni bajarsangiz, sizda **haqiqiy internet-sayt** (masalan
`https://yt-highlight-clipper.onrender.com`) paydo bo'ladi — istalgan
telefon/kompyuterdan ochib, YouTube link tashlab ishlata olasiz.

## 1-qadam: Kodni GitHub'ga joylash
1. https://github.com da bepul akkaunt oching (bo'lmasa)
2. Yangi repository yarating (masalan nomi: `yt-highlight-clipper`)
3. Ushbu papkadagi barcha fayllarni o'sha repositoryga yuklang
   (GitHub saytida "Add file → Upload files" tugmasi orqali eng oson yo'l —
   shunchaki hamma faylni sudrab tashlaysiz)

## 2-qadam: Render.com'da akkaunt ochish
1. https://render.com ga kiring, "Get Started" → GitHub akkauntingiz bilan
   ro'yxatdan o'ting

## 3-qadam: Yangi Web Service yaratish
1. Render dashboardida **"New +" → "Web Service"** tugmasini bosing
2. GitHub repositoryingizni tanlang (`yt-highlight-clipper`)
3. Render `Dockerfile`ni avtomatik taniydi — "Environment: Docker" tanlangan
   bo'lishi kerak
4. **Instance Type: Free** ni tanlang
5. **Environment Variables** bo'limida qo'shing:
   - `ANTHROPIC_API_KEY` = sizning Anthropic API kalitingiz
     (https://console.anthropic.com dan olinadi)
6. **"Create Web Service"** tugmasini bosing

## 4-qadam: Kutish
Render avtomatik ravishda kodni yig'adi (build qiladi) — bu 5-10 daqiqa
vaqt oladi. Tugagach, sizga shunday havola beriladi:

```
https://yt-highlight-clipper.onrender.com
```

Shu havolani brauzerda ochsangiz — sayt tayyor! YouTube linkni tashlab,
sinab ko'rishingiz mumkin.

## Muhim eslatmalar

- **Bepul tarif** cheklovlari bor: server 15 daqiqa foydalanilmasa "uxlab
  qoladi" va keyingi so'rovda 30-50 soniya uyg'onish vaqti ketadi; uzun
  video (bir necha soatlik strim) qayta ishlashda vaqt limiti yetmasligi
  mumkin — shunday holatda pullik tarifga ($7/oy dan) o'tish kerak bo'ladi.
- Agar GitHub bilan ishlash qiyin tuyulsa, ayting — men sizga muqobil,
  yanada sodda variant (masalan Railway.app orqali, deyarli bir xil
  qadamlar) ni ham tushuntirib beraman.
- Kodni o'zgartirish kerak bo'lsa (masalan subtitr rangini o'zgartirish),
  GitHub'dagi faylni tahrirlab saqlasangiz, Render avtomatik yangilaydi.
