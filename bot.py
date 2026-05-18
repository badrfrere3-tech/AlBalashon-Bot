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
    PicklePersistence,
)

# ─── الإعدادات ───────────────────────────────
BOT_TOKEN  = "8692227293:AAFEqO_5EqAm-jTB7GGnfVMlMh8Ru1iwSeM"
ADMIN_ID   = 5481609181
CHANNEL_ID = "@AlBalashon_Channel"

# متغيرات لمنع تكرار إرسال الأذكار
LAST_MORNING_DATE = None
LAST_EVENING_DATE = None
LAST_FRIDAY_DATE = None

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
    "👂 *الأنف والأذن والحنجرة وتجميل الأنف:*\n"
    "👨‍⚕️ د. أحمد مصطفى خطاب (إستشاري)\n"
    "📍 الطريق الرئيسي - أعلى صيدلية خطاب\n"
    "⏰ السبت، الإثنين، الأربعاء (5 - 9 مساءً)\n"
    "⏰ الأحد، الثلاثاء، الخميس (3 - 5 مساءً)\n"
    "📞 للتواصل: 01022007977\n\n"
    "💧 *مسالك بولية:*\n"
    "👨‍⚕️ د. أسامة الجندي\n"
    "⏰ يومياً (5:00 لـ 11:00 مساءً) عدا الجمعة\n\n"
    "🔬 *الجلدية:*\n"
    "👨‍⚕️ د. عبد الرحمن\n"
    "📍 عمارة الأطباء\n\n"
    "🔪 *الجراحة العامة:*\n"
    "👨‍⚕️ د. إسلام جمال هندي\n"
    "⏰ كل يوم عدا الإثنين (5:00 لـ 10:00 مساءً)\n\n"
    "🚨 *طوارئ (24 ساعة):*\n"
    "👨‍⚕️ د. عبد الله نبيل\n"
    "📞 هاتفياً: 01130396842\n"
    "💬 واتساب: 01069431963\n"
)

DEVELOPER_TEXT = (
    "🏅 *Captain & Engineer: Badr Frere*\n"
    "----------------------------------------\n"
    "💪 *[الجانب الرياضي والصحي]:*\n"
    "• التخصص: مدرب فيتنس وكوتش تغذية محترف (Professional Nutritionist).\n"
    "• المقر الحالي: أكاديمية جروكسي (Goroxi Academy) - العاشر من رمضان.\n"
    "• الخدمات: تصميم برامج تدريبية، خطط تغذية علمية وحساب ماكروز للتخسيس أو التضخيم.\n\n"
    "💻 *[الجانب التقني والبرمجي]:*\n"
    "• التخصص: Front-End Developer\n"
    "• الخدمات المتاحة لأصحاب الأعمال والمشاريع:\n"
    "  - تصميم وتطوير مواقع احترافية للبرندات والشركات.\n"
    "  - بناء أنظمة كاشير وإدارة ومبيعات متكاملة (ERP Systems).\n"
    "  - تطوير سيستم كامل لإدارة الشركات التدريبية والأكاديميات.\n\n"
    "📞 *رقم التواصل والواتساب المباشر:* 01020549760\n"
    "----------------------------------------\n"
)

EMERGENCY_PHARMACY_INFO = (
    "👨‍⚕️ *صيدلية الطوارئ الليلة بالبلاشون هي:* صيدلية دكتور إبراهيم مصطفى خضر\n"
    "📍 *العنوان:* بجوار مسجد تلعب\n"
    "📞 *للتواصل:* 01002707560\n\n"
    "⏰ *الشيفت مستمر حتى الساعة 3 صباحاً*"
)

EMERGENCY_DOCTOR_TEXT = (
    "🚨 *د/ عبد الله نبيل (طبيب طوارئ 24 ساعة)*\n\n"
    "• أرقام التواصل الفوري:\n"
    "📞 اتصال مباشر: 01130396842\n"
    "💬 واتساب: 01069431963"
)

