"""Automatic documentation generator."""
import json
from datetime import datetime
from typing import Dict, Any, List
from etl_app.core.models.pipeline import StepType


class DocumentationGenerator:
    def generate_data_lineage(self, project: Any,
                               project_config: Dict[str, Any]) -> str:
        """Generate data lineage markdown document."""
        steps = project_config.get("pipeline", {}).get("steps", {})
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        lines = [
            f"# Data Lineage — {project.name}",
            f"",
            f"> Generated: {now}",
            f"",
            f"## Overview",
            f"",
            f"```",
            f"Source CSV → [{steps.get('staging',{}).get('config',{}).get('table_name','sta.*')}] → "
            f"[{steps.get('ods',{}).get('config',{}).get('table_name','ods.*')}] → DWH",
            f"```",
            f"",
        ]

        # Source
        ingestion = steps.get(StepType.INGESTION.value, {}).get("config", {})
        lines += [
            "## 1. Source",
            "",
            f"| Attribut | Valeur |",
            f"|----------|--------|",
            f"| Fichier | `{ingestion.get('file_path', 'N/A')}` |",
            f"| Délimiteur | `{ingestion.get('delimiter', ';')}` |",
            f"| Encodage | `{ingestion.get('encoding', 'utf-8-sig')}` |",
            f"| En-tête | `{ingestion.get('has_header', True)}` |",
            "",
        ]

        # Staging
        staging = steps.get(StepType.STAGING.value, {}).get("config", {})
        if staging.get("table_name"):
            cols = staging.get("selected_columns", [])
            lines += [
                "## 2. Staging",
                "",
                f"**Table** : `sta.{staging['table_name']}`",
                "",
                "| Colonne | Type | Taille |",
                "|---------|------|--------|",
            ]
            for col in cols:
                lines.append(f"| {col} | VARCHAR | 4000 |")
            lines.append("")

        # ODS
        ods = steps.get(StepType.ODS.value, {}).get("config", {})
        if ods.get("table_name"):
            mappings = ods.get("column_mappings", [])
            calcs = ods.get("calculated_columns", [])
            lines += [
                "## 3. ODS",
                "",
                f"**Table** : `ods.{ods['table_name']}`",
                "",
                "| Colonne | Type | Taille | Source | Calcul | Renommage |",
                "|---------|------|--------|--------|--------|-----------|",
            ]
            for m in mappings:
                src = m.get("source_column", "")
                tgt = m.get("target_column", src)
                t = m.get("target_type", "NVARCHAR")
                sz = m.get("target_size", 500)
                renamed = f"{src} → {tgt}" if src != tgt else "-"
                transform = m.get("transformation", "-") or "-"
                lines.append(f"| {tgt} | {t} | {sz} | {src} | {transform} | {renamed} |")
            for calc in calcs:
                lines.append(
                    f"| {calc['name']} | calculé | - | - | `{calc['expression'][:60]}` | - |"
                )
            lines.append("")

        # Dimension
        dim = steps.get(StepType.DIMENSION.value, {}).get("config", {})
        if dim.get("table_name"):
            lines += [
                "## 4. Dimension",
                "",
                f"**Table** : `dim.{dim['table_name']}`  ",
                f"**Mode** : {dim.get('load_mode', 'insert')}  ",
                f"**Clé métier** : {', '.join(dim.get('business_key_columns', []))}  ",
                f"**Colonnes surveillées** : {', '.join(dim.get('tracked_columns', []))}",
                "",
                "| Colonne | Type | Taille | Origine | Rôle |",
                "|---------|------|--------|---------|------|",
            ]
            sk = dim.get("surrogate_key_column", "sk_id")
            if dim.get("use_surrogate_key"):
                lines.append(f"| {sk} | INT IDENTITY | - | Généré | Surrogate Key |")
            for col in dim.get("selected_columns", []):
                role = "Business Key" if col in dim.get("business_key_columns", []) else \
                       "Surveillée" if col in dim.get("tracked_columns", []) else "Attribut"
                lines.append(f"| {col} | NVARCHAR | 500 | ODS | {role} |")
            lines.append("")

        # Fact
        fact = steps.get(StepType.FACT.value, {}).get("config", {})
        if fact.get("table_name"):
            joins = fact.get("joins", [])
            lines += [
                "## 5. Table de Faits",
                "",
                f"**Table** : `fait.{fact['table_name']}`  ",
                f"**Jointures** : {len(joins)}",
                "",
                "### Jointures",
                "",
                "| Dimension | Clé source | Clé dimension | SK résultant |",
                "|-----------|-----------|---------------|--------------|",
            ]
            for j in joins:
                for k in j.get("join_keys", []):
                    alias = j.get("alias") or f"dim_{j['dimension_table']}"
                    lines.append(
                        f"| {j['dimension_schema']}.{j['dimension_table']} "
                        f"| {k.get('source','')} | {k.get('dimension','')} "
                        f"| {alias}_{j.get('surrogate_key_column','sk_id')} |"
                    )
            lines.append("")

        return "\n".join(lines)

    def generate_metrics(self, project: Any,
                          project_config: Dict[str, Any]) -> str:
        """Generate metrics JSON."""
        steps = project_config.get("pipeline", {}).get("steps", {})
        staging_cfg = steps.get(StepType.STAGING.value, {}).get("config", {})
        ods_cfg = steps.get(StepType.ODS.value, {}).get("config", {})
        dim_cfg = steps.get(StepType.DIMENSION.value, {}).get("config", {})
        fact_cfg = steps.get(StepType.FACT.value, {}).get("config", {})

        metrics = {
            "project": project.name,
            "generated_at": datetime.utcnow().isoformat(),
            "staging": {
                "table_count": 1 if staging_cfg.get("table_name") else 0,
                "tables": [staging_cfg["table_name"]] if staging_cfg.get("table_name") else [],
            },
            "ods": {
                "table_count": 1 if ods_cfg.get("table_name") else 0,
                "tables": [ods_cfg["table_name"]] if ods_cfg.get("table_name") else [],
            },
            "datawarehouse": {
                "dimensions": {
                    "table_count": 1 if dim_cfg.get("table_name") else 0,
                    "tables": [f"dim.{dim_cfg['table_name']}"] if dim_cfg.get("table_name") else [],
                },
                "facts": {
                    "table_count": 1 if fact_cfg.get("table_name") else 0,
                    "tables": [f"fait.{fact_cfg['table_name']}"] if fact_cfg.get("table_name") else [],
                },
            },
        }
        return json.dumps(metrics, indent=2, ensure_ascii=False)

    def generate_mermaid_diagram(self, project: Any,
                                   project_config: Dict[str, Any]) -> str:
        """Generate Mermaid ER diagram."""
        steps = project_config.get("pipeline", {}).get("steps", {})
        staging_cfg = steps.get(StepType.STAGING.value, {}).get("config", {})
        ods_cfg = steps.get(StepType.ODS.value, {}).get("config", {})
        dim_cfg = steps.get(StepType.DIMENSION.value, {}).get("config", {})
        fact_cfg = steps.get(StepType.FACT.value, {}).get("config", {})

        lines = ["erDiagram"]

        if fact_cfg.get("table_name"):
            fact = fact_cfg["table_name"].upper()
            fact_cols = "\n        ".join(
                f"int {col}" for col in fact_cfg.get("selected_columns", [])[:5]
            )
            lines.append(f"    {fact} {{")
            if fact_cols:
                lines.append(f"        {fact_cols}")
            lines.append("    }")

            for j in fact_cfg.get("joins", []):
                dim = j["dimension_table"].upper()
                sk = j.get("surrogate_key_column", "sk_id")
                lines.append(f"    {dim} {{")
                lines.append(f"        int {sk} PK")
                for col in dim_cfg.get("selected_columns", [])[:3]:
                    lines.append(f"        string {col}")
                lines.append("    }")
                lines.append(f"    {fact} }}|--|| {dim} : \"FK_{sk}\"")

        if ods_cfg.get("table_name") and staging_cfg.get("table_name"):
            lines.append(
                f"    STA_{staging_cfg['table_name'].upper()} ||--|| "
                f"ODS_{ods_cfg['table_name'].upper()} : \"transforms\""
            )

        return "\n".join(lines)
