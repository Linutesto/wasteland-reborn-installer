# Wasteland Reborn — dépannage (Windows + téléphone)

Quelque chose qui marche pas ? Trouve ton symptôme plus bas ; chaque
correction est une liste d'étapes, une action à la fois.

- Le guide d'installation complet : [INSTALL-WINDOWS.fr.md](INSTALL-WINDOWS.fr.md)
- Anglais : [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Windows SmartScreen bloque l'installateur

**Ce que tu vois :** *« Windows a protégé votre ordinateur »* quand tu
lances `WastelandReborn-Setup.exe` (ou `WastelandRebornHD-Setup.exe`).

1. Dans le bleu, clique sur **« Plus d'informations »**.
   - *Tu dois voir :* une ligne d'éditeur (« Éditeur inconnu ») et un
     nouveau bouton.
2. Clique sur **« Exécuter quand même »**.
   - *Tu dois voir :* la fenêtre de langue de l'installation,
     *« Language / Langue »*.
3. Pas de bouton « Exécuter quand même » (politique d'entreprise, poste de
   travail…) ? Enregistre le fichier, clic dessus → **Propriétés** → en
   bas, coche **Débloquer** → **OK**, puis relance-le.

**Pourquoi :** l'installateur n'est pas signé par un certificat payant.
C'est normal ; la somme de contrôle du guide (étape 2.4) sert à vérifier
que le fichier est intact.

## L'antivirus met l'installateur ou l'app en quarantaine

**Ce que tu vois :** le `.exe` disparaît juste après le téléchargement,
Windows dit *« Menace supprimée »*, ou la fenêtre noire de configuration
n'ouvre jamais.

1. Ouvre **Sécurité Windows** (bouclier) → **Protection contre virus et
   menaces** → **Historique de la protection**.
   - *Tu dois voir :* une entrée pour `WastelandReborn-Setup.exe` (ou
     `adb.exe`, `python.exe`, `Desinstaller.exe`).
2. Sélectionne-la → **Actions** → **Autoriser sur l'appareil**, puis
   relance le téléchargement/l'installation.
3. Empêche que ça recommence : **Paramètres de la protection contre virus
   et menaces** → **Exclusions** → **Ajouter ou supprimer des exclusions**
   → ajoute `%LOCALAPPDATA%\WastelandReborn` (et `WastelandRebornHD`) et
   ton dossier `Téléchargements`.
4. Antivirus tiers (Avast, Kaspersky, …) : même principe — ouvre sa
   quarantaine, restaure le fichier, ajoute une exception sur le dossier
   d'installation.

**Pourquoi :** les installateurs non signés et `adb.exe` (l'outil Android
de Google) déclenchent des heuristiques « application indésirable ». Fais
ça seulement pour le fichier venu de la page officielle des releases.

## L'installation ne trouve pas Fallout 2

**Ce que tu vois,** dans la fenêtre noire de configuration :

> Je n'ai pas trouve Fallout 2 automatiquement.

ou, après avoir choisi un dossier :

> Pas de master.dat + critter.dat la-dedans. Reessayer? (O/n)

1. Ouvre le dossier de ton jeu depuis le magasin et vérifie qu'il contient
   **`master.dat`** et **`critter.dat`** :

   | Magasin | Comment ouvrir le dossier |
   | --- | --- |
   | Steam | Bibliothèque → clic droit sur **Fallout 2** → **Gérer → Ouvrir le dossier du jeu** |
   | GOG | GOG Galaxy → **Fallout 2** → ⚙ → **Gérer l'installation → Afficher le dossier** |
   | Epic | Bibliothèque → **…** sur Fallout 2 → **Gérer** → icône dossier |

   - Pas là, ou le dossier est à moitié vide ? Le jeu n'est pas entièrement
     téléchargé — va voir
     [Le jeu n'est pas téléchargé ou pas vérifié](#le-jeu-nest-pas-téléchargé-ou-pas-vérifié).
2. Reviens dans la fenêtre noire et appuie sur **Entrée** à
   *« Appuie sur Entree pour choisir le dossier... »*.
   - *Tu dois voir :* une fenêtre de sélection intitulée *« Choisis le
     dossier de Fallout 2 (celui avec master.dat) »*.
3. Choisis le dossier de l'étape 1 (pas son parent, pas le sous-dossier
   `data`) → **Sélectionner un dossier**.
4. *Tu dois voir :* `Trouve : <dossier>` et
   `Utiliser ce dossier? (O/n)` → **Entrée**, puis les lignes de copie
   (`master.dat (… Mo)...`).
5. Ça dit toujours non ? L'installation cherche toute seule les installs
   Epic, Steam et GOG (de C: à Z:, bibliothèques Steam comprises). Un
   disque externe débranché, ou un dossier déplacé, n'est pas trouvé —
   c'est exactement à ça que sert le choix manuel.
6. Tu as annulé le tout plus tôt ? Tout se refait : menu Démarrer →
   **Wasteland - Configurer**.

## Le téléphone n'est pas trouvé ou l'association échoue

**Ce que tu vois :** le menu ne liste aucun téléphone, ou
*« Pas de telephone connecte. Reessayer? »*, ou l'association échoue.

Passe cette liste dans l'ordre — c'est l'un de ces points, presque
toujours :

1. **Le même Wi-Fi sur les deux.** Le PC doit aussi être en Wi-Fi, pas
   seulement le téléphone. Les réseaux « invités » isolent souvent les
   appareils : utilise le réseau principal.
2. **Le débogage sans fil est activé** sur le téléphone :
   *Paramètres → Système → Options pour les développeurs → Débogage sans
   fil*.
   - Pas encore là ? *Paramètres → À propos du téléphone →* touche 7 fois
     sur **« Numéro de build »** d'abord (Samsung : *À propos du téléphone
     → Informations sur le logiciel* ; Xiaomi : *À propos du téléphone →
     Version MIUI*).
