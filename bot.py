import logging
import sqlite3
import asyncio
import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ─── الإعدادات ───────────────────────────────
BOT_TOKEN  = "8692227293:AAFEqO_5EqAm-jTB7GGnfVMlMh8Ru1iwSeM"
ADMIN_ID   = 5481609181
CHANNEL_ID = "@AlBalashon_Channel"

# ─── الكلمات المحظورة ────────────────────────
BAD_WORDS = ["احا", "خرا", "عرص", "متناك", "شرموط", "كلب", "ابن الكلب"] # يمكن تعديلها لاحقاً

def is_profane(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    for w in BAD_WORDS:
        if w in t:
            return True
    return False

# ─── مراحل المحادثة ──────────────────────────
CHOOSING, TYPING_INPUT = range(2)

# ─── نصوص ثابتة (يمكنك تعديلها لاحقاً) ────────
DOCTORS_TEXT = (
    "🩺 *دليل الأطباء والعيادات:*\n\n"
    "🏥 *باطنة:* د. (الاسم) - المواعيد: من 5 لـ 9 مساءً\n"
    "🦷 *أسنان:* د. (الاسم) - المواعيد: من 3 لـ 8 مساءً\n"
    "*(يمكنك إضافة العيادات هنا)*"
)

# Services texts
ELEC_TEXT = "⚡ *كهربائي:* (الاسم والرقم)"
PLUMB_TEXT = "🚰 *سباك:* (الاسم والرقم)"
CARP_TEXT = "🪚 *نجار:* (الاسم والرقم)"
APPL_TEXT = "🔧 *صيانة أجهزة:* (الاسم والرقم)"
MECH_TEXT = "👨‍🔧 *ميكانيكي وصيانة أعطال:* (الاسم والرقم)"
DELIVERY_TEXT = "📦 *خدمات الشحن والتوصيل (الطيارين):* (الاسم والرقم)"

# ─── لوحات المفاتيح ──────────────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 إرسال استغاثة / حالة عاجلة"],
        ["📦 أبلغ عن مفقود / أمانة", "📢 إعلان منتج / خدماتنا"],
        ["🚕 مشاركة المشاوير والمواصلات", "💼 وظائف خالية"],
        ["🛠️ الخدمات", "🩺 دليل الأطباء والعيادات"],
        ["🩸 التبرع بالدم والطوارئ"],
    ],
    resize_keyboard=True,
)

