import pandas as pd
from pathlib import Path
from utils.color_mapper import ColorMapper


class DataLoader:
    """
    Reads backend_data.xlsx from the data/ folder.
    Converts it into the same dict structure the app expects.
    No component ever touches the file directly.

    Expected Excel columns:
        Industry, L1 Function, L2 Function,
        Refined Role, Cost as % Total Revenue Refined, Automation Score
    """

    _cache = {}

    COL_INDUSTRY   = "Industry"
    COL_L1         = "L1 Function"
    COL_L2         = "L2 Function"
    COL_ROLE       = "Refined Role"
    COL_COST       = "Cost as % Total Revenue Refined"
    COL_SCORE      = "Automation Score"

    @classmethod
    def _load_excel(cls) -> pd.DataFrame:
        path = Path("data/Backend_data.xlsx")
        df = pd.read_excel(path)

        df.columns = df.columns.str.strip()

        df[cls.COL_COST] = (
            df[cls.COL_COST]
            .astype(str)
            .str.replace("%", "", regex=False)
            .str.strip()
            .astype(float)
        )

        # Convert decimal to percentage if stored as 0.055 instead of 5.5
        if df[cls.COL_COST].max() < 1.0:
            df[cls.COL_COST] = df[cls.COL_COST] * 100

        df[cls.COL_SCORE] = pd.to_numeric(df[cls.COL_SCORE], errors="coerce").fillna(1.0)

        return df

    @classmethod
    def _get_df(cls) -> pd.DataFrame:
        if "_df" not in cls._cache:
            cls._cache["_df"] = cls._load_excel()
        return cls._cache["_df"]

    @classmethod
    def get_available_industries(cls) -> list:
        df = cls._get_df()
        return sorted(df[cls.COL_INDUSTRY].dropna().unique().tolist())

    @classmethod
    def load_industry(cls, industry: str, revenue_m: float = None) -> dict:
        """
        Returns industry data in the same structure the app expects.
        If revenue_m is provided (company revenue in M USD), computes
        absolute_cost_m = cost_pct_revenue * revenue_m / 100 for each subfunction.

        # FUTURE INTEGRATION POINT: replace _load_excel() with API call
        # df = requests.get(f"/api/data?industry={industry}").json()
        """
        cache_key = f"{industry.lower()}_{revenue_m}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        df = cls._get_df()
        df_ind = df[df[cls.COL_INDUSTRY].str.strip() == industry.strip()].copy()

        functions = []
        for l1_name, l1_group in df_ind.groupby(cls.COL_L1, sort=False):
            l1_id = cls._to_id(l1_name)
            subfunctions = []

            for _, row in l1_group.iterrows():
                l2_name = str(row[cls.COL_L2]).strip()
                score = float(row[cls.COL_SCORE])
                cost = float(row[cls.COL_COST])
                role = str(row.get(cls.COL_ROLE, "")).strip()

                absolute_cost_m = round(cost * revenue_m / 100, 2) if revenue_m else None

                subfunctions.append({
                    "id": cls._to_id(l2_name),
                    "name": l2_name,
                    "unit_cost_per_1000": cost,
                    "cost_pct_revenue": cost,
                    "absolute_cost_m": absolute_cost_m,
                    "fte_pct_headcount": 0.0,
                    "automation_score": score,
                    "role_description": role,
                    "automation_scores": {"score": score},
                })

            functions.append({
                "id": l1_id,
                "name": str(l1_name).strip(),
                "subfunctions": subfunctions,
            })

        # Calibrate color thresholds for this industry using all automation scores
        all_scores = [
            sf["automation_score"]
            for f in functions
            for sf in f["subfunctions"]
        ]
        ColorMapper.calibrate(all_scores, industry_key=industry.lower())
        ColorMapper.set_active_industry(industry.lower())

        result = {"industry": industry, "functions": functions, "revenue_m": revenue_m}
        cls._cache[cache_key] = result
        return result

    @classmethod
    def get_function(cls, industry: str, function_id: str) -> dict:
        data = cls.load_industry(industry)
        return next(
            (f for f in data["functions"] if f["id"] == function_id),
            None
        )

    @classmethod
    def get_subfunction(cls, industry: str, function_id: str, subfunction_id: str) -> dict:
        function = cls.get_function(industry, function_id)
        if not function:
            return None
        return next(
            (sf for sf in function["subfunctions"] if sf["id"] == subfunction_id),
            None
        )

    @staticmethod
    def _to_id(name: str) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")