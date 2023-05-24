from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import matplotlib.dates as mdates

import pandas as pd

def corrigir_diferenca_tempo(dataframe):
    dataframe['datetime'] = pd.to_datetime(dataframe['time'], unit='s')

    time_diff = dataframe['datetime'].diff()
    time_diff = time_diff.fillna(pd.Timedelta(seconds=0))
    time_diff = time_diff.apply(lambda x: pd.Timedelta(minutes=1) if x.total_seconds() == 1 else x)

    dataframe['datetime'] = dataframe['datetime'] + time_diff.cumsum()

    dataframe['datetime'] = dataframe['datetime'].apply(lambda dt: dt.replace(second=0))
    
    return dataframe

def timestamp_para_datahora(timestamp):
    datahora = datetime.datetime.fromtimestamp(timestamp)
    return datahora

def merge_dataframe(df, group_size=60):
    # Cria o dataframe auxiliar
    df_merged = pd.DataFrame()

    # Loop pelos grupos de tamanho "group_size"
    for i in range(0, len(df), group_size):
        # Seleciona o grupo atual
        df_group = df.iloc[i:i+group_size,:]

        # Loop pelas colunas do grupo
        for col in df_group.columns:

            # Verifica se a coluna é a datetime
            if col == 'datetime':
                # Armazena o valor da primeira linha da coluna
                col_value = df_group[col].iloc[0]

                # Ajusta apenas a hora mantendo os minutos
                col_value = col_value.replace(minute=0, second=0)

            else:
                # Armazena o valor da primeira linha da coluna
                col_value = df_group[col].iloc[0]

                # Loop pelas linhas da coluna
                for j in range(1, len(df_group)):

                    # Verifica se o valor atual é maior ou menor que o valor armazenado
                    if df_group[col].iloc[j] > col_value:
                        # Soma a diferença na variável armazenada
                        col_value += df_group[col].iloc[j] - col_value
                        
                    elif df_group[col].iloc[j] < col_value:
                        # Soma a diferença na variável armazenada
                        col_value -= col_value - df_group[col].iloc[j]

            # Insere a coluna e valor no dataframe auxiliar
            df_merged.loc[i//group_size, col] = col_value

    return df_merged

def encontrar_valor_em_dataframe(dataframe, valor):
    mask = dataframe['datetime'] == valor
    if mask.any():
        row = mask.idxmax()
        return row
    else:
        return None
    
def subtrair_uma_hora(valor):
    formato = '%Y-%m-%d %H:%M:%S'
    data_hora = datetime.strptime(valor, formato)
    nova_data_hora = data_hora - timedelta(hours=1)
    return nova_data_hora.strftime(formato)

def subtrair_uma_semana(valor):
    formato = '%Y-%m-%d %H:%M:%S'
    data_hora = datetime.strptime(valor, formato)
    nova_data_hora = data_hora - timedelta(weeks=1)
    return nova_data_hora.strftime(formato)

def somar_uma_semana(valor):
    formato = '%Y-%m-%d %H:%M:%S'
    data_hora = datetime.strptime(valor, formato)
    nova_data_hora = data_hora + timedelta(weeks=1)
    return nova_data_hora.strftime(formato)

def formatar_dataframeSemMerge(dataframe: pd.DataFrame) -> pd.DataFrame:
    # Converter a coluna "time" para valores numéricos e filtrar os valores nulos e não numéricos
    dataframe['time'] = pd.to_numeric(dataframe['time'], errors='coerce')
    dataframe = dataframe[~dataframe['time'].isna()]

    # Converter a coluna "time" para timestamp e criar a coluna "datetime"
    dataframe = corrigir_diferenca_tempo(dataframe)

    # Apagar a coluna "time", "summary", "icon", "cloudCover"
    dataframe = dataframe.drop(columns=['time', 'summary', 'icon', 'cloudCover'])

    # Ordena alfabeticamente as colunas
    dataframe = dataframe.sort_index(axis=1)

    return dataframe

def formatar_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    # Converter a coluna "time" para valores numéricos e filtrar os valores nulos e não numéricos
    dataframe['time'] = pd.to_numeric(dataframe['time'], errors='coerce')
    dataframe = dataframe[~dataframe['time'].isna()]

    # Converter a coluna "time" para timestamp e criar a coluna "datetime"
    dataframe = corrigir_diferenca_tempo(dataframe)

    # Apagar a coluna "time", "summary", "icon", "cloudCover"
    dataframe = dataframe.drop(columns=['time', 'summary', 'icon', 'cloudCover'])

    # Ordena alfabeticamente as colunas
    dataframe = dataframe.sort_index(axis=1)

    return merge_dataframe(dataframe)

def tratar_dataframe(dataframe):
    dataframe = formatar_dataframe(dataframe)

    return dataframe

def achar_anomalias(dataframe):
    df = tratar_dataframe(dataframe)

    #Colunas que não envolvem KW
    exclude_columns = ['apparentTemperature','datetime','dewPoint','humidity','precipIntensity','precipProbability','pressure','temperature','visibility','windBearing','windSpeed']

    #Salvar todos os dados do dataframe menos as colunas acima
    X = df[[column for column in list(df.columns) if column not in exclude_columns]]

    #Salvar todos os dados do dataframe menos as colunas acima
    X = df[[column for column in list(df.columns) if column not in exclude_columns]]

    #Definir padrões pro algoritmo
    isolation_forest = IsolationForest(n_estimators=100, contamination='auto')

    #Treinar o algoritmo
    isolation_forest.fit(X)

    #Achar as anomalias
    y_pred = isolation_forest.predict(X)

    #Adicionar nova coluna dizendo se é ou não anomalia
    df['anomaly'] = y_pred

    #Dataframe somente com anomalias
    anomaly = df.loc[df['anomaly'] == -1]

    return anomaly

def criar_grafico_e_tabela(csv):
    dataframe = pd.read_csv(csv, delimiter=',', low_memory=False)
    anomalias = achar_anomalias(dataframe)
    graficos = AllAnomaliesGraph(dataframe, anomalias, 27, 0.5, 10)

    return {
        'anomalias' : anomalias,
        'graficos' : graficos
    }

def AllAnomaliesGraph(dataframe, anomaly, tamX: int, proporcao: int, quantidade: int = 0):
    csv_original = formatar_dataframeSemMerge(dataframe)
    size = len(csv_original.drop(['datetime','apparentTemperature','dewPoint','humidity','precipIntensity','precipProbability','pressure','temperature','visibility','windBearing','windSpeed'], axis=1).columns)
    total_anomalias = len(anomaly.index)

    if quantidade == 0:
        quantidade = total_anomalias

    tamanho_grupo = total_anomalias // quantidade
    grupos = [anomaly.index[i:i+tamanho_grupo] for i in range(0, total_anomalias, tamanho_grupo)]

    plots = []

    for grupo in grupos:
        fig, ax = plt.subplots(figsize=(tamX, size * proporcao))
        start_date = None
        end_date = None

        for i, item in enumerate(grupo):
            a = encontrar_valor_em_dataframe(csv_original, subtrair_uma_hora(anomaly['datetime'][item]))
            b = encontrar_valor_em_dataframe(csv_original, anomaly['datetime'][item])

            if a is not None and b is not None:
                df_temp = csv_original[a:b+1]
                df_temp2 = df_temp.drop(['datetime','apparentTemperature','dewPoint','humidity','precipIntensity','precipProbability','pressure','temperature','visibility','windBearing','windSpeed'], axis=1)
                x = df_temp['datetime']
                t = 0
                for j in df_temp2.columns.tolist():
                    if t < len(df_temp2.columns):
                        y1 = df_temp2[df_temp2.columns[t]]
                        ax.plot(x, y1)
                        t += 1

                if start_date is None:
                    start_date = x[a]  # Armazena o valor de x[a] para o primeiro item do grupo

                end_date = x[b]  # Atualiza o valor de x[b] para cada item do grupo, até o último

                ax.set_xlabel('data')
                ax.set_ylabel('KW')

        ax.set_title('Intervalo de tempo de anomalia registrados de ' + str(start_date) + ' até ' + str(end_date))
        ax.legend(df_temp2.columns.tolist())  # Adiciona a legenda fora do loop interno
        plots.append(fig)

    return plots
