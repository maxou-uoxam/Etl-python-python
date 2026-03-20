"""Unit tests for CsvService."""
import io
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from etl_app.core.services.csv_service import CsvService


class TestCsvService:
    def setup_method(self):
        self.svc = CsvService()

    def test_infer_type_int(self):
        series = pd.Series(["1", "2", "3", "100"])
        assert self.svc._infer_type(series) == "INT"

    def test_infer_type_decimal(self):
        series = pd.Series(["1.5", "2.3", "3.14"])
        assert self.svc._infer_type(series) == "DECIMAL"

    def test_infer_type_date(self):
        series = pd.Series(["2024-01-01", "2024-12-31"])
        assert self.svc._infer_type(series) == "DATE"

    def test_infer_type_varchar(self):
        series = pd.Series(["hello", "world", "foo bar"])
        assert self.svc._infer_type(series) == "VARCHAR"

    def test_detect_delimiter_semicolon(self):
        from pathlib import Path
        import tempfile, os

        content = "col1;col2;col3\n1;2;3\n4;5;6"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv',
                                          delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp = f.name
        try:
            result = self.svc.detect_format(tmp)
            assert result["delimiter"] == ";"
        finally:
            os.unlink(tmp)

    def test_get_preview_columns(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("nom;age;ville\nAlice;30;Paris\nBob;25;Lyon\n",
                             encoding="utf-8")
        result = self.svc.get_preview(str(csv_file), delimiter=";")
        assert result["columns"] == ["nom", "age", "ville"]
        assert result["total_rows"] == 2

    def test_get_preview_nonexistent(self):
        result = self.svc.get_preview("/nonexistent/path.csv")
        assert "error" in result

    def test_column_types_sizing(self, tmp_path):
        csv_file = tmp_path / "types.csv"
        csv_file.write_text("id;name\n1;Alice\n2;Bob\n", encoding="utf-8")
        result = self.svc.detect_column_types(str(csv_file))
        assert "id" in result
        assert "name" in result
        # +30% rule
        assert result["name"]["suggested_size"] >= result["name"]["max_length"]
