# Wasteland Reborn — troubleshooting (Windows + phone)

Something not working? Find your symptom below; every fix is a numbered
list of one-action steps.

- The full install guide: [INSTALL-WINDOWS.md](INSTALL-WINDOWS.md)
- French: [TROUBLESHOOTING.fr.md](TROUBLESHOOTING.fr.md)

---

## Windows SmartScreen blocks the installer

**What you see:** *"Windows protected your PC"* when you run
`WastelandReborn-Setup.exe` (or `WastelandRebornHD-Setup.exe`).

1. In that blue dialog, click **More info**.
   - *You should see:* a publisher line ("Unknown publisher") and a new
     button.
2. Click **Run anyway**.
   - French Windows: *« Windows a protégé votre ordinateur »* →
     **« Plus d'informations »** → **« Exécuter quand même »**.
   - *You should see:* the setup's language window, *"Language / Langue"*.
3. No "Run anyway" button (a company/parental policy)? Save the file,
   right-click it → **Properties** → at the bottom tick **Unblock** →
   **OK**, then run it again.

**Why:** the installer is not signed with a paid certificate. That is
expected; the checksum in the guide (step 2.4) is how you know the file is
clean.

## Antivirus quarantines the installer or the app

**What you see:** the `.exe` disappears right after downloading, Windows
says *"Threat removed"*, or the black configuration window never opens.

1. Open **Windows Security** (shield icon) → **Virus & threat protection**
   → **Protection history** (*« Historique de la protection »*).
   - *You should see:* an entry for `WastelandReborn-Setup.exe` (or
     `adb.exe`, `python.exe`, `Desinstaller.exe`).
