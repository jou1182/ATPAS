# نظام الأتمتة الذكي للعروض الفنية — مستند المرجعية الشامل
## Al-Rawaf Technical Proposal Automation System (ATPAS) v2.0

**آخر تحديث:** 20 أبريل 2026  
**الإصدار:** 2.0 — نظام عالمي موسّع  
**المطور:** Claude AI  
**المسؤول الأول:** د. يوسف سليم — شركة الرواف للمقاولات  
**الحالة:** Sprint 2 مكتمل ✅ | Sprint 3 (GUI) قادم

---

## 1. ملخص تنفيذي

### 1.1 ما هو ATPAS؟

نظام سطح مكتب Windows يُحوّل اختيار أكواد من واجهة رسومية إلى عروض فنية Word منسقة ومكتملة — يوفّر على قسم العروض الفنية من ساعات إلى دقائق.

```
المستخدم يختار أكواد → النظام يجمع الفقرات → ملف Word احترافي جاهز
```

### 1.2 الوضع الحالي (20 أبريل 2026)

| المحور | الوضع |
|-------|------|
| أنواع المشاريع | 6 أنواع ✅ |
| أنواع الشبكات | 6 أنواع (S, W, A, R, C, T) ✅ |
| الجهات المالكة | 9 جهات ✅ |
| الأكواد في السجل | 64 كود نشط ✅ |
| محرك التحقق | مكتمل + 11 اختبار ✅ |
| محرك البناء | مكتمل + 7 اختبار ✅ |
| مكتبة المحتوى | جاهزة (نمط drop-file) ✅ |
| الواجهة الرسومية | لم تبدأ بعد (Sprint 3) |
| اختبارات الاندماج | 18/18 تمرّ ✅ |

---

## 2. المعمارية الشاملة (7 طبقات)

```
┌──────────────────────────────────────────────────────────┐
│  LAYER 0: GOVERNANCE                                      │
│  master_config.json ← SSOT المركزي لكل إعدادات النظام   │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  LAYER 1: METADATA & TAXONOMY                             │
│  codes_registry.json (64 كود)                            │
│  6 × project_metadata.json                               │
│  9 × owner_specifications/*.json                         │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  LAYER 2: CONTENT LIBRARY                                 │
│  templates/source_documents/{code_id}.docx               │
│  ← drop file → zero-config registration                  │
│  ← fallback: placeholder text from metadata              │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  LAYER 3: PROCESSING ENGINE                               │
│  parser → validator → dependency_resolver                │
│  builder → formatter → style_applier                     │
│  logger | error_handler | content_library                │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  LAYER 4: USER INTERFACE (Sprint 3)                       │
│  main_window → project_selector → checkbox_selector      │
│  preview_panel → build_progress                          │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  LAYER 5: OUTPUT & STORAGE                                │
│  output/generated_documents/                             │
│  output/audit_trail/ | output/logs/                      │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  LAYER 6: INTEGRATION (مستقبلي)                          │
│  Database | API | Web UI | Mobile App                    │
└──────────────────────────────────────────────────────────┘
```

---

## 3. هيكل الملفات الكامل

