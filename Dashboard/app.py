from dash import Dash, html, dcc, callback, Output, Input, State
import dash
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import dash_mantine_components as dmc


load_figure_template('cerulean')
px.set_mapbox_access_token('pk.eyJ1IjoibWFsa2VldC1kaGFsbGEiLCJhIjoiY2xnamo3czZ5MTVmNjNpbGJ2ZmpjN29iOSJ9.vxG85YQ3DWte9HqxT5n2mw')
stations_df = pd.read_csv('data/stations.csv')
stations_df = stations_df[['station_id', 'latitude', 'longitude', 'station_name']]
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN, dbc_css])
app.title = 'AQI index'


data = {}

time_of_day = ['All Day', 'Morning', 'Afternoon', 'Evening', 'Night']
level = ['Site', 'State']
freq = ['Daily', 'Monthly', 'Yearly']
pollutants = ['AQI', 'PM2.5', 'PM10', 'NO2', 'NH3', 'SO2', 'CO', 'Ozone']
pollutants_threshold = {
    'PM10': 250,
    'PM2.5': 90,
    'NO2': 180,
    'Ozone': 168,
    'CO': 10,
    'SO2': 380,
    'NH3': 800
}
# colorscale = ['#00B050','#669900' '#E5D8B7', '#FFC000', '#FF0000', '#C00000']
# colorscale = [
#     'rgb(0, 176, 80)', 
#     'rgb(102, 153, 0)', 
#     'rgb(255, 216, 30)',
#     'rgb(255, 192, 0)',
#     'rgb(255, 0, 0)',
#     'rgb(192, 0, 0)'
#     ]

colorscale = [
    'rgb(95, 169, 66)', 
    'rgb(172, 179, 52)', 
    'rgb(250, 183, 51)',
    'rgb(255, 142, 21)',
    'rgb(255, 78, 17)',
    'rgb(242, 0, 0)'
]

colorscale_bar = []
for i, c in enumerate(colorscale):
    colorscale_bar.append([i, c])

# colorscale='bluered'
default_dates = {
    'Daily': '2023-03-31',
    'Monthly': '2023-03',
    'Yearly': 2023,
}

bucket_to_num = {
    'Good': 0,
    'Satisfactory': 1,
    'Moderate': 2,
    'Poor': 3,
    'Very Poor': 4,
    'Severe': 5
}

colormap = {} 
for b, i in bucket_to_num.items():
    colormap[b] = colorscale[i]

for l in level:
    data[l] = {}
    for f in freq:
        print(f'Reading {l}-{f}')
        data[l][f] = pd.read_csv(f'data/{l.lower()}_data_{f.lower()}.csv')
with open('data/india_telengana_new.json') as in_state:
    states_geojson = json.load(in_state)

default_loc_on_level = {
    'Site': 'site_103',
    'State': 'Delhi',
}

@callback(
    Output('top-site', 'figure'),
    Input('dropdown-frequency', 'value'),
    Input('dropdown-level', 'value'),
    Input('dropdown-pollutant', 'value'),
    Input('date-picker', 'value')
)
def update_top_site(freq, level, pollutant, date_picked):
    df = data[level][freq]
    if date_picked is None:
        raise PreventUpdate
    if freq == 'Monthly':
        date_picked = date_picked[:7]
    elif freq == 'Yearly':
        date_picked = date_picked[:4]
        df['Date'] = df['Date'].astype(str)

    df = df[(df['Date'] == date_picked) & (df['Time'] == 'All Day')]
    print('In topsite', df.shape)
    df.sort_values(f'{pollutant}_mean', inplace=True, ascending=False)
    l = 'state' if level == 'State' else 'station_name'
    df = df.iloc[:10]
    if level == 'Site':
        df['station_name'] = df['station_name'].apply(lambda x: x.split(' - ')[0])
    fig = px.bar(
        df, 
        x=f'{pollutant}_mean', 
        y=l, 
        orientation='h',
        labels={f'{pollutant}_mean': pollutant,
                 l: 'State' if l == 'state' else 'Station'},
        color=f'{pollutant}_bucket',
        color_discrete_map=colormap,
    )
    fig.update_layout(yaxis_autorange='reversed')
    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
    fig.update_layout(showlegend=False)
    return fig