SERVICES_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["كهربائي", "سباك", "نجار"],
        ["صيانة أجهزة", "👨‍🔧 ميكانيكي وصيانة أعطال"],
        ["📦 خدمات الشحن والتوصيل (الطيارين)"],
        ["🏠 عقارات وسكن (بيع / إيجار)"],
        ["🔙 رجوع للقائمة الرئيسية"]
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
    conn.execute("CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def register_user(user_id: int):
    conn = sqlite3.connect("albalashon.db")
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def ban_user_db(user_id: int):
    conn = sqlite3.connect("albalashon.db")
    conn.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def is_user_banned(user_id: int) -> bool:
    conn = sqlite3.connect("albalashon.db")
    row = conn.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return bool(row)

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
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text("⛔ لا يمكنك استخدام البوت لأنه قد تم حظرك.")
        return ConversationHandler.END

    register_user(user_id)
    await update.message.reply_text(
        "💡 مرحباً بك في منصة خدمات البلاشون الذكية.\nاختر الخدمة المطلوبة من الأزرار بالأسفل:",
        reply_markup=MAIN_KEYBOARD,
    )
    return CHOOSING

# ════════════════════════════════════════════
#  مساعد للحظر التلقائي
# ════════════════════════════════════════════
async def check_and_ban(text: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text("⛔ لا يمكنك استخدام البوت لأنه قد تم حظرك.")
        return True
    
    if is_profane(text):
        ban_user_db(user_id)
        try:
            await context.bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        except Exception as e:
            logger.error("Could not ban user %s from channel: %s", user_id, e)
        await update.message.reply_text("⛔ تم حظرك نهائياً من البوت والقناة بسبب استخدام ألفاظ غير لائقة.")
        return True
    
    return False

# ════════════════════════════════════════════
#  معالج اختيارات القوائم
# ════════════════════════════════════════════

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    
    if await check_and_ban(text, update, context):
        return ConversationHandler.END

    context.user_data["choice"] = text

    # --- القائمة الرئيسية (نصوص مباشرة) ---
    if text == "🩺 دليل الأطباء والعيادات":
        await update.message.reply_text(DOCTORS_TEXT, parse_mode="Markdown")
        return CHOOSING
        
    elif text == "🛠️ الخدمات":
        await update.message.reply_text("اختر الخدمة المطلوبة من القائمة:", reply_markup=SERVICES_KEYBOARD)
        return CHOOSING
        
    elif text == "🔙 رجوع للقائمة الرئيسية":
        await update.message.reply_text("القائمة الرئيسية:", reply_markup=MAIN_KEYBOARD)
        return CHOOSING

    # --- القائمة الفرعية (الخدمات - نصوص مباشرة) ---
    elif text == "كهربائي":
        await update.message.reply_text(ELEC_TEXT, parse_mode="Markdown")
        return CHOOSING
    elif text == "سباك":
        await update.message.reply_text(PLUMB_TEXT, parse_mode="Markdown")
        return CHOOSING
    elif text == "نجار":
        await update.message.reply_text(CARP_TEXT, parse_mode="Markdown")
        return CHOOSING
    elif text == "صيانة أجهزة":
        await update.message.reply_text(APPL_TEXT, parse_mode="Markdown")
        return CHOOSING
    elif text == "👨‍🔧 ميكانيكي وصيانة أعطال":
        await update.message.reply_text(MECH_TEXT, parse_mode="Markdown")
        return CHOOSING
    elif text == "📦 خدمات الشحن والتوصيل (الطيارين)":
        await update.message.reply_text(DELIVERY_TEXT, parse_mode="Markdown")
        return CHOOSING

    # --- القائمة الرئيسية (إعلانات وروابط) ---
    elif text == "📢 إعلان منتج / خدماتنا":
        keyboard = [[InlineKeyboardButton("تواصل معنا 💬", url="https://wa.me/201020549760")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "مرحباً بك في قسم الإعلانات والخدمات. للتواصل مع الإدارة وحجز مساحة إعلانية لمنتجك أو محلك جوه البوت والقناة، يرجى التواصل معنا عبر الواتساب",
            reply_markup=reply_markup
        )
        return CHOOSING

    # --- الردود التي تتطلب إدخال بيانات من المستخدم ---
    elif text == "🩸 التبرع بالدم والطوارئ":
        await update.message.reply_text(
            "🩸 اكتب تفاصيل الحالة الحرجة فوراً (مثال: الفصيلة المطلوبة، المستشفى، ورقم تليفون التواصل):"
        )
        return TYPING_INPUT

    elif text == "💼 وظائف خالية":
        await update.message.reply_text(
            "💼 اكتب تفاصيل الوظيفة (التخصص، المرتب، رقم التواصل) وسيتم إرسالها للإدارة للموافقة عليها قبل النشر:"
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
        
    elif text == "🚕 مشاركة المشاوير والمواصلات":
        await update.message.reply_text(
            "🚕 اكتب تفاصيل مشوارك الحالي:\n"
            "- هل أنت سواق ومعاك أماكن فاضية؟\n"
            "- ولا راكب ومحتاج مواصلة؟\n"
            "- واكتب ساعتك ومكان التحرك ورقم تليفونك للتواصل."
        )
        return TYPING_INPUT
        
    elif text == "🏠 عقارات وسكن (بيع / إيجار)":
        await update.message.reply_text(
            "🏠 اكتب تفاصيل العقار:\n"
            "(شقة، محل، أرض، بيع أم إيجار، السعر، والمواصفات ورقم للتواصل):"
        )
        return TYPING_INPUT

    else:
        # نص غير معروف، أعد القائمة الحالية (سواء رئيسية أو فرعية)
        # لتسهيل الأمر سنعيد القائمة الرئيسية
        await update.message.reply_text("اختر خدمة من القائمة 👇", reply_markup=MAIN_KEYBOARD)
        return CHOOSING

# ════════════════════════════════════════════
#  معالج النص المُدخَل بعد اختيار الخدمة
# ════════════════════════════════════════════

async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    
    if await check_and_ban(user_text, update, context):
        return ConversationHandler.END

    choice    = context.user_data.get("choice", "")
    user      = update.effective_user
    username  = f"@{user.username}" if user.username else str(user.id)

    # تحديد رابط التواصل
    contact_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    try:
        if choice == "🚨 إرسال استغاثة / حالة عاجلة":
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚨 *استغاثة عاجلة جديدة!*\n\nالمُرسِل: {username}\nالرسالة:\n{user_text}",
                parse_mode="Markdown",
            )
            await update.message.reply_text("✅ تم إرسال استغاثتك للمشرف بنجاح.", reply_markup=MAIN_KEYBOARD)

        elif choice == "💼 وظائف خالية":
            # إرسال للإدارة للموافقة
            keyboard = [
                [
                    InlineKeyboardButton("✅ موافقة ونشر", callback_data=f"approve_job_{user.id}"),
                    InlineKeyboardButton("❌ رفض", callback_data=f"reject_job_{user.id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            job_request_text = (
                f"💼 *طلب نشر وظيفة جديد*\n"
                f"من: {username} (ID: {user.id})\n\n"
                f"التفاصيل:\n{user_text}"
            )
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=job_request_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            await update.message.reply_text("✅ تم استلام طلب نشر الوظيفة وجاري مراجعته من الإدارة.", reply_markup=MAIN_KEYBOARD)

        elif choice == "🚕 مشاركة المشاوير والمواصلات":
            ride_keyboard = [[InlineKeyboardButton("تواصل مع صاحب المشوار 💬", url=contact_url)]]
            ride_markup = InlineKeyboardMarkup(ride_keyboard)
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🚕 *إعلان مواصلة فوري*\n\n{user_text}\n\n🤖 للتواصل عبر البوت: @AlBalashon\\_services\\_bot",
                parse_mode="Markdown",
                reply_markup=ride_markup
            )
            await update.message.reply_text("✅ تم نشر إعلان المواصلة في القناة بنجاح!", reply_markup=MAIN_KEYBOARD)

        elif choice == "🩸 التبرع بالدم والطوارئ":
            blood_keyboard = [[InlineKeyboardButton("تواصل مع حالة الطوارئ 🩸", url=contact_url)]]
            blood_markup = InlineKeyboardMarkup(blood_keyboard)
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🚨 *نداء طوارئ عاجل - تبرع بالدم* 🚨\n\n{user_text}\n\n🤖 للتواصل عبر البوت: @AlBalashon\\_services\\_bot",
                parse_mode="Markdown",
                reply_markup=blood_markup
            )
            await update.message.reply_text("✅ تم نشر حالة الطوارئ في القناة بنجاح! نسأل الله الشفاء العاجل.", reply_markup=MAIN_KEYBOARD)

        elif choice == "🏠 عقارات وسكن (بيع / إيجار)":
            real_estate_keyboard = [[InlineKeyboardButton("تواصل مع صاحب العقار 📞", url=contact_url)]]
            real_estate_markup = InlineKeyboardMarkup(real_estate_keyboard)
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🏠 *إعلان عقارات وسكن*\n\n{user_text}\n\n🤖 للتواصل عبر البوت: @AlBalashon\\_services\\_bot",
                parse_mode="Markdown",
                reply_markup=real_estate_markup
            )
            # بما أنه كان في قائمة الخدمات، نرجعه لها أو للرئيسية. القائمة الرئيسية أفضل بعد إتمام عملية
            await update.message.reply_text("✅ تم نشر إعلان العقار في القناة بنجاح!", reply_markup=MAIN_KEYBOARD)

        else:
            # خدمات تنشر مباشرة للقناة (مثل المفقودات)
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"📢 *{choice}*\n\n{user_text}\n\n🤖 للتواصل عبر البوت: @AlBalashon\\_services\\_bot",
                parse_mode="Markdown",
            )
            await update.message.reply_text("✅ تم استقبال بياناتك ونشرها بنجاح! شكراً لك.", reply_markup=MAIN_KEYBOARD)

    except Exception as e:
        logger.error("process_input error: %s", e)
        await update.message.reply_text("❌ حدث خطأ أثناء الإرسال. تأكد أن البوت مشرف في القناة.", reply_markup=MAIN_KEYBOARD)

    context.user_data.clear()
    return CHOOSING

# ════════════════════════════════════════════
#  معالج الأزرار الإنلاين (موافقة أو رفض الوظائف)
# ════════════════════════════════════════════

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    admin_msg_text = query.message.text
    
    parts = admin_msg_text.split("التفاصيل:\n", 1)
    if len(parts) > 1:
        job_details = parts[1].strip()
    else:
        job_details = "تفاصيل غير معروفة"

    if data.startswith("approve_job_"):
        user_id = data.split("_")[2]
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"💼 *وظائف خالية*\n\n{job_details}\n\n🤖 للتواصل عبر البوت: @AlBalashon\\_services\\_bot",
                parse_mode="Markdown",
            )
            await context.bot.send_message(chat_id=user_id, text="✅ تم الموافقة على إعلان الوظيفة ونشره في القناة!")
            await query.edit_message_text(text=f"{admin_msg_text}\n\n✅ **تمت الموافقة والنشر.**")
        except Exception as e:
            logger.error("Error approving job: %s", e)
            await query.edit_message_text(text=f"{admin_msg_text}\n\n❌ **حدث خطأ أثناء النشر.**")
            
    elif data.startswith("reject_job_"):
        user_id = data.split("_")[2]
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ نعتذر منك، تم رفض إعلان الوظيفة من قبل الإدارة.")
            await query.edit_message_text(text=f"{admin_msg_text}\n\n❌ **تم الرفض والإلغاء.**")
        except Exception as e:
            logger.error("Error rejecting job: %s", e)

