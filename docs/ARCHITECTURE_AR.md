# معمارية ATPAS — دليل الفهم الشامل لأي وكيل ذكاء اصطناعي

**آخر تحديث**: 29 أغسطس 2026 · **الإصدار المرجعي**: v3.2 · **اقرأ هذا الملف بعد** `AGENTS.md` وقبل أي تعديل.

> هذا المستند يشرح **كيف يعمل ATPAS من الداخل** — المعمارية، آلية التركيب، طبقات البيانات، والواجهة. الهدف: أن يفهم أي وكيل مستقبلي التطبيق **دون البحث في كل ملف**.

---

## 1. نظرة عامة — ما هو ATPAS في ثلاث جمل

ATPAS هو تطبيق Windows (PyQt5 + python-docx) يبني **عروضاً فنية عربية** بصيغة Word لشركة مقاولات (الرواف للهندسة — قابلة للتبديل عبر `company_profile.json`).

المستخدم يختار: **مشروعاً** (6 أنواع: صرف صحي، مياه، أسفلت، صيانة طرق، إنشاءات عامة، نقل مياه) + **جهة مالكة** (20 جهة) + **أكواداً فنية** (65 نشاطاً).

النظام **يركّب ملف Word واحداً** من **مكتبة أنشطة جاهزة** — كل نشاط ملف `.docx` مستقل يُنسخ (تركيب) فوق الآخر بالترتيب، مع غلاف وفهرس وهوية الجهة المالكة.

---

## 2. خط المعالجة (Pipeline)

```
المستخدم → PyQt5 RTL UI (اختيار مشروع + جهة + أكواد)
  │
  ├─ Validator (فحص التوافق والتبعيات)           [engine/validator.py]
  ├─ DependencyResolver (إكمال النواقص + ترتيب)   [engine/dependency_resolver.py]
  │        └─ rules.is_alternative_dependency_set  [engine/rules.py]
  │
  ▼
Builder (التركيب الفعلي)                          [engine/builder.py]
  ├─ _add_cover          → صفحة الغلاف
  ├─ _add_toc_placeholder → حقل فهرس (يولّده Word عند الفتح)
  ├─ _add_sections       → لكل كود: عنوان H1 + نسخ جسم نشاطه
  │        └─ ContentLibrary.insert_into           [utils/content_library.py]
  │              └─ _copy_docx_body (نسخ OOXML عميق)
  ├─ StyleApplier        → هوية الجهة (ترويسة/تذييل/ألوان)  [engine/style_applier.py]
  ├─ Formatter           → تنسيق الخطوط والعناوين          [engine/formatter.py]
  └─ docx_manipulator    → RTL شامل + خط Tajawal            [utils/docx_manipulator.py]
  │
  ▼
output/generated_documents/proposal_{project}_{owner}_{ts}.docx
```

**مدخل الواجهة**: `ui/main_window.py:386 _build_engine()` يبني `Validator` + `DependencyResolver` من `codes_registry.json` مرة واحدة، ثم `ui/build_progress.py:57 BuildWorker.run()` يستدعي `Builder.build(...)` في خيط منفصل (QThread).

---

## 3. آلية التركيب — جوهر التطبيق (Stacking)

### 3.1 المفهوم

**كل كود فني = قسم واحد في الملف النهائي.** المحتوى الحقيقي لكل نشاط يعيش في ملف Word مستقل:
`templates/source_documents/{CODE_ID}.docx` (مثال: `001-SUR-BASE.docx`).

البنّاء لا يكتب نصاً — بل **ينسخ جسم كل ملف نشاط إلى الملف الهدف** على مستوى OOXML.

### 3.2 الحلقة الرئيسية — `engine/builder.py:370 _add_sections`

