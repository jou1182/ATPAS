# ATPAS — Implementation Plan v2.0

**Author**: Claude AI / Dr. Youssef Seleim  
**Updated**: 2026-04-20  
**Sprint Length**: 1 أسبوع  
**Target Completion**: 2026-05-18  
**Current Status**: Sprint 2 + Gap Closing ✅ → Sprint 3 (GUI) ⬜

---

## Architecture

### System Overview

```
[master_config.json]          ← SSOT المركزي: 6 مشاريع، 9 جهات، 6 شبكات
           ↓
[codes_registry.json]          ← 64 كود نشط بنظام [CATEGORY]-[PHASE]-[VARIATION]
[6 × project_metadata.json]    ← تسلسلات + تبعيات + مقترحات نموذجية
[9 × owner_specifications/]    ← أكواد إلزامية + محظورة + متطلبات خاصة
           ↓
[templates/source_documents/]  ← مكتبة المحتوى: {code_id}.docx per activity
           ↓
[parser → validator → dependency_resolver → builder → formatter → style_applier]
           ↓
[ui: main_window → project_selector → checkbox_selector → preview_panel]
           ↓
[output: generated_documents + audit_trail + logs]
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (PyQt5)   ← Sprint 3         │
│  main_window ─► project_selector (6 proj + 9 owners)    │
│  checkbox_selector ─► preview_panel ─► build_progress   │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Processing Engine   ✅ مكتمل              │
│  parser ─► validator ─► dependency_resolver             │
│  builder ─► formatter ─► style_applier                  │
│  content_library │ logger │ error_handler               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Data Layer (JSON + DOCX)   ✅ مكتمل        │
│  codes_registry.json (64 codes)                         │
│  6 × project metadata │ 9 × owner specs                 │
│  9 × style templates │ source_documents/*.docx          │
└─────────────────────────────────────────────────────────┘
```

### Components

