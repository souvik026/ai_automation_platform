from dash import html, dcc, Input, Output, State, callback, no_update, ctx
from urllib.parse import parse_qs, quote
import json

from utils.color_mapper import ColorMapper
from utils.l3_data_loader import L3DataLoader
from components.ask_ai import AskAI


# Sample AI use cases per dimension type — replace with LLM later
SAMPLE_USE_CASES = {
    "Data Availability": [
        "Automated data pipeline to consolidate fragmented records into a unified data lake",
        "OCR and NLP extraction to digitize unstructured documents and forms",
        "Real-time data quality monitoring with anomaly flagging",
    ],
    "Task Pattern Density": [
        "RPA bots to handle repetitive rule-based workflows end-to-end",
        "Intelligent workflow orchestration with exception routing to humans",
        "Process mining to identify and prioritize automation candidates",
    ],
    "Error Tolerance": [
        "AI-assisted human review with confidence scoring before action",
        "Automated audit trails and reconciliation checks at each step",
        "Dual-control validation layer for high-stakes decisions",
    ],
    "Regulatory Complexity": [
        "RegTech AI for real-time compliance monitoring and alert generation",
        "Automated regulatory reporting with jurisdictional rule engines",
        "NLP-based policy change detection and impact assessment",
    ],
    "Implementation Barriers": [
        "API-first integration layer to connect legacy systems without full migration",
        "Phased pilot approach: automate low-risk tasks first to build confidence",
        "Change management AI tooling for training and adoption tracking",
    ],
}

GENERIC_USE_CASES = [
    "Intelligent process automation to eliminate manual, repetitive steps",
    "AI-powered decision support with explainable recommendations",
    "Predictive analytics to anticipate issues before they escalate",
    "Natural language interfaces for staff productivity and query resolution",
    "Continuous monitoring and anomaly detection across operational data",
]


def _get_use_cases(l3: dict) -> list:
    """Generate contextual use cases based on highest-scoring dimensions."""
    if not l3:
        return GENERIC_USE_CASES
    sorted_dims = sorted(l3["dimensions"], key=lambda d: d["score"], reverse=True)
    cases = []
    for dim in sorted_dims[:2]:
        cases.extend(SAMPLE_USE_CASES.get(dim["name"], [])[:2])
    cases.extend(GENERIC_USE_CASES[:3])
    return list(dict.fromkeys(cases))[:5]  # deduplicate, keep 5


def _compute_thresholds(l3s: list) -> tuple:
    import numpy as np
    scores = [l["ai_score"] for l in l3s if l.get("ai_score") is not None]
    if not scores:
        return (4.0, 3.0)
    arr = np.array(scores)
    return float(np.percentile(arr, 80)), float(np.percentile(arr, 40))


def _score_color(score: float, p80: float = 4.0, p40: float = 3.0) -> str:
    if score >= p80:
        return "#1A7A4A"
    elif score >= p40:
        return "#52B788"
    else:
        return "#F4C542"


def _score_bar(score: float, p80: float = 4.0, p40: float = 3.0, max_score: float = 5.0) -> html.Div:
    color = _score_color(score, p80, p40)
    pct = (score / max_score) * 100
    return html.Div(className="l3-dim-bar-track", children=[
        html.Div(className="l3-dim-bar-fill", style={"width": f"{pct:.0f}%", "backgroundColor": color})
    ])


def _potential_label(score: float, p80: float = 4.0, p40: float = 3.0) -> str:
    if score >= p80:
        return "High"
    elif score >= p40:
        return "Medium"
    else:
        return "Low"


def _potential_class(score: float, p80: float = 4.0, p40: float = 3.0) -> str:
    if score >= p80:
        return "l3-potential-high"
    elif score >= p40:
        return "l3-potential-medium"
    else:
        return "l3-potential-low"


def _l3_card(l3: dict, index: int, p80: float = 4.0, p40: float = 3.0) -> html.Div:
    score = l3["ai_score"]
    color = _score_color(score, p80, p40)
    potential = _potential_label(score, p80, p40)
    pot_class = _potential_class(score, p80, p40)
    use_cases = _get_use_cases(l3)[:3]

    return html.Div(
        className="l3-card",
        id={"type": "l3-card", "index": index},
        n_clicks=0,
        children=[
            # Header: potential badge + name
            html.Div(className="l3-card-header", children=[
                html.Div(className=f"l3-potential-badge {pot_class}", children=f"{potential} Potential"),
                html.Div(className="l3-card-name", children=l3["name"]),
            ]),
            # Description
            html.P(l3["description"], className="l3-card-desc"),
            # Divider
            html.Div(className="l3-card-divider"),
            # AI Use Cases placeholder
            html.Div(className="l3-card-usecases-label", children="✦ AI Use Cases"),
            html.Div(className="l3-card-usecases", children=[
                html.Div(className="l3-card-uc-item", children=[
                    html.Span("→", className="l3-card-uc-arrow", style={"color": color}),
                    html.Span(uc, className="l3-card-uc-text"),
                ])
                for uc in use_cases
            ]),
            # Footer
            html.Div(className="l3-card-footer", children=[
                html.Span("AI Score: ", className="l3-card-score-label"),
                html.Span(f"{score:.1f}/5", className="l3-card-score-val", style={"color": color}),
                html.Span("  ·  Click for full insights →", className="l3-card-hint"),
            ]),
        ]
    )


