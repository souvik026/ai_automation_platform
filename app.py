import dash
from dash import dcc, html, Input, Output

# Import page layouts (registers their callbacks automatically)
from components.landing import landing_layout
from components.treemap import treemap_layout
from components.subfunction import subfunction_layout
from components.chatbot import chatbot_layout

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="AIIF Platform — Straive",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    html.Div(id="page-content"),
])


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname == "/treemap":
        return treemap_layout()
    if pathname == "/subfunction":
        return subfunction_layout()
    if pathname == "/chatbot":
        return chatbot_layout()
    return landing_layout()


if __name__ == "__main__":
    app.run(debug=True, port=8050)