```python
activities = {a["code_id"]: a for a in project_meta.get("activity_sequence", []) ...}

current_category = None
for code_id in ordered_codes:                    # ← الترتيب من DependencyResolver
    code = self._codes.get(code_id)

    category = code.get("category")              # ← 001–005
    if category != current_category:
        self._add_category_divider(doc, category, formatter,   # ← صفحة فاصل فئة
                                   is_first=(current_category is None))
        current_category = category

    heading_text = f"{name_ar}  —  {code_id}"    # ← عنوان H1 بالعربية
    formatter.add_heading(doc, heading_text, level=1)   # أو doc.add_heading

    has_real_content = self._content_lib.insert_into(doc, code_id)  # ← التركيب

    if not has_real_content:
        # بديل: عنوان إنجليزي + وصف من metadata
        doc.add_paragraph(description)
    doc.add_paragraph()   # فاصل بين الأقسام
```

**الهيكل المتقدم (ميزة v3.2)**: قبل قسم الكود الأول من كل **فئة** (001–005)، يُدرَج **صفحة فاصل** بعنوان الفئة ووصفها (من `master_config.json → code_ranges`). الفئة الأولى لا تبدأ بصفحة جديدة (تلي الفهرس طبيعياً)؛ كل انتقال بعدها يبدأ صفحة جديدة. هذا يحوّل المستند من كومة مسطّحة إلى مراحل منظمة: تحضيرية → حفر → تركيب → اختبار → تسليم. التأثير على التقدير: `estimate_pages` يضيف +1 صفحة لكل فئة إضافية ممثلة (`_category_divider_count`).

### 3.3 النسخ العميق — `utils/content_library.py:205 _copy_docx_body`

الوظيفة التي تجعل "التركيب" يعمل. تنسخ كل عنصر جسم من ملف النشاط إلى الملف الهدف مع ثلاث معالجات حرجة:

```python
# 1. الصور: إعادة تسمية كل صورة باسم فريد (يمنع تصادم image1.png من مصادر متعددة)
new_partname = PackURI(f"/word/media/atpas_{unique_id}.{ext}")

# 2. الترقيم: نسخ abstractNum/num بأرقام جديدة فوق سقف الهدف + تصحيح RTL
num_id_map = _copy_numbering_rtl(source, target_doc)
#    لكل مستوى قائمة: lvlJc left→right، w:ind left→right

# 3. العناصر: deepcopy كل عنصر وإدراجه قبل <w:sectPr> (يحافظ على ترتيب عنوان→محتوى)
for element in source.element.body:
    if tag == "sectPr": continue   # يحتفظ الهدف بتخطيط صفحته
    node = deepcopy(element)
    sect_pr.addprevious(node)
```

### 3.4 الترتيب — `engine/dependency_resolver.py`

- **الافتراضي**: `resolve(selected)` — تبعيات (DFS مع احترام البدائل) + فرز بـ `sequence_order`.
- **مع BOQ**: `resolve_with_order(selected, boq_order)` — يحافظ على ترتيب جدول الكميات المستورد، ويحقن التبعيات الناقصة قبل مستهلكها مباشرة.
- **التبعيات البديلة** (أي من مجموعة): المنطق في `engine/rules.py` **وحده** — لا يُنسخ في أي مكان آخر (AGENTS.md قاعدة 11). مثال: `002-WST-EXC` يعتمد على "أي طريقة حفر" (FINE/OPEN/TUNNEL).

### 3.5 بنية الملف النهائي

```
[غلاف: "عرض فني" + اسم المشروع + "مقدَّم إلى: <الجهة>" + تاريخ + إحصائيات]
[فهرس: حقل TOC \o "1-3" — يولّده Word عند الفتح]
[فاصل فئة 001 "الأعمال التحضيرية"]  ← (الميزة الجديدة)
  [قسم: 001-SUR-BASE — مسح وتثبيت نقاط عامة + محتوى ملفه]
  [قسم: 001-PRM-GOV — ...]
[فاصل فئة 002 "الحفر والمخلفات"]
  [قسم: 002-EXC-FINE — ...]
... (حتى 005)
[إضافات الجهة: بند تراث (مكة) / مصفوفة امتثال (وزارة الصحة) / تذييل]
[تذييل تجريبي إن كان الترخيص تجريبياً]
```

