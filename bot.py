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

# ─── مراحل المحادثة ──────────────────────────
TYPING_INPUT = 1

# ─── نصوص ثابتة (يمكنك تعديلها لاحقاً) ────────
DOCTORS_TEXT = (
    "🩺 *دليل الأطباء والعيادات بالبلاشون:*\n\n"
    "🩺 *الباطنة والجهاز الهضمي:*\n"
    "👨‍⚕️ د. فاروق دياب\n"
    "⏰ السبت للخميس (6:00 لـ 10:00 مساءً)\n"
    "📞 للتواصل: 0552801193\n\n"
    "🫀 *القلب والباطنة والصدر:*\n"
    "👨‍⚕️ د. محمد حسني\n"
    "📞 التواصل: 01067682611\n\n"
    "🧠 *المخ والأعصاب:*\n"
    "👨‍⚕️ د. أحمد صلاح\n"
    "📍 أعلى صيدلية دكتور شكري\n"
    "⏰ الإثنين للخميس (4:00 لـ 8:00 مساءً)\n\n"
    "👂 *الأنف والأذن والحنجرة:*\n"
    "👨‍⚕️ د. أحمد طارق مصطفى\n"
    "📍 أعلى صيدلية خطاب\n\n"
    "🔬 *الجلدية:*\n"
    "👨‍⚕️ د. عبد الرحمن\n"
    "📍 عمارة الأطباء\n\n"
    "🔪 *الجراحة العامة:*\n"
    "👨‍⚕️ د. إسلام جمال هندي\n"
    "⏰ كل يوم عدا الإثنين (5:00 لـ 10:00 مساءً)\n"
)

EMERGENCY_PHARMACY_INFO = (
    "👨‍⚕️ *صيدلية الطوارئ الليلة بالبلاشون هي:* [اسم الصيدلية تجريبي]\n"
    "📍 *العنوان:* [مكان الصيدلية بالظبط]\n"
    "📞 *للتواصل والدليفري:* [رقم التليفون أو الموبايل]\n\n"
    "⏰ *الشيفت مستمر حتى الساعة 8 صباحاً*"
)

DELIVERY_TEXT = "📦 *خدمات الشحن والتوصيل (الطيارين):* (الاسم والرقم)"

STAR_METAL_TEXT = (
    "🪟 *معرض استار ميتال للألوميتال*\n\n"
    "🏢 *اسم المعرض:* معرض استار ميتال للألوميتال\n"
    "👤 *صاحب المعرض:* محمود عبدالعظيم سعد\n"
    "📞 *رقم التواصل:* 01014770786"
)

# ─── لوحات المفاتيح ──────────────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 إرسال استغاثة / حالة عاجلة"],
        ["🏥 صيدليات الطوارئ الليلة", "🩸 التبرع بالدم والطوارئ"],
        ["📦 أبلغ عن مفقود / أمانة", "📢 إعلان منتج / خدماتنا"],
        ["🚕 مشاركة المشاوير والمواصلات", "💼 وظائف خالية"],
        ["🛠️ الخدمات", "🩺 دليل الأطباء والعيادات"],
        ["➕ أضف عملك"]
    ],
    resize_keyboard=True,
)

