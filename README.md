# 💰 Bot Telegram Aliran Tunai

Bot Telegram pintar untuk membantu urus kewangan perniagaan anda. Bot ini boleh memproses transaksi melalui teks dan juga memproses gambar resit secara automatik menggunakan AI.

## ✨ Ciri-ciri Utama

### 📝 **Pemprosesan Transaksi Teks**
- Hantar mesej teks tentang transaksi anda
- AI akan ekstrak maklumat seperti jenis transaksi, jumlah, pelanggan/vendor
- Data disimpan secara automatik dalam MongoDB

### 📸 **Pemprosesan Resit Gambar**
- Hantar foto resit dan bot akan baca teks automatik (OCR)
- AI akan analisis kandungan resit dan ekstrak maklumat transaksi
- Gambar resit disimpan bersama data untuk rujukan masa depan

### 📊 **Laporan Kesihatan Kewangan**
- Perintah `/status` untuk dapatkan laporan kesihatan kewangan
- Analisis Cash Conversion Cycle (CCC) 
- Nasihat tindakan berdasarkan data kewangan anda

### 📋 **Ringkasan Transaksi**
- Perintah `/summary` untuk lihat transaksi terkini
- Data diasingkan mengikut pengguna (setiap orang dapat data sendiri sahaja)

## 🚀 Cara Gunakan

### Perintah Tersedia:
- `/start` - Mesej selamat datang dan panduan
- `/status` - Laporan kesihatan kewangan dengan nasihat
- `/summary` - Ringkasan transaksi terkini anda

### Cara Hantar Transaksi:
1. **Teks**: "Jual 50 unit produk kepada Syarikat ABC secara tunai"
2. **Foto**: Ambil gambar resit dan hantar terus kepada bot

## 🛠️ Persediaan untuk Developer

### Keperluan Sistem
- Python 3.12+
- MongoDB
- Tesseract OCR
- API Key OpenAI
- Bot Token Telegram

### Pemasangan Tesseract (macOS)
```bash
brew install tesseract
```

### Langkah Pemasangan

1. **Clone repository**
```bash
git clone <repository-url>
cd aliran-tunai
```

2. **Buat virtual environment**
```bash
python -m venv aliran
source aliran/bin/activate  # macOS/Linux
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Sediakan fail .env**
```env
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
MONGO_URI=your_mongodb_connection_string
```

5. **Jalankan bot**
```bash
python main.py
```

## 🗃️ Struktur Database

Setiap transaksi disimpan dalam MongoDB dengan struktur:

```json
{
  "chat_id": 123456789,
  "action": "purchase",
  "amount": 25.99,
  "vendor": "Kedai Kopi",
  "terms": "kad",
  "description": "Kopi dan kuih",
  "date": "2025-08-16",
  "timestamp": "2025-08-16T...",
  "has_image": true,
  "receipt_image": "base64_encoded_data"
}
```

## 🔐 Privasi Data

- Setiap pengguna hanya boleh akses data sendiri sahaja
- Data diasingkan menggunakan `chat_id` Telegram
- Gambar resit disimpan dengan selamat dalam database

## 🤖 Teknologi Digunakan

- **Python 3.12** - Bahasa pengaturcaraan utama
- **python-telegram-bot** - Library untuk Telegram Bot API
- **OpenAI GPT** - AI untuk analisis teks dan resit
- **MongoDB** - Database untuk simpan transaksi
- **Tesseract OCR** - Untuk baca teks dari gambar
- **OpenCV & Pillow** - Pemprosesan gambar
- **pymongo** - MongoDB driver untuk Python

## 📄 Lesen

Projek ini adalah untuk kegunaan peribadi dan pembelajaran.

## 🆘 Sokongan

Jika ada masalah atau soalan, sila buka issue dalam repository ini.

---

**Dibuat dengan ❤️ untuk memudahkan pengurusan kewangan perniagaan**