@callback(
    Output('map', 'figure'),
    Input('dropdown-frequency', 'value'),
    Input('dropdown-level', 'value'),
    Input('dropdown-pollutant', 'value'),
    Input('date-picker', 'value'),
)
def update_map(freq, level, pollutant, date_picked):
    if level == 'Site':
        df = data[level][freq]
        if freq == 'Monthly':
            date_picked = date_picked[:7]
        elif freq == 'Yearly':
            date_picked = date_picked[:4]
            df['Date'] = df['Date'].astype(str)

        df = df[(df['Time'] == 'All Day') & (df['Date'] == date_picked)]
        new_df = pd.merge(stations_df, df, left_on='station_id', right_on='site_id', how='left')
        map_fig = px.scatter_mapbox(
            new_df,
            lat='latitude',
            lon='longitude',
            hover_name='station_name_x',
            custom_data=['station_id'],
            zoom=1,
            height=700,
            template='plotly',
            color=f'{pollutant}_bucket',
            color_discrete_map=colormap,
        )
        map_fig.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0})
        map_fig.update_layout(mapbox_bounds={"west": 65, "east": 100, "south": 7, "north": 37})
        map_fig.update_traces(marker=dict(size=15)) 
        map_fig.update_layout(showlegend=False)
        return map_fig
    else:
        df = data[level][freq]
        if freq == 'Monthly':
            date_picked = date_picked[:7]
        elif freq == 'Yearly':
            date_picked = date_picked[:4]
            df['Date'] = df['Date'].astype(str)
        df = df[(df['Time'] == 'All Day') & (df['Date'] == date_picked)]
        print('In map: ', df.shape)
        map_fig = px.choropleth_mapbox(
            df,
            geojson=states_geojson, 
            locations='state',
            color=f'{pollutant}_bucket',
            featureidkey='properties.NAME_1',
            color_discrete_map=colormap,
            custom_data=['state'],
            zoom=1,
            height=700,
        )
        map_fig.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0})
        map_fig.update_layout(mapbox_bounds={"west": 65, "east": 100, "south": 7, "north": 37})
        map_fig.update_layout(showlegend=False)
        return map_fig