2. Select it → **Actions** → **Allow on device** (*« Autoriser sur
   l'appareil »*), then download/run the file again.
3. Stop it repeating: **Virus & threat protection settings** →
   **Exclusions** → **Add or remove exclusions** → add
   `%LOCALAPPDATA%\WastelandReborn` (and `WastelandRebornHD`) and your
   `Downloads` folder.
4. Third-party antivirus (Avast, Kaspersky, …): same idea — open its
   quarantine, restore the file, add an exception for the install folder.

**Why:** unsigned installers and `adb.exe` (Google's Android tool) trip
heuristic "unwanted app" rules. Only do this for the file you downloaded
from the official release page.

## The setup cannot find Fallout 2

**What you see,** in the black configuration window:

> I couldn't find Fallout 2 automatically.

or, after picking a folder:

> No master.dat + critter.dat in there. Try again?

1. Open your game folder from the store and check it contains
   **`master.dat`** and **`critter.dat`**:

   | Store | How to open the folder |
   | --- | --- |
   | Steam | Library → right-click **Fallout 2** → **Manage → Browse local files** |
   | GOG | GOG Galaxy → **Fallout 2** → ⚙ → **Manage installation → Show folder** |
   | Epic | Library → **…** on Fallout 2 → **Manage** → folder icon |

   - Not there, or the folder is empty? The game is not fully downloaded —
     see [the game is not downloaded or not verified](#the-game-is-not-downloaded-or-not-verified).
2. Back in the black window, press **Enter** at *"Press Enter to choose
   the folder..."*.
   - *You should see:* a folder picker titled *"Choose the Fallout 2
     folder (the one with master.dat)"*.
3. Select the folder from step 1 (not its parent, not the `data` subfolder)
   → **Select Folder**.
4. *You should see:* `Found: <folder>` and `Use this folder? (Y/n)` →
   press **Enter**, then the copy lines (`master.dat (… MB)...`).
5. It still says no? The setup searches Epic, Steam and GOG installs
   automatically (C: through Z:, including extra Steam libraries). An
   external drive that is unplugged, or a folder name you moved, is not
   found — that is what the manual picker is for.
6. You cancelled the whole thing earlier? Everything is redoable:
   Start menu → **Wasteland - Setup** (FR **Wasteland - Configurer**).

## The phone is not found or pairing fails

**What you see:** the menu lists no phone, or `No phone connected. Try
again?`, or pairing says it failed.

Go through this list in order — it is one of these, almost always:

1. **Same Wi-Fi on both.** The PC must be on Wi-Fi too, not only the
   phone. Guest networks often isolate devices: use the main network.
2. **Wireless debugging is ON** on the phone: *Settings → System →
   Developer options → Wireless debugging*.
   - Not there yet? *Settings → About phone →* tap **Build number** 7
     times first (Samsung: *About phone → Software information*; Xiaomi:
     *About phone → MIUI version*).
3. **The phone is unlocked** (the screen may be on — some phones stop
   advertising while locked).
4. Run Start menu → **Wasteland - Install on phone** and pick
   **Pair another phone (wireless debugging)** (FR *« Associer un autre
   telephone (debogage sans fil) »*).
5. On the phone, tap the words **Wireless debugging** (not the switch) →
   **Pair device with pairing code**. Keep that screen open.
   - *You should see:* a 6-digit code and an *"IP address & port"* line.
6. In the black window press **Enter** when the code is shown.
   - If asked, type the **6-digit code** → Enter.
   - Still nothing: the console asks for **"IP address and port"** —
     type the *"IP address & port"* line from the phone **exactly**,
     including the colon. ⚠️ It is **not** the same port as the pairing
     code screen.
   - `Phone found: <address>:<port>` should appear, then your phone in the
     menu.
7. `No phone connected. Try again? (Y/n)` → press **Enter** (yes) and
   repeat 5–6 once; mDNS sometimes needs a second pass.
8. **Windows Firewall prompt:** the first phone install may ask to allow
   adb on private networks → **Allow**. Missing it is a classic reason the
   phone never shows up.
9. **Give up on Wi-Fi → use a USB cable:** plug the phone in, turn on
   **USB debugging** (*« Débogage USB »*), accept **Allow USB debugging?**
   on the phone, then run the menu again — the phone appears without any
   pairing.
10. `Couldn't install adb (no Internet?)` → the PC could not download
    Google's platform-tools (~7 MB). Check the connection and run the
    menu again.

## The phone shows unauthorized

**What you see:** the setup refuses the install, or your phone simply
never appears in the menu.

The menu only lists phones that already trust this PC — an untrusted
phone is invisible, not listed as an error.

1. Keep the phone plugged in (USB) or on wireless debugging, and watch
   its screen for a popup: **"Allow USB debugging?"** with a fingerprint.
2. Tick **Always allow from this computer** → **Allow**
   (*« Toujours autoriser depuis cet ordinateur »* → *« Autoriser »*).
   - No popup? In *Developer options*, tap **Revoke USB debugging
     authorizations**, then re-enable **Wireless debugging** (or replug
     the cable) — the popup comes back.
3. Run Start menu → **Wasteland - Install on phone** again: the phone
   should now be listed; pick its number.

## Black screen

**What you see:** the app or the PC game starts, then stays black.

1. **Wait ~10 seconds.** The first start unpacks engine files and, on the
   HD edition, may still be finishing an art install.
2. Close it fully and start it again: on the phone, swipe it away from
   Recent apps and reopen **Wasteland**; on the PC, close and
   double-click the desktop icon again.
3. **Phone, HD edition:** if it went black right after an HD download,
   the art install was cut short — launch once more (it resumes) or tap
   **Later** (*« Plus tard »*) to skip the art for now.
4. **Files missing** is the usual real cause: an interrupted copy.
   - On the PC: Start menu → **Wasteland - Setup** → answer **Yes** to
     *"The game files are already installed. Copy them again? (Y/n)"*.
   - On the phone: re-run Start menu → **Wasteland - Install on phone**
     (it only re-copies what is missing), or in the game's settings open
     **Game files** and choose the folder again.
5. Still black? Note your phone model + Android version (or Windows
   version) and open an issue on the
   [release repository](https://github.com/Linutesto/wasteland-reborn-installer/issues)
   with that information — it is a bug we cannot fix blind.

## Blank dialogue text

**What you see:** dialogue opens but the lines are empty, or whole
sentences are missing.

1. This almost always means the **game files were copied incompletely**
   (a copy that was interrupted, or a folder that was not the complete
   game).
2. On the PC: Start menu → **Wasteland - Setup** → **Yes** at *"The game
   files are already installed. Copy them again? (Y/n)"*.
   - *You should see:* the copy lines again, ending with
     `music: N files copied`.
3. On the phone: re-run **Wasteland - Install on phone**, or in the
   game's settings → **Game files** → **Replace game** and pick the full
   folder from your computer (saves and settings are kept).
4. Check the copy really contains the whole folder: `master.dat`,
   `critter.dat`, `data\`, and the translation files that came with your
   copy (the Restoration Project profile ships its own `translations`
   folder).
5. The game's language is the language of *your* Fallout 2 files. If your
   copy is missing its language files, text goes blank — copy the folder
   again from a fresh, verified install.

## No AI reply

**What you see:** no **`[Speak freely]`** option in dialogues, or you pick
it and nothing comes back.

1. **No `[Speak freely]` line at all** → the AI is off or unreachable.
   Run Start menu → **Wasteland - Setup** and answer the AI questions
   again (model download included).
2. **On the PC,** start the game from the desktop icon (it starts Ollama
   and the local server for you). If a box says *"Ollama is not
   responding"* — open **Ollama** first (its icon sits in the system
   tray), then start the game again.
3. **On the phone,** the PC must be on with
   **Wasteland - AI server (phone)** open. The console prints
   `AI server for the phone: http://<PC address>:8822` and
   *"Keep this window open while you play on the phone."* — closing it
   stops the AI (the game keeps working, without answers).
4. At home → phone and PC on the **same Wi-Fi**. Away from home →
   Tailscale must be running **on both, logged in with the same account**
   (`PC connected to Tailscale:` / `Phone connected to Tailscale.` in the
   setup console).
5. **Firewall:** the first time, Windows asks to open the AI port —
   *"Windows will ask for permission to open the AI port (local network
   and Tailscale only)."* → accept it (the rule is called
   **"Wasteland IA"**). Missed it? Re-run **Wasteland - Install on
   phone** and answer the AI question again.
6. The answer is not instant: the first message takes a few seconds (the
   model loads) and a busy model can take up to ~45 seconds. Type
   **English** — the game's language.
7. Model vanished? Start menu → **Wasteland - Setup** re-offers the
   download.

## HD download stuck

**What you see:** the HD art offer sits there, the progress line does not
move, or the download restarts every launch.

1. First, this is **not** fatal: **Later** (*« Plus tard »*) always starts
   the game, and an interrupted download **resumes** at the next launch
   (the setup log line is *"HD update skipped (can retry next launch)"*).
2. Check the phone/PC is online and the offer's size fits your free space
   (the offer states it in MB).
3. Close the app fully and start it again: the offer reappears with
   **Download**.
4. `HD packs unavailable for now: ...` during PC setup → the pack you
   asked for is not published yet; run **Wasteland - Setup** again later.
5. PC, silent install: read `userdata\setup-install.log` in the install
   folder — it records exactly which pack failed and why.

## Out of space

**What you see:** *"Not enough free space on the phone: … more is
needed."*, or Windows complains there is not enough room.

**Phone:**

1. Free at least the amount the message asks for (the game needs ~2 GB in
   total).
2. Old saves are the easiest win: in the game's settings → **Game files**
   → **Export saves** (keep the zip), then **Delete all saves**.
3. Clear space elsewhere (downloads, photos, unused apps) and start the
   import again — nothing was kept from the failed attempt.

**PC:**

1. You need about 3 GB free (≈ 830 MB download + ≈ 1.3 GB of game files).
2. If C: is full, change the folder on the installer's
   **Choose Install Location** page (**Browse...**) to another drive.
   - Remember: your saves then live in that folder,
     `<folder>\game\data\savegame`.

## The game is not downloaded or not verified

**What you see:** the setup cannot find the game, or the folder has no
`master.dat`, or the store shows the game as installing.

**Epic:**

1. Open the Epic Games Launcher → Library.
2. Click **…** on Fallout 2 → **Manage** → the folder icon — the folder it
   opens is the one the setup wants.
3. If files are missing: **… → Manage → Verify Files** (Epic verifies and
   downloads what is missing). Wait until it finishes.
   - The setup reads Epic's own records, so an Epic install that was never
     downloaded is reported as *not found* until it exists on disk.

**Steam:**

1. Library → right-click **Fallout 2** → **Properties → Installed files →
   Verify integrity of game files**.
2. When it finishes, the folder must contain `master.dat` and
   `critter.dat`.

**GOG:**

1. GOG Galaxy → **Fallout 2** → ⚙ → **Manage installation → Verify /
   Repair**.

**Then:** Start menu → **Wasteland - Setup** → the found folder appears as
`Found: <folder>` → **Enter**.

---

## Still stuck?

Open an issue on the
[release repository](https://github.com/Linutesto/wasteland-reborn-installer/issues)
and include:

1. Which file you ran (`WastelandReborn-Setup.exe` or
   `WastelandRebornHD-Setup.exe`) and where you downloaded it.
2. Windows version (Settings → System → About) and, for phone problems,
   the phone model + Android version.
3. The **exact text** of the error — copy it from the black window, or a
   screenshot.
4. Whether the PC step, the phone step or the AI step failed.

*Wasteland Reborn is an unofficial fan project. Fallout 2's files are never
included — you bring your own copy.*
