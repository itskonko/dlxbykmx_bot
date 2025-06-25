# DownloadX - Secure Private Telegram Video Downloader Bot
# Dependencies: python-telegram-bot, yt-dlp
# Recommended Python version: 3.10+

import os
import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          filters, ContextTypes, CallbackQueryHandler)

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("AAGD0nQei0viGUpbYEJzYpqmzyvBAUzdAM4")
ACCESS_CODE = os.getenv("ACCESS_CODE", "2026")
ALLOWED_USERS = set()

# === START COMMAND ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ALLOWED_USERS:
        await update.message.reply_text("✅ You already have access. Send me a video link.")
    else:
        await update.message.reply_text("🔐 Welcome to DownloadX.\nPlease enter your access code:")

# === MESSAGE HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in ALLOWED_USERS:
        if text == ACCESS_CODE:
            ALLOWED_USERS.add(user_id)
            await update.message.reply_text("✅ Access granted. Now send a video link.")
        else:
            await update.message.reply_text("❌ Invalid code. Try again.")
        return

    if any(x in text for x in ["youtube.com", "youtu.be", "facebook.com", "instagram.com"]):
        context.user_data['video_url'] = text
        await update.message.reply_text(
            "🎞 Select the video quality:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("360p", callback_data='360'),
                 InlineKeyboardButton("480p", callback_data='480')],
                [InlineKeyboardButton("720p", callback_data='720'),
                 InlineKeyboardButton("1080p", callback_data='1080')],
                [InlineKeyboardButton("Best", callback_data='best')]
            ])
        )
    else:
        await update.message.reply_text("⚠️ Please send a valid video link from YouTube, Facebook, or Instagram.")

# === QUALITY CALLBACK ===
async def handle_quality_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    quality = query.data
    url = context.user_data.get('video_url')

    if not url:
        await query.edit_message_text("❌ No video URL found. Please send the link again.")
        return

    await query.edit_message_text(f"⏬ Downloading in {quality} quality...")

    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]' if quality != 'best' else 'bestvideo+bestaudio/best',
        'outtmpl': 'downloadx_output.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_path = next((f for f in os.listdir('.') if f.startswith('downloadx_output.')), None)

        if file_path and os.path.getsize(file_path) < 50 * 1024 * 1024:  # Telegram limit: 50MB for normal accounts
            await context.bot.send_video(chat_id=update.effective_chat.id, video=open(file_path, 'rb'))
        elif file_path:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, 'rb'))
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Failed to download the video.")

        if file_path:
            os.remove(file_path)

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Error: {str(e)}")

# === MAIN FUNCTION ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_quality_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ DownloadX is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
