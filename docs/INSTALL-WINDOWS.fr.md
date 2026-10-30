# Installer Wasteland Reborn sous Windows — guide pas à pas

Ce guide est pour quelqu'un qui **n'est pas** programmeur. Fais les sections
dans l'ordre. Chaque étape est **une action**, suivie de ce que tu dois
voir.

- Anglais ? → [INSTALL-WINDOWS.md](INSTALL-WINDOWS.md) (same guide, in English)
- Quelque chose foire ? → [TROUBLESHOOTING.fr.md](TROUBLESHOOTING.fr.md)
- Linux ? → [INSTALL-LINUX.md](INSTALL-LINUX.md)
- La version courte est aussi dans l'installateur (`LISEZ-MOI.txt`) et dans
  le [README principal](../README.md).

**Deux éditions — choisis une seule :**

| Édition | Fichier | C'est quoi |
| --- | --- | --- |
| Classique | `WastelandReborn-Setup.exe` | le look d'origine du jeu |
| HD | `WastelandRebornHD-Setup.exe` | le même jeu avec les images redessinées 2× ; s'installe **à côté** de l'classique, avec ses propres réglages et sauvegardes |

Aucun fichier du jeu n'est inclus dans le téléchargement : il faut **ta
propre copie** de Fallout 2 (Epic, Steam ou GOG) — l'installation prend
les fichiers de chez toi.

---

## 1. Avant de commencer

1. **Windows 10 ou 11, 64 bits.** Touche Windows → tape `Informations sur
   votre PC` → Entrée.
   - *Tu dois voir :* « Type de système : système d'exploitation 64 bits ».
2. **Environ 3 Go d'espace libre** sur le disque (le téléchargement fait
   ≈ 830 Mo, les fichiers du jeu installés ≈ 1,3 Go). Ouvre l'Explorateur
   de fichiers → *Ce PC*.
   - *Tu dois voir:* ton disque C: avec plusieurs Go libres.
