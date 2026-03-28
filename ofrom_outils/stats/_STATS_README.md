# Stats

Tout le code concernant les statistiques du corpus

Cela comprend le décompte (nombre de locuteurs / enregistrements, durée, 
nombre de mots) mais aussi le dictionnaire de tokens.

## Utilisation

### Décompte

Pour les décomptes, le plus simple est d'utiliser la fonction : 
> from ofrom_outils.stats.stats import get_corpus_stats
> get_corpus_stats(
>     meta_path,  # chemin_vers_fichier_metadonnees
>     corp,       # liste des sous-corpus à prendre en compte
>     l_typs,     # liste de catégories
>     ...
>     save_path	  # chemin vers le fichier de statistiques à créer
> )

Par exemple : 
> get_corpus_stats(<metadata>, \["OFROM_multigenres"\], \["region"\])

Génèrera un fichier Excel à 'save_path' avec une feuille contenant les 
statistiques générales (par sous-corpus, ici avec 'OFROM-multigenres' 
uniquement) et une feuille 'region' contenant une table par sous-corpus 
plus la table pour l'ensemble. 

### Mise à jour des métadonnées 

Il existe une méthode cachée permettant de mettre à jour les colonnes 
'age', 'duree' et 'nbre_mots' des métadonnées automatiquement.
> from ofrom_outils.stats.stats_meta import StatsMeta
> sm = StatsMeta(<chemin_du_fichier_de_metadonnees>)
> sm.set_meta_stats()

Comme la classe '*Stats*' contient '*StatsMeta*':
> from ofrom_outils.stats.stats import Stats
> st = Stats(<chemin_du_fichier_de_metadonnees>)
> st.md.set_meta_stats()

Par défaut cette méthode ne réécrit pas les cellules contenant déjà des 
valeurs. 

### Dictionnaire de tokens

Pour le dictionnaire de tokens, il faut passer par la classe '*TokenDict*' : 
> from ofrom_outils.stats.token_dict import TokenDict
> td = TokenDict()
> td.generate()		# génère le dictionnaire en mémoire
> td.save(<chemin>)	# crée le fichier
> 
> td.load(<chemin>)	# recharge le dictionnaire depuis le fichier

Le dictionnaire fonctionne sur l'emplacement du corpus (CORE, voir 
'ofrom_outils.common.py'). Il en parcourt la totalité des tokens dans 
tous les fichiers, les groupe alphabétiquement et fournit pour chacun 
entre autres leur lemme, leurs étiquettes PoS, leur nombre d'occurrences 
et le nom des fichiers où ils apparaissent (si ce n'est pas excessif). 

## Développement

...