```
D:\PY\ATPAS\
│
├── master_config.json              ← SSOT المركزي ⭐
├── codes_registry.json             ← 64 كود نشط ⭐
│
├── metadata/owner_specifications/  ← 9 ملفات جهات مالكة
│   ├── nwc.json
│   ├── makkah.json
│   ├── moh.json
│   ├── mot.json                   ← وزارة النقل (جديد)
│   ├── nhi.json                   ← الشركة الوطنية للإسكان (جديد)
│   ├── amana_riyadh.json          ← أمانة الرياض (جديد)
│   ├── amana_qassim.json          ← أمانة القصيم (جديد)
│   ├── swa.json                   ← الهيئة السعودية للمياه (جديد)
│   └── ksia.json                  ← مطار الملك سلمان (جديد)
│
├── templates/style_templates/      ← 9 ملفات أنماط
│   ├── nwc_style.json             ← أزرق
│   ├── makkah_style.json          ← أخضر + بند التراث
│   ├── moh_style.json             ← رمادي/أحمر + مصفوفة امتثال
│   ├── mot_style.json             ← أخضر حكومي (جديد)
│   ├── nhi_style.json             ← كحلي (جديد)
│   ├── amana_riyadh_style.json    ← تيل (جديد)
│   ├── amana_qassim_style.json    ← بني غامق (جديد)
│   ├── swa_style.json             ← أزرق مائي (جديد)
│   └── ksia_style.json            ← كحلي/ذهبي (جديد)
│
├── templates/source_documents/     ← مكتبة المحتوى (drop & go)
│   └── {code_id}.docx             ← ملف لكل كود
│
├── [project_metadata].json         ← 6 ملفات بيانات المشاريع
│   ├── wastewater_project_metadata.json
│   ├── water_supply_project_metadata.json
│   ├── asphalt_project_metadata.json
│   ├── road_maintenance_project_metadata.json    (جديد)
│   ├── general_construction_project_metadata.json (جديد)
│   └── water_transmission_project_metadata.json  (جديد)
│
├── engine/                         ← محرك المعالجة (مكتمل ✅)
│   ├── __init__.py
│   ├── parser.py                  ← استخراج فقرات + صور + SHA-256 cache
│   ├── validator.py               ← 8 فحوصات + رسائل عربية
│   ├── dependency_resolver.py     ← DFS transitive closure
│   ├── builder.py                 ← بناء Word + content library
│   ├── formatter.py               ← RTL + تنسيق عربي
│   ├── style_applier.py           ← header/footer/heritage/compliance
│   ├── logger.py                  ← rotating logs + audit trail
│   └── error_handler.py           ← رسائل خطأ عربية
│
├── utils/                          ← أدوات مساعدة (مكتملة ✅)
│   ├── json_manager.py            ← load/save/merge JSON
│   ├── image_processor.py         ← استخراج/تضمين صور DPI≥300
│   ├── docx_manipulator.py        ← RTL + OOXML helpers
│   └── content_library.py         ← مكتبة المحتوى (registry+fuzzy)
│
├── ui/                             ← الواجهة الرسومية (Sprint 3)
│   └── __init__.py
│
├── tools/                          ← أدوات CLI
│   ├── import_content.py          ← split/register/list محتوى
│   └── extend_registry.py         ← إضافة أكواد جديدة
│
├── tests/                          ← 18/18 اختبار تمرّ ✅
│   ├── test_validator.py          ← 11 سيناريو
│   └── test_builder.py            ← 7 سيناريو
│
├── output/
│   ├── audit_trail/               ← سجلات JSON للعمليات
│   └── logs/                      ← rotating log files
│
├── SSOT/
│   ├── ATPAS_REFERENCE_DOCUMENT_v2.0.md  ← هذا الملف
│   └── HIERARCHICAL_CODES_SYSTEM_v2.0.md ← دليل الأكواد
│
├── docs/
│   ├── specification.md
│   ├── implementation-plan.md
│   └── tasks.md
│
└── requirements.txt
```

---

## 4. مبادئ SSOT

### خريطة SSOT

