# Ofrom_outils
Collection d'outils pour la gestion du corpus OFROM+.

## Installation

L'outillage d'OFROM+ est conçu comme un espace de travail. Il faut donc 
le télécharger manuellement (code > Download ZIP) ou via git.

Le code fourni ici ne suffit pas. Il faut : 
- ajouter le sous-dossier 'ofrom_outils/pr/'
- (s'assurer que les chemins obtenus sont les bons : que l'outillage 
a bien accès aux ressources d'OFROM+.)
- ajouter l'exécutable DisMo dans 'programmes/DisMo/'
- ajouter l'exécutable Praat dans 'programmes/praat/'
- ajouter (si 'ofrom_outils.audio' est utilisé) FFMPEG dans 
'programmes/ffmpeg/'

Si les programmes sont installés ailleurs, modifier les chemins dans 
'ofrom_outils.common' en conséquence.

L'outillage requiert une série de librairies/modules Python. Il se comporte
comme un 'package' et installera les dépendances en même temps que lui.
Il faut donc, idéalement dans un environnement virtuel, lancer : 
> ```pip install -e .```

Depuis l'emplacement du dossier contenant le fichier '.toml' et le 
sous-dossier 'ofrom_outils'.

## Utilisation
L'outillage est avant tout conçu pour être utilisé via une interface 
graphique. 
- double-cliquer sur 'maj.pyw' dans le dossier 'maj'.

(À noter que 'maj.pyw' installera l'outillage via pip si les imports 
échouent.)

Il est aussi possible de l'utiliser via des scripts : 
> ```from ofrom_outils import ...```

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

Il ne contient actuellement que 'log', 'formats', 'meta' et 'stats'. 
Une fois 'audio' ajouté, la prochaine étape est 'gui', puis 'export' et 
enfin 'pos'.