SERVICES_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📦 خدمات الشحن والتوصيل (الطيارين)"],
        ["🏠 عقارات وسكن (بيع / إيجار)"],
        ["🪟 معرض استار ميتال للألوميتال"],
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
    user_id = update.effective_user.id
    register_user(user_id)
    await update.message.reply_text(
        "💡 مرحباً بك في منصة خدمات البلاشون الذكية.\nاختر الخدمة المطلوبة من الأزرار بالأسفل:",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END

# ════════════════════════════════════════════
#  معالج اختيارات القوائم
# ════════════════════════════════════════════
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text

    if text == "🔙 رجوع للقائمة الرئيسية":
        await update.message.reply_text("القائمة الرئيسية:", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    if text == "🛠️ الخدمات":
        await update.message.reply_text("اختر الخدمة المطلوبة من القائمة:", reply_markup=SERVICES_KEYBOARD)
        return ConversationHandler.END

    if text == "🩺 دليل الأطباء والعيادات":
        await update.message.reply_text(DOCTORS_TEXT, parse_mode="Markdown")
        return ConversationHandler.END
        
    elif text == "🪟 معرض استار ميتال للألوميتال":
        contact_keyboard = [[InlineKeyboardButton("تواصل عبر واتساب 💬", url="https://wa.me/201014770786")]]
        contact_markup = InlineKeyboardMarkup(contact_keyboard)
        await update.message.reply_text(STAR_METAL_TEXT, parse_mode="Markdown", reply_markup=contact_markup)
        return ConversationHandler.END

    elif text == "🏥 صيدليات الطوارئ الليلة":
        await update.message.reply_text(EMERGENCY_PHARMACY_INFO, parse_mode="Markdown")
        return ConversationHandler.END
        
    elif text == "📦 خدمات الشحن والتوصيل (الطيارين)":
        await update.message.reply_text(DELIVERY_TEXT, parse_mode="Markdown")
        return ConversationHandler.END

    elif text == "📢 إعلان منتج / خدماتنا":
        keyboard = [[InlineKeyboardButton("تواصل معنا 💬", url="https://wa.me/201020549760")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "مرحباً بك في قسم الإعلانات. للحجز يرجى التواصل عبر الواتساب",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # --- إضافة عمل ---
    elif text == "➕ أضف عملك":
        await update.message.reply_text("الرجاء كتابة بيانات عملك في رسالة واحدة (الاسم، التخصص الدقيق، رقم التليفون، العنوان):")
        return TYPING_INPUT

    # --- الردود التي تتطلب إدخال بيانات ---
    elif text == "🩸 التبرع بالدم والطوارئ":
        await update.message.reply_text("🩸 اكتب تفاصيل الحالة الحرجة فوراً (مثال: الفصيلة، المستشفى، رقم التواصل):")
        return TYPING_INPUT

    elif text == "💼 وظائف خالية":
        await update.message.reply_text("💼 اكتب تفاصيل الوظيفة (التخصص، المرتب، رقم التواصل):")
        return TYPING_INPUT

    elif text == "🚨 إرسال استغاثة / حالة عاجلة":
        await update.message.reply_text("🚨 اكتب تفاصيل الاستغاثة ورقم التواصل:")
        return TYPING_INPUT

    elif text == "📦 أبلغ عن مفقود / أمانة":
        await update.message.reply_text("📦 اكتب مواصفات الشيء المفقود، ومكان التواجد:")
        return TYPING_INPUT
        
    elif text == "🚕 مشاركة المشاوير والمواصلات":
        await update.message.reply_text("🚕 اكتب تفاصيل مشوارك (سواق ولا راكب، والميعاد):")
        return TYPING_INPUT
        
    elif text == "🏠 عقارات وسكن (بيع / إيجار)":
        await update.message.reply_text("🏠 اكتب تفاصيل العقار (بيع/إيجار، السعر، والمواصفات):")
        return TYPING_INPUT

    else:
        # نص غير معروف
        await update.message.reply_text("اختر خدمة من القائمة 👇", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

# ════════════════════════════════════════════
#  معالج النص المُدخَل
# ════════════════════════════════════════════
async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text or update.message.caption or ""
    photo_file_id = update.message.photo[-1].file_id if update.message.photo else None
    
    if user_text in ["🔙 رجوع للقائمة الرئيسية"]:
        await update.message.reply_text("القائمة الرئيسية:", reply_markup=MAIN_KEYBOARD)
        context.user_data.clear()
        return ConversationHandler.END

    KNOWN = ["🚨 إرسال استغاثة / حالة عاجلة", "🏥 صيدليات الطوارئ الليلة", "🩸 التبرع بالدم والطوارئ",
             "📦 أبلغ عن مفقود / أمانة", "📢 إعلان منتج / خدماتنا", "🚕 مشاركة المشاوير والمواصلات",
             "💼 وظائف خالية", "🛠️ الخدمات", "🩺 دليل الأطباء والعيادات", "🪟 معرض استار ميتال للألوميتال",
             "📦 خدمات الشحن والتوصيل (الطيارين)", "🏠 عقارات وسكن (بيع / إيجار)", "➕ أضف عملك"]
             
    if user_text in KNOWN:
        context.user_data.clear()
        return await handle_choice(update, context)

    choice    = context.user_data.get("choice", "")
    user      = update.effective_user
    username  = f"@{user.username}" if user.username else str(user.id)
    contact_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    try:
        if choice == "🚨 إرسال استغاثة / حالة عاجلة":
            sos_markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع الحالة 🚨", url=contact_url)]])
            text_to_send = f"🚨 *استغاثة عاجلة*\n\n{user_text}\n\n🤖 للتواصل عبر البوت: @AlBalashon_services_bot"
            if photo_file_id: await context.bot.send_photo(CHANNEL_ID, photo_file_id, caption=text_to_send, parse_mode="Markdown", reply_markup=sos_markup)
            else: await context.bot.send_message(CHANNEL_ID, text=text_to_send, parse_mode="Markdown", reply_markup=sos_markup)
            await update.message.reply_text("✅ تم النشر.", reply_markup=MAIN_KEYBOARD)

        elif choice == "💼 وظائف خالية":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("✅ موافقة ونشر", callback_data=f"approve_job_{user.id}"), InlineKeyboardButton("❌ رفض", callback_data=f"reject_job_{user.id}")]])
            job_req = f"💼 *طلب نشر وظيفة*\nمن: {username}\n\nالتفاصيل:\n{user_text}"
            if photo_file_id: await context.bot.send_photo(ADMIN_ID, photo_file_id, caption=job_req, parse_mode="Markdown", reply_markup=markup)
            else: await context.bot.send_message(ADMIN_ID, text=job_req, parse_mode="Markdown", reply_markup=markup)
            await update.message.reply_text("✅ تم الإرسال للإدارة.", reply_markup=MAIN_KEYBOARD)

        elif choice == "🚕 مشاركة المشاوير والمواصلات":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع صاحب المشوار 💬", url=contact_url)]])
            text_to_send = f"🚕 *إعلان مواصلة فوري*\n\n{user_text}\n\n🤖 للتواصل عبر البوت: @AlBalashon_services_bot"
            if photo_file_id: await context.bot.send_photo(CHANNEL_ID, photo_file_id, caption=text_to_send, parse_mode="Markdown", reply_markup=markup)
            else: await context.bot.send_message(CHANNEL_ID, text=text_to_send, parse_mode="Markdown", reply_markup=markup)
            await update.message.reply_text("✅ تم النشر!", reply_markup=MAIN_KEYBOARD)

        elif choice == "🩸 التبرع بالدم والطوارئ":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع حالة الطوارئ 🩸", url=contact_url)]])
            text_to_send = f"🚨 *نداء طوارئ عاجل - تبرع بالدم* 🚨\n\n{user_text}\n\n🤖 للتواصل عبر البوت: @AlBalashon_services_bot"
            if photo_file_id: await context.bot.send_photo(CHANNEL_ID, photo_file_id, caption=text_to_send, parse_mode="Markdown", reply_markup=markup)
            else: await context.bot.send_message(CHANNEL_ID, text=text_to_send, parse_mode="Markdown", reply_markup=markup)
            await update.message.reply_text("✅ تم النشر! نسأل الله الشفاء.", reply_markup=MAIN_KEYBOARD)

        elif choice == "🏠 عقارات وسكن (بيع / إيجار)":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("✅ موافقة ونشر", callback_data=f"approve_realestate_{user.id}"), InlineKeyboardButton("❌ رفض", callback_data=f"reject_realestate_{user.id}")]])
            req = f"🏠 *طلب نشر إعلان عقارات وسكن*\nمن: {username}\n\nالتفاصيل:\n{user_text}"
            if photo_file_id: await context.bot.send_photo(ADMIN_ID, photo_file_id, caption=req, parse_mode="Markdown", reply_markup=markup)
            else: await context.bot.send_message(ADMIN_ID, text=req, parse_mode="Markdown", reply_markup=markup)
            await update.message.reply_text("✅ تم الإرسال للإدارة.", reply_markup=MAIN_KEYBOARD)

        elif choice == "➕ أضف عملك":
            admin_msg = (
                f"📌 *طلب إضافة جديد:*\n\n"
                f"- البيانات: {user_text}\n"
                f"- حساب المرسل: {username}"
            )
            if photo_file_id:
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=admin_msg, parse_mode="Markdown")
            else:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
            
            await update.message.reply_text("✅ تم إرسال بياناتك للإدارة بنجاح! سيتم مراجعتها والتواصل معك قريباً.", reply_markup=MAIN_KEYBOARD)

        else:
            if choice:
                text_to_send = f"📢 *{choice}*\n\n{user_text}\n\n🤖 للتواصل عبر البوت: @AlBalashon_services_bot"
                if photo_file_id: await context.bot.send_photo(CHANNEL_ID, photo_file_id, caption=text_to_send, parse_mode="Markdown")
                else: await context.bot.send_message(CHANNEL_ID, text=text_to_send, parse_mode="Markdown")
                await update.message.reply_text("✅ تم النشر بنجاح!", reply_markup=MAIN_KEYBOARD)
            else:
                await update.message.reply_text("اختر خدمة من القائمة 👇", reply_markup=MAIN_KEYBOARD)

    except Exception as e:
        logger.error("process_input error: %s", e)
        await update.message.reply_text("❌ حدث خطأ.", reply_markup=MAIN_KEYBOARD)

    context.user_data.clear()
    return ConversationHandler.END