EVENING_AZKAR_TEXT = (
    "أَعُوذُ بِاللهِ مِنْ الشَّيْطَانِ الرَّجِيمِ\n"
    "{اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ لاَ تَأْخُذُهُ سِنَةٌ وَلاَ نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلاَّ بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلاَ يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلاَّ بِمَا شَاء وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالأَرْضَ وَلاَ يَؤُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ}"
)

FRIDAY_KAHF_TEXT = (
    "✨ *لا تنسوا قراءة سورة الكهف* ✨\n"
    "----------------------------------------\n"
    "💡 *[من فضائل سورة الكهف]*:\n"
    "• *نورٌ بين الجمعتين:* قال رسول الله ﷺ: \"من قرأ سورة الكهف في يوم الجمعة، أضاء له من النور ما بين الجمعتين\".\n"
    "• *عصمة من الفتن:* تقي قاريء أول عشر آيات منها من فتنة الدجّال.\n"
    "• *طمأنينة وسكينة:* تنزل السكينة والرحمة على قارئها وتملأ بيته بالبركة.\n\n"
    "نور الله جمعتكم بكل خير وبركة 🤍\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon_services_bot"
)

DELIVERY_TEXT = "⏳ *هذه الميزة ستتوفر قريباً...*"

STAR_METAL_TEXT = (
    "🪟 *معرض استار ميتال للألوميتال*\n\n"
    "🏢 *اسم المعرض:* معرض استار ميتال للألوميتال\n"
    "👤 *صاحب المعرض:* محمود عبدالعظيم سعد\n"
    "📞 *رقم التواصل:* 01014770786"
)

TUKTUK_TEXT = (
    "🛺 *دليل سائقي التوك توك بالبلاشون:*\n\n"
    "👤 *الطالب:* كريم عماد\n"
    "• السن: 19 سنة\n"
    "📞 *رقم التواصل:* 01090305795\n"
)

RESTAURANTS_TEXT = (
    "🍔 *قائمة المطاعم بالبلاشون:*\n\n"
    "🍕 *مطعم أبو صلاح*\n"
    "▪️ *نوع الأكل:* بيتزا - كريب - برجر\n"
    "📞 *رقم التواصل:* 01030666675\n\n"
    "🍔 *مطعم أبو حنين*\n"
    "📍 *العنوان:* حفنا\n"
    "▪️ *نوع الأكل:* برجر - كريب\n"
    "📞 *رقم التواصل:* 01009751224\n\n"
    "🍟 *مطعم Viva Food*\n"
    "📍 *العنوان:* البلاشون\n"
    "▪️ *نوع الأكل:* كريب\n"
    "📞 *رقم التواصل:* 01094318213\n\n"
    "🥩 *مطعم أحمد*\n"
    "📍 *العنوان:* البلاشون\n"
    "▪️ *نوع الأكل:* مشويات - حواوشي\n"
    "📞 *أرقام التواصل:*\n"
    "📱 01006586263\n"
    "☎️ 0552805570"
)

PITCH_TEXT = (
    "🏟️ *ملعب البلاشون الخماسي*\n\n"
    "👤 *المسؤول عن الحجز:* أبو كريم\n"
    "📞 *رقم التواصل:* 01020840251"
)

# ─── لوحات المفاتيح ──────────────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 حالات عاجلة"],
        ["📦 أبلغ عن مفقود / أمانة", "📢 إعلان منتج / خدماتنا"],
        ["🚕 مشاركة المشاوير والمواصلات", "💼 وظائف خالية"],
        ["🛠️ الخدمات", "🩺 دليل الأطباء والعيادات"],
        ["➕ أضف عملك", "🛺 اطلب توك توك"],
        ["💻 مصمم البوت"]
    ],
    resize_keyboard=True,
)

URGENT_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🤝 طلب مساعدة", "🚨 طبيب طوارئ (24 ساعة)"],
        ["🏥 صيدليات الطوارئ الليلة", "🩸 التبرع بالدم والطوارئ"],
        ["🔙 رجوع للقائمة الرئيسية"]
    ],
    resize_keyboard=True,
)