---

## 4. طبقات البيانات — من أين تأتي كل معلومة

### 4.1 جدول الملفات

| الملف | الدور | حساسية التعديل |
|---|---|---|
| `codes_registry.json` | **SSOT الأكواد** — 65 كوداً (كل كود: `activity_name_ar/en`, `category`, `phase`, `project_ids`, `applicable_owners`, `sequence_order`, `dependencies`, `page_count`, `source_document`) | عالية جداً |
| `templates/source_documents/{CODE_ID}.docx` | **مكتبة الأنشطة** — المحتوى الحقيقي لكل نشاط (65 ملفاً) | عالية (محتوى فني) |
| `master_config.json` | المشاريع (6) + الجهات (20 داخل `owner_specifications`) + `code_ranges` (الفئات 001–005) + phases + network_types + admin_settings | عالية |
| `metadata/owner_specifications/<owner>.json` | قواعد الإلزام/المنع لكل جهة (`mandatory_codes`/`forbidden_codes`) — يستخدمها الـ Validator | عالية |
| `templates/style_templates/<owner>_style.json` | هوية الجهة البصرية: خطوط/ألوان/هوامش/ترويسة/تذييل + خيارات إضافية | متوسطة |
| `<project_id>_project_metadata.json` (الجذر) | معرفة المشروع: `activity_sequence` (ترتيب/إلزام/وصف)، `application_rules`، `typical_proposals` | متوسطة |
| `presets.json` | 11 وصفة عرض جاهزة (`<project>_<owner>_<variant>` + أكواد) | منخفضة |
| `company_profile.json` | هوية الشركة (White-label) — **لا يُكتب اسم الشركة في الكود** | منخفضة |
| `version.json` | رقم الإصدار الوحيد (`utils/app_version.py` يقرأه) | منخفضة |
| `ui/theme.py` | **SSOT الألوان والخطوط** — لا ألوان صلبة خارجه | منخفضة (كود) |

### 4.2 علاقات البيانات

```
master_config.json ──► <project_id>_project_metadata.json (معرفة المشروع)
  ├─ owner_specifications ──► metadata/owner_specifications/<owner>.json (قواعد الإلزام)
  │                            └─ style_guide ──► templates/style_templates/<owner>_style.json
  └─ code_ranges (فئات 001–005) ← تُستخدم في الفواصل + الفلترة

codes_registry.json ──► templates/source_documents/{CODE_ID}.docx (مكتبة الأنشطة)
      ▲                       ▲
      └── presets.json ───────┘   (وصفات جاهزة)

الإخراج: output/generated_documents/*.docx + output/audit_trail/*.json
```

### 4.3 قاعدة ذهبية (AGENTS.md)
- مصدر الأكواد: `codes_registry.json` فقط.
- مصدر المشاريع والجهات: `master_config.json → owner_specifications` فقط (لا يوجد مفتاح `owners` في الأعلى).
- لا تغيّر أسماء حقول JSON إلا بتحديث المحرك + الاختبارات + التوثيق معاً.

---

## 5. نظام الأكواد

### 5.1 الصيغة

```
NNN-PHASE-VARIATION
001-SUR-BASE
│   │    └── تنويع (BASE = أساسي)
│   └── مرحلة (SUR = مسح، EXC = حفر، PIP = تركيب، TST = اختبار، HND = تسليم...)
└── فئة (001 = تحضيرية ... 005 = تسليم)
```

### 5.2 الفئات الخمس (من `master_config.json → code_ranges`)

