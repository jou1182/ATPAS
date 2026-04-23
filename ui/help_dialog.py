#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نافذة المساعدة الشاملة لنظام ATPAS.

تحتوي على أربعة تبويبات:
  1. كيف تستخدم النظام  — دليل خطوة بخطوة للمبتدئين
  2. الأكواد والمراحل   — مرجع سريع لكل فئة
  3. اختصارات لوحة المفاتيح
  4. استكشاف الأخطاء    — حلول للمشاكل الشائعة

المستدعي: MainWindow (F1 أو زر ❓ في الـ Header)
"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


# ─────────────────────────────────────────────────────────────────────────────
# محتوى التبويبات (HTML عربي موجّه من اليمين لليسار)
# ─────────────────────────────────────────────────────────────────────────────

# _STYLE_BASE: هيكل HTML كامل مع <html dir="rtl"> لضمان RTL في Qt
_STYLE_BASE = """<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8">
<style>
  body  { font-family:'Segoe UI',Arial,sans-serif; font-size:13px;
          color:#1a1a1a; direction:rtl; text-align:right;
          margin:8px 12px; padding:0; }
  h2    { color:#152433; border-bottom:2px solid #C9921B;
          padding-bottom:6px; margin-top:18px; font-size:15px; }
  h3    { color:#1C3045; margin-top:14px; font-size:13px; }
  p     { margin:6px 0; }
  .step { background:#EEF5FB; border-right:4px solid #1C3045;
          border-radius:6px; padding:10px 14px; margin:8px 0; }
  .num  { background:#152433; color:#C9921B; border-radius:50%;
          display:inline-block; width:24px; height:24px;
          text-align:center; font-weight:800; line-height:24px;
          margin-left:8px; }
  .tip  { background:#FFF8E7; border-right:4px solid #C9921B;
          border-radius:6px; padding:8px 12px; margin:8px 0; font-size:12px; }
  .warn { background:#FFF3E0; border-right:4px solid #E65100;
          border-radius:6px; padding:8px 12px; margin:8px 0; }
  .ok   { background:#E8F5E9; border-right:4px solid #2E7D32;
          border-radius:6px; padding:8px 12px; margin:8px 0; }
  table { width:100%; border-collapse:collapse; margin:10px 0; }
  th    { background:#152433; color:#C9921B; padding:8px 12px;
          font-weight:700; }
  td    { padding:7px 12px; border-bottom:1px solid #E0E0E0; }
  tr:nth-child(even) td { background:#F5F5F5; }
  kbd   { background:#E8E8E8; border:1px solid #999; border-radius:4px;
          padding:2px 7px; font-size:12px; font-family:Consolas,monospace; }
  .badge{ background:#C9921B; color:white; border-radius:4px;
          padding:2px 8px; font-size:11px; font-weight:700; }
</style></head>
"""

