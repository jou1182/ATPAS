# ATPAS — سجل التغييرات

## [Sprint 4] — أبريل 2026 — تحسينات 10/10

### 🔒 الأمان (Priority 1)
- **منع path traversal**: تحقق تلقائي من معرّفات الأكواد قبل أي استخدام في مسارات الملفات
- **حد حجم الاستيراد**: 50 MB كحد أقصى في معالج الاستيراد
- **نمط التحقق**: `^\d{3}-[A-Z]{2,8}-[A-Z]{2,8}$` يرفض أي كود لا يطابق الصيغة

### 📝 التسجيل (Priority 2)
- تفعيل `logging.getLogger(__name__)` في: `json_manager.py`، `backup_manager.py`، `build_progress.py`، `import_wizard.py`
- كل عملية حفظ ذرية وكل استيراد ملف يُسجَّل بمستوى مناسب
- الأخطاء الحرجة تُسجَّل بـ `logger.exception` مع stack trace كامل

### ✅ الاختبارات (Priority 3)
- إضافة `tests/test_formatter.py` — 27 اختباراً لـ Formatter
- إضافة `tests/test_parser.py` — 24 اختباراً لـ Parser + helpers
- إضافة اختبارات أمان في `tests/test_edge_cases.py` — 12 اختباراً
- **إجمالي الاختبارات: 237 اختباراً** (جميعها ناجحة)

### ⚙️ CI/CD (Priority 4)
- `requirements-lock.txt`: تثبيت إصدارات دقيقة لجميع المكتبات
- `.github/workflows/tests.yml`: تثبيت من الـ lockfile، تغطية ≥75%، pylint، جدولة أسبوعية

### 🏷️ أسماء الجهات (Priority 5)
- حذف القاموس الثابت `owner_names` من `builder.py`
- الاسم العربي يُقرأ الآن من `owner_specifications` في `master_config.json`
- يدعم جميع الجهات المسجّلة تلقائياً — لا تعديل في الكود مستقبلاً

### 🔤 Type hints (Priority 6)
- إضافة `image_count: int` و `owner_name_ar/en` إلى TypedDict في `engine/types.py`
- توحيد نوع `Paragraph` في helpers الخاصة بـ `style_applier.py`
- إضافة `Any` لـ `_remap_image_ids` في `content_library.py`

### 💬 رسائل الخطأ (Priority 7)
- إعادة كتابة `engine/error_handler.py`:
  - 12 نوع خطأ Python مع رسائل عربية واضحة
  - `format_user_error()` تُضيف تلميح عملي (`💡 التوصية`) لكل خطأ
  - `safe_call()` يستخدم الرسائل الجديدة تلقائياً

### 🧪 اختبارات إضافية (Priority 8)
- `tests/test_error_handler.py` — 19 اختباراً، تغطية 100% لـ error_handler
- `TestOwnerNameAr` في `test_builder.py` — 5 اختبارات للـ owner name resolution
- **تغطية engine+utils: 84%** (كانت 82.7%)

### 🛠️ إصلاح SyntaxWarning (Priority 9)
- إصلاح `\ATPAS\` في `ui/help_dialog.py` → `\\ATPAS\\` (escape صحيح)
- لا مزيد من `SyntaxWarning: invalid escape sequence '\A'`

---

## [Sprint 3] — أبريل 2026 — النواة الوظيفية

- بناء engine كامل: Builder، Validator، DependencyResolver، Formatter، Parser
- واجهة PyQt5: MainWindow، ImportWizard، BuildProgress، BackupManager
- 64 كوداً نشطاً، 6 مشاريع، دعم 9+ جهات مالكة
