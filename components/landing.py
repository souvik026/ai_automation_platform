from dash import html, dcc, Input, Output, State, callback
import dash
from utils.data_loader import DataLoader


def _get_industry_options():
    try:
        available = DataLoader.get_available_industries()
        return [{"label": ind, "value": ind} for ind in available]
    except Exception:
        return [{"label": "Banking", "value": "Banking"}]


def landing_layout():
    return html.Div(
        className="landing-page",
        children=[
            html.Div(className="bg-orb orb-1"),
            html.Div(className="bg-orb orb-2"),
            html.Div(className="bg-orb orb-3"),
            html.Div(
                className="landing-content",
                children=[
                    # Badge
                    html.Div(
                        className="landing-badge",
                        children=[
                            html.Span("⬡", className="badge-icon"),
                            html.Span("Straive AI Practice", className="badge-text"),
                        ]
                    ),
                    # Main title
                    html.H1(
                        children=[
                            html.Span("Automation", className="title-accent"),
                            html.Br(),
                            html.Span("Index Platform", className="title-main"),
                        ],
                        className="landing-title"
                    ),
                    html.P(
                        "Identify AI Automation Opportunities Across Industry Functions",
                        className="landing-tagline"
                    ),
                    html.Div(className="landing-divider"),
                    # Form card
                    html.Div(
                        className="landing-form-card",
                        children=[
                            html.Div(
                                className="form-group",
                                children=[
                                    html.Label("Client Company Name", className="form-label"),
                                    dcc.Input(
                                        id="company-input",
                                        type="text",
                                        placeholder="e.g. HDFC Bank, JP Morgan Chase...",
                                        className="form-input",
                                        debounce=False,
                                        style={"fontSize": "16px", "padding": "14px 18px", "height": "52px"},
                                    ),
                                ]
                            ),
                            html.Div(
                                className="form-group",
                                children=[
                                    html.Label("Industry", className="form-label"),
                                    dcc.Dropdown(
                                        id="industry-dropdown",
                                        options=_get_industry_options(),
                                        value=None,
                                        placeholder="Select industry...",
                                        clearable=False,
                                        className="form-dropdown",
                                        optionHeight=52,
                                        style={"fontSize": "15px"},
                                    ),
                                ]
                            ),
                            html.Div(id="landing-error", className="form-error"),
                            html.Button(
                                children=[
                                    html.Span("Explore Automation Opportunities"),
                                    html.Span("→", className="btn-arrow"),
                                ],
                                id="explore-btn",
                                className="cta-button",
                                n_clicks=0,
                            ),
                        ]
                    ),
                    html.P(
                        "Industries loaded from backend_data.xlsx",
                        className="landing-footnote"
                    ),
                ]
            ),
            dcc.Location(id="landing-redirect", refresh=True),
        ]
    )


@callback(
    Output("landing-redirect", "href"),
    Output("landing-error", "children"),
    Input("explore-btn", "n_clicks"),
    State("company-input", "value"),
    State("industry-dropdown", "value"),
    prevent_initial_call=True,
)
def handle_explore(n_clicks, company, industry):
    if not company or not company.strip():
        return dash.no_update, "⚠ Please enter a client company name."
    if not industry:
        return dash.no_update, "⚠ Please select an industry."
    safe_company = company.strip().replace(" ", "+")
    return f"/treemap?company={safe_company}&industry={industry}", ""