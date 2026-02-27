from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import plotly.graph_objects as go
from urllib.parse import parse_qs, quote

from utils.data_loader import DataLoader
from utils.calculations import AutomationCalculator
from utils.color_mapper import ColorMapper
from components.insights import Insights
from components.ask_ai import AskAI


def build_subfunction_figure(function: dict, revenue_m: float = None) -> go.Figure:
    data = AutomationCalculator.build_subfunction_treemap_data(function, revenue_m=revenue_m)
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
        "Cost as % Revenue: %{customdata[3]:.2f}%<br>"
        + ("Absolute Cost: $%{customdata[5]:.1f}M<br>" if has_revenue else "")
        + "Automation Score: %{customdata[0]:.2f}/5<br>"
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
        uniformtext=dict(minsize=11, mode="hide"),
    )
    return fig


def _parse_params(search):
    function_id, company, industry, revenue_m = "operations", "Client", "bfsi", None
    if search:
        params = parse_qs(search.lstrip("?"))
        function_id = params.get("function_id", ["operations"])[0]
        company = params.get("company", ["Client"])[0].replace("+", " ")
        industry = params.get("industry", ["bfsi"])[0]
        rev_str = params.get("revenue", [None])[0]
        if rev_str:
            try:
                revenue_m = float(rev_str)
            except ValueError:
                pass
    return function_id, company, industry, revenue_m


def subfunction_layout():
    return html.Div(
        className="page-wrapper",
        style={"display": "flex", "flexDirection": "column", "height": "100vh", "overflow": "hidden"},
        children=[
            dcc.Location(id="subfunction-url", refresh=False),
            dcc.Store(id="sf-active-tab", data="summary"),

            # Header
            html.Div(
                className="page-header",
                children=[
                    html.Div(className="header-left", children=[
                        html.A(id="sf-back-link", children=[html.Span("←"), " All Functions"], href="/treemap", className="back-link"),
                        html.Div(className="header-title-block", children=[
                            html.Div(className="header-brand", children=[html.Span("AIP", className="brand-accent"), " Platform"]),
                            html.H2(id="sf-page-title", className="page-title"),
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
                    html.Span("  |  Click a subfunction to see details →", className="legend-hint"),
                ]
            ),

            # Body: treemap + right panel
            html.Div(
                style={"display": "flex", "flex": "1", "overflow": "hidden", "minHeight": "0"},
                children=[
                    # Treemap col
                    html.Div(
                        style={"flex": "1", "minWidth": "0", "position": "relative", "padding": "0.5rem 0 1rem 1rem"},
                        children=[
                            dcc.Graph(
                                id="subfunction-treemap",
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
                                html.Button("Summary", id="sf-tab-summary", className="insight-tab insight-tab-active", n_clicks=0),
                                html.Button("Ask AI", id="sf-tab-askai", className="insight-tab", n_clicks=0),
                            ]),
                            html.Div(
                                id="sf-tab-content",
                                className="insight-tab-body",
                                children=[html.Div("Loading...", className="insight-loading")]
                            ),
                        ]
                    ),
                ]
            ),

            dcc.Location(id="sf-redirect", refresh=True),
        ]
    )


@callback(
    Output("subfunction-treemap", "figure"),
    Output("sf-page-title", "children"),
    Output("sf-back-link", "href"),
    Output("sf-tab-content", "children"),
    Input("subfunction-url", "search"),
)
def load_subfunction(search):
    function_id, company, industry, revenue_m = _parse_params(search)
    DataLoader.load_industry(industry, revenue_m=revenue_m)
    function = DataLoader.get_function(industry, function_id, revenue_m=revenue_m)
    if not function:
        return go.Figure(), "Function not found", "/treemap", html.Div("No data.")

    fig = build_subfunction_figure(function, revenue_m=revenue_m)
    title = f"{function['name']} — Subfunction Breakdown"
    back_href = f"/treemap?company={company.replace(' ', '+')}&industry={industry}"
    if revenue_m:
        back_href += f"&revenue={revenue_m}"

    return fig, title, back_href, Insights.build_l2_summary(function, selected_sf=None)


@callback(
    Output("sf-tab-content", "children", allow_duplicate=True),
    Output("sf-tab-summary", "className"),
    Output("sf-tab-askai", "className"),
    Output("sf-active-tab", "data"),
    Input("sf-tab-summary", "n_clicks"),
    Input("sf-tab-askai", "n_clicks"),
    State("subfunction-url", "search"),
    prevent_initial_call=True,
)
def switch_sf_tab(sum_clicks, ai_clicks, search):
    triggered = ctx.triggered_id
    function_id, company, industry, revenue_m = _parse_params(search)

    if triggered == "sf-tab-summary":
        function = DataLoader.get_function(industry, function_id, revenue_m=revenue_m)
        content = Insights.build_l2_summary(function) if function else html.Div("No data.")
        return content, "insight-tab insight-tab-active", "insight-tab", "summary"

    if triggered == "sf-tab-askai":
        function = DataLoader.get_function(industry, function_id, revenue_m=revenue_m)
        func_name = function["name"] if function else ""
        content = AskAI.build_panel(page="l2", context_name=func_name)
        return content, "insight-tab", "insight-tab insight-tab-active", "askai"

    return no_update, no_update, no_update, no_update


@callback(
    Output("sf-redirect", "href", allow_duplicate=True),
    Input("subfunction-treemap", "clickData"),
    State("subfunction-url", "search"),
    prevent_initial_call=True,
)
def on_subfunction_click(click_data, search):
    """When user clicks an L2 box, navigate to L3 breakdown page."""
    if not click_data:
        return no_update

    point = click_data["points"][0]
    customdata = point.get("customdata", [])

    if len(customdata) < 5 or not customdata[4]:
        return no_update

    sf_id = customdata[4]
    function_id, company, industry, revenue_m = _parse_params(search)

    function = DataLoader.get_function(industry, function_id, revenue_m=revenue_m)
    if not function:
        return no_update

    sf = DataLoader.get_subfunction(industry, function_id, sf_id, revenue_m=revenue_m)
    if not sf:
        return no_update

    l2_name = quote(sf["name"])
    l1_name = quote(function["name"])
    url = (f"/l3breakdown?function_id={function_id}"
           f"&l2_name={l2_name}&l1_name={l1_name}"
           f"&company={quote(company)}&industry={industry}")
    if revenue_m:
        url += f"&revenue={revenue_m}"
    return url