3. **Le téléphone est déverrouillé** (l'écran peut être allumé — certains
   téléphones cessent de se signaler en veille).
4. Lance menu Démarrer → **Wasteland - Installer sur le telephone** et
   choisis **Associer un autre telephone (debogage sans fil)**.
5. Sur le téléphone, touche les mots **« Débogage sans fil »** (pas
   l'interrupteur) → **« Appairer un appareil avec un code d'appairage »**.
   Laisse cet écran ouvert.
   - *Tu dois voir :* un code à 6 chiffres et une ligne
     **« Adresse IP et port »**.
6. Dans la fenêtre noire, appuie sur **Entrée** quand le code est affiché.
   - Si on te le demande, tape le **code à 6 chiffres** → Entrée.
   - Toujours rien : la console demande **« Adresse IP et port »** — tape
     la ligne du téléphone **telle quelle**, avec les deux-points.
     ⚠️ Ce n'est **pas** le même port que celui de l'écran de code.
   - `Telephone trouve: <adresse>:<port>` devrait apparaître, puis ton
     téléphone dans le menu.
7. *« Pas de telephone connecte. Reessayer? (O/n) »* → **Entrée** (oui)
   et refais 5–6 une fois ; mDNS a parfois besoin d'un deuxième essai.
8. **Fenêtre du pare-feu :** la première installation peut demander
   l'autorisation d'adb sur les réseaux privés → **Autoriser**. Ne pas
   l'accepter est une raison classique pour que le téléphone n'apparaisse
   jamais.
9. **Tu abandonnes le Wi-Fi → câble USB :** branche le téléphone, active
   **« Débogage USB »**, accepte **« Autoriser le débogage USB ? »** sur le
   téléphone, puis relance le menu — le téléphone apparaît sans aucune
   association.
10. *« Impossible d'installer adb (pas d'Internet?) »* → le PC n'a pas pu
    télécharger les outils de Google (~7 Mo). Vérifie la connexion et
    relance le menu.

## Le téléphone affiche unauthorized

**Ce que tu vois :** l'installation refuse, ou ton téléphone ne figure
tout simplement pas dans le menu.

Le menu ne liste que les téléphones qui font déjà confiance à ce PC — un
téléphone qui ne fait pas confiance est invisible, pas affiché en erreur.

1. Branche le téléphone (USB) ou garde le débogage sans fil actif, et
   regarde son écran : une fenêtre **« Autoriser le débogage USB ? »** avec
   une empreinte.
2. Coche **Toujours autoriser depuis cet ordinateur** → **Autoriser**.
   - Pas de fenêtre ? Dans *Options pour les développeurs*, touche
     **Révoquer les autorisations de débogage USB**, puis réactive
     **Débogage sans fil** (ou rebranche le câble) — la fenêtre revient.
3. Lance menu Démarrer → **Wasteland - Installer sur le telephone**
   encore : le téléphone devrait être listé ; choisis son numéro.

## Écran noir

**Ce que tu vois :** l'app ou le jeu sur le PC démarre, puis reste noir.

