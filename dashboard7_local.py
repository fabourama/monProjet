import os
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import requests

import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import pickle
import shap
from io import StringIO
import dash_bootstrap_components as dbc


# URL de l'API
API_URL = 'http://127.0.0.1:8000/' #'http://127.0.0.1:8000/'  # "http://3.84.177.36:8000/"  # Remplacez par votre URL d'API

# ------------------------------------------------------------------------------------------------------------
# Chargement du modèle et des données
# ------------------------------------------------------------------------------------------------------------

def charger_modele_de_github(nom_utilisateur, nom_repo, chemin_fichier_modele):
    url = f"https://raw.githubusercontent.com/{nom_utilisateur}/{nom_repo}/master/{chemin_fichier_modele}"
    response = requests.get(url)

    if response.status_code == 200:
        contenu_modele = response.content
        modele_charge = pickle.loads(contenu_modele)
        # print("Modèle chargé avec succès...")
        return modele_charge
    else:
        print(f"Erreur lors de la récupération du modèle depuis GitHub. Code d'erreur : {response.status_code}")
        print(f"Message d'erreur complet : {response.text}")
        return None

nom_utilisateur = "bouramayaya"
nom_repo = "OC-Projet-7"
chemin_fichier_modele = "model/best_LGBMClassifier.pkl"

model = charger_modele_de_github(nom_utilisateur, nom_repo, chemin_fichier_modele)

# ------------------------------------------------------------------------------------------------------------
# Chargement des données
# ------------------------------------------------------------------------------------------------------------
def charger_et_concatener_fichiers_github(nom_utilisateur, nom_repo, chemin_dossier, mot_cle, nrows=None):
    url = f"https://api.github.com/repos/{nom_utilisateur}/{nom_repo}/contents/{chemin_dossier}"
    response = requests.get(url)
    fichiers_csv = []

    if response.status_code == 200:
        fichiers = response.json()
        for fichier in fichiers:
            if fichier["name"].lower().endswith('.csv') and mot_cle in fichier["name"]:
                contenu = requests.get(fichier["download_url"]).text
                dataframe = pd.read_csv(StringIO(contenu), nrows=nrows)
                fichiers_csv.append(dataframe)

        if not fichiers_csv:
            print(f"Aucun fichier contenant le mot-clé '{mot_cle}' n'a été trouvé dans le dossier GitHub.")
            return None

        dataframe_concatene = pd.concat(fichiers_csv, axis=0, ignore_index=True)
        return dataframe_concatene.set_index('SK_ID_CURR')
    else:
        print(f"Erreur lors de la récupération des fichiers : {response.status_code}")
        return None


nom_utilisateur = "bouramayaya"
nom_repo = "OC-Projet-7"
chemin_dossier = "data"

taille = None # 8000
data_test = charger_et_concatener_fichiers_github(nom_utilisateur, nom_repo, chemin_dossier, 'test_df', nrows=taille)
data_train = charger_et_concatener_fichiers_github(nom_utilisateur, nom_repo, chemin_dossier, 'train_df_', nrows=taille)
X_train = charger_et_concatener_fichiers_github(nom_utilisateur, nom_repo, chemin_dossier, 'X_train_1', nrows=taille)

print('data_test   :', data_test.shape)
# print('data_train  :', data_train.shape)
# print('X_train     :', X_train.shape)

cols = X_train.select_dtypes(['float64']).columns
scaler = StandardScaler()
scaler.fit(X_train[cols])

listvar = X_train.columns.tolist()

# Sélection des colonnes numériques pour la mise à l'échelle
data_test_scaled = data_test[listvar].copy()
data_test_scaled[cols] = scaler.transform(data_test_scaled[cols])

data_train_scaled = data_train[listvar].copy()
data_train_scaled[cols] = scaler.transform(data_train[cols])

# Initialisation de l'explainer Shapley pour les valeurs locales
explainer = shap.Explainer(model)

import dash_bootstrap_components as dbc

