from dash import html, dcc, Input, Output, State, callback, ctx
import plotly.graph_objects as go
from urllib.parse import urlparse, parse_qs

from utils.data_loader import DataLoader
from utils.calculations import AutomationCalculator
from utils.color_mapper import ColorMapper


def build_treemap_figure(industry_data: dict) -> go.Figure:
    data = AutomationCalculator.build_function_treemap_data(industry_data)

    text_labels = []
    for i, label in enumerate(data["labels"]):
        cd = data["customdata"][i]
        if cd[0] == 0 and cd[1] == "":
            text_labels.append("")
        else:
            text_labels.append(
                f"<b>{label}</b><br>"
                f"<span style='font-size:11px'>{cd[1]} Potential</span><br>"
                f"<span style='font-size:13px'>{cd[0]}/20</span>"
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
            "Unit Cost / $1,000 Revenue: $%{value:.1f}<br>"
            "Automation Potential: %{customdata[1]}<br>"
            "Score: %{customdata[0]}/20<br>"
            "Subfunctions: %{customdata[2]}<br>"
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
        uniformtext=dict(minsize=10, mode="hide"),
    )
    return fig


def treemap_layout():
    return html.Div(
        className="page-wrapper",
        children=[
            dcc.Location(id="treemap-url", refresh=False),
            dcc.Store(id="treemap-nav-store"),

            # Header bar
            html.Div(
                className="page-header",
                children=[
                    html.Div(
                        className="header-left",
                        children=[
                            html.A(
                                children=[html.Span("←"), " Back to Home"],
                                href="/",
                                className="back-link"
                            ),
                            html.Div(
                                className="header-title-block",
                                children=[
                                    html.Div(
                                        className="header-brand",
                                        children=[html.Span("AIIF", className="brand-accent"), " Platform"]
                                    ),
                                    html.H2(id="treemap-page-title", className="page-title"),
                                ]
                            ),
                        ]
                    ),
                    html.Div(
                        className="header-right",
                        children=[
                            html.Button(
                                children=["✦ Analyse with AI"],
                                id="treemap-ai-btn",
                                className="ai-button",
                                n_clicks=0,
                            ),
                        ]
                    ),
                ]
            ),

            # Legend bar
            

            # Treemap
            html.Div(
                className="treemap-container",
                children=[
                    dcc.Graph(
                        id="function-treemap",
                        className="treemap-graph",
                        config={"displayModeBar": False, "responsive": True},
                    ),
                    html.Div(
                        id="treemap-click-hint",
                        className="click-hint",
                        children="Click any function to drill down into subfunctions →"
                    ),
                ]
            ),

            dcc.Location(id="treemap-redirect", refresh=True),
        ]
    )


@callback(
    Output("function-treemap", "figure"),
    Output("treemap-page-title", "children"),
    Input("treemap-url", "search"),
)
def load_treemap(search):
    company = "Client"
    industry = "bfsi"
    if search:
        params = parse_qs(search.lstrip("?"))
        company = params.get("company", ["Client"])[0].replace("+", " ")
        industry = params.get("industry", ["bfsi"])[0]

    industry_data = DataLoader.load_industry(industry)
    fig = build_treemap_figure(industry_data)
    title = f"Automation Opportunity Map — {company} — {industry_data['industry']}"
    return fig, title


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
    if len(customdata) >= 4:
        function_id = customdata[3]
        if function_id:
            company = "Client"
            industry = "bfsi"
            if search:
                params = parse_qs(search.lstrip("?"))
                company = params.get("company", ["Client"])[0]
                industry = params.get("industry", ["bfsi"])[0]
            return f"/subfunction?function_id={function_id}&company={company}&industry={industry}"
    return None


@callback(
    Output("treemap-redirect", "href", allow_duplicate=True),
    Input("treemap-ai-btn", "n_clicks"),
    State("treemap-url", "search"),
    prevent_initial_call=True,
)
def navigate_to_chatbot(n_clicks, search):
    if not n_clicks:
        return None
    company = "Client"
    industry = "bfsi"
    if search:
        params = parse_qs(search.lstrip("?"))
        company = params.get("company", ["Client"])[0]
        industry = params.get("industry", ["bfsi"])[0]
    return f"/chatbot?scope=overview&company={company}&industry={industry}"