@callback(
    Output('line', 'figure'),
    Input('dropdown-frequency', 'value'),
    Input('dropdown-level', 'value'),
    Input('dropdown-pollutant', 'value'),
    Input('date-picker', 'value'),
    Input('map', 'clickData'),
)
def update_line(freq, level, pollutant, date_picked, map_click_data):
    if date_picked is None:
        raise PreventUpdate
    if map_click_data is None:
        loc = default_loc_on_level[level] 
    else:
        loc = map_click_data['points'][0]['customdata'][0]
    loc_index = 'site_id' if level == 'Site' else 'state'
    start_date = date.fromisoformat(date_picked)

    if freq == 'Monthly':
        start_date = date(start_date.year, start_date.month, 1)
        end_date = start_date + relativedelta(months=1)
        df = data[level]['Daily']
        df = df[(df['Time'] == 'All Day') & (df[loc_index] == loc)]
        df = df.loc[df['Date'].between(str(start_date), str(end_date))]
        x_axis = 'Date'
    elif freq == 'Yearly':
        start_date = date(start_date.year, 1, 1)
        end_date = start_date + relativedelta(years=1)
        start_date -= relativedelta(days=1)
        end_date -= relativedelta(days=1)
        df = data[level]['Monthly']
        df = df[(df['Time'] == 'All Day') & (df[loc_index] == loc)]
        df = df.loc[df['Date'].between(str(start_date), str(end_date))]
        print(df.shape)
        x_axis = 'Date'
    else:
        df = data[level]['Daily']
        df = df[(df[loc_index] == loc) & (df['Date'] == str(start_date))]
        x_axis = 'Time'

    n_rows = 2
    if pollutant == 'AQI':
        n_rows = 1
    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('AQI', pollutant)
    )

    fig.add_trace(
        go.Bar(
            x = df[x_axis],
            y = df['AQI_mean'],
            customdata=df['AQI_bucket'],
            hovertemplate='<br>'.join([
                'Day: %{x}',
                'AQI: %{y}',
                'Bucket: %{customdata}',
                '<extra></extra>'
            ]),
            marker=dict(
                color=df['AQI_bucket'].replace(bucket_to_num),
                colorscale=colorscale,
                cmin=0,
                cmax=5
            )
            # line=dict(color=px.colors.qualitative.Plotly[0]),
        ),
        row=1, col=1, 
    )
    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
    fig.update_layout(height=700)
        
    fig.update_layout(
        legend=dict(
            orientation='h',
            yanchor='top',
            xanchor='right',
            y=1.06,
            x=1,
        )
    )

    if pollutant != 'AQI':
        fig.add_trace(
            go.Bar(
                x = df[x_axis],
                y = df[f'{pollutant}_mean'],
                name='Average', 
                customdata=df[f'{pollutant}_bucket'],
                hovertemplate='<br>'.join([
                    'Day: %{x}',
                    f'{pollutant}: %{{y}}',
                    'Bucket: %{customdata}',
                    '<extra></extra>'
                ]),
                marker=dict(
                    color=df[f'{pollutant}_bucket'].replace(bucket_to_num),
                    colorscale=colorscale,
                    cmin=0,
                    cmax=5
                ),
                # line=dict(color=px.colors.qualitative.Plotly[0]),
                showlegend=False,
            ),
            row=2, col=1, 
        )
        if freq != 'Daily':
            fig.update_layout(
                xaxis2_rangeslider_visible=True,
                xaxis2_rangeslider_thickness=0.1,
                xaxis2_type='date'
            ) 
    else:
        if freq != 'Daily':
            fig.update_layout(
                xaxis_rangeslider_visible=True,
                xaxis_rangeslider_thickness=0.1,
                xaxis_type='date'
            ) 

    fig.update_layout(hovermode='x')
    fig.update_layout(showlegend=False)
    return fig

@callback(
    Output('spider', 'figure'),
    Input('dropdown-frequency', 'value'),
    Input('dropdown-level', 'value'),
    Input('date-picker', 'value'),
    Input('map', 'clickData'),
)
def update_spider(freq, level, date_picked, map_click_data):
    if date_picked is None:
        raise PreventUpdate

    if map_click_data is None:
        loc = default_loc_on_level[level] 
    else:
        loc = map_click_data['points'][0]['customdata'][0]
    loc_index = 'site_id' if level == 'Site' else 'state' 
    df = data[level][freq]
    if freq == 'Monthly':
        date_picked = date_picked[:7]
    elif freq == 'Yearly':
        date_picked = date_picked[:4]
        print('In spider', date_picked)
        df['Date'] = df['Date'].astype(str)

    df = df[(df['Time'] == 'All Day') & (df['Date'] == date_picked) & (df[loc_index] == loc)].reset_index(drop=True)
    pollutants_mask = pd.isna(df[['PM2.5_mean', 'PM10_mean', 'NO2_mean', 'NH3_mean', 'SO2_mean', 'CO_mean', 'Ozone_mean']])
    new_pollutants = []
    for p in pollutants[1:]:
        try:
            if not pollutants_mask[f'{p}_mean'].iloc[0]:
                new_pollutants.append(p)
        except:
            raise PreventUpdate
    print('In spider', new_pollutants)
    pol_values = []
    for p in new_pollutants:
        try:
            v = (df[f'{p}_mean'] / pollutants_threshold[p])[0]
        except:
            raise PreventUpdate
        print(v)
        v = min(v, 1)
        pol_values.append(v)

    fig = go.Figure(go.Scatterpolar(
        r=pol_values,
        theta=new_pollutants,
        fill='toself'
    ))
    fig.update_layout(
        polar_radialaxis_range=[0, 1]
    )
    return fig