# Initialisation de l'application Dash
# app = Dash(__name__, suppress_callback_exceptions=True)
bootstrap_theme = [dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.9.0/css/all.css']
app = Dash(__name__, external_stylesheets=bootstrap_theme, title="Dashboard Prêt à depenser")
server = app.server
app.config.suppress_callback_exceptions = True


#  Quelques fonctions utiles pour le dashboard.
# Fonction pour obtenir la prédiction
def get_prediction(client_id):
    url_get_pred = API_URL + "prediction/" + str(client_id)
    response = requests.get(url_get_pred)
    proba_default = round(float(response.content), 3)
    best_threshold = 0.5
    decision = "Refusé" if proba_default >= best_threshold else "Accordé"
    return proba_default, decision

# Fonction pour afficher la jauge de score
def plot_score_gauge(proba):
    fig = go.Figure(go.Indicator(
        domain={'x': [0, 1], 'y': [0, 1]},
        value=proba * 100,
        mode="gauge+number+delta",
        title={'text': "Jauge de score"},
        delta={'reference': 50},
        gauge={'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "black"},
               'bar': {'color': "MidnightBlue"},
               'steps': [
                   {'range': [0, 20], 'color': "Green"},
                   {'range': [20, 45], 'color': "LimeGreen"},
                   {'range': [45, 50], 'color': "Orange"},
                   {'range': [50, 100], 'color': "Red"}],
               'threshold': {'line': {'color': "brown", 'width': 4}, 'thickness': 1,
                             'value': 50}}))
    return fig


# Mise en page de l'application Dash
app.layout = html.Div([
    # Titre de la page
    html.H1("Dashboard Prêt à dépenser"),

    # Menu déroulant pour sélectionner l'ID du client
    dcc.Dropdown(
        id          = 'client-dropdown',
        options     = [{'label': str(id_client_dash), 'value': id_client_dash} for id_client_dash in data_test.index],
        value       = data_test.index[0], # None,  # Valeur par défaut, vous pouvez la changer si nécessaire
        placeholder = 'Sélectionnez un client'
    ),

    # Contenu dynamique basé sur les onglets
    dcc.Tabs(id='tabs', value='home', children=[
        dcc.Tab(label='Home', value='home'),
        dcc.Tab(label='Information du client', value='client_info'),
        dcc.Tab(label='Interprétation locale', value='local_interpretation'),
        dcc.Tab(label='Interprétation globale', value='global_interpretation'),
    ]),
    # Contenu spécifique aux onglets
    html.Div(id='tab-content')
],
    style={"padding": "10px"}
)
# Fonction de mise à jour du contenu des onglets
@app.callback(Output('tab-content', 'children'),
              [Input('tabs', 'value')])

def update_tab(tab_name):
    if tab_name == 'home':
        return html.Div([
            html.H2("Bienvenue sur le tableau de bord Prêt à dépenser"),
            html.Div([
                dcc.Markdown("Ce site contient un dashboard interactif permettant d'expliquer aux clients les "
                             "d'approbation ou refus de leur demande de crédit.\n"
                             "\nLes prédictions sont calculées à partir d'un algorithme d'apprentissage automatique "
                             "préalablement entraîné. Il s'agit d'un modèle *Light GBM* (Light Gradient Boosti"
                             "Les données utilisées sont disponibles [ici](https://www.kaggle.com/c/home-credi"
                             "Lors du déploiement, un échantillon de ces données a été utilisé.\n"
                             "\nLe dashboard est composé de plusieurs pages :\n"
                             "- **Information du client**: Vous pouvez y retrouver toutes les informations rel"
                             "selectionné dans la colonne de gauche, ainsi que le résultat de sa demande de cr"
                             "Je vous invite à accéder à cette page afin de commencer.\n"
                             "- **Interprétation locale**: Vous pouvez y retrouver quelles caractéristiques du client qui ont "
                             "influencé le choix d'approbation ou refus de la demande de crédit.\n"
                             "- **Intérprétation globale**: Vous pouvez y retrouver notamment des comparaisons"
                             "les autres clients de la base de données ainsi qu'avec des clients similaires.")
            ])
        ])
    elif tab_name == 'client_info':
        return [
            html.H2("Information du client"),
            html.Div([
                html.Button("Statut de la demande", id='start-button'),
                html.Div(id='prediction-output')
            ]),
            html.Div(id='client-info-expander-output')
        ]        

    elif tab_name == 'local_interpretation':
        return [
            html.Div("Explore l'influence de chaque caractéristique (variables) sur la probabilité d'octroi ou de refus du crédit", 
                     style={"text-align": "center"}),
            # html.Div(id='shap-graph'),
            dcc.Graph(id='shap-waterfall-plot'), 
        ]
    
    elif tab_name == 'global_interpretation':
        return [
            # html.H2("Interprétation globale", style={"text-align": "center"}),
            html.H2("Analyse features importances", style={"text-align": "center"}),
            dcc.Graph(id='feature-importance-plot'),

            html.H2("Analyse sur les clients similaires (Voisins)", style={"text-align": "center"}), 
            html.Div([
                html.Label("Choix de  l'abscisse X"),
                dcc.Dropdown(
                    id='feature1-dropdown',
                    options=[{'label': col, 'value': col} for col in data_test.columns],
                    value=data_test.columns[0],  # Valeur par défaut, colonne 0
                    placeholder='Sélectionnez Feature 1'
                ),
            ], style={'width': '48%', 'display': 'inline-block', 'margin-right': '2%'}), 

            html.Div([                
                html.Label("Choix de l'ordonnée Y"),
                dcc.Dropdown(
                    id='feature2-dropdown',
                    options=[{'label': col, 'value': col} for col in data_test.columns],
                    value=data_test.columns[4],  # Valeur par défaut, colonne 4
                    placeholder="Selectionnez l'ordonnée (Y)"
                ),
            ], style={'width': '48%', 'display': 'inline-block'}),            
            # Conteneur pour le graphique Scatter Plot
            dcc.Graph(id='scatter-plot'),
        ]

# Callback pour mettre à jour les informations du client
@app.callback(
    Output('client-info-expander-output', 'children'),
    [Input('start-button', 'n_clicks')],
    [State('client-dropdown', 'value')]
)
def update_client_info_expander(n_clicks, client_id):
    if n_clicks is None or not client_id:
        return ''
    else:
        client_info = pd.DataFrame(data_test.loc[data_test.index == client_id])
        return html.Div([
            html.Br(),
            html.Div("Voici les informations du client:"),
            html.Br(),
            dcc.Markdown(client_info.to_markdown())
        ])


# Callback pour mettre à jour la sortie de la prédiction
@app.callback(Output('prediction-output', 'children'),
              [Input('start-button', 'n_clicks')],
              [State('client-dropdown', 'value')])
def update_prediction_output(n_clicks, client_id):
    if n_clicks is None:
        return ''
    else:
        if client_id and client_id != '<Select>':
            probability, decision = get_prediction(client_id)
            if decision == 'Accordé':
                return html.Div([
                    html.H2("RÉSULTAT DE LA DEMANDE"),
                    html.Div("Crédit accordé", style={'color': 'green'}),
                    dcc.Graph(figure=plot_score_gauge(probability))
                ])
            else:
                return html.Div([
                    html.H2("RÉSULTAT DE LA DEMANDE"),
                    html.Div("Crédit refusé", style={'color': 'red'}),
                    dcc.Graph(figure=plot_score_gauge(probability))
                ])
        else:
            return ''


# Callback pour mettre à jour le graphique SHAP
@app.callback(
    Output('shap-graph', 'figure'),
    [Input('client-dropdown', 'value')]
)
def update_shap_graph(client_id):
    shap.initjs()
    if client_id is None:
        raise PreventUpdate  # If no client is selected, prevent the graph update

    client_index = data_test.index.get_loc(client_id)
    client_data = data_test_scaled[data_test_scaled.index == client_id]
    feature_names = data_test.columns.tolist()

    shap_values_client = explainer.shap_values(client_data)[0][0]
    
    # Appel à l'API pour récupérer les shap_values
    shap_api_url = f"{API_URL}shaplocal/{client_id}"
    response = requests.get(shap_api_url)

    if response.status_code == 200:
        shap_data          = response.json()
        # shap_values_client = shap_data['shap_values'][0]

        print('shap_values_client :', len(shap_data['shap_values'][0]))
        print('shap_data          :', len(shap_data['data'][0]))
        print('shap_values_client :', print(shap_values_client))

        # Create a Plotly figure using the extracted information
        shap_graph = shap.force_plot(
            explainer.expected_value[0],
            shap_values_client,
            data_test.iloc[client_index, :],
            feature_names=feature_names,
            matplotlib=True  # Set matplotlib to False to ensure it returns a Plotly figure
        )
         # Convert the AdditiveForceVisualizer object to a Plotly figure
        # shap_fig = shap_graph.data[0].to_plotly()

        # Return the Plotly figure dcc.Graph(figure=shap_graph)
        return shap_graph
    else:
        raise PreventUpdate

# Callback to update the feature importance plot
@app.callback(
    Output('feature-importance-plot', 'figure'),
    [Input('client-dropdown', 'value')]
)
def update_feature_importance_plot(client_id):
    if client_id is None:
        raise PreventUpdate  # If no client is selected, prevent the graph update

    # Calculate feature importance
    feature_imp = pd.DataFrame(
        sorted(zip(model.booster_.feature_importance(importance_type='gain'), X_train.columns)),
        columns=['Value', 'Feature']
    )

    # Create a bar plot
    feature_importance_plot = px.bar(
        feature_imp.sort_values(by="Value", ascending=True).tail(10),
        x="Value",
        y="Feature",
        orientation='h',
        title='Features Importances (10 prémières variables)',
    )
        # Update layout to center title and set font style
    feature_importance_plot.update_layout(
        title=dict(
            # text='Features Importances (10 premières variables)',
            x=0.5,  # Center the title
            font=dict(size=16,  # Set font size
                      family='Arial',  # Set font family
                      color='black'),  # Set font color : '#1f77b4'
            ),
    )
    return feature_importance_plot

# Callback pour mettre à jour le graphique Shap waterfall_plot
@app.callback(
    Output('shap-waterfall-plot', 'figure'),
    [Input('client-dropdown', 'value')]
)
def update_shap_waterfall_plot(client_id):
    shap.initjs()
    if client_id is None:
        raise PreventUpdate  # Si aucun client n'est sélectionné, empêchez la mise à jour du graphique

    # Appel à l'API pour récupérer les shap_values
    shap_api_url = f"{API_URL}shaplocal/{client_id}"
    response = requests.get(shap_api_url)

    if response.status_code == 200:
        shap_data = response.json()

        # Obtenez les valeurs Shap
        shap_values_client = shap_data['shap_values'][0]
        feature_names      = shap_data['feature_names'][:10]  # Utilisez uniquement les 10 premières variables
        expected_value     = explainer.expected_value[0]

        # Calculez les contributions cumulatives
        cumulative_shap_values = np.cumsum(shap_values_client[:10])  # Utilisez uniquement les 10 premières valeurs

        # Créez un graphique waterfall_plot avec Plotly
        shap_waterfall_plot = go.Figure()

        shap_waterfall_plot.add_trace(go.Waterfall(
            orientation="v",
            measure=["absolute"] + ["relative"] * (len(feature_names) - 1),
            x=feature_names,
            y=cumulative_shap_values,
            connector={"line":{"color":"rgb(63, 63, 63)"}},
            textposition="outside",
            decreasing={"marker":{"color":"Maroon", "line":{"color":"red", "width":2}}},
            increasing={"marker":{"color":"Teal"}},
            totals={"marker":{"color":"deep sky blue", "line":{"color": "blue", "width": 3}}}
        ))

        shap_waterfall_plot.update_layout(
            title="Shap Waterfall Plot",
            showlegend=False
        )

        return shap_waterfall_plot
    else:
        raise PreventUpdate

# Callback pour mettre à jour le graphique Scatter Plot
@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('client-dropdown', 'value'),
     Input('feature1-dropdown', 'value'),
     Input('feature2-dropdown', 'value')]
)
def update_scatter_plot(client_id, feature1, feature2):
    if client_id is None:
        raise PreventUpdate  # Si aucun client n'est sélectionné, empêchez la mise à jour du graphique

    # Appel à l'API pour récupérer les 10 voisins
    neighbors_api_url = f"{API_URL}clients_similaires/{client_id}"
    response = requests.get(neighbors_api_url)

    if response.status_code == 200:
        neighbors_data = response.json()

        # Obtenez les données du client
        client_data = data_test[data_test.index == client_id]

        # Obtenez les données des voisins
        voisins_data = data_train[data_train.index.isin(neighbors_data)]

        # Création d'un graphique scatter plot avec Plotly Express
        scatter_plot = px.scatter(
            x = voisins_data[feature1],
            y = voisins_data[feature2],
            color =data_train.loc[neighbors_data, 'TARGET'],  # Utilisez la variable 'TARGET' pour définir la couleur
            color_discrete_sequence=['green', 'red'],  # Couleurs pour '0' et '1' dans 'TARGET'
            labels ={'x': f'{feature1}', 'y': f'{feature2}', 'color': 'TARGET'},
            title  = f'Scatter Plot des 10 Voisins du client {client_id}',
        )

        # Ajoutez le point du client choisi en rouge
        scatter_plot.add_scatter(
            x=client_data[feature1],
            y=client_data[feature2],
            mode='markers',
            marker=dict(color='red'),
            name='Client Choisi'
        )
        # Mettez à jour la mise en page pour déplacer la légende en haut à droite
        scatter_plot.update_layout(
            showlegend=True,
            legend = dict(
                x  = 1,  # position en x
                y  = 1.07,  # position en y
                traceorder = 'normal',  # ordre des éléments de légende
            )
        )
        return scatter_plot
    else:
        raise PreventUpdate


# if __name__ == '__main__':
#     app.run_server(debug=True, 
#                    host = '127.0.0.1', 
#                    port = 8050,
#                    )

# Point d'entrée de l'application Dash
if __name__ == '__main__':
    app.run(debug=True, port=8080)