| الفئة | الاسم العربي | النطاق |
|---|---|---|
| 001 | الأعمال التحضيرية | 001-020 |
| 002 | الحفر والمخلفات | 002-050 |
| 003 | التركيب والتوصيل | 003-070 |
| 004 | الاختبار والفحص | 004-090 |
| 005 | التسليم والتشغيل | 005-999 |

### 5.3 مثال كود كامل (من `codes_registry.json`)

```json
"001-SUR-BASE": {
  "code_id": "001-SUR-BASE",
  "category": "001",
  "phase": "SUR",
  "variation": "BASE",
  "activity_name_ar": "مسح وتثبيت نقاط عامة",
  "activity_name_en": "General Surveying & Point Establishment",
  "project_ids": ["wastewater", "water_supply", "asphalt"],
  "network_types": ["S", "W", "A"],
  "applicable_owners": ["nwc", "makkah", "moh"],
  "sequence_order": 1,
  "dependencies": [],
  "image_count": 3,
  "page_count": 5,
  "source_document": "001-SUR-BASE.docx",
  "status": "active"
}
```

**القاعدة الذهبية**: مفتاح الكود في القاموس == حقل `code_id` == اسم ملف المصدر.

---

## 6. الواجهة (PyQt5 — 32 ملفاً في ui/)

### 6.1 سير المستخدم

```
1. اختيار المشروع + الجهة     → project_selector.py (مشاريع متعددة + جهة)
2. اختيار الأكواد              → checkbox_selector.py (فلترة + بحث + إلزاميات مقفلة 🔒)
3. المعاينة والتحقق             → preview_panel.py (أخطاء/تحذيرات + زر "إصلاح تلقائي")
4. معاينة الهيكل               → زر "🧭 معاينة هيكل العرض" (شجرة تفاعلية بالمراحل)
5. بوابات ما قبل البناء        → final_review_dialog.py + build_vars_dialog.py
6. البناء                      → build_progress.py (BuildWorker في QThread)
7. التصدير                     → فتح الملف / PDF / تقرير التغطية
```

### 6.2 المكونات الرئيسية

| الملف | الدور |
|---|---|
| `main_window.py` | الهيكل الرئيسي — يجمع كل اللوحات ويصل الإشارات |
| `header_widget.py` | الشريط العلوي الداكن + أزرار الإجراءات (11 زراً) |
| `project_selector.py` | اختيار المشاريع + الجهة |
| `presets_panel.py` | الأنماط الجاهزة (11 زراً بمجموعات) |
| `checkbox_selector.py` | قائمة الأكواد المفلترة + البحث |
| `preview_panel.py` | المعاينة والتحقق + زر البناء + معاينة الهيكل |
| `theme.py` | **SSOT** الألوان والخطوط (توكنز `CTX_*` للفئات) |
| `activation_dialog.py` | شاشة التفعيل (الترخيص) |
| `build_progress.py` | نافذة التقدم + خيط البناء |

---

## 7. الترخيص والأمان

- **الترخيص**: كود HMAC-SHA256 **offline** مربوط بـ Hardware ID (Machine GUID + MAC + اسم الجهاز). صيغة الكود: `ATPAS-XXXX-XXXXXXXXXXXX` (أيام منذ 2024-01-01 hex + توقيع).
- **الملفات**: `%APPDATA%/ATPAS/license.dat` + `trial.dat` (تجربة يوم واحد، مرة واحدة لكل جهاز).
- **النموذج المعتمد (D2)**: ترخيص دائم + دعم سنوي — انتهاء الدعم لا يوقف التشغيل.
- **خادم التفعيل**: مؤجل (specs/003 — يحتاج VPS).
- **التفاصيل**: `utils/license_manager.py`.

---

## 8. الاختبارات والجودة (بوابة CI)

