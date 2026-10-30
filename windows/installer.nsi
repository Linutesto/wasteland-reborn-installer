; Wasteland Reborn — Windows installer. Built by windows/build.sh (makensis under Wine).
; EDITION=hd passes /DHD_EDITION: its own product name, install folder and registry keys,
; so it installs beside the classic edition.
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
!ifndef UNINSTALL_MANIFEST
  !error "build.sh passes /DUNINSTALL_MANIFEST=<generated .nsh>"
!endif
!ifdef HD_EDITION
  !define PRODUCT "Wasteland Reborn HD"
  !define PRODUCT_KEY "WastelandRebornHD"
!else
  !define PRODUCT "Wasteland Reborn"
  !define PRODUCT_KEY "WastelandReborn"
!endif

Name "${PRODUCT}"
OutFile "${OUTFILE}"
InstallDir "$LOCALAPPDATA\${PRODUCT_KEY}"
InstallDirRegKey HKCU "Software\${PRODUCT_KEY}" "InstallDir"
BrandingText "Fallout 2 Restoration Project + AI NPCs"

!define MUI_ICON "${STAGE}\setup\wasteland.ico"
!define MUI_UNICON "${STAGE}\setup\wasteland.ico"
!define MUI_WELCOMEPAGE_TITLE "${PRODUCT}"
!define MUI_WELCOMEPAGE_TEXT "$(WelcomeText)"
!define MUI_FINISHPAGE_TEXT "$(FinishText)"

; The language picked in the first dialog is remembered for the uninstaller.
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY "Software\${PRODUCT_KEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Language"
!define MUI_LANGDLL_WINDOWTITLE "${PRODUCT}"
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
!ifdef HD_EDITION
LangString WelcomeText ${LANG_ENGLISH} "Wasteland Reborn HD installs beside the classic edition, keeping separate settings and saves.$\r$\n$\r$\nYou need your own Fallout 2 (Epic, Steam or GOG). Setup finds its files, offers downloadable HD graphics packs and can install the separate Wasteland HD Android app."
LangString WelcomeText ${LANG_FRENCH} "Wasteland Reborn HD s'installe a cote de l'edition classique, avec ses propres reglages et sauvegardes.$\r$\n$\r$\nIl faut votre propre Fallout 2 (Epic, Steam ou GOG). La configuration retrouve le jeu, propose les packs HD et peut installer l'application Android Wasteland HD."
LangString FinishText ${LANG_ENGLISH} "Installed. To play on the phone: Start menu > Wasteland Reborn HD > Wasteland - Install on phone. On the PC: the Wasteland Reborn HD desktop icon."
LangString FinishText ${LANG_FRENCH} "Installe. Pour jouer sur le telephone : menu Demarrer > Wasteland Reborn HD > Wasteland - Installer sur le telephone. Sur le PC : l'icone Wasteland Reborn HD du bureau."
!else
LangString WelcomeText ${LANG_ENGLISH} "Fallout 2 with the Restoration Project (RPU), made for Android phones, with NPCs you can talk to through AI (optional, with Ollama).$\r$\n$\r$\nYou need your own copy of Fallout 2 (Epic, Steam or GOG) installed on this PC: the setup finds it and takes its files.$\r$\n$\r$\nAt the end a setup window opens: game, AI, then your Android phone."
LangString WelcomeText ${LANG_FRENCH} "Fallout 2 avec le Restoration Project (RPU), fait pour les telephones Android, avec des PNJ qui parlent avec une IA (optionnelle, avec Ollama).$\r$\n$\r$\nIl faut ta propre copie de Fallout 2 (Epic, Steam ou GOG) installee sur ce PC : l'installation la retrouve et prend ses fichiers.$\r$\n$\r$\nA la fin, une fenetre de configuration s'ouvre : jeu, IA, puis telephone Android."
LangString FinishText ${LANG_ENGLISH} "Installed. To play on the phone: Start menu > Wasteland - Install on phone. On the PC: the Wasteland Reborn desktop icon."
LangString FinishText ${LANG_FRENCH} "C'est installe. Pour jouer sur le telephone : menu Demarrer > Wasteland - Installer sur le telephone. Sur le PC : l'icone Wasteland Reborn du bureau."
!endif
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

Section "${PRODUCT}"
  SetOutPath "$INSTDIR"
  File /r "${STAGE}\*.*"
  WriteRegStr HKCU "Software\${PRODUCT_KEY}" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Desinstaller.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_KEY}" "DisplayName" "${PRODUCT}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_KEY}" "UninstallString" '"$INSTDIR\Desinstaller.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_KEY}" "DisplayIcon" "$INSTDIR\setup\wasteland.ico"

  CreateShortCut "$DESKTOP\${PRODUCT}.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\setup\launcher.py"' "$INSTDIR\setup\wasteland.ico"
  RMDir /r "$SMPROGRAMS\${PRODUCT}"  ; shortcuts of an install in the other language
  CreateDirectory "$SMPROGRAMS\${PRODUCT}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\setup\launcher.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\${PRODUCT}\$(LnkSetup).lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\setup.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\${PRODUCT}\$(LnkPhone).lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\phone.py"' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\${PRODUCT}\$(LnkServer).lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\setup\launcher.py" --server' "$INSTDIR\setup\wasteland.ico"
  CreateShortCut "$SMPROGRAMS\${PRODUCT}\$(LnkUninstall).lnk" "$INSTDIR\Desinstaller.exe"

  ; NSIS /S must never block on a console prompt. The unattended path still
  ; finds and copies the player's Fallout 2, and logs optional failures.
  IfSilent silent_setup interactive_setup
silent_setup:
  ExecWait '"$INSTDIR\python\python.exe" "$INSTDIR\setup\setup.py" --unattended --lang=$(LangCode)'
  Goto setup_done
interactive_setup:
  ExecWait '"$INSTDIR\python\python.exe" "$INSTDIR\setup\setup.py" --lang=$(LangCode)'
setup_done:
SectionEnd

; Saves (game\data\savegame) and AI memories (userdata) are kept.
Section "Uninstall"
  Delete "$DESKTOP\${PRODUCT}.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT}"
  RMDir /r "$INSTDIR\platform-tools"
  !include "${UNINSTALL_MANIFEST}"
  ; Base game files and downloaded music were copied from the owner's game.
  Delete "$INSTDIR\game\master.dat"
  Delete "$INSTDIR\game\critter.dat"
  RMDir /r "$INSTDIR\game\data\sound\music"
  RMDir "$INSTDIR\game\data\sound"
  RMDir "$INSTDIR\game\data\savegame"
  RMDir "$INSTDIR\game\data"
  RMDir "$INSTDIR\game"
  Delete "$INSTDIR\Desinstaller.exe"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_KEY}"
  DeleteRegKey HKCU "Software\${PRODUCT_KEY}"
  RMDir "$INSTDIR"
SectionEnd
