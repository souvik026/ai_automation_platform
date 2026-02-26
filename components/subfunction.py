from dash import html, dcc, Input, Output, State, callback, no_update
import plotly.graph_objects as go
from urllib.parse import parse_qs

from utils.data_loader import DataLoader
from utils.calculations import AutomationCalculator
from utils.color_mapper import ColorMapper


def build_subfunction_figure(function: dict) -> go.Figure:
    data = AutomationCalculator.build_subfunction_treemap_data(function)

    # Rich text labels
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

    fig = go.Figure(go.Treemap(
        labels=data["labels"],
        parents=data["parents"],
        values=data["values"],
        customdata=data["customdata"],
        text=text_labels,
        textinfo="text",
        marker=dict(
            colors=data["colors"],
            line=dict(width=3, color="#0A1628"),
            pad=dict(t=20, b=12, l=12, r=12),
            cornerradius=6,
        ),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Cost as % Revenue: %{value:.2f}%<br>"
            "Automation Potential: %{customdata[1]}<br>"
            "<extra></extra>"
),
        textfont=dict(size=14, color="white", family="DM Sans"),
        textposition="middle center",
        tiling=dict(packing="squarify", pad=6),
    ))

    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="#0A1628",
        plot_bgcolor="#0A1628",
        font=dict(family="DM Sans", color="white"),
        uniformtext=dict(minsize=11, mode="hide"),
    )
    return fig


