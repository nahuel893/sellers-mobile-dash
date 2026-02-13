"""
Dashboard Avance Preventa - Mobile First
"""
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from config import (
    GRUPOS_MARCA, COLORES_GRUPO, DIAS_HABILES,
    DIAS_TRANSCURRIDOS, DIAS_RESTANTES, color_por_rendimiento,
)
from src.data.mock_data import get_mock_dataframe
from src.services.ventas_service import (
    get_supervisores, get_vendedores_por_supervisor,
    get_datos_vendedor, get_resumen_vendedor,
)

# ============================================================
# Datos
# ============================================================
DF = get_mock_dataframe()

# ============================================================
# App
# ============================================================
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1"},
    ],
)
app.title = "Avance Preventa"


# ============================================================
# Componentes reutilizables
# ============================================================
def crear_gauge_total(pct, ventas, cupo, falta, tendencia):
    """Gauge circular grande para el resumen total."""
    color = color_por_rendimiento(pct)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={'suffix': '%', 'font': {'size': 48, 'color': '#1a1a2e', 'family': 'Inter'}},
        gauge={
            'axis': {
                'range': [0, 150],
                'tickwidth': 0,
                'tickcolor': 'rgba(0,0,0,0)',
                'tickfont': {'size': 1, 'color': 'rgba(0,0,0,0)'},
            },
            'bar': {'color': color, 'thickness': 0.82},
            'bgcolor': '#e9ecef',
            'borderwidth': 0,
            'steps': [],
            'threshold': {
                'line': {'color': '#1a1a2e', 'width': 3},
                'thickness': 0.85,
                'value': 100,
            },
            'shape': 'angular',
        },
    ))
    fig.update_layout(
        margin=dict(t=30, b=0, l=30, r=30),
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter'},
    )

    return html.Div([
        dcc.Graph(figure=fig, config={'displayModeBar': False}, className='gauge-total'),
        html.Div([
            html.Div([
                html.Span('Vendido', className='metric-label'),
                html.Span(f'{ventas:,}'.replace(',', '.'), className='metric-value'),
            ], className='metric-item'),
            html.Div([
                html.Span('Cupo', className='metric-label'),
                html.Span(f'{cupo:,}'.replace(',', '.'), className='metric-value'),
            ], className='metric-item'),
            html.Div([
                html.Span('Falta', className='metric-label'),
                html.Span(f'{falta:,}'.replace(',', '.'), className='metric-value metric-falta'),
            ], className='metric-item'),
            html.Div([
                html.Span('Tendencia', className='metric-label'),
                html.Span(f'{tendencia:,}'.replace(',', '.'), className='metric-value'),
            ], className='metric-item'),
        ], className='metrics-row'),
    ], className='summary-card')


def crear_ring_marca(grupo, pct, ventas, cupo, falta):
    """Anillo circular para una marca individual."""
    color_marca = COLORES_GRUPO.get(grupo, '#666')
    color_pct = color_por_rendimiento(pct)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=min(pct, 150),
        number={
            'suffix': '%',
            'font': {'size': 28, 'color': '#1a1a2e', 'family': 'Inter'},
        },
        gauge={
            'axis': {
                'range': [0, 150],
                'tickwidth': 0,
                'tickcolor': 'rgba(0,0,0,0)',
                'tickfont': {'size': 1, 'color': 'rgba(0,0,0,0)'},
            },
            'bar': {'color': color_pct, 'thickness': 0.8},
            'bgcolor': '#e9ecef',
            'borderwidth': 0,
            'steps': [],
            'threshold': {
                'line': {'color': '#1a1a2e', 'width': 2},
                'thickness': 0.85,
                'value': 100,
            },
            'shape': 'angular',
        },
    ))
    fig.update_layout(
        margin=dict(t=25, b=0, l=20, r=20),
        height=140,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter'},
    )

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div(
                    className='marca-color-dot',
                    style={'backgroundColor': color_marca},
                ),
                html.H6(grupo, className='marca-title'),
            ], className='marca-header'),
            dcc.Graph(
                figure=fig,
                config={'displayModeBar': False},
                className='gauge-marca',
            ),
            html.Div([
                html.Div([
                    html.Span('Vendido', className='metric-label-sm'),
                    html.Span(f'{ventas:,}'.replace(',', '.'), className='metric-value-sm'),
                ], className='metric-item-sm'),
                html.Div([
                    html.Span('Cupo', className='metric-label-sm'),
                    html.Span(f'{cupo:,}'.replace(',', '.'), className='metric-value-sm'),
                ], className='metric-item-sm'),
                html.Div([
                    html.Span('Falta', className='metric-label-sm'),
                    html.Span(
                        f'{falta:,}'.replace(',', '.'),
                        className='metric-value-sm metric-falta',
                    ),
                ], className='metric-item-sm'),
            ], className='metrics-row-sm'),
        ], className='marca-card-body'),
    ], className='marca-card')


