# ATPAS Tasks v2.0
# Al-Rawaf Technical Proposal Automation System

**Updated**: 2026-04-20  
**Source**: docs/specification.md v2.0 + docs/implementation-plan.md  
**Total Tasks**: 39 | **Done**: 28 ✅ | **Remaining**: 11

---

## User Stories Map

| US | Priority | الوصف | FRs | الحالة |
|----|----------|-------|-----|-------|
| US1 | P1 | Data Loading & Validation Engine | FR-001, FR-002, FR-004 | ✅ مكتمل |
| US2 | P1 | Document Generation Engine | FR-006, FR-007, FR-008 | ✅ مكتمل |
| US2b | P1 | Universal System Gap Closing | FR-010 | ✅ مكتمل |
| US3 | P2 | GUI Layer | FR-003, FR-005 | ⬜ Sprint 3 |
| US4 | P3 | Audit Trail & Config | FR-009, FR-010 | ⬜ Sprint 3-4 |

---

## Phase 1: Setup ✅ DONE

- [x] T001 Create project directory structure
- [x] T002 Create requirements.txt
- [x] T003 Create engine/__init__.py ui/__init__.py utils/__init__.py tests/__init__.py

---

## Phase 2: Foundation — Data Layer ✅ DONE

- [x] T004 codes_registry.json — 34 active codes initial
- [x] T005 [P] water_supply_project_metadata.json
- [x] T006 [P] asphalt_project_metadata.json
- [x] T007 [P] nwc.json + makkah.json + moh.json (owner specs)
- [x] T008 [P] nwc_style.json + makkah_style.json + moh_style.json

---

## Phase 3: US1 — Validation Engine ✅ DONE

- [x] T009 [US1] utils/json_manager.py — load/save/merge JSON UTF-8
- [x] T010 [US1] engine/logger.py — rotating logs + audit_trail JSON
- [x] T011 [US1] engine/error_handler.py — Arabic error messages + safe_call wrapper
- [x] T012 [P] [US1] engine/validator.py — 8 checks: exists, active, project, owner, forbidden, exclusive, mandatory, dependencies
- [x] T013 [P] [US1] engine/dependency_resolver.py — DFS transitive closure; cycle-safe
- [x] T014 [US1] tests/test_validator.py — 11 scenarios passing ✅

---

## Phase 4: US2 — Document Generation Engine ✅ DONE

- [x] T015 [US2] utils/image_processor.py — extract/embed images DPI≥300
- [x] T016 [US2] utils/docx_manipulator.py — RTL + OOXML helpers (fixed CT_PPr bidi)
- [x] T017 [US2] engine/parser.py — parse docx → sections.json + images; SHA-256 cache
- [x] T018 [US2] engine/formatter.py — RTL headings, spacing, Arabic body paragraphs
- [x] T019 [US2] engine/style_applier.py — header/footer/heritage/compliance per owner
- [x] T020 [US2] engine/builder.py — content library first, metadata fallback; TOC + page numbers
- [x] T021 [US2] tests/test_builder.py — 7 integration scenarios passing ✅
- [x] T021b [US2] utils/content_library.py — registry+exact+fuzzy lookup; deep XML copy with image remap
- [x] T021c [US2] tools/import_content.py — CLI: split/register/list/missing
- [x] T021d [US2] tools/extend_registry.py — one-time: +30 codes → 64 total

---

## Phase 4b: US2b — Universal System Gap Closing ✅ DONE

- [x] T021e [US2b] codes_registry.json expanded to 64 codes (R, C, T networks)
- [x] T021f [P] [US2b] road_maintenance_project_metadata.json (22 activities, 2 proposals)
- [x] T021g [P] [US2b] general_construction_project_metadata.json (22 activities, 2 proposals)
- [x] T021h [P] [US2b] water_transmission_project_metadata.json (22 activities, 1 proposal)
- [x] T021i [P] [US2b] 6 owner spec files: mot, nhi, amana_riyadh, amana_qassim, swa, ksia
- [x] T021j [P] [US2b] 6 style templates: mot_style, nhi_style, amana_riyadh_style, amana_qassim_style, swa_style, ksia_style
- [x] T021k [US2b] master_config.json updated: 6 projects + 9 owners + 6 network types + new phases
- [x] T021l [US2b] 18/18 tests still passing after gap-closing ✅