def subfunction_layout():
    return html.Div(
        className="page-wrapper",
        children=[
            dcc.Location(id="subfunction-url", refresh=False),

            # Header bar
            html.Div(
                className="page-header",
                children=[
                    html.Div(
                        className="header-left",
                        children=[
                            html.A(
                                id="sf-back-link",
                                children=[html.Span("←"), " All Functions"],
                                href="/treemap",
                                className="back-link"
                            ),
                            html.Div(
                                className="header-title-block",
                                children=[
                                    html.Div(
                                        className="header-brand",
                                        children=[html.Span("AIP", className="brand-accent"), " Platform"]
                                    ),
                                    html.H2(id="sf-page-title", className="page-title"),
                                ]
                            ),
                        ]
                    ),
                    html.Div(
                        className="header-right",
                        children=[
                            html.Button(
                                children=["✦ Analyse with AI"],
                                id="sf-ai-btn",
                                className="ai-button",
                                n_clicks=0,
                            ),
                        ]
                    ),
                ]
            ),

            # Legend bar
            html.Div(
                className="legend-bar",
                children=[
                    html.Span("Automation Potential:", className="legend-label"),
                    html.Div(
                        className="gradient-legend-track",
                        children=[
                            html.Div(className="gradient-legend-bar"),
                            html.Div(
                                className="gradient-legend-labels",
                                children=[
                                    html.Span("Low", className="gradient-lbl-left"),
                                    html.Span("Medium", className="gradient-lbl-mid"),
                                    html.Span("Very High", className="gradient-lbl-right"),
                                ]
                            ),
                        ]
                    ),
                    html.Span("  |  Click a subfunction to see details →", className="legend-hint"),
                ]
            ),

            # Main content: treemap + side panel
            html.Div(
                className="sf-main-content",
                children=[
                    # Treemap
                    html.Div(
                        className="sf-treemap-col",
                        children=[
                            dcc.Graph(
                                id="subfunction-treemap",
                                className="treemap-graph",
                                config={"displayModeBar": False, "responsive": True},
                            ),
                        ]
                    ),

                    # Side panel
                    html.Div(
                        id="sf-side-panel",
                        className="sf-side-panel sf-panel-empty",
                        children=[
                            html.Div(
                                className="panel-empty-state",
                                children=[
                                    html.Div("◈", className="empty-icon"),
                                    html.P("Select a subfunction from the map to view details"),
                                ]
                            )
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
    Input("subfunction-url", "search"),
)
def load_subfunction(search):
    function_id = "operations"
    company = "Client"
    industry = "bfsi"
    if search:
        params = parse_qs(search.lstrip("?"))
        function_id = params.get("function_id", ["operations"])[0]
        company = params.get("company", ["Client"])[0].replace("+", " ")
        industry = params.get("industry", ["bfsi"])[0]

    function = DataLoader.get_function(industry, function_id)
    if not function:
        return go.Figure(), "Function not found", "/treemap"

    fig = build_subfunction_figure(function)
    title = f"{function['name']} — Subfunction Breakdown"
    back_href = f"/treemap?company={company.replace(' ', '+')}&industry={industry}"
    return fig, title, back_href


@callback(
    Output("sf-side-panel", "children"),
    Output("sf-side-panel", "className"),
    Input("subfunction-treemap", "clickData"),
    State("subfunction-url", "search"),
    prevent_initial_call=True,
)
def show_subfunction_panel(click_data, search):
    if not click_data:
        return no_update, no_update

    point = click_data["points"][0]
    customdata = point.get("customdata", [])
    label = point.get("label", "")

    if len(customdata) < 5 or not customdata[4]:
        return no_update, no_update

    sf_id = customdata[4]
    score = customdata[0]
    potential_label = customdata[1]
    fte_pct = customdata[2]
    cost_pct = customdata[3]

    function_id = "operations"
    industry = "bfsi"
    if search:
        params = parse_qs(search.lstrip("?"))
        function_id = params.get("function_id", ["operations"])[0]
        industry = params.get("industry", ["bfsi"])[0]

    sf = DataLoader.get_subfunction(industry, function_id, sf_id)

    color = ColorMapper.get_color(score)

    panel_content = html.Div(
        className="panel-content",
        children=[
            # Panel header
            html.Div(
                className="panel-header",
                children=[
                    html.H3(label, className="panel-title"),
                    html.Div(
                        className="panel-badge",
                        style={"backgroundColor": color},
                        children=potential_label
                    ),
                ]
            ),

            # Score bar
            html.Div(
                className="panel-score-section",
                children=[
                    html.Div(
                        className="score-display",
                        children=[
                            html.Span(f"{int(score)}", className="score-number"),
                            html.Span("/20", className="score-denom"),
                        ]
                    ),
                    html.Div(
                        className="score-bar-track",
                        children=[
                            html.Div(
                                className="score-bar-fill",
                                style={"width": f"{(score/20)*100:.0f}%", "backgroundColor": color}
                            )
                        ]
                    ),
                    html.P("Automation Score", className="score-label"),
                ]
            ),

            # Metrics
            html.Div(
                className="panel-metrics",
                children=[
                    html.Div(
                        className="metric-card",
                        children=[
                            html.Span(f"{fte_pct:.1f}%", className="metric-value"),
                            html.Span("FTE Headcount", className="metric-label"),
                        ]
                    ),
                    html.Div(
                        className="metric-card",
                        children=[
                            html.Span(f"{cost_pct:.2f}%", className="metric-value"),
                            html.Span("% of Revenue", className="metric-label"),
                        ]
                    ),
                ]
            ),

            # Score breakdown
            html.Div(
                className="panel-section",
                children=[
                    html.H4("Score Breakdown", className="section-title"),
                    html.Div(
                        className="score-criteria",
                        children=[
                            _score_criterion("Process Repeatability", sf["automation_scores"]["process_repeatability"]),
                            _score_criterion("Data Availability", sf["automation_scores"]["data_availability"]),
                            _score_criterion("Regulatory Complexity", sf["automation_scores"]["regulatory_complexity"]),
                            _score_criterion("Volume & Scale", sf["automation_scores"]["volume_scale"]),
                        ] if sf else []
                    )
                ]
            ),

            # Placeholder AI use cases (dummy for demo)
            html.Div(
                className="panel-section",
                children=[
                    html.H4("Top AI Opportunities", className="section-title"),
                    html.Div(
                        className="use-cases-list",
                        children=[
                            html.Div(className="use-case-item", children=["◆ AI-powered process automation & workflow orchestration"]),
                            html.Div(className="use-case-item", children=["◆ Intelligent document processing & data extraction"]),
                            html.Div(className="use-case-item", children=["◆ Predictive analytics & anomaly detection"]),
                        ]
                    ),
                    html.P(
                        "Connect AI engine for dynamic, function-specific use cases.",
                        className="panel-footnote"
                    )
                ]
            ),
        ]
    )

    return panel_content, "sf-side-panel sf-panel-active"


def _score_criterion(label: str, score: int) -> html.Div:
    dots = []
    for i in range(5):
        filled = i < score
        dots.append(html.Span(className="dot dot-filled" if filled else "dot dot-empty"))
    return html.Div(
        className="criterion-row",
        children=[
            html.Span(label, className="criterion-label"),
            html.Div(className="criterion-dots", children=dots),
            html.Span(str(score), className="criterion-score"),
        ]
    )


@callback(
    Output("sf-redirect", "href"),
    Input("sf-ai-btn", "n_clicks"),
    State("subfunction-url", "search"),
    prevent_initial_call=True,
)
def go_to_chatbot(n_clicks, search):
    if not n_clicks:
        return None
    function_id = "operations"
    company = "Client"
    industry = "bfsi"
    if search:
        params = parse_qs(search.lstrip("?"))
        function_id = params.get("function_id", ["operations"])[0]
        company = params.get("company", ["Client"])[0]
        industry = params.get("industry", ["bfsi"])[0]
    return f"/chatbot?scope=function&function_id={function_id}&company={company}&industry={industry}"
