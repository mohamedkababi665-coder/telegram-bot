import base64
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "8358470857:AAHczciOJHnj8hSnwmFAhM8MBc9mSo4-38o"

user_store = {}


# ================= READ FILE =================

def decode_dark(content):
    try:
        if content.startswith("darktunnel://"):
            content = content.replace("darktunnel://", "")

        decoded = base64.b64decode(content).decode()
        data = json.loads(decoded)
        return data
    except:
        return None


# ================= EXTRACT REAL VLESS =================

def extract_vless(data):
    try:
        cfg = data["vlessTunnelConfig"]["v2rayConfig"]

        uuid = cfg.get("uuid", "")
        host = cfg.get("host", "")
        port = cfg.get("port", 443)
        ws_path = cfg.get("wsPath", "/")
        ws_host = cfg.get("wsHeaderHost", "")
        sni = cfg.get("serverNameIndication", "")

        vless = (
            f"vless://{uuid}@{host}:{port}"
            f"?encryption=none&security=tls&type=ws"
            f"&host={ws_host}&path={ws_path}&sni={sni}"
            f"#MohamedPor"
        )

        return vless
    except:
        return None


# ================= CREATE MODIFIED FILE =================

def create_modified(original_data):

    # نسخ البيانات لتجنب تعديل الأصل
    data = json.loads(json.dumps(original_data))

    # حذف injectConfig (بروكسي + بيلود)
    if "injectConfig" in data["vlessTunnelConfig"]:
        del data["vlessTunnelConfig"]["injectConfig"]

    cfg = data["vlessTunnelConfig"]["v2rayConfig"]

    # لا نغير السيرفر
    # فقط تثبيت youtube SNI
    cfg["serverNameIndication"] = "youtube.com"
    cfg["sni"] = "youtube.com"

    json_data = json.dumps(data)
    encoded = base64.b64encode(json_data.encode()).decode()

    file_name = "Mohamed Por.dark"

    with open(file_name, "w") as f:
        f.write("darktunnel://" + encoded)

    return file_name


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Start", callback_data="restart")]
    ])

    await update.message.reply_text(
        "🔥 مرحبًا بك في بوت Mohamed Por\n\n"
        "📂 أرسل ملف .dark\n"
        "سيتم استخراج VLESS وإنشاء ملف جاهز",
        reply_markup=keyboard
    )


# ================= HANDLE FILE =================

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file = await update.message.document.get_file()
    content = (await file.download_as_bytearray()).decode("utf-8", "ignore")

    data = decode_dark(content)

    if not data:
        await update.message.reply_text("❌ ملف غير صالح")
        return

    user_store[update.effective_user.id] = data

    vless = extract_vless(data)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ إنشاء ملف Mohamed Por", callback_data="make")],
        [InlineKeyboardButton("🔄 Start", callback_data="restart")]
    ])

    await update.message.reply_text(
        f"✅ VLESS الحقيقي:\n\n<code>{vless}</code>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ================= BUTTON =================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "restart":
        await query.message.reply_text(
            "📂 أرسل ملف جديد .dark"
        )
        return

    data = user_store.get(query.from_user.id)

    if not data:
        await query.message.reply_text("❌ أرسل ملف أولًا")
        return

    file_name = create_modified(data)

    await query.message.reply_document(
        document=open(file_name, "rb"),
        filename="Mohamed Por.dark",
        caption="✅ تم إنشاء الملف بنجاح"
    )


# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot Running...")
app.run_polling()
