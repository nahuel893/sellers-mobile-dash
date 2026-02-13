"""Callbacks del dashboard principal."""
from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc

from config import GRUPOS_MARCA
from src.services.ventas_service import (
    get_vendedores_por_supervisor, get_datos_vendedor, get_resumen_vendedor,
)
from src.layouts.gauges import crear_gauge_total, crear_ring_marca


def _crear_seccion_vendedor(df, vendedor, con_anchor=False):
    """Genera la sección completa de un vendedor (gauge + marcas)."""
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

    cols_marcas = [
        dbc.Col(card, xs=6, md=4, xl=2, className='marca-col')
        for card in cards_marcas
    ]

    vendor_id = vendedor.lower().replace(' ', '-')

    return html.Div([
        html.Div(id=f'vendor-{vendor_id}', className='vendor-anchor'),
        html.Div([
            html.H6('Total Cervezas', className='section-title'),
            gauge_total,
        ], className='section-total'),
        html.Div([
            html.H6('Detalle por Marca', className='section-title'),
            dbc.Row(cols_marcas, className='marca-grid'),
        ], className='section-marcas'),
    ], className='vendor-section')


def _crear_indice_vendedores(vendedores):
    """Barra de navegación rápida con links a cada vendedor."""
    links = []
    for v in vendedores:
        vendor_id = v.lower().replace(' ', '-')
        links.append(
            html.A(
                v.split(' ')[0],
                href=f'#vendor-{vendor_id}',
                className='index-link',
            )
        )
    return html.Div(links, className='vendor-index')


def register_callbacks(df):
    """Registra todos los callbacks del dashboard."""

    @callback(
        Output('dropdown-vendedor', 'options'),
        Output('dropdown-vendedor', 'value'),
        Output('dropdown-vendedor', 'disabled'),
        Input('dropdown-supervisor', 'value'),
        Input('check-desplegar-todos', 'value'),
    )
    def actualizar_vendedores(supervisor, desplegar_todos):
        vendedores = get_vendedores_por_supervisor(df, supervisor)
        options = [{'label': v, 'value': v} for v in vendedores]
        disabled = 'todos' in (desplegar_todos or [])
        return options, vendedores[0] if vendedores else None, disabled

    @callback(
        Output('dashboard-content', 'children'),
        Input('dropdown-vendedor', 'value'),
        Input('dropdown-supervisor', 'value'),
        Input('check-desplegar-todos', 'value'),
    )
    def actualizar_dashboard(vendedor, supervisor, desplegar_todos):
        mostrar_todos = 'todos' in (desplegar_todos or [])

        if mostrar_todos:
            vendedores = get_vendedores_por_supervisor(df, supervisor)
            if not vendedores:
                return html.Div('Sin vendedores', className='empty-state')

            indice = _crear_indice_vendedores(vendedores)
            secciones = []
            for v in vendedores:
                resumen = get_resumen_vendedor(df, v)
                secciones.append(html.Div([
                    html.H5(
                        [v, html.Span(f'  {resumen["pct_tendencia"]}%', className='vendor-pct')],
                        className='vendor-name',
                    ),
                    _crear_seccion_vendedor(df, v, con_anchor=True),
                ], className='vendor-block'))

            return html.Div([indice, *secciones])

        if not vendedor:
            return html.Div('Seleccione un vendedor', className='empty-state')

        return _crear_seccion_vendedor(df, vendedor)