_HOW_TO_HTML = _STYLE_BASE + """
<body dir="rtl">
<h2>🚀 كيف تستخدم نظام ATPAS</h2>

<p>النظام يعمل في <strong>ثلاث خطوات رئيسية</strong> فقط:</p>

<div class="step">
  <span class="num">1</span>
  <strong>اختر نوع المشروع والجهة المالكة</strong><br>
  في أعلى الشاشة، اختر نوع المشروع من القائمة (صرف صحي، مياه، أسفلت...) ثم اختر الجهة
  المالكة (NWC، أمانة مكة، وزارة الإسكان...). ستظهر الأكواد المناسبة تلقائياً.
</div>

<div class="step">
  <span class="num">2</span>
  <strong>اختر الأكواد التي تريدها</strong><br>
  في القائمة الوسطى، ضع علامة ✓ على كل بند تريد إدراجه في العرض الفني.
  يمكنك استخدام <strong>الأنماط الجاهزة</strong> (Presets) في الشريط العلوي لتحديد مجموعات دفعة واحدة،
  أو كتابة اسم الكود في خانة البحث (Ctrl+F).
</div>

<div class="step">
  <span class="num">3</span>
  <strong>ابنِ العرض الفني</strong><br>
  في اللوحة اليمنى (المعاينة)، راجع الأكواد المختارة. عند وجود أي تحذيرات استخدم
  زر <strong>«إصلاح تلقائي»</strong> لإكمال التبعيات الناقصة تلقائياً. ثم اضغط
  <strong>«بناء العرض الفني»</strong> وسيُنشئ النظام ملف Word جاهزاً.
</div>

<h2>📋 شرح أجزاء الشاشة</h2>

<table>
  <tr><th>الجزء</th><th>الوظيفة</th></tr>
  <tr><td>شريط الأنماط الجاهزة</td><td>مجموعات أكواد شائعة — اضغط واحدة لتحديد الكل دفعة</td></tr>
  <tr><td>قائمة الأكواد (اليسار)</td><td>كل الأكواد المتاحة لمشروعك — ضع علامة على ما تريد</td></tr>
  <tr><td>لوحة المعاينة (اليمين)</td><td>ملخص ما اخترته + رسائل التحقق + زر البناء</td></tr>
  <tr><td>شريط الحالة (أسفل)</td><td>نصائح وتعليمات تتغير كل 10 ثوانٍ</td></tr>
</table>

<div class="tip">
  💡 <strong>نصيحة:</strong> استخدم الأنماط الجاهزة إذا كان مشروعك معياريًا —
  توفّر أكثر من 80% من وقت الاختيار.
</div>

<h2>🔍 البحث عن كود</h2>
<p>اضغط <kbd>Ctrl</kbd>+<kbd>F</kbd> في أي وقت لتركيز خانة البحث.
اكتب اسم الكود (مثل: SUR) أو جزء من الاسم العربي (مثل: مسح) وستُصفَّى القائمة فوراً.</p>

<div class="ok">
  ✅ <strong>لا يحتاج النظام اتصالاً بالإنترنت</strong> — يعمل بالكامل على جهازك محلياً.
</div>
</body></html>
"""

_CODES_HTML = _STYLE_BASE + """
<body dir="rtl">
<h2>📑 الأكواد والمراحل — مرجع سريع</h2>

<h3>تركيب الكود</h3>
<div class="step" style="font-family: Consolas, monospace; font-size: 14px; text-align: center; direction: ltr;">
  001 - SUR - BASE<br>
  <span style="color: #888; font-size: 11px;">
    الفئة — المرحلة — التنويع
  </span>
</div>

<h3>الفئات الرئيسية</h3>
<table>
  <tr><th>الرقم</th><th>الفئة</th><th>الأكواد الشائعة</th></tr>
  <tr><td><strong>001</strong></td><td>الأعمال التحضيرية</td><td>مسح، رخص، اعتمادات، إدارة مرور</td></tr>
  <tr><td><strong>002</strong></td><td>الحفر والمخلفات</td><td>حفر، إزالة، تسوية، جلخ أسفلت</td></tr>
  <tr><td><strong>003</strong></td><td>التركيب والتوصيل</td><td>أنابيب، خرسانة، أسفلت، هياكل فولاذية</td></tr>
  <tr><td><strong>004</strong></td><td>الاختبارات والفحوصات</td><td>ضغط، جودة خرسانة، سماكة، دك</td></tr>
  <tr><td><strong>005</strong></td><td>الإنهاء والتسليم</td><td>ردم، استعادة سطح، دهانات طريق، تسليم</td></tr>
</table>

<h3>أنواع المشاريع</h3>
<table>
  <tr><th>المعرّف</th><th>الاسم</th><th>رمز الشبكة</th></tr>
  <tr><td>wastewater</td><td>الصرف الصحي</td><td>S</td></tr>
  <tr><td>water_supply</td><td>إمدادات المياه</td><td>W</td></tr>
  <tr><td>asphalt</td><td>الطرق والأسفلت</td><td>A</td></tr>
  <tr><td>road_maintenance</td><td>صيانة الطرق</td><td>R</td></tr>
  <tr><td>general_construction</td><td>الإنشاءات العامة</td><td>C</td></tr>
  <tr><td>water_transmission</td><td>خطوط نقل المياه</td><td>T</td></tr>
</table>

<h3>الجهات المالكة</h3>
<table>
  <tr><th>المعرّف</th><th>الجهة</th><th>الشبكات</th></tr>
  <tr><td>nwc</td><td>الشركة الوطنية للمياه</td><td>S, W</td></tr>
  <tr><td>makkah</td><td>أمانة العاصمة المقدسة</td><td>S, W, A</td></tr>
  <tr><td>moh</td><td>وزارة الإسكان</td><td>S, W, A</td></tr>
  <tr><td>mot</td><td>وزارة النقل والخدمات اللوجستية</td><td>R, A</td></tr>
  <tr><td>swa</td><td>الهيئة السعودية للمياه</td><td>W, T</td></tr>
  <tr><td>nhi</td><td>الشركة الوطنية للإسكان</td><td>C</td></tr>
  <tr><td>amana_riyadh</td><td>أمانة منطقة الرياض</td><td>R, A, S, W</td></tr>
  <tr><td>amana_qassim</td><td>أمانة منطقة القصيم</td><td>R, A, S, W</td></tr>
  <tr><td>ksia</td><td>مطار الملك سلمان الدولي</td><td>C, R, A</td></tr>
</table>

<div class="tip">
  💡 <strong>كيف يعمل التصفية؟</strong> عند اختيار مشروع وجهة، تظهر فقط الأكواد
  التي تنتمي لهذا المشروع وتقبلها هذه الجهة. الأكواد الإلزامية تُحدَّد تلقائياً.
</div>
</body></html>
"""

