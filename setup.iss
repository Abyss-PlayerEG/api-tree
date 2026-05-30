; ─── API Tree - Inno Setup Installer Script ───
; Build: iscc setup.iss  (requires Inno Setup 6+)
; Install Inno Setup: winget install --id JRSoftware.InnoSetup

#define MyAppName "API Tree"
#define MyAppVersion "26.5.30"
#define MyAppPublisher "API Tree"
#define MyAppExeName "api-tree.exe"
#define MyAppCmdName "api-tree"

[Setup]
AppId={{B8F4A3D2-7E61-4C9F-A1B5-6D2E8F0C3A91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output
OutputDir=dist
OutputBaseFilename={#MyAppCmdName}-setup-v{#MyAppVersion}
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; UI
WizardStyle=modern
; Permissions - requires admin (installs for all users to Program Files)
PrivilegesRequired=admin
; Environment - notify system about PATH changes
ChangesEnvironment=yes
; 64-bit support
ArchitecturesInstallIn64BitMode=x64compatible
; Misc
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addtopath"; Description: "Add to &PATH (use api-tree from any terminal)"; GroupDescription: "Environment:"; Flags: checkedonce

[Files]
Source: "dist\{#MyAppCmdName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; Add install directory to system PATH
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
; Add install folder to Windows Defender exclusions (prevents false positives)
Filename: "powershell.exe"; Parameters: "-NoProfile -Command Add-MpPreference -ExclusionPath '{app}'"; Flags: runhidden waituntilterminated; StatusMsg: "Adding to Windows Defender exclusions..."
; Show a brief usage hint after install
Filename: "cmd.exe"; Parameters: "/k echo {#MyAppName} v{#MyAppVersion} & ""{app}\{#MyAppExeName}"" -h"; Flags: nowait postinstall skipifsilent; Description: "Show usage"

[Code]
// ─── PATH manipulation (system-wide) ───

function NeedsAddPath(Path: string): Boolean;
var
  CurrentPath: string;
begin
  Result := True;
  if not RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', CurrentPath) then
    Exit;
  // Check if path is already in PATH (case-insensitive)
  if Pos(';' + Uppercase(Path) + ';', ';' + Uppercase(CurrentPath) + ';') > 0 then
    Result := False;
end;

// Clean up PATH on uninstall (system-wide)
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Paths: string;
  InstPath: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    InstPath := ExpandConstant('{app}');
    if RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', Paths) then
    begin
      // Remove the install directory from PATH
      StringChange(Paths, InstPath + ';', '');
      StringChange(Paths, ';' + InstPath, '');
      if CompareText(Paths, InstPath) = 0 then
        Paths := '';
      // Clean up any double semicolons
      StringChange(Paths, ';;', ';');
      // Trim trailing/leading semicolons
      if (Length(Paths) > 0) and (Paths[Length(Paths)] = ';') then
        Delete(Paths, Length(Paths), 1);
      if (Length(Paths) > 0) and (Paths[1] = ';') then
        Delete(Paths, 1, 1);
      RegWriteStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', Paths);
    end;
  end;
end;
