# نظام الأتمتة الذكي للعروض الفنية - مستند المرجعية الشامل
## Al-Rawaf Technical Proposal Automation System (ATPAS) v1.0

**آخر تحديث:** 20 أبريل 2026  
**المطور الرئيسي:** Claude AI  
**المسؤول الأول:** د. يوسف سليم (Dr. Youssef Seleim)  
**المنظمة:** شركة الرواف للمقاولات

---

## 📑 جدول المحتويات

1. [نظرة عامة على النظام](#1-نظرة-عامة-على-النظام)
2. [المعمارية الشاملة](#2-المعمارية-الشاملة)
3. [البيانات والهيكل](#3-البيانات-والهيكل)
4. [دورة حياة النظام](#4-دورة-حياة-النظام)
5. [هيكل الملفات والمجلدات](#5-هيكل-الملفات-والمجلدات)
6. [مبادئ SSOT والمرونة](#6-مبادئ-ssot-والمرونة)
7. [الخطة التطبيقية](#7-الخطة-التطبيقية)
8. [الأسئلة الحتمية](#8-الأسئلة-الحتمية)
9. [القاموس والمصطلحات](#9-القاموس-والمصطلحات)
10. [ملاحظات تقنية](#10-ملاحظات-تقنية)

---

## 1. نظرة عامة على النظام

### 1.1 الهدف الرئيسي

بناء **نظام أتمتة ذكي** يسمح بإنشاء عروض فنية احترافية بسرعة وكفاءة من خلال:
- ✅ قائمة أكواد بسيطة (001, 002, 003, ...)
- ✅ واجهة رسومية سهلة (Checkbox list)
- ✅ تجميع تلقائي للفقرات والصور
- ✅ ملف Word منسق نهائي

### 1.2 المشكلة التي يحلها

**الوضع الحالي:**
```
قائد الطاقم ← يكتب عرض يدويّاً ← نسخ لصق من ملفات متعددة ← تنسيق يدوي ← وقت طويل ❌
```

**الوضع المستهدف:**
```
قائد الطاقم ← يختار أكواد من واجهة رسومية ← النظام ينتج ملف كامل منسق ← دقائق ✅
```

### 1.3 المميزات الأساسية

| الميزة | الوصف |
|---------|-------|
| **مكتبة موحدة** | ملف واحد لكل نوع مشروع (صرف، مياه، أسفلت) |
| **أكواد رقمية بسيطة** | 001, 002, 003, ... حتى 300+ |
| **واجهة رسومية** | اختيار الأكواد بـ Checkboxes |
| **صور مضمنة** | الصور تُحفظ تلقائياً بجودتها |
| **تسلسل منطقي** | التنبيه عند الأكواد الناقصة |
| **مرونة عالية** | يسهل التعديل والتطوير المستقبلي |
| **توثيق شامل** | كل تغيير يُسجل في Audit Trail |

### 1.4 الفريق والمسؤوليات

```
د. يوسف سليم (Dr. Jou)
├── المسؤول الأول عن المتطلبات
├── اختبار النموذج الأول
└── تدريب الفريق

Claude AI
├── تطوير المحرك (Engine)
├── بناء الواجهة الرسومية
└── التوثيق الفنية

فريق الرواف (4 مهندسين)
├── اختبار الاستخدام
├── تقديم ملاحظات
└── الاستخدام اليومي
```

---

## 2. المعمارية الشاملة

### 2.1 الطبقات الرئيسية (7 طبقات)

```
┌───────────────────────────────────────────────────────────┐
│  LAYER 0: GOVERNANCE LAYER                                │
│  (طبقة الحوكمة - master_config.json)                     │
│  ← كل البيانات الوصفية تُدار من هنا                      │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│  LAYER 1: METADATA & TAXONOMY LAYER                       │
│  (طبقة البيانات الوصفية)                                  │
│  ← projects/ ← codes_registry.json ← owner_specs/         │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│  LAYER 2: CONTENT LIBRARY LAYER                           │
│  (مكتبة المحتوى)                                          │
│  ← Wastewater_Master.docx ← Sections JSON ← Assets        │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│  LAYER 3: PROCESSING ENGINE LAYER                         │
│  (محرك المعالجة)                                          │
│  ← parser ← validator ← builder ← formatter               │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│  LAYER 4: USER INTERFACE LAYER                            │
│  (الواجهة الرسومية)                                       │
│  ← MainWindow ← CheckboxSelector ← PreviewPanel           │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│  LAYER 5: OUTPUT & STORAGE LAYER                          │
│  (المخرجات والتخزين)                                      │
│  ← Generated Documents ← Logs ← Audit Trail               │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│  LAYER 6: INTEGRATION LAYER (Future)                      │
│  (طبقة التكامل - للتطوير المستقبلي)                      │
│  ← Database ← API ← Web UI ← Mobile App                   │
└───────────────────────────────────────────────────────────┘
```

### 2.2 تدفق البيانات

```
USER INPUT (اختيار أكواد)
        ↓
    PARSER (فك ترميز الأكواد)
        ↓
    VALIDATOR (التحقق من الصحة والتبعيات)
        ↓
    DEPENDENCY RESOLVER (حل التبعيات)
        ↓
    CONTENT EXTRACTOR (استخراج الفقرات والصور)
        ↓
    FORMATTER (تطبيق التنسيق)
        ↓
    STYLE APPLIER (تطبيق أسلوب الجهة المالكة)
        ↓
    DOCUMENT BUILDER (بناء ملف Word)
        ↓
    OUTPUT GENERATOR (حفظ الملف + تقارير)
        ↓
OUTPUT (ملف Word + سجلات)
```

---

## 3. البيانات والهيكل

### 3.1 نموذج البيانات الرئيسي

#### **master_config.json** (الملف المركزي الرئيسي)

```json
{
  "system": {
    "name": "Al-Rawaf Technical Proposal Automation System",
    "version": "1.0.0",
    "last_updated": "2026-04-20",
    "maintainer": "Dr. Youssef Seleim",
    "organization": "Al-Rawaf Contracting Co."
  },

  "projects": {
    "wastewater": {
      "id": "wastewater",
      "name_ar": "نظام الصرف الصحي",
      "name_en": "Wastewater System",
      "source_file": "templates/source_documents/Wastewater_Master.docx",
      "metadata_file": "metadata/projects/wastewater.json",
      "total_codes": 85,
      "owner_specs": ["nwc", "makkah"],
      "activities": ["surveying", "excavation", "installation", "testing", "completion"],
      "last_modified": "2026-04-20"
    },
    "water_supply": { "id": "water_supply", "..." },
    "asphalt": { "id": "asphalt", "..." }
  },

  "code_ranges": {
    "001-050": "General & Preparatory Activities",
    "051-100": "Excavation & Earthwork",
    "101-150": "Installation & Assembly",
    "151-200": "Testing & Commissioning",
    "201-250": "Completion & Handover",
    "251-300": "Special Activities"
  },

  "owner_specifications": ["nwc", "makkah", "moh"],

  "ui_config": {
    "window_title": "Al-Rawaf Proposal Builder",
    "theme": "dark",
    "default_project": "wastewater"
  }
}
```

#### **codes_registry.json** (سجل الأكواس الموحد)

```json
{
  "metadata": {
    "total_codes": 300,
    "last_updated": "2026-04-20",
    "format_version": "2.0"
  },

  "codes": {
    "001": {
      "code_id": "001",
      "activity_name_ar": "مسح وتثبيت نقاط",
      "activity_name_en": "Surveying and Point Establishment",
      "project_id": "wastewater",
      "section": "الأعمال التحضيرية",
      "paragraph_index": 0,
      "has_images": true,
      "image_count": 3,
      "sequence_order": 1,
      "dependencies": [],
      "owner_specs_required": ["nwc", "makkah"],
      "tags": ["surveying", "preparatory"],
      "created_date": "2026-04-01",
      "last_modified": "2026-04-15",
      "version": "2.1",
      "status": "active"
    },

    "002": {
      "code_id": "002",
      "activity_name_ar": "الحصول على الرخص والموافقات",
      "activity_name_en": "Obtaining Permits and Approvals",
      "project_id": "wastewater",
      "section": "الأعمال التحضيرية",
      "paragraph_index": 1,
      "has_images": false,
      "image_count": 0,
      "sequence_order": 2,
      "dependencies": ["001"],
      "owner_specs_required": ["nwc", "makkah"],
      "tags": ["legal", "preparatory"],
      "created_date": "2026-04-01",
      "last_modified": "2026-04-15",
      "version": "1.0",
      "status": "active"
    },

    "003": {
      "code_id": "003",
      "activity_name_ar": "اعتماد المخططات والرسومات",
      "activity_name_en": "Approval of Plans and Drawings",
      "project_id": "wastewater",
      "section": "الأعمال التحضيرية",
      "paragraph_index": 2,
      "has_images": true,
      "image_count": 5,
      "sequence_order": 3,
      "dependencies": ["001", "002"],
      "owner_specs_required": ["nwc", "makkah"],
      "tags": ["documentation", "preparatory"],
      "created_date": "2026-04-01",
      "last_modified": "2026-04-20",
      "version": "3.0",
      "status": "active"
    }

    // ... حتى 300+ كود
  }
}
```

#### **projects/wastewater.json**

```json
{
  "project_id": "wastewater",
  "name_ar": "نظام الصرف الصحي",
  "name_en": "Wastewater System",
  "description_ar": "نظام متكامل لمعالجة وتجميع مياه الصرف الصحي",
  "total_codes": 85,
  
  "activities_sequence": [
    {
      "activity_id": "001-020",
      "activity_name_ar": "الأعمال التحضيرية",
      "activity_name_en": "Preparatory Activities",
      "codes": ["001", "002", "003", "004", "005"],
      "sequence": 1,
      "prerequisites": []
    },
    {
      "activity_id": "021-050",
      "activity_name_ar": "أعمال الحفر والمخلفات",
      "activity_name_en": "Excavation and Waste",
      "codes": ["021", "022", "023"],
      "sequence": 2,
      "prerequisites": ["001-020"]
    },
    {
      "activity_id": "051-080",
      "activity_name_ar": "أعمال التركيب والاختبار",
      "activity_name_en": "Installation and Testing",
      "codes": ["051", "052", "053"],
      "sequence": 3,
      "prerequisites": ["001-050"]
    }
  ]
}
```

#### **owner_specifications/nwc.json**

```json
{
  "owner_id": "nwc",
  "owner_name_ar": "الشركة الوطنية للمياه",
  "owner_name_en": "National Water Company",
  "default_codes_range": ["001", "050"],
  
  "mandatory_sections": [
    "safety",
    "quality_control",
    "environmental_compliance",
    "site_management"
  ],
  
  "style_guide": "nwc_style.json",
  
  "specific_requirements": {
    "header_format": "NWC Standard Header",
    "footer_format": "NWC Standard Footer",
    "color_scheme": "blue_white",
    "font_family": "Times New Roman",
    "font_size_body": 12,
    "font_size_heading": 14
  }
}
```

### 3.2 أمثلة على المحتوى المستخرج

#### **wastewater_sections.json** (مستخرجات معالجة)

```json
{
  "section_001": {
    "code_id": "001",
    "heading": "مسح وتثبيت نقاط المشروع",
    "content": "يتم إجراء مسح شامل للموقع وتثبيت نقاط المرجعية...",
    "images": [
      {
        "image_id": "img_001_01",
        "filename": "surveying_equipment_001.jpg",
        "caption": "أجهزة المسح المستخدمة",
        "size_bytes": 245000,
        "format": "jpg",
        "dpi": 300
      },
      {
        "image_id": "img_001_02",
        "filename": "survey_plan_001.jpg",
        "caption": "خطة المسح",
        "size_bytes": 340000,
        "format": "jpg",
        "dpi": 300
      }
    ],
    "tables": [
      {
        "table_id": "tbl_001_01",
        "caption": "نقاط المسح",
        "columns": ["Point ID", "X Coordinate", "Y Coordinate", "Elevation"]
      }
    ],
    "extracted_date": "2026-04-20",
    "extraction_version": "1.0"
  },

  "section_002": { "..." }
}
```

---

## 4. دورة حياة النظام

### 4.1 مراحل التشغيل الأساسية

```
PHASE 1: INITIALIZATION (التهيئة)
├── قراءة master_config.json
├── التحقق من سلامة البيانات الوصفية
├── تحميل ملفات المشاريع
└── جاهزية الواجهة الرسومية
    ↓

PHASE 2: USER INPUT (إدخال المستخدم)
├── فتح واجهة رسومية
├── تحديد المشروع
├── اختيار الجهة المالكة
├── اختيار الأكواد (Checkboxes)
└── معاينة حية
    ↓

PHASE 3: VALIDATION (التحقق)
├── فحص توفر جميع الأكواد
├── فحص التبعيات (Dependencies)
├── التحقق من التسلسل المنطقي
└── إطلاق تحذيرات إن لزم
    ↓

PHASE 4: PROCESSING (المعالجة)
├── استخراج الفقرات من الملف الأساسي
├── استخراج الصور بجودتها
├── ترتيب العناصر حسب الأكواد
├── حل أي تبعيات تلقائية
└── تطبيق تنسيق الجهة المالكة
    ↓

PHASE 5: OUTPUT (الإخراج)
├── بناء ملف Word نهائي
├── حفظ الملف
├── توليد Build Report
├── تسجيل Audit Trail
└── إطلاع المستخدم بالنجاح
```

### 4.2 رسم تدفق العمليات (Flowchart)

```
START
  ↓
[قراءة master_config.json] ← إذا فشل: ERROR & EXIT
  ↓
[عرض واجهة المشروع والجهة المالكة]
  ↓
[عرض قائمة الأكواد (Checkboxes)]
  ↓
[المستخدم يختار الأكواد]
  ↓
[النقر على "Preview"]
  ↓
[فحص التبعيات]
  ├─ إذا ناقصة → تحذير + اقتراح إضافتها
  └─ إذا صحيح → متابعة
  ↓
[عرض معاينة حية]
  ↓
[المستخدم يأكد]
  ↓
[البدء بمعالجة المحتوى]
  ├─ فك ترميز الملف الأساسي
  ├─ استخراج الفقرات
  ├─ استخراج الصور
  └─ ترتيب العناصر
  ↓
[تطبيق التنسيق]
  ├─ أسلوب الجهة المالكة
  ├─ ترقيم الصفحات
  └─ فهرس المحتويات
  ↓
[بناء ملف Word]
  ↓
[حفظ الملف]
  ↓
[توليد التقارير]
  ├─ Build Report (HTML)
  └─ Audit Trail (JSON)
  ↓
[عرض رسالة النجاح]
  ↓
END
```

---

## 5. هيكل الملفات والمجلدات

### 5.1 الهيكل الكامل

```
al_rawaf_proposal_system/
│
├── 📋 README.md                          ← نقطة البداية
├── 📋 ARCHITECTURE.md                    ← التوثيق المعماري
├── 📋 USER_GUIDE.md                      ← دليل المستخدم
├── 📋 DEVELOPER_GUIDE.md                 ← دليل المطور
│
├── 🔧 config/                            ← طبقة التكوين
│   ├── master_config.json                ← الملف المركزي الرئيسي ⭐
│   ├── schema_definitions.json           ← تعريف هيكل البيانات
│   ├── validation_rules.json             ← قواعد التحقق
│   ├── ui_config.json                    ← إعدادات الواجهة
│   └── version_control.json              ← إدارة الإصدارات
│
├── 📋 metadata/                          ← طبقة البيانات الوصفية
│   ├── codes_registry.json               ← سجل الأكواد ⭐
│   ├── activity_taxonomy.json            ← تصنيف الأنشطة
│   ├── dependencies_map.json             ← خريطة التبعيات
│   ├── projects/
│   │   ├── wastewater.json
│   │   ├── water_supply.json
│   │   └── asphalt.json
│   └── owner_specifications/
│       ├── nwc.json
│       ├── makkah.json
│       └── moh.json
│
├── 📚 templates/                         ← مكتبة المحتوى
│   ├── source_documents/                 ← الملفات الأساسية
│   │   ├── Wastewater_Master.docx
│   │   ├── Water_Supply_Master.docx
│   │   └── Asphalt_Master.docx
│   ├── extracted_sections/               ← مستخرجات معالجة
│   │   ├── wastewater_sections.json
│   │   ├── water_sections.json
│   │   └── asphalt_sections.json
│   └── style_templates/
│       ├── base_style.json
│       ├── nwc_style.json
│       └── makkah_style.json
│
├── ⚙️ engine/                             ← محرك المعالجة
│   ├── __init__.py
│   ├── parser.py                         ← فك ترميز الملفات
│   ├── validator.py                      ← التحقق من الصحة
│   ├── builder.py                        ← بناء الملفات
│   ├── formatter.py                      ← التنسيق
│   ├── dependency_resolver.py            ← حل التبعيات
│   ├── style_applier.py                  ← تطبيق الأسلوب
│   ├── logger.py                         ← تسجيل العمليات
│   └── error_handler.py                  ← معالجة الأخطاء
│
├── 🖥️ ui/                                 ← الواجهة الرسومية
│   ├── main_window.py                    ← النافذة الرئيسية
│   ├── checkbox_selector.py              ← قائمة الأكواد التفاعلية
│   ├── preview_panel.py                  ← معاينة حية
│   ├── settings_dialog.py                ← الإعدادات
│   ├── project_selector.py               ← تحديد المشروع
│   ├── owner_selector.py                 ← تحديد الجهة المالكة
│   └── build_progress.py                 ← شريط التقدم
│
├── 🔨 utils/                             ← أدوات مساعدة
│   ├── file_handler.py                   ← معالجة الملفات
│   ├── image_processor.py                ← معالجة الصور
│   ├── docx_manipulator.py               ← معالجة Word
│   ├── json_manager.py                   ← إدارة JSON
│   └── encryption.py                     ← التشفير (اختياري)
│
├── 📤 output/                            ← المخرجات
│   ├── generated_documents/              ← الملفات المُنتجة
│   ├── build_logs/                       ← سجلات البناء
│   │   └── build_20260420_143025.log
│   ├── audit_trail/                      ← تتبع التدقيق
│   │   └── audit_20260420_143025.json
│   └── reports/                          ← تقارير البناء
│       └── build_report_20260420.html
│
├── ✅ tests/                             ← الاختبارات
│   ├── test_parser.py
│   ├── test_validator.py
│   ├── test_builder.py
│   ├── test_integration.py
│   └── test_fixtures/
│
├── 📖 docs/                              ← التوثيق الإضافية
│   ├── ARCHITECTURE.md                   ← هذا الملف
│   ├── INSTALLATION.md
│   ├── USER_GUIDE.md
│   ├── DEVELOPER_GUIDE.md
│   ├── API_REFERENCE.md
│   ├── CODES_MANUAL.md                   ← قاموس الأكواد
│   └── TROUBLESHOOTING.md
│
├── 📦 requirements.txt                   ← المكتبات المطلوبة
├── 🔧 setup.py                           ← ملف التثبيت
├── 🚀 main.py                            ← نقطة الدخول الرئيسية
└── 📖 README.md                          ← الملف التعريفي

```

### 5.2 مثال على مسار ملف محدد

```
الملف: Wastewater_Master.docx (الملف الأساسي)
├── الموقع: templates/source_documents/Wastewater_Master.docx
├── الحجم: ~50 MB (مع الصور)
├── عدد الفقرات: ~85 فقرة
└── كل فقرة ← كود (001 إلى 085)

عند فك الترميز (Parsing):
├── استخراج النص ← wastewater_sections.json
├── استخراج الصور ← images/wastewater/img_*.jpg
├── استخراج الجداول ← tables/wastewater_tables.json
└── حفظ البيانات الوصفية

عند الاستخدام (Usage):
├── المستخدم يختار: "001, 003, 005, 010"
├── النظام يقرأ codes_registry.json
├── يستخرج الفقرات من wastewater_sections.json
├── يجمعها بالترتيب
└── ينتج ملف Word نهائي
```

---

## 6. مبادئ SSOT والمرونة

### 6.1 SSOT (Single Source of Truth)

**المبدأ الأساسي:**
```
كل معلومة توجد في مكان واحد فقط
↓
إذا أردت تعديلها، تعديل واحد فقط
↓
التأثير ينتشر تلقائياً في النظام كله
```

### 6.2 خريطة SSOT

| المعلومة | موقعها الوحيد | الملفات المستخدمة |
|---------|------------|----------------|
| تعريف الأكواس | codes_registry.json | parser.py, builder.py |
| بيانات المشروع | projects/wastewater.json | validator.py, selector.py |
| الجهات المالكة | owner_specifications/ | style_applier.py |
| المحتوى النصي | Wastewater_Master.docx | parser.py → sections.json |
| الصور | داخل الملف الأساسي | image_processor.py |
| قواعد التحقق | validation_rules.json | validator.py |

### 6.3 سيناريوهات التعديل المستقبلي

#### **السيناريو 1: إضافة كود جديد**
```
الخطوة 1: تعديل codes_registry.json فقط
├── أضف entry جديد: {"code": "086", ...}
└── تم ✅

الخطوة 2: إذا كان لها محتوى:
├── أضفها في الملف الأساسي (Wastewater_Master.docx)
└── أعد فك الترميز (Re-parse)

الخطوة 3: تم ✅
```

#### **السيناريو 2: تغيير أسلوب الجهة المالكة**
```
الخطوة 1: عدّل owner_specifications/nwc.json فقط
├── غيّر الألوان
├── غيّر الخطوط
└── تم ✅

الخطوة 2: كل الملفات الجديدة المُنتجة ستستخدم الأسلوب الجديد ✅
```

#### **السيناريو 3: إضافة جهة مالكة جديدة**
```
الخطوة 1: أنشئ owner_specifications/new_owner.json فقط
├── حدد الأسلوب
├── حدد المتطلبات الخاصة
└── تم ✅

الخطوة 2: عدّل master_config.json
├── أضف الجهة الجديدة في owner_specifications
└── تم ✅

الخطوة 3: الواجهة الرسومية ستعرضها تلقائياً ✅
```

#### **السيناريو 4: التطور المستقبلي - إضافة قاعدة بيانات**
```
الوضع الحالي: JSON files
↓
التطور المستقبلي: PostgreSQL Database
↓
التأثير على النظام:
├── فقط غيّر metadata/loader.py
├── باقي النظام لا يتغير
└── لأن واجهة الوصول موحدة ✅
```

---

## 7. الخطة التطبيقية

### 7.1 الجدول الزمني الشامل (4 أسابيع)

#### **الأسبوع 1: التحضير والتحليل**

**الأهداف:**
- □ تحليل الملفات الموجودة لديك
- □ بناء codes_registry.json الأولي
- □ بناء metadata/projects/
- □ بناء owner_specifications/

**المخرجات:**
- ✅ codes_registry.json (100 كود على الأقل)
- ✅ 3 ملفات metadata للمشاريع
- ✅ 2 ملف owner_specifications
- ✅ master_config.json

**المسؤول:** د. يوسف + Claude

---

#### **الأسبوع 2: بناء المحرك**

**الأهداف:**
- □ تطوير parser.py (فك ترميز الملفات)
- □ تطوير validator.py (التحقق)
- □ تطوير builder.py (بناء الملفات)
- □ تطوير image_processor.py

**المخرجات:**
- ✅ محرك يعمل 100%
- ✅ اختبارات وحدة (Unit Tests)
- ✅ نموذج عملي يعمل

**الاختبار:** على نموذج صغير (5 أكواد فقط)

---

#### **الأسبوع 3: بناء الواجهة الرسومية**

**الأهداف:**
- □ تطوير main_window.py
- □ تطوير checkbox_selector.py
- □ تطوير preview_panel.py
- □ تطوير project/owner_selector.py

**المخرجات:**
- ✅ واجهة رسومية كاملة
- ✅ معاينة حية تعمل
- ✅ تكامل كامل مع المحرك

**الاختبار:** على 20-30 كود

---

#### **الأسبوع 4: الاختبار والتوثيق**

**الأهداف:**
- □ اختبار شامل (50+ سيناريو)
- □ كتابة التوثيق الكاملة
- □ دليل المستخدم
- □ دليل المطور

**المخرجات:**
- ✅ نظام جاهز للاستخدام
- ✅ توثيق شاملة
- ✅ دليل المستخدم (بالعربية والإنجليزية)

**التدريب:** فريق الرواف

---

### 7.2 نقاط التحكم (Checkpoints)

```
Week 1 End:
├── ✅ كل البيانات الوصفية جاهزة؟
├── ✅ codes_registry.json كامل؟
└── ✅ metadata موثوق؟

Week 2 End:
├── ✅ المحرك يعمل بلا أخطاء؟
├── ✅ الصور تُحفظ بجودتها؟
└── ✅ النموذج الأول يعمل؟

Week 3 End:
├── ✅ الواجهة سهلة الاستخدام؟
├── ✅ المعاينة حية تعمل؟
└── ✅ لا توجد مشاكل تكامل؟

Week 4 End:
├── ✅ كل الاختبارات تمرّ؟
├── ✅ التوثيق شاملة؟
└── ✅ الفريق مدرّب؟
```

---

## 8. الأسئلة الحتمية

### 8.1 أسئلة فنية

**السؤال 1.1: هيكل الملفات الحالية**
```
كم ملف Word لديك الآن؟
├── الصرف الصحي: ? صفحة, ? فقرة
├── المياه: ? صفحة, ? فقرة
└── الأسفلت: ? صفحة, ? فقرة
```

**السؤال 1.2: التنسيق**
```
هل الملفات الحالية:
├── منسقة بشكل موحد؟
├── بنفس الخط والحجم؟
└── بنفس الأسلوب؟
```

### 8.2 أسئلة تنظيمية

**السؤال 2.1: الأولويات**
```
أي مشروع تريد أن تبدأ معه؟
├── الصرف الصحي
├── المياه
└── الأسفلت
```

**السؤال 2.2: الاختبار**
```
هل تريد نموذج تجريبي أولاً؟
├── نعم, بـ 30-50 كود فقط
└── لا, ابدأ بالنسخة الكاملة
```

### 8.3 أسئلة أمنية

**السؤال 3.1: البيانات**
```
هل بيانات المشاريع:
├── سرية عالية؟
├── تحتاج تشفير؟
└── يمكن مشاركتها؟
```

---

## 9. القاموس والمصطلحات

### 9.1 المصطلحات التقنية (عربي ↔ إنجليزي)

| العربية | الإنجليزية | المعنى |
|--------|----------|-------|
| كود | Code | رقم يشير إلى فقرة/نشاط (001, 002, ...) |
| فقرة | Paragraph/Section | جزء من الملف الأساسي |
| سجل الأكواد | Codes Registry | قاعدة بيانات الأكواد الموحدة |
| البيانات الوصفية | Metadata | معلومات عن البيانات (not data itself) |
| فك الترميز | Parsing | استخراج البيانات من الملفات |
| بناء | Building | تجميع الأجزاء في ملف نهائي |
| تحقق | Validation | فحص صحة البيانات |
| تبعية | Dependency | متطلب أساسي لنشاط ما |
| معاينة | Preview | عرض ما سيُنتج قبل الحفظ |
| معالج | Engine | برنامج يقوم بعملية ما |
| أسلوب | Style | قالب تنسيق معين |

### 9.2 اختصارات مهمة

```
SSOT    = Single Source of Truth (مصدر واحد للحقيقة)
ATPAS   = Al-Rawaf Technical Proposal Automation System
UI      = User Interface (واجهة المستخدم)
CSV     = Comma Separated Values
JSON    = JavaScript Object Notation
docx    = Word Document Format
PNG/JPG = Image Formats
API     = Application Programming Interface
HTML    = HyperText Markup Language
QC      = Quality Control
```

---

## 10. ملاحظات تقنية

### 10.1 متطلبات التكنولوجيا

```
Python:
├── الإصدار: Python 3.9 أو أحدث
├── المكتبات الرئيسية:
│   ├── python-docx (معالجة Word)
│   ├── Pillow (معالجة الصور)
│   ├── PyQt5/PySimpleGUI (الواجهة الرسومية)
│   ├── openpyxl (معالجة Excel)
│   ├── python-pptx (معالجة PowerPoint - اختياري)
│   └── json (موجود افتراضياً)
└── متطلبات النظام:
    ├── Windows 10+ أو macOS 10.14+ أو Linux
    ├── RAM: 4GB على الأقل
    └── Disk Space: 500MB

تحميل المتطلبات:
pip install -r requirements.txt
```

### 10.2 البنية الموصى بها للمتغيرات البيئية

```python
# .env file (اختياري للإنتاج)
PROJECT_NAME=ATPAS
DEBUG_MODE=False
LOG_LEVEL=INFO
OUTPUT_DIRECTORY=/path/to/output
TEMPLATES_DIRECTORY=/path/to/templates
METADATA_DIRECTORY=/path/to/metadata
```

### 10.3 معايير الجودة

```
✅ Code Quality:
├── PEP 8 compliance
├── Type hints everywhere
├── Docstrings for all functions
└── Unit test coverage >80%

✅ Documentation:
├── جميع الملفات موثقة
├── جميع الدوال لها docstrings
├── أمثلة عملية لكل ميزة
└── معالجة الأخطاء موثقة

✅ Performance:
├── معالجة ملف 50 صفحة < 5 seconds
├── استخدام الذاكرة < 500MB
└── معالجة 300+ كود بسلاسة
```

### 10.4 معالجة الأخطاء

```python
# نموذج معالجة الأخطاء

try:
    # العملية الرئيسية
    result = process_codes(selected_codes)
except ValidationError as e:
    logger.error(f"Validation Error: {e}")
    show_user_message("اختيار غير صحيح: " + str(e))
except FileNotFoundError as e:
    logger.error(f"File Not Found: {e}")
    show_user_message("الملف غير موجود")
except Exception as e:
    logger.critical(f"Unexpected Error: {e}")
    show_user_message("خطأ غير متوقع، يرجى التواصل مع المطور")
finally:
    # تنظيف الموارد
    cleanup_resources()
```

### 10.5 السجلات والتتبع (Logging & Audit)

```json
{
  "audit_trail_example": {
    "timestamp": "2026-04-20T14:30:25Z",
    "user": "Dr. Youssef",
    "action": "PROPOSAL_GENERATED",
    "project": "wastewater",
    "owner": "nwc",
    "selected_codes": ["001", "002", "003", "005"],
    "generated_file": "Proposal_Wastewater_v1.docx",
    "file_size_bytes": 2457632,
    "processing_time_seconds": 4.23,
    "status": "SUCCESS",
    "build_report": "build_report_20260420_143025.html"
  }
}
```

---

## 11. الخطوات التالية الفورية

### 11.1 ماذا نحتاج منك الآن

```
1️⃣ أرسل لنا:
   ├── عينة من ملف Word الأساسي (أول 10 فقرات)
   ├── عدد الأكواد الكلي لكل مشروع
   └── نموذج من الأكواد تتصورها (مثلاً: 001-010 لمشروع الصرف)

2️⃣ أجب على الأسئلة في القسم 8

3️⃣ أخبرنا:
   ├── أي مشروع تريد أن نبدأ معه؟
   ├── كم كود في المرحلة الأولى (50؟ 100؟)
   └── متى تريد النسخة الأولى الجاهزة؟
```

### 11.2 المراحل التالية

```
بعد إجاباتك:
  ↓
سننشئ نموذج أولي (Proof of Concept)
  ↓
تختبره على ملفاتك الفعلية
  ↓
نجمع ملاحظاتك
  ↓
نطور النسخة الكاملة
  ↓
تدريب الفريق
  ↓
إطلاق النظام ✅
```

---

## 12. المراجع والموارد

### 12.1 مكتبات Python المستخدمة

- **python-docx**: https://python-docx.readthedocs.io/
- **Pillow**: https://pillow.readthedocs.io/
- **PyQt5**: https://doc.qt.io/qt-5/
- **openpyxl**: https://openpyxl.readthedocs.io/

### 12.2 معايير التوثيق

- PEP 257 – Docstring Conventions
- Google Python Style Guide
- NumPy Documentation Style

### 12.3 تواصل وتحديثات

```
📧 البريد الإلكتروني: (سيُضاف)
📞 الاجتماعات: (كل 3 أيام)
💾 مستودع البيانات: (سيُضاف)
📊 لوحة التقدم: (سيُضاف)
```

---

## 13. الملخص التنفيذي

### 13.1 رؤية النظام

```
بدلاً من:
"كتابة العرض يدويّاً من 5 ملفات مختلفة، تنسيق يدوي، ساعات من العمل"

إلى:
"اختيار أكواد من واجهة رسومية، ملف منسق تلقائياً، دقائق من العمل"
```

### 13.2 الفوائد الرئيسية

```
1. ⚡ السرعة: من ساعات إلى دقائق
2. 🎯 الدقة: لا أخطاء يدوية
3. 🔄 المرونة: يسهل التعديل والتطوير
4. 📊 التتبع: كل تغيير مسجل
5. 💪 الاحترافية: ملفات متسقة الأسلوب
6. 🔐 الأمان: بيانات منظمة وموثوقة
```

### 13.3 النتائج المتوقعة

```
بعد شهر واحد:
✅ نظام يعمل 100%
✅ 300+ كود جاهزة
✅ واجهة رسومية احترافية
✅ توثيق شاملة
✅ فريق مدرب

بعد 3 أشهر:
✅ نسخة متطورة مع قاعدة بيانات
✅ API للتطبيقات الخارجية
✅ تقارير وتحليلات متقدمة

بعد 6 أشهر:
✅ واجهة ويب
✅ تطبيق جوال
✅ AI suggestions للأكواد الناقصة
```

---

## 14. ملاحظات نهائية

### 14.1 الأهم المهم

```
⭐ هذا النظام مبني على SSOT
  ↓
  كل بيانة في مكان واحد فقط
  ↓
  يسهل التعديل والتطوير المستقبلي
  ↓
  النظام يتطور مع احتياجاتك
```

### 14.2 الالتزام بالجودة

```
✅ جودة Code
✅ جودة Documentation
✅ جودة Testing
✅ جودة User Experience
```

### 14.3 الدعم المستمر

```
بعد الإطلاق:
├── تحديثات منتظمة
├── إصلاح الأخطاء سريعاً
├── ميزات جديدة حسب الطلب
└── دعم فني مستمر
```

---

## 📞 جهات الاتصال والتعاون

**د. يوسف سليم (Project Owner)**
- الدور: المسؤول الأول عن المتطلبات والتصميم
- المسؤولية: الموافقة على المراحل والاختبار

**Claude AI (Development Team)**
- الدور: التطوير والبرمجة والتوثيق
- المسؤولية: الجودة والتطبيق

**فريق الرواف (QA & Users)**
- الدور: الاختبار والتقييم
- المسؤولية: الملاحظات والاقتراحات

---

## 📝 تاريخ التعديلات

| التاريخ | الإصدار | التعديلات | المسؤول |
|--------|---------|----------|--------|
| 20/4/2026 | v1.0 | النسخة الأولى الكاملة | Claude AI |
| TBA | v1.1 | تحديثات بناءً على الملاحظات | Claude AI |
| TBA | v2.0 | إضافة ميزات جديدة | Claude AI |

---

**© 2026 Al-Rawaf Contracting Co. - All Rights Reserved**

---

## 🚀 الخطوة التالية

**اقرأ هذا المستند بعناية، ثم أرسل لي:**

```
1. إجاباتك على الأسئلة في القسم 8
2. عينة من أول ملف Word (أول 5-10 فقرات)
3. قائمة بأسماء الأكواد التي تتصورها
4. الجدول الزمني المفضل لديك
```

**ثم سننتقل إلى المرحلة الأولى من التطبيق! 🎯**

---

**Document Created:** April 20, 2026  
**For:** Dr. Youssef Seleim, Al-Rawaf Contracting Co.  
**Status:** Ready for Review & Feedback