3. **Ton Fallout 2, installé et au complet.** Ouvre son dossier dans ton
   magasin et regarde ce qu'il contient :

   | Magasin | Comment ouvrir le dossier |
   | --- | --- |
   | Steam | Bibliothèque → clic droit sur **Fallout 2** → **Gérer → Ouvrir le dossier du jeu** |
   | GOG | GOG Galaxy → **Fallout 2** → ⚙ → **Gérer l'installation → Afficher le dossier** |
   | Epic | Bibliothèque → **…** sur Fallout 2 → **Gérer** → icône dossier (l'installation dit la même chose : *« Dans le lanceur Epic : clic sur les ... de Fallout 2 > Gerer > icone de dossier. »*) |

   - *Tu dois voir :* un dossier qui contient **`master.dat`** et
     **`critter.dat`**, plus un dossier `data`. S'il manque ces deux
     fichiers, le jeu n'est pas complet — va dans
     [Dépannage](TROUBLESHOOTING.fr.md#le-jeu-nest-pas-téléchargé-ou-pas-vérifié).
4. **Le téléphone (optionnel)** — tu peux sauter et l'ajouter plus tard.
   - Android **7.0 ou plus récent**, **64 bits (arm64)**, environ
     **2 Go libres**.
   - Presque tous les téléphones des dernières années passent ; le
     vérifie tout seul et te le dit si le tien passe pas.
5. **Ollama (optionnel) — c'est l'IA des PNJ.** Installe-le seulement si
   tu veux l'IA.
   - Téléchargement : <https://ollama.com> → *Download for Windows* →
     lance-le.
   - *Tu dois voir :* Ollama s'installe et son icône apparaît dans la zone
     de notification (en bas à droite).
   - L'installation te propose alors un modèle à télécharger. Le par
     défaut, le numéro **1**, est **`qwen3:4b`** (léger, ~2,6 Go,
     recommandé). Les autres choix : `qwen3:8b` (~5,2 Go, carte graphique
     8 Go+) et `gemma3:4b` (~3,3 Go).

## 2. Télécharger

1. Ouvre la page des releases :
   <https://github.com/Linutesto/wasteland-reborn-installer/releases/latest>
2. Télécharge **un seul** fichier :
   - `WastelandReborn-Setup.exe` (classique) ou
   - `WastelandRebornHD-Setup.exe` (HD) — ≈ 830 Mo chacun.
   Télécharge aussi `SHA256SUMS.txt` (un petit fichier texte avec les
   sommes de contrôle).
   - *Tu dois voir :* le(s) fichier(s) dans ton dossier `Téléchargements`.
3. **Windows SmartScreen** (il apparaîtra plus tard, quand tu lances le
   fichier) : *« Windows a protégé votre ordinateur »* → clique sur
   **« Plus d'informations »** → clique sur **« Exécuter quand même »**.
   - Le fichier n'est pas signé par Google/Microsoft : cet avertissement
     est normal.
4. *(Recommandé)* **Vérifie que le téléchargement est bon.**
   1. Appuie sur **Win+R**, tape `cmd`, Entrée.
      - *Tu dois voir :* une fenêtre noire.
   2. Tape `cd Downloads` puis Entrée (ou `cd Téléchargements`).
   3. Tape `certutil -hashfile WastelandReborn-Setup.exe SHA256` puis
      Entrée.
      - *Tu dois voir :* une longue ligne de lettres et de chiffres
        (« SHA256 hash of file … »).
   4. Ouvre `SHA256SUMS.txt` avec le Bloc-notes et compare : les deux
      doivent être **identiques** (utilise
      `WastelandRebornHD-Setup.exe` dans la commande si c'est celui que tu
      as téléchargé). Pas identique → retélécharge.

## 3. Installer sur le PC

1. Double-clique sur le fichier d'installation téléchargé.
   - Si SmartScreen apparaît : **« Plus d'informations » → « Exécuter
     quand même »** (étape 2.3).
   - *Tu dois voir :* une petite fenêtre intitulée **« Wasteland Reborn »**
     avec une liste de langues et la ligne **"Language / Langue"**.
2. Choisis **English** ou **French**, clique sur **OK**.
   - *Tu dois voir :* la page de bienvenue, avec le titre
     **« Wasteland Reborn »** et ce texte :

     > Fallout 2 avec le Restoration Project (RPU), fait pour les
     > telephones Android, avec des PNJ qui parlent avec une IA
     > (optionnelle, avec Ollama).
     >
     > Il faut ta propre copie de Fallout 2 (Epic, Steam ou GOG) installee
     > sur ce PC : l'installation la retrouve et prend ses fichiers.
     >
     > A la fin, une fenetre de configuration s'ouvre : jeu, IA, puis
     > telephone Android.

     (Version anglaise du même écran : *« Fallout 2 with the Restoration
     Project (RPU), made for Android phones, with NPCs you can talk to
     through AI (optional, with Ollama). … »*)
3. Clique sur **Suivant >** (`&Suivant >`).
   - *Tu dois voir :* la page des dossiers, intitulée
     **« Choisissez le dossier d'installation »**, qui montre
     `C:\Users\<toi>\AppData\Local\WastelandReborn`.
   - Garde ce dossier, sauf si C: est presque plein ; change-le avec
     **Parcourir...** si besoin. **Note où il est : c'est là que vivent
     tes sauvegardes.**
4. Clique sur **Installer** (`&Installer`).
   - *Tu dois voir :* une barre de progression,
     « Installation des fichiers », pendant la copie (une minute ou deux).
5. **Quand la copie finit, une fenêtre noire s'ouvre** — c'est la
   configuration, intitulée `Wasteland Reborn - Configuration`. Elle parle
   la langue choisie à l'étape 2. Réponds à chaque question, une à la
   fois :

   **a) « 1/3  Ton jeu Fallout 2 »**
   - Si ton jeu a été trouvé, elle affiche `Trouve : <dossier>` puis
     demande **`Utiliser ce dossier? (O/n)`**. Appuie sur **Entrée** si
     le dossier est bon.
   - Si elle ne l'a **pas** trouvé : *« Je n'ai pas trouve Fallout 2
     automatiquement. »* → appuie sur **Entrée**, choisis le dossier qui
     contient `master.dat` (la fenêtre demande : *« Choisis le dossier de
     Fallout 2 (celui avec master.dat) »*), puis **Entrée**. Si elle
     répond *« Pas de master.dat + critter.dat la-dedans. Reessayer?
     (O/n) »*, recommence avec le bon dossier.
   - *Tu dois voir :* les lignes de copie —
     `master.dat (… Mo)...`, `critter.dat ...`,
     `musique : N fichiers copies` (ou `musique : introuvable (le jeu
     marche sans)` : sans danger).
   - **Édition HD seulement :** une question
     **« Telecharger les packs graphiques HD disponibles? »**. Entrée
     pour oui ; les packs se téléchargent après la copie du jeu.

   **b) « 2/3  PNJ avec IA (optionnel) »**
   - **Ollama pas installé :** tu lis *« Ollama n'est pas installe : IA
     desactivee. »* — rien à faire, le jeu marche normalement.
   - **Ollama installé :** la question
     **`Ollama detecte. Activer les PNJ avec IA? (O/n)`**. Appuie sur
     **Entrée** pour oui, puis choisis un modèle : la liste commence par
     **1. Qwen 3 4B  - leger, ~2,6 Go, va sur presque tout (recommande)**
     — **Entrée** accepte le 1.
     - *Tu dois voir :* `Telechargement de qwen3:4b (ca peut prendre
       plusieurs minutes)...` qui finit par `IA activee avec qwen3:4b.`
     - Tu réponds **non** (ou pas d'Ollama) : rien d'autre change, l'IA
       reste simplement fermée et s'active plus tard avec
       **Wasteland - Configurer**.

   **c) « Telephone Android (optionnel) »**
   - Possible : `Installation d'adb (outils Android officiels de Google,
     ~7 Mo)...` puis `OK`. adb, c'est l'outil Android officiel de Google ;
     l'installation le télécharge toute seule.
   - Ensuite le menu du téléphone apparaît (voir
     [section 5](#5-installer-sur-le-telephone-depuis-le-pc)).
     **Tu peux sauter maintenant** : appuie juste sur **Entrée** (la
     réponse par défaut est *Passer*).
6. Ferme la fenêtre noire quand elle affiche **« Fini! »** et
   *« Appuie sur Entree pour fermer »* — appuie sur **Entrée**.
   - *Tu dois voir :* la dernière page de l'installation :

     > C'est installe. Pour jouer sur le telephone : menu Demarrer >
     > Wasteland - Installer sur le telephone. Sur le PC : l'icone
     > Wasteland Reborn du bureau.

     (Version anglaise : *« Installed. To play on the phone: Start menu >
     Wasteland - Install on phone. On the PC: the Wasteland Reborn
     desktop icon. »*)
7. Clique sur **Fermer** (`&Fermer`).
   - *Tu dois voir :* une icône sur le bureau **« Wasteland Reborn »**
     (double-clique pour jouer **sur le PC**), et dans le menu Démarrer un
     dossier **« Wasteland Reborn »** qui contient :

     | Français | Anglais |
     | --- | --- |
     | `Wasteland Reborn` (lance le jeu) | `Wasteland Reborn` |
     | `Wasteland - Configurer` | `Wasteland - Setup` |
     | `Wasteland - Installer sur le telephone` | `Wasteland - Install on phone` |
     | `Wasteland - Serveur IA (telephone)` | `Wasteland - AI server (phone)` |
     | `Desinstaller` | `Uninstall` |

     (L'édition HD vit dans son propre dossier, **« Wasteland Reborn
     HD »**.)

## 4. Préparer le téléphone

À faire une seule fois. Il faut le **même Wi-Fi** sur le téléphone et sur
le PC.

1. Sur le téléphone, ouvre **Paramètres** → **À propos du téléphone**.
2. Touche 7 fois sur **« Numéro de build »**.
   - Pixel / Android stock : *À propos du téléphone → Numéro de build*.
   - Samsung : *À propos du téléphone → Informations sur le logiciel →
     Numéro de build*.
   - Xiaomi : *À propos du téléphone → Version MIUI* (7 touches).
   - *Tu dois voir :* « Vous êtes maintenant un développeur ! ».
3. Reviens à **Paramètres → Système → Options pour les développeurs** et
   **active**-les si elles ne le sont pas.
   - Samsung : *Paramètres → Options pour les développeurs*.
     Xiaomi : *Paramètres supplémentaires → Options pour les développeurs*.
4. **Active** **« Débogage sans fil »** (Wireless debugging). Garde le
   téléphone déverrouillé, sur le même Wi-Fi que le PC.
5. Touche les mots **« Débogage sans fil »** eux-mêmes (pas
   l'interrupteur) → **« Appairer un appareil avec un code d'appairage »**
   (en anglais : *Pair device with pairing code*).
   - *Tu dois voir :* un **code à 6 chiffres** et une ligne
     **« Adresse IP et port »**. Laisse cet écran ouvert.
   - Le code à 6 chiffres et la ligne « Adresse IP et port » n'utilisent
     **pas le même port** — l'installation te demande l'un, puis parfois
     l'autre.
6. **Variante USB (sans Wi-Fi) :** branche le téléphone par câble, **active**
   le **« Débogage USB »** (USB debugging) et accepte la demande
   **« Autoriser le débogage USB ? »** → **Autoriser** — la fenêtre
   montre une empreinte de ce PC.

## 5. Installer sur le telephone depuis le PC

1. Menu Démarrer → **Wasteland - Installer sur le telephone**.
   - *Tu dois voir :* une fenêtre noire dont le titre est
     **« Telephone Android (optionnel) »**.
   - Si adb n'était pas encore là, il est téléchargé d'abord :
     `Installation d'adb (outils Android officiels de Google, ~7 Mo)...`
     → `OK`.
2. Le menu demande **« Installer Wasteland sur quel telephone? »** et
   liste ce qu'il a trouvé :

   ```
   1. Pixel 7
   2. Associer un autre telephone (debogage sans fil)
   3. Passer
   Choix [3] :
   ```

   - Tape le numéro de **ton** téléphone puis **Entrée**.
   - Rien de listé, ou pas encore appairé ? Tape le numéro **Associer un
     autre telephone**, **Entrée**, puis suis les instructions à l'écran —
     elles répètent les étapes de la section 4 et finissent par :
     *« Quand le code est affiche (ou le cable branche), appuie sur
     Entree... »* → Entrée, tape le **code à 6 chiffres** quand on te le
     demande, et si le téléphone n'apparaît toujours pas, tape la ligne
     **« Adresse IP et port »** exactement comme le téléphone l'affiche.
   - **Entrée** tout de suite = **Passer** (rien n'est installé ; tu
     referas plus tard via le menu Démarrer).
3. Ce qui se passe ensuite, dans l'ordre :
   - `Installation de "Wasteland"...` — l'app part sur le téléphone.
   - `Copie du jeu (~1,3 Go par Wi-Fi : quelques minutes, garde l'ecran
     allume)...` — **garde l'écran allumé et le Wi-Fi ouvert.**
   - *Tu dois voir,* à la fin :
     `C'est installe! "Wasteland" vient de s'ouvrir.` /
     `Tu peux maintenant debrancher / desactiver le debogage sans fil.`
   - Durée : **quelques minutes**, surtout la copie. L'app
     (**« Wasteland »**, icône verte) s'ouvre toute seule et le jeu démarre.
   - L'édition HD installe l'app **« Wasteland HD »** à la place ; les
     deux peuvent coexister.
4. **Si l'installation refuse :** *« Ce telephone (…) n'est pas compatible
   : il faut un Android 64 bits (arm64). »* → ce téléphone ne peut pas
   faire tourner le jeu. Sur certains téléphones l'installation est
   refusée tant que tu n'as pas activé **« Installer via USB »** dans les
   Options pour les developpeurs (Xiaomi et autres) — voir
   [Dépannage](TROUBLESHOOTING.fr.md#le-téléphone-nest-pas-trouvé-ou-lassociation-échoue).

### Le chemin « seulement le téléphone » (sans installateur PC)

À utiliser si tu prépares le téléphone seul (c'est aussi la façon
d'installer sur un **deuxième** téléphone.

1. Sur le téléphone, ouvre la page des releases et télécharge
   [`Wasteland-arm64.apk`](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-arm64.apk)
   (classique) ou
   [`Wasteland-HD-arm64.apk`](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-HD-arm64.apk)
   (HD) — environ 4 Mo.
2. Touche l'APK téléchargé → Android demande la permission d'installer des
   apps de cette source (Chrome, Fichiers…) → autorise une fois →
   **Installer**.
   - L'app n'est pas signée par Google Play : c'est normal.
3. Mets ton dossier Fallout 2 sur le téléphone : copie-le par câble USB
   (choisis *Transfert de fichiers*), par un cloud ou par une messagerie —
   comme dossier dans `Téléchargements`, ou comme une seule archive
   (`.zip`, `.7z`, `.rar`).
4. Ouvre l'app. Au premier lancement, l'écran **"Files of the game"** affiche
   deux boutons : **Choose the folder** et **Choose an archive**.
   - *Tu dois voir :* *« Looking for the game… »*, puis **"Fallout 2
     found."** avec ce qu'elle a trouvé et la ligne **"To copy: …, free on
     the phone: …"**.
5. Clique sur **Copy**. *Tu dois voir :* **"Copying the game…"** avec une
   barre ; quand c'est fini, le jeu démarre tout seul. Garde l'écran allumé.
   - À noter : cet écran du premier lancement est pour l'instant
     **en anglais seulement**, même sur un téléphone en français (l'écran
     des graphismes HD, lui, est traduit).

## 6. L'art HD (édition HD seulement)

Les packs d'art HD se téléchargent **tout seul dans l'app** ; tu ne les
copies jamais à la main.

1. **Sur le téléphone :** à chaque démarrage de l'app HD, elle vérifie s'il
   y a de l'art (quelques secondes, *« Recherche de nouveaux graphismes
   HD… »*).
   - *S'il y a du nouveau, tu vois* le titre
     **« Mise à jour des graphismes HD »**, puis une ligne du genre
     **« Graphismes HD : World art: tiles, walls, scenery…, 187,0 Mo »**
     et **« 2 packs à télécharger (… Mo au total). »**.
2. Clique sur **« Télécharger »** (*Download*).
   - *Tu dois voir :* une progression **« world : 42 % »**, puis
     **« Installation des graphismes HD : world… »**, puis le jeu.
3. Clique sur **« Plus tard »** (*Later*) et le jeu démarre tout de
   suite ; la proposition revient au prochain démarrage, et un
   téléchargement interrompu **reprend** où il s'était arrêté.
4. **Espace :** l'offre affiche la taille exacte en Mo avant que tu
   acceptes — garde ce montant plus une marge (aujourd'hui quelques centaines
   de Mo ; les packs grossissent avec le temps).
5. **Vérification manuelle :** dans les réglages du jeu, ouvre
   **Game files** — l'écran montre un bouton **« Vérifier les graphismes
   HD »** (*Check for HD art*) sous les deux boutons d'import.
6. **Sur le PC :** l'installateur HD a proposé les packs pendant
   l'installation. Pour réessayer : menu Démarrer → **Wasteland -
   Configurer** et réponds **oui** à
   *« Telecharger les packs graphiques HD disponibles? »*.

## 7. Les PNJ avec IA (optionnel)

L'IA tourne **sur ton PC** (via [Ollama](https://ollama.com)) ; le
téléphone ne fait que lui parler.

### Sur le PC

1. Installe Ollama si tu ne l'as pas encore (<https://ollama.com>) et
   lance-le une fois pour qu'il s'installe dans la zone de notification.
2. Lance le jeu avec l'icône du bureau **« Wasteland Reborn »** (ou
   **« Wasteland Reborn HD »**).
3. **Vérifie que ça marche :** parle à un PNJ jusqu'à ce que les options de
   dialogue apparaissent — la dernière est **`[Speak freely]`**
   (toujours en anglais, même en français). Choisis-la et écris ta phrase
   **en anglais** (la langue du jeu).
   - *Tu dois voir :* la réponse du PNJ après quelques secondes (le
     premier message est plus lent : le modèle se charge).
   - **Pas de ligne `[Speak freely]` ?** L'IA est fermée → menu Démarrer →
     **Wasteland - Configurer** et réponds de nouveau aux questions de
     l'IA.

### Sur le téléphone — à la maison

1. Sur le PC, menu Démarrer → **Wasteland - Serveur IA (telephone)**.
   - *Tu dois voir :* une console qui affiche
     `Serveur IA pour le telephone : http://<adresse du PC>:8822` et
     *« Laisse cette fenetre ouverte pendant que tu joues sur le
     telephone. Ferme-la pour arreter. »* — **laisse-la ouverte.**
2. Le téléphone doit être sur le **même Wi-Fi** que le PC.
3. Pendant l'installation tu as choisi
   **« 2. Seulement a la maison (meme Wi-Fi que le PC) »**.
4. **La première fois**, Windows demande la permission d'ouvrir le port de
   l'IA : *« Windows va demander une autorisation pour ouvrir le port de
   l'IA (reseau local et Tailscale seulement). »* → accepte l'invite
   (Oui). La règle s'appelle **« Wasteland IA »**.

### Partout (loin de la maison) — Tailscale

Choisis **« 1. Partout (installe et configure Tailscale sur le PC et le
telephone) »** dans le menu du téléphone et l'installation fait ça :

1. **Sur le PC :** elle télécharge et installe
   [Tailscale](https://tailscale.com) (un VPN privé gratuit) — Windows
   demande la permission → accepte.
2. **Une page web s'ouvre :** connecte-toi (Google, Microsoft, …). La
   console dit *« Connexion de Tailscale sur le PC : une page web va
   s'ouvre. Connecte-toi (Google, Microsoft...). Utilise le MEME compte
   sur le telephone ensuite. »*
3. **Sur le téléphone :** l'app Tailscale est installée et s'ouvre toute
   seule : connecte-toi avec **le même compte**, puis accepte la demande
   de connexion VPN (c'est Tailscale qui la fait). La console attend —
   **appuie sur Entrée** pour passer si tu abandonnes.
4. *Tu dois voir :* `PC connecte a Tailscale: 100.x.x.x` et
   `Telephone connecte a Tailscale.`
5. Si ça ne marche pas, l'installation le dit et revient en arrière :
   *« Tailscale pas pret : l'IA du telephone marchera a la maison (meme
   Wi-Fi). »* — réessaie plus tard avec menu Démarrer → **Wasteland -
   Installer sur le telephone**.

   ⚠️ À la question **`Choix [1] :`**, la valeur par défaut est
   **1 = Partout** : appuyer sur Entrée tout de suite installe Tailscale.
   Tape **2** si tu le veux seulement à la maison, **3** pour pas d'IA sur
   le téléphone.

6. **Vérifie que ça marche :** ouvre un dialogue sur le téléphone → la
   dernière option est **`[Speak freely]`** → écris en anglais → la
   réponse arrive. Si elle n'arrive pas, la fenêtre du serveur est sans
   doute fermée — voir
   [Dépannage](TROUBLESHOOTING.fr.md#pas-de-réponse-de-lia).

### Activer l'IA plus tard

Rien à configurer à la main : menu Démarrer → **Wasteland - Configurer**
relance les questions, téléchargement du modèle compris.

## 8. Mettre à jour, sauvegarder, désinstaller

### Mettre à jour vers une nouvelle version

1. **PC :** télécharge le nouveau `WastelandReborn-Setup.exe` (même
   édition) et lance-le. Il s'ouvre sur la page des dossiers déjà pointée
   vers ton vieux dossier — **garde-le** (clique **Suivant >** puis
   **Installer**).
   - Réglages, sauvegardes et mémoires de l'IA sont conservés.
   - L'édition HD ne met à jour que l'installation HD, et inversement.
2. **Téléphone (installé depuis le PC) :** lance menu Démarrer →
   **Wasteland - Installer sur le telephone** avec la nouvelle version ; elle
   recopie ce qui a changé et garde tes sauvegardes.
3. **Téléphone (chemin APK) :** installe le nouvel APK **par-dessus
   l'ancienne app** (même édition). Tes sauvegardes restent.
   - Les deux apps (`Wasteland` et `Wasteland HD`) sont séparées : chacune
     se met à jour avec son propre APK.

### Sauvegarder tes parties

1. **Sur le PC :** ouvre l'Explorateur de fichiers et va dans
   `%LOCALAPPDATA%\WastelandReborn\game\data\savegame`
   (colle-le dans la barre d'adresse ; l'édition HD utilise
   `%LOCALAPPDATA%\WastelandRebornHD\...`).
   - *Tu dois voir :* des dossiers comme `SLOT0001`, `SLOT0002`, …
2. Copie ce dossier `savegame` quelque part en sûr (clé USB, cloud).
   - Les mémoires de ton IA sont juste à côté, dans
     `%LOCALAPPDATA%\WastelandReborn\userdata` — copie-les aussi si tu
     veux les garder.
3. **Sur le téléphone :** dans les réglages du jeu, ouvre **Game files** →
   **Export saves** (« toutes les sauvegardes dans une seule archive ») et
   choisis où mettre le zip.

### Désinstaller

- **PC :** menu Démarrer → **Wasteland Reborn → Desinstaller**, ou
  *Paramètres → Applications → Wasteland Reborn → Désinstaller*. Ça enlève
  le programme, ses raccourcis et l'icône du bureau, et **garde**
  `game\data\savegame` (tes sauvegardes) et `userdata` (les mémoires de
  l'IA). Supprime ces deux dossiers toi-même si tu veux tout effacer.
- **Téléphone :** désinstalle l'app **Wasteland** comme n'importe quelle
  app. Android supprime ses données — **exporte tes sauvegardes avant**
  (étape 3 ci-dessus).

## 9. Dépannage — tableau rapide

Explications complètes, étape par étape :
[TROUBLESHOOTING.fr.md](TROUBLESHOOTING.fr.md) (EN :
[TROUBLESHOOTING.md](TROUBLESHOOTING.md)).

| Ce que tu vois | Que faire |
| --- | --- |
| *« Windows a protégé votre ordinateur »* en lançant l'installateur | **« Plus d'informations » → « Exécuter quand même »** → [aide](TROUBLESHOOTING.fr.md#windows-smartscreen-bloque-linstallateur) |
| L'installateur disparaît, ou l'antivirus dit « supprimé » | Ton antivirus a mis en quarantine un fichier non signé → [aide](TROUBLESHOOTING.fr.md#lantivirus-met-linstallateur-ou-lapp-en-quarantaine) |
| *« Je n'ai pas trouve Fallout 2 automatiquement »* / *« Pas de master.dat + critter.dat »* | Indique-lui le dossier de la section 1.3 → [aide](TROUBLESHOOTING.fr.md#linstallation-ne-trouve-pas-fallout-2) |
| Le téléphone n'apparaît jamais dans le menu | Même Wi-Fi, débogage sans fil activé, téléphone déverrouillé → [aide](TROUBLESHOOTING.fr.md#le-téléphone-nest-pas-trouvé-ou-lassociation-échoue) |
| Code d'association refusé / *« Pas de telephone connecte »* | Rouvre **Appairer un appareil avec un code d'appairage** ; si on te le demande, donne la ligne « Adresse IP et port » → [aide](TROUBLESHOOTING.fr.md#le-téléphone-nest-pas-trouvé-ou-lassociation-échoue) |
| Téléphone listé **unauthorized** (ou absent) | Accepte **Autoriser le débogage USB ?** sur l'écran du téléphone → [aide](TROUBLESHOOTING.fr.md#le-téléphone-affiche-unauthorized) |
| Écran noir au démarrage du jeu | [aide](TROUBLESHOOTING.fr.md#écran-noir) |
| Texte des dialogues vide | Copie de jeu incomplète, en général → [aide](TROUBLESHOOTING.fr.md#texte-de-dialogue-vide) |
| Pas de `[Speak freely]`, ou aucune réponse du PNJ | Ollama/serveur fermé → [aide](TROUBLESHOOTING.fr.md#pas-de-réponse-de-lia) |
| Téléchargement HD bloqué ou qui repart | Il reprend au prochain démarrage ; vérifie connexion/espace → [aide](TROUBLESHOOTING.fr.md#téléchargement-hd-bloqué) |
| *« Not enough free space on the phone »* | Libère de la place ou supprime des sauvegardes → [aide](TROUBLESHOOTING.fr.md#plus-de-place) |
| Epic : fichiers non téléchargés / non vérifiés | Vérifie le jeu dans Epic, puis relance **Wasteland - Configurer** → [aide](TROUBLESHOOTING.fr.md#le-jeu-nest-pas-téléchargé-ou-pas-vérifié) |

---

*Wasteland Reborn est un projet de fans non officiel, ni affilié ni approuvé
par Bethesda Softworks, ZeniMax ou Interplay. Les fichiers de Fallout 2 ne
sont jamais inclus : apporte ta propre copie.*