@callback(
    Output('date-picker', 'minDate'),
    Output('date-picker', 'inputFormat'),
    Output('date-picker-label', 'children'),
    Input('dropdown-frequency', 'value'),
    Input('dropdown-level', 'value'),
    Input('map', 'clickData'),
)
def update_datepicker(freq, level, map_click_data):
    if map_click_data is None:
        loc = default_loc_on_level[level] 
    else:
        loc = map_click_data['points'][0]['customdata'][0]
    loc_index = 'site_id' if level == 'Site' else 'state'
    df = data[level]['Daily']
    min_date = df[(df['Time'] == 'All Day') & (df[loc_index] == loc)]['Date'].min()
    print(min_date)
    if freq == 'Monthly':
        return [min_date, 'MMM, YY', 'Month']
    elif freq == 'Daily':
        return [min_date, 'DD MMM, YY', 'Date']
    else:
        return [min_date, 'YYYY', 'Year']


@callback(
    Output('title', 'children'),
    Input('map', 'clickData'),   
    Input('dropdown-level', 'value'),
)
def update_title(click_data, level):
    if click_data is not None:
        print(click_data)
        try:
            if level == 'State':
                return click_data['points'][0]['customdata']
            else:
                return click_data['points'][0]['hovertext']
        except:
            raise PreventUpdate
    else:
        if level == 'Site':
            return 'CRRI Mathura Road, Delhi'
        else:
            return 'Delhi'

# @callback(
#     Output('dropdown-by-2', 'options'),
#     Output('dropdown-by-2', 'value'),
#     Input('dropdown-by', 'value'),
# )
# def update_by_options(by_val):
#     if by_val == compare_by[0]:
#         return [{'label': 'State', 'value': 'State'},
#             {'label': 'Site', 'value': 'Site'}], 'State'
#     else:
#         return [{'label': 'Year', 'value': 'year'},
#                 {'label': 'Month', 'value': 'month'}], 'year'


@callback(
    Output('by-location', 'style'),
    Output('by-date', 'style'),
    Input('dropdown-by', 'value')
)
def update_menus_by(by_val):
    if by_val == compare_by[0]:
        return [{'display': 'block'}, {'display': 'none'}]
    else:
        return [{'display': 'none'}, {'display': 'block'}]


@callback(
    Output('compare-map', 'figure'),
    Input('dropdown-by-2', 'value'),
)
def update_compare_map(location):
    if location not in ('State', 'Site'):
        raise PreventUpdate
    
    if location == 'Site':
        map_fig = px.scatter_mapbox(
            stations_df,
            lat='latitude',
            lon='longitude',
            hover_name='station_name',
            custom_data=['station_id'],
            hover_data=['station_id'],
            zoom=1,
            height=700,
            template='plotly',
        )
        map_fig.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0})
        map_fig.update_layout(mapbox_bounds={"west": 65, "east": 100, "south": 7, "north": 37})
        map_fig.update_traces(marker=dict(size=15)) 
        map_fig.update_layout(showlegend=False)
        return map_fig 
    else:
        df = data['State']['Yearly']
        map_fig = px.choropleth_mapbox(
            df,
            geojson=states_geojson, 
            locations='state',
            featureidkey='properties.NAME_1',
            custom_data=['state'],
            zoom=1,
            height=700,
        )
        map_fig.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0})
        map_fig.update_layout(mapbox_bounds={"west": 65, "east": 100, "south": 7, "north": 37})
        map_fig.update_layout(showlegend=False)
        return map_fig


