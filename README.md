# ETL Manager

Application web locale Python pour remplacer SSIS dans les pipelines ETL.
Interface graphique moderne avec thème sombre/clair, pipeline en 6 étapes,
génération automatique de SQL/documentation, versioning YAML Git-friendly.

## Démarrage rapide

```bash
# 1. Créer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate    # Windows
# ou: source .venv/bin/activate  (Linux/Mac)

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. (Optionnel) Configurer l'environnement
copy .env.example .env
# Éditer .env selon vos besoins

# 4. Lancer l'application
python main.py

# 5. Ouvrir dans le navigateur
#    http://localhost:8000
```

## Architecture

```
etl_app/
├── api/              # FastAPI routes + application factory
│   └── routes/       # Endpoints REST + routes UI (HTML)
├── core/
│   ├── models/       # Modèles SQLAlchemy (ORM) + Pydantic
│   ├── repositories/ # Couche d'accès aux données (Repository pattern)
│   ├── services/     # Logique métier (ProjectService, CsvService…)
│   └── viewmodels/   # MVVM ViewModels (bridge service ↔ UI)
├── database/         # Base SQLite + initialisation schéma
├── etl/
│   ├── steps/        # Étapes ETL (Ingestion, Staging, ODS, Dim, Fait, Post)
│   └── generators/   # Générateurs SQL + Documentation
├── config/           # Paramètres (Pydantic Settings)
└── ui/
    ├── static/       # CSS, JS, images
    └── templates/    # Jinja2 (Tailwind CSS + Alpine.js + HTMX)
```

## Pipeline ETL — 6 étapes

| # | Étape | Description |
|---|-------|-------------|
| 1 | **Ingestion CSV** | Lecture, détection format, prévisualisation paginée |
| 2 | **Staging** | Chargement `sta.*` en VARCHAR(4000), TRUNCATE + batch insert |
| 3 | **ODS** | Mapping, renommage, calculs Python/SQL, typage, indexation |
| 4 | **Dimensions** | Mode INSERT ou MERGE/UPSERT avec clé métier |
| 5 | **Table de Faits** | Jointures dimensions, récupération SK |
| 6 | **Post-traitement** | Déplacement fichier Entrée → Sortie si succès |

## Fonctionnalités

- **CRUD complet** projets, connexions SQL Server
- **Multi-environnements** : DEV, PREPROD, RECETTE, PROD
- **Dry-run** : simulation complète sans écriture SQL Server
- **Documentation auto** : Data Lineage (Markdown), Métriques (JSON), Schéma ER (Mermaid)
- **Export ZIP** : archive Git-friendly du projet (YAML + SQL)
- **Thème sombre/clair** persisté dans localStorage
- **Chiffrement** des mots de passe (Fernet/AES-256)
- **Logs structurés** par exécution avec niveaux DEBUG/INFO/WARNING/ERROR

## Tests

```bash
pytest                    # Tous les tests
pytest tests/unit/        # Tests unitaires seulement
pytest -v --tb=long       # Mode verbeux
```

## Structure des projets (Git-friendly)

```
projects/
└── MON_PROJET/
    ├── project.yaml                        # Config principale
    ├── schemas/
    │   ├── staging_tables.json
    │   ├── ods_tables.json
    │   └── dwh_tables.json
    ├── transformations/
    │   ├── staging/load_staging.sql
    │   ├── ods/transformations.sql
    │   └── dwh/
    │       ├── dimensions/dim_*.sql
    │       └── facts/fact_*.sql
    └── documentation/
        ├── data_lineage.md
        ├── metrics.json
        └── schema_diagram.mmd
```
