class ColorMapper:
    """
    Score scale: 1 to 5
    Below 1.8        : Grey (minimal automation potential)
    1.8 and above    : Green gradient from light to dark
                       min score in dataset = lightest green
                       max score in dataset = darkest green
    No scores shown in UI — labels only.
    """

    GREY = "#7F8C8D"

    # Green gradient stops (score 1.8 = light, 5.0 = dark)
    GRADIENT_GREEN = [
        (1.8, 144, 238, 144),  # light green
        (2.5, 88,  196, 98),   # mid-light green
        (3.5, 55,  180, 90),   # mid green
        (4.5, 33,  160, 75),   # mid-dark green
        (5.0, 27,  142, 68),   # deep green
    ]

    # These get set dynamically per dataset
    _score_min = 1.8
    _score_max = 5.0

    @classmethod
    def calibrate(cls, all_scores: list):
        """
        Call this once after loading data, passing all
        automation scores in the dataset. Sets the min/max
        so the gradient stretches across the actual data range.
        """
        valid = [s for s in all_scores if s >= 1.8]
        if valid:
            cls._score_min = min(valid)
            cls._score_max = max(valid)
            # Avoid divide by zero if all scores are equal
            if cls._score_min == cls._score_max:
                cls._score_max = cls._score_min + 0.1

    @classmethod
    def get_color(cls, score: float) -> str:
        if score < 1.8:
            return cls.GREY

        # Normalise score to 0-1 within actual data range
        t = (score - cls._score_min) / (cls._score_max - cls._score_min)
        t = max(0.0, min(1.0, t))

        # Map t across green gradient stops
        g = cls.GRADIENT_GREEN
        # Use t to interpolate across the full gradient
        scaled = t * (len(g) - 1)
        idx = int(scaled)
        idx = min(idx, len(g) - 2)
        local_t = scaled - idx

        _, r0, g0, b0 = g[idx]
        _, r1, g1, b1 = g[idx + 1]

        r = int(r0 + local_t * (r1 - r0))
        gv = int(g0 + local_t * (g1 - g0))
        b = int(b0 + local_t * (b1 - b0))
        return f"#{r:02X}{gv:02X}{b:02X}"

    @classmethod
    def get_label(cls, score: float) -> str:
        if score < 1.8:
            return "Minimal"
        if score < 2.5:
            return "Low"
        if score < 3.5:
            return "Medium"
        if score < 4.5:
            return "High"
        return "Very High"

    @classmethod
    def get_legend(cls) -> list:
        return [
            {"color": cls.GREY,      "label": "Minimal"},
            {"color": "#90EE90",     "label": "Low"},
            {"color": "#58C462",     "label": "Medium"},
            {"color": "#37B05A",     "label": "High"},
            {"color": "#1B8E44",     "label": "Very High"},
        ]