@callback(
    Output('multi-values', 'data'),
    Input('compare-map', 'clickData'),
    State('multi-values', 'data')
)
def add_locations(map_click_data, multi_data):
    if map_click_data is None:
        raise PreventUpdate
    loc = map_click_data['points'][0]['customdata'][0]
    if multi_data is None or multi_data == '':
        multi_data = '[]'
    curr_data = json.loads(multi_data)
    if loc not in curr_data:
        curr_data.append(loc)
    print(curr_data)
    return json.dumps(curr_data)

@callback(
    Output('multi-values', 'data', allow_duplicate=True),
    Input('dropdown-by', 'value'),
    Input('dropdown-by-2', 'value'),
    prevent_initial_call=True,
)
def reset_data(by, by_2):
    return '[]'


@callback(
    Output('compare-line', 'figure'),
    Input('dropdown-by', 'value'),
    Input('dropdown-by-2', 'value'),
    Input('dropdown-locations', 'value'),
    Input('dropdown-compare-frequency', 'value'),
    Input('compare-date-picker', 'value'),
    Input('dropdown-compare-pollutant', 'value')
)
def update_compare_line(by, by_2, locations, freq, date_picked, pollutant):
    if by == 'Location':
        loc_idx = 'state' if by_2 == 'State' else 'site_id'
        if locations is None:
            locations = []
        start_date = date.fromisoformat(date_picked)

        if freq == 'Monthly':
            start_date = date(start_date.year, start_date.month, 1)
            end_date = start_date + relativedelta(months=1)
            df = data[by_2]['Daily']
            df = df[(df['Time'] == 'All Day') & (df[loc_idx].isin(locations))]
            df = df.loc[df['Date'].between(str(start_date), str(end_date))]
        elif freq == 'Yearly':
            start_date = date(start_date.year, 1, 1)
            end_date = start_date + relativedelta(years=1)
            start_date -= relativedelta(days=1)
            end_date -= relativedelta(days=1)
            df = data[by_2]['Monthly']
            df = df[(df['Time'] == 'All Day') & (df[loc_idx].isin(locations))]
            df = df.loc[df['Date'].between(str(start_date), str(end_date))]
        print(by, by_2, locations, freq, date_picked, pollutant)
        print(df.shape)
        fig = px.line(
            df,
            x = 'Date',
            y = f'{pollutant}_mean',
            color=loc_idx,
        )
        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
        fig.update_layout(
            xaxis_rangeslider_visible=True,
            xaxis_rangeslider_thickness=0.1,
            xaxis_type='date'
        ) 
        return fig
    else:
        if locations is None:
            locations = []
        years = [(date(2018, 12, 31), date(2019, 12, 31)), 
                 (date(2019, 12, 31), date(2020, 12, 31)), 
                 (date(2020, 12, 31), date(2021, 12, 31))]
        df = data[by_2]['Monthly']
        df = df.loc[(df['Time'] == 'All Day')]
        loc_idx = 'state' if by_2 == 'State' else 'site_id'
        fig = make_subplots(rows=3, cols=1, 
                            subplot_titles=['2019', '2020', '2021'],
                            vertical_spacing=0.08)
        for i, (s, e) in enumerate(years):
            new_df = df.loc[df['Date'].between(str(s), str(e))]
            d = []
            for l in locations:
                d.append(new_df.loc[new_df[loc_idx] == l][f'{pollutant}_mean'])
            fig.add_trace(go.Heatmap(
                z = d,
                x = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                y = locations,
                coloraxis='coloraxis',
            ), row=i + 1, col=1)
            fig.update_layout(height=700)
            fig.update_layout(coloraxis=dict(colorscale='Bluered'), showlegend=False)
        
        return fig



@callback(
    Output('multi-values', 'data', allow_duplicate=True),
    Output('dropdown-locations', 'value'),
    Output('dropdown-locations', 'options'),
    Input('multi-values', 'data'),
    Input('dropdown-locations', 'value'),
    prevent_initial_call=True,
)
def sync_locations(multi_data, store_data):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if multi_data is None or multi_data == '':
        multi_data = []
    curr_data = json.loads(multi_data)
    if trigger_id == 'multi-values':
        return json.dumps(curr_data), curr_data, curr_data
    else:
        return json.dumps(store_data), store_data, store_data

