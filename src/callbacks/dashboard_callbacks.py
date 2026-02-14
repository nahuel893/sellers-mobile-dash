"""Callbacks del dashboard principal."""
from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc

from config import GRUPOS_MARCA, CATEGORIAS, NOMBRES_CATEGORIA
from src.services.ventas_service import (
    get_supervisores, get_vendedores_por_supervisor,
    get_datos_vendedor, get_resumen_vendedor,
    get_datos_supervisor, get_resumen_supervisor,
    get_datos_sucursal, get_resumen_sucursal,
)
from src.layouts.gauges import crear_gauge_total, crear_ring_marca


def _crear_slide_cervezas(datos, resumen):
    """Slide de cervezas: gauge total + detalle por marca."""
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

    return html.Div([
        html.Div([
            html.H6('Total Cervezas', className='section-title'),
            gauge_total,
        ], className='section-total'),
        html.Div([
            html.H6('Detalle por Marca', className='section-title'),
            dbc.Row(cols_marcas, className='marca-grid'),
        ], className='section-marcas'),
    ], className='carousel-slide')


def _crear_slide_otros(resumenes):
    """Slide combinado con gauges de varias categorías (sin desglose por marca).

    resumenes: lista de (nombre_categoria, resumen_dict)
    """
    secciones = []
    for nombre, resumen in resumenes:
        gauge = crear_gauge_total(
            pct=resumen['pct_tendencia'],
            ventas=resumen['ventas'],
            cupo=resumen['cupo'],
            falta=resumen['falta'],
            tendencia=resumen['tendencia'],
        )
        secciones.append(html.Div([
            html.H6(f'Total {nombre}', className='section-title'),
            gauge,
        ], className='section-total'))

    return html.Div(secciones, className='carousel-slide')


def _crear_carrusel(slides, anchor_id):
    """Genera el carrusel con dots de navegación."""
    dots = [
        html.Span(
            className='carousel-dot active' if i == 0 else 'carousel-dot'
        )
        for i in range(len(slides))
    ]

    return html.Div([
        html.Div(id=anchor_id, className='vendor-anchor'),
        html.Div([
            html.Div(slides, className='carousel-track'),
            html.Div(dots, className='carousel-dots'),
        ], className='vendor-carousel'),
    ], className='vendor-section')


def _crear_seccion_vendedor(df, vendedor, con_anchor=False):
    """Genera el carrusel completo de un vendedor con slides por categoría."""
    vendor_id = vendedor.lower().replace(' ', '-')
    otros = [c for c in CATEGORIAS if c != 'CERVEZAS']

    datos_cerv = get_datos_vendedor(df, vendedor, 'CERVEZAS')
    resumen_cerv = get_resumen_vendedor(df, vendedor, 'CERVEZAS')

    otros_resumenes = [
        (NOMBRES_CATEGORIA.get(cat, cat), get_resumen_vendedor(df, vendedor, cat))
        for cat in otros
    ]

    slides = [
        _crear_slide_cervezas(datos_cerv, resumen_cerv),
        _crear_slide_otros(otros_resumenes),
    ]

    return _crear_carrusel(slides, f'vendor-{vendor_id}')


def _crear_seccion_agregada(datos_fn, resumen_fn, anchor_id):
    """Genera un carrusel con datos agregados (sucursal, supervisor, etc.)."""
    otros = [c for c in CATEGORIAS if c != 'CERVEZAS']

    datos_cerv = datos_fn('CERVEZAS')
    resumen_cerv = resumen_fn('CERVEZAS')

    otros_resumenes = [
        (NOMBRES_CATEGORIA.get(cat, cat), resumen_fn(cat))
        for cat in otros
    ]

    slides = [
        _crear_slide_cervezas(datos_cerv, resumen_cerv),
        _crear_slide_otros(otros_resumenes),
    ]

    return _crear_carrusel(slides, anchor_id)


