# META

Tout le code concernant la manipulation des métadonnées.

## Utilisation

Tout passe par la classe '*Meta*':
> from ofrom_outils.meta.meta import Meta
> 
> meta = Meta().load()

À l'initialisation, la classe *Meta* aura un chemin vers le fichier de 
métadonnées par défaut. On peut le lui fournir en argument au besoin.

Une fois la classe créée, il faut encore lui dire de charger les 
métadonnées en mémoire avec '*.load()*'. 

À partir de là, *Meta* permet de récupérer des métadonnées (avec '*.get()*') 
et de modifier ces métadonnées (avec '*.set()*'). Ces échanges sont vérifiés 
par des validateurs : la métadonnée sera TOUJOURS récupérée ou modifiée mais 
si la valeur est invalide, elle est réduite à une valeur par défaut (pour 
OFROM+, "NR").

Pour modifier les métadonnées avec plus de prudence, '*.ch_set()*' ne modifie 
que s'il n'existe pas déjà une valeur valide dans la métadonnée à modifier. 

> valeur = meta.get(<code_transcription>, <code_locuteur>, <nom_de_colonne>)
> 
> meta.set(<code_transcription>, <code_locuteur>, <nom_de_colonne>, <valeur>)
> 
> meta.ch_set(idem)
> 
> meta.add_to_trans(Transcription)
> 
> meta.set_pub(<nom_du_sous_corpus>, <chemin_du_corpus>)

Pour ajouter les métadonnées à une Transcription (librairie 'corflow'), 
'*.add_to_trans()*' n'a besoin que de la transcription (l'objet en mémoire, 
pas le chemin de fichier). 

Pour générer un fichier de métadonnées public (qui retire des colonnes 
"techniques"), '*.set_pub()*' a besoin du nom du dossier et du chemin du 
corpus (voir CORE dans 'ofrom_outils.common').

Attention à sauvegarder le fichier de métadonnées avec '*.save()*' ou les 
modifications ne seront pas conservées ; et à fermer le fichier après 
utilisation avec '*.close()*' s'il doit être accessible ailleurs.

## Code

### Modèle de données

Les métadonnées sont contenues par défaut dans un fichier Excel (.xslx). 
Ce fichier devrait toujours avoir son correspondant OpenOffice (.ods).

Les métadonnées sont chargées en mémoire sous la forme d'un objet 
'*MetaDict*' (voir 'meta_models.py') :
> MetaDict  
> | tr<str, Tr>  
> |- d (dict<str, str>)  
> |- spk (list<str>)  
> | spk<(str, str), Spk>  
> |- d (dict<str, str>)  
> |- sh (tuple<str, int>)  

*MetaDict* contient un dictionnaire de 
transcriptions (sous forme d'objets '*Tr*') et une liste de locuteurs 
par transcription (sous forme d'objets '*Spk*'). Les clés de MetaDict.spk 
sont un tuple (*trcode, spkcode*) pour le code de transcription et locuteur 
respectivement : les métadonnées d'un locuteur peuvent changer d'une 
transcription à une autre (notamment les relations). 
- '*Tr*' contient les métadonnées de la transcription ('d') et une liste 
des locuteurs de cette transcription ('spk').
- '*Spk*' contient les métadonnées du locuteur ('d') et sa position dans le 
fichier ('sh'). 

Pour accéder à l'âge, donc, il faut : 
> `MetaDict.spk[(trcode, spkcode)].d['age']`

En théorie les autres scripts n'ont pas à accéder directement à ce modèle. 
*Meta* est là pour en assurer l'accès et en maintenir la cohérence. 

### Validation

La validation des données (voir 'meta_validation.py') repose sur deux 
classes ('*VVal*' et '*VCell*') qui partagent les mêmes fonctions : 

> val_to_str()
> str_to_regex()
> regex_to_list()
> regex_to_date()

Les métadonnées d'OFROM+ seront toujours sous la forme d'une chaîne de 
caractères (string), d'où 'val_to_str()'. 

Une expression régulière élimine les caractères indésirables : c'est 
'str_to_regex()' (dont la regex liste les symboles autorisés).

Certaines colonnes n'ont qu'un nombre de valeurs limité (typiquement 'Role'). 
On peut en fournir la liste et le validateur vérifie que la valeur s'y trouve. 

Ou certaines colonnes sont des dates, auquel cas on en vérifie et standardise 
le format. À noter que ce n'est pas de l'ISO mais un format requis par les 
XMLs pour le dépôt sur le site ('*CELL_D*').

La variable globale D_VAL liste les colonnes avec un validateur personnalisé. 
Autrement le validateur par défaut s'applique ('str_to_regex()' avec une 
expression régulière prédéfinie '*CELL_R*'). 

### Remarques

Si le nom des colonnes est modifié dans le fichier de métadonnées, il faut 
corriger ces noms en conséquence dans 'meta_functions.py'. Il faut que le 
script sache : 
- où trouver les codes de transcription / locuteur,
- quelles métadonnées appartiennent à la transcription, 
- quelles métadonnées appartiennent au locuteur, 
- quelles métadonnées vont dans le fichier public.

À noter aussi qu'il existe un locuteur particulier, 'enquêteur', qui n'est 
pas dans le fichier de métadonnées (puisqu'il n'est pas censé en avoir). 
Le code le détecte (avec 'ENQU') et lui attribue la valeur par défaut ('NR').

