import math
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# --------------------------
# stałe
g = 9.81  # stała grawitacyjna
cisnieniePoczatkowe = 101300.0
masaMolowaPowietrza = 0.029  # masa molowa powietrza (kg/mol)
r = 287.05  # indywidualna stała gazowa dla powietrza
R = 8.31  # stała gazowa
mol = 0.024  # objętość jednego mola powietrza (m^3)
temperaturaPoczatkowa = 15 + 273.0
utrataCieplaNaMetr = 0.2
temperaturaMax = 420

# --------------------------
# stałe zmienne
masaCalkowita = 900.0
objetoscMax = 3100.0  # objętość maksymalna balonu (m^3)
objetoscMin = 2900.0  # objętość minimalna balonu (m^3)


def tworzenieGrafu(time, height):
    wysokoscDocelowa = height
    wysokosc = [0.0, ]
    przyspieszenie = [0.0, ]
    objetoscLista = [objetoscMin, ]
    temperaturaZewnetrzna = [temperaturaPoczatkowa, ]
    temperaturaWewnetrzna = [temperaturaPoczatkowa, ]
    gestoscPowietrzaAktualna = [(cisnieniePoczatkowe * math.exp(
        (-1 * masaMolowaPowietrza * g * wysokosc[0]) / (R * (293 - 0.006 * wysokosc[0])))) / (r * (
                293 - 0.006 * wysokosc[0])), ]
    cisnienieZewnetrzne = [cisnieniePoczatkowe * math.exp((-1 * masaMolowaPowietrza * g * wysokosc[0]) / (R * (
                293 - 0.006 * wysokosc[0]))), ]
    nw = [objetoscLista[0] / mol, ]

    czas = [0.0, ]
    okresProbkowania = 0.1
    iloscProbkowan = int(time / okresProbkowania) + 1

    # regulator
    stalaCalkowania = 0.03
    wzmocnienie = 1125.0
    uchybRegulacji = [height - wysokosc[0], ]
    upi = [stalaCalkowania * (uchybRegulacji[0] + (okresProbkowania / wzmocnienie) * sum(
        uchybRegulacji)), ]

    for i in range(1, iloscProbkowan):
        czas.append(i * okresProbkowania)
        gestoscPowietrzaAktualna.append((cisnieniePoczatkowe * math.exp(
            (-1 * masaMolowaPowietrza * g * wysokosc[-1]) / (R * (temperaturaPoczatkowa - 0.006 * wysokosc[-1])))) / (
                                                    r * (temperaturaPoczatkowa - 0.006 * wysokosc[-1])))
        cisnienieZewnetrzne.append(cisnieniePoczatkowe * math.exp(
            (-1 * masaMolowaPowietrza * g * wysokosc[-1]) / (R * (temperaturaPoczatkowa - 0.006 * wysokosc[-1]))))
        nw.append(objetoscLista[-1] / mol)
        cisnienieWewnetrzne = cisnienieZewnetrzne[i]
        temperaturaZewnetrzna.append(temperaturaPoczatkowa - 0.006 * wysokosc[-1])
        uchybRegulacji.append(uchybRegulacji[-1] + wysokoscDocelowa - wysokosc[-1])
        upi.append(stalaCalkowania * (uchybRegulacji[-1] - uchybRegulacji[-2] + (okresProbkowania / wzmocnienie) * uchybRegulacji[-1]))
        temperaturaWewnetrzna.append(min(temperaturaMax, max(temperaturaPoczatkowa + upi[i] - utrataCieplaNaMetr, temperaturaWewnetrzna[-1] - utrataCieplaNaMetr)))
        objetoscAktualna = nw[i] * R * temperaturaWewnetrzna[i] / cisnienieWewnetrzne
        if objetoscAktualna < objetoscMax:
            objetoscLista.append(objetoscAktualna)
        else:
            objetoscLista.append((objetoscMax))
        przyspieszenie.append((g * ((objetoscLista[i] * gestoscPowietrzaAktualna[i] * (
                    1 - temperaturaZewnetrzna[i] / temperaturaWewnetrzna[i])) / masaCalkowita - 1)))
        wysokoscAktualna = wysokosc[-1] + przyspieszenie[i] * okresProbkowania + przyspieszenie[i] * okresProbkowania * okresProbkowania / 2
        if wysokoscAktualna > 0:
            wysokosc.append(wysokoscAktualna)
        else:
            wysokosc.append(0)
    godziny = []
    for godzina in czas:
        tmp = godzina / 3600
        godziny.append(tmp)
    return {"Czas": godziny, "Wysokosc": wysokosc, "TemperaturaWewnetrzna": temperaturaWewnetrzna}

df = tworzenieGrafu(8000, 2500)

website = Dash(__name__)
website.layout = html.Div(children=[

    html.H1("Projekt symulacji lotu balonem", id='page-title'),
    html.Div(id='input-div', children=[
        html.H4("Zadana wysokość [m]"),
        dcc.Input(id='input-Wysokość', value=2500, type="number"),
        html.H4("Czas symulacji [s]"),
        dcc.Input(id='input-Czas', value=8000, type="number")
    ]),
    #html.Button("Symuluj", id="sym-btn", style={"cursor": "pointer", "color": "white", "padding": "10px", "background-color":"gray", "margin-top":"20px", "border-radius":"10px", "border":"solid 1px gray"}),
    dcc.Graph(id='main-graph', figure={'data': [{
        'x': df["Czas"],
        'y': df["Wysokosc"]
    }]}),
    dcc.Graph(id='temperature-graph', figure={'data': [{
        'x': df["Czas"],
        'y': df["TemperaturaWewnetrzna"]
    }]}),
], style={"display": "flex", "flex-direction": "column", "align-items": "center", "width": "100vw"})


@website.callback(
    Output(component_id = 'main-graph', component_property = 'figure'),
    Input(component_id = 'input-Czas', component_property = 'value'),
    Input(component_id = 'input-Wysokość', component_property = 'value')
)
def aktualnizowanieWykresuWysokosci(time, height):
    df = tworzenieGrafu(time, height)
    graph = px.line(df, x = "Czas", y = "Wysokosc")
    graph.update_layout(transition_duration=500)
    return graph

@website.callback(
    Output(component_id='temperature-graph', component_property='figure'),
    Input(component_id = 'input-Czas', component_property = 'value'),
    Input(component_id = 'input-Wysokość', component_property = 'value')
)
def aktualizowanieWykresuTemperatury(time, height):
    df = tworzenieGrafu(time, height)
    graph = px.line(df, x = "Czas", y = "TemperaturaWewnetrzna")
    graph.update_layout(transition_duration=500)
    return graph

website.run(debug=True)
