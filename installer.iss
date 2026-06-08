[Setup]
AppName=AI BOS
AppVersion=1.0.0
DefaultDirName={autopf}\AIBOS
DisableProgramGroupPage=yes
OutputBaseFilename=AIBOS_Setup
Compression=lzma2/ultra
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\AI_BOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\AI BOS"; Filename: "{app}\AI_BOS.exe"

[Run]
Filename: "{app}\AI_BOS.exe"; Description: "Launch AI BOS"; Flags: nowait postinstall skipifsilent