"""Componentes visuales: gauge total y ring por marca."""
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from config import COLORES_GRUPO, color_por_rendimiento


def _fmt(n):
    """Formatea número con separador de miles (punto)."""
    return f'{n:,}'.replace(',', '.')


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
                html.Span(_fmt(ventas), className='metric-value'),
            ], className='metric-item'),
            html.Div([
                html.Span('Cupo', className='metric-label'),
                html.Span(_fmt(cupo), className='metric-value'),
            ], className='metric-item'),
            html.Div([
                html.Span('Falta', className='metric-label'),
                html.Span(_fmt(falta), className='metric-value metric-falta'),
            ], className='metric-item'),
            html.Div([
                html.Span('Tendencia', className='metric-label'),
                html.Span(_fmt(tendencia), className='metric-value'),
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
                    html.Span(_fmt(ventas), className='metric-value-sm'),
                ], className='metric-item-sm'),
                html.Div([
                    html.Span('Cupo', className='metric-label-sm'),
                    html.Span(_fmt(cupo), className='metric-value-sm'),
                ], className='metric-item-sm'),
                html.Div([
                    html.Span('Falta', className='metric-label-sm'),
                    html.Span(
                        _fmt(falta),
                        className='metric-value-sm metric-falta',
                    ),
                ], className='metric-item-sm'),
            ], className='metrics-row-sm'),
        ], className='marca-card-body'),
    ], className='marca-card')
