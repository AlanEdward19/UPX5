import base64, pandas as pd, dash
from io import StringIO
from dash import Dash, dcc, html, dash_table

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
        columns=[{"name": i, "id": i} for i in ['coluna1', 'coluna2', 'coluna3']],
        data=[],
        style_table={
            'maxHeight': '400px',
            'overflowY': 'scroll'
        }
    ),
    # Gráfico para exibir os dados processados
    dcc.Graph(id='processed-data-graph')
])

# Callback para processar o arquivo e exibir os dados inválidos na tabela
@app.callback(
    dash.dependencies.Output('invalid-data-table', 'data'),
    dash.dependencies.Input('process-data-button', 'n_clicks'),
    dash.dependencies.State('upload-data', 'contents')
)

def process_file(n_clicks, contents):
    if n_clicks > 0 and contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(StringIO(decoded.decode('utf-8')))
            invalid_data = AcharAnomalias(csvfile=df)
            return invalid_data.to_dict('records')
        except Exception as e:
            print(e)
            return []
    else:
        return []

# Callback para exibir o gráfico com base nos dados processados
@app.callback(
    dash.dependencies.Output('processed-data-graph', 'figure'),
    dash.dependencies.Input('process-data-button', 'n_clicks'),
    dash.dependencies.State('upload-data', 'contents')
)
def display_graph(n_clicks, contents):
    if n_clicks > 0 and contents is not None:
        # Processar o arquivo usando o modelo de aprendizado de máquina
        # Retorna os dados processados para criação do gráfico
        return {'data': [{'x': [1, 2, 3], 'y': [4, 5, 6], 'type': 'bar'}]}
    else:
        return {}

if __name__ == '__main__':
    app.run_server(debug=True)