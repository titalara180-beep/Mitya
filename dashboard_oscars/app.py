#plotly interactive plots
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
from dash import dash_table
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# -------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------
df = pd.read_csv("oscars.csv")
df.columns = df.columns.str.strip()

# -------------------------------------------------------------
# CREATE DASH APP
# -------------------------------------------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# -------------------------------------------------------------
# LAYOUT
# -------------------------------------------------------------
app.layout = html.Div([
    html.H1("🎬 Oscars Box Office & Critical Acclaimed Intelligence", style={"textAlign": "center", "color": "#B8860B"}),
    html.P("An interactive dashboard exploring box office earnings, IMDb ratings, and Academy Awards success for legendary films.", style={"textAlign": "center", "fontStyle": "italic"}),

    dcc.Tabs(id="mainTabs", value="overviewTab", children=[
        dcc.Tab(label="Overview", value="overviewTab"),
        dcc.Tab(label="Box Office vs Ratings", value="graphicsTab"),
        dcc.Tab(label="Data Table", value="tableTab"),
        dcc.Tab(label="Summary Statistics", value="summaryTab"),
    ]),

    html.Hr(),

    # ------------------- FILTERS -------------------
    html.Div([
        html.Div([
            html.Label("Select Genre:"),
            dcc.Dropdown(
                id="genreFilter",
                options=[{"label": "All", "value": "All"}] +
                        [{"label": g, "value": g} for g in sorted(df["genre"].unique())],
                value=["All"],
                multi=True,
                style={"width": "95%"}
            )
        ], style={'width': '35%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Minimum Box Office ($M):"),
            dcc.Slider(
                id="boxOfficeFilter",
                min=float(df["box_office_millions"].min()),
                max=float(df["box_office_millions"].max()),
                value=float(df["box_office_millions"].min()),
                marks={0: '0M', 300: '300M', 600: '600M', 1000: '1000M'},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'width': '60%', 'display': 'inline-block', 'paddingLeft': '5%'})
    ], style={"padding": "15px", "backgroundColor": "#f9f9f9", "borderRadius": "5px"}),

    html.Hr(),

    html.Div(id="tabContent"),
    dcc.Store(id="filteredData")
])

# -------------------------------------------------------------
# CALLBACK → FILTER DATA
# -------------------------------------------------------------
@app.callback(
    Output("filteredData", "data"),
    [Input("genreFilter", "value"),
     Input("boxOfficeFilter", "value")]
)
def filter_data(genresel, minbox):
    dff = df.copy()

    if "All" not in genresel:
        dff = dff[dff["genre"].isin(genresel)]

    dff = dff[dff["box_office_millions"] >= minbox]
    return dff.to_dict("records")

# -------------------------------------------------------------
# CALLBACK → MAIN TABS
# -------------------------------------------------------------
@app.callback(
    Output("tabContent", "children"),
    [Input("mainTabs", "value"),
     Input("filteredData", "data")]
)
def render_tabs(tab, data):
    if not data:
        return html.Div("Loading data...")

    dff = pd.DataFrame(data)

    if tab == "overviewTab":
        fig = go.Figure(go.Histogram(x=dff["total_wins"], marker_color="#B8860B"))
        fig.update_layout(title="Distribution of Total Oscar Wins (Real Masterpieces)", xaxis_title="Wins", yaxis_title="Count")

        return html.Div([
            html.H3("Overview of Academy Award Winning Masterpieces"),
            html.P("This dashboard analyzes iconic Best Picture winners, evaluating their commercial box office earnings against public IMDb feedback."),
            dcc.Graph(figure=fig),
            html.Div([
                html.Div([
                    html.H4("Key Insight 1"),
                    html.P("Blockbusters like Titanic and Lord of the Rings prove that massive commercial success can coexist with sweeping Oscar records.")
                ], style={"width": "48%", "display": "inline-block", "padding": "10px", "border": "1px solid #ddd"}),
                html.Div([
                    html.H4("Key Insight 2"),
                    html.P("Biographies and Dramas consistently secure high critical acclaim and Academy recognition across decades.")
                ], style={"width": "48%", "display": "inline-block", "padding": "10px", "border": "1px solid #ddd", "float": "right"})
            ])
        ])

    if tab == "graphicsTab":
        return html.Div([
            dcc.Tabs(id="nestedTabs", value="scatter", children=[
                dcc.Tab(label="Box Office vs IMDb Rating", value="scatter"),
                dcc.Tab(label="Average Wins by Genre", value="bar"),
                dcc.Tab(label="IMDb Rating Distribution", value="box")
            ]),
            html.Div(id="nestedContent", style={"paddingTop": "20px"})
        ])

    if tab == "tableTab":
        return html.Div([
            html.H3("Filtered Data Table (6 Columns - Real Films)"),
            dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in dff.columns],
                data=dff.to_dict("records"),
                page_size=12,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "center"},
                filter_action="native",
                sort_action="native"
            )
        ])

    if tab == "summaryTab":
        return html.Div([
            html.H3("Summary Statistics"),
            html.Pre(dff.describe().to_string(), style={"background": "#f4f4f4", "padding": "15px", "borderRadius": "5px"})
        ])

# -------------------------------------------------------------
# CALLBACK → NESTED GRAPH TABS
# -------------------------------------------------------------
@app.callback(
    Output("nestedContent", "children"),
    [Input("nestedTabs", "value"),
     Input("filteredData", "data")]
)
def nested_graphs(nestedTab, data):
    if not data:
        return html.Div("Waiting for data...")

    dff = pd.DataFrame(data)

    if nestedTab == "scatter":
        fig = go.Figure(data=go.Scatter(
            x=dff["box_office_millions"],
            y=dff["imdb_rating"],
            mode="markers+text",
            text=dff["film"],
            textposition="top center",
            marker=dict(
                size=12,
                color=dff["total_wins"],
                colorscale="Sunset",
                showscale=True,
                colorbar=dict(title="Total Wins")
            )
        ))
        fig.update_layout(title="Box Office vs IMDb Rating (Hover or check film labels)", xaxis_title="Box Office ($M)", yaxis_title="IMDb Rating", height=600)
        return dcc.Graph(figure=fig)

    if nestedTab == "bar":
        if len(dff) > 0:
            avg_wins = dff.groupby("genre")["total_wins"].mean().reset_index()
            fig = go.Figure(go.Bar(x=avg_wins["genre"], y=avg_wins["total_wins"], marker_color="#DAA520"))
            fig.update_layout(title="Average Total Wins by Genre", xaxis_title="Genre", yaxis_title="Average Wins")
        else:
            fig = go.Figure()
        return dcc.Graph(figure=fig)

    if nestedTab == "box":
        fig = go.Figure(data=go.Box(y=dff["imdb_rating"], name="IMDb Rating", marker_color="#B8860B"))
        fig.update_layout(title="Distribution of IMDb Ratings")
        return dcc.Graph(figure=fig)

# -------------------------------------------------------------
# RUN APP
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