#### Component: Data Layer  ✅ مكتمل
**Responsibility**: جميع البيانات الوصفية والمحتوى — نمط SSOT  
**Files**: codes_registry.json, *_project_metadata.json, owner_specifications/*.json, style_templates/*.json

#### Component: Content Library  ✅ مكتمل
**Responsibility**: إيجاد وإدراج ملفات المحتوى بثلاث أولويات (registry → exact → fuzzy)  
**Files**: utils/content_library.py, templates/source_documents/

#### Component: Parser  ✅ مكتمل
**Responsibility**: استخراج فقرات + صور من .docx مع SHA-256 cache  
**Files**: engine/parser.py

#### Component: Validator  ✅ مكتمل
**Responsibility**: 8 فحوصات: وجود، حالة، مشروع، جهة، محظور، حصري، إلزامي، تبعيات  
**Files**: engine/validator.py

#### Component: Dependency Resolver  ✅ مكتمل
**Responsibility**: DFS transitive closure — آمن من الحلقات  
**Files**: engine/dependency_resolver.py

#### Component: Builder  ✅ مكتمل
**Responsibility**: تجميع فقرات الأكواد (content library أولاً، metadata fallback)  
**Files**: engine/builder.py

#### Component: Style Applier  ✅ مكتمل
**Responsibility**: header/footer/heritage clause/compliance matrix حسب الجهة  
**Files**: engine/style_applier.py

#### Component: UI (PyQt5)  ⬜ Sprint 3
**Responsibility**: واجهة عربية RTL — 6 مشاريع، 9 جهات، 64 كود  
**Files**: ui/main_window.py, ui/project_selector.py, ui/checkbox_selector.py, ui/preview_panel.py, ui/build_progress.py

---

## File Structure

| File | Status | Purpose |
|------|--------|---------|
| `master_config.json` | ✅ | SSOT المركزي: 6 مشاريع، 9 جهات، 6 شبكات |
| `codes_registry.json` | ✅ | 64 كود نشط |
| `wastewater_project_metadata.json` | ✅ | بيانات مشروع الصرف الصحي |
| `water_supply_project_metadata.json` | ✅ | بيانات مشروع المياه |
| `asphalt_project_metadata.json` | ✅ | بيانات مشروع الأسفلت |
| `road_maintenance_project_metadata.json` | ✅ | صيانة الطرق — 22 نشاط |
| `general_construction_project_metadata.json` | ✅ | الإنشاءات — 22 نشاط |
| `water_transmission_project_metadata.json` | ✅ | نقل المياه — 22 نشاط |
| `metadata/owner_specifications/nwc.json` | ✅ | متطلبات NWC |
| `metadata/owner_specifications/makkah.json` | ✅ | متطلبات أمانة مكة |
| `metadata/owner_specifications/moh.json` | ✅ | متطلبات وزارة الإسكان |
| `metadata/owner_specifications/mot.json` | ✅ | متطلبات وزارة النقل |
| `metadata/owner_specifications/nhi.json` | ✅ | متطلبات الشركة الوطنية للإسكان |
| `metadata/owner_specifications/amana_riyadh.json` | ✅ | متطلبات أمانة الرياض |
| `metadata/owner_specifications/amana_qassim.json` | ✅ | متطلبات أمانة القصيم |
| `metadata/owner_specifications/swa.json` | ✅ | متطلبات الهيئة السعودية للمياه |
| `metadata/owner_specifications/ksia.json` | ✅ | متطلبات مطار الملك سلمان |
| `templates/style_templates/nwc_style.json` | ✅ | أزرق |
| `templates/style_templates/makkah_style.json` | ✅ | أخضر/ذهبي + بند التراث |
| `templates/style_templates/moh_style.json` | ✅ | رمادي/أحمر + مصفوفة امتثال |
| `templates/style_templates/mot_style.json` | ✅ | أخضر حكومي |
| `templates/style_templates/nhi_style.json` | ✅ | كحلي |
| `templates/style_templates/amana_riyadh_style.json` | ✅ | تيل |
| `templates/style_templates/amana_qassim_style.json` | ✅ | بني غامق |
| `templates/style_templates/swa_style.json` | ✅ | أزرق مائي |
| `templates/style_templates/ksia_style.json` | ✅ | كحلي/ذهبي |
| `engine/__init__.py` | ✅ | |
| `engine/parser.py` | ✅ | SHA-256 cache |
| `engine/validator.py` | ✅ | 8 فحوصات |
| `engine/dependency_resolver.py` | ✅ | DFS cycle-safe |
| `engine/builder.py` | ✅ | content library + TOC + page numbers |
| `engine/formatter.py` | ✅ | RTL Arabic |
| `engine/style_applier.py` | ✅ | heritage + compliance |
| `engine/logger.py` | ✅ | rotating + audit trail |
| `engine/error_handler.py` | ✅ | Arabic messages |
| `utils/__init__.py` | ✅ | |
| `utils/json_manager.py` | ✅ | load/save/merge |
| `utils/image_processor.py` | ✅ | DPI≥300 |
| `utils/docx_manipulator.py` | ✅ | RTL OOXML fix |
| `utils/content_library.py` | ✅ | registry+exact+fuzzy+deep copy |
| `tools/import_content.py` | ✅ | CLI split/register/list |
| `tools/extend_registry.py` | ✅ | add codes CLI |
| `tests/test_validator.py` | ✅ | 11 scenarios |
| `tests/test_builder.py` | ✅ | 7 scenarios |
| `ui/__init__.py` | ✅ | empty |
| `ui/project_selector.py` | ⬜ | Sprint 3 |
| `ui/checkbox_selector.py` | ⬜ | Sprint 3 |
| `ui/preview_panel.py` | ⬜ | Sprint 3 |
| `ui/build_progress.py` | ⬜ | Sprint 3 |
| `ui/main_window.py` | ⬜ | Sprint 3 |
| `main.py` | ⬜ | Sprint 3 |
| `tests/test_integration.py` | ⬜ | Sprint 4 |
| `docs/USER_GUIDE_AR.md` | ⬜ | Sprint 4 |

---

## Sprint Plan

### Sprint 1 — Foundation ✅ مكتمل (أسبوع 1)
بنية المجلدات + أكواد أولية + 3 مشاريع + 3 جهات

### Sprint 2 — Engine ✅ مكتمل (أسبوع 2)
محرك التحقق + محرك البناء + مكتبة المحتوى + 18/18 اختبار

### Gap Closing ✅ مكتمل (بين Sprint 2 و 3)
+30 كود → 64 | +3 مشاريع → 6 | +6 جهات → 9 | +6 أنماط

### Sprint 3 — GUI ⬜ (أسبوع 3)

**الهدف**: واجهة رسومية PyQt5 عاملة كاملاً

**المهام الرئيسية**:

#### TASK-UI-001: ui/project_selector.py
- QComboBox للمشاريع الستة مع أسماء عربية
- dropdown الجهات المالكة مفلتر حسب applicable_networks
- يُصدر إشارة `(project_id, owner_id)` عند التغيير

#### TASK-UI-002: ui/checkbox_selector.py
- Checkboxes مجمّعة في 5 أقسام (001→005)
- RadioButtons للمجموعات الحصرية (EXC-FINE/OPEN/TUNNEL)
- أكواد إلزامية محددة ومقفلة تلقائياً
- عداد "X كود / Y صفحة" يتحدث فورياً

#### TASK-UI-003: ui/preview_panel.py
- قائمة الأكواد المختارة مرتبة بالتسلسل
- إجمالي الصفحات والصور
- تحذيرات تبعيات باللون الأحمر + "إصلاح تلقائي"
- زر "بناء" مفعّل فقط عند اختيار صحيح

#### TASK-UI-004: ui/build_progress.py
- QProgressDialog مع رسائل عربية (جاري التحقق... جاري البناء... اكتمل!)
- زر "فتح الملف" عند النجاح

#### TASK-UI-005: ui/main_window.py
- نافذة 1200×800 RTL
- تكامل كل المكونات
- QSplitter: يسار (project_selector + checkbox_selector) + يمين (preview_panel)

#### TASK-UI-006: main.py
```python
from utils.json_manager import load_json
from engine.validator import Validator
from engine.builder import Builder
from ui.main_window import MainWindow

config = load_json("master_config.json")
codes = load_json("codes_registry.json")
app = QApplication(sys.argv)
window = MainWindow(config, codes)
window.show()
sys.exit(app.exec_())
```

#### TASK-UI-007: ربط UI بالمحرك
```python
# في QThread لعدم تجميد الواجهة
def build_worker():
    is_valid, errors, warnings = validator.validate(codes, owner, project)
    if not is_valid:
        emit_error(errors)
        return
    resolved = resolver.resolve(codes)
    ok, msg = builder.build(resolved, project, owner, output_path)
    emit_complete(output_path if ok else None, msg)
```

### Sprint 4 — Integration & Polish ⬜ (أسبوع 4)

- tests/test_integration.py: 6 سيناريوهات end-to-end
- docs/USER_GUIDE_AR.md: شرح مصوّر للمستخدم النهائي
- اختبارات شاملة على أكواد حقيقية
- تحسينات UX بناءً على تجربة فريق الرواف

---

## Risk Assessment

| المخاطرة | التأثير | الاحتمال | الحل |
|---------|--------|---------|-----|
| ملفات .docx بتنسيق غير متوقع | عالٍ | متوسط | fallback placeholder + log warning |
| أداء بطيء لملفات كبيرة | متوسط | منخفض | SHA-256 cache + lazy loading |
| تعارض PyQt5 على Windows | متوسط | منخفض | pyinstaller + bundled Qt |
| أكواد جديدة تكسر التبعيات | منخفض | منخفض | SSOT + validator coverage |

---

## Timeline

| Sprint | الفترة | التركيز | المخرج |
|--------|--------|---------|-------|
| 1 | أسبوع 1 ✅ | Foundation | Data layer جاهزة |
| 2 | أسبوع 2 ✅ | Engine | Builder يعمل + 18 اختبار |
| Gap | بين ✅ | Universal | 64 كود، 9 جهات، 6 مشاريع |
| 3 | أسبوع 3 ⬜ | GUI | واجهة كاملة |
| 4 | أسبوع 4 ⬜ | Polish | v1.0 جاهزة للإنتاج |