# ════════════════════════════════════════════
#  معالج الأزرار الإنلاين العالمية للإدارة
# ════════════════════════════════════════════
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    admin_msg = query.message
    admin_msg_text = admin_msg.text or admin_msg.caption or ""
    photo_file_id = admin_msg.photo[-1].file_id if admin_msg.photo else None
    
    parts = admin_msg_text.split("التفاصيل:\n", 1)
    details = parts[1].strip() if len(parts) > 1 else "تفاصيل غير معروفة"

    # --- Jobs ---
    if data.startswith("approve_job_"):
        user_id = data.split("_")[2]
        try:
            text_to_send = f"💼 *وظائف خالية*\n\n{details}\n\n🤖 للتواصل عبر البوت: @AlBalashon_services_bot"
            if photo_file_id: await context.bot.send_photo(CHANNEL_ID, photo_file_id, caption=text_to_send, parse_mode="Markdown")
            else: await context.bot.send_message(CHANNEL_ID, text=text_to_send, parse_mode="Markdown")
            
            await context.bot.send_message(chat_id=user_id, text="✅ تم الموافقة على إعلان الوظيفة ونشره!")
            if photo_file_id: await query.edit_message_caption(caption=f"{admin_msg_text}\n\n✅ **تم النشر.**")
            else: await query.edit_message_text(text=f"{admin_msg_text}\n\n✅ **تم النشر.**")
        except Exception as e: logger.error(e)
            
    elif data.startswith("reject_job_"):
        user_id = data.split("_")[2]
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ تم رفض إعلان الوظيفة.")
            if photo_file_id: await query.edit_message_caption(caption=f"{admin_msg_text}\n\n❌ **مرفوض.**")
            else: await query.edit_message_text(text=f"{admin_msg_text}\n\n❌ **مرفوض.**")
        except: pass

    # --- Real estate ---
    elif data.startswith("approve_realestate_"):
        user_id = data.split("_")[2]
        try:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع المالك 📞", url=f"tg://user?id={user_id}")]])
            text_to_send = f"🏠 *إعلان عقارات وسكن*\n\n{details}\n\n🤖 للتواصل عبر البوت: @AlBalashon_services_bot"
            if photo_file_id: await context.bot.send_photo(CHANNEL_ID, photo_file_id, caption=text_to_send, parse_mode="Markdown", reply_markup=markup)
            else: await context.bot.send_message(CHANNEL_ID, text=text_to_send, parse_mode="Markdown", reply_markup=markup)
            
            await context.bot.send_message(chat_id=user_id, text="✅ تم نشر إعلان العقار!")
            if photo_file_id: await query.edit_message_caption(caption=f"{admin_msg_text}\n\n✅ **تم النشر.**")
            else: await query.edit_message_text(text=f"{admin_msg_text}\n\n✅ **تم النشر.**")
        except Exception as e: logger.error(e)
            
    elif data.startswith("reject_realestate_"):
        user_id = data.split("_")[2]
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ تم رفض إعلان العقار.")
            if photo_file_id: await query.edit_message_caption(caption=f"{admin_msg_text}\n\n❌ **مرفوض.**")
            else: await query.edit_message_text(text=f"{admin_msg_text}\n\n❌ **مرفوض.**")
        except: pass

