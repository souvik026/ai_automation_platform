from dash import html, dcc, Input, Output, State, callback, no_update
from urllib.parse import parse_qs

from utils.data_loader import DataLoader
from utils.calculations import AutomationCalculator
from utils.color_mapper import ColorMapper


QUESTIONS = [
    {"id": "q1", "label": "Top Automation Opportunities"},
    {"id": "q2", "label": "AI Use Cases"},
    {"id": "q3", "label": "Key Challenges"},
    {"id": "q4", "label": "Where to Start"},
    {"id": "q5", "label": "Expected ROI"},
    {"id": "q6", "label": "How can Straive Help"},
]

# LLM INTEGRATION POINT
# Replace build_static_response() with a call to your LLM API:
# e.g. response = openai.chat.completions.create(
#     model="gpt-4o",
#     messages=[{"role": "user", "content": build_prompt(function_data, question_id)}]
# )
# return response.choices[0].message.content
DUMMY_RESPONSES = {
    "q1": [
        "High-volume, rule-based processes with structured data inputs",
        "Document-heavy workflows with repetitive extraction tasks",
        "Exception handling and reconciliation processes",
        "Reporting pipelines with predictable data flows",
        "Customer-facing query resolution with defined answer sets",
    ],
    "q2": [
        "Intelligent Document Processing (IDP) using OCR + LLMs",
        "ML-based predictive scoring and risk models",
        "Conversational AI for internal and external query handling",
        "Process mining to identify bottleneck workflows",
        "Robotic Process Automation (RPA) for structured data tasks",
        "NLP-based classification and routing engines",
    ],
    "q3": [
        "Legacy system integration and data quality gaps",
        "Change management and workforce reskilling needs",
        "Regulatory compliance requirements limiting full automation",
        "Model explainability demands from audit and risk teams",
        "Siloed data making it hard to build unified training sets",
    ],
    "q4": [
        "Prioritise high-repeatability, high-volume processes first",
        "Run a 6-week AI maturity assessment to baseline current state",
        "Pilot in one subfunction before scaling across the function",
        "Establish a data governance framework as a prerequisite",
        "Identify a cross-functional AI champion to sponsor the program",
    ],
    "q5": [
        "20–40% reduction in processing turnaround time (TAT)",
        "30–50% decrease in manual effort (FTE redeployment)",
        "60–80% reduction in error rates for structured data tasks",
        "Payback period typically 12–18 months post-implementation",
        "Additional uplift from improved compliance and audit outcomes",
    ],
    "q6": [
        "Straive delivers end-to-end AI operationalization — from strategy to deployment",
        "Pre-built BFSI AI accelerators reduce implementation time by 40%",
        "Dedicated change management and training programs for workforce transition",
        "Regulatory-aware AI models designed for BFSI compliance requirements",
        "Managed AI services model for ongoing model monitoring and improvement",
        "Proven track record across Tier-1 banks, insurers, and NBFCs globally",
    ],
}


def chatbot_layout():
    return html.Div(
        className="page-wrapper",
        children=[
            dcc.Location(id="chatbot-url", refresh=False),
            dcc.Store(id="chat-messages-store", data=[]),

            # Header
            html.Div(
                className="page-header",
                children=[
                    html.Div(
                        className="header-left",
                        children=[
                            html.A(
                                id="chatbot-back-link",
                                children=[html.Span("←"), " Back"],
                                href="/treemap",
                                className="back-link"
                            ),
                            html.Div(
                                className="header-title-block",
                                children=[
                                    html.Div(
                                        className="header-brand",
                                        children=[html.Span("AIP", className="brand-accent"), " AI Analyst"]
                                    ),
                                    html.H2(id="chatbot-context-title", className="page-title"),
                                ]
                            ),
                        ]
                    ),
                    html.Div(
                        className="header-right",
                        children=[
                            html.Div(
                                className="ai-status-badge",
                                children=[
                                    html.Span(className="status-dot"),
                                    html.Span("Demo Mode — Static Responses", className="status-text"),
                                ]
                            )
                        ]
                    ),
                ]
            ),

            # Chat layout
            html.Div(
                className="chat-layout",
                children=[
                    # Left: question panel
                    html.Div(
                        className="chat-questions-panel",
                        children=[
                            html.H4("Ask a Question", className="questions-panel-title"),
                            html.P("Select a question to get AI-powered insights:", className="questions-hint"),
                            html.Div(
                                className="question-chips",
                                children=[
                                    html.Button(
                                        q["label"],
                                        id={"type": "question-chip", "index": q["id"]},
                                        className="question-chip",
                                        n_clicks=0,
                                    )
                                    for q in QUESTIONS
                                ]
                            ),
                            html.Div(className="questions-divider"),
                            html.Div(
                                className="context-info-box",
                                id="chatbot-context-box",
                            ),
                        ]
                    ),

                    # Right: chat window
                    html.Div(
                        className="chat-window-panel",
                        children=[
                            html.Div(
                                id="chat-messages",
                                className="chat-messages",
                                children=[
                                    _welcome_bubble(),
                                ]
                            ),
                        ]
                    ),
                ]
            ),

            # Footer
            html.Div(
                className="chat-footer",
                children=[
                    html.Span("⚡ "),
                    html.Span(
                        "Responses based on BFSI industry benchmarks and Straive research. ",
                        className="footer-main"
                    ),
                    html.Span(
                        "Connect LLM for dynamic, client-specific analysis.",
                        className="footer-hint"
                    ),
                ]
            ),
        ]
    )


