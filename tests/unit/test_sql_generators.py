"""Unit tests for SQL generators."""
import pytest
from etl_app.etl.steps.staging import StagingStep
from etl_app.etl.steps.ods import OdsStep
from etl_app.etl.steps.dimension import DimensionStep
from etl_app.etl.steps.fact import FactStep


class TestStagingGenerator:
    def test_generate_sql_contains_table_name(self):
        step = StagingStep(conn_str="")
        config = {"table_name": "sta_ventes", "selected_columns": ["col1", "col2"]}
        sql = step.generate_sql(config)
        assert "sta_ventes" in sql
        assert "VARCHAR(4000)" in sql
        assert "col1" in sql

    def test_generate_sql_has_drop_create(self):
        step = StagingStep(conn_str="")
        config = {"table_name": "test", "selected_columns": ["a"]}
        sql = step.generate_sql(config)
        assert "DROP TABLE" in sql
        assert "CREATE TABLE" in sql


class TestOdsGenerator:
    def test_generate_sql_with_mappings(self):
        step = OdsStep(conn_str="")
        config = {
            "table_name": "ods_ventes",
            "source_staging_table": "sta_ventes",
            "column_mappings": [
                {"source_column": "COL_A", "target_column": "col_a",
                 "transformation": None}
            ],
        }
        sql = step.generate_sql(config)
        assert "ods_ventes" in sql
        assert "sta_ventes" in sql

    def test_generate_sql_with_filter(self):
        step = OdsStep(conn_str="")
        config = {
            "table_name": "ods_t",
            "source_staging_table": "sta_t",
            "column_mappings": [],
            "filters": [{"expression": "montant > 0", "expression_type": "sql"}],
        }
        sql = step.generate_sql(config)
        assert "WHERE" in sql
        assert "montant > 0" in sql


class TestDimensionGenerator:
    def test_insert_mode(self):
        step = DimensionStep(conn_str="")
        config = {
            "table_name": "dim_produit",
            "source_ods_table": "ods_produit",
            "load_mode": "insert",
            "selected_columns": ["code", "libelle"],
        }
        sql = step.generate_sql(config)
        assert "INSERT INTO" in sql
        assert "dim_produit" in sql

    def test_merge_mode(self):
        step = DimensionStep(conn_str="")
        config = {
            "table_name": "dim_produit",
            "source_ods_table": "ods_produit",
            "load_mode": "merge",
            "business_key_columns": ["code"],
            "tracked_columns": ["libelle"],
            "selected_columns": ["code", "libelle"],
        }
        sql = step.generate_sql(config)
        assert "MERGE" in sql
        assert "WHEN MATCHED" in sql
        assert "WHEN NOT MATCHED" in sql


class TestFactGenerator:
    def test_generate_sql_with_joins(self):
        step = FactStep(conn_str="")
        config = {
            "table_name": "fait_ventes",
            "source_ods_table": "ods_ventes",
            "selected_columns": ["montant"],
            "joins": [
                {
                    "dimension_schema": "dim",
                    "dimension_table": "dim_produit",
                    "surrogate_key_column": "sk_id",
                    "join_keys": [{"source": "code_produit", "dimension": "code"}],
                }
            ],
        }
        sql = step.generate_sql(config)
        assert "fait_ventes" in sql
        assert "dim_produit" in sql
        assert "LEFT JOIN" in sql
