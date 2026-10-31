# Wasteland Reborn

**Fallout 2 on your Android phone** — classic **Wasteland** and the **HD**
edition — on the open-source **Fallout 2 Community Edition** engine (mobile
fork), with the **Restoration Project (RPU)** + FO2Tweaks, a full touch UI,
and **NPCs you can talk to freely through a local AI** (optional, via Ollama).

*[Version française ci-dessous](#wasteland-reborn--en-français)*

## ⬇️ Download

| What | Link | Size |
| --- | --- | --- |
| 📱 Classic app | [Wasteland-arm64.apk](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-arm64.apk) | ≈ 4 MB |
| 📱 HD app | [Wasteland-HD-arm64.apk](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-HD-arm64.apk) | ≈ 4 MB |
| 💻 Windows installer (classic or HD) | [WastelandReborn-Setup.exe](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest) · [WastelandRebornHD-Setup.exe](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest) | ≈ 830 MB each |
| Checksums | [SHA256SUMS.txt](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/SHA256SUMS.txt) | |

Updating an installed app? Install the new APK over it — your saves stay.
The two apps (`Wasteland` and `Wasteland HD`) are separate packages: they
install side by side, each with its own files and saves.

## 📖 Install guides

Longer, step-by-step guides — one action per step, every button and menu
quoted exactly as the program shows it (including the French ones):

| Guide | What it covers |
| --- | --- |
| [Windows — English](docs/INSTALL-WINDOWS.md) | before you start, download + checksum, every installer page, the phone, HD art, AI NPCs, updating, backup, troubleshooting table |
| [Windows — en français](docs/INSTALL-WINDOWS.fr.md) | même guide, en français (tutoiement) |
| [Troubleshooting — English](docs/TROUBLESHOOTING.md) · [en français](docs/TROUBLESHOOTING.fr.md) | SmartScreen, antivirus, "game not found", phone not found/pairing/unauthorized, black screen, blank dialogue, no AI reply, HD download, space, Epic files |
| [Linux — English](docs/INSTALL-LINUX.md) | the Linux path |

The quick version also ships inside the installer as `README.txt` /
`LISEZ-MOI.txt`.

## You need your own Fallout 2

**No game files are included in anything you download here.** Fallout 2 is
not ours to give away: you need **your own copy** (Epic, Steam or GOG), and
you copy its files yourself. Everything else — engine, Restoration Project,
touch UI, HD art — is in these releases.

- An Android phone with a **64-bit (arm64)** processor, or Windows 10/11.
- About 2 GB free on the phone for the game's files.
- Optional: [Ollama](https://ollama.com) for the AI NPCs.

---

## Install path A — phone only

1. **Get the APK** on the phone (open this README on the phone and tap the
   link above): `Wasteland-arm64.apk` for the classic look, or
   `Wasteland-HD-arm64.apk` for the HD edition.
2. **Install it.** Android asks for permission to install apps from this
   source (Chrome, Files, …) → allow it once. The app is unsigned by Google
   Play, that is expected.
3. **Put your Fallout 2 files on the phone.** On the computer where the game
   is installed, find its folder:

   | Store | Where the game lives | How to open the folder |
   | --- | --- | --- |
   | Steam | `…\steamapps\common\Fallout 2` (often `C:\Program Files (x86)\Steam\steamapps\common\Fallout 2`) | Library → right-click **Fallout 2** → **Manage → Browse local files** |
   | GOG | `C:\GOG Games\Fallout 2` (or `…\GOG Galaxy\Games\Fallout 2`) | GOG Galaxy → **Fallout 2** → ⚙ / Options → **Manage installation → Show folder** |
   | Epic | `C:\Program Files\Epic Games\Fallout 2` | Library → **…** on Fallout 2 → **Manage** → folder icon |

   What matters: the folder that contains **`master.dat`** and
   **`critter.dat`** (plus its `data\` folder — music and mods). Copy **the
   whole folder** to the phone, any way you like:

   - **USB cable**: connect the phone, choose *File transfer*, drag the folder
     into the phone's `Downloads`.
   - **Cloud drive or messenger**: zip the folder first (`.zip`, `.7z`,
     `.rar` all work) and put the archive in the phone's `Downloads`.

4. **Import them in the app.** First launch shows **Files of the game** →
   **Choose the folder** (the one you dragged over) or **Choose an archive**
   (the `.zip` you sent). The app finds `master.dat` + `critter.dat` at any
   depth, tells you what it found, and copies it in (mods and saves come
   along). Keep the screen on for the few minutes it takes.
5. **HD edition only — the HD art.** The HD app checks for art packs each
   time it starts and **offers the download** (name, size, **Download** /
   **Later**); you can also open **Files of the game → Check for HD art**.
   It needs an internet connection; **Later** starts the game right away, and
   an interrupted download resumes.
6. **Play.** The game itself needs no connection afterwards.

No computer? The game folder can also come from another phone, a SD card or
any file manager — step 4 is the same.

## Install path B — PC + phone

1. **Run `WastelandReborn-Setup.exe`** (classic) or
   `WastelandRebornHD-Setup.exe` (HD) and pick your language. Windows shows
   *"Windows protected your PC"* (the file is not signed) → **More info** →
   **Run anyway**.
2. **Follow the setup.** It finds your Fallout 2 (Epic, Steam, GOG or a folder
   you point it at) and copies the files. The HD installer additionally offers
   the HD art packs once your game is found.
3. **At the end a window opens**: your game, the AI (if Ollama is installed),
   then the phone. Turn on **wireless debugging** on the phone (Developer
   options), same Wi-Fi as the PC, and pick the phone in the menu — or skip
   and do it later from **Start menu › Wasteland › Install on phone**. adb
   (Google's official Android tool) is downloaded automatically.
4. **Play** on the phone (the **Wasteland** app), or on the PC with the
   desktop icon (classic mouse controls).

In dialogues, pick **[Speak freely]** and type whatever you want to the
character. **AI on the phone** runs on the PC: **Start menu › Wasteland ›
AI server (phone)** must be open; the menu's *Everywhere* option installs
[Tailscale](https://tailscale.com) (free private VPN) on both — log in with
the **same account** on each. Without the server the game plays normally,
offline.

The HD installer installs beside the classic one
(`%LOCALAPPDATA%\WastelandRebornHD`), with its own settings and saves.

## Linux PC and Android from Linux

See the step-by-step [Linux guide](docs/INSTALL-LINUX.md) for Ubuntu, Fedora, Arch and Steam Deck, including optional AI and phone transfer.

## Install path C — build from source

Everything is rebuilt from this repository on Linux x86_64. No Fallout 2 file
is downloaded or included: players add their own at install time.

```sh
git clone --recursive https://github.com/Linutesto/wasteland-reborn-installer
cd wasteland-reborn-installer
./bootstrap.sh                  # toolchains, RPU profile, classic APK (accept the Android SDK licenses)
./bootstrap.sh --edition hd     # HD APK (apk/Wasteland-HD-arm64.apk)
windows/build.sh                # windows/dist/WastelandReborn-Setup.exe
EDITION=hd windows/build.sh     # windows/dist/WastelandRebornHD-Setup.exe
```

Host packages: `git cmake ninja rsync unzip curl tar xz python3`, ImageMagick,
SDL2 and zlib development files, and `makensis` or Wine.
`./bootstrap.sh --no-android` skips the Android SDK; then pass an APK:
`APK=path/to.apk windows/build.sh`.
Tests: `python3 -m unittest discover -s windows/tests -v` (offline, 7 tests)
and `bash windows/tests/test_wine_install.sh` (needs Wine and your own game
files in `gamedata/`; it skips without them). Releasing: see
[RELEASING.md](RELEASING.md).

| Part | Where | What |
| --- | --- | --- |
| Engine | `src/imbaner_fallout2-ce-mobile` (submodule, branch `wasteland-reborn-hd`) | fallout2-ce mobile fork + touch UI, AI free talk, Windows build, HD rendering and art updater |
| HD packs | `bootstrap.sh` → `src/wasteland-hd-tools` (pinned) | the pack downloader the HD installer ships; the HD images live in [wasteland-hd-assets](https://github.com/Linutesto/wasteland-hd-assets) |
| AI brain | `brain/` | Python HTTP server between the game and Ollama / an OpenAI-compatible server (`python3 -m unittest discover -s brain/tests`) |
| Game profile | `profile/` + `tools/mkprofile.py` | RPU + FO2Tweaks from their GitHub releases (pinned sha256), the game config and overlay → `build/profile` |
| Windows installer | `windows/` | NSIS installer for both editions, setup scripts (game detection, Ollama, phone over adb, Tailscale, HD art) |
| Release tooling | `tools/release.sh`, `RELEASING.md`, `.github/workflows/` | the v1.2 asset layout and the chunked-upload workflow |

Your APK is signed with your own Android debug key, so it can't update the
released app (Android refuses a different signature): back up your saves,
uninstall the released app, then install yours.

## The HD art

The HD edition re-draws the game's pictures at 2× (256-color originals →
RGBA). It ships as separate packs the app downloads by itself, so a phone
only pulls what exists today and tops up later:

| Pack | What it covers | State |
| --- | --- | --- |
| `world` | floors, walls, scenery, items and misc in the game world (also carries interface and inventory art the engine does not display yet) | available |
| `heads` | talking heads: the dialogue portraits in HD (app 1.3 or later) | available |
| `critters-01`, `critters-02`, … | people, monsters and animals — split into parts, released as each part finishes | in production |

Installed packs are recorded per profile; already-installed packs are never
offered again, and a changed pack is offered as an update. The classic app
ignores HD art entirely.

## Credits

- [Fallout 2 CE](https://github.com/alexbatalov/fallout2-ce) and the
  [mobile fork](https://github.com/imbaner/fallout2-ce-mobile)
- [Restoration Project (RPU)](https://github.com/BGforgeNet/Fallout2_Restoration_Project)
  and [FO2Tweaks](https://github.com/BGforgeNet/FO2tweaks) by BGforgeNet
- Python (embeddable), NSIS, Ollama

Fallout is a trademark of Bethesda Softworks. Unofficial fan project: we
include **no game files** — bring your own Fallout 2.

---

# Wasteland Reborn — en français

**Fallout 2 sur ton téléphone Android** — l'édition **classique** et l'édition
**HD** — sur le moteur open source **Fallout 2 Community Edition** (fork
mobile), avec le **Restoration Project (RPU)** + FO2Tweaks, une interface
tactile complète et des **PNJ qui répondent en texte libre grâce à une IA
locale** (optionnelle, via Ollama).

## ⬇️ Télécharger

| Ce qu'il y a | Lien | Taille |
| --- | --- | --- |
| 📱 App classique | [Wasteland-arm64.apk](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-arm64.apk) | ≈ 4 Mo |
| 📱 App HD | [Wasteland-HD-arm64.apk](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-HD-arm64.apk) | ≈ 4 Mo |
| 💻 Installateur Windows (classique ou HD) | [WastelandReborn-Setup.exe](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest) · [WastelandRebornHD-Setup.exe](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest) | ≈ 830 Mo chacun |
| Sommes de contrôle | [SHA256SUMS.txt](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/SHA256SUMS.txt) | |

Mise à jour d'une app déjà installée ? Installez l'APK par-dessus : tes
sauvegardes restent. Les deux apps (`Wasteland` et `Wasteland HD`) sont des
paquets distincts : elles coexistent, chacune avec ses fichiers et ses
sauvegardes.

## 📖 Guides d'installation

Des guides pas à pas — une action par étape, chaque bouton et chaque menu
recopié exactement comme le programme l'affiche :

| Guide | Ce qu'il couvre |
| --- | --- |
| [Windows — en français](docs/INSTALL-WINDOWS.fr.md) | avant de commencer, téléchargement + somme de contrôle, chaque page de l'installation, le téléphone, l'art HD, les PNJ avec IA, mise à jour, sauvegardes, tableau de dépannage |
| [Windows — English](docs/INSTALL-WINDOWS.md) | same guide, in English |
| [Dépannage — en français](docs/TROUBLESHOOTING.fr.md) · [English](docs/TROUBLESHOOTING.md) | SmartScreen, antivirus, « jeu introuvable », téléphone introuvable/association/unauthorized, écran noir, texte vide, pas de réponse de l'IA, téléchargement HD, place, fichiers Epic |
| [Linux — English](docs/INSTALL-LINUX.md) | le chemin Linux |

La version courte est aussi dans l'installateur, dans `LISEZ-MOI.txt` /
`README.txt`.

## Il te faut TA propre copie de Fallout 2

**Aucun fichier du jeu n'est inclus dans ce que tu télécharges ici.** Fallout 2
n'est pas à nous à donner : il faut **ta propre copie** (Epic, Steam ou GOG)
et tu copies ses fichiers toi-même. Tout le reste — moteur, Restoration
Project, interface tactile, art HD — est dans ces releases.

- Un téléphone Android **64 bits (arm64)**, ou Windows 10/11.
- Environ 2 Go libres sur le téléphone pour les fichiers du jeu.
- Optionnel : [Ollama](https://ollama.com) pour les PNJ avec IA.

---

## PC Linux et Android depuis Linux

Suis le [guide Linux en français](docs/INSTALL-LINUX.fr.md) pour Ubuntu, Fedora, Arch et Steam Deck, avec IA et transfert vers le téléphone en option.

## Chemin A — seulement le téléphone

1. **Récupère l'APK** sur le téléphone (ouvre ce README sur le téléphone et
   touche le lien ci-dessus) : `Wasteland-arm64.apk` pour l'aspect classique,
   ou `Wasteland-HD-arm64.apk` pour l'édition HD.
2. **Installe-le.** Android demande la permission d'installer des apps
   sources inconnues (Chrome, Fichiers, …) → autorise une fois. L'app n'est
   pas signée par Google Play, c'est normal.
3. **Mets les fichiers de Fallout 2 sur le téléphone.** Sur l'ordinateur où le
   jeu est installé, trouve son dossier :

   | Magasin | Où est le jeu | Comment ouvrir le dossier |
   | --- | --- | --- |
   | Steam | `…\steamapps\common\Fallout 2` (souvent `C:\Program Files (x86)\Steam\steamapps\common\Fallout 2`) | Bibliothèque → clic droit sur **Fallout 2** → **Gérer → Ouvrir le dossier du jeu** |
   | GOG | `C:\GOG Games\Fallout 2` (ou `…\GOG Galaxy\Games\Fallout 2`) | GOG Galaxy → **Fallout 2** → ⚙ → **Gérer l'installation → Afficher le dossier** |
   | Epic | `C:\Program Files\Epic Games\Fallout 2` | Bibliothèque → **…** sur Fallout 2 → **Gérer** → icône dossier |

   L'important : le dossier qui contient **`master.dat`** et
   **`critter.dat`** (avec son dossier `data\` — musique et mods). Copie
   **tout le dossier** sur le téléphone, comme tu veux :

   - **Câble USB** : branche le téléphone, choisis *Transfert de fichiers*,
     glisse le dossier dans `Téléchargements` du téléphone.
   - **Cloud ou messagerie** : compresse d'abord le dossier (`.zip`, `.7z`,
     `.rar` marchent) et mets l'archive dans `Téléchargements`.

4. **Importe-les dans l'app.** Au premier lancement, l'écran **Fichiers du
   jeu** → **Choisir le dossier** (celui que tu viens de glisser) ou
   **Choisir une archive** (le `.zip` envoyé). L'app trouve `master.dat` et
   `critter.dat` à n'importe quelle profondeur, te montre ce qu'elle a trouvé
   et copie tout (mods et sauvegardes compris). Laisse l'écran allumé les
   quelques minutes que ça prend.
5. **Édition HD seulement — l'art HD.** L'app HD cherche les packs d'art à
   chaque démarrage et **propose le téléchargement** (nom, taille,
   **Télécharger** / **Plus tard**) ; tu peux aussi ouvrir **Fichiers du jeu →
   Vérifier l'art HD**. Il faut une connexion ; **Plus tard** lance le jeu
   tout de suite, et un téléchargement interrompu reprend où il en était.
6. **Joue.** Ensuite le jeu n'a plus besoin de connexion.

Pas d'ordinateur sous la main ? Le dossier du jeu peut aussi venir d'un autre
téléphone, d'une carte SD ou d'un gestionnaire de fichiers — l'étape 4 est la
même.

## Chemin B — PC + téléphone

1. **Lance `WastelandReborn-Setup.exe`** (classique) ou
   `WastelandRebornHD-Setup.exe` (HD) et choisis la langue. Windows affiche
   « Windows a protégé votre ordinateur » (fichier non signé) → **Informations
   complémentaires** → **Exécuter quand même**.
2. **Suis l'installation.** Elle retrouve ton Fallout 2 (Epic, Steam, GOG ou
   un dossier que tu lui indiques) et prend ses fichiers. L'installateur HD
   propose en plus les packs d'art HD une fois le jeu trouvé.
3. **À la fin, une fenêtre s'ouvre** : ton jeu, l'IA (si Ollama est installé),
   puis le téléphone. Active le **débogage sans fil** sur le téléphone
   (Options pour les développeurs), même Wi-Fi que le PC, et choisis le
   téléphone dans le menu — ou passe et fais-le plus tard via **Menu Démarrer
   › Wasteland › Installer sur le téléphone**. adb (l'outil Android officiel
   de Google) est téléchargé tout seul.
4. **Joue** sur le téléphone (l'app **Wasteland**) ou sur le PC avec l'icône
   du bureau (souris classique).

En dialogue, choisis **[Speak freely]** et écris ce que tu veux au personnage.
**L'IA sur le téléphone** passe par le PC : **Menu Démarrer › Wasteland ›
Serveur IA (téléphone)** doit être ouvert ; l'option « Partout » installe
[Tailscale](https://tailscale.com) (VPN privé gratuit) sur les deux —
connecte-toi avec **le même compte** sur chacun. Sans serveur, le jeu marche
normalement, hors ligne.

L'installateur HD s'installe à côté de l'édition classique
(`%LOCALAPPDATA%\WastelandRebornHD`), avec ses propres réglages et
sauvegardes.

## Chemin C — construire depuis les sources

Tout se reconstruit depuis ce dépôt sous Linux x86_64. Aucun fichier de
Fallout 2 n'est téléchargé ni inclus : les joueurs ajoutent le leur au moment
de l'installation.

```sh
git clone --recursive https://github.com/Linutesto/wasteland-reborn-installer
cd wasteland-reborn-installer
./bootstrap.sh                  # outils, profil RPU, APK classique (accepte les licences du SDK Android)
./bootstrap.sh --edition hd     # APK HD (apk/Wasteland-HD-arm64.apk)
windows/build.sh                # windows/dist/WastelandReborn-Setup.exe
EDITION=hd windows/build.sh     # windows/dist/WastelandRebornHD-Setup.exe
```

Paquets requis, tests, publication : voir la section anglaise « Build from
source » plus haut et [RELEASING.md](RELEASING.md).

## L'art HD

L'édition HD redessine les images du jeu en 2× (originales 256 couleurs →
RGBA). Il est livré en packs séparés que l'app télécharge toute seule, pour
qu'un téléphone ne prenne que ce qui existe et complète plus tard :

| Pack | Ce qu'il couvre | État |
| --- | --- | --- |
| `world` | planchers, murs, décors, objets et divers sur la carte (contient aussi de l'art d'interface que le moteur n'affiche pas encore) | disponible |
| `heads` | têtes parlantes : les portraits de dialogue en HD (app 1.3 ou plus récente) | disponible |
| `critters-01`, `critters-02`, … | gens, monstres et animaux — découpés en parts, publiés au fur et à mesure | en production |

Les packs installés sont enregistrés par profil ; un pack déjà installé n'est
plus proposé, et un pack modifié est proposé comme mise à jour. L'app
classique ignore totalement l'art HD.

## Crédits

- [Fallout 2 CE](https://github.com/alexbatalov/fallout2-ce) et le
  [fork mobile](https://github.com/imbaner/fallout2-ce-mobile)
- [Restoration Project (RPU)](https://github.com/BGforgeNet/Fallout2_Restoration_Project)
  et [FO2Tweaks](https://github.com/BGforgeNet/FO2tweaks) — BGforgeNet
- Python (embeddable), NSIS, Ollama

Fallout est une marque de Bethesda Softworks. Projet de fans, non officiel :
**aucun fichier de jeu n'est inclus** — apporte ta propre copie de Fallout 2.
