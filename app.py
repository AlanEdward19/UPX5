import base64
import pandas as pd
import dash
from dash import html
import dash_table
from dash import dcc
import plotly.express as px

from io import StringIO
from Scripts.MachineLearning import AcharAnomalias

# Criar o aplicativo Dash
app = dash.Dash(__name__)

# Estilos CSS personalizados
styles = {
    'upload': {
        'width': '99%',
        'height': '60px',
        'lineHeight': '60px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin': '10px',
        'background-color': '#f0f0f0',
        'color': '#555',
        'cursor': 'pointer',
    },
    'button': {
        'margin': '20px auto',
        'display': 'block',
        'font-size': '15px',
        'background-color': '#007bff',
        'color': '#fff',
        'border': 'none',
        'border-radius': '5px',
        'padding': '10px 20px',
        'cursor': 'pointer',
    },
    'table-container': {
        'maxHeight': '400px',
        'overflowY': 'scroll',
        'border': '1px solid #ccc',
        'border-radius': '5px',
    },
    'graph': {
        'margin': '20px 0',
    },
}

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Análise de dados", style={'text-align': 'center', 'margin-top': '30px'}),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Arraste e solte ou ',
            html.A('selecione um arquivo')
        ]),
        style=styles['upload'],
        multiple=False
    ),

    html.Button('Processar Arquivo', id='process-data-button', n_clicks=0, style=styles['button']),

    html.Div(id='upload-feedback'),

    html.Div([
        html.Div(id='table-container', style=styles['table-container'], children=[
            dash_table.DataTable(
                id='invalid-data-table',
                columns=[{"name": i, "id": i} for i in ['Eletrodomestico', 'Comodo', 'Gasto', 'Data', 'MediaGasto', 'DesvioPadrao']],
                data=[],
            )
        ])
    ]),

    dcc.Graph(id='processed-data-graph', style=styles['graph']),

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
    [dash.dependencies.Output('invalid-data-table', 'data'),
     dash.dependencies.Output('upload-feedback', 'children')],
    [dash.dependencies.Input('process-data-button', 'n_clicks')],
    [dash.dependencies.State('upload-data', 'contents')]
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
            feedback = html.Div('Arquivo processado com sucesso!', style={'color': 'green'})
            return invalid_data, feedback

        except Exception as e:
            feedback = html.Div(f'Ocorreu um erro ao processar o arquivo: {str(e)}', style={'color': 'red'})
            return [], feedback
    else:
        return [], None


# Callback para exibir o gráfico com base nos dados processados
@app.callback(
    dash.dependencies.Output('processed-data-graph', 'figure'),
    [dash.dependencies.Input('process-data-button', 'n_clicks'),
     dash.dependencies.Input('filter-data-checklist', 'value')],
    [dash.dependencies.State('upload-data', 'contents')]
)
def display_graph(n_clicks, filter_value, contents):
    global processed_data, dataframe

    if n_clicks > 0 and contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            dataframe = pd.read_csv(StringIO(decoded.decode('utf-8')), delimiter=";")
            processed_data = AcharAnomalias(dataframe)

            # Obter os dados que não estão em processed_data e plotar em verde
            df_not_processed = dataframe[~dataframe.set_index(['Comodo', 'Data', 'Eletrodomestico']).index.isin(
                processed_data.set_index(['Comodo', 'Data', 'Eletrodomestico']).index)]
            fig = px.line(df_not_processed, x='Data', y='Gasto', color='Comodo', line_group='Eletrodomestico',
                          labels={'Gasto': 'Gasto original'})

            # Obter os dados que estão em processed_data e plotar em vermelho, separados por comodo
            for comodo in processed_data['Comodo'].unique():
                df_comodo = processed_data[processed_data['Comodo'] == comodo]
                fig.add_trace(px.line(df_comodo, x='Data', y='Gasto', color=px.Constant(comodo),
                                       line_group='Eletrodomestico',
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
