# نظام الأتمتة الذكي للعروض الفنية — مستند المرجعية الشامل
## Al-Rawaf Technical Proposal Automation System (ATPAS) v3.0

**آخر تحديث:** 21 أبريل 2026  
**الإصدار:** 3.0 — النظام الكامل مع واجهة رسومية وCI/CD  
**المطور:** Claude AI  
**المسؤول الأول:** د. يوسف سليم — شركة الرواف للمقاولات  
**الحالة:** Sprint 3 مكتمل ✅ | التطبيق يعمل كـ EXE | 73 اختبار يمرّ | GitHub CI فعّال

---

## 1. ملخص تنفيذي

### 1.1 ما هو ATPAS؟

نظام سطح مكتب Windows يُحوّل اختيار أكواد من واجهة رسومية عربية إلى عروض فنية Word منسقة ومكتملة — يوفّر على قسم العروض الفنية من ساعات إلى دقائق.

```
المستخدم يختار: مشروع + جهة + أكواد
        ↓
الواجهة الرسومية (PyQt5 — RTL عربي كامل)
        ↓
المحرك: تحقق → حل تبعيات → بناء Word
        ↓
ملف Word احترافي جاهز (< 5 ثوانٍ)
```

### 1.2 الوضع الحالي (21 أبريل 2026)