1. **Attends ~10 secondes.** Au premier démarrage, les fichiers du moteur
   se décompressent et, sur l'édition HD, une installation d'art peut être
   en train de finir.
2. Ferme pour de bon et relance : sur le téléphone, glisse l'app hors des
   apps récentes et rouvre **Wasteland** ; sur le PC, ferme et
   double-clique de nouveau sur l'icône du bureau.
3. **Téléphone, édition HD :** si le noir est arrivé juste après un
   téléchargement HD, l'installation d'art a été coupée — relance une fois
   (elle reprend) ou clique sur **« Plus tard »** pour ignorer l'art pour
   l'instant.
4. **Fichiers manquants** est la vraie cause habituelle : une copie
   interrompue.
   - Sur le PC : menu Démarrer → **Wasteland - Configurer** → répons
     **oui** à *« Les fichiers du jeu sont deja installes. Les recopier?
     (o/N) »*.
   - Sur le téléphone : relance menu Démarrer → **Wasteland - Installer
     sur le telephone** (il ne recopie que ce qui manque), ou dans les
     réglages du jeu ouvre **Game files** et rechoisis le dossier.
5. Toujours noir ? Note le modèle du téléphone + version d'Android (ou la
   version de Windows) et ouvre une issue sur le
   [dépôt des releases](https://github.com/Linutesto/wasteland-reborn-installer/issues)
   avec cette info — c'est un bug qu'on ne peut pas corriger à l'aveugle.

## Texte de dialogue vide

**Ce que tu vois :** le dialogue s'ouvre mais les lignes sont vides, ou il
manque des phrases entières.

1. Ça veut presque toujours dire que les **fichiers du jeu ont été copiés
   incomplètement** (copie interrompue, ou dossier qui n'était pas le jeu
   au complet).
2. Sur le PC : menu Démarrer → **Wasteland - Configurer** → **oui** à
   *« Les fichiers du jeu sont deja installes. Les recopier? (o/N) »*.
   - *Tu dois voir :* les lignes de copie de nouveau, finissant par
     `musique : N fichiers copies`.
3. Sur le téléphone : relance **Wasteland - Installer sur le telephone**,
   ou dans les réglages du jeu → **Game files** → **Replace game** et
   choisis le dossier complet de ton ordinateur (sauvegardes et réglages
   sont conservés).
4. Vérifie que la copie contient bien tout le dossier : `master.dat`,
   `critter.dat`, `data\`, et les fichiers de traduction de ta copie (le
   profil Restoration Project apporte son propre dossier
   `translations`).
5. La langue du jeu, c'est la langue des fichiers de **ta** copie de
   Fallout 2. Si les fichiers de langue manquent, le texte devient vide —
   recopie le dossier depuis une installation neuve et vérifiée.

## Pas de réponse de l'IA

**Ce que tu vois :** pas d'option **`[Speak freely]`** dans les dialogues,
ou tu la choisis et rien ne revient.

1. **Pas de ligne `[Speak freely]` du tout** → l'IA est fermée ou
   injoignable. Lance menu Démarrer → **Wasteland - Configurer** et
   réponds de nouveau aux questions de l'IA (téléchargement du modèle
   compris).
2. **Sur le PC,** lance le jeu depuis l'icône du bureau (elle démarre
   Ollama et le serveur local pour toi). Si une boîte dit *« Ollama ne
   repond pas »* — ouvre **Ollama** d'abord (son icône est dans la zone de
   notification), puis relance le jeu.
3. **Sur le téléphone,** le PC doit être allumé avec
   **Wasteland - Serveur IA (telephone)** ouvert. La console affiche
   `Serveur IA pour le telephone : http://<adresse du PC>:8822` et
   *« Laisse cette fenetre ouverte pendant que tu joues sur le telephone.
   Ferme-la pour arreter. »* — la fermer coupe l'IA (le jeu continue, sans
   réponses).
4. À la maison → téléphone et PC sur le **même Wi-Fi**. Ailleurs →
   Tailscale doit tourner **sur les deux, connecté au même compte**
   (`PC connecte a Tailscale:` / `Telephone connecte a Tailscale.` dans la
   console de configuration).
5. **Pare-feu :** la première fois, Windows demande d'ouvrir le port de
   l'IA — *« Windows va demander une autorisation pour ouvrir le port de
   l'IA (reseau local et Tailscale seulement). »* → accepte (la règle
   s'appelle **« Wasteland IA »**). Raté ? Relance **Wasteland -
   Installer sur le telephone** et réponds de nouveau à la question de
   l'IA.
