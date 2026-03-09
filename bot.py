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

TOKEN = "8741949277:AAHmxeny4IOMMT2-I7MQB0eWuqODipCpv0c"

user_store = {}

# ================= SNI LIST =================

SNI_LIST = [
    "youtube.com",
    "yt3.ggpht.com",
    "i.ytimg.com",
    "wzrkt.com",
    "clevertap-prod.com",
    "r3---sn.googlevideo.com",
    "redirector.googlevideo.com"
]

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

# ================= EXTRACT VLESS =================

def extract_vless(data):
    try:

        cfg = data["vlessTunnelConfig"]["v2rayConfig"]

        uuid = cfg.get("uuid", "")
        ws_path = cfg.get("wsPath", "/")
        host_header = cfg.get("wsHeaderHost", "")

        vless = (
            f"vless://{uuid}@google.com:443"
            f"?encryption=none"
            f"&security=tls"
            f"&type=ws"
            f"&host={host_header}"
            f"&path={ws_path}"
            f"&sni=youtube.com"
            f"#Mohamed-Pro"
        )

        return vless

    except:
        return "❌ فشل استخراج VLESS"

# ================= CREATE FILE =================

def create_file(original, sni):

    data = json.loads(json.dumps(original))

    if "injectConfig" in data["vlessTunnelConfig"]:
        del data["vlessTunnelConfig"]["injectConfig"]

    cfg = data["vlessTunnelConfig"]["v2rayConfig"]

    cfg["host"] = "google.com"
    cfg["port"] = 443
    cfg["serverNameIndication"] = sni
    cfg["sni"] = sni

    json_data = json.dumps(data)
    encoded = base64.b64encode(json_data.encode()).decode()

    file_name = f"{sni}.dark"

    with open(file_name, "w") as f:
        f.write("darktunnel://" + encoded)

    return file_name

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Start", callback_data="restart")]
    ])

    await update.message.reply_text(
        "🔥 مرحبًا بك في بوت Mohamed Pro\n\n"
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
        [InlineKeyboardButton("📂 إنشاء ملف Mohamed Pro", callback_data="make")],
        [InlineKeyboardButton("🧠 تغيير SNI", callback_data="sni")],
        [InlineKeyboardButton("🔄 Start", callback_data="restart")]
    ])

    await update.message.reply_text(
        f"✅ VLESS المستخرج:\n\n<code>{vless}</code>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# ================= BUTTON =================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "restart":
        await query.message.reply_text("📂 أرسل ملف جديد .dark")
        return

    data = user_store.get(user_id)

    if not data:
        await query.message.reply_text("❌ أرسل ملف أولاً")
        return

    if query.data == "make":

        file_name = create_file(data, "youtube.com")

        await query.message.reply_document(
            document=open(file_name, "rb"),
            filename="Mohamed Pro.dark",
            caption="✅ تم إنشاء الملف باستخدام SNI: youtube.com"
        )

# ================= SHOW SNI =================

    elif query.data == "sni":

        buttons = []

        for sni in SNI_LIST:
            buttons.append([InlineKeyboardButton(sni, callback_data=f"sni_{sni}")])

        buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="restart")])

        await query.message.reply_text(
            "اختر SNI البديل:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# ================= CREATE SNI FILE =================

    elif query.data.startswith("sni_"):

        sni = query.data.replace("sni_", "")

        file_name = create_file(data, sni)

        await query.message.reply_document(
            document=open(file_name, "rb"),
            filename=f"{sni}.dark",
            caption=f"🚀 تم إنشاء الملف باستخدام SNI:\n{sni}"
        )

# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot Running...")

app.run_polling()
