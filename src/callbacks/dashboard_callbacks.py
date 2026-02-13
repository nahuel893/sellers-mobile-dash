"""Callbacks del dashboard principal."""
from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc

from config import GRUPOS_MARCA
from src.services.ventas_service import (
    get_vendedores_por_supervisor, get_datos_vendedor, get_resumen_vendedor,
)
from src.layouts.gauges import crear_gauge_total, crear_ring_marca


def register_callbacks(df):
    """Registra todos los callbacks del dashboard."""

    @callback(
        Output('dropdown-vendedor', 'options'),
        Output('dropdown-vendedor', 'value'),
        Input('dropdown-supervisor', 'value'),
    )
    def actualizar_vendedores(supervisor):
        vendedores = get_vendedores_por_supervisor(df, supervisor)
        options = [{'label': v, 'value': v} for v in vendedores]
        return options, vendedores[0] if vendedores else None

    @callback(
        Output('dashboard-content', 'children'),
        Input('dropdown-vendedor', 'value'),
    )
    def actualizar_dashboard(vendedor):
        if not vendedor:
            return html.Div('Seleccione un vendedor', className='empty-state')

        datos = get_datos_vendedor(df, vendedor)
        resumen = get_resumen_vendedor(df, vendedor)

        gauge_total = crear_gauge_total(
            pct=resumen['pct_tendencia'],
            ventas=resumen['ventas'],
            cupo=resumen['cupo'],
            falta=resumen['falta'],
            tendencia=resumen['tendencia'],
        )

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

        # Grilla responsive: 2 cols mobile, 3 tablet, 6 desktop
        cols_marcas = [
            dbc.Col(card, xs=6, md=4, xl=2, className='marca-col')
            for card in cards_marcas
        ]

        return html.Div([
            html.Div([
                html.H6('Total Cervezas', className='section-title'),
                gauge_total,
            ], className='section-total'),
            html.Div([
                html.H6('Detalle por Marca', className='section-title'),
                dbc.Row(cols_marcas, className='marca-grid'),
            ], className='section-marcas'),
        ])
