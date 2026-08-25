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
from PyQt5.QtGui import QFont, QTextOption
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

from ui import theme


# ─────────────────────────────────────────────────────────────────────────────
# محتوى التبويبات (HTML عربي موجّه من اليمين لليسار)
# ─────────────────────────────────────────────────────────────────────────────

# _STYLE_BASE: هيكل HTML كامل مع <html dir="rtl"> لضمان RTL في Qt
_STYLE_BASE = f"""<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8">
<style>
  body  {{ font-family:'Tajawal'; font-size:13px;
          color:{theme.TEXT}; direction:rtl; text-align:right;
          margin:10px 14px; padding:0; unicode-bidi:embed; }}
  h2    {{ color:{theme.HEADER}; border-bottom:2px solid {theme.ACCENT};
          padding-bottom:6px; margin-top:16px; margin-bottom:8px;
          font-size:16px; font-weight:800; text-align:right; }}
  h3    {{ color:{theme.NAVY_MID}; margin-top:12px; margin-bottom:6px;
          font-size:14px; font-weight:800; text-align:right; }}
  p     {{ margin:6px 0; text-align:right; direction:rtl; }}
  .step {{ background:#EEF5FB; border-right:4px solid {theme.NAVY_MID};
          border-radius:6px; padding:10px 14px; margin:8px 0;
          text-align:right; direction:rtl; }}
  .num  {{ background:{theme.HEADER}; color:{theme.ACCENT}; border-radius:50%;
          display:inline-block; width:24px; height:24px;
          text-align:center; font-weight:800; line-height:24px;
          margin-left:8px; }}
  .tip  {{ background:#FFF8E7; border-right:4px solid {theme.ACCENT};
          border-radius:6px; padding:8px 12px; margin:8px 0; font-size:12px;
          text-align:right; direction:rtl; }}
  .warn {{ background:#FFF4E6; border-right:4px solid __WARNING__;
          border-radius:6px; padding:8px 12px; margin:8px 0;
          text-align:right; direction:rtl; }}
  .ok   {{ background:#EAF5EF; border-right:4px solid __SUCCESS__;
          border-radius:6px; padding:8px 12px; margin:8px 0;
          text-align:right; direction:rtl; }}
  .line {{ margin:3px 0; text-align:right; direction:rtl; }}
  .ltr  {{ direction:ltr; unicode-bidi:embed; display:inline-block;
          font-family:Tajawal; }}
  table {{ width:100%; border-collapse:collapse; margin:10px 0; }}
  th    {{ background:{theme.HEADER}; color:{theme.ACCENT}; padding:8px 12px;
          font-weight:700; text-align:right; direction:rtl; }}
  td    {{ padding:7px 12px; border-bottom:1px solid #E0E0E0;
          text-align:right; direction:rtl; }}
  tr:nth-child(even) td {{ background:#F5F5F5; }}
  kbd   {{ background:#E8E8E8; border:1px solid #999; border-radius:4px;
          padding:2px 7px; font-size:12px; font-family:Tajawal; }}
  .badge{{ background:{theme.ACCENT}; color:white; border-radius:4px;
          padding:2px 8px; font-size:11px; font-weight:700; }}
</style></head>
""".replace("__WARNING__", theme.WARNING).replace("__SUCCESS__", theme.SUCCESS)

_HOW_TO_HTML = _STYLE_BASE + """
<body dir="rtl">
<h2>كيف تستخدم النظام</h2>

<p>النظام يعمل في <strong>ثلاث خطوات رئيسية</strong> فقط:</p>

<div class="step">
  <p class="line"><strong>الخطوة الأولى: اختر نوع المشروع والجهة المالكة</strong></p>
  <p class="line">في أعلى الشاشة، اختر نوع المشروع من القائمة، ثم اختر الجهة المالكة.</p>
  <p class="line">ستظهر الأكواد المناسبة تلقائياً حسب اختيارك.</p>
</div>

<div class="step">
  <p class="line"><strong>الخطوة الثانية: اختر الأكواد التي تريدها</strong></p>
  <p class="line">في القائمة الوسطى، ضع علامة على كل بند تريد إدراجه في العرض الفني.</p>
  <p class="line">يمكنك استخدام الأنماط الجاهزة أو البحث عن الكود من خانة البحث <span dir="ltr">Ctrl+F</span>.</p>
</div>

<div class="step">
  <p class="line"><strong>الخطوة الثالثة: ابنِ العرض الفني</strong></p>
  <p class="line">في اللوحة اليمنى، راجع الأكواد المختارة ورسائل التحقق.</p>
  <p class="line">عند عدم وجود أخطاء، اضغط «بناء العرض الفني» وسيُنشئ النظام ملف وورد جاهزاً.</p>
</div>

<h2>شرح أجزاء الشاشة</h2>

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

<h2>البحث عن كود</h2>
<p>اضغط <kbd>Ctrl</kbd>+<kbd>F</kbd> في أي وقت لتركيز خانة البحث.
اكتب اسم الكود (مثل: SUR) أو جزء من الاسم العربي (مثل: مسح) وستُصفَّى القائمة فوراً.</p>

<div class="ok">
  ✅ <strong>لا يحتاج النظام اتصالاً بالإنترنت</strong> — يعمل بالكامل على جهازك محلياً.
</div>
</body></html>
"""

