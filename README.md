# TMDL Relationship Automation

Outils Python pour visualiser et modifier automatiquement les relations Power BI en PBIP (Git-friendly).

## 📋 Outils inclus

### 1. **Viewer Tk** (`view_tmdl_relationships_tk.py`)
Interface graphique pour parcourir toutes les relations d'un semantic model.

```bash
python scripts/view_tmdl_relationships_tk.py
```

**Fonctionnalités:**
- Liste toutes les relations avec leurs paramètres
- Filtrage par nom, fichier, colonnes
- Panneau de détails avec bloc TMDL complet
- **Édition directe:** modification de `crossFilteringBehavior` et `isActive`
- **Dry Run:** prévisualisation des changements avant application
- **Apply Changes:** modification du fichier TMDL + rechargement automatique

### 2. **Script d'Automatisation** (`update_tmdl_relationship.py`)
Outil CLI pour modifier les relations programmatiquement, idéal pour CI/CD et scripts batch.

```bash
python scripts/update_tmdl_relationship.py <file> <relationship-name> [options]
```

**Options:**
- `--cross-filtering {oneDirection|bothDirections}` : Change le filtrage
- `--is-active {true|false}` : Active/désactive la relation
- `--property NAME=VALUE` : Modifie une propriété arbitraire
- `--dry-run` : Affiche le résultat sans écrire le fichier

## 🎯 Exemple concret

### Scénario
Tu as une relation `medals.code → athletes.code` (ID: `1caa4312-c095-9117-0360-2a4353cd02e7`) et ton responsable demande un filtrage **bidirectionnel**.

### Étape 1: Aperçu avec dry-run
```bash
python scripts/update_tmdl_relationship.py \
  "summer_olympics_2024_dashboard.SemanticModel\definition\relationships.tmdl" \
  "1caa4312-c095-9117-0360-2a4353cd02e7" \
  --cross-filtering bothDirections \
  --dry-run
```

### Étape 2: Appliquer la modification
```bash
python scripts/update_tmdl_relationship.py \
  "summer_olympics_2024_dashboard.SemanticModel\definition\relationships.tmdl" \
  "1caa4312-c095-9117-0360-2a4353cd02e7" \
  --cross-filtering bothDirections
```

### Étape 3: Vérifier dans Git
```bash
git diff summer_olympics_2024_dashboard.SemanticModel/definition/relationships.tmdl
```

**Résultat:**
```diff
 relationship 1caa4312-c095-9117-0360-2a4353cd02e7
+	isActive: true
+	crossFilteringBehavior: bothDirections
 	fromColumn: medals.code
 	toColumn: athletes.code
```

### Étape 4: Commit et push
```bash
git add summer_olympics_2024_dashboard.SemanticModel/definition/relationships.tmdl
git commit -m "Update relationship medals->athletes: change to bidirectional filtering"
git push origin main
```

## ✨ Avantages

| Aspect | Power BI Desktop | PBIP + Scripts |
|--------|------------------|----------------|
| **Visiblité** | Interface compliquée | Liste claire dans un tableau |
| **Modification** | Manuelle | Automatisée + Git-tracked |
| **Versionning** | Binaire (pbix) | Texte (TMDL) → Diffs lisibles |
| **CI/CD** | Impossible | Facile avec scripts |
| **Review** | Pas de trace | Pull request avec changements précis |
| **Batch editing** | Un par un | Tous d'un coup |

## 📦 Requirements

- Python 3.8+
- tkinter (inclus avec Python sur Windows)

## 🚀 Intégration Git

Les fichiers TMDL sont du texte pur, donc les modifications sont **100% traçables**:
- Pas d'énormes fichiers binaires
- Diffs humainement lisibles
- Facile à merger/revert
- Compatible avec CI/CD (GitHub Actions, GitLab CI, etc.)

## 📝 Notes

- Les IDs de relation (UUID) se trouvent dans `relationships.tmdl`
- Recherche le nom ou l'ID dans le Tk viewer pour identifier la relation à modifier
- Le script détecte automatiquement l'indentation TMDL
- Supports commentaires avec `///` en début de bloc