# ════════════════════════════════════════════
#  أوامر الأدمن والأذكار المجدولة
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
        await asyncio.sleep(0.05)

    await status.edit_text(f"✅ أُرسلت لـ {sent} مستخدم.\n❌ فشل لـ {failed} مستخدم.")


async def send_daily_azkar(context: ContextTypes.DEFAULT_TYPE):
    azkar_text = (
        "☀️ *أذكار الصباح | بنية فتح الأبواب والبركة* ☀️\n\n"
        "- سبحان الله\n"
        "- الحمد لله\n"
        "- لا إله إلا الله\n"
        "- صلى الله على محمد، صلى الله عليه وسلم (صلِّ على رسول الله)"
    )
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=azkar_text, parse_mode="Markdown")
    except Exception as e:
        logger.error("Failed to send morning azkar: %s", e)

# ════════════════════════════════════════════
#  الإعداد والتشغيل
# ════════════════════════════════════════════

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إعداد أذكار الصباح يومياً الساعة 6 صباحاً بتوقيت مصر
    tz = datetime.timezone(datetime.timedelta(hours=3))
    t = datetime.time(hour=6, minute=0, tzinfo=tz)
    app.job_queue.run_daily(send_daily_azkar, time=t)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING:     [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
            TYPING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_input)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("stats",      stats))
    app.add_handler(CommandHandler("broadcast",  broadcast))

    logger.info("🚀 AlBalashon Bot started. Send /start to begin.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()