| المحور | الوضع |
|--------|------|
| أنواع المشاريع | 6 أنواع ✅ |
| أنواع الشبكات | 6 أنواع (S, W, A, R, C, T) ✅ |
| الجهات المالكة | 9 جهات ✅ |
| الأكواد في السجل | 64 كود نشط ✅ |
| الواجهة الرسومية | مكتملة وتعمل ✅ |
| التطبيق EXE | جاهز: dist/ATPAS/ATPAS.exe ✅ |
| إجمالي الاختبارات | 73/73 تمرّ ✅ |
| GitHub Repository | https://github.com/jou1182/ATPAS (private) ✅ |
| CI/CD | GitHub Actions تشغّل 73 اختبار على كل push ✅ |

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
│  ← content_registry.json (explicit override)             │
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
│  LAYER 4: USER INTERFACE — PyQt5 RTL ✅ مكتملة           │
│  main_window → project_selector → checkbox_selector      │
│  preview_panel → build_progress → header_widget          │
│  presets_panel | theme | motion                          │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  LAYER 5: OUTPUT & STORAGE                                │
│  output/generated_documents/                             │
│  output/audit_trail/ | output/logs/                      │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│  LAYER 6: DEVOPS & CI                                     │
│  GitHub: github.com/jou1182/ATPAS (private)              │
│  GitHub Actions: tests.yml (windows-latest, 73 tests)    │
│  PyInstaller: dist/ATPAS/ATPAS.exe (onedir)              │
└──────────────────────────────────────────────────────────┘
```

---

## 3. هيكل الملفات الكامل

```
D:\PY\ATPAS\
│
├── .gitignore                     ← يحمي الملفات الحساسة ⭐
├── .impeccable.md                 ← سياق التصميم (Luxury Industrial)
├── main.py                        ← نقطة الدخول الرئيسية
├── requirements.txt               ← المكتبات المطلوبة
├── atpas.spec                     ← إعداد PyInstaller
├── build_exe.bat                  ← سكريبت بناء EXE
│
├── master_config.json             ← SSOT المركزي ⭐
├── codes_registry.json            ← 64 كود نشط ⭐
├── presets.json                   ← قوالب اختيار سريع ⭐
│
├── metadata/owner_specifications/ ← 9 جهات مالكة
│   ├── nwc.json
│   ├── makkah.json
│   ├── moh.json
│   ├── mot.json
│   ├── nhi.json
│   ├── amana_riyadh.json
│   ├── amana_qassim.json
│   ├── swa.json
│   └── ksia.json
│
├── templates/
│   ├── style_templates/           ← 9 ملفات أنماط تنسيق
│   │   ├── nwc_style.json         ← أزرق
│   │   ├── makkah_style.json      ← أخضر + بند التراث
│   │   ├── moh_style.json         ← رمادي/أحمر + مصفوفة امتثال
│   │   ├── mot_style.json
│   │   ├── nhi_style.json
│   │   ├── amana_riyadh_style.json
│   │   ├── amana_qassim_style.json
│   │   ├── swa_style.json
│   │   └── ksia_style.json
│   └── source_documents/          ← مكتبة المحتوى (drop & go)
│       ├── {code_id}.docx         ← ملف لكل كود (حالياً: placeholder)
│       └── content_registry.json  ← تسجيل صريح لمسارات بديلة
│
├── engine/                        ← محرك المعالجة ✅
│   ├── builder.py                 ← بناء Word + content library
│   ├── validator.py               ← 8 فحوصات + رسائل عربية
│   ├── dependency_resolver.py     ← DFS transitive closure
│   ├── formatter.py               ← RTL + تنسيق عربي
│   ├── style_applier.py           ← header/footer/heritage/compliance
│   ├── parser.py                  ← استخراج فقرات + SHA-256 cache
│   ├── logger.py                  ← rotating logs + audit trail
│   └── error_handler.py           ← رسائل خطأ عربية
│
├── utils/                         ← أدوات مساعدة ✅
│   ├── content_library.py         ← registry + fuzzy match (bug-fixed)
│   ├── json_manager.py            ← load/save/merge JSON
│   ├── docx_manipulator.py        ← RTL + OOXML helpers
│   └── image_processor.py         ← استخراج/تضمين صور DPI≥300
│
├── ui/                            ← الواجهة الرسومية PyQt5 ✅
│   ├── main_window.py             ← النافذة الرئيسية + status tips
│   ├── project_selector.py        ← اختيار المشروع والجهة
│   ├── checkbox_selector.py       ← قائمة الأكواد (BiDi RTL)
│   ├── preview_panel.py           ← ملخص الاختيار + التحقق
│   ├── build_progress.py          ← نافذة البناء + QThread
│   ├── header_widget.py           ← شعار هندسي سداسي + عداد متحرك
│   ├── presets_panel.py           ← لوحة القوالب السريعة
│   ├── theme.py                   ← Luxury Industrial palette v2
│   └── motion.py                  ← prefers_reduced_motion() helpers
│
├── tests/                         ← 73 اختبار تمرّ ✅
│   ├── test_validator.py          ← 11 سيناريو
│   ├── test_builder.py            ← 7 سيناريو
│   ├── test_integration.py        ← 6 سيناريوهات E2E
│   ├── test_content_library.py    ← 26 سيناريو (TDD)
│   └── test_json_manager.py       ← 23 سيناريو (TDD)
│
├── docs/
│   ├── specification.md
│   ├── implementation-plan.md
│   ├── tasks.md
│   └── product-backlog.md
│
├── SSOT/
│   ├── ATPAS_REFERENCE_DOCUMENT_v3.0.md  ← هذا الملف
│   └── HIERARCHICAL_CODES_SYSTEM_v2.0.md ← دليل الأكواد (لم يتغير)
│
├── .github/workflows/
│   └── tests.yml                  ← GitHub Actions CI
│
├── assets/
│   └── atpas.ico                  ← أيقونة التطبيق
│
├── output/                        ← ملفات مولّدة (غير محفوظة في Git)
│   ├── generated_documents/       ← العروض الفنية المنتجة
│   ├── audit_trail/               ← سجلات JSON للعمليات
│   └── logs/                      ← rotating log files
│
└── dist/ATPAS/                    ← EXE جاهز (غير محفوظ في Git)
    ├── ATPAS.exe                  ← التطبيق القابل للتشغيل
    └── _internal/                 ← مكتبات PyInstaller
```

---

## 4. نظام التصميم — Luxury Industrial

### لوحة الألوان (v2)

| الرمز | اللون | الاستخدام |
|-------|------|----------|
| `BG` | `#EDE7D9` | خلفية التطبيق (بيج دافئ) |
| `SURFACE` | `#FEFCF7` | الأسطح المرتفعة (أبيض دافئ) |
| `HEADER` | `#152433` | الرأس (كحلي عميق) |
| `ACCENT` | `#C9921B` | التمييز (ذهبي دافئ) |
| `TEXT` | `#121B28` | النص الأساسي |
| `SUCCESS` | `#2B7549` | البناء الناجح |
| `ERROR` | `#B03030` | الأخطاء |

### مبادئ الحركة

