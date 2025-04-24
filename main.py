import os
import uuid
import logging
import shutil
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "7316868526:AAFfx9_6ocBz7U8VkRMGz_sczz09nbmxiPE")
logging.basicConfig(level=logging.INFO)

UPLOAD_DIR = "user_uploads"
OUTPUT_PATH = "output/result.jpg"
user_images = {}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("output", exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! 👕 لطفاً عکس بدن خودت رو بفرست، بعدش هم لباس رو.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo_file = await update.message.photo[-1].get_file()

    filename = f"{user_id}_{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)
    await photo_file.download_to_drive(file_path)

    if user_id not in user_images:
        user_images[user_id] = {"person": file_path}
        await update.message.reply_text("عکس بدن دریافت شد ✅ حالا عکس لباس رو بفرست.")
    else:
        user_images[user_id]["cloth"] = file_path
        await update.message.reply_text("در حال اجرای مدل... ⏳")

        try:
            run_ladi_vton(user_images[user_id]["person"], user_images[user_id]["cloth"])

            with open(OUTPUT_PATH, "rb") as out_file:
                await update.message.reply_photo(photo=InputFile(out_file))
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در اجرای مدل: {e}")
        finally:
            user_images.pop(user_id, None)

def run_ladi_vton(person_path, cloth_path):
    # پوشه تمیز
    shutil.copy(person_path, "assets/image/person.jpg")
    shutil.copy(cloth_path, "assets/cloth/cloth.jpg")

    # اجرای اسکریپت مدل
    os.system("python ladi-vton/inference.py")

    # فایل خروجی معمولاً در مسیر ladi-vton/output/ قرار می‌گیرد
    shutil.copy("output/try-on.jpg", OUTPUT_PATH)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("🤖 ربات آماده‌ست...")
    app.run_polling()