SERVICES_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🏟️ حجز ملعب البلاشون", "🍔 مطاعم"],
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

    if "رجوع" in text:
        await update.message.reply_text("القائمة الرئيسية:", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    if "الخدمات" in text and not "الشحن" in text:
        await update.message.reply_text("اختر الخدمة المطلوبة من القائمة:", reply_markup=SERVICES_KEYBOARD)
        return ConversationHandler.END

    if "حالات عاجلة" in text:
        await update.message.reply_text("اختر الخدمة المطلوبة من القائمة:", reply_markup=URGENT_KEYBOARD)
        return ConversationHandler.END

    if "دليل الأطباء" in text:
        doctors_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 تواصل مع د. خطاب (واتساب)", url="https://wa.me/201022007977")],
            [InlineKeyboardButton("💬 طوارئ د. عبدالله (واتساب)", url="https://wa.me/201069431963")]
        ])
        await update.message.reply_text(DOCTORS_TEXT, parse_mode="Markdown", reply_markup=doctors_markup)
        return ConversationHandler.END

    if "مصمم البوت" in text:
        developer_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💻 تواصل مع مصمم البوت (واتساب)", url="https://wa.me/201020549760")]
        ])
        await update.message.reply_text(DEVELOPER_TEXT, parse_mode="Markdown", reply_markup=developer_markup)
        return ConversationHandler.END
        
    if "توك توك" in text:
        tuktuk_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 تواصل مع كريم (واتساب)", url="https://wa.me/201090305795")]
        ])
        await update.message.reply_text(TUKTUK_TEXT, parse_mode="Markdown", reply_markup=tuktuk_markup)
        return ConversationHandler.END
        
    elif "مطاعم" in text:
        restaurants_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🍕 أبو صلاح", url="https://wa.me/201030666675"),
             InlineKeyboardButton("🍔 أبو حنين", url="https://wa.me/201009751224")],
            [InlineKeyboardButton("🍟 Viva Food", url="https://wa.me/201094318213"),
             InlineKeyboardButton("🥩 مطعم أحمد", url="https://wa.me/201006586263")]
        ])
        await update.message.reply_text(RESTAURANTS_TEXT, parse_mode="Markdown", reply_markup=restaurants_markup)
        return ConversationHandler.END

    elif "ملعب البلاشون" in text or "حجز ملعب" in text:
        contact_keyboard = [[InlineKeyboardButton("تواصل للحجز عبر واتساب 💬", url="https://wa.me/201020840251")]]
        contact_markup = InlineKeyboardMarkup(contact_keyboard)
        await update.message.reply_text(PITCH_TEXT, parse_mode="Markdown", reply_markup=contact_markup)
        return ConversationHandler.END

    elif "استار ميتال" in text:
        contact_keyboard = [[InlineKeyboardButton("تواصل عبر واتساب 💬", url="https://wa.me/201014770786")]]
        contact_markup = InlineKeyboardMarkup(contact_keyboard)
        await update.message.reply_text(STAR_METAL_TEXT, parse_mode="Markdown", reply_markup=contact_markup)
        return ConversationHandler.END

    elif "طوارئ الليلة" in text or "صيدليات" in text:
        contact_keyboard = [[InlineKeyboardButton("تواصل عبر واتساب 💬", url="https://wa.me/201002707560")]]
        contact_markup = InlineKeyboardMarkup(contact_keyboard)
        await update.message.reply_text(EMERGENCY_PHARMACY_INFO, parse_mode="Markdown", reply_markup=contact_markup)
        return ConversationHandler.END

    elif "طبيب طوارئ" in text:
        contact_keyboard = [[InlineKeyboardButton("💬 تواصل طوارئ (واتساب)", url="https://wa.me/201069431963")]]
        contact_markup = InlineKeyboardMarkup(contact_keyboard)
        await update.message.reply_text(EMERGENCY_DOCTOR_TEXT, parse_mode="Markdown", reply_markup=contact_markup)
        return ConversationHandler.END
        
    elif "الشحن والتوصيل" in text:
        await update.message.reply_text(DELIVERY_TEXT, parse_mode="Markdown")
        return ConversationHandler.END

    elif "إعلان منتج" in text:
        keyboard = [[InlineKeyboardButton("تواصل معنا 💬", url="https://wa.me/201020549760")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "مرحباً بك في قسم الإعلانات. للحجز يرجى التواصل عبر الواتساب",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # --- إضافة عمل ---
    elif "أضف عملك" in text:
        await update.message.reply_text("الرجاء كتابة بيانات عملك في رسالة واحدة (الاسم، التخصص الدقيق، رقم التليفون، العنوان):")
        return TYPING_INPUT

    # --- الردود التي تتطلب إدخال بيانات ---
    elif "التبرع بالدم" in text:
        await update.message.reply_text("🩸 اكتب تفاصيل الحالة الحرجة فوراً (مثال: الفصيلة، المستشفى، رقم التواصل):")
        return TYPING_INPUT

    elif "وظائف" in text:
        await update.message.reply_text("💼 اكتب تفاصيل الوظيفة (التخصص، المرتب، رقم التواصل):")
        return TYPING_INPUT

    elif "طلب مساعدة" in text:
        await update.message.reply_text("🚨 اكتب تفاصيل طلب المساعدة أو الاستغاثة ورقم التواصل:")
        return TYPING_INPUT

    elif "مفقود" in text or "أمانة" in text:
        await update.message.reply_text("📦 اكتب مواصفات الشيء المفقود، ومكان التواجد:")
        return TYPING_INPUT
        
    elif "مشاوير" in text or "مواصلات" in text:
        await update.message.reply_text("🚕 اكتب تفاصيل مشوارك (سواق ولا راكب، والميعاد):")
        return TYPING_INPUT
        
    elif "عقارات" in text or "سكن" in text:
        await update.message.reply_text("🏠 اكتب تفاصيل العقار (بيع/إيجار، السعر، والمواصفات):")
        return TYPING_INPUT

    else:
        # نص غير معروف
        await update.message.reply_text("اختر خدمة من القائمة 👇", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

# ════════════════════════════════════════════
#  معالج النص المُدخَل (نظام المراجعة الشامل)
# ════════════════════════════════════════════
async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text or update.message.caption or ""
    photo_file_id = update.message.photo[-1].file_id if update.message.photo else None
    
    if user_text in ["🔙 رجوع للقائمة الرئيسية"]:
        await update.message.reply_text("القائمة الرئيسية:", reply_markup=MAIN_KEYBOARD)
        context.user_data.clear()
        return ConversationHandler.END

    KNOWN = ["🚨 حالات عاجلة", "🏥 صيدليات الطوارئ الليلة", "🩸 التبرع بالدم والطوارئ",
             "🤝 طلب مساعدة", "🚨 طبيب طوارئ (24 ساعة)", "📦 أبلغ عن مفقود / أمانة", "📢 إعلان منتج / خدماتنا", 
             "🚕 مشاركة المشاوير والمواصلات", "💼 وظائف خالية", "🛠️ الخدمات", 
             "🩺 دليل الأطباء والعيادات", "🪟 معرض استار ميتال للألوميتال",
             "📦 خدمات الشحن والتوصيل (الطيارين)", "🏠 عقارات وسكن (بيع / إيجار)", "➕ أضف عملك",
             "🛺 اطلب توك توك", "💻 مصمم البوت", "🔙 رجوع للقائمة الرئيسية", 
             "📦 أبلغ عن مفقود", "🏠 عقارات وسكن", "🚕 مشاركة المشاوير", "🛠 الخدمات", "🍔 مطاعم", "🏟️ حجز ملعب البلاشون"]
             
    if user_text in KNOWN:
        context.user_data.clear()
        return await handle_choice(update, context)

    choice    = context.user_data.get("choice", "")
    user      = update.effective_user
    username  = f"@{user.username}" if user.username else str(user.id)

    try:
        # 1. نظام إرسال الأعمال الخاصة للإدارة بدون نشر
        if "أضف عملك" in choice:
            admin_msg = (
                f"📌 *طلب إضافة عمل جديد:*\n\n"
                f"- البيانات: {user_text}\n"
                f"- حساب المرسل: {username}"
            )
            if photo_file_id: await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=admin_msg, parse_mode="Markdown")
            else: await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
            await update.message.reply_text("✅ تم إرسال بياناتك للإدارة بنجاح! سيتم مراجعتها والتواصل معك قريباً.", reply_markup=MAIN_KEYBOARD)

        # 2. نظام طلبات النشر الموحد في القناة
        else:
            action_code = ""
            action_name = ""
            
            if "طلب مساعدة" in choice:
                action_code = "sos"
                action_name = "طلب مساعدة / استغاثة"
            elif "وظائف" in choice:
                action_code = "job"
                action_name = "وظيفة"
            elif "مشاركة المشاوير" in choice or "المواصلات" in choice:
                action_code = "ride"
                action_name = "مواصلة"
            elif "التبرع بالدم" in choice:
                action_code = "blood"
                action_name = "تبرع بالدم"
            elif "عقارات" in choice:
                action_code = "real"
                action_name = "إعلان عقارات"
            elif "مفقود" in choice or "أمانة" in choice:
                action_code = "lost"
                action_name = "مفقودات"
                
            if action_code:
                markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ موافقة ونشر", callback_data=f"app_{action_code}_{user.id}"),
                    InlineKeyboardButton("❌ رفض الطلب", callback_data=f"rej_{action_code}_{user.id}")
                ]])
                req = f"🔔 *طلب نشر ({action_name})*\nمن: {username}\n\nالتفاصيل:\n{user_text}"
                
                if photo_file_id: await context.bot.send_photo(ADMIN_ID, photo_file_id, caption=req, parse_mode="Markdown", reply_markup=markup)
                else: await context.bot.send_message(ADMIN_ID, text=req, parse_mode="Markdown", reply_markup=markup)
                
                await update.message.reply_text(f"✅ تم إرسال طلب نشر ({action_name}) للإدارة، وسيتم نشره فور الموافقة عليه.", reply_markup=MAIN_KEYBOARD)
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
    
    # استخراج اسم المشرف الذي قام بالعملية
    admin_user = update.effective_user.username or update.effective_user.first_name
    
    parts = admin_msg_text.split("التفاصيل:\n", 1)
    details = parts[1].strip() if len(parts) > 1 else "تفاصيل غير معروفة"

    # --- الرفض الموحد ---
    if data.startswith("rej_"):
        user_id = data.split("_")[2]
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ نعتذر، تم رفض طلب النشر من قبل الإدارة.")
            if photo_file_id: await query.edit_message_caption(caption=f"{admin_msg_text}\n\n❌ **تم الرفض بواسطة {admin_user}.**", parse_mode="Markdown")
            else: await query.edit_message_text(text=f"{admin_msg_text}\n\n❌ **تم الرفض بواسطة {admin_user}.**", parse_mode="Markdown")
        except: pass
        return

    # --- الموافقة والنشر الموحد ---
    if data.startswith("app_"):
        action = data.split("_")[1]
        user_id = data.split("_")[2]
        contact_url = f"tg://user?id={user_id}"

        markup = None
        if action == "sos":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع الحالة 🚨", url=contact_url)]])
            text_to_send = f"🚨 *استغاثة عاجلة*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon_services_bot"
        elif action == "blood":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع حالة الطوارئ 🩸", url=contact_url)]])
            text_to_send = f"🚨 *نداء طوارئ عاجل - تبرع بالدم* 🚨\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon_services_bot"
        elif action == "ride":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع صاحب المشوار 💬", url=contact_url)]])
            text_to_send = f"🚕 *إعلان مواصلة فوري*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon_services_bot"
        elif action == "lost":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل للإبلاغ 💬", url=contact_url)]])
            text_to_send = f"📢 *مفقودات وأمانات*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon_services_bot"
        elif action == "job":
            text_to_send = f"💼 *وظائف خالية*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon_services_bot"
        elif action == "real":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع المالك 📞", url=contact_url)]])
            text_to_send = f"🏠 *إعلان عقارات وسكن*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon_services_bot"
        else:
            return

        try:
            if photo_file_id:
                if markup: await context.bot.send_photo(CHANNEL_ID, photo_file_id, caption=text_to_send, parse_mode="Markdown", reply_markup=markup)
                else: await context.bot.send_photo(CHANNEL_ID, photo_file_id, caption=text_to_send, parse_mode="Markdown")
            else:
                if markup: await context.bot.send_message(CHANNEL_ID, text=text_to_send, parse_mode="Markdown", reply_markup=markup)
                else: await context.bot.send_message(CHANNEL_ID, text=text_to_send, parse_mode="Markdown")
            
            await context.bot.send_message(chat_id=user_id, text="✅ تمت الموافقة على طلبك ونشره في القناة بنجاح!")
            if photo_file_id: await query.edit_message_caption(caption=f"{admin_msg_text}\n\n✅ **نُشر بواسطة {admin_user}.**", parse_mode="Markdown")
            else: await query.edit_message_text(text=f"{admin_msg_text}\n\n✅ **نُشر بواسطة {admin_user}.**", parse_mode="Markdown")
        except Exception as e:
            logger.error(e)
            if photo_file_id: await query.edit_message_caption(caption=f"{admin_msg_text}\n\n❌ **حدث خطأ أثناء النشر.**", parse_mode="Markdown")
            else: await query.edit_message_text(text=f"{admin_msg_text}\n\n❌ **حدث خطأ أثناء النشر.**", parse_mode="Markdown")

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
    global LAST_MORNING_DATE
    now_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date()
    if LAST_MORNING_DATE == now_date:
        return
    LAST_MORNING_DATE = now_date

    azkar_text = (
        "☀️ *أذكار الصباح | بنية فتح الأبواب والبركة* ☀️\n\n"
        "- سبحان الله\n- الحمد لله\n- لا إله إلا الله\n"
        "- صلى الله على محمد، صلى الله عليه وسلم (صلِّ على رسول الله)"
    )
    try: await context.bot.send_message(CHANNEL_ID, azkar_text, parse_mode="Markdown")
    except Exception: pass

