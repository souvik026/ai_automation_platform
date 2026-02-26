from dash import html, dcc
import plotly.graph_objects as go
from utils.color_mapper import ColorMapper


class Insights:
    @staticmethod
    def build_score_bar_chart(items: list, name_key: str = "name", score_key: str = "automation_score", is_func: bool = False) -> go.Figure:
        if is_func:
            names = [f["name"] for f in items]
            scores = []
            colors = []
            for f in items:
                sfs = f["subfunctions"]
                avg = sum(sf["automation_score"] for sf in sfs) / len(sfs) if sfs else 0
                scores.append(round(avg, 2))
                colors.append(ColorMapper.get_color(avg))
        else:
            names = [i[name_key] for i in items]
            scores = [round(i[score_key], 2) for i in items]
            colors = [ColorMapper.get_color(s) for s in scores]

        fig = go.Figure(go.Bar(
            x=scores, y=names, orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{s:.2f}" for s in scores],
            textposition="outside",
            textfont=dict(color="#8899BB", size=11, family="DM Sans"),
            hovertemplate="<b>%{y}</b><br>Score: %{x:.2f}/5<extra></extra>",
        ))
        fig.update_layout(
            margin=dict(t=8, b=8, l=8, r=32),
            paper_bgcolor="#111f38", plot_bgcolor="#111f38",
            font=dict(family="DM Sans", color="#8899BB", size=11),
            xaxis=dict(range=[0, 5.5], showgrid=True, gridcolor="#1e3355", zeroline=False, tickfont=dict(color="#556888", size=10)),
            yaxis=dict(showgrid=False, tickfont=dict(color="#F0F4FF", size=11), automargin=True),
            height=max(160, len(items) * 42),
            bargap=0.35,
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
        total_cost = round(sum(s["cost"] for s in func_stats), 1)
        opportunities = sorted(func_stats, key=lambda x: x["score"], reverse=True)[:3]

        return html.Div(className="insights-content", children=[
            html.Div(className="insights-section-header", children=[
                html.Span("Industry Overview", className="insights-section-title"),
                html.Span(f"{len(functions)} functions", className="insights-section-badge"),
            ]),
            html.Div(className="insight-callouts", children=[
                cls._callout_card("Avg Score", f"{overall_avg}/5", "across all functions", "#00C9A7"),
                cls._callout_card("Total Cost", f"{total_cost}%", "of revenue", "#0066FF"),
            ]),
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Highest & Lowest Potential", className="insights-section-title")
            ]),
            html.Div(className="insight-callouts", children=[
                cls._callout_card("Highest", top["name"], f"Score: {top['score']}/5", "#27AE60"),
                cls._callout_card("Lowest", bottom["name"], f"Score: {bottom['score']}/5", "#C0392B"),
            ]),
            html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
                html.Span("Score by Function", className="insights-section-title")
            ]),
            dcc.Graph(
                figure=cls.build_score_bar_chart(functions, is_func=True),
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
        subfunctions = function["subfunctions"]
        has_revenue = bool(subfunctions and subfunctions[0].get("absolute_cost_m") is not None)

        if not subfunctions:
            return html.Div("No subfunctions available.", className="insight-empty")

        avg_score = round(sum(sf["automation_score"] for sf in subfunctions) / len(subfunctions), 2)
        top_sf = max(subfunctions, key=lambda x: x["automation_score"])
        bottom_sf = min(subfunctions, key=lambda x: x["automation_score"])
        total_cost = round(sum(sf["cost_pct_revenue"] for sf in subfunctions), 2)
        opportunities = sorted(subfunctions, key=lambda x: x["automation_score"], reverse=True)[:3]

        children = [
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
                html.Span("Score by Subfunction", className="insights-section-title")
            ]),
            dcc.Graph(
                figure=cls.build_score_bar_chart(subfunctions),
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
        ]

        if selected_sf:
            color = ColorMapper.get_color(selected_sf["automation_score"])
            children += [
                html.Div(className="insights-divider"),
                html.Div(className="insights-section-header", children=[
                    html.Span(f"Selected: {selected_sf['name']}", className="insights-section-title")
                ]),
                html.Div(className="sf-detail-block", children=[
                    html.Div(className="sf-detail-score-row", children=[
                        html.Span("Automation Score", className="sf-detail-label"),
                        html.Span(f"{selected_sf['automation_score']:.1f}/5", className="sf-detail-score", style={"color": color}),
                    ]),
                    html.Div(className="score-bar-track", children=[
                        html.Div(className="score-bar-fill", style={
                            "width": f"{(selected_sf['automation_score'] / 5) * 100:.0f}%",
                            "backgroundColor": color
                        })
                    ]),
                    html.Div(className="sf-detail-metrics", children=[
                        html.Div([
                            html.Span(f"{selected_sf['cost_pct_revenue']:.2f}%", className="metric-value"),
                            html.Span("% of Revenue", className="metric-label"),
                        ], className="metric-card"),
                        html.Div([
                            html.Span(
                                f"${selected_sf['absolute_cost_m']:.1f}M" if selected_sf.get("absolute_cost_m") else "N/A",
                                className="metric-value"
                            ),
                            html.Span("Absolute Cost", className="metric-label"),
                        ], className="metric-card"),
                    ]),
                    html.Div(className="sf-detail-opportunities", children=[
                        html.H4("Top AI Opportunities", className="section-title"),
                        html.Div("◆ AI-powered process automation & workflow orchestration", className="use-case-item"),
                        html.Div("◆ Intelligent document processing & data extraction", className="use-case-item"),
                        html.Div("◆ Predictive analytics & anomaly detection", className="use-case-item"),
                        html.P("Connect LLM for dynamic, function-specific use cases.", className="panel-footnote"),
                    ]),
                ]),
            ]

        children.append(html.Div("Template summary — connect LLM for dynamic insights", className="insights-footnote"))
        return html.Div(className="insights-content", children=children)