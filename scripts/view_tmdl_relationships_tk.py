#!/usr/bin/env python3
"""Tkinter viewer for TMDL relationship blocks.

The app scans a semantic model folder for .tmdl files, extracts relationship
declarations, and shows them in a table plus a details panel.
"""

from __future__ import annotations

import re
import subprocess
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import json
import csv
from io import StringIO



TOP_LEVEL_PREFIXES = (
    "relationship ",
    "table ",
    "model ",
    "role ",
    "perspective ",
    "cultureInfo ",
    "expression ",
    "function ",
)

RELATIONSHIP_START_RE = re.compile(r"^\s*relationship\s+(?:'([^']+)'|\"([^\"]+)\"|([^\s]+))")


@dataclass
class RelationshipInfo:
    name: str
    file_path: Path
    start_line: int
    end_line: int
    from_column: str = ""
    to_column: str = ""
    is_active: str = ""
    cross_filtering: str = ""
    security_filtering: str = ""
    raw_block: str = ""


def detect_block_end(lines: list[str], start_index: int) -> int:
    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        stripped = lines[index].lstrip()
        if not stripped.strip():
            continue
        if not lines[index].startswith(("\t", "    ")) and stripped.startswith(TOP_LEVEL_PREFIXES):
            end_index = index
            break
    return end_index


def extract_relationships_from_text(text: str, file_path: Path) -> list[RelationshipInfo]:
    lines = text.splitlines(keepends=True)
    relationships: list[RelationshipInfo] = []

    for index, line in enumerate(lines):
        match = RELATIONSHIP_START_RE.match(line)
        if not match:
            continue

        name = next(group for group in match.groups() if group)
        end_index = detect_block_end(lines, index)
        block_lines = lines[index:end_index]
        block_text = "".join(block_lines)

        info = RelationshipInfo(
            name=name,
            file_path=file_path,
            start_line=index + 1,
            end_line=end_index,
            raw_block=block_text,
        )

        for block_line in block_lines[1:]:
            stripped = block_line.strip()
            if stripped.startswith("fromColumn:"):
                info.from_column = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("toColumn:"):
                info.to_column = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("isActive:"):
                info.is_active = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("crossFilteringBehavior:"):
                info.cross_filtering = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("securityFilteringBehavior:"):
                info.security_filtering = stripped.split(":", 1)[1].strip()

        relationships.append(info)

    return relationships


def scan_relationships(root: Path) -> list[RelationshipInfo]:
    relationships: list[RelationshipInfo] = []
    for file_path in root.rglob("*.tmdl"):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8-sig", errors="replace")
        relationships.extend(extract_relationships_from_text(text, file_path))
    relationships.sort(key=lambda item: (str(item.file_path).lower(), item.name.lower()))
    return relationships