| المعلومة | موقعها الوحيد | من يقرأها |
|---------|-------------|---------|
| تعريف الأكواد | codes_registry.json | validator, builder, ui |
| بيانات المشاريع | *_project_metadata.json | validator, selector |
| متطلبات الجهات | owner_specifications/*.json | validator, style_applier |
| المحتوى النصي | source_documents/{code}.docx | content_library, builder |
| أنماط التنسيق | style_templates/*.json | style_applier |
| إعدادات النظام | master_config.json | جميع المكونات |

### سيناريوهات التعديل

**إضافة كود جديد:**
```
1. أضف entry في codes_registry.json
2. ضع ملف {CODE_ID}.docx في templates/source_documents/
3. أعد التشغيل → يظهر في الواجهة تلقائياً ✅
```

**إضافة جهة مالكة جديدة:**
```
1. أنشئ metadata/owner_specifications/{id}.json
2. أنشئ templates/style_templates/{id}_style.json
3. أضف في master_config.json → owner_specifications
4. أعد التشغيل ✅
```

**إضافة نوع مشروع جديد:**
```
1. أنشئ {project_id}_project_metadata.json
2. أضف الأكواد الجديدة في codes_registry.json
3. أضف في master_config.json → projects
4. أعد التشغيل ✅
```

---

## 5. تدفق البناء (Build Flow)

```
المستخدم يختار: project_id + owner_id + [code_ids]
                    ↓
            Validator.validate()
            ├── الكود موجود وفعّال؟
            ├── الكود ينطبق على هذا المشروع؟
            ├── الكود غير محظور للجهة؟
            ├── لا تعارض بين الأكواد الحصرية؟
            ├── الأكواد الإلزامية للجهة موجودة؟
            └── التبعيات مكتملة؟ (تحذير)
                    ↓
        DependencyResolver.resolve()
        ← DFS transitive closure (آمن من الحلقات)
                    ↓
            Builder.build()
            ├── لكل كود بالترتيب:
            │   ├── ContentLibrary.find(code_id)
            │   │   ├── registry JSON lookup
            │   │   ├── exact filename match
            │   │   └── case-insensitive scan
            │   ├── إذا وجد: _copy_docx_body() (deep XML copy)
            │   └── إذا لم يجد: placeholder من metadata
            ├── Formatter: RTL + headings + spacing
            ├── StyleApplier: header/footer/heritage/compliance
            └── TOC + page numbers
                    ↓
            output/{timestamp}_proposal.docx ✅
            output/audit_trail/audit_{ts}.json ✅
```

---

## 6. حالة التطوير (Sprint Tracker)

### Sprint 1 — Data Foundation ✅ مكتمل

| المهمة | الحالة |
|-------|-------|
| هيكل المجلدات | ✅ |
| codes_registry.json (34 كود أولي) | ✅ |
| 3 project metadata files | ✅ |
| 3 owner specs + 3 style templates | ✅ |
| utils/json_manager.py | ✅ |

### Sprint 2 — Engine ✅ مكتمل

| المهمة | الحالة |
|-------|-------|
| engine/logger.py | ✅ |
| engine/error_handler.py | ✅ |
| engine/validator.py (11 اختبار) | ✅ |
| engine/dependency_resolver.py | ✅ |
| utils/image_processor.py | ✅ |
| utils/docx_manipulator.py | ✅ |
| engine/parser.py (SHA-256 cache) | ✅ |
| engine/formatter.py | ✅ |
| engine/style_applier.py | ✅ |
| engine/builder.py (7 اختبار) | ✅ |
| utils/content_library.py | ✅ |
| tools/import_content.py | ✅ |
| tools/extend_registry.py | ✅ |

### Gap Closing Sprint ✅ مكتمل

| المهمة | الحالة |
|-------|-------|
| +30 كود في codes_registry.json (إجمالي 64) | ✅ |
| road_maintenance_project_metadata.json | ✅ |
| general_construction_project_metadata.json | ✅ |
| water_transmission_project_metadata.json | ✅ |
| 6 owner specs جديدة | ✅ |
| 6 style templates جديدة | ✅ |
| master_config.json محدّث (6 مشاريع، 9 جهات) | ✅ |
| 18/18 اختبارات تمرّ | ✅ |

### Sprint 3 — GUI ⬜ قادم

| المهمة | الحالة |
|-------|-------|
| ui/project_selector.py | ⬜ |
| ui/checkbox_selector.py | ⬜ |
| ui/preview_panel.py | ⬜ |
| ui/build_progress.py | ⬜ |
| ui/main_window.py | ⬜ |
| main.py (entry point) | ⬜ |
| ربط UI بالمحرك | ⬜ |

### Sprint 4 — Integration & Polish ⬜

| المهمة | الحالة |
|-------|-------|
| tests/test_integration.py | ⬜ |
| docs/USER_GUIDE_AR.md | ⬜ |
| اختبارات شاملة | ⬜ |

---

## 7. القاموس التقني

| العربية | الإنجليزية | المعنى |
|--------|-----------|-------|
| كود | Code | مفتاح يشير لنشاط محدد: 001-SUR-BASE |
| سجل الأكواد | Codes Registry | codes_registry.json — قاموس كل الأكواد |
| مكتبة المحتوى | Content Library | مجلد source_documents/{code}.docx |
| التبعية | Dependency | كود يجب وجوده قبل كود آخر |
| الحصرية | Mutually Exclusive | مجموعة لا يُختار منها إلا كود واحد |
| محرك البناء | Builder | engine/builder.py — ينتج ملف Word |
| محرك التحقق | Validator | engine/validator.py — 8 فحوصات |
| حل التبعيات | Dependency Resolver | DFS لإيجاد كل المتطلبات |
| نمط SSOT | Single Source of Truth | كل بيانة في مكان واحد فقط |
| خط تدفق المحتوى | Content Pipeline | Drop docx → auto-register → build |

---

## 8. أرقام مرجعية سريعة

```
الأكواد الكلية:        64 كود نشط
أنواع المشاريع:         6 أنواع
أنواع الشبكات:          6 (S, W, A, R, C, T)
الجهات المالكة:         9 جهات
الاختبارات:           18/18 ✅
أقصى صفحات نموذجية:    ~100 صفحة
وقت البناء المستهدف:   < 5 ثوانٍ لـ 60 صفحة
Python المطلوبة:       3.9+
المكتبات الرئيسية:     python-docx, Pillow, PyQt5, openpyxl
```

---

## 9. سجل التعديلات

| التاريخ | الإصدار | ما تغيّر |
|--------|--------|---------|
| 20/4/2026 | v1.0 | النسخة الأولى: 3 مشاريع، 3 جهات، 34 كود |
| 20/4/2026 | v2.0 | التوسيع الشامل: 6 مشاريع، 9 جهات، 64 كود |

---

**© 2026 Al-Rawaf Contracting Co. — جميع الحقوق محفوظة**