6. La réponse n'est pas instantanée : le premier message prend quelques
   secondes (le modèle se charge) et un modèle occupé peut prendre
   ~45 secondes. Écris **en anglais** — la langue du jeu.
7. Le modèle a disparu ? Menu Démarrer → **Wasteland - Configurer**
   propose de le retélécharger.

## Téléchargement HD bloqué

**Ce que tu vois :** l'offre d'art HD reste là, la barre ne bouge plus, ou
le téléchargement repart à chaque démarrage.

1. Ce n'est **jamais** bloquant : **« Plus tard »** démarre le jeu tout de
   suite, et un téléchargement interrompu **reprend** au prochain
   démarrage (la ligne du journal est *« HD update skipped (can retry next
   launch)"*).
2. Vérifie que le téléphone/le PC est en ligne et que la taille annoncée
   en Mo tient dans ton espace libre.
3. Ferme l'app pour de rouvre-la : l'offre revient avec
   **« Télécharger »**.
4. *« Packs HD indisponibles pour le moment : … »* pendant la setup PC →
   le pack demandé n'est pas encore publié ; relance **Wasteland -
   Configurer** plus tard.
5. PC, installation silencieuse : lis `userdata\setup-install.log` dans le
   dossier d'installation — il dit quel pack a échoué et pourquoi.

## Plus de place

**Ce que tu vois :** *« Not enough free space on the phone: … more is
needed. »*, ou Windows se plaint qu'il n'y a pas assez de place.

**Téléphone :**

1. Libère au moins ce que le message demande (il faut ~2 Go au total).
2. Les vieilles sauvegardes sont le plus simple : dans les réglages du jeu
   → **Game files** → **Export saves** (garde le zip), puis
   **Delete all saves**.
3. Fais de la place ailleurs (téléchargements, photos, apps inutiles) et
   relance l'import — la tentative ratée n'a rien gardé.

**PC :**

1. Il faut environ 3 Go libres (≈ 830 Mo téléchargés + ≈ 1,3 Go de
   fichiers du jeu).
2. Si C: est plein, change de dossier sur la page
   **Choisissez le dossier d'installation** (**Parcourir...**) vers un
   autre disque.
   - Rappel : tes sauvegardes vivent alors dans `<dossier>\game\data\savegame`.

## Le jeu n'est pas téléchargé ou pas vérifié

**Ce que tu vois :** l'installation ne trouve pas le jeu, ou le dossier
n'a pas de `master.dat`, ou le magasin indique que le jeu est en cours
d'installation.

**Epic :**

1. Ouvre le lanceur Epic Games Launcher → Bibliothèque.
2. Clique sur **…** sur Fallout 2 → **Gérer** → l'icône dossier — le
   dossier qu'il ouvre est celui que l'installation veut.
3. S'il manque des fichiers : **… → Gérer → Vérifier les fichiers** (Epic
   vérifie et télécharge ce qui manque). Attends la fin.
   - L'installation lit les propres registres d'Epic : un jeu Epic jamais
     téléchargé est déclaré *introuvable* tant qu'il n'existe pas sur le
   disque.

**Steam :**

1. Bibliothèque → clic droit sur **Fallout 2** → **Propriétés → Fichiers
   locaux → Vérifier l'intégrité des fichiers du jeu**.
2. Quand c'est fini, le dossier doit contenir `master.dat` et
   `critter.dat`.

**GOG :**

1. GOG Galaxy → **Fallout 2** → ⚙ → **Gérer l'installation → Vérifier /
   Réparer**.

**Puis :** menu Démarrer → **Wasteland - Configurer** → le dossier trouvé
apparaît comme `Trouve : <dossier>` → **Entrée**.

---

## Toujours bloqué ?

Ouvre une issue sur le
[dépôt des releases](https://github.com/Linutesto/wasteland-reborn-installer/issues)
et inclut :

1. Quel fichier tu as lancé (`WastelandReborn-Setup.exe` ou
   `WastelandRebornHD-Setup.exe`) et où tu l'as téléchargé.
2. Ta version de Windows (Paramètres → Système → Informations) et, pour un
   problème de téléphone, le modèle + la version d'Android.
3. Le **texte exact** de l'erreur — copie-le depuis la fenêtre noire, ou
   une capture d'écran.
4. Si c'est l'étape PC, l'étape téléphone ou l'étape IA qui échoue.

*Wasteland Reborn est un projet de fans non officiel. Les fichiers de
Fallout 2 ne sont jamais inclus — apporte ta propre copie.*
