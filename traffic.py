import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import folium
from folium.plugins import HeatMap
from dash.dependencies import Input, Output

df_road_restrictions = pd.read_csv('restrictions.csv')
df_road_restrictions = df_road_restrictions.reset_index()  # Resets the MultiIndex to columns

# If the first row contains actual column names, set it as the header
df_road_restrictions.columns = df_road_restrictions.iloc[0]  # Set the first row as column names
df_road_restrictions = df_road_restrictions[1:] 
df_road_restrictions = df_road_restrictions[(df_road_restrictions["MaxImpact"] == "High") | (df_road_restrictions["MaxImpact"] == "Medium")]

df_road_restrictions['Latitude'] = pd.to_numeric(df_road_restrictions['Latitude'], errors='coerce')
df_road_restrictions['Longitude'] = pd.to_numeric(df_road_restrictions['Longitude'], errors='coerce')

df_road_restrictions = df_road_restrictions.dropna(subset=["Latitude", "Longitude"])


df_congestion = pd.read_csv('congestion.csv')
df_congestion_clean = df_congestion.dropna(subset=['latitude', 'longitude', 'avg_daily_vol'])

collisions_df = pd.read_csv('collide_2024.csv')
fatal_collisions = collisions_df[collisions_df["FATALITIES"] > 0]
fatal_collisions = fatal_collisions[(fatal_collisions['LAT_WGS84'] != 0.00) & (fatal_collisions['LONG_WGS84'] != 0.00)]

df_bridges = pd.read_csv('poor_bridges.csv')

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# Default button styles
default_button_style = {
    'padding': '10px',
    'margin': '5px',
    'opacity': 1, 
    'border': '1px solid black',
    'color': 'white',
    'background-color': '#007bff',  # Blue color for better visibility
    'font-weight': 'bold',
    'border-radius': '8px'
}

# Layout with buttons for toggling features
app.layout = html.Div([
    html.H1("Toronto Traffic Dashboard", 
            style={'text-align': 'center', 'margin-bottom': '20px', 'font-weight': 'bold', 'font-family': 'Arial, sans-serif'}),
    
    dbc.Row([
        dbc.Col(html.Button("Traffic Congestion Heatmap", id="toggle-heatmap", n_clicks=0, style=default_button_style), width=3),
        dbc.Col(html.Button("Road Closures", id="toggle-markers", n_clicks=0, style=default_button_style), width=3),
        dbc.Col(html.Button("Poor Bridge Locations", id="toggle-bridges", n_clicks=0, style=default_button_style), width=3),
        dbc.Col(html.Button("Fatal Collisions", id="toggle-collisions", n_clicks=0, style=default_button_style), width=3),
    ], style={'margin-bottom': '20px', 'justify-content': 'center'}),

    # Map container
    dbc.Row([
        dbc.Col(html.Div([
            dcc.Loading(id="loading", type="circle", children=html.Iframe(id="map", width="100%", height="600px", 
                                                                         style={'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'}))
        ]), width=12)
    ])
])

# Callback to update button styles dynamically
@app.callback(
    [
        Output("toggle-heatmap", "style"),
        Output("toggle-markers", "style"),
        Output("toggle-bridges", "style"),
        Output("toggle-collisions", "style")
    ],
    [
        Input("toggle-heatmap", "n_clicks"),
        Input("toggle-markers", "n_clicks"),
        Input("toggle-bridges", "n_clicks"),
        Input("toggle-collisions", "n_clicks")
    ]
)
def update_button_styles(n_heatmap, n_markers, n_bridges, n_collisions):
    bright_style = default_button_style.copy()
    bright_style['opacity'] = 1
    bright_style['background-color'] = '#28a745'  # Green for active buttons

    dim_style = default_button_style.copy()
    dim_style['opacity'] = 0.6
    dim_style['background-color'] = '#007bff'  # Blue for inactive buttons

    return (
        bright_style if n_heatmap % 2 == 1 else dim_style,
        bright_style if n_markers % 2 == 1 else dim_style,
        bright_style if n_bridges % 2 == 1 else dim_style,
        bright_style if n_collisions % 2 == 1 else dim_style
    )

# Callback to update map based on toggles
@app.callback(
    Output("map", "srcDoc"),
    [
        Input("toggle-heatmap", "n_clicks"),
        Input("toggle-markers", "n_clicks"),
        Input("toggle-bridges", "n_clicks"),
        Input("toggle-collisions", "n_clicks")
    ]
)
def update_map(n_heatmap, n_markers, n_bridges, n_collisions):
    m = folium.Map(location=[43.7, -79.42], zoom_start=12)

    # Add road restriction markers
    if n_markers % 2 == 1:
        for _, row in df_road_restrictions.iterrows():
            folium.Marker([row['Latitude'], row['Longitude']], popup=row['Description']).add_to(m)

    # Add congestion heatmap
    if n_heatmap % 2 == 1:
        heat_data = [[row['latitude'], row['longitude'], row['avg_daily_vol']] 
                     for _, row in df_congestion.iterrows() if row['avg_daily_vol'] > 25000]
        HeatMap(heat_data).add_to(m)

    # Add bridge markers
    if n_bridges % 2 == 1:
        for _, row in df_bridges.iterrows():
            bridge_icon = folium.CustomIcon(icon_image="bridge_logo.png", icon_size=(30, 30), icon_anchor=(15, 30))
            folium.Marker(
                [row['Latitude'], row['Longitude']], 
                popup=row['CONDITION'],
                icon=bridge_icon
            ).add_to(m)

    # Add fatal collision markers
    if n_collisions % 2 == 1:
        for _, row in fatal_collisions.iterrows():
            death_marker = folium.CustomIcon(icon_image="skull.png", icon_size=(30, 30), icon_anchor=(15, 30))
            folium.Marker(
                [row['LAT_WGS84'], row['LONG_WGS84']], 
                popup=f"Fatalities: {row['FATALITIES']}", 
                icon=death_marker
            ).add_to(m)

    return m._repr_html_()

server = app.server 


