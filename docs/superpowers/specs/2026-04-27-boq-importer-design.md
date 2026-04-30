# BOQ Importer — وثيقة التصميم
**التاريخ:** 2026-04-27  
**الإصدار:** 1.0  
**المسؤول:** د. يوسف سليم  
**الحالة:** مُنفَّذ ✅ — `engine/boq_importer.py` · `engine/boq_matcher.py` · `engine/gap_handler.py` · `ui/boq_review_panel.py`

---

## 1. المشكلة

المستخدم يقرأ جدول الكميات (Excel أو PDF) ويترجم بنوده يدوياً إلى أكواد في البرنامج — العملية تأخذ ساعة إلى ساعتين لكل مناقصة.

---

## 2. الحل — منظومة BOQ Importer

```
المستخدم يلخص جدول الكميات → Excel بسيط (أسماء بنود)
                ↓
        BOQ Importer يقرأ الملف
                ↓
        Smart Matcher يطابق كل بند بالأكواد الموجودة
                ↓
     بنود موجودة ✅ → مقترحة تلقائياً بالترتيب الصح
     بنود مجهولة ⚠️ → Gap Handler يتيح إنشاء كود جديد لحظياً
                ↓
        BOQ Review Panel — مراجعة وتعديل
                ↓
        موافقة → Word جاهز ✅
```

---

## 3. مدخل المستخدم — Excel Template

```
| اسم البند               |
|-------------------------|
| حفر بالميكنة            |
| خرسانة عادية            |
| أعمال الصرف الصحي       |
| ...                     |
```

- عمود واحد فقط (Column A)
- أسماء البنود بالعربية
- الصف الأول header اختياري (يُكتشف تلقائياً)
- المستخدم يعمله بمعرفته ويرفعه للبرنامج

---

## 4. المكونات الجديدة

### 4.1 `engine/boq_importer.py`
**الوظيفة:** يقرأ ملف Excel ويستخرج أسماء البنود نظيفة.

```python
def read_boq(filepath: str) -> list[str]:
    # يقرأ .xlsx / .xls
    # يكتشف header تلقائياً
    # يُرجع قائمة أسماء نظيفة (stripped, non-empty)
```

**المكتبة:** `openpyxl` (موجودة بالفعل في requirements.txt)

---

### 4.2 `engine/boq_matcher.py`
**الوظيفة:** يطابق كل بند بأقرب كود في codes_registry.json.

**خوارزمية المطابقة:**
1. تنظيف النص (مسافات زائدة، تشكيل)
2. حساب fuzzy ratio مع كل كود في السجل (الاسم + الوصف)
3. إذا أعلى ratio ≥ 70% → اقتراح
4. إذا < 70% → `None` (غير موجود)

```python
@dataclass
class MatchResult:
    boq_item: str          # اسم البند من الجدول
    code_id: str | None    # الكود المقترح (None = مجهول)
    score: float           # نسبة المطابقة 0.0–1.0
    is_new: bool           # هل أُنشئ لحظياً؟

def match_boq(items: list[str], registry: dict) -> list[MatchResult]:
    ...
```

**المكتبة:** `difflib.SequenceMatcher` (standard library — بدون تبعية جديدة)

---

### 4.3 `engine/gap_handler.py`
**الوظيفة:** يعالج البنود المجهولة ويُنشئ أكواداً جديدة.

```python
def create_code_from_boq(
    boq_item: str,
    project_type: str,
    registry_path: str
) -> str:  # يُرجع الـ code_id الجديد
    # ينشئ ID تلقائي (مثلاً: CUSTOM-001)
    # يضيف placeholder في codes_registry.json
    # يُرجع code_id
```

---

### 4.4 `ui/boq_review_panel.py`
**الوظيفة:** واجهة مراجعة نتائج المطابقة.

**العناصر:**
- جدول: البند | الكود المقترح | نسبة المطابقة | حالة
- البنود المجهولة: خلفية صفراء + زر "أضف كود جديد"
- زر: رفع ملف Excel
- زر: موافق → ابنِ العرض
- إعادة ترتيب drag & drop (بسيط)

---

## 5. تكامل مع النظام الحالي

| المكوّن | التغيير |
|---------|---------|
| `ui/main_window.py` | إضافة زر "استورد جدول كميات" |
| `engine/dependency_resolver.py` | لا تغيير — يُستخدم لترتيب الأكواد المقترحة |
| `codes_registry.json` | يستقبل الأكواد الجديدة من gap_handler |
| `engine/builder.py` | لا تغيير — يستقبل الأكواد النهائية كما هو |

---

## 6. التسلسل المنطقي

يبقى `dependency_resolver.py` المسؤول عن الترتيب. بعد المطابقة:
```
أكواد مقترحة → dependency_resolver.resolve() → أكواد مرتبة → review panel
```

---

## 7. الملفات الجديدة

| الملف | الحالة |
|-------|--------|
| `engine/boq_importer.py` | جديد |
| `engine/boq_matcher.py` | جديد |
| `engine/gap_handler.py` | جديد |
| `ui/boq_review_panel.py` | جديد |

## 8. الملفات المعدّلة

| الملف | التعديل |
|-------|---------|
| `ui/main_window.py` | زر "استورد جدول كميات" |
| `docs/tasks.md` | مهام Sprint 3b |
| `docs/specification.md` | FR-011, FR-012 |
| `SSOT/ATPAS_REFERENCE_DOCUMENT_v2.0.md` | قسم BOQ Importer |

---

## 9. معايير النجاح

- جدول 30 بند يُعالَج في < 5 ثوانٍ
- دقة المطابقة ≥ 80% على البنود النموذجية
- البنود المجهولة تظهر بوضوح وتُحل في < دقيقة
- الكود الجديد يُحفظ ويظهر في البرنامج فوراً بعد إنشائه
