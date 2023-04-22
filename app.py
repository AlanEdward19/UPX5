import base64, pandas as pd, dash
from io import StringIO
from dash import Dash, dcc, html, dash_table
import plotly.express as px

from Scripts.MachineLearning import AcharAnomalias

# Criar o aplicativo Dash
app = Dash(__name__)

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Análise de dados"),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Arraste e solte ou ',
            html.A('selecione um arquivo')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Permitir upload de apenas um arquivo
        multiple=False
    ),
    html.Button('Processar Arquivo', id='process-data-button', n_clicks=0),
    # Tabela para exibir os dados inválidos
    dash_table.DataTable(
        id='invalid-data-table',
        columns=[{"name": i, "id": i} for i in ['Eletrodomestico', 'Comodo', 'Gasto', 'Data', 'MediaGasto', 'DesvioPadrao']],
        data=[],
        style_table={
            'maxHeight': '400px',
            'overflowY': 'scroll'
        }
    ),
    # Gráfico para exibir os dados processados
    dcc.Graph(id='processed-data-graph'),

    # Checkbox para filtrar os dados exibidos no gráfico
    dcc.Checklist(
        id='filter-data-checklist',
        options=[
            {'label': 'Mostrar apenas dados processados', 'value': 'processed'}
        ],
        value=[]
    )
])

# Variável para armazenar os dados processados
processed_data = None
dataframe = None

# Callback para processar o arquivo e exibir os dados inválidos na tabela
@app.callback(
    dash.dependencies.Output('invalid-data-table', 'data'),
    dash.dependencies.Input('process-data-button', 'n_clicks'),
    dash.dependencies.State('upload-data', 'contents')
)

def process_file(n_clicks, contents):
    global processed_data, dataframe
    
    if n_clicks > 0 and contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            dataframe = pd.read_csv(StringIO(decoded.decode('utf-8')), delimiter=";")
            processed_data = AcharAnomalias(dataframe)
            invalid_data = processed_data.to_dict('records')
            return invalid_data
        
        except Exception as e:
            print(e)
            return []
    else:
        return []


# Callback para exibir o gráfico com base nos dados processados
@app.callback(
    dash.dependencies.Output('processed-data-graph', 'figure'),
    dash.dependencies.Input('process-data-button', 'n_clicks'),
    dash.dependencies.State('upload-data', 'contents'),
    dash.dependencies.State('filter-data-checklist', 'value')
)

def display_graph(n_clicks, contents, filter_value):
    global processed_data, dataframe

    if n_clicks > 0 and contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            dataframe = pd.read_csv(StringIO(decoded.decode('utf-8')), delimiter=";")
            processed_data = AcharAnomalias(dataframe)

            # Obter os dados que não estão em processed_data e plotar em verde
            df_not_processed = dataframe[~dataframe.set_index(['Comodo', 'Data', 'Eletrodomestico']).index.isin(processed_data.set_index(['Comodo', 'Data', 'Eletrodomestico']).index)]
            fig = px.line(df_not_processed, x='Data', y='Gasto', color='Comodo', line_group='Eletrodomestico', labels={'Gasto': 'Gasto original'})

            # Obter os dados que estão em processed_data e plotar em vermelho, separados por comodo
            for comodo in processed_data['Comodo'].unique():
                df_comodo = processed_data[processed_data['Comodo'] == comodo]
                fig.add_trace(px.line(df_comodo, x='Data', y='Gasto', color=px.Constant(comodo), line_group='Eletrodomestico',
                                       labels={'Gasto': 'Gasto processado'})['data'][0])

            fig.update_layout(title='Gastos por Comodo', xaxis_title='Data', yaxis_title='Gasto')
            return fig
        except Exception as e:
            print(e)
            return {}
    else:
        return {}


if __name__ == '__main__':
    app.run_server(debug=True)