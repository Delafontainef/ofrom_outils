# Ofrom_outils
Collection d'outils pour la gestion du corpus OFROM+. 

## Utilisation
L'outillage est conçu pour être utilisé autant via l'interface graphique 
qu'avec des invites de commande.

- Pour l'interface graphique, double-cliquer sur 'maj.pyw' à la racine. 
- Pour les invites de commande, utiliser l'outillage comme un package.

> ```pip install -e .```

Puis importer les fonctions / classes :

> ```from ofrom_scripts import ...```

ou utiliser les scripts directement.

Les scripts peuvent dépendre de programmes-tiers, typiquement Praat ou ffmpeg. 
Les programmes-tiers sont installés dans "programmes/" où les scripts vont 
chercher leurs exécutables.

Les scripts travaillent sur les ressources d'OFROM+. 

Les scripts '.praat' sont dans "programmes/praat/".

## Opérations

Il s'agit surtout ici de présenter des catégories "d'opérations" regroupées en 
sous-dossiers dans l'outillage.

- audio : gère les formats audio et leur amplitude via ffmpeg
- export : gère toutes les opérations pour la mise à jour du corpus
- nakala : gère l'API avec NAKALA. 
- pos : (inutilisé) génère le PoS via un modèle CRF
- stats : génère des statistiques (tables) ainsi que le dictionnaire de tokens

À quoi s'ajoutent les scripts Praat : 

- anon_ofrom_plus : anonymisation via Hirst (2013)
- ph_ofrom : (inutilisé) annotation phonémique

Et d'autres scripts soutenant ces opérations ou pour des besoins ponctuels. 

## Version

L'outillage d'OFROM+ <ofrom.unine.ch> est en refonte. 

Elle ne contient actuellement que les scripts pour travailler avec les 
métadonnées et les anciens scripts pour gérer ffmpeg. 