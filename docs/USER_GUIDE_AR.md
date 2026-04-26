# دليل المستخدم — نظام ATPAS
**نظام الرواف لأتمتة العروض الفنية**  
الإصدار 1.0 | آخر تحديث: أبريل 2026

---

## الفهرس

0. [ابدأ من هنا: الدليل المبسط لإضافة الأكواد](#0-ابدأ-من-هنا-الدليل-المبسط-لإضافة-الأكواد)
1. [نظرة عامة على النظام](#1-نظرة-عامة-على-النظام)
2. [تشغيل التطبيق](#2-تشغيل-التطبيق)
3. [بنية الملفات](#3-بنية-الملفات)
4. [الملفات الرئيسية التي ستعمل عليها](#4-الملفات-الرئيسية-التي-ستعمل-عليها)
5. [كيف يعمل النظام — المبدأ الأساسي](#5-كيف-يعمل-النظام--المبدأ-الأساسي)
6. [إضافة كود جديد](#6-إضافة-كود-جديد)
7. [تعديل كود موجود](#7-تعديل-كود-موجود)
8. [ربط ملف Word بكود (مكتبة المحتوى)](#8-ربط-ملف-word-بكود-مكتبة-المحتوى)
9. [أدوات سطر الأوامر (tools/)](#9-أدوات-سطر-الأوامر-tools)
10. [إضافة مالك جهة جديدة](#10-إضافة-مالك-جهة-جديدة)
11. [إضافة مشروع جديد](#11-إضافة-مشروع-جديد)
12. [نظام الترقيم والتسمية](#12-نظام-الترقيم-والتسمية)
13. [الأكواد والمراحل الموجودة](#13-الأكواد-والمراحل-الموجودة)
14. [التحقق من صحة التغييرات](#14-التحقق-من-صحة-التغييرات)
15. [الأخطاء الشائعة وحلولها](#15-الأخطاء-الشائعة-وحلولها)
16. [صحة النظام](#16-صحة-النظام)
17. [إدارة الأكواد من داخل التطبيق](#17-إدارة-الأكواد-من-داخل-التطبيق)
18. [سجل إصدارات العروض](#18-سجل-إصدارات-العروض)

---

## 0. ابدأ من هنا: الدليل المبسط لإضافة الأكواد

إذا كان هدفك إضافة أو تعديل كود بدون خبرة برمجية، ابدأ بهذا الملف:

```text
docs/NON_TECH_CODE_WORKFLOW_AR.md
```

وإذا كان من يعمل على المشروع وكيل ذكاء صناعي أو مطور جديد، يجب أن يبدأ من:

```text
SSOT/ATPAS_REFERENCE_DOCUMENT_v4.0.md
```

هاتان الوثيقتان هما المرجع الأحدث بعد تحديث 26 أبريل 2026.

---

## 1. نظرة عامة على النظام

ATPAS نظام مكتبي (Desktop) مبني على Python + PyQt5، يعمل على Windows.

**ما يفعله النظام:**
1. تختار نوع المشروع (صرف صحي / مياه / أسفلت / إنشاءات ...)
2. تختار الجهة المالكة (NWC / مكة / وزارة الإسكان ...)
3. تختار الأكواد التي تريدها (من قائمة 64 كود نشط حاليًا)
4. النظام يبني ملف Word تلقائياً يجمع محتوى كل كود بالتنسيق الصحيح

**ثلاثة مبادئ تحكم كل شيء:**
- **codes_registry.json** — قائمة كل الأكواد وصفاتها
- **master_config.json** — إعدادات المشاريع والجهات والنظام
- **templates/source_documents/** — ملفات Word لكل كود (المحتوى الفعلي)

---

## 2. تشغيل التطبيق

### تشغيل من الكود المصدري (للتطوير)
```
cd D:\PY\ATPAS
python main.py
```

### تشغيل EXE (للمستخدم النهائي)
```
dist\ATPAS\ATPAS.exe
```

### تشغيل الاختبارات
```
cd D:\PY\ATPAS
python -m pytest tests/ -v
```
المتوقع حاليًا: **247 اختبار، كلهم أخضر**

### فحص صحة النظام من الواجهة

من الشريط العلوي اضغط:

```text
صحة النظام
```

أو استخدم الاختصار:

```text
Ctrl+H
```

سيعرض التطبيق تقريرًا عربيًا عن الأكواد، الجهات، الأنماط الجاهزة، وملفات Word المرتبطة.

---

## 3. بنية الملفات

```
ATPAS/
│
├── codes_registry.json          ← ⭐ قائمة كل الأكواد (SSOT)
├── master_config.json           ← ⭐ إعدادات المشاريع والجهات
├── presets.json                 ← مجموعات أكواد جاهزة
│
├── templates/
│   ├── source_documents/        ← ⭐ ملفات Word لكل كود (.docx)
│   │   ├── 001-SUR-BASE.docx
│   │   ├── 001-PRM-GOV.docx
│   │   └── ...
│   ├── content_registry.json    ← تسجيل ملفات بأسماء مختلفة
│   └── style_templates/         ← قوالب تنسيق لكل جهة
│
├── engine/
│   ├── builder.py               ← يبني ملف Word النهائي
│   ├── validator.py             ← يتحقق من صحة الأكواد المختارة
│   ├── parser.py
│   └── ...
│
├── utils/
│   ├── content_library.py       ← يبحث ويدير ملفات المحتوى
│   └── json_manager.py          ← قراءة/حفظ JSON
│
├── ui/
│   ├── main_window.py           ← النافذة الرئيسية
│   ├── checkbox_selector.py     ← قائمة اختيار الأكواد
│   ├── preview_panel.py         ← معاينة الكود المختار
│   └── ...
│
├── tools/
│   ├── extend_registry.py       ← سكريبت إضافة أكواد جديدة
│   └── import_content.py        ← سكريبت استيراد ملفات Word
│
├── tests/                       ← اختبارات (247 اختبار حاليًا)
├── output/                      ← ملفات العروض المولّدة (لا تُرفع على GitHub)
└── SSOT/                        ← وثائق مرجعية
```

---

## 4. الملفات الرئيسية التي ستعمل عليها

| الملف | متى تعدله |
|-------|-----------|
| `codes_registry.json` | إضافة أو تعديل أو تعطيل كود |
| `master_config.json` | إضافة مشروع جديد أو جهة مالكة جديدة |
| `templates/source_documents/` | إضافة أو تعديل محتوى كود بالـ Word |
| `templates/content_registry.json` | ربط ملف باسم مختلف لكود معين |

---

## 5. كيف يعمل النظام — المبدأ الأساسي

```
المستخدم يختار:
  المشروع: wastewater
  الجهة:   nwc
  الأكواد: [001-SUR-BASE, 001-PRM-GOV, 002-EXC-FINE]

         ↓

validator.py يتحقق:
  - هل الأكواد متوافقة مع المشروع؟
  - هل هناك أكواد إلزامية ناقصة؟
  - هل الترتيب صحيح (dependencies)؟

         ↓

builder.py يبني:
  لكل كود:
    → content_library.py يبحث عن {code_id}.docx في source_documents/
    → إذا وجد: ينسخ محتوى الـ Word مباشرة
    → إذا لم يجد: يكتب نص placeholder

         ↓

output/proposal_YYYYMMDD_HHMMSS.docx
```

---

## 6. إضافة كود جديد

### الطريقة 1: مباشرة في codes_registry.json (أبسط)

افتح `codes_registry.json` وأضف كوداً جديداً داخل `"codes": { ... }`:

```json
"005-HND-FIN": {
    "code_id": "005-HND-FIN",
    "category": "005",
    "phase": "HND",
    "variation": "FIN",
    "activity_name_ar": "التسليم النهائي للمشروع",
    "activity_name_en": "Final Project Handover",
    "project_ids": ["wastewater", "water_supply"],
    "network_types": ["S", "W"],
    "applicable_owners": ["nwc", "makkah", "moh"],
    "sequence_order": 99,
    "dependencies": ["004-TST-BASE"],
    "has_images": false,
    "image_count": 0,
    "page_count": 3,
    "source_document": "005-HND-FIN.docx",
    "tags": ["handover", "final", "completion"],
    "status": "active",
    "created_date": "2026-04-21",
    "last_modified": "2026-04-21",
    "version": "1.0",
    "notes": "آخر خطوة في المشروع"
}
```

بعدها حدّث `metadata.total_codes` بالعدد الجديد.

---

### الطريقة 2: عبر سكريبت Python (للإضافة الجماعية)

افتح `tools/extend_registry.py` وأضف الأكواد في قاموس `NEW_CODES`:

```python
NEW_CODES = {
    "005-HND-FIN": {
        "code_id": "005-HND-FIN",
        "category": "005",
        "phase": "HND",
        "variation": "FIN",
        "activity_name_ar": "التسليم النهائي للمشروع",
        "activity_name_en": "Final Project Handover",
        "project_ids": ["wastewater", "water_supply"],
        "network_types": ["S", "W"],
        "applicable_owners": ["nwc", "makkah"],
        "sequence_order": 99,
        "dependencies": ["004-TST-BASE"],
        "has_images": False,
        "image_count": 0,
        "page_count": 3,
        "source_document": "005-HND-FIN.docx",
        "tags": ["handover", "final"],
        "status": "active",
        "created_date": "2026-04-21",
        "last_modified": "2026-04-21",
        "version": "1.0"
    },
    # أضف المزيد هنا...
}
```

ثم شغّل:
```
cd D:\PY\ATPAS
python tools/extend_registry.py
```
النتيجة: `Registry expanded: 64 -> 65 codes`

---

### الحقول الإلزامية لكل كود

| الحقل | المعنى | مثال |
|-------|--------|-------|
| `code_id` | الكود (نفس المفتاح) | `"005-HND-FIN"` |
| `category` | الفئة (أول 3 أرقام) | `"005"` |
| `phase` | المرحلة (3-5 حروف) | `"HND"` |
| `variation` | التنويع | `"FIN"` |
| `activity_name_ar` | اسم النشاط بالعربية | `"التسليم النهائي"` |
| `activity_name_en` | اسم النشاط بالإنجليزية | `"Final Handover"` |
| `project_ids` | المشاريع التي ينتمي إليها | `["wastewater"]` |
| `network_types` | أنواع الشبكة | `["S", "W"]` |
| `applicable_owners` | الجهات التي يظهر لها | `["nwc", "makkah"]` |
| `sequence_order` | رقم الترتيب في التسلسل | `99` |
| `dependencies` | الأكواد التي يعتمد عليها | `["004-TST-BASE"]` |
| `status` | الحالة | `"active"` أو `"deprecated"` |

---

## 7. تعديل كود موجود

### تعديل الاسم
افتح `codes_registry.json`، ابحث عن الكود، عدّل:
```json
"activity_name_ar": "الاسم الجديد بالعربية",
"activity_name_en": "New English Name"
```

### تعديل الجهات المسموح لها
```json
"applicable_owners": ["nwc", "makkah", "swa"]
```
أضف أو احذف أي جهة من القائمة.

### تعديل المشاريع
```json
"project_ids": ["wastewater", "water_supply", "water_transmission"]
```

### تعطيل كود (بدون حذفه)
```json
"status": "deprecated"
```
الكود يختفي من الواجهة لكن يبقى في السجل.

### تغيير الترتيب
```json
"sequence_order": 15
```
رقم أصغر = يظهر أولاً في القائمة.

### تغيير التبعيات
```json
"dependencies": ["001-SUR-BASE", "001-APP-DES"]
```
هذا يعني: لا يمكن اختيار هذا الكود إلا إذا كان الكودان `001-SUR-BASE` و `001-APP-DES` محددين أيضاً.

### بعد أي تعديل — حدّث هذا الحقل
```json
"last_modified": "2026-04-21",
"version": "1.1"
```

---

## 8. ربط ملف Word بكود (مكتبة المحتوى)

هذا هو **جوهر العمل الحقيقي** — المحتوى الذي سيُكتب في العرض الفني.

### الطريقة 1: الأبسط — ضع الملف مباشرة

ضع ملف Word باسم `{CODE_ID}.docx` في مجلد:
```
templates/source_documents/001-SUR-BASE.docx
templates/source_documents/001-PRM-GOV.docx
```
النظام يجده تلقائياً — **لا تعديل في أي ملف آخر**.

### الطريقة 2: الملف باسم مختلف أو في مكان مختلف

```
python tools/import_content.py register 001-SUR-BASE "C:\Documents\survey_works.docx"
```
هذا يضيف سطراً في `templates/content_registry.json`:
```json
{
  "001-SUR-BASE": "C:\\Documents\\survey_works.docx"
}
```

### الطريقة 3: تقسيم ملف Word رئيسي تلقائياً

إذا عندك ملف Word واحد فيه كل البنود، كل بند بـ "Heading 1" باسمه:
```
python tools/import_content.py split "C:\Documents\Master_Document.docx"
```

**المعاينة قبل التنفيذ (آمن):**
```
python tools/import_content.py split "Master_Document.docx" --dry-run
```

### استعراض ما هو مرتبط وما هو ناقص
```bash
# عرض كل الأكواد المرتبطة بملف Word
python tools/import_content.py list

# عرض الأكواد التي لا تزال تستخدم Placeholder
python tools/import_content.py missing
```

### شروط ملف Word الخاص بالكود
- أي ملف `.docx` عادي
- يمكن أن يحتوي على: نصوص / جداول / صور مدمجة
- الصور ستُنسخ تلقائياً مع الملف
- التنسيق الخاص بك (خطوط/ألوان) يُحترم ما لم يتعارض مع قالب الجهة

---

## 9. أدوات سطر الأوامر (tools/)

### import_content.py — إدارة مكتبة المحتوى

```bash
# تقسيم ملف رئيسي إلى ملفات منفصلة
python tools/import_content.py split master.docx

# تقسيم مع تحديد مجلد الإخراج
python tools/import_content.py split master.docx --output-dir templates/source_documents/

# معاينة فقط (بدون كتابة)
python tools/import_content.py split master.docx --dry-run

# ربط ملف محدد بكود
python tools/import_content.py register 001-SUR-BASE "path/to/file.docx"

# عرض كل الملفات المرتبطة
python tools/import_content.py list

# عرض الأكواد بدون ملفات
python tools/import_content.py missing
```

### extend_registry.py — إضافة أكواد جماعية

```bash
python tools/extend_registry.py
```
يقرأ `NEW_CODES` من نفس الملف ويضيفها للـ registry.

---

## 10. إضافة مالك / جهة جديدة

### الخطوة 1: أضف في master_config.json

في القسم `"owner_specifications"`:

```json
"my_new_owner": {
    "owner_id": "my_new_owner",
    "owner_name_ar": "الجهة الجديدة",
    "owner_name_en": "New Owner Authority",
    "owner_code": "NWO",
    "applicable_networks": ["S", "W"],
    "default_language": "ar",
    "mandatory_sections": [
        "safety",
        "quality_control"
    ],
    "preferred_codes_prefix": "NWO",
    "style_guide": "new_owner_style.json",
    "typical_codes_range": "001-090",
    "specific_requirements": {
        "color_scheme": "blue_white",
        "font_family": "Times New Roman",
        "font_size_body": 12,
        "font_size_heading": 14,
        "logo_required": true
    },
    "contact": "projects@newowner.gov.sa",
    "created_date": "2026-04-21"
}
```

### الخطوة 2: أضف الجهة للأكواد المناسبة في codes_registry.json

لكل كود تريده يظهر لهذه الجهة، أضف `"my_new_owner"` في `applicable_owners`:

```json
"applicable_owners": ["nwc", "makkah", "my_new_owner"]
```

### الخطوة 3 (اختيارية): أضف ملف تنسيق

أنشئ `templates/style_templates/new_owner_style.json` بنفس بنية الملفات الموجودة.

---

## 11. إضافة مشروع جديد

### الخطوة 1: أضف في master_config.json

في القسم `"projects"`:

```json
"my_new_project": {
    "project_id": "my_new_project",
    "name_ar": "اسم المشروع بالعربية",
    "name_en": "Project Name in English",
    "description_ar": "وصف المشروع",
    "description_en": "Project Description",
    "network_type": "X",
    "network_type_name": "NewType",
    "source_document": "templates/source_documents/MyProject_Master.docx",
    "metadata_file": "metadata/projects/my_new_project.json",
    "sections_file": "templates/extracted_sections/my_new_project_sections.json",
    "total_codes": 0,
    "applicable_owners": ["nwc", "makkah"],
    "typical_page_range": [30, 80],
    "created_date": "2026-04-21",
    "last_modified": "2026-04-21",
    "status": "active"
}
```

### الخطوة 2: أضف نوع الشبكة في master_config.json

في القسم `"network_types"`:
```json
"X": {
    "code": "X",
    "name_ar": "النوع الجديد",
    "name_en": "New Network Type",
    "description": "وصف النوع الجديد"
}
```

### الخطوة 3: أضف الأكواد المناسبة

في `codes_registry.json`، لكل كود يناسب المشروع الجديد، أضف `"my_new_project"` في `project_ids`:
```json
"project_ids": ["wastewater", "my_new_project"]
```

---

## 12. نظام الترقيم والتسمية

### تركيب الكود
```
[CATEGORY]-[PHASE]-[VARIATION]
    001  -  SUR  -    BASE
    │        │         └─ التنويع (3-6 حروف/أرقام)
    │        └─────────── المرحلة (3-5 حروف)
    └──────────────────── الفئة (3 أرقام)
```

### الفئات الرئيسية

| الرقم | الفئة | الوصف |
|-------|-------|-------|
| 001 | الأعمال التحضيرية | المسح، الرخص، الاعتمادات |
| 002 | الحفر والمخلفات | حفر، إزالة، تسوية |
| 003 | التركيب والتوصيل | أنابيب، خرسانة، أسفلت |
| 004 | الاختبارات والفحوصات | اختبار ضغط، جودة |
| 005 | الإنهاء والتسليم | ردم، استعادة السطح، تسليم |

### المراحل الموجودة

| الكود | الاسم | الفئة |
|-------|-------|-------|
| SUR | المسح والتثبيت | 001 |
| PRM | الرخص والموافقات | 001 |
| APP | الاعتمادات | 001 |
| TRF | إدارة المرور | 001 |
| RDS | فحص الطريق | 001 |
| SOI | دراسة التربة | 001 |
| MAT | نقل المواد | 002 |
| EXC | الحفر | 002 |
| WST | إدارة المخلفات | 002 |
| PAV | تقييم الرصيف | 002 |
| MIL | جلخ الأسفلت | 002 |
| PIP | تركيب الأنابيب | 003 |
| WLD | اللحام والوصلات | 003 |
| FND | الأساسات | 003 |
| RBR | حديد التسليح | 003 |
| STR | الخرسانة الإنشائية | 003 |
| MAS | البناء بالبلوك | 003 |
| STL | الهياكل الفولاذية | 003 |
| ANC | كتل الارتكاز | 003 |
| AIR | صمامات التهوية | 003 |
| ASP | طبقات الأسفلت | 003 |
| CRB | حجارة الحافة | 003 |
| TST | الاختبارات | 004 |
| QC | فحص الجودة | 004 |
| INS | التمديدات والتشطيبات | 004 |
| BKF | الردم | 005 |
| RST | استعادة السطح | 005 |
| HND | التسليم النهائي | 005 |
| MRK | دهانات الطريق | 005 |
| SGN | اللوحات المرورية | 005 |
| SAF | الحواجز الأمنية | 005 |
| CLN | تنظيف الموقع | 005 |

### المشاريع الموجودة

| ID | الاسم | نوع الشبكة |
|----|-------|------------|
| wastewater | الصرف الصحي | S |
| water_supply | إمدادات المياه | W |
| asphalt | الطرق والأسفلت | A |
| road_maintenance | صيانة الطرق | R |
| general_construction | الإنشاءات العامة | C |
| water_transmission | خطوط النقل الرئيسية | T |

### الجهات الموجودة (20 جهة)

| ID | الاسم |
|----|-------|
| nwc | الشركة الوطنية للمياه |
| makkah | أمانة العاصمة المقدسة |
| moh | وزارة الإسكان |
| mot | وزارة النقل |
| nhi | الشركة الوطنية للإسكان |
| amana_riyadh | أمانة منطقة الرياض |
| amana_qassim | أمانة القصيم |
| swa | الهيئة السعودية للمياه |
| ksia | مطار الملك سلمان الدولي |
| amana_eastern | أمانة المنطقة الشرقية |
| amana_jeddah | أمانة محافظة جدة |
| amana_madinah | أمانة منطقة المدينة المنورة |
| modon | هيئة المدن الصناعية |
| royal_commission_jubail | الهيئة الملكية للجبيل وينبع |
| sar | السكك الحديدية السعودية - SAR |
| royal_court | الشؤون الخاصة لخادم الحرمين الشريفين |
| air_force | القوات الجوية السعودية |
| yanbu_project | الإدارة العامة لمشروع ينبع |
| baladiya_rabigh | بلدية محافظة رابغ |
| amana_riyadh_royal | الهيئة الملكية لمدينة الرياض |

---

## 13. الأكواد والمراحل الموجودة

حالياً في النظام **64 كوداً نشطاً** موزعة على:
- صرف صحي (wastewater): الأساس
- مياه (water_supply): يشارك كثير من الأكواد مع الصرف
- أسفلت (asphalt)
- صيانة طرق (road_maintenance): 20 كوداً
- إنشاءات عامة (general_construction): 18 كوداً
- خطوط نقل مياه (water_transmission): 22 كوداً

لعرض كل الأكواد مع أسمائها:
```bash
python -c "
from utils.json_manager import load_json
reg = load_json('codes_registry.json')
for k, v in reg['codes'].items():
    print(f'{k:<25} {v[\"activity_name_ar\"]}')
"
```

---

## 14. التحقق من صحة التغييرات

### بعد أي تعديل في codes_registry.json أو master_config.json

```bash
cd D:\PY\ATPAS
python -m pytest tests/ -v
```

الاختبارات تتحقق من:
- صحة بنية الـ JSON
- منطق الـ validator (أكواد متعارضة، dependencies)
- منطق content_library (البحث عن الملفات)

**إذا اجتازت الـ 247 اختبار = تغييراتك آمنة.**

### التحقق من ملفات المحتوى

```bash
# كم كود لديه ملف Word؟
python tools/import_content.py list

# كم كود لا يزال placeholder؟
python tools/import_content.py missing
```

---

## 15. الأخطاء الشائعة وحلولها

### "code_id not found in registry"
**السبب:** اخترت كوداً في الواجهة لكنه غير موجود في `codes_registry.json`.  
**الحل:** أضف الكود في `codes_registry.json` أو تأكد من الإملاء.

### الكود لا يظهر في قائمة مشروع معين
**السبب:** `project_ids` لا يشمل هذا المشروع، أو `applicable_owners` لا يشمل هذه الجهة.  
**الحل:** أضف المشروع/الجهة للكود في `codes_registry.json`.

### الكود يظهر placeholder بدل المحتوى الحقيقي
**السبب:** لا يوجد ملف `.docx` في `templates/source_documents/` بالاسم الصحيح.  
**الحل:** ضع الملف أو استخدم `import_content.py register`.

### "Invalid JSON" عند تشغيل التطبيق
**السبب:** خطأ نحوي في `codes_registry.json` أو `master_config.json` (فاصلة زائدة، قوس ناقص).  
**الحل:** افتح الملف في VS Code — سيظهر الخطأ بخط أحمر.  
أو استخدم: `python -m json.tool codes_registry.json`

### dependency error عند اختيار الأكواد
**السبب:** اخترت كوداً يعتمد على كود آخر لم تختره.  
**الحل:** أضف الكود المطلوب، أو عدّل `dependencies` في السجل.

### الصور لا تظهر في ملف الإخراج
**السبب:** الصور كانت مرتبطة (linked) وليس مدمجة (embedded) في ملف Word المصدر.  
**الحل:** في Word: Insert → Pictures → افتح الصورة مباشرة (لا تستخدم Insert Link).

---

## ملاحظة مهمة — البيانات الحساسة

الملفات التالية محمية بـ `.gitignore` ولا تُرفع على GitHub أبداً:
```
كلمة السر الافتراضية.txt   ← كلمة المرور الافتراضية rawaf2024
_owners_real.json           ← أسماء الجهات الحقيقية
_owner_extract.json         ← بيانات الموظفين
templates/source_documents/*.docx  ← المحتوى الفعلي للبنود
output/**                   ← كل ملفات العروض المُنتجة
```

---

## 16. صحة النظام

نافذة **صحة النظام** هي أول خطوة فحص قبل أي تعديل كبير أو قبل بناء عرض مهم.

تعرض النافذة:

- عدد الأكواد الكلي والنشط.
- عدد المشاريع والجهات المالكة.
- عدد الأنماط الجاهزة.
- عدد ملفات Word الموجودة.
- الأكواد التي لا تملك ملف Word مطابقًا.
- أخطاء الربط بين الأكواد والمشاريع والجهات.
- التبعيات الناقصة.

طريقة الاستخدام:

1. افتح التطبيق.
2. اضغط **صحة النظام** من الشريط العلوي.
3. راجع درجة الجاهزية.
4. إذا ظهرت أخطاء حمراء، أصلحها قبل بناء العرض.
5. إذا ظهرت تحذيرات برتقالية، يمكن البناء غالبًا، لكن الأفضل علاجها للوصول لجودة أعلى.
6. استخدم زر **نسخ التقرير** إذا أردت إرسال التقرير لمطور أو وكيل ذكاء صناعي.

قاعدة عملية:  
إذا كانت الشاشة بلا أخطاء حمراء، فبيانات النظام الأساسية سليمة. وإذا اختفت التحذيرات أيضًا، فهذا يعني أن النظام قريب من حالة تشغيل مثالية.

---

## 17. إدارة الأكواد من داخل التطبيق

نافذة **الأكواد** تسمح بإضافة أو تعديل أو تعطيل كود بدون فتح `codes_registry.json`.

طريقة الفتح:

```text
الشريط العلوي -> الأكواد
```

أو:

```text
Ctrl+M
```

ما يمكنك عمله:

- البحث عن كود موجود.
- تعديل الاسم العربي أو الإنجليزي.
- تعديل المشروع والجهة المالكة وأنواع الشبكات.
- تعديل التبعيات.
- تعديل عدد الصفحات وترتيب الظهور.
- تعطيل كود بدل حذفه.
- إضافة كود جديد من نموذج واضح.

خطوات إضافة كود جديد:

1. افتح نافذة **الأكواد**.
2. اضغط **إضافة كود جديد**.
3. اكتب معرف الكود مثل `003-PIP-MAIN`.
4. اكتب الاسم العربي.
5. اختر المشروع والجهة المالكة من الأزرار.
6. اكتب عدد الصفحات التقريبي.
7. اضغط **حفظ التعديل**.
8. افتح **صحة النظام** للتأكد أن الكود لا يسبب أخطاء.

قاعدة مهمة:  
لا تحذف كودًا قديمًا إلا للضرورة القصوى. استخدم **تعطيل الكود** حتى يبقى السجل محفوظًا ويمكن الرجوع إليه.

---

## 18. سجل إصدارات العروض

كل مرة يتم فيها بناء عرض فني بنجاح، يحفظ النظام سجلًا دائمًا لهذا العرض.

الملفات تحفظ هنا:

```text
output/reports/proposal_versions.json
output/reports/proposal_versions.csv
```

ماذا يحتوي السجل؟

- رقم إصدار مثل `PV-000001`.
- معرف عرض فريد يبدأ بـ `ATPAS`.
- تاريخ ووقت البناء.
- نوع المشروع.
- الجهة المالكة.
- الأكواد المستخدمة.
- عدد الأكواد.
- عدد الصفحات التقريبي.
- مسار ملف Word الناتج.
- حجم الملف.
- بصمة `sha256` للتأكد أن الملف لم يتغير.
- إصدار التطبيق المستخدم في البناء.

كيف تستخدمه؟

1. افتح ملف `proposal_versions.csv` في Excel.
2. راجع آخر عرض تم إنشاؤه.
3. استخدم رقم الإصدار عند التواصل مع الفريق.
4. إذا وجدت نسختين لنفس المشروع، قارن التاريخ ورقم الإصدار.

هذا السجل لا يعتمد على ذاكرة المستخدم. هو دفتر رسمي لكل عرض تم إنشاؤه.

---

## خلاصة سريعة — ماذا أعمل لو أردت...

| الرغبة | الإجراء |
|--------|---------|
| إضافة كود جديد | استخدم زر `الأكواد` من الشريط العلوي |
| إضافة كثير من الأكواد دفعة واحدة | أضفها في `tools/extend_registry.py` ثم شغّله |
| تعديل اسم كود | استخدم زر `الأكواد` من الشريط العلوي |
| ربط ملف Word بكود | ضع `{CODE_ID}.docx` في `templates/source_documents/` |
| ربط ملف باسم مختلف | `python tools/import_content.py register CODE_ID file.docx` |
| معرفة الأكواد بدون محتوى | `python tools/import_content.py missing` |
| إضافة جهة مالكة جديدة | أضفها في `master_config.json` → `owner_specifications` |
| إضافة مشروع جديد | أضفه في `master_config.json` → `projects` |
| تعطيل كود مؤقتاً | `"status": "deprecated"` في `codes_registry.json` |
| التحقق من صحة كل شيء | `python -m pytest tests/ -v` |

---

*آخر تحديث: أبريل 2026 — د. يوسف سليم | شركة الرواف للمقاولات*
