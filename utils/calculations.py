from utils.color_mapper import ColorMapper


class AutomationCalculator:
    """
    All treemap sizing and automation score logic lives here.
    No other file computes scores or sizes.
    """

    @staticmethod
    def get_automation_score(scores: dict) -> int:
        """
        Sum of all 4 criteria scores.
        Max possible = 20 (4 criteria x 5 points each).
        """
        return sum(scores.values())

    @staticmethod
    def get_function_unit_cost(function: dict) -> float:
        """
        Function box size = sum of all subfunctions' unit_cost_per_1000.
        NEVER manually set — always derived from children automatically.
        """
        return sum(sf["unit_cost_per_1000"] for sf in function["subfunctions"])

    @staticmethod
    def get_function_automation_score(function: dict) -> float:
        """
        Function automation score = weighted average of subfunction scores,
        weighted by unit_cost_per_1000.

        Larger (more expensive) subfunctions influence the parent score more.
        """
        total_cost = sum(sf["unit_cost_per_1000"] for sf in function["subfunctions"])
        if total_cost == 0:
            return 0
        weighted_score = sum(
            AutomationCalculator.get_automation_score(sf["automation_scores"])
            * sf["unit_cost_per_1000"]
            for sf in function["subfunctions"]
        )
        return weighted_score / total_cost

    @staticmethod
    def build_function_treemap_data(industry_data: dict) -> dict:
        """
        Builds the data dict Plotly needs for the function-level treemap.
        Returns: { labels, parents, values, colors, customdata }
        """
        labels = []
        parents = []
        values = []
        colors = []
        customdata = []

        industry_name = industry_data["industry"]

        # Root node
        labels.append(industry_name)
        parents.append("")
        values.append(0)
        colors.append("#132038")
        customdata.append([0, ""])

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
            customdata.append([round(score, 1), label, sf_count, func["id"]])

        return {
            "labels": labels,
            "parents": parents,
            "values": values,
            "colors": colors,
            "customdata": customdata,
        }

    @staticmethod
    def build_subfunction_treemap_data(function: dict) -> dict:
        """
        Builds Plotly treemap data for a single function's subfunctions.
        Returns: { labels, parents, values, colors, customdata }
        """
        labels = []
        parents = []
        values = []
        colors = []
        customdata = []

        func_name = function["name"]

        # Root node = the function itself
        labels.append(func_name)
        parents.append("")
        values.append(0)
        colors.append("#132038")
        customdata.append([0, "", 0, 0])

        for sf in function["subfunctions"]:
            score = AutomationCalculator.get_automation_score(sf["automation_scores"])
            color = ColorMapper.get_color(score)
            label = ColorMapper.get_label(score)

            labels.append(sf["name"])
            parents.append(func_name)
            values.append(sf["unit_cost_per_1000"])
            colors.append(color)
            customdata.append([
                score,
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