_SHORTCUTS_HTML = _STYLE_BASE + """
<body dir="rtl">
<h2>⌨️ اختصارات لوحة المفاتيح</h2>

<table>
  <tr><th>الاختصار</th><th>الوظيفة</th></tr>
  <tr>
    <td><kbd>F1</kbd></td>
    <td>فتح نافذة المساعدة (هذه النافذة)</td>
  </tr>
  <tr>
    <td><kbd>Ctrl</kbd> + <kbd>F</kbd></td>
    <td>تركيز خانة البحث في قائمة الأكواد</td>
  </tr>
  <tr>
    <td><kbd>Ctrl</kbd> + <kbd>A</kbd></td>
    <td>تحديد كل نص في خانة البحث (لمسحه سريعاً)</td>
  </tr>
  <tr>
    <td><kbd>Escape</kbd></td>
    <td>مسح خانة البحث وإظهار كل الأكواد</td>
  </tr>
  <tr>
    <td><kbd>Space</kbd></td>
    <td>تحديد / إلغاء تحديد الكود المُظلَّل</td>
  </tr>
  <tr>
    <td><kbd>Alt</kbd> + <kbd>F4</kbd></td>
    <td>إغلاق التطبيق</td>
  </tr>
</table>

<h3>نصائح للعمل الأسرع</h3>

<div class="tip">
  ⚡ <strong>الأنماط الجاهزة (Presets):</strong> للمشاريع المعيارية، اختر نمطاً جاهزاً
  من الشريط العلوي — يُعيّن المشروع والجهة ويُحدّد كل الأكواد دفعة واحدة.
</div>

<div class="tip">
  🔍 <strong>البحث الذكي:</strong> يمكنك البحث بالرقم (001)، بكود المرحلة (SUR)،
  أو بجزء من الاسم العربي (مسح أو حفر).
</div>

<div class="tip">
  🔧 <strong>الإصلاح التلقائي:</strong> عند ظهور خطأ "تبعية ناقصة"، اضغط زر
  «إصلاح تلقائي» في لوحة المعاينة — سيُضيف الأكواد الناقصة تلقائياً.
</div>

<div class="ok">
  ✅ <strong>بدون أخطاء = جاهز للبناء.</strong> يُفعَّل زر «بناء العرض» فقط عند
  اجتياز كل فحوصات التحقق.
</div>
</body></html>
"""

