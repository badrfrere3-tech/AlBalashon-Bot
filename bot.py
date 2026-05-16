import logging
import sqlite3
import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ─── الإعدادات ───────────────────────────────
BOT_TOKEN  = "8692227293:AAFEqO_5EqAm-jTB7GGnfVMlMh8Ru1iwSeM"
ADMIN_ID   = 5481609181
CHANNEL_ID = "@AlBalashon_Channel"

# ─── مراحل المحادثة ──────────────────────────
CHOOSING, TYPING_INPUT = range(2)

# ─── جدول المواصلات (عدّله بحرية) ───────────
TRANSPORT_TEXT = (
    "🚌 *دليل مواعيد مواصلات البلشون المحدث:*\n\n"
    "⏱️ *ميكروباص الزقازيق:* من الـ 6 صباحاً وحتى الـ 11 مساءً (من الموقف).\n"
    "⏱️ *ميكروباص بيلبيس:* متوفر على مدار الساعة من على الطريق الرئيسي.\n"
    "🚂 *قطارات محطة بيلبيس (إلى القاهرة):*\n"
    "- قطار رقم 941 (مكيف) الساعة 6:15 صباحاً.\n"
    "- قطار رقم 953 (مميز) الساعة 7:30 صباحاً."
)

# ─── لوحة المفاتيح الرئيسية ─────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 إرسال استغاثة / حالة عاجلة"],
        ["📦 أبلغ عن مفقود / أمانة", "📢 إعلان منتج / خدماتنا"],
        ["🚌 مواعيد المواصلات", "💼 وظائف خالية"],
    ],
    resize_keyboard=True,
)

# ─── Logging ────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════
#  قاعدة البيانات
# ════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect("albalashon.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()


def register_user(user_id: int):
    conn = sqlite3.connect("albalashon.db")
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_all_user_ids() -> list:
    conn = sqlite3.connect("albalashon.db")
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_user_count() -> int:
    conn = sqlite3.connect("albalashon.db")
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


# ════════════════════════════════════════════
#  /start
# ════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    register_user(update.effective_user.id)
    await update.message.reply_text(
        "💡 مرحباً بك في منصة خدمات البلاشون الذكية.\nاختر الخدمة المطلوبة من الأزرار بالأسفل:",
        reply_markup=MAIN_KEYBOARD,
    )
    return CHOOSING


# ════════════════════════════════════════════
#  معالج اختيارات القائمة الرئيسية
# ════════════════════════════════════════════

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text

    if text == "🚌 مواعيد المواصلات":
        # يرد مباشرة بدون الانتقال لحالة إدخال
        await update.message.reply_text(TRANSPORT_TEXT, parse_mode="Markdown")
        return CHOOSING

    elif text == "💼 وظائف خالية":
        await update.message.reply_text(
            f"💼 لمتابعة الوظائف المتاحة ادخل على قناتنا:\n"
            f"https://t.me/{CHANNEL_ID.lstrip('@')}\n\n"
            "لو عايز تضيف وظيفة، اكتب تفاصيلها (التخصص، المرتب، التواصل) هنا:"
        )
        return TYPING_INPUT

    elif text == "🚨 إرسال استغاثة / حالة عاجلة":
        await update.message.reply_text(
            "🚨 اكتب تفاصيل الاستغاثة ورقم التواصل وسأرسلها للمشرف فوراً:"
        )
        return TYPING_INPUT

    elif text == "📦 أبلغ عن مفقود / أمانة":
        await update.message.reply_text(
            "📦 اكتب مواصفات الشيء المفقود، ومكان التواجد، ورقم تليفونك للنشر:"
        )
        return TYPING_INPUT

    elif text == "📢 إعلان منتج / خدماتنا":
        keyboard = [
            [InlineKeyboardButton("تواصل معنا 💬", url="https://wa.me/201020549760")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "مرحباً بك في قسم الإعلانات والخدمات. للتواصل مع الإدارة وحجز مساحة إعلانية لمنتجك أو محلك جوه البوت والقناة، يرجى التواصل معنا عبر الواتساب",
            reply_markup=reply_markup
        )
        return CHOOSING

    else:
        # أي نص غير معروف → أعد القائمة
        await update.message.reply_text(
            "اختر خدمة من القائمة 👇", reply_markup=MAIN_KEYBOARD
        )
        return CHOOSING


# ════════════════════════════════════════════
#  معالج النص المُدخَل بعد اختيار الخدمة
# ════════════════════════════════════════════

async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    choice    = context.user_data.get("choice", "")
    user      = update.effective_user
    username  = f"@{user.username}" if user.username else str(user.id)

    try:
        if choice == "🚨 إرسال استغاثة / حالة عاجلة":
            # → إلى الأدمن فقط
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🚨 *استغاثة عاجلة جديدة!*\n\n"
                    f"المُرسِل: {username}\n"
                    f"الرسالة:\n{user_text}"
                ),
                parse_mode="Markdown",
            )
        else:
            # → إلى القناة
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=(
                    f"📢 *{choice}*\n\n"
                    f"{user_text}\n\n"
                    "🤖 للتواصل عبر البوت: @AlBalashon\\_services\\_bot"
                ),
                parse_mode="Markdown",
            )

        await update.message.reply_text(
            "✅ تم استقبال بياناتك ونشرها بنجاح! شكراً لك.",
            reply_markup=MAIN_KEYBOARD,
        )

    except Exception as e:
        logger.error("process_input error: %s", e)
        await update.message.reply_text(
            "❌ حدث خطأ أثناء الإرسال. تأكد أن البوت مشرف في القناة.",
            reply_markup=MAIN_KEYBOARD,
        )

    context.user_data.clear()
    return CHOOSING


# ════════════════════════════════════════════
#  أوامر الأدمن
# ════════════════════════════════════════════

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر للمشرف فقط.")
        return
    count = get_user_count()
    await update.message.reply_text(f"📊 عدد المشتركين في البوت حالياً: {count} شخص.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر للمشرف فقط.")
        return

    # context.args قد يكون None أو فارغاً
    if not context.args:
        await update.message.reply_text("⚠️ اكتب الرسالة بعد الأمر:\n/broadcast نص الرسالة")
        return

    msg   = " ".join(context.args)
    users = get_all_user_ids()
    sent  = failed = 0

    status = await update.message.reply_text(f"📤 جاري الإرسال إلى {len(users)} مستخدم...")

    for uid in users:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 *تنويه عام:*\n\n{msg}",
                parse_mode="Markdown",
            )
            sent += 1
        except Exception as e:
            logger.warning("broadcast skip %s: %s", uid, e)
            failed += 1
        await asyncio.sleep(0.05)  # rate limit

    await status.edit_text(
        f"✅ أُرسلت لـ {sent} مستخدم.\n❌ فشل لـ {failed} مستخدم."
    )


# ════════════════════════════════════════════
#  الإعداد والتشغيل
# ════════════════════════════════════════════

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        # entry_points: /start فقط — لا نضع MessageHandler هنا
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING:     [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
            TYPING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_input)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stats",      stats))
    app.add_handler(CommandHandler("broadcast",  broadcast))

    logger.info("🚀 AlBalashon Bot started. Send /start to begin.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()