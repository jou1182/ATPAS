; ═══════════════════════════════════════════════════════════════════════════
; ATPAS — Inno Setup Installer Script
; نظام بناء العروض الفنية — الرواف للهندسة والتقنية
;
; كيفية الاستخدام:
;   1. ابنِ EXE أولاً:  pyinstaller ATPAS.spec
;   2. افتح هذا الملف في Inno Setup Compiler
;   3. اضغط Build → Compile  (أو F9)
;   4. النتيجة في مجلد:  installer_output\ATPAS-Setup-x.x.x.exe
; ═══════════════════════════════════════════════════════════════════════════

#define MyAppName        "ATPAS"
#define MyAppNameAr      "نظام بناء العروض الفنية"
; ⚠ حافظ على مزامنة هذا الرقم مع version.json (المصدر الوحيد للإصدار)
#define MyAppVersion     "3.1"
#define MyAppPublisher   "الرواف للهندسة والتقنية"
#define MyAppPublisherEn "Al-Rawaf Engineering"
#define MyAppURL         "https://github.com/jou1182/ATPAS"
#define MyAppSupportMail "jou1182@gmail.com"
#define MyAppExeName     "ATPAS.exe"
#define MySourceDir      "dist\ATPAS"

; ── إعدادات التثبيت ──────────────────────────────────────────────────────
[Setup]
AppId={{8F3A2B1C-D4E5-4F6A-B7C8-9D0E1F2A3B4C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=mailto:{#MyAppSupportMail}
AppUpdatesURL={#MyAppURL}
AppComments={#MyAppNameAr}

; مسار التثبيت الافتراضي
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; إعدادات الإخراج
OutputDir=installer_output
OutputBaseFilename=ATPAS-Setup-{#MyAppVersion}

; الضغط — lzma2 أفضل نسبة للملفات الكبيرة
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; الأيقونة والمظهر
SetupIconFile=assets\atpas.ico
WizardStyle=modern
WizardResizable=no
WizardSizePercent=120

; صلاحيات التثبيت (admin مطلوب لـ Program Files)
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; معلومات إضافية تظهر في "إضافة/إزالة البرامج"
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} — {#MyAppPublisher}

; منع تشغيل أكثر من نسخة من المثبّت
AppMutex=ATPAS_Setup_Mutex

; لا نريد نافذة إعادة التشغيل
RestartIfNeededByRun=no

; ── اللغة ────────────────────────────────────────────────────────────────
[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"; \
    LanguageName: "العربية"; LanguageID: $0401

; ── المهام الاختيارية (عرضها للمستخدم) ──────────────────────────────────
[Tasks]
Name: "desktopicon"; \
    Description: "إنشاء اختصار على سطح المكتب"; \
    GroupDescription: "اختصارات إضافية:"; \
    Flags: unchecked

Name: "quicklaunchicon"; \
    Description: "إنشاء اختصار في شريط المهام السريعة"; \
    GroupDescription: "اختصارات إضافية:"; \
    Flags: unchecked

; ── الملفات المُثبَّتة ───────────────────────────────────────────────────
; ملاحظة: جميع ملفات البيانات (JSON/assets/fonts) مُحزَّمة داخل _internal\
;          بواسطة PyInstaller — لا حاجة لنسخها منفردةً.
[Files]
; الملف التنفيذي الرئيسي
Source: "{#MySourceDir}\{#MyAppExeName}"; \
    DestDir: "{app}"; \
    Flags: ignoreversion

; جميع الملفات الداخلية (DLLs، مكتبات Python، assets، JSON)
Source: "{#MySourceDir}\_internal\*"; \
    DestDir: "{app}\_internal"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ── الاختصارات ────────────────────────────────────────────────────────────
[Icons]
; قائمة ابدأ
Name: "{group}\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"; \
    Comment: "{#MyAppNameAr} — {#MyAppPublisher}"; \
    WorkingDir: "{app}"

Name: "{group}\إلغاء تثبيت {#MyAppName}"; \
    Filename: "{uninstallexe}"; \
    Comment: "إزالة {#MyAppName} من الجهاز"

; سطح المكتب (اختياري)
Name: "{autodesktop}\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"; \
    Comment: "{#MyAppNameAr} — {#MyAppPublisher}"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon

; شريط المهام السريعة (اختياري)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"; \
    Tasks: quicklaunchicon

; ── التشغيل بعد التثبيت ──────────────────────────────────────────────────
[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "تشغيل {#MyAppName} الآن"; \
    Flags: nowait postinstall skipifsilent; \
    WorkingDir: "{app}"

; ── الحذف عند إلغاء التثبيت ──────────────────────────────────────────────
[UninstallDelete]
; احذف مجلد _internal بالكامل
Type: filesandordirs; Name: "{app}\_internal"

; احذف الملفات المُنشأة أثناء التشغيل (logs etc.) — اختياري
; Type: filesandordirs; Name: "{userappdata}\ATPAS"

; ── كود Pascal: فحوصات مسبقة ─────────────────────────────────────────────
[Code]
// تحقق أن Windows 10 أو أحدث
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  if Version.Major < 10 then
  begin
    MsgBox(
      'يتطلب {#MyAppName} نظام Windows 10 أو أحدث.' + #13#10 +
      'الإصدار الحالي غير مدعوم.',
      mbError, MB_OK
    );
    Result := False;
  end
  else
    Result := True;
end;

// عرض رسالة ترحيبية بالعربية
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'سيتم تثبيت [name/ver] على جهازك.' + #13#10#13#10 +
    'يُنصح بإغلاق جميع التطبيقات الأخرى قبل المتابعة.' + #13#10#13#10 +
    'للدعم الفني: {#MyAppSupportMail}';
end;