_CODES_HTML = _STYLE_BASE + """
<body dir="rtl">
<h2>الأكواد والمراحل — مرجع سريع</h2>

<h3>تركيب الكود</h3>
<div class="step" style="font-family: Tajawal; font-size: 14px; text-align: center; direction: ltr;">
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

<h3>أمثلة من الجهات المالكة</h3>
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
  التي تنتمي لهذا المشروع وتقبلها هذه الجهة. يدعم النظام 20 جهة مالكة، والأكواد الإلزامية تُحدَّد تلقائياً.
</div>
</body></html>
"""

_SHORTCUTS_HTML = _STYLE_BASE + """
<body dir="rtl">
<h2>اختصارات لوحة المفاتيح</h2>

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
    <td><kbd>Alt</kbd> + <kbd>F4</kbd></td>
    <td>إغلاق التطبيق</td>
  </tr>
</table>

<h3>نصائح للعمل الأسرع</h3>

<div class="tip">
  ⚡ <strong>الأنماط الجاهزة:</strong> للمشاريع المعيارية، اختر نمطاً جاهزاً
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
<h2>استكشاف الأخطاء — حلول للمشاكل الشائعة</h2>

<h3>لماذا لا تظهر بعض الأكواد في القائمة؟</h3>
<div class="tip">
  <p class="line">الأكواد مُصنَّفة حسب المشروع والجهة. إذا لم يظهر كود معيّن:</p>
  <p class="line">• تأكد أن المشروع المختار يشمل هذا الكود.</p>
  <p class="line">• تأكد أن الجهة المالكة مخوّلة لهذا الكود.</p>
  <p class="line">• ابحث عن الكود بخانة البحث <span dir="ltr">Ctrl+F</span>، فقد يكون في مجموعة أخرى.</p>
</div>

<h3>ظهر خطأ «تبعية ناقصة» — ماذا أفعل؟</h3>
<div class="ok">
  اضغط زر <strong>«إصلاح تلقائي»</strong> في لوحة المعاينة.
  النظام يُضيف الأكواد المطلوبة تلقائياً. هذا ليس خطأً — بعض الأكواد
  تتطلب بنوداً أخرى أن تكون موجودة قبلها (مثلاً: الحفر يحتاج مسحاً مسبقاً).
</div>

<h3>زر «بناء العرض» غير مُفعَّل</h3>
<div class="tip">
  <p class="line">يتطلب التفعيل:</p>
  <p class="line">• تحديد كود واحد على الأقل.</p>
  <p class="line">• عدم وجود أخطاء تحقق. زر الإصلاح التلقائي يحل أغلبها.</p>
</div>

<h3>ملف Word الناتج يحتوي نصوصاً عامة بدل المحتوى الحقيقي</h3>
<div class="warn">
  <p class="line">⚠️ هذا يعني أن ملف Word الخاص بهذا الكود غير موجود في مكتبة المحتوى.</p>
  <p class="line">الحل: أضف الملف إلى مجلد <strong><span dir="ltr">templates/source_documents/</span></strong>.</p>
  <p class="line">اسم الملف المطلوب: <strong><span dir="ltr">{CODE_ID}.docx</span></strong>، مثال: <span dir="ltr">001-SUR-BASE.docx</span>.</p>
  <p class="line">راجع دليل المستخدم <span dir="ltr">docs/USER_GUIDE_AR.md</span> للتفاصيل.</p>
</div>

<h3>التطبيق يعمل على جهاز لكن الواجهة تبدو قديمة على جهاز آخر</h3>
<div class="warn">
  <p class="line">⚠️ <strong>المشكلة الأكثر شيوعاً:</strong> نسخ مجلد <span dir="ltr">dist\\ATPAS\\</span> القديم بدون إعادة البناء أولاً.</p>
  <p class="line"><strong>الحل الصحيح:</strong></p>
  <p class="line">1. عند أي تغيير في الكود أو البيانات: شغّل <strong><span dir="ltr">build_exe.bat</span></strong> أولاً.</p>
  <p class="line">2. انتظر حتى ينتهي البناء.</p>
  <p class="line">3. انسخ مجلد <strong><span dir="ltr">dist\\ATPAS\\</span></strong> بالكامل للجهاز الآخر.</p>
  <p class="line">4. راجع تاريخ البناء أعلى الشاشة للتأكد من الإصدار.</p>
</div>

<h3>الملف الناتج لا يفتح في Word</h3>
<div class="tip">
  <p class="line">• تأكد من وجود Microsoft Word 2016 أو أحدث.</p>
  <p class="line">• الملف في مجلد <span dir="ltr">output/generated_documents/</span> بجوار <span dir="ltr">ATPAS.exe</span>.</p>
  <p class="line">• اضغط «فتح المجلد» في نافذة البناء للوصول المباشر.</p>
</div>

<h3>النظام بطيء أو يتجمّد أثناء البناء</h3>
<div class="ok">
  هذا طبيعي لمشاريع كبيرة (20+ كوداً بصور مدمجة). الشريط يتحرك خلف الكواليس —
  انتظر حتى تظهر رسالة «✅ العرض الفني جاهز».
</div>

<h2>للمساعدة الإضافية</h2>
<div class="ok">
  <p class="line">راجع ملف الدليل الكامل: <strong><span dir="ltr">docs/USER_GUIDE_AR.md</span></strong></p>
  <p class="line">أو راجع وثائق SSOT في: <strong><span dir="ltr">SSOT/ATPAS_REFERENCE_DOCUMENT_v4.1.md</span></strong></p>
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
        title = QLabel("المساعدة — نظام بناء العروض الفنية")
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title.setStyleSheet(f"""
            font-size: 16px; font-weight: 800; color: {theme.HEADER};
            padding: 4px 0; border-bottom: 2px solid {theme.ACCENT};
        """)
        layout.addWidget(title)

        # ── تبويبات ────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setLayoutDirection(Qt.RightToLeft)
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(f"""
            QTabBar::tab {{
                font-size: 12px; padding: 8px 18px;
                font-weight: 700; min-width: 128px;
                text-align: center;
            }}
            QTabBar::tab:selected {{
                background: {theme.HEADER}; color: {theme.ACCENT};
                border-bottom: 3px solid {theme.ACCENT};
            }}
            QTabBar::tab:!selected {{
                background: #F0F0F0; color: #444;
            }}
            QTabWidget::pane {{ border: 1px solid #DDD; }}
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
        welcome_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.NAVY_MID}; color: {theme.ACCENT};
                border: none; border-radius: 5px;
                padding: 6px 16px; font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {theme.HEADER}; }}
        """)
        welcome_btn.clicked.connect(self._reshow_welcome)

        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.HEADER}; color: white;
                border: none; border-radius: 5px;
                padding: 6px 24px; font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {theme.NAVY_MID}; }}
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
        browser = QTextBrowser()
        browser.setLayoutDirection(Qt.RightToLeft)
        browser.setReadOnly(True)
        browser.document().setDefaultStyleSheet(
            "body, p, div, h2, h3, td, th { direction: rtl; text-align: right; }"
        )
        # إجبار RTL على مستوى المستند (يتجاوز قيود Qt على ul/li)
        opt = browser.document().defaultTextOption()
        opt.setTextDirection(Qt.RightToLeft)
        opt.setAlignment(Qt.AlignRight)
        opt.setWrapMode(QTextOption.WordWrap)
        browser.document().setDefaultTextOption(opt)
        browser.setHtml(html)
        browser.setOpenExternalLinks(False)
        browser.setStyleSheet(
            f"QTextBrowser {{ border: none; background: white; padding: 6px; "
            f"color: {theme.TEXT}; }}"
        )
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