controls = dbc.Card([
    html.Div([
        dbc.Label("Level"),
        dcc.Dropdown(
            id='dropdown-level',
            options=[{'label': t, 'value': t} for t in level],
            value=level[0],
            clearable=False,
        ),
    ]),

    html.Div([
        dbc.Label("Frequency"),
        dcc.Dropdown(
            id='dropdown-frequency',
            options=[{'label': t, 'value': t} for t in freq],
            value=freq[1],
            clearable=False,
        ),
    ]),
    html.Div([
        dbc.Label('Date', id='date-picker-label'),
        dmc.DatePicker(
            id='date-picker',
            value=date(2023, 3, 31),
            maxDate=date(2023, 3, 31),
            initialLevel='year',
        )
    ], 
    id='date-picker-wrap',
    ),
    html.Div([
        dbc.Label("Pollutants"),
        dcc.Dropdown(
            id='dropdown-pollutant',
            options=[{'label': t, 'value': t} for t in pollutants],
            value=pollutants[0],
            clearable=False,
        ),
    ]),
], body=True)

navbar = dbc.NavbarSimple(
    brand='AQI of India',
    color='primary',
    dark=True,
    fluid=True,
)

compare_by = ['Location', 'Date']
compare_controls = dbc.Card([
    html.Div([
        dbc.Label("Compare by"),
        dcc.Dropdown(
            id='dropdown-by',
            options=[{'label': t, 'value': t} for t in compare_by],
            value=compare_by[0],
            clearable=False,
        ),
        dcc.Dropdown(
            id='dropdown-by-2',
            options = [{'label': 'Site', 'value': 'Site'}, {'label': 'State', 'value': 'State'}],
            value='Site',
            clearable=False,
        ),
        dbc.Label('Locations'),
        dcc.Dropdown(
            id='dropdown-locations',
            multi=True,
        ),
        html.Div([
            dbc.Label('Frequency'),
            dcc.Dropdown(
                id='dropdown-compare-frequency',
                options=[{'label': t, 'value': t} for t in freq[1:]],
                value=freq[1],
                clearable=False,
            ),
            dbc.Label('Date'),
            dmc.DatePicker(
                id='compare-date-picker',
                value=date(2023, 3, 31),
                minDate=date(2015, 3, 31),
                maxDate=date(2023, 3, 31),
            ),
        ], id='by-location', style={'display': 'none'}),

        html.Div([
        ], id='by-date', style={'display': 'none'}),
        dbc.Label('Pollutant'),
        dcc.Dropdown(
            id='dropdown-compare-pollutant',
            options=[{'label': t, 'value': t} for t in pollutants],
            value=pollutants[0],
            clearable=False,
        )
    ]),

], body=True)

app.layout = dbc.Container([
    navbar,
    dcc.Tabs([
        dcc.Tab(label='Home', children=[
            html.H3(id='title'),
            dbc.Row([
                dbc.Col(dbc.Row([
                    controls,
                    dcc.Graph(id='top-site')
                ]), md=3),
                dbc.Col(dcc.Graph(id='map'), md=5),
                dbc.Col(dbc.Row([
                    dcc.Graph(id='line'),
                    dcc.Graph(id='spider'),
                ]), md=4, style={'maxHeight': '800px', 'overflow': 'scroll'})
            ]),
        ]),
        dcc.Tab(label='Compare', children=[
            html.H3(children='Compare data'),
            dbc.Row([
                dbc.Col(dbc.Row([
                    compare_controls
                ]), md=3),
                dbc.Col(dcc.Graph(id='compare-map'), md=5),
                dbc.Col(dbc.Row([
                    dcc.Graph(id='compare-line'),
                ]), md=4)
            ]),
            dcc.Store(id='multi-values'),
        ])
    ]),
],
    fluid=True,
    class_name='dbc',
    style={'padding': '0px'})


if __name__ == '__main__':
    app.run_server(debug=True)