def _build_panel_default(l3_count: int, l2_name: str) -> html.Div:
    return html.Div(className="insights-content", children=[
        html.Div(className="insights-section-header", children=[
            html.Span(l2_name, className="insights-section-title"),
            html.Span(f"{l3_count} tasks", className="insights-section-badge"),
        ]),
        html.Div(className="l3-panel-empty", children=[
            html.Div("◈", className="empty-icon"),
            html.P("Click any task card to see AI use cases and insights", style={"color": "#556888", "fontSize": "13px", "textAlign": "center"}),
        ]),
        html.Div("Template insights — connect LLM for dynamic analysis", className="insights-footnote"),
    ])


def _build_panel_selected(l3: dict, p80: float = 4.0, p40: float = 3.0) -> html.Div:
    score = l3["ai_score"]
    color = _score_color(score, p80, p40)
    label = _potential_label(score, p80, p40)
    use_cases = _get_use_cases(l3)

    return html.Div(className="insights-content", children=[
        # Header
        html.Div(className="insights-section-header", children=[
            html.Span(l3["name"], className="insights-section-title"),
            html.Span(label, className="insights-section-badge",
                      style={"backgroundColor": color, "color": "white", "borderColor": color}),
        ]),

        # AI Score display
        html.Div(className="sf-score-display", style={"marginBottom": "12px"}, children=[
            html.Div(className="sf-score-circle", style={"borderColor": color}, children=[
                html.Span(f"{score:.1f}", className="sf-score-big", style={"color": color}),
                html.Span("/5", className="sf-score-denom"),
            ]),
            html.Div(className="sf-score-bar-col", children=[
                html.Div("AI Automation Score", className="sf-detail-label"),
                html.Div(className="score-bar-track", children=[
                    html.Div(className="score-bar-fill", style={
                        "width": f"{(score / 5) * 100:.0f}%",
                        "backgroundColor": color
                    })
                ]),
                html.Div(f"{(score / 5) * 100:.0f}% of max potential", className="callout-sub"),
            ]),
        ]),

        # Dimension breakdown
        html.Div(className="insights-section-header", style={"marginTop": "8px"}, children=[
            html.Span("Score Breakdown", className="insights-section-title")
        ]),
        html.Div(className="l3-dim-breakdown", children=[
            html.Div(className="l3-dim-detail-row", children=[
                html.Div(className="l3-dim-detail-header", children=[
                    html.Span(dim["name"], className="l3-dim-detail-name"),
                    html.Span(f"{dim['score']:.0f}/5", className="l3-dim-detail-score",
                              style={"color": _score_color(dim["score"])}),
                ]),
                _score_bar(dim["score"]),
                html.Div(dim["label"], className="l3-dim-detail-label"),
            ])
            for dim in l3["dimensions"]
        ]),

        # AI Use Cases
        html.Div(className="insights-section-header", style={"marginTop": "16px"}, children=[
            html.Span("AI Use Cases", className="insights-section-title"),
            html.Span("sample", className="insights-section-badge"),
        ]),
        html.Div(className="l3-use-cases", children=[
            html.Div(className="l3-use-case-item", children=[
                html.Span(f"{i+1}", className="l3-uc-num"),
                html.Span(uc, className="l3-uc-text"),
            ])
            for i, uc in enumerate(use_cases)
        ]),

        html.Div("Sample use cases — connect LLM for function-specific AI insights", className="insights-footnote"),
    ])


def _parse_params(search: str) -> tuple:
    function_id, l2_name, l1_name, company, industry, revenue_m = "ops", "", "", "Client", "bfsi", None
    if search:
        params = parse_qs(search.lstrip("?"))
        function_id = params.get("function_id", ["ops"])[0]
        l2_name = params.get("l2_name", [""])[0]
        l1_name = params.get("l1_name", [""])[0]
        company = params.get("company", ["Client"])[0]
        industry = params.get("industry", ["bfsi"])[0]
        rev_str = params.get("revenue", [None])[0]
        if rev_str:
            try:
                revenue_m = float(rev_str)
            except ValueError:
                pass
    return function_id, l2_name, l1_name, company, industry, revenue_m


