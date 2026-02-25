class ColorMapper:
    """
    All color and label logic lives here only.
    Colors use smooth gradient interpolation: green (low score) -> red (high score).
    High automation score = high automation POTENTIAL = more urgent/valuable = red end.
    """

    # Score bands for labels only (colors are now interpolated)
    SCORE_BANDS = [
        (18, 20, "Very High"),
        (14, 17, "High"),
        (9,  13, "Medium"),
        (0,   8, "Lower"),
    ]

    # Gradient stops: score 0 = green, score 20 = red
    # Format: (score, R, G, B)
    GRADIENT = [
    (0,  180, 30,  20),   # deep red   (lowest automation)
    (3,  192, 57,  43),   # red-orange
    (6,  230, 126, 34),   # orange
    (11, 241, 196, 15),   # yellow
    (14, 88,  196, 98),   # mid-green
    (20, 39,  174, 96),   # green      (highest automation)
]

    @classmethod
    def _interpolate(cls, score: float) -> tuple:
        """Interpolates RGB values along the gradient for a given score (0-20)."""
        score = max(0, min(20, score))
        for i in range(len(cls.GRADIENT) - 1):
            s0, r0, g0, b0 = cls.GRADIENT[i]
            s1, r1, g1, b1 = cls.GRADIENT[i + 1]
            if s0 <= score <= s1:
                t = (score - s0) / (s1 - s0) if s1 != s0 else 0
                r = int(r0 + t * (r1 - r0))
                g = int(g0 + t * (g1 - g0))
                b = int(b0 + t * (b1 - b0))
                return (r, g, b)
        return (180, 30, 20)

    @classmethod
    def get_color(cls, score: float) -> str:
        """Returns smooth gradient hex color for a given automation score."""
        r, g, b = cls._interpolate(score)
        return f"#{r:02X}{g:02X}{b:02X}"

    @classmethod
    def get_label(cls, score: float) -> str:
        """Returns human-readable potential label for a score."""
        for low, high, label in cls.SCORE_BANDS:
            if low <= score <= high:
                return label
        return "Lower"

    @classmethod
    def get_legend(cls) -> list:
        """Returns gradient legend stops for rendering in UI."""
        stops = [
            (0,  "Low"),
            (5,  ""),
            (10, "Medium"),
            (15, ""),
            (20, "Very High"),
        ]
        return [{"color": cls.get_color(s), "label": l, "score": s} for s, l in stops]
