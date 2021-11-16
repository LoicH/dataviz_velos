import pandas as pd
import dash

import numpy as np
from dash import dcc
from dash import html

import plotly.express as px

external_stylesheets = ["https://www.w3schools.com/w3css/4/w3.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


data_folder = "data/"
data = pd.read_csv(data_folder + "clean_data.csv")
data = data.loc[
    :,
    [
        "X",
        "Y",
        "capacite",
        "couverture",
        "surveillance",
        "lumiere",
        "proprietaire",
        "gestionnaire",
    ],
]


# Calcul des capacités
gest_capas = data.loc[:, ["gestionnaire", "capacite"]]
gest_capas = gest_capas.dropna()
gest_capas = (
    gest_capas.groupby("gestionnaire")
    .agg(c=("capacite", "count"), capacite_totale=("capacite", "sum"))
    .reset_index()
    .sort_values("capacite_totale", ascending=False)
)
print(gest_capas.quantile())


confort = ["couverture", "surveillance", "lumiere"]
selection_confort = []
for c in confort:
    selection_confort.append(html.P("Influence de la {}".format(c)))
    selection_confort.append(html.Div(id="weight-{}".format(c), children=[]))
    selection_confort.append(
        dcc.Slider(id="slider-{}".format(c), min=0, max=1, step=0.1, value=1)
    )

app.layout = html.Div(
    [
        html.Div([html.H1("Stationnements Vélo")], className="w3-container"),
        # Capacité des abris
        html.Div(
            [
                html.H2("Affichage des places de vélos"),
                html.P("Recherche (pas besoin de majuscules) :"),
                dcc.Textarea(
                    id="select_gestionnaire", placeholder="Zone de recherche", value=""
                ),
                html.Div(id="text_selection", children=[]),
            ],
            className="w3-container w3-blue",
        ),
        html.Br(),
        # Confort des abris
        html.Div(
            [
                html.H3("Meilleurs gestionnaires"),
                dcc.Graph(id="top_gestionnaires", figure={}),
                html.H3("Emplacements des abris vélos"),
                dcc.Graph(id="map_capacites", figure={}),
            ],
            className="w3-container w3-light-blue",
        ),
        html.Div(
            [html.H2("Confort dans les abris")]
            + selection_confort
            + [dcc.Graph(id="confort-gestionnaires", figure={})],
            className="w3-container w3-green",
        ),
    ]
)


@app.callback(
    [
        dash.Output("text_selection", "children"),
        dash.Output("top_gestionnaires", "figure"),
        dash.Output("map_capacites", "figure"),
    ],
    [dash.Input("select_gestionnaire", "value")],
)
def update_capas(selection: str):
    selection = selection.lower()
    print(selection)
    container = "Selection = {}".format(selection)
    bar_top_gestionnaires = px.bar(
        gest_capas[gest_capas["gestionnaire"].str.lower().str.contains(selection)][:50],
        x="gestionnaire",
        y="capacite_totale",
    )

    capacites = data.dropna(subset=["capacite"]).sort_values("capacite")
    if selection:
        capacites = capacites.dropna(subset=["gestionnaire"])
        capacites = capacites[
            capacites["gestionnaire"].str.lower().str.contains(selection)
        ]
    capacites = capacites[:1000]
    map_capacites = px.scatter_geo(
        capacites["capacite"], lat=capacites.Y, lon=capacites.X, scope="europe"
    )

    return container, bar_top_gestionnaires, map_capacites


@app.callback(
    [
        dash.Output("weight-couverture", "children"),
        dash.Output("weight-surveillance", "children"),
        dash.Output("weight-lumiere", "children"),
        dash.Output("confort-gestionnaires", "figure"),
    ],
    [
        dash.Input("slider-couverture", "value"),
        dash.Input("slider-surveillance", "value"),
        dash.Input("slider-lumiere", "value"),
    ],
)
def update_confort(weight_couverture, weight_surveillance, weight_lumiere):
    print(weight_couverture, weight_surveillance, weight_lumiere)
    s = weight_couverture + weight_surveillance + weight_lumiere
    w_couv = weight_couverture / s
    w_surv = weight_surveillance / s
    w_lum = weight_lumiere / s

    surete = data.loc[
        :, ["gestionnaire", "couverture", "surveillance", "lumiere"]
    ].dropna()
    surete["lumiere"] = surete["lumiere"].astype(bool)
    print(surete.dtypes)
    surete = (
        surete.groupby("gestionnaire")[["couverture", "surveillance", "lumiere"]]
        .sum()
        .reset_index()
    )
    surete["total"] = (
        w_couv * surete["couverture"]
        + w_surv * surete["surveillance"]
        + w_lum * surete["lumiere"]
    )
    surete = surete.sort_values("total", ascending=False)[:10]
    print(surete)
    fig = px.bar(surete, x=surete["gestionnaire"], y=surete["total"])

    return (
        "{:.1%}".format(w_couv),
        "{:.1%}".format(w_surv),
        "{:.1%}".format(w_lum),
        fig,
    )


if __name__ == "__main__":
    app.run_server(debug=True)
