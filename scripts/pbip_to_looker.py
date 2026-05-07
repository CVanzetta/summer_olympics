#!/usr/bin/env python3
"""
Convert Power BI PBIP semantic model to Looker LookML.

Usage:
    python pbip_to_looker.py <path_to_pbip> <output_dir>

Example:
    python pbip_to_looker.py "summer_olympics_2024.pbip" "./looker_model"
"""

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class Column:
    name: str
    column_type: str
    description: str = ""


@dataclass
class Table:
    name: str
    columns: List[Column]
    description: str = ""


@dataclass
class Relationship:
    name: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cross_filtering: str = "oneDirection"
    is_active: bool = True


def parse_tmdl_columns(tmdl_path: Path) -> Dict[str, List[Column]]:
    """Extract columns from tables in TMDL files."""
    columns_by_table = {}
    
    for tmdl_file in tmdl_path.glob("**/*.tmdl"):
        content = tmdl_file.read_text(encoding="utf-8")
        
        # Find table declarations
        table_pattern = r"table\s+(\w+)\s*\{([^}]+)\}"
        for table_match in re.finditer(table_pattern, content, re.DOTALL):
            table_name = table_match.group(1)
            table_content = table_match.group(2)
            
            # Extract columns
            column_pattern = r"column\s+(\w+)[\s:]+([^\n]+)"
            columns = []
            for col_match in re.finditer(column_pattern, table_content):
                col_name = col_match.group(1)
                col_type = col_match.group(2).split(";")[0].strip()
                # Simplify type mapping
                col_type = col_type.split("(")[0].strip()  # Remove parameters
                columns.append(Column(name=col_name, column_type=col_type))
            
            if columns:
                columns_by_table[table_name] = columns
    
    return columns_by_table


def parse_relationships(tmdl_path: Path) -> List[Relationship]:
    """Extract relationships from relationships.tmdl."""
    relationships = []
    rel_file = tmdl_path / "relationships.tmdl"
    
    if not rel_file.exists():
        return relationships
    
    content = rel_file.read_text(encoding="utf-8")
    
    # Find relationship blocks
    rel_pattern = r"relationship\s+([^\s{]+)\s*\{([^}]+)\}"
    for rel_match in re.finditer(rel_pattern, content, re.DOTALL):
        rel_id = rel_match.group(1).strip("'\"")
        rel_body = rel_match.group(2)
        
        # Extract properties
        from_col = re.search(r"fromColumn:\s*(\S+)", rel_body)
        to_col = re.search(r"toColumn:\s*(\S+)", rel_body)
        cross_filt = re.search(r"crossFilteringBehavior:\s*(\w+)", rel_body)
        is_active = re.search(r"isActive:\s*(true|false)", rel_body)
        
        if from_col and to_col:
            from_parts = from_col.group(1).split(".")
            to_parts = to_col.group(1).split(".")
            
            relationships.append(
                Relationship(
                    name=rel_id,
                    from_table=from_parts[0] if len(from_parts) > 1 else "unknown",
                    from_column=from_parts[-1],
                    to_table=to_parts[0] if len(to_parts) > 1 else "unknown",
                    to_column=to_parts[-1],
                    cross_filtering=cross_filt.group(1) if cross_filt else "oneDirection",
                    is_active=is_active.group(1) == "true" if is_active else True,
                )
            )
    
    return relationships


def generate_looker_view(table: str, columns: List[Column], relationships_from_table: List[Relationship]) -> str:
    """Generate LookML view for a table."""
    view_name = table.lower().replace(" ", "_")
    
    lookml = f"""view: {view_name} {{
  sql_table_name: {table} ;;
  
"""
    
    # Add primary key dimension (assuming 'id' exists)
    id_col = next((c for c in columns if c.name.lower() == "id"), None)
    if id_col:
        lookml += f"""  dimension: id {{
    primary_key: yes
    type: number
    sql: ${{TABLE}}.id ;;
  }}

"""
    
    # Add other columns
    for col in columns:
        if col.name.lower() == "id":
            continue
        
        dim_name = col.name.lower().replace(" ", "_")
        col_type = "string" if "text" in col.column_type.lower() or col.column_type.lower() == "string" else "number" if "int" in col.column_type.lower() or "decimal" in col.column_type.lower() else "date" if "date" in col.column_type.lower() else "string"
        
        lookml += f"""  dimension: {dim_name} {{
    type: {col_type}
    sql: ${{TABLE}}.{col.name} ;;
  }}

"""
    
    # Add count measure
    lookml += f"""  measure: count {{
    type: count
    drill_fields: [id]
  }}
"""
    
    # Add joins for relationships FROM this table
    for rel in relationships_from_table:
        if rel.to_table != table:
            join_name = rel.to_table.lower().replace(" ", "_")
            lookml += f"""
  measure: {join_name}_count {{
    type: count
    filters: [{{ref}}: {join_name}.id]
  }}
"""
    
    lookml += "}\n"
    return lookml


