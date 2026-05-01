# Feature Specification: Context-Aware Excavation Selection

**Feature Branch**: `001-excavation-context-rules`
**Created**: 2026-05-01
**Status**: Draft
**Input**: User description: "توسيع وفصل أكواد الحفر حسب سياق المشروع والجهة المالكة: عند اختيار NWC لمشاريع المياه والصرف تظهر أكواد حفر البنية التحتية مثل الخنادق والحفر المفتوح والنفقي، وعند اختيار الشركة الوطنية للإسكان NHI/NHC أو مشاريع المباني تظهر أكواد حفر المباني مثل حفر الأساسات، الحفر العام، نزح المياه، سند جوانب الحفر، مكافحة النمل الأبيض، إحلال التربة، وعزل القواعد. يجب أن تمنع التجربة خلط أكواد حفر الشبكات مع أكواد حفر المباني وأن تقدم أنماطًا جاهزة وتحذيرات واضحة عند وجود تعارض أو نقص في سياق الحفر."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - اختيار حفر البنية التحتية تلقائيًا (Priority: P1)

كمهندس عروض، عندما أختار جهة مثل الشركة الوطنية للمياه ومشروع مياه أو صرف صحي، أريد أن تظهر لي فقط خيارات الحفر المناسبة لشبكات البنية التحتية حتى لا أخلط عرض الأنابيب والخنادق مع أعمال حفر المباني.

**Why this priority**: هذا هو الخطر الأكبر في العروض الفنية؛ خلط نوع حفر غير مناسب يضعف العرض وقد يؤدي إلى رفضه أو طلب تعديلات جوهرية.

**Independent Test**: يمكن اختباره باختيار مشروع صرف صحي أو مياه مع جهة NWC والتحقق من ظهور خيارات الحفر الخاصة بالخنادق والأنابيب فقط، وعدم ظهور حفر الأساسات أو مكافحة النمل الأبيض ضمن الاختيارات المتاحة أو الأنماط الجاهزة.

**Acceptance Scenarios**:

1. **Given** أن المستخدم اختار جهة NWC ومشروع صرف صحي، **When** يستعرض أكواد الحفر، **Then** تظهر له خيارات مثل حفر دقيق لأنابيب صغيرة، حفر مكشوف لأنابيب رئيسية، وحفر نفقي، ولا تظهر خيارات حفر الأساسات أو مكافحة النمل الأبيض.
2. **Given** أن المستخدم اختار جهة NWC ومشروع مياه، **When** يطبق نمطًا جاهزًا لشبكة توزيع أو خط رئيسي، **Then** يحتوي النمط على نوع حفر بنية تحتية واحد مناسب ولا يضيف أكواد حفر مبانٍ.

---

### User Story 2 - اختيار حفر المباني عند مشاريع الإسكان والإنشاءات (Priority: P1)

كمهندس عروض لمشاريع مبانٍ سكنية أو فلل أو عمائر، عندما أختار الشركة الوطنية للإسكان أو مشروع إنشاءات عامة، أريد أن تظهر لي أكواد حفر المباني مثل الأساسات، نزح المياه، سند الجوانب، مكافحة النمل الأبيض، إحلال التربة، وعزل القواعد.

**Why this priority**: مشاريع المباني لها منطق حفر مختلف تمامًا عن شبكات المياه والصرف؛ الفصل الصحيح يرفع جودة العرض ويجعل المكتبة صالحة لاستخدامات الإسكان.

**Independent Test**: يمكن اختباره باختيار مشروع إنشاءات عامة مع جهة الشركة الوطنية للإسكان والتحقق من أن قائمة الحفر والأنماط الجاهزة تعرض أعمال حفر المباني ولا تعرض حفر الخنادق أو TBM.

**Acceptance Scenarios**:

1. **Given** أن المستخدم اختار الشركة الوطنية للإسكان ومشروع إنشاءات عامة، **When** يستعرض أكواد الحفر، **Then** تظهر أكواد حفر الأساسات والحفر العام وتسوية الموقع والأعمال المرتبطة بحفر المباني.
2. **Given** أن المستخدم يجهز عرضًا لمبنى سكني، **When** يطبق نمطًا جاهزًا للمباني، **Then** يتضمن النمط أعمال حفر المباني الأساسية ولا يتضمن حفرًا نفقيًا أو حفر خنادق أنابيب.

---

### User Story 3 - منع التعارض بين سياقات الحفر (Priority: P2)

