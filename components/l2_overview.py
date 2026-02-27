from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import plotly.graph_objects as go
from urllib.parse import parse_qs

from utils.data_loader import DataLoader
from utils.calculations import AutomationCalculator
from utils.color_mapper import ColorMapper
from components.insights import Insights
from components.ask_ai import AskAI


def build_l2_overview_figure(industry_data: dict) -> go.Figure:
    """Flat treemap of ALL L2 subfunctions across all L1 functions."""
    all_scores = [
        sf["automation_score"]
        for func in industry_data["functions"]
        for sf in func["subfunctions"]
    ]
    ColorMapper.calibrate(all_scores)

    revenue_m = industry_data.get("revenue_m")
    has_revenue = revenue_m is not None

    labels, parents, values, colors, customdata = [], [], [], [], []

    # Root node
    industry_name = industry_data["industry"]
    labels.append(industry_name)
    parents.append("")
    values.append(0)
    colors.append("#132038")
    customdata.append([0, "", "", "", 0, 0])

    for func in industry_data["functions"]:
        for sf in func["subfunctions"]:
            score = sf["automation_score"]
            color = ColorMapper.get_color(score)
            label = ColorMapper.get_label(score)
            size = sf.get("absolute_cost_m") or sf["unit_cost_per_1000"] if has_revenue else sf["unit_cost_per_1000"]

            labels.append(sf["name"])
            parents.append(industry_name)
            values.append(size)
            colors.append(color)
            customdata.append([
                round(score, 2),
                label,
                func["name"],       # parent L1 name
                sf["id"],
                sf["cost_pct_revenue"],
                round(sf.get("absolute_cost_m") or 0, 1),
            ])

    if has_revenue:
        hover = (
            "<b>%{label}</b><br>"
            "L1 Function: %{customdata[2]}<br>"
            "Cost as % Revenue: %{customdata[4]:.2f}%<br>"
            "Absolute Cost: $%{customdata[5]:.1f}M<br>"
            "Automation Score: %{customdata[0]:.2f}/5<br>"
            "<extra></extra>"
        )
    else:
        hover = (
            "<b>%{label}</b><br>"
            "L1 Function: %{customdata[2]}<br>"
            "Cost as % Revenue: %{customdata[4]:.2f}%<br>"
            "Automation Score: %{customdata[0]:.2f}/5<br>"
            "<extra></extra>"
        )

    text_labels = []
    for i, label in enumerate(labels):
        cd = customdata[i]
        if cd[0] == 0 and cd[1] == "":
            text_labels.append("")
        else:
            text_labels.append(
                f"<b>{label}</b><br>"
                f"<span style='font-size:11px'>{cd[1]} Potential</span><br>"
                f"<span style='font-size:10px; opacity:0.7'>{cd[2]}</span>"
            )

    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values,
        customdata=customdata, text=text_labels, textinfo="text",
        marker=dict(colors=colors, line=dict(width=2, color="#0A1628"),
                    pad=dict(t=20, b=10, l=10, r=10), cornerradius=5),
        hovertemplate=hover,
        textfont=dict(size=13, color="white", family="DM Sans"),
        textposition="middle center",
        tiling=dict(packing="squarify", pad=4),
    ))
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
        font=dict(family="DM Sans", color="white"),
        uniformtext=dict(minsize=10, mode="hide"),
    )
    return fig


def _parse_params(search):
    company, industry, revenue_m = "Client", "bfsi", None
    if search:
        params = parse_qs(search.lstrip("?"))
        company = params.get("company", ["Client"])[0].replace("+", " ")
        industry = params.get("industry", ["bfsi"])[0]
        rev_str = params.get("revenue", [None])[0]
        if rev_str:
            try:
                revenue_m = float(rev_str)
            except ValueError:
                pass
    return company, industry, revenue_m


