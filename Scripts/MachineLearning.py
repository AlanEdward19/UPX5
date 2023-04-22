import pandas as pd, numpy as np, re
from joblib import load
import os.path
import os

def AlterarGastos(dataframe):
    dataframe['Gasto'] = dataframe['Gasto'].apply(lambda x: float(re.sub(r'KWh$', '', x).replace(',', '.')) if isinstance(x, str) else x)
    return dataframe

def AcharAnomalias(csvfile):
    
    # Lendo arquivos CSV
    df1 = AlterarGastos(pd.read_csv('Files/PresetArquivoTrain.CSV', delimiter=';'))
    df3 = AlterarGastos(csvfile)

    # Agrupando dados por eletrodoméstico e computando a média de gastos
    df1_grouped = df1.groupby(['Eletrodomestico']).mean()

    #Carregando modelo
    model = load('Model/clusterbrain.joblib')

    # Prevendo os clusters dos valores médios dos gastos
    df1_grouped['cluster'] = model.predict(df1_grouped[['Gasto']])

    # Prevendo o cluster de cada valor de gasto do segundo arquivo
    df3['cluster'] = model.predict(df3[['Gasto']])

    # Computando as médias de gastos por cluster do segundo arquivo
    df3_clustered = df3.groupby(['Eletrodomestico', 'cluster']).mean().reset_index()

    # Merge entre os dados do primeiro arquivo e os dados do segundo arquivo com as médias de gastos por cluster
    df_merged = pd.merge(df1_grouped.reset_index(), df3_clustered, on=['Eletrodomestico', 'cluster'], suffixes=('_train', '_test'))

    # Calculando o desvio em relação à média de gastos por cluster para cada linha do segundo arquivo
    df3['DesvioPadrao'] = np.abs(df3['Gasto'] - df_merged['Gasto_test'])

    # Selecionando as linhas do segundo arquivo que estão fora do padrão
    limite = 0.1  # limite de 10% de desvio em relação à média por cluster
    df_fora_do_padrao = df3[df3['DesvioPadrao'] > limite]

    return df_fora_do_padrao