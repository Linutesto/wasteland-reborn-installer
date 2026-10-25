# Wasteland Reborn — installateur Windows

Fallout 2 avec le **Restoration Project (RPU)** + FO2Tweaks, sur le moteur
open source **Fallout 2 Community Edition** (fork mobile), avec des **PNJ qui
répondent en texte libre grâce à une IA locale** (optionnelle, via Ollama).
Peut aussi installer le jeu sur un téléphone Android.

## ⬇️ Télécharger

**[WastelandReborn-Setup.exe](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest)** (≈ 830 Mo, Windows 10/11 64 bits)

## Il te faut

- **Ta propre copie de Fallout 2** installée (Epic, Steam ou GOG). Aucun
  fichier du jeu n'est inclus : l'installation retrouve ton jeu et copie
  `master.dat`, `critter.dat` et la musique.
- Optionnel : [Ollama](https://ollama.com) pour l'IA.
- Optionnel : un téléphone Android 64 bits (débogage sans fil activé).

## Installation

1. Lance `WastelandReborn-Setup.exe`. Windows peut afficher « Windows a
   protégé votre ordinateur » (fichier non signé) → **Informations
   complémentaires** → **Exécuter quand même**.
2. À la fin, une fenêtre de configuration te pose les questions :
   ton jeu, l'IA (si Ollama est là), puis un petit menu pour le téléphone
   (choisir un téléphone, en associer un avec le code à 6 chiffres, ou passer).
   adb (outil Android officiel de Google) est téléchargé automatiquement.
3. Joue avec l'icône **Wasteland Reborn** sur le bureau.

En dialogue, choisis **[Speak freely]** et écris ce que tu veux au personnage
(en anglais, la langue du jeu).

Menu Démarrer › Wasteland Reborn : *Configurer* (activer l'IA plus tard),
*Installer sur le téléphone*, *Serveur IA (téléphone)* (l'IA du téléphone
passe par le PC, sur le même Wi-Fi).

## Crédits

- [Fallout 2 CE](https://github.com/alexbatalov/fallout2-ce) et le
  [fork mobile](https://github.com/imbaner/fallout2-ce-mobile)
- [Restoration Project (RPU)](https://github.com/BGforgeNet/Fallout2_Restoration_Project)
  et [FO2Tweaks](https://github.com/BGforgeNet/FO2tweaks) — BGforgeNet
- Python (embeddable), NSIS, Ollama

Fallout est une marque de Bethesda Softworks. Projet de fans, non officiel.
