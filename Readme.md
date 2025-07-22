# Chatbot Biologi Bu Rani

Ini adalah proyek chatbot Telegram yang dirancang khusus untuk menjawab pertanyaan seputar biologi. Chatbot ini menggunakan API OpenAI (ChatGPT) untuk menghasilkan respons berdasarkan instruksi sistem yang telah ditentukan.

## Fitur

*   Menjawab pertanyaan spesifik tentang biologi.
*   Mampu merespons sapaan umum dengan ramah.
*   Menolak pertanyaan di luar topik biologi (kecuali sapaan).
*   Dapat membantu menyusun kerangka RPP (Rencana Pelaksanaan Pembelajaran) biologi berdasarkan input KD/Capaian Pembelajaran dan alokasi waktu.
*   Menyimpan riwayat percakapan terbatas untuk konteks.
*   Mendukung format MarkdownV2 untuk respons yang terstruktur.
*   Menangani pesan non-teks dengan pemberitahuan.

## Persyaratan

*   Python 3.6 atau lebih tinggi
*   Akun Telegram dan BotFather untuk mendapatkan token bot.
*   Akun OpenAI dan kunci API.

## Instalasi

1.  Clone repositori ini atau unduh file `bot.py`.
2.  Instal dependensi Python:
    ```bash
    pip install python-telegram-bot openai python-dotenv
    ```
3.  Buat file `.env` di direktori yang sama dengan `bot.py`.
4.  Tambahkan variabel lingkungan berikut ke file `.env`, ganti nilai placeholder dengan token dan kunci API Anda:
    ```env
    TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
    OPENAI_API_KEY=YOUR_OPENAI_API_KEY
    ```

## Penggunaan

1.  Jalankan skrip Python:
    ```bash
    python bot.py
    ```
2.  Buka aplikasi Telegram dan cari bot Anda berdasarkan username yang Anda buat di BotFather.
3.  Mulai percakapan dengan bot.

### Perintah

*   `/start`: Memulai percakapan dengan bot dan membersihkan riwayat.
*   `/clear`: Membersihkan riwayat percakapan saat ini.

### Interaksi

*   Ajukan pertanyaan seputar biologi.
*   Untuk meminta RPP, sebutkan kebutuhan RPP dan berikan informasi KD/Capaian Pembelajaran serta alokasi waktu.
*   Bot akan menolak pertanyaan yang tidak relevan dengan biologi (kecuali sapaan).

## Konfigurasi Lanjutan

*   **`SYSTEM_INSTRUCTION_BIOLOGY`**: Variabel ini di dalam `bot.py` mendefinisikan peran dan aturan bot. Anda dapat memodifikasinya untuk mengubah perilaku bot.
*   **`OPENAI_MODEL`**: Variabel ini menentukan model OpenAI yang digunakan (default: `gpt-4.1-nano`). Anda bisa menggantinya dengan model lain yang tersedia di akun OpenAI Anda.
*   **`MAX_HISTORY_MESSAGES`**: Menentukan berapa banyak pasangan pesan (pengguna + bot) yang disimpan dalam riwayat percakapan untuk konteks.

## Catatan

*   Pastikan kunci API Anda aman dan tidak dibagikan secara publik.
*   Penggunaan API OpenAI mungkin dikenakan biaya.
*   Penanganan MarkdownV2 di Telegram bisa rumit. Respons bot mencoba melakukan escaping dasar, tetapi format kompleks mungkin memerlukan penyesuaian.