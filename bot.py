import logging
import os
from openai import AsyncOpenAI 
from dotenv import load_dotenv  
from telegram import Update  
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes  
from telegram.constants import ParseMode  
from telegram.error import BadRequest  

# Muat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Ambil token dan kunci API
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Use OPENAI_API_KEY

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
    "Jangan mencoba menjawab pertanyaan di luar biologi selain sapaan umum."
    "Jika pengguna meminta pembuatan RPP (Rencana Pelaksanaan Pembelajaran) atau dokumen serupa, jawab Saya bisa membantu membuatkan RPP untuk Anda. Silakan berikan informasi mengenai Kompetensi Dasar (KD) atau Capaian Pembelajaran yang ingin dicapai serta alokasi waktu pembelajaran (misalnya 2 x 45 menit). RPP akan disusun berdasarkan komponen utama yang meliputi: Kompetensi Dasar dan indikator pencapaiannya, Materi Ajar, Metode Pembelajaran, Media pembelajaran dan sumber belajar, Langkah-langkah Pembelajaran (pendahuluan, inti, penutup), serta Penilaian (asesmen). Setelah informasi tersebut diberikan, saya akan segera menyusun RPP yang sesuai."
    "Selalu gunakan format daftar bernomor untuk menyajikan poin-poin utama. Gunakan angka dengan tanda titik (1., 2., 3., dst.) untuk level utama. "
    "Untuk sub-poin di bawah poin utama, gunakan format huruf kecil diikuti titik (a., b., c., dst.). "
    "Jika diperlukan level ketiga, gunakan simbol bullet point (•) untuk sub-sub poin. "
    "Pastikan output MarkdownV2 kamu valid. Misalnya, karakter seperti '.', '(', ')', '-', '!', '+' harus di-escape dengan backslash jika bukan bagian dari sintaks Markdown normal. Contoh: 'Ini adalah teks \\- dengan tanda hubung yang di-escape'."
)

# Konfigurasi API OpenAI
try:

    client = AsyncOpenAI(api_key=OPENAI_API_KEY) # Initialize OpenAI client
    OPENAI_MODEL = "gpt-4o-mini"  # Use correct model name

except Exception as e:
    logger.error(f"Gagal mengkonfigurasi OpenAI API: {e}") 
    exit()

MAX_HISTORY_MESSAGES = 10 


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    context.user_data.pop('chat_history', None) # Clear history on start
    welcome_message = (
        f"Halo {user.mention_markdown_v2()}\n\n"
        "*Selamat datang di LioraTa'*\n"
        "Silahkan bertanya seputar biologi dan saya akan mencoba menjawabnya\\.\n"
        "*\"Hanya menjawab seputar Biologi\"*\n\n"
        "_Gunakan /clear untuk menghapus riwayat percakapan\\._"
    )
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN_V2)


async def clear_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop('chat_history', None)
    await update.message.reply_text("Riwayat percakapan Anda telah dibersihkan.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Menerima pesan dari {user_id}: {user_text}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Get chat history, default to empty list if not exists
    chat_history = context.user_data.get('chat_history', [])

    messages = [{'role': 'system', 'content': SYSTEM_INSTRUCTION_BIOLOGY}]

    # Add previous messages from history (OpenAI format)
    for msg in chat_history:
        if 'role' in msg and 'content' in msg:
            messages.append({'role': msg['role'], 'content': msg['content']})

    # Add the current user message
    messages.append({'role': 'user', 'content': user_text})

    bot_response_text = "Maaf, terjadi kesalahan internal saat mencoba menjawab pertanyaan Anda. Silakan coba lagi nanti."
    raw_openai_output = ""

    try:
        # Call OpenAI Chat Completion API
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=1020, # Equivalent to Gemini's max_output_tokens
            temperature=0.4 # Equivalent to Gemini's temperature
        )

        # Parse the response
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            raw_openai_output = response.choices[0].message.content
            bot_response_text = raw_openai_output
            chat_history.append({'role': 'user', 'content': user_text})
            chat_history.append({'role': 'assistant', 'content': raw_openai_output})
            if len(chat_history) > 2 * MAX_HISTORY_MESSAGES:
                 # Keep the last MAX_HISTORY_MESSAGES pairs
                 chat_history = chat_history[-(2 * MAX_HISTORY_MESSAGES):]

            context.user_data['chat_history'] = chat_history
        else:
            logger.warning("Tidak ada konten teks yang valid dalam respons OpenAI.")
            bot_response_text = "Maaf, saya tidak bisa memberikan jawaban saat ini."

    except Exception as e:
        # logger.error(f"Error saat memproses pesan dengan Gemini: {e}")
        logger.error(f"Error saat memproses pesan dengan OpenAI: {e}") # Update error message
        # Check for specific OpenAI errors if needed, e.g., openai.APIError
        bot_response_text = "Terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi."

    # Mengirim pesan ke pengguna
    try:
        if not bot_response_text.strip():
            logger.warning("bot_response_text kosong sebelum dikirim ke Telegram.")
            bot_response_text = "Terjadi kesalahan dalam memproses respons."
            await update.message.reply_text(bot_response_text)
            return


        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        escaped_text = bot_response_text
        for char in chars_to_escape:
             escaped_text = escaped_text.replace(char, f'\\{char}')

        await update.message.reply_text(escaped_text, parse_mode=ParseMode.MARKDOWN_V2)

    except BadRequest as e:
        logger.error(f"BadRequest Telegram saat parsing Markdown: {e}")
        # If MarkdownV2 parsing fails, send as plain text
        await update.message.reply_text(bot_response_text, parse_mode=None)


# --- Fungsi baru untuk menangani input non-teks ---
async def handle_non_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani pesan yang bukan teks, seperti file atau foto."""
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
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL | filters.AUDIO | filters.VIDEO | filters.Sticker.ALL | filters.Dice.ALL | filters.LOCATION | filters.CONTACT | filters.POLL | filters.VENUE | filters.ANIMATION | filters.VOICE, handle_non_text_message))


    # logger.info("Memulai bot...")
    logger.info("Memulai bot dengan OpenAI API...") # Update log message
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()