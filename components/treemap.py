from dash import html, dcc, Input, Output, State, callback, ctx, no_update
import plotly.graph_objects as go
from urllib.parse import parse_qs

from utils.data_loader import DataLoader
from utils.calculations import AutomationCalculator
from components.insights import Insights
from components.ask_ai import AskAI


def build_treemap_figure(industry_data: dict) -> go.Figure:
    data = AutomationCalculator.build_function_treemap_data(industry_data)
    has_revenue = data.get("has_revenue", False)

    text_labels = []
    for i, label in enumerate(data["labels"]):
        cd = data["customdata"][i]
        if cd[0] == 0 and cd[1] == "":
            text_labels.append("")
        else:
            text_labels.append(
                f"<b>{label}</b><br>"
                f"<span style='font-size:12px'>{cd[1]} Potential</span>"
            )

    hover = (
        "<b>%{label}</b><br>"
        "Cost as % Revenue: %{customdata[4]:.2f}%<br>"
        + ("Absolute Cost: $%{customdata[5]:.1f}M<br>" if has_revenue else "")
        + "Avg Automation Score: %{customdata[0]:.2f}/5<br>"
        "Subfunctions: %{customdata[2]}<br>"
        "<extra></extra>"
    )

    fig = go.Figure(go.Treemap(
        labels=data["labels"], parents=data["parents"], values=data["values"],
        customdata=data["customdata"], text=text_labels, textinfo="text",
        marker=dict(colors=data["colors"], line=dict(width=3, color="#0A1628"),
                    pad=dict(t=20, b=12, l=12, r=12), cornerradius=6),
        hovertemplate=hover,
        textfont=dict(size=14, color="white", family="DM Sans"),
        textposition="middle center", tiling=dict(packing="squarify", pad=6),
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


def treemap_layout():
    return html.Div(
        className="page-wrapper",
        style={"display": "flex", "flexDirection": "column", "height": "100vh", "overflow": "hidden"},
        children=[
            dcc.Location(id="treemap-url", refresh=False),
            dcc.Store(id="treemap-nav-store"),
            dcc.Store(id="treemap-active-tab", data="summary"),

            # Header
            html.Div(
                className="page-header",
                children=[
                    html.Div(className="header-left", children=[
                        html.A(children=[html.Span("←"), " Back to Home"], href="/", className="back-link"),
                        html.Div(className="header-title-block", children=[
                            html.Div(className="header-brand", children=[html.Span("AIIF", className="brand-accent"), " Platform"]),
                            html.H2(id="treemap-page-title", className="page-title"),
                        ]),
                    ]),
                    html.Div(className="header-right", children=[
                        html.Button(
                            children=["⊞ View All Subfunctions"],
                            id="treemap-l2overview-btn",
                            className="ai-button",
                            n_clicks=0,
                        ),
                    ]),
                ]
            ),

            # Body: treemap + right panel
            html.Div(
                style={"display": "flex", "flex": "1", "overflow": "hidden", "minHeight": "0"},
                children=[
                    # Treemap col
                    html.Div(
                        style={"flex": "1", "minWidth": "0", "position": "relative", "padding": "1rem 0 1rem 1.5rem"},
                        children=[
                            dcc.Graph(
                                id="function-treemap",
                                style={"width": "100%", "height": "100%"},
                                config={"displayModeBar": False, "responsive": True},
                            ),
                            html.Div(
                                id="treemap-click-hint",
                                className="click-hint",
                                children="Click any function to drill down into subfunctions →"
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
                                html.Button("Summary", id="treemap-tab-summary", className="insight-tab insight-tab-active", n_clicks=0),
                                html.Button("Ask AI", id="treemap-tab-askai", className="insight-tab", n_clicks=0),
                            ]),
                            html.Div(
                                id="treemap-tab-content",
                                className="insight-tab-body",
                                children=[html.Div("Loading...", className="insight-loading")]
                            ),
                        ]
                    ),
                ]
            ),

            dcc.Location(id="treemap-redirect", refresh=True),
        ]
    )


@callback(
    Output("function-treemap", "figure"),
    Output("treemap-page-title", "children"),
    Output("treemap-tab-content", "children"),
    Input("treemap-url", "search"),
)
def load_treemap(search):
    company, industry, revenue_m = _parse_params(search)
    industry_data = DataLoader.load_industry(industry, revenue_m=revenue_m)
    fig = build_treemap_figure(industry_data)
    rev_label = f" | Revenue: ${revenue_m:,.0f}M" if revenue_m else ""
    title = f"Automation Opportunity Map — {company} — {industry_data['industry']}{rev_label}"
    return fig, title, Insights.build_l1_summary(industry_data)


@callback(
    Output("treemap-tab-content", "children", allow_duplicate=True),
    Output("treemap-tab-summary", "className"),
    Output("treemap-tab-askai", "className"),
    Output("treemap-active-tab", "data"),
    Input("treemap-tab-summary", "n_clicks"),
    Input("treemap-tab-askai", "n_clicks"),
    State("treemap-url", "search"),
    prevent_initial_call=True,
)
def switch_treemap_tab(sum_clicks, ai_clicks, search):
    triggered = ctx.triggered_id
    company, industry, revenue_m = _parse_params(search)
    industry_data = DataLoader.load_industry(industry, revenue_m=revenue_m)

    if triggered == "treemap-tab-summary":
        return Insights.build_l1_summary(industry_data), "insight-tab insight-tab-active", "insight-tab", "summary"
    if triggered == "treemap-tab-askai":
        return AskAI.build_panel("l1", industry_data.get("industry", "")), "insight-tab", "insight-tab insight-tab-active", "askai"
    return no_update, no_update, no_update, no_update


@callback(
    Output("treemap-redirect", "href"),
    Input("function-treemap", "clickData"),
    State("treemap-url", "search"),
    prevent_initial_call=True,
)
def on_treemap_click(click_data, search):
    if not click_data:
        return None
    point = click_data["points"][0]
    customdata = point.get("customdata", [])
    if len(customdata) >= 4 and customdata[3]:
        company, industry, revenue_m = _parse_params(search)
        url = f"/subfunction?function_id={customdata[3]}&company={company.replace(' ', '+')}&industry={industry}"
        if revenue_m:
            url += f"&revenue={revenue_m}"
        return url
    return None


@callback(
    Output("treemap-redirect", "href", allow_duplicate=True),
    Input("treemap-l2overview-btn", "n_clicks"),
    State("treemap-url", "search"),
    prevent_initial_call=True,
)
def go_to_l2_overview(n_clicks, search):
    if not n_clicks:
        return no_update
    company, industry, revenue_m = _parse_params(search)
    url = f"/l2overview?company={company.replace(' ', '+')}&industry={industry}"
    if revenue_m:
        url += f"&revenue={revenue_m}"
    return url