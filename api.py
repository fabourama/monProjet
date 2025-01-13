from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import pickle
import shap
import uvicorn
import os
import requests
from io import StringIO

# Instanciation de l'API
app = FastAPI()


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

taille = 1000
data        = charger_et_concatener_fichiers_github(nom_utilisateur, nom_repo, chemin_dossier, 'test_df', nrows=taille)
data_train  = charger_et_concatener_fichiers_github(nom_utilisateur, nom_repo, chemin_dossier, 'train_df_1', nrows=taille)
X_train     = charger_et_concatener_fichiers_github(nom_utilisateur, nom_repo, chemin_dossier, 'X_train_1', nrows=taille)

print('data   :', data.shape)



# # Reglage du repertoire de travail
# path='/home/ubuntu/OC/OC-Projet-7'
# os.chdir(path) # 'C:/Users/Fane0763/OpenClassroom/OC Projet 7'
# 
# # Chargement du modèle et des données
# model = pickle.load(open('./model/best_LGBMClassifier.pkl', 'rb'))
# 
# # Chargement des bases
# data_train = pd.read_csv('./data/train_df.csv').set_index('SK_ID_CURR')
# data       = pd.read_csv('./data/test_df.csv').set_index('SK_ID_CURR')
# X_train    = pd.read_csv('./data/X_train.csv').set_index('SK_ID_CURR')

cols = X_train.select_dtypes(['float64']).columns

scaler = StandardScaler()
scaler.fit(X_train[cols])

listvar = X_train.columns.tolist()

# Sélection des colonnes numériques pour la mise à l'échelle
data_scaled = data[listvar].copy()

data_scaled[cols] = scaler.transform(data_scaled[cols])

data_train_scaled = data_train.copy()
data_train_scaled[cols] = scaler.transform(data_train_scaled[cols])

# Initialisation de l'explainer Shapley pour les valeurs locales
explainer = shap.Explainer(model)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.get('/')
def welcome():
    """
    Message de bienvenue.
    """
    return 'Welcome to the API'


@app.get('/{client_id}')
def check_client_id(client_id: int):  # = Path(, title="Client ID", ge=1)
    """
    Vérification de l'existence d'un client dans la base de données.
    """
    if client_id in list(data.index):  # list(data['SK_ID_CURR'])
        return True
    else:
        raise HTTPException(status_code=404, detail="Client not found")


@app.get('/prediction/{client_id}')
async def get_prediction(client_id: int):
    """
    Calcul de la probabilité de défaut pour un client.
    """
    client_data = data_scaled[data_scaled.index == client_id]
    if client_data.empty:
        raise HTTPException(status_code=404, detail="Client data not found")
    info_client = client_data  # client_data.drop('SK_ID_CURR', axis=1)
    prediction = model.predict_proba(info_client)[0][1]
    return prediction


@app.get('/clients_similaires/{client_id}')
async def get_data_voisins(client_id: int):
    """
    Calcul des clients similaires les plus proches.
    """
    features = list(data_train_scaled.columns)
    # features.remove('SK_ID_CURR')
    features.remove('TARGET')
    # print(features)
    nn = NearestNeighbors(n_neighbors=10, metric='euclidean')
    nn.fit(data_train_scaled[features])
    reference_id = client_id
    reference_observation = data_scaled[data_scaled.index == reference_id][features].values
    indices = nn.kneighbors(reference_observation, return_distance=False)
    # print(indices)
    df_voisins = data_train.iloc[indices[0], :].index.tolist()  # data_train.iloc[indices[0], :].index
    return df_voisins


@app.get('/shaplocal/{client_id}')
async def shap_values_local(client_id: int):
    """
    Calcul des valeurs Shapley locales pour un client.
    """
    client_data = data_scaled[data_scaled.index == client_id]
    if client_data.empty:
        raise HTTPException(status_code=404, detail="Client data not found")

    client_data = client_data
    # shap_val = explainer.shap_values(client_data)[1]
    try:
        shap_val = explainer.shap_values(client_data)[1]
        return {
            'shap_values': shap_val.tolist(),
            'base_value': explainer.expected_value,
            'data': client_data.values.tolist(),
            'feature_names': client_data.columns.tolist()
        }
    except Exception as e:
        print(f'Error: {e}')

@app.get('/shap/')
def shap_values():
    """
    Calcul des valeurs Shapley pour l'ensemble du jeu de données.
    """
    try:
        # Calcul des SHAP values
        shap_val = explainer.shap_values(data_scaled)
        #  Convertir en fichier JSON 
        return {
            'shap_values_0': shap_val[0].tolist(),  # .tolist()
            'shap_values_1': shap_val[1].tolist(),  # .tolist()
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001) 
