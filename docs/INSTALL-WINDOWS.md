# Install Wasteland Reborn on Windows — step by step

This guide is for someone who is **not** a programmer. Do the sections in
order. Every step is **one action**, followed by what you should see.

- French? → [INSTALL-WINDOWS.fr.md](INSTALL-WINDOWS.fr.md) (même guide, en français)
- Something goes wrong? → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Linux? → [INSTALL-LINUX.md](INSTALL-LINUX.md)
- The quick version also ships in the installer as `README.txt` /
  `LISEZ-MOI.txt`, and in the [main README](../README.md).

**Two editions — pick one:**

| Edition | File | What it is |
| --- | --- | --- |
| Classic | `WastelandReborn-Setup.exe` | the game's original look |
| HD | `WastelandRebornHD-Setup.exe` | the same game with redrawn 2× graphics; installs **beside** the classic one, with its own settings and saves |

No game files are included in either download: you must own Fallout 2
(Epic, Steam or GOG) and the setup copies the files from your own copy.

---

## 1. Before you start

1. **Windows 10 or 11, 64-bit.** Press the Windows key → type `About your
   PC` → Enter.
   - *You should see:* "System type: 64-bit operating system". (In French
     Windows: « Type de système : système d'exploitation 64 bits ».)
2. **About 3 GB of free disk space** (the download is ≈ 830 MB, the
   installed game files are ≈ 1.3 GB). Open File Explorer → *This PC*.
   - *You should see:* your C: drive with several GB free.
3. **Your own Fallout 2, installed and complete.** Open its folder in your
   store and check what is inside:

   | Store | How to open the folder |
   | --- | --- |
   | Steam | Library → right-click **Fallout 2** → **Manage → Browse local files** |
   | GOG | GOG Galaxy → **Fallout 2** → ⚙ → **Manage installation → Show folder** |
   | Epic | Library → **…** on Fallout 2 → **Manage** → folder icon (the setup says it the same way: *"In the Epic launcher: click the ... of Fallout 2 > Manage > folder icon."*) |

   - *You should see:* a folder containing **`master.dat`** and
     **`critter.dat`**, plus a `data` folder. If those two files are not
     there, the game is not fully installed — go to
     [Troubleshooting](TROUBLESHOOTING.md#the-game-is-not-downloaded-or-not-verified).
4. **The phone (optional)** — you can skip it and add it later.
   - Android **7.0 or newer**, **64-bit (arm64)**, about **2 GB free**.
   - Almost every phone from the last few years qualifies; the installer
     checks it for you and tells you if yours does not.
5. **Ollama (optional) — this is the AI for the NPCs.** Only install it if
   you want the AI.
   - Download: <https://ollama.com> → *Download for Windows* → run it.
   - *You should see:* Ollama installs and its icon appears in the system
     tray (bottom right).
   - The setup then offers a model to download. The default, number **1**,
     is **`qwen3:4b`** (light, ~2.6 GB, recommended). The other choices are
     `qwen3:8b` (~5.2 GB, needs an 8 GB+ graphics card) and `gemma3:4b`
     (~3.3 GB).

## 2. Download

1. Open the releases page:
   <https://github.com/Linutesto/wasteland-reborn-installer/releases/latest>
2. Download **one** setup file:
   - `WastelandReborn-Setup.exe` (classic) or
   - `WastelandRebornHD-Setup.exe` (HD) — both are ≈ 830 MB.
   Also download `SHA256SUMS.txt` (a small text file with the checksums).
   - *You should see:* the file(s) in your `Downloads` folder.
3. **Windows SmartScreen** (it appears later, when you run the file):
   *"Windows protected your PC"* → click **More info** → click **Run
   anyway**.
   - French Windows: *« Windows a protégé votre ordinateur »* →
     **« Plus d'informations »** → **« Exécuter quand même »**.
   - The file is not signed by Google/Microsoft — that warning is expected.
4. *(Recommended)* **Check the download is intact.**
   1. Press **Win+R**, type `cmd`, press Enter.
      - *You should see:* a black window.
   2. Type `cd Downloads` and press Enter.
   3. Type `certutil -hashfile WastelandReborn-Setup.exe SHA256` and press
      Enter.
      - *You should see:* a long line of letters and numbers
        ("SHA256 hash of file …").
   4. Open `SHA256SUMS.txt` with Notepad and compare: the two must be
      identical (use `WastelandRebornHD-Setup.exe` in the command if that
      is the file you downloaded). Not identical → download it again.

## 3. Install on the PC

1. Double-click the setup file you downloaded.
   - If SmartScreen appears: **More info → Run anyway** (step 2.3).
   - *You should see:* a small window titled **"Wasteland Reborn"** with a
     language list and the line **"Language / Langue"**.
2. Choose **English** or **French**, click **OK**.
   - *You should see:* the welcome page, with the title **"Wasteland
     Reborn"** and this text:
     > Fallout 2 with the Restoration Project (RPU), made for Android
     > phones, with NPCs you can talk to through AI (optional, with
     > Ollama).
     >
     > You need your own copy of Fallout 2 (Epic, Steam or GOG) installed
     > on this PC: the setup finds it and takes its files.
     >
     > At the end a setup window opens: game, AI, then your Android phone.

     (French version shown by the installer:
     *« Fallout 2 avec le Restoration Project (RPU), fait pour les
     telephones Android, avec des PNJ qui parlent avec une IA (optionnelle,
     avec Ollama). … »*)
3. Click **Next >** (`Suivant >`).
   - *You should see:* the folder page, titled **"Choose Install Location"**
     (*« Choisissez le dossier d'installation »*), showing
     `C:\Users\<you>\AppData\Local\WastelandReborn`.
   - Keep that folder unless C: is nearly full; change it with
     **Browse...** (`Parcourir...`) if needed. Remember where it is: that
     is where your saves will live.
4. Click **Install** (`Installer`).
   - *You should see:* a progress bar, "Installing"
     (*« Installation des fichiers »*), while files are copied (a minute or
     two).
5. **When the copying ends, a black window opens** — this is the
   configuration. It is titled `Wasteland Reborn - Configuration` and it
   talks in the language you picked at step 2. Answer each question, one at
   a time:

   **a) "1/3  Your Fallout 2 game"** (*« 1/3  Ton jeu Fallout 2 »*)
   - If your game was found it prints `Found: <folder>` and asks
     **`Use this folder? (Y/n)`** (*`Utiliser ce dossier? (O/n)`*).
     Press **Enter** if the folder is right.
   - If it did **not** find the game you see
     *"I couldn't find Fallout 2 automatically."* → press **Enter**, pick
     the folder that contains `master.dat` (the dialog asks:
     *"Choose the Fallout 2 folder (the one with master.dat)"*), then
     **Enter** again. If it complains *"No master.dat + critter.dat in
     there. Try again?"*, pick the right folder.
   - *You should see:* the copy lines —
     `master.dat (… MB)...`, `critter.dat ...`,
     `music: N files copied` (or `music: not found (the game works
     without it)` — that one is harmless).
   - **HD edition only:** a question **"Download the available HD graphics
     packs?"** (*« Telecharger les packs graphiques HD disponibles? »*).
     Press Enter for Yes; the packs download after the game files are
     copied.

   **b) "2/3  AI NPCs (optional)"** (*« 2/3  PNJ avec IA (optionnel) »*)
   - **No Ollama installed:** you see *"Ollama is not installed: AI is
     off."* — nothing to do, the game plays normally.
   - **Ollama installed:** you see **`Ollama found. Turn on AI NPCs?
     (Y/n)`** (*`Ollama detecte. Activer les PNJ avec IA? (O/n)`*).
     Press **Enter** for Yes, then pick a model: the list starts with
     **1. Qwen 3 4B - light, ~2.6 GB, runs on almost anything
     (recommended)** — press **Enter** to accept number 1.
     - *You should see:* `Downloading qwen3:4b (this can take several
       minutes)...` ending with `AI on with qwen3:4b.`
     - Say **n** here (or have no Ollama) and nothing else changes: the AI
       simply stays off and can be turned on later with
       **Wasteland - Setup**.

   **c) "Android phone (optional)"** (*« Telephone Android (optionnel) »*)
   - You may get: `Installing adb (official Android tools from Google,
     ~7 MB)...` then `OK`. adb is Google's own tool; the installer
     downloads it by itself.
   - Then the phone menu appears (see
     [section 5](#5-install-on-the-phone-from-the-pc)). **It is fine to
     skip it now**: just press **Enter** (the default answer is *Skip*).
6. Close the black window when it says **"Done!"** (*« Fini! »*) and
   *"Press Enter to close"* — press **Enter**.
   - *You should see:* the installer's last page, reading:
     > Installed. To play on the phone: Start menu > Wasteland - Install on
     > phone. On the PC: the Wasteland Reborn desktop icon.

     (French: *« C'est installe. Pour jouer sur le telephone : menu
     Demarrer > Wasteland - Installer sur le telephone. Sur le PC :
     l'icone Wasteland Reborn du bureau. »*)
7. Click **Finish** (`Fermer`).
   - *You should see:* a desktop icon **"Wasteland Reborn"** (double-click
     it to play **on the PC**), and in the Start menu a folder **"Wasteland
     Reborn"** containing:

     | English | French |
     | --- | --- |
     | `Wasteland Reborn` (starts the game) | `Wasteland Reborn` |
     | `Wasteland - Setup` | `Wasteland - Configurer` |
     | `Wasteland - Install on phone` | `Wasteland - Installer sur le telephone` |
     | `Wasteland - AI server (phone)` | `Wasteland - Serveur IA (telephone)` |
     | `Uninstall` | `Desinstaller` |

     (The HD edition lives in its own folder, **"Wasteland Reborn HD"**.)

## 4. Prepare the phone

Do this once. You need the **same Wi-Fi** on the phone and the PC.

1. On the phone, open **Settings** → **About phone**.
2. Tap **Build number** seven times.
   - Pixel / stock Android: *About phone → Build number*.
   - Samsung: *About phone → Software information → Build number*.
   - Xiaomi: *About phone → MIUI version* (seven taps).
   - *You should see:* "You are now a developer!" (« Vous êtes maintenant
     un développeur ! »).
3. Go back to **Settings → System → Developer options** and turn it **ON**
   if it is not.
   - Samsung: *Settings → Developer options*. Xiaomi: *Settings →
     Additional settings → Developer options*.
4. Turn **ON** **Wireless debugging** (French Android: **« Débogage sans
   fil »**). Keep the phone unlocked and on the same Wi-Fi as the PC.
5. Tap the words **Wireless debugging** themselves (not the switch) →
   **Pair device with pairing code** (« Appairer un appareil avec un code
   d'appairage »).
   - *You should see:* a **6-digit code**, and an **"IP address & port"**
     line (« Adresse IP et port »). Leave this screen open.
   - The 6-digit code and the "IP address & port" line use **different
     ports** — the setup asks for one, then possibly the other.
6. **USB alternative (no Wi-Fi needed):** plug the phone in with a cable,
   turn **ON** **USB debugging** (« Débogage USB ») and accept
   **Allow USB debugging?** → **Allow** (« Autoriser »?) — the popup
   carries a fingerprint of this PC.

## 5. Install on the phone from the PC

1. Start menu → **Wasteland - Install on phone**
   (*« Wasteland - Installer sur le telephone »*).
   - *You should see:* a black window whose heading reads
     **"Android phone (optional)"** (*« Telephone Android (optionnel) »*).
   - If adb was not installed yet, it is downloaded first:
     `Installing adb (official Android tools from Google, ~7 MB)...` →
     `OK`.
2. The menu asks **"Install Wasteland on which phone?"**
   (*« Installer Wasteland sur quel telephone? »*) and lists what it
   found:

   ```
   1. Pixel 7
   2. Pair another phone (wireless debugging)
   3. Skip
   Choice [3] :
   ```

   - Type the number of your phone and press **Enter**.
   - Nothing listed, or you have not paired yet? Type the **pair** number,
     press **Enter**, then follow the on-screen instructions — they repeat
     the steps of section 4 and end with:
     *"When the code is shown (or the cable plugged in), press Enter..."*
     Press Enter, type the **6-digit code** when asked, and if it still
     does not appear, type the **"IP address & port"** line exactly as the
     phone shows it.
   - Pressing **Enter** straight away = *Skip* (nothing is installed, and
     you can redo this later from the Start menu).
3. What happens next, in order:
   - `Installing "Wasteland"...` — the app goes on the phone.
   - `Copying the game (~1.3 GB over Wi-Fi: a few minutes, keep the screen
     on)...` — **keep the phone unlocked and on Wi-Fi.**
   - *You should see,* at the end:
     `Installed! "Wasteland" just opened.` /
     `You can now unplug / turn off wireless debugging.`
   - Total: **a few minutes**, mostly the copy. The app (**"Wasteland"**,
     green icon) opens by itself and the game starts.
   - The HD edition installs the **"Wasteland HD"** app instead; the two
     can coexist.
4. **If the setup refuses:** *"This phone (…) is not supported: it needs
   64-bit Android (arm64)"* → this phone cannot run the game. On some
   phones the install is refused until you turn **on** *"Install via USB"*
   in Developer options (Xiaomi and others) — see
   [Troubleshooting](TROUBLESHOOTING.md#the-phone-is-not-found-or-pairing-fails).

### The phone-only path (no PC installer)

Use this if you prefer to set the phone up alone (it is also the way to
install on a *second* phone).

1. On the phone, open the release page and download
   [`Wasteland-arm64.apk`](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-arm64.apk)
   (classic) or
   [`Wasteland-HD-arm64.apk`](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-HD-arm64.apk)
   (HD) — about 4 MB.
2. Tap the downloaded APK → Android asks permission to install apps from
   that source (Chrome, Files…) → allow it once → **Install**.
   - The app is not signed by Google Play; that is expected.
3. Put your Fallout 2 folder on the phone: copy it over a USB cable (choose
   *File transfer*), a cloud drive, or a messenger — as a folder in
   `Downloads`, or as one archive (`.zip`, `.7z`, `.rar`).
4. Open the app. The first launch shows **"Files of the game"** with two
   buttons: **Choose the folder** and **Choose an archive**.
   - *You should see:* *"Looking for the game…"*, then **"Fallout 2
     found."** with what it found and a line
     **"To copy: …, free on the phone: …"**.
5. Click **Copy**. *You should see:* **"Copying the game…"** with a
   progress line; when it ends the game starts by itself. Keep the screen
   on.
   - Note: this first-launch screen is currently **in English only**, even
     on a French phone (the HD art screen is translated).

## 6. HD art (HD edition only)

The HD packs are downloaded **by the app itself**; you never copy them by
hand.

1. **On the phone:** every time you start the HD app it checks for art
   (a few seconds, "Checking for new HD art…" / « Recherche de nouveaux
   graphismes HD… »).
   - *If something new exists you see* the title **"HD art update"**
     (*« Mise à jour des graphismes HD »*), then a line like
     **"HD art update: World art: tiles, walls, scenery…, 187.0 MB"**
     (*« Graphismes HD : … , 187.0 Mo »*) and
     **"2 pack(s) ready to download (… MB total)."**
     (*« 2 packs à télécharger (… Mo au total). »*).
2. Click **Download** (*« Télécharger »*).
   - *You should see:* a progress line **"world: 42%"**
     (*« world : 42 % »*), then **"Installing HD art: world…"**
     (*« Installation des graphismes HD : world… »*), then the game.
3. Click **Later** (*« Plus tard »*) instead and the game starts at once;
   the offer comes back at the next launch, and an interrupted download
   **resumes** where it stopped.
4. **Space:** the offer tells you the exact size in MB before you commit —
   keep that much plus a margin free (today a couple of hundred MB; packs
   grow over time).
5. **Manual check:** in the game's settings open **Game files** — the
   screen shows a **Check for HD art** button (*« Vérifier les graphismes
   HD »*) under the two import buttons.
6. **On the PC:** the HD installer offered the packs during setup. To retry
   later: Start menu → **Wasteland - Setup** and answer **Yes** to
   *"Download the available HD graphics packs?"*.

## 7. AI NPCs (optional)

The AI runs **on your PC** (via [Ollama](https://ollama.com)); the phone
only talks to it.

### On the PC

1. Install Ollama if you have not yet (<https://ollama.com>), and start it
   once so it sits in the system tray.
2. Start the game with the desktop icon **"Wasteland Reborn"** (or
   **"Wasteland Reborn HD"**).
3. **Check it works:** talk to an NPC until the dialogue options appear —
   the last one reads **`[Speak freely]`**. Pick it and type your line
   **in English** (the game's language).
   - *You should see:* the NPC's answer after a few seconds (the first
     message is slower: the model is loading).
   - **No `[Speak freely]` line?** The AI is off → Start menu →
     **Wasteland - Setup** and answer the AI questions again.

### On the phone — at home

1. On the PC, Start menu → **Wasteland - AI server (phone)**
   (*« Wasteland - Serveur IA (telephone) »*).
   - *You should see:* a console printing
     `AI server for the phone: http://<PC address>:8822` and
     *"Keep this window open while you play on the phone. Close it to
     stop."* — **leave it open.**
2. The phone must be on the **same Wi-Fi** as the PC.
3. During setup you chose **"2. Only at home (same Wi-Fi as the PC)"**
   (*« 2. Seulement a la maison »*).
4. The **first** time, Windows asks permission to open the AI port:
   *"Windows will ask for permission to open the AI port (local network
   and Tailscale only)."* → accept the UAC prompt (Yes). The rule is
   called **"Wasteland IA"**.

### Everywhere (away from home) — Tailscale

Pick **"1. Everywhere (installs and sets up Tailscale on the PC and the
phone)"** (*« 1. Partout »*) in the phone menu and the setup does this:

1. **On the PC:** it downloads and installs
   [Tailscale](https://tailscale.com) (a free private VPN) — Windows asks
   for permission → accept.
2. A **web page opens**: log in (Google, Microsoft, …). The console says
   *"Signing Tailscale in on the PC: a web page will open. Log in (Google,
   Microsoft...). Use the SAME account on the phone afterwards."*
3. **On the phone:** the Tailscale app is installed and opens by itself:
   log in with the **same account**, and accept the VPN request (that is
   Tailscale asking). The console waits — *press Enter to skip* if you
   give up.
4. *You should see:* `PC connected to Tailscale: 100.x.x.x` and
   `Phone connected to Tailscale.`
5. If it does not work, the setup says so and falls back:
   *"Tailscale not ready: the phone's AI will work at home (same Wi-Fi)."*
   — try again later with Start menu → **Wasteland - Install on phone**.

   ⚠️ At the question **`Choice [1] :`** the default is **1 = Partout /
   Everywhere**: pressing Enter straight away installs Tailscale. Type
   **2** if you only want it at home, **3** for no AI on the phone.

6. **Check it works:** open a dialogue on the phone → the last option is
   **`[Speak freely]`** → type in English → the answer arrives. If it does
   not, the server window is probably closed — see
   [Troubleshooting](TROUBLESHOOTING.md#no-ai-reply).

### Turning the AI on later

Nothing to configure by hand: Start menu → **Wasteland - Setup** (FR
**Wasteland - Configurer**) re-runs the questions, including the model
download.

## 8. Updating, saving and uninstalling

### Updating to a new release

1. **PC:** download the new `WastelandReborn-Setup.exe` (same edition) and
   run it. It opens on the folder page already pointing at your old folder
   — **keep it** (click **Next >** then **Install**).
   - Settings, saves and AI memories are kept.
   - The HD edition updates the HD install only, and vice versa.
2. **Phone (installed from the PC):** run Start menu → **Wasteland -
   Install on phone** with the new release; it re-copies what changed and
   keeps your saves.
3. **Phone (APK path):** install the new APK **over the old app** (same
   edition). Your saves stay.
   - The two apps (`Wasteland` and `Wasteland HD`) are separate: each is
     updated with its own APK.

### Backing up your saves

1. **On the PC:** open File Explorer and go to
   `%LOCALAPPDATA%\WastelandReborn\game\data\savegame`
   (type it in the address bar; the HD edition uses
   `%LOCALAPPDATA%\WastelandRebornHD\...`).
   - *You should see:* folders like `SLOT0001`, `SLOT0002`, …
2. Copy that `savegame` folder somewhere safe (USB key, cloud drive).
   - Your AI memories live next to it in
     `%LOCALAPPDATA%\WastelandReborn\userdata` — copy that too if you want
     to keep them.
3. **On the phone:** in the game's settings open **Game files** →
   **Export saves** (*« Export saves »*: "All saves in one archive") and
   pick where to save the zip.

### Uninstalling

- **PC:** Start menu → **Wasteland Reborn → Uninstall** (FR
  **Desinstaller**), or Windows *Settings → Apps → Wasteland Reborn →
  Uninstall*. It removes the program, its shortcuts and the desktop icon,
  and **keeps** `game\data\savegame` (your saves) and `userdata` (AI
  memories). Delete those two folders yourself if you want everything
  gone.
- **Phone:** uninstall the **Wasteland** app as any other app. Android
  deletes its data — **export your saves first** (step 3 above).

## 9. Troubleshooting quick table

Full explanations with numbered steps:
[TROUBLESHOOTING.md](TROUBLESHOOTING.md) (FR:
[TROUBLESHOOTING.fr.md](TROUBLESHOOTING.fr.md)).

| What you see | What to do |
| --- | --- |
| *"Windows protected your PC"* when running the setup | **More info → Run anyway** → [help](TROUBLESHOOTING.md#windows-smartscreen-blocks-the-installer) |
| The setup / APK disappears, or antivirus says "removed" | Your antivirus quarantined an unsigned file → [help](TROUBLESHOOTING.md#antivirus-quarantines-the-installer-or-the-app) |
| *"I couldn't find Fallout 2 automatically"* / *"No master.dat + critter.dat"* | Point it at the folder from section 1.3 → [help](TROUBLESHOOTING.md#the-setup-cannot-find-fallout-2) |
| The phone never appears in the menu | Same Wi-Fi, wireless debugging ON, phone unlocked → [help](TROUBLESHOOTING.md#the-phone-is-not-found-or-pairing-fails) |
| Pairing code rejected / *"No phone connected"* | Re-open **Pair device with pairing code**, use the "IP address & port" line if asked → [help](TROUBLESHOOTING.md#the-phone-is-not-found-or-pairing-fails) |
| Phone listed as **unauthorized** (or missing) | Accept **Allow USB debugging?** on the phone screen → [help](TROUBLESHOOTING.md#the-phone-shows-unauthorized) |
| Black screen when the game starts | [help](TROUBLESHOOTING.md#black-screen) |
| Dialogue text is empty/blank | Usually an incomplete game copy → [help](TROUBLESHOOTING.md#blank-dialogue-text) |
| No `[Speak freely]`, or no answer from the NPC | Ollama/server off → [help](TROUBLESHOOTING.md#no-ai-reply) |
| HD download stuck or restarting | It resumes at the next launch; check connection/space → [help](TROUBLESHOOTING.md#hd-download-stuck) |
| *"Not enough free space on the phone"* | Free space or delete saves → [help](TROUBLESHOOTING.md#out-of-space) |
| Epic: files not downloaded / not verified | Verify the game in Epic, then re-run **Wasteland - Setup** → [help](TROUBLESHOOTING.md#the-game-is-not-downloaded-or-not-verified) |

---

*Wasteland Reborn is an unofficial fan project, not affiliated with or
endorsed by Bethesda Softworks, ZeniMax or Interplay. Fallout 2's files
are never included: you bring your own copy.*
