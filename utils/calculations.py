from utils.color_mapper import ColorMapper


class AutomationCalculator:
    """
    All sizing and scoring logic.
    Now reads a single automation_score float (1-5 scale)
    instead of summing sub-criteria.
    """

    @staticmethod
    def get_automation_score(scores: dict) -> float:
        """
        Reads the single 'score' key from the scores dict.
        Kept for interface compatibility.
        """
        return float(scores.get("score", 1.0))

    @staticmethod
    def get_function_unit_cost(function: dict) -> float:
        """Sum of all subfunctions' unit_cost_per_1000."""
        return sum(sf["unit_cost_per_1000"] for sf in function["subfunctions"])

    @staticmethod
    def get_function_automation_score(function: dict) -> float:
        subfunctions = function["subfunctions"]
        if not subfunctions:
            return 1.0
        return sum(sf["automation_score"] for sf in subfunctions) / len(subfunctions)

    @staticmethod
    def build_function_treemap_data(industry_data: dict) -> dict:
        # Calibrate gradient to actual score range in this dataset
        all_scores = [
            sf["automation_score"]
            for func in industry_data["functions"]
            for sf in func["subfunctions"]
        ]
        ColorMapper.calibrate(all_scores)

        labels, parents, values, colors, customdata = [], [], [], [], []
        industry_name = industry_data["industry"]

        labels.append(industry_name)
        parents.append("")
        values.append(0)
        colors.append("#132038")
        customdata.append([0, "", 0, ""])

        for func in industry_data["functions"]:
            unit_cost = AutomationCalculator.get_function_unit_cost(func)
            score = AutomationCalculator.get_function_automation_score(func)
            color = ColorMapper.get_color(score)
            label = ColorMapper.get_label(score)
            sf_count = len(func["subfunctions"])

            labels.append(func["name"])
            parents.append(industry_name)
            values.append(unit_cost)
            colors.append(color)
            customdata.append([round(score, 2), label, sf_count, func["id"]])

        return {
            "labels": labels,
            "parents": parents,
            "values": values,
            "colors": colors,
            "customdata": customdata,
        }

    @staticmethod
    def build_subfunction_treemap_data(function: dict) -> dict:
        # Calibrate gradient to scores within this function
        all_scores = [sf["automation_score"] for sf in function["subfunctions"]]
        ColorMapper.calibrate(all_scores)

        labels, parents, values, colors, customdata = [], [], [], [], []
        func_name = function["name"]

        labels.append(func_name)
        parents.append("")
        values.append(0)
        colors.append("#132038")
        customdata.append([0, "", 0, 0, ""])

        for sf in function["subfunctions"]:
            score = sf["automation_score"]
            color = ColorMapper.get_color(score)
            label = ColorMapper.get_label(score)

            labels.append(sf["name"])
            parents.append(func_name)
            values.append(sf["unit_cost_per_1000"])
            colors.append(color)
            customdata.append([
                round(score, 2),
                label,
                sf.get("fte_pct_headcount", 0),
                sf.get("cost_pct_revenue", 0),
                sf["id"],
            ])

        return {
            "labels": labels,
            "parents": parents,
            "values": values,
            "colors": colors,
            "customdata": customdata,
        }