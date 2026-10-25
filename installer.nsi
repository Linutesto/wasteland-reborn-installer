; Wasteland Reborn — Windows installer. Built by windows/build.sh (makensis under Wine).
Unicode true
SetCompressor /SOLID lzma
SetCompressorDictSize 64
RequestExecutionLevel user

!include "MUI2.nsh"

!ifndef STAGE
  !error "build.sh passes /DSTAGE=<payload dir>"
!endif
!ifndef OUTFILE
  !define OUTFILE "WastelandReborn-Setup.exe"
!endif

Name "Wasteland Reborn"
OutFile "${OUTFILE}"
InstallDir "$LOCALAPPDATA\WastelandReborn"
InstallDirRegKey HKCU "Software\WastelandReborn" "InstallDir"
BrandingText "Fallout 2 Restoration Project + PNJ avec IA"

!define MUI_ICON "${STAGE}\setup\wasteland.ico"
!define MUI_UNICON "${STAGE}\setup\wasteland.ico"
!define MUI_WELCOMEPAGE_TITLE "Wasteland Reborn"
!define MUI_WELCOMEPAGE_TEXT "Fallout 2 avec le Restoration Project (RPU) et des PNJ qui parlent avec une IA (optionnelle, avec Ollama).$\r$\n$\r$\nIl faut ta propre copie de Fallout 2 (Epic, Steam ou GOG) installee sur ce PC : l'installation la retrouve et prend ses fichiers.$\r$\n$\r$\nA la fin, une fenetre de configuration s'ouvre : jeu, IA, puis telephone Android si tu veux."
!define MUI_FINISHPAGE_TEXT "C'est installe. Lance le jeu avec l'icone Wasteland Reborn sur le bureau."

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "French"

Section "Wasteland Reborn"
  SetOutPath "$INSTDIR"
  File /r "${STAGE}\*.*"
  WriteRegStr HKCU "Software\WastelandReborn" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Desinstaller.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WastelandReborn" "DisplayName" "Wasteland Reborn"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WastelandReborn" "UninstallString" '"$INSTDIR\Desinstaller.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WastelandReborn" "DisplayIcon" "$INSTDIR\setup\wasteland.ico"

  CreateShortCut "$DESKTOP\Wasteland Reborn.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\setup\launcher.py"' "$INSTDIR\setup\wasteland.ico"
  CreateDirectory "$SMPROGRAMS\Wasteland Reborn"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\Wasteland Reborn.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\setup\launcher.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\Wasteland - Configurer.lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\setup.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\Wasteland - Installer sur le telephone.lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\phone.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\Wasteland - Serveur IA (telephone).lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\launcher.py" --server' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\Desinstaller.lnk" "$INSTDIR\Desinstaller.exe"

  ExecWait '"$INSTDIR\python\python.exe" "$INSTDIR\setup\setup.py"'
SectionEnd

; Saves (game\data\savegame) and AI memories (userdata) are kept.
Section "Uninstall"
  Delete "$DESKTOP\Wasteland Reborn.lnk"
  RMDir /r "$SMPROGRAMS\Wasteland Reborn"
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\brain"
  RMDir /r "$INSTDIR\setup"
  RMDir /r "$INSTDIR\phone"
  RMDir /r "$INSTDIR\platform-tools"
  RMDir /r "$INSTDIR\game\mods"
  RMDir /r "$INSTDIR\game\appearance"
  RMDir /r "$INSTDIR\game\data\sound"
  Delete "$INSTDIR\game\*.dat"
  Delete "$INSTDIR\game\*.exe"
  Delete "$INSTDIR\Desinstaller.exe"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WastelandReborn"
  DeleteRegKey HKCU "Software\WastelandReborn"
SectionEnd
