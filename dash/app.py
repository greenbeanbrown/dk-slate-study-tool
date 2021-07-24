import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import pandas as pd

import sys
sys.path.insert(0, '..')
from functions import cleanup_mlb_lineup_data, cleanup_mma_lineup_data, prep_raw_dk_contest_data, filter_dk_users

def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

ALLOWED_TYPES = (
    "text", "number"
)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
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
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
    # Adding function to process data
    html.Div(children=[
        html.H4(children='DK Slate Study Lineups')
        #generate_table(df)
])
    #html.Div(
    #    dcc.Input(
    #        id="input_text",
    #        type="text",
    #        placeholder="input text",
    #    )
    #),
    #html.Div(id="out-all-types")
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        #html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data = filter_dk_users(prep_raw_dk_contest_data(df, 'MLB')[1], prep_raw_dk_contest_data(df, 'MLB')[0]).to_dict('records'),
            #data=df.to_dict('records'),
            #columns=[{'name': i, 'id': i} for i in df.columns]
            columns=[{'name': i, 'id': i} for i in filter_dk_users(prep_raw_dk_contest_data(df, 'MLB')[1], prep_raw_dk_contest_data(df, 'MLB')[0]).columns],

            sort_action="native"
            #sort_mode="multi"
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])


@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children
    else:
        pass

#@app.callback(
#    Output("out-all-types", "children"),
#    #[Input("input_{}".format(_), "value") for _ in ALLOWED_TYPES],
#     Input('input_text', "value"),
#    )
#def cb_render(*vals):
#    return(str(val) for val in vals if val)

          
    #return " | ".join((str(val) for val in vals if val))



if __name__ == '__main__':
    app.run_server(debug=True)