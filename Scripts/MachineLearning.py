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
    df_merged = pd.DataFrame()

    for i in range(0, len(df), group_size):
        df_group = df.iloc[i:i+group_size,:]

        for col in df_group.columns:
            if col == 'datetime':
                col_value = df_group[col].iloc[0]
                col_value = col_value.replace(minute=0, second=0)
            else:
                col_value = df_group[col].iloc[0]
                for j in range(1, len(df_group)):
                    if df_group[col].iloc[j] > col_value:
                        col_value += df_group[col].iloc[j] - col_value
                    elif df_group[col].iloc[j] < col_value:
                        col_value -= col_value - df_group[col].iloc[j]

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
    nova_data_hora = valor - timedelta(hours=1)
    return nova_data_hora.strftime('%Y-%m-%d %H:%M:%S')

def subtrair_uma_semana(valor):
    nova_data_hora = valor - timedelta(weeks=1)
    return nova_data_hora.strftime('%Y-%m-%d %H:%M:%S')

def somar_uma_semana(valor):
    nova_data_hora = valor + timedelta(weeks=1)
    return nova_data_hora.strftime('%Y-%m-%d %H:%M:%S')

def formatar_dataframeSemMerge(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe['time'] = pd.to_numeric(dataframe['time'], errors='coerce')
    dataframe = dataframe[~dataframe['time'].isna()]

    dataframe = corrigir_diferenca_tempo(dataframe)

    dataframe = dataframe.drop(columns=['time', 'summary', 'icon', 'cloudCover'])

    dataframe = dataframe.sort_index(axis=1)

    return dataframe

def formatar_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe['time'] = pd.to_numeric(dataframe['time'], errors='coerce')
    dataframe = dataframe[~dataframe['time'].isna()]

    dataframe = corrigir_diferenca_tempo(dataframe)

    dataframe = dataframe.drop(columns=['time', 'summary', 'icon', 'cloudCover'])

    dataframe = dataframe.sort_index(axis=1)

    return merge_dataframe(dataframe)

def tratar_dataframe(dataframe):
    dataframe = formatar_dataframe(dataframe)
    return dataframe

def achar_anomalias(dataframe):
    df = tratar_dataframe(dataframe)

    exclude_columns = ['apparentTemperature','datetime','dewPoint','humidity','precipIntensity','precipProbability','pressure','temperature','visibility','windBearing','windSpeed']

    X = df[[column for column in list(df.columns) if column not in exclude_columns]]

    isolation_forest = IsolationForest(n_estimators=100, contamination='auto')

    isolation_forest.fit(X)

    y_pred = isolation_forest.predict(X)

    df['anomaly'] = y_pred

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
                    start_date = x[a]

                end_date = x[b]

                ax.set_xlabel('data')
                ax.set_ylabel('KW')

        ax.set_title('Intervalo de tempo de anomalia registrados de ' + str(start_date) + ' até ' + str(end_date))
        ax.legend(df_temp2.columns.tolist())
        plots.append(fig)

    return plots

