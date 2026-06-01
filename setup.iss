

 ; ─── API Tree - Inno Setup Installer Script ───
; Build: iscc setup.iss  (requires Inno Setup 6+)
; Install Inno Setup: winget install --id JRSoftware.InnoSetup

#define MyAppName "API Tree"
#ifndef MyAppVersion
#define MyAppVersion "99.99.99"
#endif
#ifndef MyAppNumericVersion
#define MyAppNumericVersion MyAppVersion
#endif
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
OutputBaseFilename={#MyAppCmdName}-setup-{#MyAppVersion}-win64
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
VersionInfoVersion={#MyAppNumericVersion}
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
; Broadcast environment change to all windows (CMD/PowerShell pick up new PATH)
Filename: "powershell.exe"; Parameters: "-NoProfile -Command $null = [Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('PATH', 'User'), 'Process'); Add-Type -Name WinAPI -Namespace Win32 -MemberDefinition '[DllImport(\""user32.dll\"")] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);'; $HWND_BROADCAST = [IntPtr]0xffff; $WM_SETTINGCHANGE = 0x001A; $SMTO_ABORTIFHUNG = 0x0002; $null = [Win32.WinAPI]::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [UIntPtr]::Zero, 'Environment', $SMTO_ABORTIFHUNG, 5000, [ref][UIntPtr]::Zero)"; Flags: runhidden waituntilterminated
; Show usage hint: reload PATH from registry so api-tree is available immediately
Filename: "powershell.exe"; Parameters: "-NoProfile -NoExit -Command $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User'); Clear-Host; Write-Host '{#MyAppName} Version: {#MyAppVersion}'; Write-Host ''; api-tree -h"; Flags: nowait postinstall skipifsilent; Description: "Show usage"

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
  ResultCode: Integer;
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
      
      // Broadcast environment change so open terminals pick up the cleaned PATH
      Exec('powershell.exe', '-NoProfile -Command ' +
        '$HWND_BROADCAST=[IntPtr]0xffff;$WM_SETTINGCHANGE=0x001A;' +
        'Add-Type -Name WinAPI -Namespace Win32 -MemberDefinition ''[DllImport("user32.dll")]' +
        'public static extern IntPtr SendMessageTimeout(IntPtr hWnd,uint Msg,' +
        'UIntPtr wParam,string lParam,uint fuFlags,uint uTimeout,out UIntPtr lpdwResult);'';' +
        '$null=[Win32.WinAPI]::SendMessageTimeout($HWND_BROADCAST,$WM_SETTINGCHANGE,' +
        '[UIntPtr]::Zero,''Environment'',0x0002,5000,[ref][UIntPtr]::Zero)',
        '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
