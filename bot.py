import logging
import os
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

# Muat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Ambil token dan API key
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    logger.error("Token Telegram Bot tidak ditemukan!")
    exit()
if not OPENAI_API_KEY:
    logger.error("Kunci API OpenAI tidak ditemukan!")
    exit()

# Instruksi sistem untuk OpenAI (ChatGPT)
SYSTEM_INSTRUCTION_BIOLOGY = (
    "Kamu adalah asisten AI yang sangat ahli dalam bidang biologi. "
    "Tugasmu adalah menjawab pertanyaan yang berkaitan dengan biologi secara akurat dan informatif. "
    "Berikan jawaban yang ringkas dan langsung ke intinya kecuali jika pengguna secara eksplisit meminta penjelasan yang lebih detail (misalnya, dengan frasa 'jelaskan lebih lanjut', 'detailnya', 'lebih lengkap'). Jika pengguna meminta detail, baru berikan penjelasan yang lebih mendalam. "
    "Kamu juga BOLEH merespons sapaan umum dengan ramah (contohnya: 'halo', 'hai', 'selamat pagi', 'apa kabar?', 'bolehkah saya bertanya?'). "
    "Setelah merespons sapaan tersebut, kamu bisa dengan sopan menambahkan bahwa spesialisasi utamamu adalah menjawab pertanyaan terkait biologi. "
    "Untuk semua pertanyaan LAIN di luar sapaan dasar tersebut, jika pertanyaan tidak berhubungan dengan biologi, kamu HARUS menolak dengan sopan dan "
    "menjelaskan bahwa kamu hanya dapat menjawab pertanyaan seputar biologi. "
    "Jangan mencoba menjawab pertanyaan di luar biologi selain sapaan umum. "
    "Jika pengguna meminta pembuatan RPP (Rencana Pelaksanaan Pembelajaran) atau dokumen serupa, jawab: Saya bisa membantu membuatkan RPP untuk Anda. Silakan berikan informasi mengenai Kompetensi Dasar (KD) atau Capaian Pembelajaran yang ingin dicapai serta alokasi waktu pembelajaran (misalnya 2 x 45 menit)... "
    "PERHATIAN: Jangan gunakan atau hasilkan format Markdown, kode, atau simbol Markdown apapun dalam jawabanmu. Selalu jawab hanya dalam format teks biasa (plain text) tanpa format khusus."
)

# Hapus simbol Markdown dari teks
def remove_markdown_symbols(text: str) -> str:
    text = re.sub(r"[*_`~>#\-+=|{}\[\]\\]", "", text)  # Hapus simbol khusus
    text = re.sub(r"#+\s*", "", text)  # Hapus heading markdown
    return text

# Konfigurasi API OpenAI
try:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    OPENAI_MODEL = "gpt-4o-mini"
except Exception as e:
    logger.error(f"Gagal mengkonfigurasi OpenAI API: {e}")
    exit()

MAX_HISTORY_MESSAGES = 10

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    context.user_data.pop('chat_history', None)
    welcome_message = (
        f"Halo {user.first_name}\n\n"
        "Selamat datang di LioraTa'\n"
        "Silakan bertanya seputar biologi dan saya akan menjawabnya.\n"
        "\"Hanya menjawab seputar Biologi\"\n\n"
        "Gunakan /clear untuk menghapus riwayat percakapan."
    )
    await update.message.reply_text(welcome_message)

async def clear_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop('chat_history', None)
    await update.message.reply_text("Riwayat percakapan Anda telah dibersihkan.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Menerima pesan dari {user_id}: {user_text}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    chat_history = context.user_data.get('chat_history', [])

    messages = [{'role': 'system', 'content': SYSTEM_INSTRUCTION_BIOLOGY}]
    for msg in chat_history:
        if 'role' in msg and 'content' in msg:
            messages.append({'role': msg['role'], 'content': msg['content']})
    messages.append({'role': 'user', 'content': user_text})

    bot_response_text = "Maaf, terjadi kesalahan internal saat mencoba menjawab pertanyaan Anda."
    raw_openai_output = ""

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=1020,
            temperature=0.4
        )

        if response.choices and response.choices[0].message and response.choices[0].message.content:
            raw_openai_output = response.choices[0].message.content
            cleaned_output = remove_markdown_symbols(raw_openai_output)
            bot_response_text = cleaned_output

            chat_history.append({'role': 'user', 'content': user_text})
            chat_history.append({'role': 'assistant', 'content': raw_openai_output})

            if len(chat_history) > 2 * MAX_HISTORY_MESSAGES:
                chat_history = chat_history[-(2 * MAX_HISTORY_MESSAGES):]

            context.user_data['chat_history'] = chat_history
        else:
            bot_response_text = "Maaf, saya tidak bisa memberikan jawaban saat ini."

    except Exception as e:
        logger.error(f"Error saat memproses pesan dengan OpenAI: {e}")
        bot_response_text = "Terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi."

    try:
        if not bot_response_text.strip():
            bot_response_text = "Terjadi kesalahan dalam memproses respons."
        await update.message.reply_text(bot_response_text, parse_mode=None)
    except BadRequest as e:
        logger.error(f"BadRequest Telegram: {e}")
        await update.message.reply_text("Terjadi kesalahan saat mengirim balasan.")

async def handle_non_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    logger.info(f"Menerima pesan non-teks dari {user_id}")
    await update.message.reply_text(
        "Maaf, saya hanya bisa memproses pesan teks. Silakan ajukan pertanyaan Anda dalam bentuk teks."
    )

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clear", clear_history_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.Document.ALL | filters.AUDIO | filters.VIDEO | filters.Sticker.ALL |
        filters.Dice.ALL | filters.LOCATION | filters.CONTACT | filters.POLL | filters.VENUE |
        filters.ANIMATION | filters.VOICE, handle_non_text_message))

    logger.info("Memulai bot dengan OpenAI API...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
