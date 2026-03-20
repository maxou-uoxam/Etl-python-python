"""CSV analysis and preview service."""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from loguru import logger


COMMON_DELIMITERS = [";", ",", "\t", "|"]
COMMON_ENCODINGS = ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]


class CsvService:
    def detect_format(self, file_path: str) -> Dict[str, Any]:
        """Auto-detect CSV delimiter and encoding."""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        # Detect encoding
        encoding = self._detect_encoding(path)
        delimiter = self._detect_delimiter(path, encoding)

        return {
            "delimiter": delimiter,
            "encoding": encoding,
            "has_header": True,
            "file_size_mb": round(path.stat().st_size / 1024 / 1024, 2),
        }

    def _detect_encoding(self, path: Path) -> str:
        sample = path.read_bytes()[:4096]
        for enc in COMMON_ENCODINGS:
            try:
                sample.decode(enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue
        return "utf-8-sig"

    def _detect_delimiter(self, path: Path, encoding: str) -> str:
        try:
            with open(path, encoding=encoding, errors="replace") as f:
                sample = "".join(f.readline() for _ in range(5))
        except Exception:
            return ";"

        counts = {d: sample.count(d) for d in COMMON_DELIMITERS}
        return max(counts, key=counts.get)

    def get_preview(
        self,
        file_path: str,
        delimiter: str = ";",
        encoding: str = "utf-8-sig",
        has_header: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Read CSV and return paginated preview."""
        try:
            df = pd.read_csv(
                file_path,
                sep=delimiter,
                encoding=encoding,
                header=0 if has_header else None,
                dtype=str,
                keep_default_na=False,
                on_bad_lines="skip",
                nrows=10000,  # Cap for preview
            )
        except Exception as e:
            return {"error": str(e), "columns": [], "rows": [], "total_rows": 0}

        total_rows = len(df)
        start = (page - 1) * page_size
        end = start + page_size
        page_df = df.iloc[start:end]

        return {
            "columns": list(df.columns),
            "rows": page_df.values.tolist(),
            "total_rows": total_rows,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_rows + page_size - 1) // page_size,
        }

    def detect_column_types(
        self,
        file_path: str,
        delimiter: str = ";",
        encoding: str = "utf-8-sig",
        sample_size: int = 1000,
    ) -> Dict[str, Dict[str, Any]]:
        """Detect column types and compute max sizes."""
        try:
            df = pd.read_csv(
                file_path,
                sep=delimiter,
                encoding=encoding,
                dtype=str,
                keep_default_na=False,
                nrows=sample_size,
            )
        except Exception as e:
            return {}

        result = {}
        for col in df.columns:
            series = df[col].dropna()
            max_len = int(series.str.len().max()) if len(series) > 0 else 10
            # Apply +30% sizing rule
            suggested_size = max(10, int(max_len * 1.3))
            detected_type = self._infer_type(series)
            result[col] = {
                "detected_type": detected_type,
                "max_length": max_len,
                "suggested_size": suggested_size,
                "null_count": int(df[col].isna().sum()),
                "sample_values": series.head(3).tolist(),
            }
        return result

    def _infer_type(self, series: "pd.Series") -> str:
        """Infer Python/SQL type from string series."""
        if series.empty:
            return "VARCHAR"
        sample = series.dropna().head(100)

        # Try integer
        try:
            sample.astype(int)
            return "INT"
        except (ValueError, TypeError):
            pass

        # Try float
        try:
            sample.str.replace(",", ".").astype(float)
            return "DECIMAL"
        except (ValueError, TypeError):
            pass

        # Try date
        date_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2}|^\d{2}/\d{2}/\d{4}|^\d{2}-\d{2}-\d{4}"
        )
        if sample.str.match(date_pattern).mean() > 0.8:
            return "DATE"

        return "VARCHAR"

    def list_csv_files(self, folder: str,
                        pattern: str = "*.csv") -> List[Dict[str, Any]]:
        """List CSV files in a folder."""
        path = Path(folder)
        if not path.exists():
            return []
        files = []
        for f in sorted(path.glob(pattern)):
            files.append({
                "name": f.name,
                "path": str(f),
                "size_mb": round(f.stat().st_size / 1024 / 1024, 2),
            })
        return files
