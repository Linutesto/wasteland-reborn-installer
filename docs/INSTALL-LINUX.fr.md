# Installer Wasteland Reborn sous Linux

Il te faut ta propre copie installée de Fallout 2. Ce dépôt ne télécharge jamais les fichiers du jeu. Ces étapes visent Ubuntu, Fedora, Arch et le **mode Bureau** du Steam Deck, en x86_64. Prévois plusieurs Go pour les outils, le jeu et l'art HD optionnel.

## 1. Installe les paquets

Dans un terminal, utilise seulement la ligne de ta distribution. Le système du Steam Deck est en lecture seule par défaut : utilise un conteneur de développement ou déverrouille-le avant pacman.

```sh
sudo apt install git cmake ninja-build rsync unzip curl tar xz-utils python3 imagemagick libsdl2-dev zlib1g-dev libpng-dev libfreetype-dev xvfb adb
sudo dnf install git cmake ninja-build rsync unzip curl tar xz python3 ImageMagick SDL2-devel zlib-devel libpng-devel freetype-devel xorg-x11-server-Xvfb android-tools
sudo pacman -S git cmake ninja rsync unzip curl tar xz python imagemagick sdl2 zlib libpng freetype2 xorg-server-xvfb android-tools
```

`--linux-only` ne demande pas les outils Windows. Pour compiler aussi l’installateur Windows, installe NSIS ou Wine.

## 2. Prépare le dépôt

```sh
git clone --recursive https://github.com/Linutesto/wasteland-reborn-installer.git
cd wasteland-reborn-installer
./bootstrap.sh --linux-only
```

Cette commande prépare le profil RPU sans le SDK Android. Pour compiler aussi un APK, lance `./bootstrap.sh` (classique) ou `./bootstrap.sh --edition hd` (HD) et accepte les licences Android. C'est plus long. `linux/phone.sh` peut aussi télécharger un APK publié.

## 3. Installe et joue

```sh
linux/install.sh --edition classic
wasteland
```

Le script cherche dans Steam natif, Steam Flatpak et les autres bibliothèques Steam, puis dans les emplacements habituels Heroic, Lutris et Wine/GOG. S'il ne trouve rien, indique le dossier qui contient `master.dat` et `critter.dat` :

```sh
linux/install.sh --edition classic --game /path/to/Fallout2
```

Pour la HD :

```sh
linux/install.sh --edition hd --game /path/to/Fallout2
wasteland
```

L'art HD est téléchargé après la vérification de tes fichiers. Si les packs ne sont pas encore publiés ou que le réseau échoue, tu peux jouer sans eux et relancer l'installation plus tard. Une entrée dans le menu Bureau et `~/.local/bin/wasteland` sont créés. Si la commande est introuvable, lance `~/.local/bin/wasteland` directement.

## PNJ avec IA (optionnel)

Installe et démarre [Ollama](https://ollama.com/), puis :

```sh
linux/install.sh --edition classic --game /path/to/Fallout2 --ai
wasteland
```

Le script propose le petit modèle `qwen3:4b`. Le cerveau local écoute sur `127.0.0.1:8822` pendant le jeu. L’IA du téléphone est désactivée par défaut. Pour l’activer, laisse `wasteland-brain` tourner sur le PC, trouve son adresse locale ou Tailscale, puis ajoute `--ai-server http://PC_IP:8822 --ai-token-file ~/.local/share/wasteland-reborn/brain/token` à `linux/phone.sh`. Le téléphone doit joindre le port 8822 du PC ; utilise ton réseau privé et garde le jeton secret.

## Téléphone Android (optionnel)

Active le débogage USB et accepte la demande affichée sur le téléphone :

```sh
adb devices
linux/phone.sh --edition classic --dry-run
linux/phone.sh --edition classic
```

Pour la HD, choisis `--edition hd`. Le script installe l'APK correspondant, crée le dossier de l'app et le profil RPU, copie ton jeu et sa musique, et envoie l'art HD sous forme de ZIP. Il ne remplace pas les sauvegardes du téléphone. Sans APK local, il télécharge celui de la dernière release. Tu peux aussi passer `--apk /path/to/file.apk`.

Pour le sans-fil, ouvre **Options pour les développeurs → Débogage sans fil → Associer avec un code**. Le port d'association est différent du port de connexion :

```sh
linux/phone.sh --edition classic --pair PHONE_IP:PAIR_PORT --code 123456 --connect PHONE_IP:CONNECT_PORT --dry-run
```

Enlève `--dry-run` après avoir vérifié les commandes et le paquet affichés. Si plusieurs appareils sont connectés, indique `--serial SERIAL` d'après `adb devices`.

## Mets à jour ou désinstalle

```sh
git pull --recurse-submodules
./bootstrap.sh --linux-only
linux/install.sh --edition classic --game /path/to/Fallout2
linux/uninstall.sh
```

Le manifeste de désinstallation retire les fichiers installés, mais garde les fichiers modifiés et les sauvegardes. Si les deux éditions partagent le préfixe, une désinstallation retire les deux. Pour un préfixe personnalisé, utilise `--prefix DIR` à l'installation, au transfert et à la désinstallation.

## Si ça coince

- **Pas de son :** vérifie la sortie audio et les paquets SDL2/PipeWire ; essaie une autre sortie.
- **Écran noir :** vérifie `master.dat` et `critter.dat`, puis lance `~/.local/bin/wasteland` dans un terminal pour lire l'erreur. Relance `./bootstrap.sh --linux-only` si le profil manque.
- **adb unauthorized :** déverrouille le téléphone, accepte la demande de débogage USB, puis relance `adb devices`.
- **Téléphone introuvable :** essaie un câble de données ou vérifie que PC et téléphone sont sur le même Wi-Fi. Les deux ports sans fil sont différents.
- **Art HD absent :** relance `linux/install.sh --edition hd --game /path/to/Fallout2` quand les packs sont publiés et accessibles.
- **Cerveau inaccessible :** vérifie `ollama list`, démarre Ollama et assure-toi que le port local 8822 est libre. L'IA du téléphone reste désactivée dans l'installation de base.
