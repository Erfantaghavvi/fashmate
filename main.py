import os
import uuid
import logging
import shutil
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# تنظیمات عمومی
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
logging.basicConfig(level=logging.INFO)

UPLOAD_DIR = "user_uploads"
OUTPUT_DIR = "output"
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, "result.jpg")
MODEL_OUTPUT = "ladi-vton/output/try-on.jpg"
user_images = {}

# ایجاد پوشه‌های ضروری
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("assets/image", exist_ok=True)
os.makedirs("assets/cloth", exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! 👕 لطفاً ابتدا عکس بدن خودت رو بفرست و بعدش عکس لباس رو.")

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
        await update.message.reply_text("در حال اجرای مدل LaDI-VTON... 🛠️ لطفاً منتظر بمانید.")

        try:
            run_ladi_vton(user_images[user_id]["person"], user_images[user_id]["cloth"])
            if not os.path.exists(MODEL_OUTPUT):
                raise FileNotFoundError("خروجی try-on پیدا نشد!")

            shutil.copy(MODEL_OUTPUT, OUTPUT_IMAGE)

            with open(OUTPUT_IMAGE, "rb") as out_file:
                await update.message.reply_photo(photo=InputFile(out_file))

        except Exception as e:
            logging.error(f"Error during model execution: {e}")
            await update.message.reply_text(f"❌ خطا در اجرای مدل: {e}")

        finally:
            user_images.pop(user_id, None)

def run_ladi_vton(person_path: str, cloth_path: str):
    # پاک‌سازی ورودی قبلی
    for path in ["assets/image/person.jpg", "assets/cloth/cloth.jpg"]:
        if os.path.exists(path):
            os.remove(path)

    shutil.copy(person_path, "assets/image/person.jpg")
    shutil.copy(cloth_path, "assets/cloth/cloth.jpg")


    # اجرای مدل LaDI-VTON
    exit_code = os.system("python inference.py")
    if exit_code != 0:
        raise RuntimeError("اجرای اسکریپت مدل با خطا مواجه شد.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("🤖 ربات LaDI-VTON آماده‌ی کار است...")
    app.run_polling()
