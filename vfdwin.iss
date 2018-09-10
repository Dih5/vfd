; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{E0C12F71-198F-454B-9843-20278ED5EFFF}
AppName=VFD
AppVersion=0.3.2
AppPublisher=Dih5
AppPublisherURL=https://github.com/Dih5/vfd
AppSupportURL=https://github.com/Dih5/vfd
AppUpdatesURL=https://github.com/Dih5/vfd
DefaultDirName={pf}\VFD
DisableProgramGroupPage=yes
LicenseFile=.\LICENSE
InfoBeforeFile=.\vfdwin.txt
OutputBaseFilename=vfdsetup
Compression=lzma
SolidCompression=yes
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: ".\dist\vfdwin\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{commonprograms}\VFD"; Filename: "{app}\vfdgui.exe"
Name: "{commondesktop}\VFD"; Filename: "{app}\vfdgui.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\vfdgui.exe"; Description: "{cm:LaunchProgram,VFD}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCR; Subkey: ".vfd"; ValueData: "VFD"; Flags: uninsdeletevalue; ValueType: string; ValueName: ""
Root: HKCR; Subkey: "VFD"; ValueData: "Vernacular Figure Description"; Flags: uninsdeletekey; ValueType: string; ValueName: ""
Root: HKCR; Subkey: "VFD\DefaultIcon"; ValueData: "{app}\vfdgui.exe,0"; ValueType: string; ValueName: ""
Root: HKCR; Subkey: "VFD\shell\open\command"; ValueData: """{app}\vfdgui.exe"" ""%1"""; ValueType: string; ValueName: ""