كمراجع فني، أريد أن يمنع النظام أو يحذر بوضوح عند اختيار أكواد حفر من سياقات متعارضة، حتى لا يصل عرض غير متماسك إلى مرحلة الاعتماد النهائي.

**Why this priority**: حتى مع القوائم المفلترة قد تحدث اختيارات مخصصة أو استيراد BOQ أو تعديلات لاحقة؛ يحتاج النظام إلى طبقة تحقق تمنع التعارضات.

**Independent Test**: يمكن اختباره بمحاولة جمع كود حفر خنادق مع كود حفر أساسات في عرض واحد لمشروع واحد، والتحقق من ظهور تحذير أو منع واضح قبل البناء.

**Acceptance Scenarios**:

1. **Given** أن العرض خاص بمشروع صرف صحي، **When** يحتوي الاختيار على كود حفر أساسات، **Then** يعرض النظام تعارضًا يوضح أن كود الحفر لا يطابق سياق المشروع.
2. **Given** أن العرض خاص بمشروع إنشاءات عامة، **When** يحتوي الاختيار على كود حفر نفقي، **Then** يظهر تحذير واضح قبل الاعتماد النهائي ويطلب تعديل الاختيار.

---

### User Story 4 - توجيه المستخدم عند نقص حزمة الحفر (Priority: P3)

كمستخدم غير متخصص، أريد أن يخبرني النظام إذا كانت حزمة الحفر ناقصة، مثل اختيار حفر أساسات دون نزح مياه أو سند جوانب عند الحاجة، حتى أستكمل العرض بثقة.

**Why this priority**: هذه ميزة جودة وإرشاد، وتأتي بعد ضمان الفصل الأساسي بين حفر الشبكات وحفر المباني.

**Independent Test**: يمكن اختباره باختيار مشروع مبانٍ يحتوي حفر أساسات فقط والتحقق من أن النظام يقترح عناصر مساندة مناسبة دون إضافتها قسرًا إذا لم تكن إلزامية.

**Acceptance Scenarios**:

1. **Given** أن المستخدم اختار حفر أساسات لمشروع مبنى، **When** يراجع الاعتماد النهائي، **Then** يرى ملاحظات توصية حول نزح المياه أو سند الجوانب أو مكافحة النمل الأبيض إذا لم تكن مختارة.
2. **Given** أن المشروع يحتوي بيانات أو نمطًا يشير إلى وجود مياه جوفية أو حفر عميق، **When** يراجع الاختيار، **Then** يرفع النظام أهمية أكواد النزح أو سند الجوانب كمتطلبات أو توصيات واضحة.

### Edge Cases

