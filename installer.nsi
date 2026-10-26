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
BrandingText "Fallout 2 Restoration Project + AI NPCs"

!define MUI_ICON "${STAGE}\setup\wasteland.ico"
!define MUI_UNICON "${STAGE}\setup\wasteland.ico"
!define MUI_WELCOMEPAGE_TITLE "Wasteland Reborn"
!define MUI_WELCOMEPAGE_TEXT "$(WelcomeText)"
!define MUI_FINISHPAGE_TEXT "$(FinishText)"

; The language picked in the first dialog is remembered for the uninstaller.
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY "Software\WastelandReborn"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Language"
!define MUI_LANGDLL_WINDOWTITLE "Wasteland Reborn"
!define MUI_LANGDLL_INFO "Language / Langue"
!define MUI_LANGDLL_ALWAYSSHOW

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"

; Passed to the configuration scripts (setup.py --lang=...), which save it.
LangString LangCode ${LANG_ENGLISH} "en"
LangString LangCode ${LANG_FRENCH} "fr"
LangString WelcomeText ${LANG_ENGLISH} "Fallout 2 with the Restoration Project (RPU), made for Android phones, with NPCs you can talk to through AI (optional, with Ollama).$\r$\n$\r$\nYou need your own copy of Fallout 2 (Epic, Steam or GOG) installed on this PC: the setup finds it and takes its files.$\r$\n$\r$\nAt the end a setup window opens: game, AI, then your Android phone."
LangString WelcomeText ${LANG_FRENCH} "Fallout 2 avec le Restoration Project (RPU), fait pour les telephones Android, avec des PNJ qui parlent avec une IA (optionnelle, avec Ollama).$\r$\n$\r$\nIl faut ta propre copie de Fallout 2 (Epic, Steam ou GOG) installee sur ce PC : l'installation la retrouve et prend ses fichiers.$\r$\n$\r$\nA la fin, une fenetre de configuration s'ouvre : jeu, IA, puis telephone Android."
LangString FinishText ${LANG_ENGLISH} "Installed. To play on the phone: Start menu > Wasteland - Install on phone. On the PC: the Wasteland Reborn desktop icon."
LangString FinishText ${LANG_FRENCH} "C'est installe. Pour jouer sur le telephone : menu Demarrer > Wasteland - Installer sur le telephone. Sur le PC : l'icone Wasteland Reborn du bureau."
LangString LnkSetup ${LANG_ENGLISH} "Wasteland - Setup"
LangString LnkSetup ${LANG_FRENCH} "Wasteland - Configurer"
LangString LnkPhone ${LANG_ENGLISH} "Wasteland - Install on phone"
LangString LnkPhone ${LANG_FRENCH} "Wasteland - Installer sur le telephone"
LangString LnkServer ${LANG_ENGLISH} "Wasteland - AI server (phone)"
LangString LnkServer ${LANG_FRENCH} "Wasteland - Serveur IA (telephone)"
LangString LnkUninstall ${LANG_ENGLISH} "Uninstall"
LangString LnkUninstall ${LANG_FRENCH} "Desinstaller"

Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
FunctionEnd

Section "Wasteland Reborn"
  SetOutPath "$INSTDIR"
  File /r "${STAGE}\*.*"
  WriteRegStr HKCU "Software\WastelandReborn" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Desinstaller.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WastelandReborn" "DisplayName" "Wasteland Reborn"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WastelandReborn" "UninstallString" '"$INSTDIR\Desinstaller.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WastelandReborn" "DisplayIcon" "$INSTDIR\setup\wasteland.ico"

  CreateShortCut "$DESKTOP\Wasteland Reborn.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\setup\launcher.py"' "$INSTDIR\setup\wasteland.ico"
  RMDir /r "$SMPROGRAMS\Wasteland Reborn"  ; shortcuts of an install in the other language
  CreateDirectory "$SMPROGRAMS\Wasteland Reborn"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\Wasteland Reborn.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\setup\launcher.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\$(LnkSetup).lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\setup.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\$(LnkPhone).lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\phone.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\$(LnkServer).lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\launcher.py" --server' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\Wasteland Reborn\$(LnkUninstall).lnk" "$INSTDIR\Desinstaller.exe"

  ExecWait '"$INSTDIR\python\python.exe" "$INSTDIR\setup\setup.py" --lang=$(LangCode)'
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
