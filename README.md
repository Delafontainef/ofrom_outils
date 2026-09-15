# Ofrom_outils
Collection d'outils pour la gestion du corpus OFROM+.

## Installation

L'outillage d'OFROM+ est conçu comme un espace de travail. Il faut donc 
le télécharger manuellement (code > Download ZIP) ou via git.

Le code fourni ici ne suffit pas. Il faut remplir le dossier 'programmes' 
avec les fichiers manquants : 
- l'exécutable DisMo dans 'programmes/Dismo/'
- l'exécutable Praat dans 'programmes/praat'
- FFMPEG dans 'programmes/ffmpeg/'
- le dossier 'programmes/_ofrom/'

Si les programmes sont installés ailleurs, il faut modifier 
manuellement les chemins dans 'ofrom_outils.common' en conséquence.

L'outillage requiert une série de librairies/modules Python. Il se comporte
comme un 'package' et installera les dépendances en même temps que lui.
Il faut donc, idéalement dans un environnement virtuel, lancer : 
> ```pip install -e .```

Depuis l'emplacement du dossier contenant le fichier '.toml' et le 
sous-dossier 'ofrom_outils'.

## Utilisation
L'outillage est avant tout conçu pour être utilisé via une interface 
graphique. 
- double-cliquer sur 'ofrom.pyw' à la racine.

Il est aussi possible de l'utiliser via des scripts : 

```from ofrom_outils import ...```

Les scripts '.praat' sont eux dans "programmes/praat/".

## Opérations

Les principales opérations de l'outillage se trouvent dans des sous-dossiers
dédiés : 
- audio : gestion des fichiers audio (conversion, amplitude) via ffmpeg
- export : toute la chaîne de traitement pour la mise à jour du corpus
- stats : génération des statistiques (tables et dictionnaire)

À quoi s'ajoutent les scripts Praat (dans 'programmes/praat/) :
- anon_ofrom_plus : anonymisation via Hirst (2013)
- ph_ofrom : (inutilisé) annotation phonémique

 Les autres scripts soutiennent ces opérations :
- formats : conversions pour le module *corflow*
- gui : gestion de l'interface graphique
- log : gestion des messages (terminal ou interface graphique)
- meta : gestion des métadonnées (lecture/écriture)
- pos : (inutilisé) annotation automatique en PoS

## Remarques

L'outillage d'OFROM+ <ofrom.unine.ch> est en refonte. 

Il contient actuellement : 
- audio
- log
- formats
- meta
- stats
- gui

Il lui manque encore 'export' et enfin 'pos'.

La GUI ne couvre que le module 'audio'.