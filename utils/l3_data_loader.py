import pandas as pd
from pathlib import Path


class L3DataLoader:
    """
    Reads Backend_data_2.xlsx from the data/ folder.
    Provides L3 breakdown data keyed by (industry, l1, l2).
    """

    _cache = {}

    COL_INDUSTRY   = "industry"
    COL_L1         = "l1_function"
    COL_L2         = "l2_function"
    COL_L3         = "l3_function"
    COL_DESC       = "description"
    COL_AI_SCORE   = "AI Score"

    SCORE_COLS = [
        ("data_availability_score",       "data_availability_label",       "data_availability_reason"),
        ("task_pattern_density_score",     "task_pattern_density_label",     "task_pattern_density_reason"),
        ("error_tolerance_score",          "error_tolerance_label",          "error_tolerance_reason"),
        ("regulatory_complexity_score",    "regulatory_complexity_label",    "regulatory_complexity_reason"),
        ("implementation_barriers_score",  "implementation_barriers_label",  "implementation_barriers_reason"),
    ]

    DIMENSION_NAMES = [
        "Data Availability",
        "Task Pattern Density",
        "Error Tolerance",
        "Regulatory Complexity",
        "Implementation Barriers",
    ]

    @classmethod
    def _load_excel(cls) -> pd.DataFrame:
        path = Path("data/Backend_data_2.xlsx")
        df = pd.read_excel(path)
        df.columns = df.columns.str.strip()
        # Normalize column names to lowercase for safety
        col_map = {c: c.strip() for c in df.columns}
        df = df.rename(columns=col_map)
        df[cls.COL_AI_SCORE] = pd.to_numeric(df[cls.COL_AI_SCORE], errors="coerce").fillna(1.0)
        for score_col, _, _ in cls.SCORE_COLS:
            if score_col in df.columns:
                df[score_col] = pd.to_numeric(df[score_col], errors="coerce").fillna(1.0)
        return df

    @classmethod
    def _get_df(cls) -> pd.DataFrame:
        if "_df" not in cls._cache:
            cls._cache["_df"] = cls._load_excel()
        return cls._cache["_df"]

    @classmethod
    def get_l3_functions(cls, industry: str, l1: str, l2: str) -> list:
        """
        Returns list of L3 function dicts for a given industry/l1/l2 combination.
        """
        cache_key = f"l3_{industry}_{l1}_{l2}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        df = cls._get_df()
        mask = (
            df[cls.COL_INDUSTRY].str.strip().str.lower() == industry.strip().lower()
        ) & (
            df[cls.COL_L1].str.strip().str.lower() == l1.strip().lower()
        ) & (
            df[cls.COL_L2].str.strip().str.lower() == l2.strip().lower()
        )
        subset = df[mask].copy()

        result = []
        for _, row in subset.iterrows():
            dimensions = []
            for (score_col, label_col, reason_col), dim_name in zip(cls.SCORE_COLS, cls.DIMENSION_NAMES):
                dimensions.append({
                    "name": dim_name,
                    "score": float(row.get(score_col, 1)),
                    "label": str(row.get(label_col, "")),
                    "reason": str(row.get(reason_col, "")),
                })

            result.append({
                "name": str(row[cls.COL_L3]).strip(),
                "description": str(row.get(cls.COL_DESC, "")).strip(),
                "ai_score": float(row[cls.COL_AI_SCORE]),
                "dimensions": dimensions,
            })

        cls._cache[cache_key] = result
        return result

    @classmethod
    def get_l3_by_name(cls, industry: str, l1: str, l2: str, l3_name: str) -> dict:
        l3s = cls.get_l3_functions(industry, l1, l2)
        return next((l for l in l3s if l["name"].lower() == l3_name.lower()), None)