- إذا اختار المستخدم أكثر من مشروع في عرض واحد، يجب أن يميز النظام بين سياقات الحفر لكل مشروع وألا يخلط أكواد شبكة المياه مع أكواد مبنى إلا إذا كان العرض متعدد النطاقات ومصرحًا بذلك بوضوح.
- إذا كانت الجهة المالكة تصلح لأكثر من نوع مشروع، مثل جهة عامة تقبل طرقًا أو مباني، يكون نوع المشروع هو المحدد الأساسي لسياق الحفر.
- إذا تم استيراد BOQ يحتوي بنود حفر من سياق مختلف عن المشروع المختار، يجب أن تظهر ملاحظة تعارض قبل الاعتماد النهائي.
- إذا كان كود حفر موجودًا بلا تصنيف سياق، يجب اعتباره غير مؤكد وإظهاره كملاحظة تحتاج مراجعة بدل إدخاله تلقائيًا.
- إذا لم يوجد نمط جاهز مناسب للجهة والمشروع، يجب أن يبقى المستخدم قادرًا على الاختيار اليدوي مع تحذيرات جودة واضحة.
- إذا كان اسم الجهة أو المشروع طويلًا جدًا، أو يحتوي نصًا عربيًا وإنجليزيًا ورموزًا، يجب أن تبقى شاشة الاختيار والاعتماد النهائي قابلة للقراءة دون تداخل أو قص غير مفهوم.
- إذا كانت مكتبة الأكواد فارغة أو لا تحتوي أي كود حفر صالح للسياق المختار، يجب أن تظهر حالة فارغة واضحة تقترح إضافة كود أو اختيار سياق آخر بدل إظهار قائمة صامتة.
- إذا حاول المستخدم تنفيذ الاعتماد النهائي أكثر من مرة بسرعة، يجب ألا تتكرر عملية البناء أو الاعتماد أو تظهر نتائج متعارضة.
- إذا تم فتح عرض قديم يحتوي أكواد حفر لم تعد مصنفة أو لم تعد مناسبة للسياق الحالي، يجب أن يفتح للقراءة مع ملاحظة مراجعة بدل أن يفشل.
- إذا كان المستخدم يعمل بتكبير شاشة عالٍ أو حجم خط كبير، يجب أن تظل رسائل التعارض والتحذير قابلة للقراءة بالكامل.
- إذا كان المستخدم يعمل على شاشة لابتوب صغيرة نسبيًا، يجب أن يستطيع إكمال اختيار سياق الحفر والاعتماد النهائي دون فقد أزرار أساسية خارج الشاشة.
- إذا كان المستخدم يعمل على شاشة كبيرة أو 4K، يجب أن تستفيد الواجهة من المساحة الإضافية لعرض الاختيارات والمراجعة دون تمديد النصوص لمسافات تصعب قراءتها.
- إذا كان المستخدم يستخدم لوحة مفاتيح فقط أو جهاز لمس على Windows، يجب أن تبقى عناصر اختيار الحفر والاعتماد النهائي قابلة للوصول دون الاعتماد على التحويم بالماوس فقط.
- إذا كان المستخدم يعاني من عمى ألوان أو يعمل على شاشة منخفضة الجودة، يجب أن تبقى حالة سياق الحفر مفهومة من النص والرموز وليس اللون وحده.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST classify excavation-related codes by excavation context, including infrastructure trenching, open trench/mainline excavation, tunneling, road/asphalt removal, building foundations, general site excavation, dewatering, shoring/support, termite treatment, soil replacement, and foundation waterproofing.
- **FR-002**: System MUST use the selected project type and owner to determine which excavation contexts are valid for the current proposal.
- **FR-003**: System MUST show infrastructure excavation options for NWC water and wastewater proposals and exclude building excavation options from normal selection and presets for that context.
- **FR-004**: System MUST show building excavation options for NHI/NHC or general construction proposals and exclude infrastructure trenching and tunneling options from normal selection and presets for that context.
- **FR-005**: System MUST prevent mutually exclusive excavation methods from being selected together within the same project scope unless the proposal is explicitly multi-scope and each excavation method belongs to a separate scope.
- **FR-006**: System MUST warn before final approval when selected excavation codes do not match the selected project and owner context.
- **FR-007**: System MUST identify missing recommended excavation companion activities for building projects, including dewatering, shoring/support, termite treatment, soil replacement, and foundation waterproofing, when they are relevant to the selected excavation scenario.
- **FR-008**: System MUST provide or update ready-made presets so common NWC network scenarios and NHI/NHC building scenarios contain context-appropriate excavation packages.
- **FR-009**: System MUST ensure final review clearly states whether excavation selection is context-valid, missing recommended activities, or blocked by a conflict.
- **FR-010**: System MUST support manual expert override only when the final review records the mismatch and the user confirms the decision.
- **FR-011**: System MUST keep existing valid NWC water and wastewater workflows usable after the feature is introduced.
- **FR-012**: System MUST keep existing valid general construction workflows usable after the feature is introduced.
- **FR-013**: System MUST display clear empty states when no excavation code or preset is available for the selected owner and project context.
- **FR-014**: System MUST preserve user selections and entered proposal data when an excavation-context warning appears, so users can correct the issue without starting over.
- **FR-015**: System MUST make conflict and warning messages readable for long Arabic/English mixed labels, including long owner names, project names, and code descriptions.
- **FR-016**: System MUST avoid duplicate final approval or build actions if the user repeats the same action rapidly.
- **FR-017**: System MUST treat unclassified excavation codes as review-required items and never auto-select them silently.
- **FR-018**: System MUST provide Arabic messages that state the problem, the affected code or context, and the recommended correction.
- **FR-019**: System MUST keep excavation selection and final review usable at common desktop and laptop window sizes used by office engineers.
- **FR-020**: System MUST adapt dense excavation lists through grouping, scrolling, or progressive disclosure so the user can still compare choices without losing context.
- **FR-021**: System MUST keep primary actions visible or reachable when text size or display scaling is increased.
- **FR-022**: System MUST support keyboard-only navigation for the excavation selection, warnings, and final review confirmation flow.
- **FR-023**: System MUST ensure touch-capable Windows devices have sufficiently large and separated interaction targets for excavation selection and final review actions.
- **FR-024**: System MUST present multi-project excavation contexts in a way that separates scopes clearly instead of compressing all choices into one indistinguishable list.
- **FR-025**: System MUST use color purposefully to distinguish excavation contexts, validation states, and final review decisions while staying consistent with the ATPAS professional navy/gold identity.
- **FR-026**: System MUST reserve strong warning and error colors for real conflicts or blocked decisions, not normal informational categories.
- **FR-027**: System MUST pair every color-coded excavation state with text, icon, label, or grouping so color is never the only indicator.
- **FR-028**: System MUST keep success, warning, blocked, and informational states visually distinct across selection lists, presets, and final review.
- **FR-029**: System MUST avoid using many unrelated colors for excavation categories; colors should be limited, consistent, and tied to user meaning.
- **FR-030**: System MUST maintain readable contrast for all colored text, badges, borders, and decision messages.