def generate_looker_explore(tables: Set[str], relationships: List[Relationship]) -> str:
    """Generate LookML explore combining views."""
    primary_table = sorted(tables)[0] if tables else "main"
    explore_name = primary_table.lower().replace(" ", "_")
    
    lookml = f"""explore: {explore_name} {{
  label: "{primary_table}"
  description: "Explore {primary_table} with related data"
  
"""
    
    # Add joins for relationships
    for rel in relationships:
        if rel.from_table == primary_table and rel.to_table != primary_table:
                        join_name = rel.to_table.lower().replace(" ", "_")
                        # Build sql_on using literal LookML references like ${view_name}.column
                        primary_view = primary_table.lower().replace(" ", "_")
                        sql_on = "${" + primary_view + "}." + rel.from_column + " = ${" + join_name + "}." + rel.to_column + " ;;"
                        lookml += (
                                "  join: "
                                + join_name
                                + " {\n"
                                + "    type: left_outer\n"
                                + "    relationship: many_to_one\n"
                                + "    sql_on: "
                                + sql_on
                                + "\n  }\n\n"
                        )
    
    lookml += "}\n"
    return lookml


def convert_pbip_to_looker(pbip_path: Path, output_dir: Path) -> None:
    """Main conversion function."""
    pbip_path = Path(pbip_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find semantic model
    semantic_models = list(pbip_path.glob("*SemanticModel"))
    if not semantic_models:
        print(f"❌ No semantic model found in {pbip_path}")
        return
    
    model_path = semantic_models[0] / "definition"
    if not model_path.exists():
        print(f"❌ Model definition not found at {model_path}")
        return
    
    print(f"📂 Found model: {semantic_models[0].name}")
    
    # Parse tables and relationships
    columns_by_table = parse_tmdl_columns(model_path)
    relationships = parse_relationships(model_path)
    
    print(f"📊 Found {len(columns_by_table)} tables and {len(relationships)} relationships")
    
    # Generate LookML views
    views_dir = output_dir / "views"
    views_dir.mkdir(exist_ok=True)
    
    for table_name, columns in columns_by_table.items():
        rels_from_table = [r for r in relationships if r.from_table == table_name]
        looker_view = generate_looker_view(table_name, columns, rels_from_table)
        
        view_file = views_dir / f"{table_name.lower().replace(' ', '_')}.view.lkml"
        view_file.write_text(looker_view, encoding="utf-8")
        print(f"✓ Generated view: {view_file.name}")
    
    # Generate LookML explore
    explore_file = output_dir / "explores.model.lkml"
    explore_content = ""
    for table_name in columns_by_table.keys():
        explore_content += generate_looker_explore({table_name}, relationships)
    
    explore_file.write_text(explore_content, encoding="utf-8")
    print(f"✓ Generated explore: {explore_file.name}")
    
    # Generate metadata summary
    metadata = {
        "source": str(pbip_path),
        "tables": list(columns_by_table.keys()),
        "relationships": [
            {
                "name": r.name,
                "from": f"{r.from_table}.{r.from_column}",
                "to": f"{r.to_table}.{r.to_column}",
                "type": r.cross_filtering,
                "active": r.is_active,
            }
            for r in relationships
        ],
    }
    
    metadata_file = output_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Generated metadata: {metadata_file.name}")
    
    print(f"\n✅ Conversion complete! LookML files in: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Convert Power BI PBIP to Looker LookML")
    parser.add_argument("pbip_path", type=str, help="Path to Power BI project (.pbip)")
    parser.add_argument("output_dir", type=str, help="Output directory for LookML files")
    
    args = parser.parse_args()
    convert_pbip_to_looker(Path(args.pbip_path), Path(args.output_dir))


if __name__ == "__main__":
    main()