# ════════════════════════════════════════════
#  أوامر الأدمن والأذكار المجدولة
# ════════════════════════════════════════════
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID: return
    count = get_user_count()
    await update.message.reply_text(f"📊 عدد المشتركين في البوت حالياً: {count} شخص.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return await update.message.reply_text("⚠️ اكتب الرسالة بعد الأمر:\n/broadcast نص الرسالة")
    
    msg = " ".join(context.args)
    users = get_all_user_ids()
    sent = failed = 0
    status = await update.message.reply_text(f"📤 جاري الإرسال إلى {len(users)} مستخدم...")
    
    for uid in users:
        try:
            await context.bot.send_message(uid, f"📢 *تنويه عام:*\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except Exception: failed += 1
        await asyncio.sleep(0.05)
        
    await status.edit_text(f"✅ أُرسلت لـ {sent} مستخدم.\n❌ فشل لـ {failed} مستخدم.")

async def send_daily_azkar(context: ContextTypes.DEFAULT_TYPE):
    azkar_text = (
        "☀️ *أذكار الصباح | بنية فتح الأبواب والبركة* ☀️\n\n"
        "- سبحان الله\n- الحمد لله\n- لا إله إلا الله\n"
        "- صلى الله على محمد، صلى الله عليه وسلم (صلِّ على رسول الله)"
    )
    try: await context.bot.send_message(CHANNEL_ID, azkar_text, parse_mode="Markdown")
    except Exception: pass

# ════════════════════════════════════════════
#  الإعداد والتشغيل
# ════════════════════════════════════════════
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    tz = datetime.timezone(datetime.timedelta(hours=3))
    t = datetime.time(hour=6, minute=0, tzinfo=tz)
    app.job_queue.run_daily(send_daily_azkar, time=t)

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice),
        ],
        states={
            TYPING_INPUT: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, process_input)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    logger.info("🚀 AlBalashon Bot started. Send /start to begin.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()