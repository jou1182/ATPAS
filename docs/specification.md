# ATPAS — Al-Rawaf Technical Proposal Automation System
# Specification v2.0

**Author**: Dr. Youssef Seleim / Claude AI  
**Date**: 2026-04-20  
**Status**: Active — Sprint 2 Complete, Sprint 3 (GUI) Next  
**Organization**: Al-Rawaf Contracting Co.

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-04-20 | Claude AI | Initial specification — 3 projects, 3 owners |
| 2.0.0 | 2026-04-20 | Claude AI | Expanded: 6 projects, 9 owners, 64 codes, universal system |
| 3.0.0 | 2026-04-27 | Claude AI | BOQ Importer — العمود الفقري: استيراد جدول الكميات + مطابقة ذكية + إنشاء أكواد جديدة |

---

## Overview

**Purpose**: نظام سطح مكتب Windows يُحوّل جدول كميات المنافسة إلى عروض فنية Word منسقة ومكتملة — يوفّر على قسم العروض الفنية من ساعات إلى دقائق لأي نوع مشروع مع أي جهة مالكة.

**Core Concept** (v3.0):
```
المستخدم يلخص جدول الكميات → Excel بسيط
         ↓
BOQ Importer يقرأ الملف ويطابق الأكواد تلقائياً
         ↓
المستخدم يراجع ويوافق
         ↓
Word احترافي جاهز ✅
```

**Scope**:
- **IN (v2.0)**:
  - 6 أنواع مشاريع: صرف صحي (S)، مياه (W)، أسفلت (A)، طرق (R)، إنشاءات (C)، نقل مياه (T)
  - 9 جهات مالكة: NWC, Makkah, MOH, MOT, NHI, Amana Riyadh, Amana Qassim, SWA, KSIA
  - 64 كود نشط مع نظام هرمي [CATEGORY]-[PHASE]-[VARIATION]
  - تطبيق سطح مكتب Windows (PyQt5)
  - مكتبة محتوى: ملف .docx لكل كود (drop & go)
  - واجهة رسومية عربية RTL
  - تحقق تلقائي من التبعيات والقواعد
  - سجلات Audit Trail
  - نظام قابل للتوسيع بلا تعديل في الكود
- **OUT (v1.0)**:
  - قاعدة بيانات SQL
  - API خارجي
  - واجهة ويب / تطبيق جوال
  - مشاركة متعددة مستخدمين عبر الشبكة

**Stakeholders**:
- **د. يوسف سليم**: مالك المشروع — يوافق على المراحل، يختبر النماذج
- **فريق الرواف (4 مهندسين)**: المستخدمون النهائيون
- **Claude AI**: التطوير والبرمجة والتوثيق

---

## Functional Requirements

### FR-001: تحميل سجل الأكواد

**Description**: النظام يحمّل codes_registry.json (64 كود) عند البدء.

**Acceptance Criteria**:
- [ ] Given وجود codes_registry.json، when تشغيل النظام، then تحمّل جميع الأكواد < 2 ثانية
- [ ] Given ملف JSON تالف، when تشغيل، then رسالة خطأ عربية واضحة
- [ ] Given كود حالته "inactive"، when عرض الواجهة، then لا يظهر للمستخدم

**Priority**: High | **Effort**: S | **Status**: ✅ مكتمل

---

### FR-002: اختيار المشروع والجهة المالكة

**Description**: المستخدم يختار من 6 مشاريع و 9 جهات، وتتفلتر الأكواد تلقائياً.

**Acceptance Criteria**:
- [ ] Given فتح التطبيق، when عرض الواجهة، then تظهر 6 خيارات مشروع و 9 جهات
- [ ] Given اختيار مشروع، when تحديث القائمة، then تظهر فقط أكواد ذلك المشروع
- [ ] Given اختيار NWC، when عرض الأكواد، then 001-PRM-MUN غير ظاهر (محظور)
- [ ] Given اختيار MOT، when عرض الأكواد، then 001-TRF-MGT محدد مسبقاً (إلزامي)

**Priority**: High | **Effort**: S | **Status**: ✅ جاهز في Engine، ⬜ GUI قادم

---

### FR-003: واجهة الاختيار التفاعلية

**Description**: قائمة Checkboxes مجمّعة بالفئة (001–005) مع قواعد الحصرية.

**Acceptance Criteria**:
- [ ] Given عرض الأكواد، when تجميعها، then مجمّعة في 5 أقسام (001, 002, 003, 004, 005)
- [ ] Given مجموعة حصرية (EXC-FINE / EXC-OPEN / EXC-TUNNEL)، when اختيار أحدها، then يُلغى تحديد الباقين
- [ ] Given أكواد إلزامية، when عرض القائمة، then محددة ومقفلة تلقائياً
- [ ] Given أي تغيير في الاختيار، when تحديث عداد، then يظهر "X كود / Y صفحة" فورياً

**Priority**: High | **Effort**: M | **Status**: ⬜ Sprint 3

---

### FR-004: التحقق التلقائي والتبعيات

**Description**: النظام يتحقق من صحة الاختيارات قبل البناء.

**Acceptance Criteria**:
- [ ] Given تبعية مفقودة، when فحص، then تحذير + زر "إصلاح تلقائي"
- [ ] Given أكواد متعارضة (EXC-FINE + EXC-OPEN)، when محاولة بناء، then رفض + رسالة عربية
- [ ] Given كود محظور للجهة، when اختياره، then رسالة خطأ واضحة
- [ ] Given اختيار صحيح كامل، when فحص، then زر "بناء" مفعّل

