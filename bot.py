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
ADMIN_ID_2 = 1049124970
ADMINS     = [ADMIN_ID, ADMIN_ID_2]  # قائمة جميع الآدمنز لتوجيه الطلبات
CHANNEL_ID = "@AlBalashon_Channel"

# تم استبدال المتغيرات العامة باستخدام context.bot_data لحفظ الحالة

# ─── مراحل المحادثة ──────────────────────────
WAITING_FOR_REQUEST_DETAILS = 1

# ─── نصوص ثابتة (يمكنك تعديلها لاحقاً) ────────
DOCTORS_TEXT = (
    "🩺 *دليل الأطباء والعيادات بالبلاشون:*\n\n"
    "يرجى اختيار التخصص المطلوب من الأزرار بالأسفل لعرض كافة التفاصيل والمواعيد.\n\n"
    "----------------------------------------\n"
    "🚨 *[ملاحظة هامة]:*\n"
    "• 👨‍⚕️ د/ عبد الله نبيل الشوبكي (طوارئ 24 ساعة)\n"
    "  📞 هاتفياً: 01130396842 | 💬 واتساب: 01069431963\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

DENTISTRY_TEXT = (
    "🦷 *[طب وجراحة الفم والأسنان]*\n"
    "----------------------------------------\n\n"
    "• 👨‍⚕️ د/ محمود حسن (جراحة وتجميل الأسنان)\n"
    "  📍 العنوان: البلاشون - أمام الجامع الكبير.\n"
    "  📅 المواعيد: من السبت إلى الخميس (من 5:00 مساءً إلى 10:00 مساءً).\n"
    "  📞 للتواصل: 0552800010 - 01002992125\n\n"
    "• 👨‍⚕️ د/ سيد مصطفى درويش (الفم والأسنان)\n"
    "  📅 المواعيد: الأحد، الثلاثاء، والخميس (من 1:00 ظهراً إلى 9:00 مساءً).\n"
    "  📞 رقم الموبايل: 01091339445\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

PHYSIO_NUTRITION_TEXT = (
    "🦾 *[العلاج الطبيعي والتغذية]*\n"
    "----------------------------------------\n\n"
    "• 👨‍⚕️ د/ أحمد صقر (أخصائي العلاج الطبيعي، التغذية العلاجية، والحجامة الطبية)\n"
    "  📍 العنوان: البلاشون - مركز بلبيس.\n"
    "  📞 رقم التواصل: 01064348233\n\n"
    "• 👨‍⚕️ د/ أحمد سامي عزام (العلاج الطبيعي، الجلسات المنزلية، والحجامة)\n"
    "  📝 التخصص: حالات الجراحة، الكسور، الجلطات، والمسنين.\n"
    "  📞 أرقام التواصل: 01050915289 - 01113997889\n\n"
    "• 👨‍⚕️ د/ يوسف محمد محمد (أخصائي العلاج الطبيعي - Physiotherapy)\n"
    "  📞 أرقام التواصل: 01004567506 - 01016233543\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

INTERNAL_CARDIO_CHEST_TEXT = (
    "🫁 *[الباطنة والقلب والصدر]*\n"
    "----------------------------------------\n\n"
    "• 👨‍⚕️ د/ فاروق دياب (الباطنة والجهاز الهضمي)\n"
    "  📅 المواعيد: من السبت للخميس (من 6:00 مساءً لـ 10:00 مساءً).\n"
    "  📞 للتواصل: 0552801193\n\n"
    "• 👨‍⚕️ د/ محمد حسني (القلب والباطنة والصدر)\n"
    "  📞 للتواصل: 01067682611\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

OBSTETRICS_GYNECOLOGY_TEXT = (
    "🤰 *[أمراض النساء والتوليد]*\n"
    "----------------------------------------\n\n"
    "• 👩‍⚕️ د/ سهام هجرس (أخصائية النساء والتوليد)\n"
    "  📍 العنوان: أعلى صيدلية الدكتور شكري محمد - بجوار مجوهرات حامد محروس.\n"
    "  📅 المواعيد: يومياً بدءاً من الساعة 5:00 مساءً.\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

ENT_TEXT = (
    "👂 *[الأنف والأذن والحنجرة]*\n"
    "----------------------------------------\n\n"
    "• 👨‍⚕️ د/ أحمد مصطفى خطاب (استشاري الأنف والأذن والحنجرة وتجميل الأنف)\n"
    "  📍 العنوان: الطريق الرئيسي - أعلى صيدلية خطاب.\n"
    "  📅 المواعيد: \n"
    "  - السبت، الإثنين، والأربعاء (من 5:00 إلى 9:00 مساءً).\n"
    "  - الأحد، الثلاثاء، والخميس (من 3:00 إلى 5:00 مساءً).\n"
    "  📞 للتواصل: 01022007977\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

NEURO_SURGERY_TEXT = (
    "🧠 *[مخ وأعصاب وجراحة عامة]*\n"
    "----------------------------------------\n\n"
    "• 👨‍⚕️ د/ أحمد صلاح (المخ والأعصاب)\n"
    "  📍 العنوان: أعلى صيدلية دكتور شكري.\n"
    "  📅 المواعيد: من الإثنين للخميس (من 4:00 عصراً لـ 8:00 مساءً).\n\n"
    "• 👨‍⚕️ د/ إسلام جمال هندي (الجراحة العامة)\n"
    "  📅 المواعيد: كل يوم عدا الإثنين (من 5:00 مساءً لـ 10:00 مساءً).\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

UROLOGY_DERMA_TEXT = (
    "🩸 *[المسالك البولية والجلدية]*\n"
    "----------------------------------------\n\n"
    "• 👨‍⚕️ د/ أسامة الجندي (مسالك بولية)\n"
    "  📅 المواعيد: يومياً عدا الجمعة (من 5:00 مساءً لـ 11:00 مساءً).\n\n"
    "• 👨‍⚕️ د/ عبد الرحمن (الجلدية)\n"
    "  📍 العنوان: عمارة الأطباء.\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

XRAY_LABS_TEXT = (
    "🔬 *[مراكز الأشعة والتحاليل]*\n"
    "----------------------------------------\n\n"
    "• 🏢 مركز أ.د/ محمد عبد الخالق باشا للأشعة التشخيصية\n"
    "  📍 العنوان: البلاشون - بجوار بنزينة رمضان عبد الكريم.\n"
    "  📅 المواعيد: \n"
    "  - يومياً: من 2:30 ظهراً إلى 10:30 مساءً.\n"
    "  - الجمعة: من 3:00 عصراً إلى 10:00 مساءً.\n"
    "  📞 أرقام التواصل: 0552801774 - 01025071770 - 01289740450\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

ALFATH_CLINICS_TEXT = (
    "🏛️ *عيادات الفتح التخصصية*\n"
    "----------------------------------------\n\n"
    "🦷 *[قسم طب وجراحة الفم والأسنان]:*\n\n"
    "• 👨‍⚕️ د/ علي الشاهد (أخصائي طب وجراحة الفم والأسنان)\n"
    "  📅 المواعيد: السبت، الأحد، الاثنين، والجمعة.\n"
    "  ⏰ الوقت: من 4:00 إلى 9:00 مساءً.\n\n"
    "• 👨‍⚕️ د/ خالد أبو زيد باشا (أخصائي طب وجراحة الفم والأسنان)\n"
    "  📅 المواعيد: الثلاثاء والأربعاء.\n"
    "  ⏰ الوقت: من 4:00 إلى 9:00 مساءً.\n\n"
    "• 👩‍⚕️ د/ الشيماء جمال (أخصائية طب وجراحة الفم والأسنان)\n"
    "  📅 المواعيد: الخميس.\n"
    "  ⏰ الوقت: من 4:00 إلى 9:00 مساءً.\n\n"
    "----------------------------------------\n\n"
    "👁️ *[عيادة الرمد والعيون]:*\n\n"
    "• 👨‍⚕️ د/ أحمد مكاوي (أخصائي طب وجراحة العيون)\n"
    "  📅 المواعيد: الثلاثاء والجمعة.\n"
    "  ⏰ الوقت: من 4:00 إلى 7:00 مساءً.\n\n"
    "----------------------------------------\n\n"
    "🩺 *[عيادة الباطنة العامة]:*\n\n"
    "• 👨‍⚕️ د/ إبراهيم عاطف الجندي (نائب الباطنة العامة بمستشفى الأحرار التعليمي بالزقازيق)\n"
    "  📅 المواعيد: الأحد والجمعة.\n"
    "  ⏰ الوقت: من 5:00 إلى 9:00 مساءً.\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
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
    "📞 *للتواصل:* 01002707560\n"
    "⏰ *الشيفت مستمر حتى الساعة 3 صباحاً*\n\n"
    "💊 *صيدليات الدكتورة إيمان عبد الفتاح*\n"
    "----------------------------------------\n"
    "📍 *[الفرع الأول]:*\n"
    "• العنوان: أمام الدكتور جمال عبد الناصر.\n"
    "• ⏰ مواعيد العمل: من 9:00 صباحاً حتى 1:00 ليلاً.\n\n"
    "📍 *[الفرع الثاني]:*\n"
    "• العنوان: أمام مضيفة موسى العراقي.\n"
    "• ⏰ مواعيد العمل: من 8:00 صباحاً حتى 3:00 ليلاً.\n\n"
    "----------------------------------------\n"
    "📞 *[للتواصل والاستشارة الطبية]:*\n"
    "• د/ كريم السحت: 01206097087\n"
    "• أ/ نبيل عبد السلام: 01062786766\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
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

SELF_CARE_TEXT = (
    "✨ *صيدلية د/ نهال محمد - Self Care* ✨\n"
    "----------------------------------------\n\n"
    "🛍️ *[أقسام ومنتجات العيادة والتجميل]:*\n\n"
    "• 🇰🇷 المنتجات الكورية (Korean Skincare):\n"
    "  - متوفر أحدث المنتجات الكورية الأصلية للعناية بالبشرة والشعر.\n\n"
    "• 🧪 براندات العناية العالمية (Skin & Hair Care):\n"
    "  - متوفر منتجات (La Roche-Posay - CeraVe - Vichy).\n"
    "  - جميع منتجات العناية بالبشرة والشعر بأرخص الأسعار.\n\n"
    "• 💄 البرفيوم والميك أب (Perfumes & Makeup):\n"
    "  - تشكيلة مميزة من البرفيوم (Outlet & Original).\n"
    "  - متوفر جميع المستلزمات الخاصة بالميك أب عالي الجودة.\n\n"
    "----------------------------------------\n"
    "📍 *[العنوان]:*\n"
    "• الموقف بجانب الحاج فهمي صاحب الأسمنت\n\n"
    "📞 *[أرقام التواصل والطلب]:*\n"
    "• الخط الأرضي: 2804454\n"
    "• رقم المحمول: 01024559627\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

DELIVERY_TEXT = (
    "📦 *دليل كباتن الشحن والتوصيل (دليفري)*\n"
    "----------------------------------------\n\n"
    "• 🛵 الكابتن: علي شاكر (دليفري)\n"
    "  📍 العنوان: عزبة الشيمي\n"
    "  📞 للتواصل: 01018226726\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

ALWAFAA_LIBRARY_TEXT = (
    "📚✨ *مكتبة الوفاء - للخدمات الطلابية والمكتبية المتكاملة*\n"
    "----------------------------------------\n\n"
    "🎒 *[الكتب والمناهج الدراسية]:*\n"
    "• متوفر جميع الكتب والمذكرات لجميع المراحل التعليمية (الابتدائية، الإعدادية، الثانوية).\n"
    "• توفير ملخصات وكتب خارجية لأقوى المدرسين.\n\n"
    "🖨️ *[خدمات الطباعة والتصوير]:*\n"
    "• طباعة وتصوير أوراق ومذكرات بجودة عالية (أبيض وأسود / ألوان).\n"
    "• طباعة مباشرة لملفات الـ PDF والـ Word والـ Excel من الموبايل أو الفلاشة.\n"
    "• خدمات التغليف (سلك / حراري) وتكعيب المذكرات.\n\n"
    "💼 *[أدوات مكتبية ومدرسية]:*\n"
    "• تشكيلة متكاملة من الأدوات المكتبية، الكشاكيل، الأقلام، والوسائل التعليمية.\n"
    "• هدايا وأدوات مبتكرة للأطفال وطلاب المدارس.\n\n"
    "💻 *[الخدمات الإلكترونية والأبحاث]:*\n"
    "• عمل أبحاث لجميع المراحل الدراسية والجامعية وتنسيق ملفات تخرج وطباعتها.\n"
    "• تحميل ملازم ومذكرات المراجعات النهائية وضبط الهوامش قبل الطباعة.\n\n"
    "----------------------------------------\n"
    "📍 *[العنوان]:*\n"
    "• شارع الموقف بجانب فهمي صاحب الأسمنت\n\n"
    "📞 *[للتواصل أو إرسال ملفات الطباعة]:*\n"
    "• رقم المحمول: 01099661248\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

SAAD_OFFICE_TEXT = (
    "⚖️ *مكتب السعد للمحاسبة والمراجعة والخدمات الضريبية* ⚖️\n"
    "👨‍💼 *المحاسب/ سعد عبد الحميد سعد (محاسب ومراجع قانوني وخبير ضرائب)*\n"
    "----------------------------------------\n\n"
    "✨ *[خدماتنا المتكاملة]:*\n\n"
    "💼 *1. تأسيس الشركات والتراخيص:*\n"
    "• تأسيس الشركات بكافة أنواعها (داخل الهيئة العامة للاستثمار).\n"
    "• استخراج كافة التراخيص (رخص نشاط صناعية ومحلية).\n"
    "• استخراج بطاقات الاستيراد والتصدير، وبطاقات الاحتياجات.\n"
    "• فتح البطاقات الضريبية (ضرائب عامة وقيمة مضافة).\n\n"
    "📊 *2. المحاسبة والمراجعة والميزانيات:*\n"
    "• مراجعة الحسابات بدقة وإعداد الميزانيات العمومية.\n"
    "• إعداد دراسات الجدوى المعتمدة.\n"
    "• إصدار شهادات الدخل للتقديم على شقق الإسكان الاجتماعي.\n\n"
    "📝 *3. الضرائب والإقرارات والمنازعات:*\n"
    "• إعداد الإقرارات الضريبية بكافة أنواعها (دخل - كسب عمل - قيمة مضافة - مرتبات وأجور).\n"
    "• إدارة وحل المنازعات الضريبية بكافة مستوياتها.\n"
    "• حل مشاكل التصرفات العقارية ودفع الضرائب الخاصة بها.\n\n"
    "👥 *4. التأمينات والاستشارات:*\n"
    "• فتح الملفات التأمينية، والتأمين على العمال أو فصلهم.\n"
    "• تقديم الاستشارات القانونية والضريبية (داخل المكتب أو عبر الواتساب).\n\n"
    "----------------------------------------\n"
    "📍 *[الفروع والعناوين]:*\n"
    "• 🏬 الفرع الأول: البلاشون - آخر شارع الوحدة المحلية - بلبيس - الشرقية.\n"
    "• 🏬 الفرع الثاني: بلبيس - أمام مأمورية الضرائب العامة - بجوار مسجد الطاهرات.\n\n"
    "📞 *[أرقام التواصل والاستفسار]:*\n"
    "• 🟢 01099609882 (اتصال أو واتساب)\n"
    "• 💬 01067743223 (واتساب فقط)\n"
    "• 📞 01119461438 (اتصال فقط)\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

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

WORKERS_TEXT = (
    "🛠️ *دليل الصنايعية بالبلاشون:*\n\n"
    "يرجى اختيار تخصص الصنايعي المطلوب من الأزرار بالأسفل لعرض الأسماء وأرقام التواصل.\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

WOOD_WORKERS_TEXT = (
    "🪵 *[أعمال الخشب والموبيليات]*\n"
    "----------------------------------------\n\n"
    "• 🛠️ محمد كمال شديد\n"
    "  📞 رقم التواصل: 01002803443 - 0552803443\n\n"
    "• 🛠️ أيمن جمال\n"
    "  📞 رقم التواصل: 01002263168\n\n"
    "• 🛠️ السيد موسى\n"
    "  📞 رقم التواصل: 01094143194\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

PAINT_WORKERS_TEXT = (
    "🎨 *[أعمال تشطيب الدهانات]*\n"
    "----------------------------------------\n\n"
    "• 🎨 حسن القربي\n"
    "  📞 رقم التواصل: 01022443024 - 01103624415\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

ELEC_WORKERS_TEXT = (
    "⚡ *[تأسيس وتشطيب الكهرباء]*\n"
    "----------------------------------------\n\n"
    "• ⚡ مصطفى حسين\n"
    "  📞 رقم التواصل: 01010718608\n\n"
    "• ⚡ محمد حسن فاضل\n"
    "  📞 رقم التواصل: 01023367875\n\n"
    "• ⚡ عمرو القمحاوي\n"
    "  📞 رقم التواصل: 01093100354\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

CERAMIC_WORKERS_TEXT = (
    "🧱 *[تركيب السيراميك والبورسلين]*\n"
    "----------------------------------------\n\n"
    "• 🧱 محمد قاسم\n"
    "  📞 رقم التواصل: 01093000617\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
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

CHARITY_TEXT = (
    "🏛️ *الجمعية الشرعية بالبلاشون* 🏛️\n"
    "----------------------------------------\n\n"
    "📞 *[أرقام التواصل والاستعلام]:*\n"
    "• ☎️ الخط الأرضي: 0552803988\n"
    "• 📱 أ/ طارق محمود: 01062154844\n\n"
    "----------------------------------------\n"
    "🤖 للبوت والخدمات: t.me/AlBalashon\_services\_bot"
)

# ─── لوحات المفاتيح ──────────────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 حالات عاجلة"],
        ["self care ✨", "🚕 مشاركة المشاوير والمواصلات"],
        ["💼 وظائف خالية", "🛠️ الخدمات"],
        ["🩺 دليل الأطباء والعيادات", "الجمعية الشرعية 🏛️"],
        ["🛺 اطلب توك توك", "💻 مصمم البوت"]
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
        ["دليل الصنايعية 🛠️", "📦 خدمات الشحن والتوصيل (الطيارين)"],
        ["🪟 معرض استار ميتال للألوميتال", "مكتبة الوفاء 📚"],
        ["مكتب السعد للمحاسبة والمراجعة ⚖️"],
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
            [InlineKeyboardButton("طب وجراحة الفم والأسنان 🦷", callback_data="doc_dentist")],
            [InlineKeyboardButton("العلاج الطبيعي والتغذية 🦾", callback_data="doc_physio")],
            [InlineKeyboardButton("الباطنة والقلب والصدر 🫁", callback_data="doc_internal")],
            [InlineKeyboardButton("أمراض النساء والتوليد 🤰", callback_data="doc_obgyn")],
            [InlineKeyboardButton("الأنف والأذن والحنجرة 👂", callback_data="doc_ent")],
            [InlineKeyboardButton("مخ وأعصاب وجراحة عامة 🧠", callback_data="doc_neuro_surgery")],
            [InlineKeyboardButton("المسالك البولية والجلدية 🩸", callback_data="doc_uro_derma")],
            [InlineKeyboardButton("مراكز الأشعة والتحاليل 🔬", callback_data="doc_xray_labs")],
            [InlineKeyboardButton("عيادات الفتح التخصصية 🏛️", callback_data="alfath_clinics")]
        ])
        await update.message.reply_text(DOCTORS_TEXT, parse_mode="Markdown", reply_markup=doctors_markup, disable_web_page_preview=True)
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

    elif "مكتبة الوفاء" in text:
        await update.message.reply_text(ALWAFAA_LIBRARY_TEXT, parse_mode="Markdown")
        return ConversationHandler.END

    elif "مكتب السعد" in text or "محاسبة" in text:
        await update.message.reply_text(SAAD_OFFICE_TEXT, parse_mode="Markdown")
        return ConversationHandler.END

    elif "طوارئ الليلة" in text or "صيدليات" in text:
        contact_keyboard = [
            [InlineKeyboardButton("تواصل مع صيدلية د. إبراهيم 💬", url="https://wa.me/201002707560")],
            [InlineKeyboardButton("د. كريم السحت (واتساب) 💬", url="https://wa.me/201206097087")],
            [InlineKeyboardButton("أ. نبيل عبد السلام (واتساب) 💬", url="https://wa.me/201062786766")]
        ]
        contact_markup = InlineKeyboardMarkup(contact_keyboard)
        await update.message.reply_text(EMERGENCY_PHARMACY_INFO, parse_mode="Markdown", reply_markup=contact_markup)
        return ConversationHandler.END

    elif "طبيب طوارئ" in text:
        contact_keyboard = [[InlineKeyboardButton("💬 تواصل طوارئ (واتساب)", url="https://wa.me/201069431963")]]
        contact_markup = InlineKeyboardMarkup(contact_keyboard)
        await update.message.reply_text(EMERGENCY_DOCTOR_TEXT, parse_mode="Markdown", reply_markup=contact_markup)
        return ConversationHandler.END
        
    elif "الصنايعية" in text:
        workers_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("أعمال الخشب والموبيليات 🪵", callback_data="work_wood")],
            [InlineKeyboardButton("أعمال تشطيب الدهانات 🎨", callback_data="work_paint")],
            [InlineKeyboardButton("تأسيس وتشطيب الكهرباء ⚡", callback_data="work_elec")],
            [InlineKeyboardButton("تركيب السيراميك والبورسلين 🧱", callback_data="work_ceramic")]
        ])
        await update.message.reply_text(WORKERS_TEXT, parse_mode="Markdown", reply_markup=workers_markup, disable_web_page_preview=True)
        return ConversationHandler.END

    elif "الشحن والتوصيل" in text:
        await update.message.reply_text(DELIVERY_TEXT, parse_mode="Markdown")
        return ConversationHandler.END

    # --- الردود التي تتطلب إدخال بيانات ---
    elif "التبرع بالدم" in text:
        await update.message.reply_text("🩸 اكتب تفاصيل الحالة الحرجة فوراً (مثال: الفصيلة، المستشفى، رقم التواصل):")
        return WAITING_FOR_REQUEST_DETAILS

    elif "وظائف" in text:
        await update.message.reply_text("💼 اكتب تفاصيل الوظيفة (التخصص، المرتب، رقم التواصل):")
        return WAITING_FOR_REQUEST_DETAILS

    elif "طلب مساعدة" in text:
        await update.message.reply_text("🚨 اكتب تفاصيل طلب المساعدة أو الاستغاثة ورقم التواصل:")
        return WAITING_FOR_REQUEST_DETAILS

    elif "شكاوى" in text or "مقترح" in text:
        await update.message.reply_text("📝 اكتب تفاصيل شكواك أو مقترحك وسيتم إرسالها للإدارة:")
        return WAITING_FOR_REQUEST_DETAILS

    elif "مفقودات" in text:
        await update.message.reply_text("📢 اكتب تفاصيل المفقودات أو الأمانات مع رقم للتواصل:")
        return WAITING_FOR_REQUEST_DETAILS

    elif "self care" in text.lower() or "self care ✨" in text:
        await update.message.reply_text(SELF_CARE_TEXT, parse_mode="Markdown")
        return ConversationHandler.END
        
    elif "مشاوير" in text or "مواصلات" in text:
        await update.message.reply_text("🚕 اكتب تفاصيل مشوارك (سواق ولا راكب، والميعاد):")
        return WAITING_FOR_REQUEST_DETAILS

    elif "الجمعية الشرعية" in text:
        await update.message.reply_text(CHARITY_TEXT, parse_mode="Markdown")
        return ConversationHandler.END

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
             "🤝 طلب مساعدة", "🚨 طبيب طوارئ (24 ساعة)", "self care ✨", 
             "🚕 مشاركة المشاوير والمواصلات", "💼 وظائف خالية", "🛠️ الخدمات", 
             "🩺 دليل الأطباء والعيادات", "🪟 معرض استار ميتال للألوميتال",
             "📦 خدمات الشحن والتوصيل (الطيارين)", "مكتبة الوفاء 📚", "دليل الصنايعية 🛠️",
             "مكتب السعد للمحاسبة والمراجعة ⚖️", "مكتب السعد", "الجمعية الشرعية 🏛️",
             "🛺 اطلب توك توك", "💻 مصمم البوت", "🔙 رجوع للقائمة الرئيسية", 
             "🚕 مشاركة المشاوير", "🛠 الخدمات", "🍔 مطاعم", "🏟️ حجز ملعب البلاشون",
             "مكتبة الوفاء", "دليل الصنايعية", "الجمعية الشرعية", "شكاوى", "مفقودات"]
             
    if user_text in KNOWN:
        context.user_data.clear()
        return await handle_choice(update, context)

    choice    = context.user_data.get("choice", "")
    user      = update.effective_user
    username  = f"@{user.username}" if user.username else str(user.id)

    try:
        # نظام طلبات النشر الموحد في القناة
        action_code = ""
        action_name = ""
        
        if "طلب مساعدة" in choice:
            action_code = "sos"
            action_name = "طلب مساعدة / استغاثة"
        elif "شكاوى" in choice or "مقترح" in choice:
            action_code = "complaint"
            action_name = "شكوى / مقترح"
        elif "مفقودات" in choice:
            action_code = "lost"
            action_name = "مفقودات وأمانات"
        elif "وظائف" in choice:
            action_code = "job"
            action_name = "وظيفة"
        elif "مشاركة المشاوير" in choice or "المواصلات" in choice:
            action_code = "ride"
            action_name = "مواصلة"
        elif "التبرع بالدم" in choice:
            action_code = "blood"
            action_name = "تبرع بالدم"
            
        if action_code:
            markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ موافقة ونشر", callback_data=f"app_{action_code}_{user.id}"),
                InlineKeyboardButton("❌ رفض الطلب", callback_data=f"rej_{action_code}_{user.id}")
            ]])
            req = f"🚨 {action_name} جديد\nمن: {username}\n\nالتفاصيل:\n{user_text}"
            
            for admin in ADMINS:
                try:
                    if photo_file_id: await context.bot.send_photo(admin, photo_file_id, caption=req, reply_markup=markup)
                    else: await context.bot.send_message(admin, text=req, reply_markup=markup)
                except Exception as admin_err:
                    logger.warning("فشل الإرسال للآدمن %s: %s", admin, admin_err)
            
            await update.message.reply_text("تم إرسال طلبك بنجاح إلى الإدارة وسنتواصل معك قريباً. ✅", reply_markup=MAIN_KEYBOARD)
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
    
    if data == "alfath_clinics":
        await query.message.reply_text(ALFATH_CLINICS_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "doc_dentist":
        await query.message.reply_text(DENTISTRY_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "doc_physio":
        await query.message.reply_text(PHYSIO_NUTRITION_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "doc_internal":
        await query.message.reply_text(INTERNAL_CARDIO_CHEST_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "doc_obgyn":
        await query.message.reply_text(OBSTETRICS_GYNECOLOGY_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "doc_ent":
        await query.message.reply_text(ENT_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "doc_neuro_surgery":
        await query.message.reply_text(NEURO_SURGERY_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "doc_uro_derma":
        await query.message.reply_text(UROLOGY_DERMA_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "doc_xray_labs":
        await query.message.reply_text(XRAY_LABS_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "work_wood":
        await query.message.reply_text(WOOD_WORKERS_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "work_paint":
        await query.message.reply_text(PAINT_WORKERS_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "work_elec":
        await query.message.reply_text(ELEC_WORKERS_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return
    elif data == "work_ceramic":
        await query.message.reply_text(CERAMIC_WORKERS_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
        return

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
            text_to_send = f"🚨 *استغاثة عاجلة*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon\_services\_bot"
        elif action == "blood":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع حالة الطوارئ 🩸", url=contact_url)]])
            text_to_send = f"🚨 *نداء طوارئ عاجل - تبرع بالدم* 🚨\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon\_services\_bot"
        elif action == "ride":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل مع صاحب المشوار 💬", url=contact_url)]])
            text_to_send = f"🚕 *إعلان مواصلة فوري*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon\_services\_bot"
        elif action == "lost":
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("تواصل للإبلاغ 💬", url=contact_url)]])
            text_to_send = f"📢 *مفقودات وأمانات*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon\_services\_bot"
        elif action == "job":
            text_to_send = f"💼 *وظائف خالية*\n\n{details}\n\n🤖 للتواصل عبر البوت: t.me/AlBalashon\_services\_bot"
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
    if update.effective_user.id not in ADMINS: return
    count = get_user_count()
    await update.message.reply_text(f"📊 عدد المشتركين في البوت حالياً: {count} شخص.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMINS: return
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
    now_date_str = str(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date())
    last_morning = context.bot_data.get("last_morning_date")
    if last_morning == now_date_str:
        return
    context.bot_data["last_morning_date"] = now_date_str

    azkar_text = (
        "☀️ *أذكار الصباح | بنية فتح الأبواب والبركة* ☀️\n\n"
        "- سبحان الله\n- الحمد لله\n- لا إله إلا الله\n"
        "- صلى الله على محمد، صلى الله عليه وسلم (صلِّ على رسول الله)"
    )
    try: await context.bot.send_message(CHANNEL_ID, azkar_text, parse_mode="Markdown")
    except Exception: pass

async def send_daily_evening_azkar(context: ContextTypes.DEFAULT_TYPE):
    now_date_str = str(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date())
    last_evening = context.bot_data.get("last_evening_date")
    if last_evening == now_date_str:
        return
    context.bot_data["last_evening_date"] = now_date_str

    try: await context.bot.send_message(CHANNEL_ID, f"🌆 *أذكار المساء*\n\n{EVENING_AZKAR_TEXT}", parse_mode="Markdown")
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

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice),
        ],
        states={
            WAITING_FOR_REQUEST_DETAILS: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, process_input)],
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