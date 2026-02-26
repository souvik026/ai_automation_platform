from dash import html, dcc, Input, Output, State, callback, no_update, ctx


QUESTIONS_L1 = [
    {"id": "q1", "label": "Where should we start?"},
    {"id": "q2", "label": "Biggest opportunities?"},
    {"id": "q3", "label": "Expected ROI?"},
    {"id": "q4", "label": "Key challenges?"},
    {"id": "q5", "label": "How can Straive help?"},
]

QUESTIONS_L2 = [
    {"id": "q1", "label": "Automate this function?"},
    {"id": "q2", "label": "Key AI use cases?"},
    {"id": "q3", "label": "What data is needed?"},
    {"id": "q4", "label": "Timeline & effort?"},
    {"id": "q5", "label": "How can Straive help?"},
]

RESPONSES = {
    "q1": {
        "l1": "Start with the highest-scoring function that also has the largest cost exposure. Run an 8–12 week pilot to validate ROI before scaling across the organisation.",
        "l2": "Begin with the highest-scoring subfunction. Map current workflows, identify repetitive rule-based tasks, and deploy an RPA or AI pilot to demonstrate early savings.",
    },
    "q2": {
        "l1": "Functions scoring above 3.5/5 with >5% revenue cost exposure are the clearest wins — high volume, structured data, and repetitive patterns ideal for automation.",
        "l2": "The top subfunctions by score are your priority. Intelligent document processing, workflow automation, and predictive analytics are the most commonly applicable patterns.",
    },
    "q3": {
        "l1": "Industry benchmarks show 20–40% cost reduction within 18–24 months for high-potential functions. Combined with the revenue exposure shown, the addressable savings are significant.",
        "l2": "Automation pilots in this type of function typically achieve payback within 6–12 months. Straive can model exact ROI using your headcount and volume data.",
    },
    "q4": {
        "l1": "Key challenges include data quality, change management, regulatory compliance, and legacy system integration. A phased approach with clear governance mitigates these.",
        "l2": "Challenges here may include unstructured data handling, exception management, and model accuracy thresholds — all solvable with the right architecture and oversight.",
    },
    "q5": {
        "l1": "Straive offers end-to-end support: opportunity assessment, solution design, pilot delivery, and scale-up — with deep domain expertise for this industry.",
        "l2": "Straive can deploy a targeted AI solution for this function within 8–16 weeks, covering data engineering, model development, integration, and post-deployment support.",
    },
}


def _user_bubble(text):
    return html.Div(className="user-bubble", children=text)


def _bot_bubble(text):
    return html.Div(className="bot-bubble", children=[html.Span("✦ ", className="bot-icon"), text])


class AskAI:
    """
    Renders the Ask AI tab panel.
    # LLM INTEGRATION POINT: Replace RESPONSES lookup with API call.
    """

    @staticmethod
    def build_panel(page: str = "l1", context_name: str = "") -> html.Div:
        questions = QUESTIONS_L1 if page == "l1" else QUESTIONS_L2
        msg_id = f"ask-ai-messages-{page}"
        input_id = f"ask-ai-input-{page}"
        send_id = f"ask-ai-send-{page}"

        return html.Div(
            className="ask-ai-content",
            children=[
                html.Div(className="ask-ai-context-bar", children=[
                    html.Span("✦", className="ask-ai-icon"),
                    html.Span(
                        f"Analysing: {context_name}" if context_name else "Analysing current view",
                        className="ask-ai-context-text"
                    ),
                    html.Span("Demo Mode", className="ai-status-badge"),
                ]),
                html.Div(
                    id=msg_id,
                    className="ask-ai-messages",
                    children=[
                        _bot_bubble(f"Hello! I'm your AI advisor. Select a question below or type your own to get insights about {context_name or 'this view'}.")
                    ]
                ),
                html.Div(
                    className="ask-ai-chips",
                    children=[
                        html.Button(
                            q["label"],
                            id={"type": f"ask-ai-chip-{page}", "index": q["id"]},
                            className="question-chip",
                            n_clicks=0,
                        )
                        for q in questions
                    ]
                ),
                html.Div(className="ask-ai-input-row", children=[
                    dcc.Input(id=input_id, type="text", placeholder="Ask a question...", className="ask-ai-input", debounce=True),
                    html.Button("→", id=send_id, className="ask-ai-send-btn", n_clicks=0),
                ]),
                html.Div("Responses are illustrative. Connect LLM for live AI insights.", className="insights-footnote"),
            ]
        )


@callback(
    Output("ask-ai-messages-l1", "children"),
    Input({"type": "ask-ai-chip-l1", "index": "__ALL__"}, "n_clicks"),
    Input("ask-ai-send-l1", "n_clicks"),
    State("ask-ai-input-l1", "value"),
    State("ask-ai-messages-l1", "children"),
    prevent_initial_call=True,
)
def handle_l1_message(chip_clicks, send_clicks, input_value, current_messages):
    triggered = ctx.triggered_id
    messages = list(current_messages or [])
    if isinstance(triggered, dict) and triggered.get("type") == "ask-ai-chip-l1":
        qid = triggered["index"]
        label = {q["id"]: q["label"] for q in QUESTIONS_L1}.get(qid, "")
        response = RESPONSES.get(qid, {}).get("l1", "No response available.")
        messages.append(_user_bubble(label))
        messages.append(_bot_bubble(response))
        return messages
    if triggered == "ask-ai-send-l1" and input_value and input_value.strip():
        messages.append(_user_bubble(input_value.strip()))
        messages.append(_bot_bubble("This is a demo response — connect the LLM integration point in ask_ai.py for live answers."))
        return messages
    return no_update


@callback(
    Output("ask-ai-messages-l2", "children"),
    Input({"type": "ask-ai-chip-l2", "index": "__ALL__"}, "n_clicks"),
    Input("ask-ai-send-l2", "n_clicks"),
    State("ask-ai-input-l2", "value"),
    State("ask-ai-messages-l2", "children"),
    prevent_initial_call=True,
)
def handle_l2_message(chip_clicks, send_clicks, input_value, current_messages):
    triggered = ctx.triggered_id
    messages = list(current_messages or [])
    if isinstance(triggered, dict) and triggered.get("type") == "ask-ai-chip-l2":
        qid = triggered["index"]
        label = {q["id"]: q["label"] for q in QUESTIONS_L2}.get(qid, "")
        response = RESPONSES.get(qid, {}).get("l2", "No response available.")
        messages.append(_user_bubble(label))
        messages.append(_bot_bubble(response))
        return messages
    if triggered == "ask-ai-send-l2" and input_value and input_value.strip():
        messages.append(_user_bubble(input_value.strip()))
        messages.append(_bot_bubble("This is a demo response — connect the LLM integration point in ask_ai.py for live answers."))
        return messages
    return no_update