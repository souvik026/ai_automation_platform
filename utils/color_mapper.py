import numpy as np


# Fixed colors — only 3 tiers
COLOR_HIGH   = "#1A7A4A"   # Deep green  — top 20%
COLOR_MEDIUM = "#52B788"   # Light green — next 40%
COLOR_LOW    = "#F4C542"   # Yellow      — bottom 40%
COLOR_DEFAULT = COLOR_LOW  # fallback before calibration

LABEL_HIGH   = "High"
LABEL_MEDIUM = "Medium"
LABEL_LOW    = "Low"


class ColorMapper:
    """
    Percentile-based color and label logic, calibrated per industry.

    Tiers (computed from all automation scores for that industry):
      Top 20%  → Deep Green  (#1A7A4A) — High Potential
      Next 40% → Light Green (#52B788) — Medium Potential
      Bot 40%  → Yellow      (#F4C542) — Low Potential

    Usage:
        ColorMapper.calibrate(all_scores)   # call once per industry load
        ColorMapper.get_color(score)
        ColorMapper.get_label(score)
    """

    # Per-industry calibration: maps industry_key → (p80_threshold, p40_threshold)
    # p80 = 80th percentile (top 20% are above this)
    # p40 = 40th percentile (bottom 40% are below this)
    _thresholds: dict = {}
    _active_industry: str = "_default"

    # Default thresholds before any calibration (1–5 scale)
    _default_p80: float = 4.0
    _default_p40: float = 3.0

    @classmethod
    def calibrate(cls, scores: list, industry_key: str = "_default") -> None:
        """
        Compute percentile thresholds from a list of scores for a given industry.
        Call this whenever industry data is loaded.
        """
        if not scores:
            return
        arr = np.array([s for s in scores if s is not None and not np.isnan(s)])
        if len(arr) == 0:
            return
        p80 = float(np.percentile(arr, 80))  # top 20% above this
        p40 = float(np.percentile(arr, 40))  # bottom 40% below this
        cls._thresholds[industry_key] = (p80, p40)
        cls._active_industry = industry_key

    @classmethod
    def set_active_industry(cls, industry_key: str) -> None:
        cls._active_industry = industry_key

    @classmethod
    def _get_thresholds(cls) -> tuple:
        return cls._thresholds.get(
            cls._active_industry,
            (cls._default_p80, cls._default_p40)
        )

    @classmethod
    def get_color(cls, score: float) -> str:
        if score is None:
            return COLOR_DEFAULT
        p80, p40 = cls._get_thresholds()
        if score >= p80:
            return COLOR_HIGH
        elif score >= p40:
            return COLOR_MEDIUM
        else:
            return COLOR_LOW

    @classmethod
    def get_label(cls, score: float) -> str:
        if score is None:
            return LABEL_LOW
        p80, p40 = cls._get_thresholds()
        if score >= p80:
            return LABEL_HIGH
        elif score >= p40:
            return LABEL_MEDIUM
        else:
            return LABEL_LOW

    @classmethod
    def get_color_and_label(cls, score: float) -> tuple:
        return cls.get_color(score), cls.get_label(score)