### Key Entities

- **Excavation Context**: A business category describing the correct excavation family for a proposal, such as infrastructure network excavation, road/asphalt excavation, or building excavation.
- **Excavation Code**: A selectable technical activity related to excavation or its companions, identified by code, Arabic name, applicable project types, applicable owners, and context classification.
- **Project Scope**: The selected project type or combination of project types that determines which excavation contexts are acceptable.
- **Owner Context**: The selected owner or client entity, used with project scope to guide and validate code selection.
- **Excavation Package**: A group of one primary excavation method and its required or recommended companion activities for a common proposal scenario.
- **Context Validation Result**: The review outcome indicating valid, warning, or blocked excavation selection, with Arabic explanation for the user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of NWC water and wastewater presets contain only infrastructure-compatible excavation methods.
- **SC-002**: 100% of NHI/NHC or general construction presets contain only building-compatible excavation methods.
- **SC-003**: Users can identify and select a valid excavation method for a common NWC network proposal in under 60 seconds.
- **SC-004**: Users can identify and select a valid excavation package for a common building proposal in under 90 seconds.
- **SC-005**: Final review detects 100% of deliberate test cases where building excavation is mixed into a water/wastewater proposal or infrastructure tunneling is mixed into a building proposal.
- **SC-006**: Smoke tests for one NWC wastewater preset and one NHI/NHC building preset complete with zero validation errors.
- **SC-007**: Support or review notes related to wrong excavation method selection are reduced by at least 80% after the feature is adopted.
- **SC-008**: Users can recover from a context warning without losing their selected project, owner, or selected codes in 100% of tested warning scenarios.
- **SC-009**: Long Arabic/English mixed owner and project names remain readable with no critical overlap in the selection screen and final review.
- **SC-010**: Repeated rapid approval or build attempts result in only one recorded approval/build action in 100% of tested cases.
- **SC-011**: Users can complete the NWC excavation selection flow on a typical laptop display in under 90 seconds without hidden critical actions.
- **SC-012**: Users can complete the NHI/NHC building excavation selection flow with increased display scaling without text overlap or clipped approval actions.
- **SC-013**: Keyboard-only users can reach every excavation filter, selectable code, warning, and final approval action in a logical order.
- **SC-014**: On wide displays, excavation choices remain readable and grouped, with no primary text line exceeding a comfortable review length in the main decision areas.
- **SC-015**: Users can correctly identify infrastructure excavation, building excavation, warning, and blocked states from the interface without needing external explanation.
- **SC-016**: In accessibility review, no required excavation-context decision depends on color alone.
- **SC-017**: Reviewers rate the color treatment as clear and professional in at least 90% of internal acceptance checks.

## Assumptions

- NWC proposals primarily cover water, wastewater, and water transmission infrastructure unless paired with a different project scope.
- NHI is the current registry key for the National Housing Company; NHC may be treated as an alias or future display label for the same business owner if needed.
- Project type is the primary determinant of excavation context; owner refines the allowed set but does not override project meaning.
- Building excavation companion activities may start as recommended items unless project data or preset scenario makes them mandatory.
- Existing code IDs and proposal history should remain readable; this feature extends classification and validation rather than renaming historical records.
- Manual expert override is allowed for rare real-world mixed-scope cases, but it must be visible in the final review so the risk is not hidden.
- The primary target is a Windows desktop/laptop office workflow, with support for common display scaling and touch-capable Windows devices.
- Mobile phone use is not a primary scenario for this feature; adaptation focuses on desktop window sizes, large displays, high scaling, keyboard use, and optional touch input.
- Color should reinforce ATPAS brand behavior: navy for structure and trust, gold for important decisions or primary emphasis, restrained green for valid/ready states, amber for caution, and red only for blocked or conflicting choices.
- Excavation context colors should help recognition but remain secondary to Arabic labels and grouping.