_TROUBLESHOOT_HTML = _STYLE_BASE + """
<body dir="rtl">
<h2>🔧 استكشاف الأخطاء — حلول للمشاكل الشائعة</h2>

<h3>❓ لماذا لا تظهر بعض الأكواد في القائمة؟</h3>
<div class="tip">
  الأكواد مُصنَّفة حسب المشروع والجهة. إذا لم يظهر كود معيّن:<br>
  ▪ تأكد أن المشروع المختار يشمل هذا الكود<br>
  ▪ تأكد أن الجهة المالكة مخوّلة لهذا الكود<br>
  ▪ ابحث عن الكود بخانة البحث (Ctrl+F) — ربما هو موجود في مجموعة أخرى
</div>

<h3>❓ ظهر خطأ «تبعية ناقصة» — ماذا أفعل؟</h3>
<div class="ok">
  اضغط زر <strong>«إصلاح تلقائي»</strong> في لوحة المعاينة.
  النظام يُضيف الأكواد المطلوبة تلقائياً. هذا ليس خطأً — بعض الأكواد
  تتطلب بنوداً أخرى أن تكون موجودة قبلها (مثلاً: الحفر يحتاج مسحاً مسبقاً).
</div>

<h3>❓ زر «بناء العرض» غير مُفعَّل</h3>
<div class="tip">
  يتطلب التفعيل:<br>
  ▪ تحديد كود واحد على الأقل<br>
  ▪ لا وجود لأخطاء تحقق (الإصلاح التلقائي يحلها)
</div>

<h3>❓ ملف الـ Word الناتج يحتوي نصوصاً عامة بدل المحتوى الحقيقي</h3>
<div class="warn">
  ⚠️ هذا يعني أن ملف Word الخاص بهذا الكود غير موجود في مكتبة المحتوى.
  الحل: أضف الملف إلى مجلد <strong>templates/source_documents/</strong>
  باسم <strong>{CODE_ID}.docx</strong> (مثال: 001-SUR-BASE.docx).
  راجع دليل المستخدم (docs/USER_GUIDE_AR.md) للتفاصيل.
</div>

<h3>❓ التطبيق يعمل على جهاز لكن الواجهة تبدو قديمة على جهاز آخر</h3>
<div class="warn">
  ⚠️ <strong>المشكلة الأكثر شيوعاً:</strong> نسخت مجلد dist\\ATPAS\\ القديم
  بدون إعادة البناء أولاً.<br><br>
  <strong>الحل الصحيح:</strong><br>
  1. عند أي تغيير في الكود أو البيانات: شغّل <strong>build_exe.bat</strong> أولاً<br>
  2. انتظر حتى ينتهي (دقيقتين تقريباً)<br>
  3. انسخ مجلد <strong>dist\\ATPAS\\</strong> بالكامل للجهاز الآخر<br>
  4. الواجهة ستُظهر تاريخ البناء في أعلى الشاشة للتأكد من الإصدار
</div>

<h3>❓ الملف الناتج لا يفتح في Word</h3>
<div class="tip">
  ▪ تأكد من وجود Microsoft Word 2016 أو أحدث<br>
  ▪ الملف في مجلد output/generated_documents/ بجوار ATPAS.exe<br>
  ▪ اضغط «فتح المجلد» في نافذة البناء للوصول المباشر
</div>

<h3>❓ النظام بطيء أو يتجمّد أثناء البناء</h3>
<div class="ok">
  هذا طبيعي لمشاريع كبيرة (20+ كوداً بصور مدمجة). الشريط يتحرك خلف الكواليس —
  انتظر حتى تظهر رسالة «✅ العرض الفني جاهز».
</div>

<h2>📞 للمساعدة الإضافية</h2>
<div class="ok">
  راجع ملف الدليل الكامل: <strong>docs/USER_GUIDE_AR.md</strong><br>
  أو راجع وثائق SSOT في: <strong>SSOT/ATPAS_REFERENCE_DOCUMENT_v3.0.md</strong>
</div>
</body></html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# HelpDialog
# ─────────────────────────────────────────────────────────────────────────────

class HelpDialog(QDialog):
    """
    نافذة المساعدة الشاملة لنظام ATPAS.

    Usage:
        dialog = HelpDialog(parent=self, tab_index=0)
        dialog.exec_()
    """

    def __init__(self, parent=None, tab_index: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("المساعدة — نظام ATPAS")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(680, 560)
        self.resize(740, 600)
        self.setModal(True)

        self._build_ui(tab_index)

    def _build_ui(self, tab_index: int) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 8)

        # ── عنوان ──────────────────────────────────────────────────────
        title = QLabel("❓ المساعدة — نظام بناء العروض الفنية")
        title.setStyleSheet("""
            font-size: 16px; font-weight: 800; color: #152433;
            padding: 4px 0; border-bottom: 2px solid #C9921B;
        """)
        layout.addWidget(title)

        # ── تبويبات ────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab {
                font-size: 12px; padding: 7px 16px;
                font-weight: 600; min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #152433; color: #C9921B;
                border-bottom: 3px solid #C9921B;
            }
            QTabBar::tab:!selected {
                background: #F0F0F0; color: #444;
            }
            QTabWidget::pane { border: 1px solid #DDD; }
        """)

        tabs.addTab(self._make_browser(_HOW_TO_HTML),     "كيف تستخدم")
        tabs.addTab(self._make_browser(_CODES_HTML),       "الأكواد والمراحل")
        tabs.addTab(self._make_browser(_SHORTCUTS_HTML),   "اختصارات")
        tabs.addTab(self._make_browser(_TROUBLESHOOT_HTML),"استكشاف الأخطاء")

        tabs.setCurrentIndex(max(0, min(tab_index, 3)))
        layout.addWidget(tabs, stretch=1)

        # ── أزرار ──────────────────────────────────────────────────────
        from PyQt5.QtWidgets import QHBoxLayout, QPushButton

        btn_row = QHBoxLayout()

        # زر "أعد عرض دليل البداية" — يحذف ملف الترحيب ويفتح الشاشة مجدداً
        welcome_btn = QPushButton("🏁 أعد عرض دليل البداية")
        welcome_btn.setToolTip("يحذف علامة 'شاهدت الترحيب' ويفتح شاشة البداية الآن")
        welcome_btn.setStyleSheet("""
            QPushButton {
                background: #1C3045; color: #C9921B;
                border: none; border-radius: 5px;
                padding: 6px 16px; font-size: 12px; font-weight: 700;
            }
            QPushButton:hover { background: #152433; }
        """)
        welcome_btn.clicked.connect(self._reshow_welcome)

        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #152433; color: white;
                border: none; border-radius: 5px;
                padding: 6px 24px; font-size: 12px; font-weight: 700;
            }
            QPushButton:hover { background: #1C3045; }
        """)
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(welcome_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _reshow_welcome(self) -> None:
        """احذف ملف الترحيب وأعد عرض شاشة البداية فوراً."""
        from ui.welcome_overlay import WelcomeDialog, _get_marker_path
        marker = _get_marker_path()
        try:
            marker.unlink(missing_ok=True)
        except OSError:
            pass
        self.accept()                          # أغلق نافذة المساعدة
        WelcomeDialog(self.parent()).exec_()   # أظهر شاشة الترحيب

    @staticmethod
    def _make_browser(html: str) -> QTextBrowser:
        """صفحة HTML قابلة للتمرير داخل التبويب — RTL عربي."""
        from PyQt5.QtGui import QTextOption
        browser = QTextBrowser()
        browser.setLayoutDirection(Qt.RightToLeft)
        browser.setHtml(html)
        # إجبار RTL على مستوى المستند (يتجاوز قيود Qt على ul/li)
        opt = browser.document().defaultTextOption()
        opt.setTextDirection(Qt.RightToLeft)
        browser.document().setDefaultTextOption(opt)
        browser.setOpenExternalLinks(False)
        browser.setStyleSheet("border: none; background: white; padding: 4px;")
        return browser


# ─────────────────────────────────────────────────────────────────────────────
# اختبار مستقل (شغّل الملف مباشرة)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dlg = HelpDialog(tab_index=0)
    dlg.show()
    sys.exit(app.exec_())
