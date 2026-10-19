; =====================================================================
; Inno Setup Script for Project Zomboid Server Manager
; Compatible with Inno Setup 6.0+
; =====================================================================

#define MyAppName "Project Zomboid Server Manager"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "PZ Server Manager Team"
#define MyAppURL "https://github.com/nmazarov/pz-server-manager"
#define MyAppExeName "PZ Server Manager.exe"

[Setup]
AppId={{D37E88A1-8E24-4B29-876B-914F23D69801}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
DefaultGroupName={#MyAppName}
SourceDir=..
LicenseFile=LICENSE
OutputDir=installer_output
OutputBaseFilename=PZ_Server_Manager_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Source standalone exe from PyInstaller dist folder
Source: "dist\PZ Server Manager.exe"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Default server directory in ProgramData
Name: "{commonappdata}\PZServer"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Automatically configure Windows Defender Firewall for Project Zomboid server ports
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""Project Zomboid Server (UDP)"" dir=in action=allow protocol=UDP localport=16261,16262,8766,8767"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""Project Zomboid Server (TCP)"" dir=in action=allow protocol=TCP localport=16261,27015"; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""Project Zomboid Server (UDP)"""; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""Project Zomboid Server (TCP)"""; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""Project Zomboid Web Dashboard (TCP)"""; Flags: runhidden

[Code]
// Verify 64-bit Java installation on Windows
function InitializeSetup(): Boolean;
var
  JavaVer: String;
  HasJava: Boolean;
begin
  Result := True;
  HasJava := RegQueryStringValue(HKLM, 'SOFTWARE\JavaSoft\Java Runtime Environment', 'CurrentVersion', JavaVer) or
             RegQueryStringValue(HKLM, 'SOFTWARE\JavaSoft\JDK', 'CurrentVersion', JavaVer) or
             RegQueryStringValue(HKLM, 'SOFTWARE\Eclipse Adoptium\JRE', 'CurrentVersion', JavaVer) or
             RegQueryStringValue(HKLM, 'SOFTWARE\OpenJDK\JDK', 'CurrentVersion', JavaVer);

  if not HasJava then
  begin
    if MsgBox('Программа Project Zomboid Dedicated Server требует 64-битную Java (JRE/JDK).' + #13#10 + #13#10 +
              'Java не была автоматически обнаружена на вашем компьютере.' + #13#10 +
              'Продолжить установку приложения?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;
