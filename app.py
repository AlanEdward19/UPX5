import base64
import pandas as pd
import dash
from dash import html
import dash_table
from dash import dcc
import plotly.graph_objects as go
from matplotlib import pyplot as plt

from io import StringIO
from Scripts.MachineLearning import criar_grafico_e_tabela

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
                columns=[{"name": i, "id": i} for i in ['Barn [kW]','Dishwasher [kW]','Fridge [kW]','Furnace 1 [kW]','Furnace 2 [kW]','Garage door [kW]','Home office [kW]','House overall [kW]','Kitchen 12 [kW]','Kitchen 14 [kW]','Kitchen 38 [kW]','Living room [kW]','Microwave [kW]','Solar [kW]','Well [kW]','Wine cellar [kW]','apparentTemperature','datetime','dewPoint','gen [kW]','use [kW]']],
                data=[],
            )
        ])
    ]),

    html.Div(id='processed-data-graph', style=styles['graph']),
])

# Função para processar o arquivo, exibir os dados inválidos na tabela e exibir os gráficos
def process_and_display_data(n_clicks, contents):
    if n_clicks > 0 and contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            dados = criar_grafico_e_tabela(StringIO(decoded.decode('utf-8')))

            dataframe = dados['anomalias'].to_dict('records')
            graficos = dados['graficos']

            feedback = html.Div('Arquivo processado com sucesso!', style={'color': 'green'})

            # Exibir os gráficos com base nos dados processados
            graphs = []
            for i, grafico in enumerate(graficos):
                if isinstance(grafico['fig'], plt.Figure):
                    fig = go.Figure()
                    for ax in grafico['fig'].get_axes():
                        for line, legend in zip(ax.get_lines(), grafico['legend']):
                            fig.add_trace(go.Scatter(x=line.get_xdata(), y=line.get_ydata(), name=legend))
                    fig.update_layout(
                        title=grafico['title'],
                        xaxis_title='Data',
                        yaxis_title='Gasto',
                    )
                    graphs.append(dcc.Graph(id=f'processed-data-graph-{i}', figure=fig, style=styles['graph']))

            return dataframe, feedback, graphs

        except Exception as e:
            feedback = html.Div(f'Ocorreu um erro ao processar o arquivo: {str(e)}', style={'color': 'red'})
            return [], feedback, None
    else:
        return [], None, None

# Callback para processar o arquivo, exibir os dados inválidos na tabela e exibir os gráficos
@app.callback(
    [dash.dependencies.Output('invalid-data-table', 'data'),
     dash.dependencies.Output('upload-feedback', 'children'),
     dash.dependencies.Output('processed-data-graph', 'children')],
    [dash.dependencies.Input('process-data-button', 'n_clicks')],
    [dash.dependencies.State('upload-data', 'contents')]
)
def process_and_display_callback(n_clicks, contents):
    dataframe, feedback, graphs = process_and_display_data(n_clicks, contents)
    return dataframe, feedback, graphs

if __name__ == '__main__':
    app.run_server(debug=True)