def _crear_bloque(titulo, carrusel, pct, css_class):
    """Crea un bloque con título + % + carrusel."""
    return html.Div([
        html.H5(
            [titulo, html.Span(f'  {pct}%', className='vendor-pct')],
            className=f'vendor-name {css_class}-name',
        ),
        carrusel,
    ], className=f'vendor-block {css_class}-block')


def _crear_seccion_sucursal(df, sucursal):
    """Genera el bloque con totales de la sucursal."""
    nombre = sucursal.split(' - ', 1)[1] if ' - ' in sucursal else sucursal
    resumen = get_resumen_sucursal(df, sucursal)
    carrusel = _crear_seccion_agregada(
        datos_fn=lambda cat: get_datos_sucursal(df, sucursal, cat),
        resumen_fn=lambda cat: get_resumen_sucursal(df, sucursal, cat),
        anchor_id=f'sucursal-{sucursal.split(" - ")[0]}',
    )
    return _crear_bloque(nombre, carrusel, resumen['pct_tendencia'], 'sucursal')


def _crear_seccion_supervisor(df, supervisor, sucursal):
    """Genera el bloque con totales de un supervisor."""
    resumen = get_resumen_supervisor(df, supervisor, sucursal)
    carrusel = _crear_seccion_agregada(
        datos_fn=lambda cat: get_datos_supervisor(df, supervisor, sucursal, cat),
        resumen_fn=lambda cat: get_resumen_supervisor(df, supervisor, sucursal, cat),
        anchor_id=f'supervisor-{supervisor.lower().replace(" ", "-")}',
    )
    return _crear_bloque(supervisor, carrusel, resumen['pct_tendencia'], 'supervisor')


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
        Output('dropdown-supervisor', 'options'),
        Output('dropdown-supervisor', 'value'),
        Input('dropdown-sucursal', 'value'),
    )
    def actualizar_supervisores(sucursal):
        supervisores = get_supervisores(df, sucursal)
        options = [{'label': s, 'value': s} for s in supervisores]
        return options, supervisores[0] if supervisores else None

    @callback(
        Output('dropdown-vendedor', 'options'),
        Output('dropdown-vendedor', 'value'),
        Output('dropdown-vendedor', 'disabled'),
        Input('dropdown-supervisor', 'value'),
        Input('dropdown-sucursal', 'value'),
        Input('check-desplegar-todos', 'value'),
    )
    def actualizar_vendedores(supervisor, sucursal, desplegar_todos):
        if not supervisor:
            return [], None, False
        vendedores = get_vendedores_por_supervisor(df, supervisor, sucursal)
        options = [{'label': v, 'value': v} for v in vendedores]
        disabled = 'todos' in (desplegar_todos or [])
        return options, vendedores[0] if vendedores else None, disabled

    @callback(
        Output('dashboard-content', 'children'),
        Input('dropdown-vendedor', 'value'),
        Input('dropdown-supervisor', 'value'),
        Input('dropdown-sucursal', 'value'),
        Input('check-desplegar-todos', 'value'),
    )
    def actualizar_dashboard(vendedor, supervisor, sucursal, desplegar_todos):
        mostrar_todos = 'todos' in (desplegar_todos or [])

        # Totales de jerarquía: sucursal y supervisor
        seccion_suc = _crear_seccion_sucursal(df, sucursal) if sucursal else None
        seccion_sup = _crear_seccion_supervisor(df, supervisor, sucursal) if supervisor else None

        if mostrar_todos:
            vendedores = get_vendedores_por_supervisor(df, supervisor, sucursal)
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

            parts = [s for s in [seccion_suc, seccion_sup, indice] if s is not None]
            return html.Div([*parts, *secciones])

        if not vendedor:
            return html.Div('Seleccione un vendedor', className='empty-state')

        parts = [s for s in [seccion_suc, seccion_sup] if s is not None]
        parts.append(_crear_seccion_vendedor(df, vendedor))
        return html.Div(parts)