# ============================================================
# Layout
# ============================================================
app.layout = dbc.Container([

    # --- Header ---
    html.Div([
        html.H4('Avance Preventa', className='header-title'),
        html.Div([
            html.Span(f'Viernes, 13 de febrero de 2026', className='header-date'),
        ]),
        html.Div([
            html.Div([
                html.Span('Días hábiles', className='dias-label'),
                html.Span(str(DIAS_HABILES), className='dias-value'),
            ], className='dias-item'),
            html.Div([
                html.Span('Transcurridos', className='dias-label'),
                html.Span(str(DIAS_TRANSCURRIDOS), className='dias-value dias-trans'),
            ], className='dias-item'),
            html.Div([
                html.Span('Faltan', className='dias-label'),
                html.Span(str(DIAS_RESTANTES), className='dias-value dias-rest'),
            ], className='dias-item'),
        ], className='dias-row'),
    ], className='header-section'),

    # --- Filtros ---
    html.Div([
        html.Div([
            html.Label('Supervisor', className='filter-label'),
            dcc.Dropdown(
                id='dropdown-supervisor',
                options=[{'label': s, 'value': s} for s in get_supervisores(DF)],
                value=get_supervisores(DF)[0],
                clearable=False,
                className='filter-dropdown',
            ),
        ], className='filter-group'),
        html.Div([
            html.Label('Vendedor', className='filter-label'),
            dcc.Dropdown(
                id='dropdown-vendedor',
                clearable=False,
                className='filter-dropdown',
            ),
        ], className='filter-group'),
    ], className='filters-section'),

    # --- Contenido dinámico ---
    html.Div(id='dashboard-content'),

], fluid=True, className='app-container')


# ============================================================
# Callbacks
# ============================================================
@callback(
    Output('dropdown-vendedor', 'options'),
    Output('dropdown-vendedor', 'value'),
    Input('dropdown-supervisor', 'value'),
)
def actualizar_vendedores(supervisor):
    vendedores = get_vendedores_por_supervisor(DF, supervisor)
    options = [{'label': v, 'value': v} for v in vendedores]
    return options, vendedores[0] if vendedores else None


@callback(
    Output('dashboard-content', 'children'),
    Input('dropdown-vendedor', 'value'),
)
def actualizar_dashboard(vendedor):
    if not vendedor:
        return html.Div('Seleccione un vendedor', className='empty-state')

    # Datos del vendedor
    datos = get_datos_vendedor(DF, vendedor)
    resumen = get_resumen_vendedor(DF, vendedor)

    # --- Gauge total ---
    gauge_total = crear_gauge_total(
        pct=resumen['pct_tendencia'],
        ventas=resumen['ventas'],
        cupo=resumen['cupo'],
        falta=resumen['falta'],
        tendencia=resumen['tendencia'],
    )

    # --- Cards por marca ---
    cards_marcas = []
    for grupo in GRUPOS_MARCA:
        fila = datos[datos['grupo_marca'] == grupo]
        if fila.empty:
            continue
        row = fila.iloc[0]
        card = crear_ring_marca(
            grupo=grupo,
            pct=int(row['pct_tendencia']),
            ventas=int(row['ventas']),
            cupo=int(row['cupo']),
            falta=int(row['falta']),
        )
        cards_marcas.append(card)

    # Distribuir cards en grilla de 2 columnas
    filas_grilla = []
    for i in range(0, len(cards_marcas), 2):
        cols = [dbc.Col(cards_marcas[i], width=6)]
        if i + 1 < len(cards_marcas):
            cols.append(dbc.Col(cards_marcas[i + 1], width=6))
        filas_grilla.append(dbc.Row(cols, className='marca-row'))

    return html.Div([
        html.Div([
            html.H6('Total Cervezas', className='section-title'),
            gauge_total,
        ], className='section-total'),
        html.Div([
            html.H6('Detalle por Marca', className='section-title'),
            *filas_grilla,
        ], className='section-marcas'),
    ])


# ============================================================
# Run
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