```python
# ui/motion.py
prefers_reduced_motion() → bool   # احترام إعدادات إمكانية الوصول
motion_ms(ms)           → int    # تعطيل الحركة تلقائياً إذا لزم
motion_single_shot(ms, fn)        # QTimer مع احترام prefers_reduced_motion
```

### الحركات المنفّذة (4 حركات)

| الحركة | الملف | المدة | الغرض |
|--------|------|------|------|
| نبضة زر البناء | preview_panel.py | 420ms InOutCubic | تنبيه عند الجاهزية |
| وميض تحديد الكود | checkbox_selector.py | 200ms QTimer | تأكيد الاختيار |
| انزلاق القوالب | presets_panel.py | 230ms OutCubic/InCubic | طيّ/فتح سلس |
| شريط تقدم سلس | build_progress.py | 180ms OutCubic | تحديث فوري |

---

## 5. مبادئ SSOT

### خريطة SSOT

| المعلومة | موقعها الوحيد | من يقرأها |
|---------|-------------|---------|
| تعريف الأكواد | codes_registry.json | validator, builder, ui |
| بيانات المشاريع | *_project_metadata.json | validator, selector |
| متطلبات الجهات | owner_specifications/*.json | validator, style_applier |
| المحتوى النصي | source_documents/{code}.docx | content_library, builder |
| أنماط التنسيق | style_templates/*.json | style_applier |
| إعدادات النظام | master_config.json | جميع المكونات |
| قوالب الاختيار | presets.json | ui/presets_panel |
| سياق التصميم | .impeccable.md | جميع جلسات التطوير |

### سيناريوهات التعديل

**إضافة ملف محتوى Word لكود موجود:**
```
1. ضع الملف في templates/source_documents/{CODE_ID}.docx
2. أعد التشغيل → يظهر الكود بـ 🟢 في الواجهة تلقائياً ✅
   (لا حاجة لأي تعديل في الكود — ContentLibrary تكتشفه تلقائياً)
```

**إضافة كود جديد:**
```
1. أضف entry في codes_registry.json
2. ضع ملف {CODE_ID}.docx في templates/source_documents/ (اختياري)
3. أعد التشغيل → يظهر في الواجهة تلقائياً ✅
```

**إضافة جهة مالكة جديدة:**
```
1. أنشئ metadata/owner_specifications/{id}.json
2. أنشئ templates/style_templates/{id}_style.json
3. أضف في master_config.json → owner_specifications
4. أعد التشغيل ✅
```

**إضافة قالب اختيار سريع:**
```
1. أضف entry في presets.json
2. أعد التشغيل → يظهر في لوحة القوالب ✅
```

---

## 6. تدفق البناء (Build Flow)

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
            Builder.build()  [في QThread منفصل]
            ├── لكل كود بترتيب sequence_order:
            │   ├── ContentLibrary.find(code_id)
            │   │   ├── content_registry.json lookup (أولوية)
            │   │   ├── exact filename: {code_id}.docx
            │   │   └── fuzzy scan: case/hyphen insensitive
            │   ├── إذا وجد: _copy_docx_body() (deep XML copy)
            │   └── إذا لم يجد: placeholder من metadata
            ├── Formatter: RTL + headings + spacing
            ├── StyleApplier: header/footer/heritage/compliance
            └── TOC + page numbers
                    ↓
            output/generated_documents/{timestamp}_proposal.docx ✅
            output/audit_trail/audit_{ts}.json ✅
```

---

## 7. حالة التطوير (Sprint Tracker)

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

### Sprint 3 — GUI ✅ مكتمل

| المهمة | الحالة |
|-------|-------|
| ui/theme.py — Luxury Industrial palette v2 | ✅ |
| ui/motion.py — accessibility helpers | ✅ |
| ui/project_selector.py | ✅ |
| ui/checkbox_selector.py — BiDi RTL layout | ✅ |
| ui/preview_panel.py — validation + build btn | ✅ |
| ui/build_progress.py — QThread + progress | ✅ |
| ui/header_widget.py — hexagonal logo + counters | ✅ |
| ui/presets_panel.py — collapsible quick-select | ✅ |
| ui/main_window.py — status tips + easter egg | ✅ |
| main.py — entry point | ✅ |
| ربط UI بالمحرك الكامل | ✅ |

### Design Sprint — /delight /bolder /animate ✅ مكتمل

| المهمة | الحالة |
|-------|-------|
| Luxury Industrial design system | ✅ |
| Header: hexagonal engineering seal | ✅ |
| 4 حركات UI (نبضة، وميض، انزلاق، شريط) | ✅ |
| رسائل build هندسية بالعربية | ✅ |
| Status tips + Easter egg (≥20 كود) | ✅ |
| .impeccable.md — design context | ✅ |

### TDD Sprint ✅ مكتمل

| المهمة | الحالة |
|-------|-------|
| tests/test_integration.py — 6 E2E scenarios | ✅ |
| tests/test_content_library.py — 26 scenarios | ✅ |
| tests/test_json_manager.py — 23 scenarios | ✅ |
| إصلاح ContentLibrary.exists() fuzzy-match | ✅ |
| إجمالي: 73/73 اختبار تمرّ | ✅ |

### DevOps Sprint ✅ مكتمل

| المهمة | الحالة |
|-------|-------|
| PyInstaller EXE (onedir): dist/ATPAS/ATPAS.exe | ✅ |
| .gitignore شامل (يحمي الملفات الحساسة) | ✅ |
| GitHub Repository (private): jou1182/ATPAS | ✅ |
| GitHub Actions CI: windows-latest | ✅ |
| نسخة احتياطية سحابية | ✅ |

### Sprint 4 — Content & Polish ⬜ قادم

| المهمة | الأولوية |
|-------|---------|
| BKL-010: تقرير البناء post-build | عالية |
| BKL-011: تحسين audit_trail UX | متوسطة |
| BKL-012: USER_GUIDE_AR.md | متوسطة |
| BKL-013: Hot reload للإعدادات | منخفضة |
| BKL-014: تصدير ملخص JSON قبل البناء | منخفضة |
| إضافة ملفات .docx حقيقية في source_documents/ | **حرجة** |

---

## 8. إصلاحات الأخطاء المسجّلة

| التاريخ | الملف | الخطأ | الإصلاح |
|--------|------|------|---------|
| 21/4/2026 | utils/content_library.py | `exists()` يعود بـ False لملفات fuzzy-named | إضافة normalized fallback في `exists()` |

---

## 9. ملاحظات الأمان والخصوصية

### ملفات محمية بـ .gitignore (لا تُرفع أبداً)

| الملف | السبب |
|------|------|
| `_owners_real.json` | بيانات عملاء حقيقيين (جهات حكومية) |
| `_owner_extract.json` | أسماء موظفين حقيقيين |
| `كلمة السر الافتراضية.txt` | كلمة مرور النظام |
| `output/**` | عروض فنية مولّدة قد تحتوي بيانات مشاريع |
| `dist/` | EXE مبني (ضخم، يُبنى محلياً) |
| `__pycache__/` | ملفات Python cache |
| `*.xlsx` | وثائق Excel شخصية |

### مستودع GitHub
- **النوع:** Private — لا يراه أحد غير صاحب الحساب
- **الرابط:** https://github.com/jou1182/ATPAS

---

## 10. أرقام مرجعية سريعة

```
الأكواد الكلية:          64 كود نشط
أنواع المشاريع:           6 أنواع
أنواع الشبكات:            6 (S, W, A, R, C, T)
الجهات المالكة:           9 جهات
الاختبارات:             73/73 ✅
أقصى صفحات نموذجية:      ~100 صفحة
وقت البناء المستهدف:     < 5 ثوانٍ لـ 60 صفحة
Python المطلوبة:         3.10+
المكتبات الرئيسية:       python-docx, Pillow, PyQt5
GitHub:                  github.com/jou1182/ATPAS (private)
EXE:                     dist/ATPAS/ATPAS.exe
```

---

## 11. سجل التعديلات

| التاريخ | الإصدار | ما تغيّر |
|--------|--------|---------|
| 20/4/2026 | v1.0 | النسخة الأولى: 3 مشاريع، 3 جهات، 34 كود |
| 20/4/2026 | v2.0 | التوسيع الشامل: 6 مشاريع، 9 جهات، 64 كود |
| 21/4/2026 | v3.0 | Sprint 3 مكتمل: GUI + EXE + 73 اختبار + GitHub CI + TDD + bug fix |

---

**© 2026 Al-Rawaf Contracting Co. — جميع الحقوق محفوظة**  
**v3.0 — نظام مكتمل وجاهز للاستخدام**