class RelationshipViewer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TMDL Relationship Viewer")
        self.geometry("1200x720")
        self.minsize(1000, 600)

        default_root = Path(__file__).resolve().parents[2] / "summer_olympics_2024_dashboard.SemanticModel"
        if not default_root.exists():
            default_root = Path(__file__).resolve().parents[2] / "projet.SemanticModel"
        if not default_root.exists():
            default_root = Path.cwd()
        self.model_root = tk.StringVar(value=str(default_root))
        self.status_var = tk.StringVar(value="Choisis un dossier de modèle pour afficher les relations.")
        self.search_var = tk.StringVar()
        self.relationships: list[RelationshipInfo] = []
        self.filtered_relationships: list[RelationshipInfo] = []

        self._build_ui()
        self.refresh_relationships()

    def _build_ui(self) -> None:
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Treeview', rowheight=24, font=('Consolas', 10))
        self.style.configure('Treeview.Heading', font=('Consolas', 11, 'bold'))

        header = ttk.Frame(self, padding=12)
        header.pack(fill="x", background="#f0f0f0")

        ttk.Label(header, text="Dossier modèle", font=("Consolas", 10, "bold")).pack(side="left")
        root_entry = ttk.Entry(header, textvariable=self.model_root, width=72)
        root_entry.pack(side="left", padx=(10, 8), fill="x", expand=True)
        ttk.Button(header, text="Parcourir", command=self.choose_folder).pack(side="left", padx=(0, 4))
        ttk.Button(header, text="Rafraîchir", command=self.refresh_relationships).pack(side="left")

        search_bar = ttk.Frame(self, padding=(12, 8, 12, 8))
        search_bar.pack(fill="x")
        ttk.Label(search_bar, text="🔍 Filtrer").pack(side="left")
        search_entry = ttk.Entry(search_bar, textvariable=self.search_var)
        search_entry.pack(side="left", padx=(10, 8), fill="x", expand=True)
        search_entry.bind("<KeyRelease>", lambda _event: self.apply_filter())

        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.pack(fill="both", expand=True, padx=12, pady=8)

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=3)
        main.add(right, weight=2)

        columns = ("file", "from", "to", "active", "cross")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("file", text="📁 Fichier")
        self.tree.heading("from", text="📤 From")
        self.tree.heading("to", text="📥 To")
        self.tree.heading("active", text="✓ Active")
        self.tree.heading("cross", text="↔ Cross filter")
        self.tree.column("file", width=360, anchor="w")
        self.tree.column("from", width=220, anchor="w")
        self.tree.column("to", width=220, anchor="w")
        self.tree.column("active", width=80, anchor="center")
        self.tree.column("cross", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_relationship())

        tree_scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(fill="y", side="right")

        ttk.Label(right, text="📋 Détails", padding=(0, 0, 0, 6), font=("Consolas", 10, "bold")).pack(anchor="w")

        self.detail = tk.Text(right, wrap="word", height=12, font=("Consolas", 10), bg="#f9f9f9")
        self.detail.pack(fill="both", expand=True)
        self.detail.configure(state="disabled")

        edit_frame = ttk.LabelFrame(right, text="✎ Modifier", padding=8)
        edit_frame.pack(fill="x", pady=(8, 0))

        ttk.Label(edit_frame, text="Cross Filtering:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.cross_filter_var = tk.StringVar(value="")
        cross_combo = ttk.Combobox(
            edit_frame,
            textvariable=self.cross_filter_var,
            values=("oneDirection", "bothDirections"),
            state="readonly",
            width=20,
        )
        cross_combo.grid(row=0, column=1, sticky="w")

        ttk.Label(edit_frame, text="Is Active:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        self.is_active_var = tk.StringVar(value="")
        active_combo = ttk.Combobox(
            edit_frame, textvariable=self.is_active_var, values=("true", "false"), state="readonly", width=20
        )
        active_combo.grid(row=1, column=1, sticky="w", pady=(6, 0))

        btn_frame = ttk.Frame(edit_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(btn_frame, text="✓ Apply", command=self.apply_changes).pack(side="left", padx=(0, 4))
        ttk.Button(btn_frame, text="👁 Dry Run", command=self.dry_run_changes).pack(side="left")

        export_frame = ttk.LabelFrame(right, text="📤 Export", padding=8)
        export_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(export_frame, text="JSON", command=self.export_json).pack(side="left", padx=(0, 4))
        ttk.Button(export_frame, text="CSV", command=self.export_csv).pack(side="left")

        bottom = ttk.Label(self, textvariable=self.status_var, padding=(12, 4), font=("Consolas", 9))
        bottom.pack(fill="x", background="#e8e8e8")

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier du semantic model")
        if folder:
            self.model_root.set(folder)
            self.refresh_relationships()

    def refresh_relationships(self) -> None:
        root = Path(self.model_root.get()).expanduser()
        if not root.exists():
            self.relationships = []
            self.filtered_relationships = []
            self._render_tree()
            self._set_detail_text("Dossier introuvable.")
            self.status_var.set("Le dossier sélectionné n'existe pas.")
            return

        try:
            self.relationships = scan_relationships(root)
        except Exception as exc:  # noqa: BLE001 - show the problem in the UI instead of crashing.
            self.relationships = []
            self.filtered_relationships = []
            self._render_tree()
            self._set_detail_text(f"Erreur pendant le scan:\n{exc}")
            self.status_var.set("Erreur pendant l'analyse du modèle.")
            return

        self.apply_filter()
        if self.relationships:
            self.status_var.set(f"{len(self.relationships)} relation(s) trouvée(s) dans {root}.")
        else:
            self.status_var.set(f"Aucune relation trouvée dans {root}.")

    def apply_filter(self) -> None:
        query = self.search_var.get().strip().lower()
        if not query:
            self.filtered_relationships = list(self.relationships)
        else:
            self.filtered_relationships = [
                item
                for item in self.relationships
                if query in item.name.lower()
                or query in str(item.file_path).lower()
                or query in item.from_column.lower()
                or query in item.to_column.lower()
            ]
        self._render_tree()

    def _render_tree(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        for index, item in enumerate(self.filtered_relationships):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    str(item.file_path),
                    item.from_column,
                    item.to_column,
                    item.is_active or "",
                    item.cross_filtering or "",
                ),
            )

        if self.filtered_relationships:
            self.tree.selection_set("0")
            self.tree.focus("0")
            self.show_selected_relationship()
        else:
            self._set_detail_text("Aucune relation à afficher.")

    def show_selected_relationship(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        index = int(selection[0])
        if index >= len(self.filtered_relationships):
            return

        item = self.filtered_relationships[index]
        details = [
            f"Nom: {item.name}",
            f"Fichier: {item.file_path}",
            f"Lignes: {item.start_line}-{item.end_line}",
            f"From: {item.from_column or '-'}",
            f"To: {item.to_column or '-'}",
            f"isActive: {item.is_active or '-'}",
            f"crossFilteringBehavior: {item.cross_filtering or '-'}",
            f"securityFilteringBehavior: {item.security_filtering or '-'}",
            "",
            "Bloc TMDL:",
            item.raw_block.rstrip(),
        ]
        self._set_detail_text("\n".join(details))
        self.cross_filter_var.set(item.cross_filtering or "")
        self.is_active_var.set(item.is_active or "")

    def apply_changes(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Aucune relation sélectionnée.")
            return

        index = int(selection[0])
        if index >= len(self.filtered_relationships):
            return

        item = self.filtered_relationships[index]
        cross_filter = self.cross_filter_var.get().strip()
        is_active = self.is_active_var.get().strip()

        if not cross_filter and not is_active:
            messagebox.showinfo("Info", "Aucun changement à appliquer.")
            return

        script = Path(__file__).resolve().parents[0] / "update_tmdl_relationship.py"
        if not script.exists():
            messagebox.showerror("Erreur", f"Script non trouvé: {script}")
            return

        cmd = ["python", str(script), str(item.file_path), item.name]
        if cross_filter:
            cmd.extend(["--cross-filtering", cross_filter])
        if is_active:
            cmd.extend(["--is-active", is_active])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            messagebox.showinfo("Succès", f"Relation '{item.name}' modifiée avec succès!")
            self.refresh_relationships()
        except subprocess.CalledProcessError as exc:
            messagebox.showerror("Erreur", f"Modification échouée:\n{exc.stderr}")

    def dry_run_changes(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Aucune relation sélectionnée.")
            return

        index = int(selection[0])
        if index >= len(self.filtered_relationships):
            return

        item = self.filtered_relationships[index]
        cross_filter = self.cross_filter_var.get().strip()
        is_active = self.is_active_var.get().strip()

        if not cross_filter and not is_active:
            messagebox.showinfo("Info", "Aucun changement à prévisualiser.")
            return

        script = Path(__file__).resolve().parents[0] / "update_tmdl_relationship.py"
        if not script.exists():
            messagebox.showerror("Erreur", f"Script non trouvé: {script}")
            return

        cmd = ["python", str(script), str(item.file_path), item.name, "--dry-run"]
        if cross_filter:
            cmd.extend(["--cross-filtering", cross_filter])
        if is_active:
            cmd.extend(["--is-active", is_active])

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            preview_window = tk.Toplevel(self)
            preview_window.title("Dry Run Preview")
            preview_window.geometry("800x600")
            text = tk.Text(preview_window, wrap="word", font=("Consolas", 10))
            text.pack(fill="both", expand=True, padx=8, pady=8)
            text.insert("1.0", result.stdout)
            text.configure(state="disabled")
        except subprocess.CalledProcessError as exc:
            messagebox.showerror("Erreur", f"Dry run échoué:\n{exc.stderr}")

    def export_json(self) -> None:
        if not self.relationships:
            messagebox.showwarning("Attention", "Aucune relation à exporter.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="relationships.json"
        )
        if not file_path:
            return
        
        data = []
        for rel in self.relationships:
            data.append({
                "name": rel.name,
                "file": str(rel.file_path),
                "from_column": rel.from_column,
                "to_column": rel.to_column,
                "is_active": rel.is_active,
                "cross_filtering_behavior": rel.cross_filtering_behavior,
            })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.status_var.set(f"✓ Exported {len(data)} relations to {Path(file_path).name}")
        messagebox.showinfo("Succès", f"{len(data)} relations exported to {Path(file_path).name}")

    def export_csv(self) -> None:
        if not self.relationships:
            messagebox.showwarning("Attention", "Aucune relation à exporter.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="relationships.csv"
        )
        if not file_path:
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "File", "From Column", "To Column", "Active", "Cross Filter"])
            for rel in self.relationships:
                writer.writerow([rel.name, rel.file_path, rel.from_column, rel.to_column, rel.is_active, rel.cross_filtering_behavior])
        
        self.status_var.set(f"✓ Exported {len(self.relationships)} relations to {Path(file_path).name}")
        messagebox.showinfo("Succès", f"{len(self.relationships)} relations exported to {Path(file_path).name}")

    def _set_detail_text(self, text: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert("1.0", text)
        self.detail.configure(state="disabled")


def main() -> int:
    app = RelationshipViewer()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())