**Priority**: High | **Effort**: M | **Status**: ✅ مكتمل في engine/validator.py

---

### FR-005: معاينة حية (Preview Panel)

**Description**: عرض قائمة الأكواد المختارة بأسمائها + إجمالي الصفحات.

**Acceptance Criteria**:
- [ ] Given تغيير اختيار، when تحديث معاينة، then تنعكس التغييرات فوراً
- [ ] Given وجود تحذيرات تبعية، when عرضها، then باللون الأحمر مع وصف واضح
- [ ] Given اختيار صحيح، when عرض إجمالي، then يطابق مجموع صفحات الأكواد ±10%

**Priority**: High | **Effort**: S | **Status**: ⬜ Sprint 3

---

### FR-006: بناء ملف Word

**Description**: النظام يجمع فقرات الأكواد في ملف Word منسق حسب الجهة المالكة.

**Acceptance Criteria**:
- [ ] Given اختيار صحيح، when ضغط "بناء"، then ملف .docx ينتج في output/
- [ ] Given ملف محتوى موجود للكود، when البناء، then يُنسخ المحتوى كاملاً (نص + صور)
- [ ] Given ملف محتوى غير موجود، when البناء، then placeholder text من metadata
- [ ] Given 60+ صفحة و20+ صورة، when قياس الأداء، then البناء < 5 ثوانٍ

**Priority**: High | **Effort**: L | **Status**: ✅ مكتمل في engine/builder.py

---

### FR-007: أسلوب الجهة المالكة

**Description**: كل جهة لها نمط تنسيق خاص (ألوان، header/footer، بنود خاصة).

**Acceptance Criteria**:
- [ ] Given NWC، when تطبيق الأسلوب، then header/footer أزرق مع شعار NWC
- [ ] Given Makkah، when تطبيق الأسلوب، then أخضر + بند حماية التراث
- [ ] Given MOH/SWA/KSIA، when تطبيق الأسلوب، then مصفوفة امتثال كاملة
- [ ] Given أي جهة، when توليد الملف، then فهرس محتويات + ترقيم صفحات

**Priority**: High | **Effort**: M | **Status**: ✅ مكتمل في engine/style_applier.py

---

### FR-008: مكتبة المحتوى (Content Library)

**Description**: نمط "drop & go" — وضع ملف .docx في المجلد يعني تسجيل تلقائي.

**Acceptance Criteria**:
- [ ] Given ملف 001-SUR-BASE.docx في templates/source_documents/، when البناء، then محتواه يُدرج تلقائياً
- [ ] Given عدم وجود ملف، when البناء، then placeholder من metadata بدون خطأ
- [ ] Given أمر import_content split master.docx، when التنفيذ، then ينقسم إلى ملفات per-code

**Priority**: High | **Effort**: M | **Status**: ✅ مكتمل في utils/content_library.py

---

### FR-009: Audit Trail وسجلات

**Description**: كل عملية بناء تُسجَّل كاملاً.

**Acceptance Criteria**:
- [ ] Given بناء ناجح، when فحص audit_trail/، then JSON بالأكواد + وقت + حجم + نتيجة
- [ ] Given خطأ في البناء، when فحص logs/، then سبب الخطأ مسجّل بالتفصيل

**Priority**: Medium | **Effort**: S | **Status**: ✅ مكتمل في engine/logger.py

---

### FR-010: إضافة أكواد جديدة بدون تعديل كود

**Description**: المستخدم يضيف كود جديد عبر JSON فقط — لا تعديل في Python.

**Acceptance Criteria**:
- [ ] Given إضافة كود في codes_registry.json، when إعادة التشغيل، then يظهر في الواجهة تلقائياً
- [ ] Given وضع {CODE_ID}.docx في source_documents/، when البناء، then المحتوى يُستخدم مباشرة

**Priority**: High | **Effort**: S | **Status**: ✅ مكتمل (SSOT architecture)

---

## Non-Functional Requirements

### NFR-001: الأداء
- ملف 60 صفحة + 20 صورة: بناء < 5 ثوانٍ
- تحميل التطبيق: < 3 ثوانٍ
- استجابة الواجهة: < 100ms عند كل تغيير

### NFR-002: الموثوقية
- لا انهيار عند ملفات .docx تالفة (graceful fallback)
- لا حلقات لا نهائية في حل التبعيات
- استعادة تلقائية عند خطأ غير متوقع

### NFR-003: الاستخدامية
- واجهة عربية RTL كاملة
- رسائل خطأ واضحة بالعربية
- لا خطوة تعليمية لبدء الاستخدام

### NFR-004: الصيانة
- إضافة جهة جديدة: 2 ملف JSON فقط
- إضافة كود جديد: سطر في JSON + ملف .docx
- إضافة مشروع جديد: ملف JSON واحد

---

## Technical Constraints

- **Python**: 3.9+
- **UI Framework**: PyQt5
- **Document**: python-docx
- **Images**: Pillow (DPI ≥ 300)
- **Platform**: Windows 10+
- **Data**: JSON files (لا قاعدة بيانات في v1.0)

---

## Success Criteria

- [ ] النظام ينتج ملف Word كامل لأي مشروع من 6 أنواع
- [ ] النظام يدعم 9 جهات مالكة بأنماط مختلفة
- [ ] 18/18 اختبارات تمرّ بنجاح
- [ ] الواجهة الرسومية تعمل كاملاً
- [ ] مهندس الرواف يُنتج عرضاً في < 5 دقائق
