"""Componente de mapa de clientes."""
from dash import html, dcc
import plotly.graph_objects as go


def crear_mapa(df_clientes, vendedor):
    """Mapa Scattermapbox con los clientes asignados al vendedor."""
    if df_clientes.empty:
        return html.Div(
            f'Sin clientes con coordenadas para "{vendedor}"',
            className='empty-state',
        )

    # Nombre a mostrar: fantasia si existe, sino razon_social
    nombres = df_clientes['fantasia'].fillna(df_clientes['razon_social'])
    hover_text = nombres + '<br>' + df_clientes['des_localidad'].fillna('')

    fig = go.Figure(go.Scattermapbox(
        lat=df_clientes['latitud'],
        lon=df_clientes['longitud'],
        mode='markers',
        marker=dict(size=10, color='#1565C0'),
        text=hover_text,
        hoverinfo='text',
    ))

    fig.update_layout(
        mapbox_style='open-street-map',
        mapbox=dict(
            center=dict(
                lat=df_clientes['latitud'].mean(),
                lon=df_clientes['longitud'].mean(),
            ),
            zoom=12,
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        height=600,
    )

    return html.Div([
        html.Div(
            f'{len(df_clientes)} clientes',
            className='mapa-count',
        ),
        dcc.Graph(
            figure=fig,
            config={'displayModeBar': False},
            className='mapa-graph',
        ),
    ], className='mapa-container')