def _welcome_bubble():
    return html.Div(
        className="chat-bubble-wrapper bot-wrapper",
        children=[
            html.Div(className="chat-avatar bot-avatar", children=["✦"]),
            html.Div(
                className="chat-bubble bot-bubble",
                children=[
                    html.P("Hello! I'm the AIIF AI Analyst.", className="bubble-intro"),
                    html.P(
                        "Select a question from the panel on the left to get insights on automation opportunities, "
                        "use cases, challenges, and ROI for this function.",
                        className="bubble-body"
                    ),
                    html.P(
                        "Note: This is a demo — responses are illustrative. Connect an LLM for live analysis.",
                        className="bubble-note"
                    ),
                ]
            ),
        ]
    )


def _user_bubble(text: str) -> html.Div:
    return html.Div(
        className="chat-bubble-wrapper user-wrapper",
        children=[
            html.Div(className="chat-bubble user-bubble", children=[text]),
            html.Div(className="chat-avatar user-avatar", children=["👤"]),
        ]
    )


def _bot_bubble(question_id: str, function_name: str) -> html.Div:
    bullets = DUMMY_RESPONSES.get(question_id, ["No response available."])
    return html.Div(
        className="chat-bubble-wrapper bot-wrapper",
        children=[
            html.Div(className="chat-avatar bot-avatar", children=["✦"]),
            html.Div(
                className="chat-bubble bot-bubble",
                children=[
                    html.P(
                        f"Based on BFSI industry data for {function_name}:",
                        className="bubble-intro"
                    ),
                    html.Ul(
                        className="bubble-list",
                        children=[html.Li(b) for b in bullets]
                    ),
                ]
            ),
        ]
    )


@callback(
    Output("chatbot-context-title", "children"),
    Output("chatbot-back-link", "href"),
    Output("chatbot-context-box", "children"),
    Input("chatbot-url", "search"),
)
def load_chatbot_context(search):
    scope = "overview"
    function_id = None
    company = "Client"
    industry = "bfsi"

    if search:
        params = parse_qs(search.lstrip("?"))
        scope = params.get("scope", ["overview"])[0]
        function_id = params.get("function_id", [None])[0]
        company = params.get("company", ["Client"])[0].replace("+", " ")
        industry = params.get("industry", ["bfsi"])[0]

    if scope == "function" and function_id:
        func = DataLoader.get_function(industry, function_id)
        func_name = func["name"] if func else "Unknown Function"
        title = f"Analysing: {func_name}"
        back_href = f"/subfunction?function_id={function_id}&company={company.replace(' ', '+')}&industry={industry}"
        score = AutomationCalculator.get_function_automation_score(func) if func else 0
        color = ColorMapper.get_color(score)
        label = ColorMapper.get_label(score)
        sf_count = len(func["subfunctions"]) if func else 0
        context_box = html.Div([
            html.P(func_name, className="ctx-func-name"),
            html.Div(
                className="ctx-badge",
                style={"backgroundColor": color},
                children=label
            ),
            html.Div(className="ctx-stats", children=[
                html.Div([html.Span(f"{score:.1f}/20", className="ctx-stat-val"), html.Span("Automation Score", className="ctx-stat-lbl")]),
                html.Div([html.Span(str(sf_count), className="ctx-stat-val"), html.Span("Subfunctions", className="ctx-stat-lbl")]),
            ])
        ])
    else:
        industry_data = DataLoader.load_industry(industry)
        title = f"Analysing: All {industry_data['industry']} Functions"
        back_href = f"/treemap?company={company.replace(' ', '+')}&industry={industry}"
        n_funcs = len(industry_data["functions"])
        context_box = html.Div([
            html.P("Full Industry View", className="ctx-func-name"),
            html.Div(className="ctx-stats", children=[
                html.Div([html.Span(str(n_funcs), className="ctx-stat-val"), html.Span("Functions", className="ctx-stat-lbl")]),
                html.Div([html.Span(industry_data["industry"], className="ctx-stat-val"), html.Span("Industry", className="ctx-stat-lbl")]),
            ])
        ])

    return title, back_href, context_box


@callback(
    Output("chat-messages", "children"),
    Input({"type": "question-chip", "index": "q1"}, "n_clicks"),
    Input({"type": "question-chip", "index": "q2"}, "n_clicks"),
    Input({"type": "question-chip", "index": "q3"}, "n_clicks"),
    Input({"type": "question-chip", "index": "q4"}, "n_clicks"),
    Input({"type": "question-chip", "index": "q5"}, "n_clicks"),
    Input({"type": "question-chip", "index": "q6"}, "n_clicks"),
    State("chat-messages", "children"),
    State("chatbot-url", "search"),
    prevent_initial_call=True,
)
def handle_question(q1, q2, q3, q4, q5, q6, current_messages, search):
    from dash import ctx
    if not ctx.triggered_id:
        return no_update

    question_id = ctx.triggered_id["index"]
    question_label = next((q["label"] for q in QUESTIONS if q["id"] == question_id), "")

    function_name = "BFSI"
    if search:
        params = parse_qs(search.lstrip("?"))
        scope = params.get("scope", ["overview"])[0]
        if scope == "function":
            function_id = params.get("function_id", [None])[0]
            industry = params.get("industry", ["bfsi"])[0]
            if function_id:
                func = DataLoader.get_function(industry, function_id)
                if func:
                    function_name = func["name"]

    if current_messages is None:
        current_messages = [_welcome_bubble()]

    new_messages = list(current_messages) + [
        _user_bubble(question_label),
        _bot_bubble(question_id, function_name),
    ]
    return new_messages
