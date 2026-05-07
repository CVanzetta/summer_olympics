# Power BI + Looker Automation Toolkit

Complete automation suite for Power BI PBIP relationship management, GUI browsing, and Looker LookML conversion. All tools are Git-friendly with text-based tracking.

## 🎯 Features

### 1. **CLI Automation Script** (`update_tmdl_relationship.py`)
Modify relationships in Power BI semantic models programmatically:
- Change `crossFilteringBehavior` (one-direction ↔ bi-directional)
- Toggle `isActive` status
- Dry-run preview before applying
- Git-friendly text modifications
- Batch processing support

### 2. **GUI Relationship Browser** (`view_tmdl_relationships_tk.py`)
- 🔍 **Search & Filter**: Find relationships by name, table, or column
- 👁 **Visual Display**: See all relationships in a sortable table
- ✎ **Edit Interface**: Modify properties with dropdown menus
- 📤 **Export**: Save relationships to **JSON** or **CSV**
- 🎨 **Enhanced UI**: Modern styling with icons, colors, emoji indicators
- 📋 **Dry-run Preview**: See changes before applying
- Real-time filtering and selection

### 3. **LookML Converter** (`pbip_to_looker.py`)
Automatically convert Power BI semantic models to Looker LookML:
- Table → View mapping
- Column type inference (string, number, date, etc.)
- Relationship → Join conversion
- Automatic measure generation (counts, sums)
- Metadata export for audit trail

## 📋 Installation

```bash
# No external dependencies required
# Uses only Python built-ins: tkinter, pathlib, subprocess, json, csv, re
python -m pip install --upgrade pip
```

## 🚀 Usage

### CLI: Modify a Single Relationship

```bash
python scripts/update_tmdl_relationship.py \
  "C:\path\to\model\relationships.tmdl" \
  "1caa4312-c095-9117-0360-2a4353cd02e7" \
  --cross-filtering bothDirections \
  --is-active true
```

**Options:**
- `--cross-filtering {oneDirection|bothDirections}` - Filter direction
- `--is-active {true|false}` - Relationship status
- `--property KEY VALUE` - Set custom property
- `--dry-run` - Preview changes without writing

### GUI: Browse & Edit Relationships

```bash
python scripts/view_tmdl_relationships_tk.py
```

**In the GUI:**
1. Select a folder containing a `.SemanticModel` directory
2. Browse all relationships in the table
3. Search/filter relationships
4. Select a relationship to edit
5. Change `Cross Filtering` and `Is Active` dropdowns
6. Click `👁 Dry Run` to preview changes
7. Click `✓ Apply Changes` to modify TMDL
8. Export to JSON or CSV

### LookML: Convert to Looker

```bash
python scripts/pbip_to_looker.py "summer_olympics_2024.pbip" "./looker_output"
```

**Generates:**
- `views/` - LookML view files (one per table)
- `explores.model.lkml` - Explore definitions with joins
- `metadata.json` - Relationship mapping for reference

## 📊 Example Workflow

### Scenario: Modify Medals → Athletes Relationship

**Step 1: View in GUI**
```bash
python scripts/view_tmdl_relationships_tk.py
# GUI opens automatically
# Select: medals.code → athletes.code from table
```

**Step 2: Edit Properties**
```
In the right panel:
  Cross Filtering: select "bothDirections"
  Is Active: select "true"
```

**Step 3: Preview Changes**
```
Click "👁 Dry Run"
New window shows TMDL diff:
```

```diff
relationship 1caa4312-c095-9117-0360-2a4353cd02e7
+	isActive: true
+	crossFilteringBehavior: bothDirections
	fromColumn: medals.code
	toColumn: athletes.code
```

**Step 4: Apply Changes**
```
Click "✓ Apply Changes"
Script modifies TMDL file
GUI refreshes automatically
```

**Step 5: Track in Git**
```bash
cd C:\path\to\model
git diff
# Shows exactly what changed
git add summer_olympics_2024.SemanticModel/definition/relationships.tmdl
git commit -m "Update medals->athletes: enable bidirectional filtering"
git push origin main
```

### Export Relationships

**To JSON:**
```bash
# Click "📤 Export" → "JSON"
# File: relationships.json
{
  "name": "1caa4312-c095-9117-0360-2a4353cd02e7",
  "file": "summer_olympics_2024.SemanticModel/definition/relationships.tmdl",
  "from_column": "medals.code",
  "to_column": "athletes.code",
  "is_active": "true",
  "cross_filtering_behavior": "bothDirections"
}
```

**To CSV:**
```bash
# Click "📤 Export" → "CSV"
# Spreadsheet-friendly format
# Columns: Name, File, From Column, To Column, Active, Cross Filter
```

### Convert to LookML