async def send_daily_evening_azkar(context: ContextTypes.DEFAULT_TYPE):
    global LAST_EVENING_DATE
    now_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date()
    if LAST_EVENING_DATE == now_date:
        return
    LAST_EVENING_DATE = now_date

    try: await context.bot.send_message(CHANNEL_ID, f"🌆 *أذكار المساء*\n\n{EVENING_AZKAR_TEXT}", parse_mode="Markdown")
    except Exception: pass

async def send_friday_reminder(context: ContextTypes.DEFAULT_TYPE):
    global LAST_FRIDAY_DATE
    now_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date()
    if LAST_FRIDAY_DATE == now_date:
        return
    LAST_FRIDAY_DATE = now_date

    try: await context.bot.send_message(CHANNEL_ID, FRIDAY_KAHF_TEXT, parse_mode="Markdown")
    except Exception: pass

# ════════════════════════════════════════════
#  الإعداد والتشغيل
# ════════════════════════════════════════════
def main():
    init_db()
    persistence = PicklePersistence(filepath="albalashon_state.pickle")
    app = Application.builder().token(BOT_TOKEN).persistence(persistence).build()
    
    tz = datetime.timezone(datetime.timedelta(hours=3))
    t_morning = datetime.time(hour=6, minute=0, tzinfo=tz)
    app.job_queue.run_daily(send_daily_azkar, time=t_morning)
    
    t_evening = datetime.time(hour=20, minute=0, tzinfo=tz)
    app.job_queue.run_daily(send_daily_evening_azkar, time=t_evening)

    t_friday = datetime.time(hour=8, minute=0, tzinfo=tz)
    app.job_queue.run_daily(send_friday_reminder, time=t_friday, days=(4,))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice),
        ],
        states={
            TYPING_INPUT: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, process_input)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=False,
        name="main_conversation",
        persistent=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    logger.info("🚀 AlBalashon Bot started. Send /start to begin.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()