- **498 اختباراً** (`python -m pytest tests -q`) — يجب أن تبقى خضراء بعد أي تغيير.
- **بوابة CI** (`.github/workflows/tests.yml`): تغطية engine+utils ≥ 75% (الحالية 84%) + pylint ≥ 7، على Python 3.10.
- **الحُرّاس**:
  - `tests/test_theme_contrast.py` — تباين WCAG (13 زوجاً مقفلاً) — أي توكن جديد يُقفل عليه.
  - `tests/test_import_smoke.py` — يمنع أخطاء الاستيراد الصامتة.
  - `tests/test_ui_screenshots.py` — لقطات واجهة (تتحدث عمداً فقط).
- **الاختبارات الأهم للمحرك**: `tests/test_builder.py` (سيناريوهات بناء + حقن تبعيات + عقد الإخراج العربي).

---

## 9. خريطة ملفات سريعة (لأي وكيل يبدأ)

```
ATPAS/
├── main.py                     → نقطة الدخول (ترخيص → QApplication → MainWindow)
├── engine/                     → محرك المستندات (14 ملفاً)
│   ├── builder.py              → ★ التركيب: غلاف + فهرس + أقسام + فواصل فئات
│   ├── validator.py            → فحص الأكواد (خطأ/تحذير)
│   ├── dependency_resolver.py  → إكمال التبعيات + الترتيب
│   ├── rules.py                → ★ التبعيات البديلة (SSOT — لا تنسخه)
│   ├── style_applier.py        → هوية الجهة (ترويسة/تذييل/ألوان)
│   ├── formatter.py            → تنسيق الخطوط
│   ├── boq_importer.py         → قراءة جدول الكميات (Excel)
│   ├── boq_matcher.py          → مطابقة BOQ بالأكواد (تشابه ≥70%)
│   ├── gap_handler.py          → أكواد مخصصة 999-CUS-NNN
│   ├── parser.py               → أداة استخراج قديمة (خارج مسار البناء)
│   ├── error_handler.py        → رسائل عربية + توصيات
│   ├── logger.py               → سجل + مسار تدقيق
│   └── types.py                → TypedDict عقود البيانات
├── ui/                         → الواجهة (32 ملفاً)
├── utils/                      → أدوات (25 ملفاً)
│   ├── content_library.py      → ★ تركيب المحتوى (النسخ العميق)
│   ├── docx_manipulator.py     → RTL + خطوط + حفظ
│   ├── license_manager.py      → الترخيص
│   ├── archive_index.py        → فهرس SQLite لسجل العروض
│   └── ...
├── templates/
│   ├── source_documents/       → ★ مكتبة الأنشطة (65 ملف .docx)
│   ├── style_templates/        → 20 نمط جهة (JSON)
│   └── content_approval.json   → حالات اعتماد المحتوى
├── codes_registry.json         → ★ SSOT الأكواد
├── master_config.json          → ★ SSOT المشاريع والجهات
├── presets.json                → الأنماط الجاهزة
├── company_profile.json        → هوية الشركة (White-label)
├── version.json                → رقم الإصدار
├── specs/                      → المواصفات والقرارات (001–005)
├── SSOT/                       → المراجع المعيارية
└── docs/                       → التوثيق (ARCHITECTURE/GLOSSARY/DECISIONS/ROADMAP)
```

---

## 10. روابط إلزامية قبل أي عمل

| المستند | لماذا |
|---|---|
| `AGENTS.md` | القواعد الـ11 غير القابلة للكسر + نقطة الاستئناف |
| `SSOT/ATPAS_REFERENCE_DOCUMENT_v4.1.md` | المرجع المعياري (الأرقام الحية، القرارات) |
| `docs/ROADMAP.md` | القرارات المعتمدة + الأولويات |
| `docs/GLOSSARY_AR.md` | المصطلحات الدقيقة للمجال |
| `docs/DECISIONS_AR.md` | سجل القرارات المعمارية |
| `specs/` | مواصفات الميزات (لا ميزة بلا مواصفة) |

**تحذير**: لا تقرأ ملفات `docs/archive/` كمرجع حي — إنها مجمّدة تاريخياً بأرقام قديمة.