```bash
# Convert entire project
python scripts/pbip_to_looker.py "summer_olympics_2024.pbip" "./looker_model"

# Output structure:
# looker_model/
# ├── views/
# │   ├── athletes.view.lkml
# │   ├── medals.view.lkml
# │   └── countries.view.lkml
# ├── explores.model.lkml
# └── metadata.json
```

**Generated views contain:**
- Dimensions for each column
- Primary key identification
- Count measures
- Joined measure references
- Type inference (string, number, date)

## 🔄 Power BI ↔ Looker Integration

### Option A: Looker Reads Power BI (Live Connection)
```
No conversion needed!
- Looker connects directly to Power BI via API
- Live data access
- Best for: dashboards, metrics, existing reports
- Disadvantage: limited transformation control
```

### Option B: Convert to LookML (Migration)
```bash
python scripts/pbip_to_looker.py "project.pbip" "./looker_model"
git add looker_model/
git commit -m "Migrate Power BI to Looker"
```

**Advantages:**
- Full control over data model
- Version-controlled transformations
- Can customize measures/dimensions
- Enables Looker's full feature set

### Comparison Table

| Aspect | Power BI PBIP | Looker LookML |
|--------|---------------|---------------|
| **Format** | Text (TMDL) | Text (LookML) |
| **Storage** | Binary PBIX / Text PBIP | Git repositories |
| **Relationships** | Implicit + explicit | Explicit joins |
| **Version Control** | Git-friendly | Git-native |
| **Deployment** | Manual / Server | Git-based CI/CD |
| **Live Data** | Direct semantic model | API/database connection |
| **Customization** | Limited | Extensive |

## 📁 Project Structure

```
new-tp/
├── scripts/
│   ├── update_tmdl_relationship.py    # CLI automation (140+ lines)
│   ├── view_tmdl_relationships_tk.py  # GUI browser (320+ lines)
│   └── pbip_to_looker.py              # LookML converter (280+ lines)
├── README.md                          # This file
└── .git/
    ├── objects/
    ├── refs/
    └── HEAD
```

## 🛠️ Development

Each script is self-contained with no external package dependencies.

**To add custom properties:**
```python
# update_tmdl_relationship.py
# Just add another --property argument
# Indentation is auto-detected and preserved
```

**To extend the GUI:**
```python
# view_tmdl_relationships_tk.py
# Edit _build_ui() to add new buttons/controls
# Add methods for new export formats (Excel, Parquet, etc.)
```

**To improve LookML generation:**
```python
# pbip_to_looker.py
# Edit generate_looker_view() for custom measures
# Add filters() for row-level security
# Add explore.always_filter for derived tables
```

## 🎓 Use Cases

1. **Audit Trail**
   - Git diffs show exactly who changed relationships and when
   - Perfect for compliance and governance

2. **Testing**
   - Dry-run workflow validates changes before production
   - Prevents accidental breaking changes

3. **Documentation**
   - LookML converts implicit relationships to explicit documentation
   - CSV export for data dictionary

4. **CI/CD Pipeline**
   - CLI script integrates with GitHub Actions, GitLab CI, Jenkins
   - Batch modify all relationships in one command

5. **Multi-team Collaboration**
   - GUI browser democratizes relationship management
   - No Power BI Desktop needed for browsing
   - JSON/CSV exports for stakeholders

6. **Migration Projects**
   - LookML converter assists in Power BI → Looker migrations
   - Metadata export for gap analysis

## 📝 Technical Notes

### PBIP Format
- **PBIP** (Power BI Project): Text-based, Git-friendly
- **PBIX** (Power BI Desktop): Binary, hard to track
- PBIP is recommended for team collaboration

### TMDL (Tabular Model Definition Language)
- Text-based DSL for Power BI models
- Preserves all formatting and comments
- Line-based parsing allows surgical edits without reparsing entire file
- Automatically detects and maintains indentation

### Relationship Properties
```tmdl
relationship 1caa4312-c095-9117-0360-2a4353cd02e7
	isActive: true
	crossFilteringBehavior: bothDirections  # or oneDirection
	fromColumn: medals.code
	toColumn: athletes.code
```

### Dry-Run Mechanism
- Uses `--dry-run` flag to preview changes
- Shows exact TMDL before/after
- No files are modified
- Safe to run multiple times

## ⚠️ Limitations

- LookML converter assumes standard Power BI naming conventions
- Complex DAX measures are not converted (manual mapping needed)
- Row-level security (RLS) requires manual LookML filter implementation
- Looker connection to Power BI requires API credentials and network access

## 📚 References

- [Power BI PBIP Format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [TMDL Language Reference](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview)
- [Looker LookML Guide](https://cloud.google.com/looker/docs/lookml-overview)

---

**Made with ❤️ for Power BI automation and Looker integration**
