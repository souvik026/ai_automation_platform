from dash import html, dcc
import plotly.graph_objects as go
from utils.color_mapper import ColorMapper


class Insights:

    @staticmethod
    def build_pie_chart(labels: list, values: list, colors: list, title: str = "") -> go.Figure:
        fig = go.Figure(go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors, line=dict(color="#0A1628", width=2)),
            textinfo="percent",
            textfont=dict(size=11, color="white", family="DM Sans"),
            hovertemplate="<b>%{label}</b><br>Cost: %{value:.2f}%<br>Share: %{percent}<extra></extra>",
            hole=0.45,
            sort=False,
        ))
        fig.update_layout(
            margin=dict(t=8, b=8, l=8, r=8),
            paper_bgcolor="#111f38",
            plot_bgcolor="#111f38",
            font=dict(family="DM Sans", color="#8899BB", size=11),
            showlegend=True,
            legend=dict(
                font=dict(size=10, color="#8899BB"),
                bgcolor="rgba(0,0,0,0)",
                orientation="v",
                x=1.0, y=0.5,
                xanchor="left",
            ),
            height=200,
        )
        return fig

    @staticmethod
    def _callout_card(label, value, sub, color):
        return html.Div(
            className="insight-callout-card",
            style={"borderLeft": f"3px solid {color}"},
            children=[
                html.Div(label, className="callout-label"),
                html.Div(value, className="callout-value", style={"color": color}),
                html.Div(sub, className="callout-sub"),
            ]
        )

    @staticmethod
    def _opportunity_item(rank, name, score, cost, has_revenue=False, abs_cost=None):
        color = ColorMapper.get_color(score)
        cost_str = f"${abs_cost:.1f}M" if has_revenue and abs_cost else f"{cost:.1f}% rev"
        return html.Div(
            className="opportunity-item",
            children=[
                html.Span(f"{rank}", className="opp-rank"),
                html.Div(className="opp-details", children=[
                    html.Div(name, className="opp-name"),
                    html.Div(cost_str, className="opp-cost"),
                ]),
                html.Div(f"{score:.1f}", className="opp-score-badge", style={"backgroundColor": color}),
            ]
        )

    @classmethod
    def build_l1_summary(cls, industry_data: dict) -> html.Div:
        functions = industry_data["functions"]
        revenue_m = industry_data.get("revenue_m")
        has_revenue = revenue_m is not None

        if not functions:
            return html.Div("No data available.", className="insight-empty")

        func_stats = []
        for f in functions:
            sfs = f["subfunctions"]
            avg_score = sum(sf["automation_score"] for sf in sfs) / len(sfs) if sfs else 0
            total_cost = sum(sf["cost_pct_revenue"] for sf in sfs)
            abs_cost = sum(sf["absolute_cost_m"] or 0 for sf in sfs) if has_revenue else None
            func_stats.append({
                "name": f["name"], "score": round(avg_score, 2),
                "cost": round(total_cost, 2),
                "abs_cost": round(abs_cost, 1) if abs_cost is not None else None,
            })

        top = max(func_stats, key=lambda x: x["score"])
        bottom = min(func_stats, key=lambda x: x["score"])
        overall_avg = round(sum(s["score"] for s in func_stats) / len(func_stats), 2)
        total_cost_sum = round(sum(s["cost"] for s in func_stats), 1)
        opportunities = sorted(func_stats, key=lambda x: x["score"], reverse=True)[:3]

        # Pie: cost breakdown by function
        pie_labels = [s["name"] for s in func_stats]
        pie_values = [s["cost"] for s in func_stats]
        pie_colors = [ColorMapper.get_color(s["score"]) for s in func_stats]

        return html.Div(className="insights-content", children=[
            html.Div(className="insights-section-header", children=[
                html.Span("Industry Overview", className="insights-section-title"),
                html.Span(f"{len(functions)} functions", className="insights-section-badge"),
            ]),
            html.Div(className="insight-callouts", children=[
                cls._callout_card("Avg Score", f"{overall_avg}/5", "across all functions", "#00C9A7"),
                cls._callout_card("Total Cost", f"{total_cost_sum}%", "of revenue", "#0066FF"),
            ]),
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Highest & Lowest Potential", className="insights-section-title")
            ]),
            html.Div(className="insight-callouts", children=[
                cls._callout_card("Highest", top["name"], f"Score: {top['score']}/5", "#27AE60"),
                cls._callout_card("Lowest", bottom["name"], f"Score: {bottom['score']}/5", "#C0392B"),
            ]),
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Cost Breakdown by Function", className="insights-section-title")
            ]),
            dcc.Graph(
                figure=cls.build_pie_chart(pie_labels, pie_values, pie_colors),
                config={"displayModeBar": False, "responsive": True},
                className="insights-chart",
            ),
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Top Opportunities", className="insights-section-title")
            ]),
            html.Div(className="opportunities-list", children=[
                cls._opportunity_item(i+1, o["name"], o["score"], o["cost"], has_revenue, o.get("abs_cost"))
                for i, o in enumerate(opportunities)
            ]),
            html.Div("Template summary — connect LLM for dynamic insights", className="insights-footnote"),
        ])

    @classmethod
    def build_l2_summary(cls, function: dict, selected_sf: dict = None) -> html.Div:
        """
        If selected_sf is provided, show ONLY that subfunction's detail.
        Otherwise show the full function overview.
        """
        subfunctions = function["subfunctions"]
        has_revenue = bool(subfunctions and subfunctions[0].get("absolute_cost_m") is not None)

        if not subfunctions:
            return html.Div("No subfunctions available.", className="insight-empty")

        # If a subfunction is clicked, show its detail view only
        if selected_sf:
            return cls._build_sf_detail(function, selected_sf, has_revenue)

        # Default: full function overview
        avg_score = round(sum(sf["automation_score"] for sf in subfunctions) / len(subfunctions), 2)
        top_sf = max(subfunctions, key=lambda x: x["automation_score"])
        bottom_sf = min(subfunctions, key=lambda x: x["automation_score"])
        total_cost = round(sum(sf["cost_pct_revenue"] for sf in subfunctions), 2)
        opportunities = sorted(subfunctions, key=lambda x: x["automation_score"], reverse=True)[:3]

        pie_labels = [sf["name"] for sf in subfunctions]
        pie_values = [sf["cost_pct_revenue"] for sf in subfunctions]
        pie_colors = [ColorMapper.get_color(sf["automation_score"]) for sf in subfunctions]

        return html.Div(className="insights-content", children=[
            html.Div(className="insights-section-header", children=[
                html.Span(function["name"], className="insights-section-title"),
                html.Span(f"{len(subfunctions)} subfunctions", className="insights-section-badge"),
            ]),
            html.Div(className="insight-callouts", children=[
                cls._callout_card("Avg Score", f"{avg_score}/5", "across subfunctions", "#00C9A7"),
                cls._callout_card("Total Cost", f"{total_cost}%", "of revenue", "#0066FF"),
            ]),
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Highest & Lowest", className="insights-section-title")
            ]),
            html.Div(className="insight-callouts", children=[
                cls._callout_card("Highest", top_sf["name"], f"Score: {top_sf['automation_score']}/5", "#27AE60"),
                cls._callout_card("Lowest", bottom_sf["name"], f"Score: {bottom_sf['automation_score']}/5", "#C0392B"),
            ]),
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Cost Breakdown", className="insights-section-title")
            ]),
            dcc.Graph(
                figure=cls.build_pie_chart(pie_labels, pie_values, pie_colors),
                config={"displayModeBar": False, "responsive": True},
                className="insights-chart",
            ),
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Top Opportunities", className="insights-section-title")
            ]),
            html.Div(className="opportunities-list", children=[
                cls._opportunity_item(i+1, sf["name"], sf["automation_score"], sf["cost_pct_revenue"], has_revenue, sf.get("absolute_cost_m"))
                for i, sf in enumerate(opportunities)
            ]),
            html.Div("Click any subfunction for detailed insights", className="insights-footnote"),
        ])

    @classmethod
    def _build_sf_detail(cls, function: dict, sf: dict, has_revenue: bool) -> html.Div:
        """Focused detail view for a single selected subfunction."""
        color = ColorMapper.get_color(sf["automation_score"])
        score_pct = (sf["automation_score"] / 5) * 100

        return html.Div(className="insights-content", children=[
            # Back hint
            html.Div(className="sf-detail-back-hint", children=[
                html.Span("← ", style={"color": "#556888"}),
                html.Span(function["name"], style={"color": "#556888", "fontSize": "11px"}),
            ]),

            # SF name + badge
            html.Div(className="insights-section-header", children=[
                html.Span(sf["name"], className="insights-section-title"),
                html.Span(
                    ColorMapper.get_label(sf["automation_score"]),
                    className="insights-section-badge",
                    style={"backgroundColor": color, "color": "white", "borderColor": color}
                ),
            ]),

            # Score display
            html.Div(className="sf-score-display", children=[
                html.Div(className="sf-score-circle", style={"borderColor": color}, children=[
                    html.Span(f"{sf['automation_score']:.1f}", className="sf-score-big", style={"color": color}),
                    html.Span("/5", className="sf-score-denom"),
                ]),
                html.Div(className="sf-score-bar-col", children=[
                    html.Div("Automation Score", className="sf-detail-label"),
                    html.Div(className="score-bar-track", children=[
                        html.Div(className="score-bar-fill", style={
                            "width": f"{score_pct:.0f}%",
                            "backgroundColor": color
                        })
                    ]),
                    html.Div(f"{score_pct:.0f}% of max potential", className="callout-sub"),
                ]),
            ]),

            # Cost metrics
            html.Div(className="insight-callouts", style={"marginTop": "12px"}, children=[
                cls._callout_card("% of Revenue", f"{sf['cost_pct_revenue']:.2f}%", "cost exposure", "#0066FF"),
                cls._callout_card(
                    "Absolute Cost",
                    f"${sf['absolute_cost_m']:.1f}M" if sf.get("absolute_cost_m") else "N/A",
                    "estimated cost" if sf.get("absolute_cost_m") else "enter revenue",
                    "#00C9A7"
                ),
            ]),

            # Role description
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Function Description", className="insights-section-title")
            ]),
            html.Div(
                sf.get("role_description", "No description available."),
                className="sf-role-description"
            ),

            # AI Opportunities
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Top AI Opportunities", className="insights-section-title")
            ]),
            html.Div(className="sf-detail-opportunities", children=[
                html.Div("◆ AI-powered process automation & workflow orchestration", className="use-case-item"),
                html.Div("◆ Intelligent document processing & data extraction", className="use-case-item"),
                html.Div("◆ Predictive analytics & anomaly detection", className="use-case-item"),
            ]),
            html.P("Connect LLM for dynamic, function-specific use cases.", className="insights-footnote"),
        ])

    @classmethod
    def build_l2_overview_summary(cls, industry_data: dict) -> html.Div:
        """Summary for the all-L2 overview page. No pie chart. Top subfunctions list."""
        functions = industry_data["functions"]
        revenue_m = industry_data.get("revenue_m")
        has_revenue = revenue_m is not None

        # Flatten all subfunctions
        all_sfs = []
        for func in functions:
            for sf in func["subfunctions"]:
                all_sfs.append({
                    "name": sf["name"],
                    "l1": func["name"],
                    "score": sf["automation_score"],
                    "cost": sf["cost_pct_revenue"],
                    "abs_cost": sf.get("absolute_cost_m"),
                })

        if not all_sfs:
            return html.Div("No data available.", className="insight-empty")

        total_sfs = len(all_sfs)
        overall_avg = round(sum(s["score"] for s in all_sfs) / total_sfs, 2)
        total_cost = round(sum(s["cost"] for s in all_sfs), 1)
        top = max(all_sfs, key=lambda x: x["score"])
        bottom = min(all_sfs, key=lambda x: x["score"])

        # Top 5 by score
        top5 = sorted(all_sfs, key=lambda x: x["score"], reverse=True)[:5]
        # Bottom 5 by score
        bottom5 = sorted(all_sfs, key=lambda x: x["score"])[:5]

        def sf_row(rank, sf, show_rank=True):
            color = ColorMapper.get_color(sf["score"])
            cost_str = f"${sf['abs_cost']:.1f}M" if has_revenue and sf.get("abs_cost") else f"{sf['cost']:.1f}%"
            return html.Div(
                className="opportunity-item",
                children=[
                    html.Span(f"{rank}", className="opp-rank") if show_rank else None,
                    html.Div(className="opp-details", children=[
                        html.Div(sf["name"], className="opp-name"),
                        html.Div(sf["l1"], className="opp-cost", style={"color": "#556888"}),
                    ]),
                    html.Div(
                        children=[
                            html.Div(f"{sf['score']:.1f}", className="opp-score-badge", style={"backgroundColor": color}),
                            html.Div(cost_str, className="opp-cost", style={"textAlign": "right", "marginTop": "2px"}),
                        ]
                    ),
                ]
            )

        return html.Div(className="insights-content", children=[
            # Header
            html.Div(className="insights-section-header", children=[
                html.Span("All Subfunctions", className="insights-section-title"),
                html.Span(f"{total_sfs} total", className="insights-section-badge"),
            ]),

            # Callouts
            html.Div(className="insight-callouts", children=[
                cls._callout_card("Avg Score", f"{overall_avg}/5", f"across {total_sfs} subfunctions", "#00C9A7"),
                cls._callout_card("Total Cost", f"{total_cost}%", "of revenue", "#0066FF"),
            ]),

            # Highest / Lowest
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Highest & Lowest", className="insights-section-title")
            ]),
            html.Div(className="insight-callouts", children=[
                cls._callout_card("Highest", top["name"], f"{top['l1']} · {top['score']}/5", "#27AE60"),
                cls._callout_card("Lowest", bottom["name"], f"{bottom['l1']} · {bottom['score']}/5", "#C0392B"),
            ]),

            # Top 5 subfunctions
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Top 5 Subfunctions", className="insights-section-title"),
                html.Span("by score", className="insights-section-badge"),
            ]),
            html.Div(className="opportunities-list", children=[
                sf_row(i+1, sf) for i, sf in enumerate(top5)
            ]),

            # Bottom 5
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Lowest 5 Subfunctions", className="insights-section-title"),
                html.Span("by score", className="insights-section-badge"),
            ]),
            html.Div(className="opportunities-list", children=[
                sf_row(i+1, sf) for i, sf in enumerate(bottom5)
            ]),

            html.Div("Template summary — connect LLM for dynamic insights", className="insights-footnote"),
        ])