---

## Phase 5: US3 — GUI Layer ⬜ Sprint 3

**Story Goal**: المستخدم يختار أكواد ويبني عرض فني من واجهة رسومية عربية

**Independent test criteria**:
- التطبيق يفتح بدون أخطاء
- اختيار مشروع يُحدّث قائمة الأكواد تلقائياً
- FINE+OPEN لا يمكن تحديدهما معاً
- زر "بناء" يُنتج ملف .docx في output/

- [ ] T022 [US3] Create ui/project_selector.py — QComboBox لـ 6 مشاريع + 9 جهات مفلترة
- [ ] T023 [US3] Create ui/checkbox_selector.py — checkboxes مجمّعة بالفئة (001-005); radio للحصريين; إلزاميون محددون مقفلون; عداد X كود / Y صفحة
- [ ] T024 [US3] Create ui/preview_panel.py — قائمة أكواد مرتبة + إجمالي صفحات/صور + تحذيرات باللون الأحمر + "إصلاح تلقائي" + زر بناء
- [ ] T025 [US3] Create ui/build_progress.py — QProgressDialog 0→100% رسائل عربية + "فتح الملف"
- [ ] T026 [US3] Create ui/main_window.py — 1200×800 RTL عربي يدمج كل مكونات UI
- [ ] T027 [US3] Create main.py — entry point: master_config → CodesRegistry → QApplication
- [ ] T028 [US3] Wire UI to engine — QThread: validator→resolver→builder→style_applier; أخطاء كـ QMessageBox عربية

---

## Phase 6: US4 — Audit Trail & Config ⬜ Sprint 3-4

- [ ] T029 [US4] Extend engine/logger.py — generate_audit_trail() مكتمل مع build_context كامل
- [ ] T030 [P] [US4] Test config hot-reload — كود جديد في JSON يظهر عند إعادة التشغيل

---

## Phase 7: Polish & Integration Tests ⬜ Sprint 4

- [ ] T031 Write tests/test_integration.py — 6 سيناريوهات end-to-end: ملف .docx صالح + صفحات صحيحة ±10% + أسلوب الجهة صحيح
- [ ] T032 [P] Write docs/USER_GUIDE_AR.md — تثبيت + شرح مصوّر + حل المشاكل الشائعة

---

## Dependency Graph

```
T001 → T002 → T003                              (Phase 1 ✅)
T004 → T005 → T006 → T007 → T008               (Phase 2 ✅)

T009 → T010 → T011
T009 ──────────────→ T012 → T014                (Phase 3 ✅)
T009 ──────────────→ T013

T015 → T016 → T017
T017 ──────→ T018 → T019 → T020 → T021         (Phase 4 ✅)
T020 ──────→ T021b → T021c

T004 → T021d → T021e → T021f,g,h,i,j,k,l       (Phase 4b ✅)

T012 + T013 + T020 →
T022 → T023 → T024 → T025 → T026 → T027 → T028 (Phase 5 ⬜)

T010 → T029 → T030                              (Phase 6 ⬜)

T021 + T028 → T031 → T032                       (Phase 7 ⬜)
```

**Critical Path**: T009 → T012 → T020 → T028 → T031  
**Next Milestone**: T022–T028 (GUI Layer)

---

## Progress Summary

| Phase | Tasks | Done | Remaining |
|-------|-------|------|-----------|
| Phase 1: Setup | 3 | 3 ✅ | 0 |
| Phase 2: Foundation | 5 | 5 ✅ | 0 |
| Phase 3: US1 Validation | 6 | 6 ✅ | 0 |
| Phase 4: US2 Builder | 10 | 10 ✅ | 0 |
| Phase 4b: Gap Closing | 8 | 8 ✅ | 0 |
| Phase 5: US3 GUI | 7 | 0 | **7** |
| Phase 6: US4 Audit | 2 | 0 | 2 |
| Phase 7: Polish | 2 | 0 | 2 |
| **Total** | **43** | **32 ✅** | **11** |

---

## Test Results

```
tests/test_validator.py   11/11 ✅
tests/test_builder.py      7/7  ✅
─────────────────────────────────
Total                     18/18 ✅
```