def l3_breakdown_layout():
    return html.Div(
        className="page-wrapper",
        style={"display": "flex", "flexDirection": "column", "height": "100vh", "overflow": "hidden"},
        children=[
            dcc.Location(id="l3-url", refresh=False),
            dcc.Store(id="l3-active-tab", data="summary"),
            dcc.Store(id="l3-selected-index", data=None),

            # Header
            html.Div(className="page-header", children=[
                html.Div(className="header-left", children=[
                    html.A(id="l3-back-link", children=[html.Span("←"), " Subfunctions"], href="/subfunction", className="back-link"),
                    html.Div(className="header-title-block", children=[
                        html.Div(className="header-brand", children=[html.Span("AIP", className="brand-accent"), " Platform"]),
                        html.H2(id="l3-page-title", className="page-title"),
                    ]),
                ]),
            ]),

            # Body
            html.Div(
                style={"display": "flex", "flex": "1", "overflow": "hidden", "minHeight": "0"},
                children=[
                    # Left: card grid
                    html.Div(
                        style={"flex": "1", "minWidth": "0", "overflowY": "auto", "padding": "1.5rem"},
                        children=[
                            html.Div(id="l3-card-grid", className="l3-card-grid"),
                        ]
                    ),
                    # Right: insight panel
                    html.Div(
                        style={
                            "width": "340px", "flexShrink": "0",
                            "background": "#111f38", "borderLeft": "1px solid #1e3355",
                            "display": "flex", "flexDirection": "column", "overflow": "hidden"
                        },
                        children=[
                            html.Div(className="insight-tabs", children=[
                                html.Button("Summary", id="l3-tab-summary", className="insight-tab insight-tab-active", n_clicks=0),
                                html.Button("Ask AI", id="l3-tab-askai", className="insight-tab", n_clicks=0),
                            ]),
                            html.Div(id="l3-tab-content", className="insight-tab-body",
                                     children=[html.Div("Loading...", className="insight-loading")]),
                        ]
                    ),
                ]
            ),
        ]
    )


@callback(
    Output("l3-card-grid", "children"),
    Output("l3-page-title", "children"),
    Output("l3-back-link", "href"),
    Output("l3-tab-content", "children"),
    Input("l3-url", "search"),
)
def load_l3_page(search):
    function_id, l2_name, l1_name, company, industry, revenue_m = _parse_params(search)

    l3s = L3DataLoader.get_l3_functions(industry, l1_name, l2_name)
    # Ensure L3 color calibration is active for this industry
    ColorMapper.set_active_industry(f"{industry.strip().lower()}_l3")
    l3s = sorted(l3s, key=lambda x: x["ai_score"], reverse=True)
    p80, p40 = _compute_thresholds(l3s)

    cards = [_l3_card(l3, i, p80, p40) for i, l3 in enumerate(l3s)] if l3s else [
        html.Div("No L3 data found for this subfunction.", className="insight-empty")
    ]

    title = f"{l2_name} — Task Breakdown"
    back_href = f"/subfunction?function_id={function_id}&company={quote(company)}&industry={industry}"
    if revenue_m:
        back_href += f"&revenue={revenue_m}"

    panel = _build_panel_default(len(l3s), l2_name)
    return cards, title, back_href, panel


@callback(
    Output("l3-tab-content", "children", allow_duplicate=True),
    Output("l3-tab-summary", "className"),
    Output("l3-tab-askai", "className"),
    Output("l3-active-tab", "data"),
    Output("l3-selected-index", "data"),
    Input({"type": "l3-card", "index": "__ALL__"}, "n_clicks"),
    State("l3-url", "search"),
    State("l3-active-tab", "data"),
    prevent_initial_call=True,
)
def on_card_click(n_clicks_list, search, active_tab):
    if not ctx.triggered_id or not any(n_clicks_list):
        return no_update, no_update, no_update, no_update, no_update

    index = ctx.triggered_id["index"]
    function_id, l2_name, l1_name, company, industry, revenue_m = _parse_params(search)
    l3s = L3DataLoader.get_l3_functions(industry, l1_name, l2_name)

    if index >= len(l3s):
        return no_update, no_update, no_update, no_update, no_update

    selected = l3s[index]
    p80, p40 = _compute_thresholds(l3s)
    panel = _build_panel_selected(selected, p80, p40)
    return panel, "insight-tab insight-tab-active", "insight-tab", "summary", index


@callback(
    Output("l3-tab-content", "children", allow_duplicate=True),
    Output("l3-tab-summary", "className", allow_duplicate=True),
    Output("l3-tab-askai", "className", allow_duplicate=True),
    Output("l3-active-tab", "data", allow_duplicate=True),
    Input("l3-tab-summary", "n_clicks"),
    Input("l3-tab-askai", "n_clicks"),
    State("l3-url", "search"),
    State("l3-selected-index", "data"),
    prevent_initial_call=True,
)
def switch_l3_tab(sum_clicks, ai_clicks, search, selected_index):
    triggered = ctx.triggered_id
    function_id, l2_name, l1_name, company, industry, revenue_m = _parse_params(search)
    l3s = L3DataLoader.get_l3_functions(industry, l1_name, l2_name)

    if triggered == "l3-tab-summary":
        if selected_index is not None and selected_index < len(l3s):
            p80, p40 = _compute_thresholds(l3s)
            content = _build_panel_selected(l3s[selected_index], p80, p40)
        else:
            content = _build_panel_default(len(l3s), l2_name)
        return content, "insight-tab insight-tab-active", "insight-tab", "summary"

    if triggered == "l3-tab-askai":
        if selected_index is not None and selected_index < len(l3s):
            context_name = l3s[selected_index]["name"]
        else:
            context_name = l2_name
        content = AskAI.build_panel(page="l2", context_name=context_name)
        return content, "insight-tab", "insight-tab insight-tab-active", "askai"

    return no_update, no_update, no_update, no_update