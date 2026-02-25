import json
from pathlib import Path


class DataLoader:
    """
    All JSON reading and parsing in one place.
    No component ever touches the JSON file directly.
    """

    _cache = {}

    @classmethod
    def load_industry(cls, industry: str) -> dict:
        """
        Loads and caches industry JSON.

        # FUTURE INTEGRATION POINT: replace with FastAPI call
        # return requests.get(f"/api/industry/{industry}").json()
        """
        key = industry.lower()
        if key in cls._cache:
            return cls._cache[key]
        path = Path(f"data/{key}.json")
        with open(path) as f:
            data = json.load(f)
        cls._cache[key] = data
        return data

    @classmethod
    def get_function(cls, industry: str, function_id: str) -> dict:
        data = cls.load_industry(industry)
        return next((f for f in data["functions"] if f["id"] == function_id), None)

    @classmethod
    def get_subfunction(cls, industry: str, function_id: str, subfunction_id: str) -> dict:
        function = cls.get_function(industry, function_id)
        if not function:
            return None
        return next(
            (sf for sf in function["subfunctions"] if sf["id"] == subfunction_id),
            None
        )

    @classmethod
    def get_all_functions(cls, industry: str) -> list:
        data = cls.load_industry(industry)
        return data.get("functions", [])
