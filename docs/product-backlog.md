# ATPAS Product Backlog (Execution-Ready)

**Date:** 2026-04-20  
**Scope:** تحويل أفكار المنتج الحالية إلى Backlog قابل للتنفيذ مباشرة  
**Primary Goal:** تدفق كامل من اختيار الأكواد حتى بناء ملف Word صحيح من واجهة عربية واضحة

## Prioritization

- `P0`: أساسي للتشغيل الفعلي (MVP UI + Engine Integration).
- `P1`: مهم لرفع السرعة والجودة وتجربة المستخدم.
- `P2`: تحسينات توسعية بعد استقرار التدفق الأساسي.

## Backlog Items

| ID | Priority | Type | Story / Task | Acceptance Criteria | Estimate |
|---|---|---|---|---|---|
| BKL-001 | P0 | Feature | إنشاء `ui/main_window.py` بهيكل RTL واضح (Project -> Codes -> Preview -> Build) | النافذة تعمل بدون أخطاء، RTL صحيح، تحميل السجل عند البدء | 3 pts |
| BKL-002 | P0 | Feature | إنشاء `ui/project_selector.py` لاختيار المشروع والجهة مع فلترة صحيحة | تغيير المشروع/الجهة يحدّث الأكواد المعروضة مباشرة | 3 pts |
| BKL-003 | P0 | Feature | إنشاء `ui/checkbox_selector.py` بعرض الأكواد حسب الفئات + عداد صفحات/أكواد | دعم الاختيارات المتنافية، إظهار الأكواد الإلزامية بشكل صحيح | 5 pts |
| BKL-004 | P0 | Feature | إنشاء `ui/preview_panel.py` مع تحذيرات التبعيات وزر الإصلاح التلقائي | Preview يعرض الأكواد مرتبة، التحذيرات تظهر بالعربية، زر الإصلاح يضيف النواقص | 5 pts |
| BKL-005 | P0 | Feature | إنشاء `ui/build_progress.py` وربط زر Build بـ QThread | الواجهة لا تتجمد أثناء البناء، Progress يظهر حتى الاكتمال | 3 pts |
| BKL-006 | P0 | Integration | ربط UI مع `validator -> dependency_resolver -> builder -> style_applier` | بناء ملف `.docx` من الواجهة بنجاح لسيناريو wastewater+nwc | 5 pts |
| BKL-007 | P0 | Quality | توحيد رسائل الأخطاء العربية في UI باستخدام `engine/error_handler.py` | جميع أخطاء التشغيل تُعرض بصياغة عربية مفهومة | 2 pts |
| BKL-008 | P0 | Testing | إضافة `tests/test_integration.py` لسيناريوهات E2E الأساسية (4 سيناريوهات) | اختبارات E2E تمر بنجاح وتغطي المسار الكامل | 5 pts |
| BKL-009 | P1 | Feature | Preset Scenarios (أزرار جاهزة لأنماط متكررة) | اختيار Preset يملأ الأكواد تلقائيًا مع قابلية التعديل | 3 pts |
| BKL-010 | P1 | Feature | تقرير Build مختصر بالعربية بعد كل عملية | يظهر: الحالة، الزمن، عدد الصفحات، الملف الناتج، التحذيرات | 3 pts |
| BKL-011 | P1 | Quality | تحسين `audit_trail` بإضافة حقول UX (preset, auto_fix_used, warnings_count) | كل عملية بناء تسجل معلومات كاملة للمراجعة | 2 pts |
| BKL-012 | P1 | Documentation | إنشاء دليل تشغيل سريع `docs/USER_GUIDE_AR.md` | عضو جديد يقدر ينفذ أول Build خلال 15 دقيقة | 2 pts |
| BKL-013 | P2 | Feature | Hot Reload لإعدادات الأكواد عند إعادة فتح الصفحة | التغييرات في `codes_registry.json` تظهر بدون تعديل كود | 3 pts |
| BKL-014 | P2 | Feature | تصدير ملخص الاختيار إلى JSON قبل البناء | ملف الملخص يحتوي كل الأكواد والحسابات ويُحفظ في `output/reports` | 2 pts |

## User Stories (Mapped)

- `US-01 (P0)`: كمهندس، أريد اختيار المشروع والجهة ورؤية الأكواد المناسبة فقط.
- `US-02 (P0)`: كمهندس، أريد اكتشاف نواقص التبعيات وإصلاحها تلقائيًا قبل البناء.
- `US-03 (P0)`: كمهندس، أريد بناء ملف Word من الواجهة بدون تجمد أو أخطاء غير مفهومة.
- `US-04 (P1)`: كمهندس، أريد Presets جاهزة لتسريع إعداد سيناريوهات شائعة.
- `US-05 (P1)`: كقائد فريق، أريد تقارير وعملية تدقيق واضحة لكل Build.

## Suggested Execution Sequence (Week Plan)

1. BKL-001, BKL-002
2. BKL-003
3. BKL-004
4. BKL-005, BKL-006
5. BKL-007, BKL-008
6. BKL-009, BKL-010 (after P0 sign-off)
7. BKL-011, BKL-012

## Definition of Done

- كل بند يمر عبر: تنفيذ + اختبار + توثيق مختصر.
- لا يوجد كسر في اختبارات `tests/test_validator.py` و`tests/test_builder.py`.
- جميع الرسائل النهائية للمستخدم في واجهة التشغيل بالعربية.
- مسار `Build from UI` يعمل لسيناريو واحد على الأقل من البداية للنهاية.