def l2_overview_layout():
    return html.Div(
        className="page-wrapper",
        style={"display": "flex", "flexDirection": "column", "height": "100vh", "overflow": "hidden"},
        children=[
            dcc.Location(id="l2overview-url", refresh=False),
            dcc.Store(id="l2overview-active-tab", data="summary"),

            # Header
            html.Div(
                className="page-header",
                children=[
                    html.Div(className="header-left", children=[
                        html.A(id="l2overview-back-link", children=[html.Span("←"), " L1 Functions"], href="/treemap", className="back-link"),
                        html.Div(className="header-title-block", children=[
                            html.Div(className="header-brand", children=[html.Span("AIIF", className="brand-accent"), " Platform"]),
                            html.H2(id="l2overview-page-title", className="page-title"),
                        ]),
                    ]),
                ]
            ),

            # Legend
            html.Div(
                className="legend-bar",
                children=[
                    html.Span("Automation Potential:", className="legend-label"),
                    html.Div(className="gradient-legend-track", children=[
                        html.Div(className="gradient-legend-bar"),
                        html.Div(className="gradient-legend-labels", children=[
                            html.Span("Low", className="gradient-lbl-left"),
                            html.Span("Medium", className="gradient-lbl-mid"),
                            html.Span("Very High", className="gradient-lbl-right"),
                        ]),
                    ]),
                    html.Span("  |  All subfunctions across all L1 functions", className="legend-hint"),
                ]
            ),

            # Body
            html.Div(
                style={"display": "flex", "flex": "1", "overflow": "hidden", "minHeight": "0"},
                children=[
                    # Treemap
                    html.Div(
                        style={"flex": "1", "minWidth": "0", "position": "relative", "padding": "0.5rem 0 1rem 1rem"},
                        children=[
                            dcc.Graph(
                                id="l2overview-treemap",
                                style={"width": "100%", "height": "100%"},
                                config={"displayModeBar": False, "responsive": True},
                            ),
                        ]
                    ),
                    # Right panel
                    html.Div(
                        style={
                            "width": "340px", "flexShrink": "0",
                            "background": "#111f38", "borderLeft": "1px solid #1e3355",
                            "display": "flex", "flexDirection": "column", "overflow": "hidden"
                        },
                        children=[
                            html.Div(className="insight-tabs", children=[
                                html.Button("Summary", id="l2overview-tab-summary", className="insight-tab insight-tab-active", n_clicks=0),
                                html.Button("Ask AI", id="l2overview-tab-askai", className="insight-tab", n_clicks=0),
                            ]),
                            html.Div(
                                id="l2overview-tab-content",
                                className="insight-tab-body",
                                children=[html.Div("Loading...", className="insight-loading")]
                            ),
                        ]
                    ),
                ]
            ),
        ]
    )


@callback(
    Output("l2overview-treemap", "figure"),
    Output("l2overview-page-title", "children"),
    Output("l2overview-back-link", "href"),
    Output("l2overview-tab-content", "children"),
    Input("l2overview-url", "search"),
)
def load_l2_overview(search):
    company, industry, revenue_m = _parse_params(search)
    industry_data = DataLoader.load_industry(industry, revenue_m=revenue_m)

    fig = build_l2_overview_figure(industry_data)
    rev_label = f" | Revenue: ${revenue_m:,.0f}M" if revenue_m else ""
    title = f"All Subfunctions — {company} — {industry_data['industry']}{rev_label}"
    back_href = f"/treemap?company={company.replace(' ', '+')}&industry={industry}"
    if revenue_m:
        back_href += f"&revenue={revenue_m}"

    summary = Insights.build_l2_overview_summary(industry_data)
    return fig, title, back_href, summary


@callback(
    Output("l2overview-tab-content", "children", allow_duplicate=True),
    Output("l2overview-tab-summary", "className"),
    Output("l2overview-tab-askai", "className"),
    Output("l2overview-active-tab", "data"),
    Input("l2overview-tab-summary", "n_clicks"),
    Input("l2overview-tab-askai", "n_clicks"),
    State("l2overview-url", "search"),
    prevent_initial_call=True,
)
def switch_l2overview_tab(sum_clicks, ai_clicks, search):
    triggered = ctx.triggered_id
    company, industry, revenue_m = _parse_params(search)
    industry_data = DataLoader.load_industry(industry, revenue_m=revenue_m)

    if triggered == "l2overview-tab-summary":
        return Insights.build_l2_overview_summary(industry_data), "insight-tab insight-tab-active", "insight-tab", "summary"
    if triggered == "l2overview-tab-askai":
        return AskAI.build_panel("l1", industry_data.get("industry", "")), "insight-tab", "insight-tab insight-tab-active", "askai"
    return no_update, no_update, no_update, no_update