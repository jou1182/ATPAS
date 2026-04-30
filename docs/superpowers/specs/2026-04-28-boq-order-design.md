# BOQ Order Preservation — وثيقة التصميم
**التاريخ:** 2026-04-28
**الإصدار:** 1.0
**المسؤول:** د. يوسف سليم
**الحالة:** مُنفَّذ ✅ — `engine/resolver.py` → `resolve_with_order()`

---

## 1. المشكلة

بعد استيراد جدول الكميات عبر BOQ Importer، يُرتَّب ملف Word الناتج حسب `sequence_order`
في السجل الداخلي — لا حسب تسلسل بنود المنافسة. المهندس يريد أن يجد الأقسام في نفس
ترتيب العميل، ما يُسهّل المراجعة والتقديم.

---

## 2. الحل — resolve_with_order

```
Excel (ترتيب المنافسة)
        ↓ BOQ Importer
BOQReviewPanel → يحفظ الترتيب في codes_accepted(code_ids)
        ↓
MainWindow._boq_order = code_ids   ← جديد: يحفظ الترتيب
        ↓
Builder.build(boq_order=...)       ← جديد: يمرر الترتيب
        ↓
resolver.resolve_with_order()      ← جديد: يحقن التبعيات بالترتيب
        ↓
Word مرتب بترتيب المنافسة ✅
```

---

## 3. الخوارزمية — resolve_with_order

**المدخل:**
- `selected_codes`: جميع الأكواد المختارة
- `boq_order`: الأكواد بترتيب Excel (subset أو كل selected_codes)

**الخطوات:**
1. حساب المجموعة الكاملة (مع التبعيات المتعدية) من `selected_codes`
2. تحديد الأكواد الزائدة (في المجموعة الكاملة لكن ليست في boq_order) → `extras`
3. المرور على `boq_order` بالتسلسل:
   - قبل كل كود: حقن أي تبعية من `extras` لم تُحقن بعد
   - إضافة الكود
4. إلحاق أي extras متبقية (مرتبة بـ sequence_order) في النهاية

**مثال:**
```
BOQ order:  [حفر, خرسانة, أسفلت]
التبعيات:   حفر ← يحتاج [مسح]
extras:     {مسح}

النتيجة:    [مسح←محقون, حفر, خرسانة, أسفلت] ✅
```

---

## 4. الملفات المتأثرة

| الملف | التعديل | الحجم |
|-------|---------|-------|
| `engine/dependency_resolver.py` | إضافة `resolve_with_order()` | +25 سطر |
| `ui/main_window.py` | `_boq_order` + تمرير للـ dialog | +10 سطر |
| `ui/build_progress.py` | `boq_order` param في Worker + Dialog | +8 سطر |
| `engine/builder.py` | `boq_order` param في `build()` | +5 سطر |
| `tests/test_boq_ordering.py` | اختبارات الترتيب الجديد | ملف جديد |

**لا تغيير في:** JSON schemas, codes_registry, master_config, أي UI آخر.

---

## 5. مبدأ Backward Compatibility

```python
# السلوك القديم — لم يتغير
builder.build(selected_codes=[...], project_id=..., owner_id=...)
# → resolver.resolve()  ← نفس الترتيب القديم

# السلوك الجديد — عند استيراد BOQ فقط
builder.build(selected_codes=[...], project_id=..., owner_id=..., boq_order=[...])
# → resolver.resolve_with_order()  ← ترتيب المنافسة
```

---

## 6. معايير النجاح

- BOQ مكون من 10 بنود → Word مرتب بنفس تسلسلها
- تبعية ناقصة تُحقن قبل الكود الذي يحتاجها (لا في النهاية)
- البناء العادي (بدون BOQ) لا يتأثر
- جميع الاختبارات الحالية (281) تستمر ناجحة
- اختبارات جديدة ≥ 8 سيناريوهات تغطي الحالات الحدية
