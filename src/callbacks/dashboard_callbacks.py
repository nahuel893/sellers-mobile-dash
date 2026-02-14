"""Callbacks del dashboard principal."""
from urllib.parse import unquote

from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

from config import GRUPOS_MARCA, CATEGORIAS, NOMBRES_CATEGORIA
from src.services.ventas_service import (
    get_sucursales, get_supervisores, get_vendedores_por_supervisor,
    get_datos_vendedor, get_resumen_vendedor,
    get_datos_supervisor, get_resumen_supervisor,
    get_datos_sucursal, get_resumen_sucursal,
)
from src.layouts.gauges import crear_gauge_total, crear_ring_marca
from src.layouts.filters import crear_filtros
from src.layouts.mapa import crear_mapa


def _to_slug(nombre):
    """Convierte nombre a slug URL-safe: 'FACUNDO CACERES' → 'FACUNDO-CACERES'."""
    return nombre.strip().replace(' ', '-')


def _from_slug(slug):
    """Convierte slug a nombre: 'FACUNDO-CACERES' → 'FACUNDO CACERES'."""
    return slug.replace('-', ' ')


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


def _crear_bloque(titulo, carrusel, pct, css_class, href=None):
    """Crea un bloque con título + % + carrusel. Si href, el título es un link."""
    titulo_content = [titulo, html.Span(f'  {pct}%', className='vendor-pct')]
    if href:
        titulo_el = html.H5(
            dcc.Link(titulo_content, href=href, className='nav-link-title'),
            className=f'vendor-name {css_class}-name',
        )
    else:
        titulo_el = html.H5(
            titulo_content,
            className=f'vendor-name {css_class}-name',
        )
    return html.Div([
        titulo_el,
        carrusel,
    ], className=f'vendor-block {css_class}-block')


def _crear_seccion_sucursal(df, sucursal):
    """Genera el bloque con totales de la sucursal."""
    nombre = sucursal.split(' - ', 1)[1] if ' - ' in sucursal else sucursal
    suc_id = sucursal.split(' - ')[0]
    resumen = get_resumen_sucursal(df, sucursal)
    carrusel = _crear_seccion_agregada(
        datos_fn=lambda cat: get_datos_sucursal(df, sucursal, cat),
        resumen_fn=lambda cat: get_resumen_sucursal(df, sucursal, cat),
        anchor_id=f'sucursal-{suc_id}',
    )
    return _crear_bloque(
        nombre, carrusel, resumen['pct_tendencia'], 'sucursal',
        href=f'/sucursal/{suc_id}',
    )


def _crear_seccion_supervisor(df, supervisor, sucursal):
    """Genera el bloque con totales de un supervisor."""
    resumen = get_resumen_supervisor(df, supervisor, sucursal)
    carrusel = _crear_seccion_agregada(
        datos_fn=lambda cat: get_datos_supervisor(df, supervisor, sucursal, cat),
        resumen_fn=lambda cat: get_resumen_supervisor(df, supervisor, sucursal, cat),
        anchor_id=f'supervisor-{supervisor.lower().replace(" ", "-")}',
    )
    suc_id = sucursal.split(' - ')[0] if sucursal else ''
    suc_param = f'?sucursal={suc_id}' if suc_id else ''
    return _crear_bloque(
        supervisor, carrusel, resumen['pct_tendencia'], 'supervisor',
        href=f'/supervisor/{_to_slug(supervisor)}{suc_param}',
    )


def _crear_indice_vendedores(vendedores):
    """Barra de navegación rápida con links a cada vendedor."""
    links = [
        html.A('Inicio', href='#top', className='index-link index-link-top'),
    ]
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


def _crear_bloque_vendedor(df, vendedor):
    """Crea un bloque de vendedor con nombre-link + carrusel."""
    resumen = get_resumen_vendedor(df, vendedor)
    # Obtener sucursal para link al mapa
    vendor_data = df[df['vendedor'] == vendedor]
    suc_id = ''
    if not vendor_data.empty:
        suc = str(vendor_data.iloc[0]['sucursal'])
        suc_id = suc.split(' - ')[0] if ' - ' in suc else ''

    titulo_content = [
        vendedor,
        html.Span(f'  {resumen["pct_tendencia"]}%', className='vendor-pct'),
    ]
    mapa_link = dcc.Link(
        'Ver Mapa',
        href=f'/mapa/{_to_slug(vendedor)}?sucursal={suc_id}',
        className='mapa-btn',
    )
    return html.Div([
        html.Div([
            html.H5(
                dcc.Link(titulo_content, href=f'/vendedor/{_to_slug(vendedor)}', className='nav-link-title'),
                className='vendor-name',
            ),
            mapa_link,
        ], className='vendor-header-row'),
        _crear_seccion_vendedor(df, vendedor, con_anchor=True),
    ], className='vendor-block')


def _parse_url(pathname):
    """Parsea la URL y retorna (vista, slug).

    Rutas soportadas:
        /                              → ('home', None)
        /vendedor/FACUNDO-CACERES      → ('vendedor', 'FACUNDO-CACERES')
        /supervisor/GFLORES?sucursal=1 → ('supervisor', 'GFLORES')
        /sucursal/1                    → ('sucursal', '1')
    """
    if not pathname or pathname == '/':
        return 'home', None
    parts = [p for p in pathname.strip('/').split('/') if p]
    if len(parts) == 2:
        vista = parts[0].lower()
        slug = unquote(parts[1])
        if vista in ('vendedor', 'supervisor', 'sucursal', 'mapa'):
            return vista, slug
    return 'home', None


def register_callbacks(df):
    """Registra todos los callbacks del dashboard."""

    @callback(
        Output('page-content', 'children'),
        Input('url', 'pathname'),
        Input('url', 'search'),
    )
    def router(pathname, search):
        """Renderiza la vista según la URL."""
        vista, param = _parse_url(pathname)

        if vista == 'home':
            sucursales = get_sucursales(df)
            return html.Div([
                html.Div([
                    crear_filtros(sucursales),
                    html.Div(id='sidebar-index'),
                ], className='sidebar-panel'),
                html.Div(id='dashboard-content', className='main-content'),
            ], className='dashboard-layout')

        if vista == 'vendedor':
            return _render_vendedor_page(df, _from_slug(param))

        if vista == 'supervisor':
            # Extraer ?sucursal=<id> del query string
            sucursal = None
            if search:
                for part in search.lstrip('?').split('&'):
                    if part.startswith('sucursal='):
                        suc_id = unquote(part.split('=', 1)[1])
                        sucursal = _find_sucursal(df, suc_id)
            return _render_supervisor_page(df, _from_slug(param), sucursal)

        if vista == 'sucursal':
            return _render_sucursal_page(df, param)

        if vista == 'mapa':
            return _render_mapa_page(df, _from_slug(param), search)

        return html.Div('Página no encontrada', className='empty-state')

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
        Output('dashboard-content', 'children'),
        Output('sidebar-index', 'children'),
        Input('dropdown-supervisor', 'value'),
        Input('dropdown-sucursal', 'value'),
    )
    def actualizar_dashboard(supervisor, sucursal):
        # Totales de jerarquía: sucursal y supervisor
        seccion_suc = _crear_seccion_sucursal(df, sucursal) if sucursal else None
        seccion_sup = _crear_seccion_supervisor(df, supervisor, sucursal) if supervisor else None

        vendedores = get_vendedores_por_supervisor(df, supervisor, sucursal) if supervisor else []
        if not vendedores:
            parts = [s for s in [seccion_suc, seccion_sup] if s is not None]
            return html.Div(parts) if parts else html.Div('Sin vendedores', className='empty-state'), None

        indice = _crear_indice_vendedores(vendedores)
        secciones = [_crear_bloque_vendedor(df, v) for v in vendedores]

        parts = [s for s in [seccion_suc, seccion_sup] if s is not None]
        return html.Div([*parts, *secciones]), indice


def _crear_back_link(href, text='Volver'):
    """Link de navegación hacia atrás."""
    return html.Div(
        dcc.Link(f'< {text}', href=href, className='back-link'),
        className='back-link-container',
    )


def _find_sucursal(df, suc_id):
    """Busca sucursal por ID numérico. Retorna string completo o None."""
    for s in get_sucursales(df):
        if s.split(' - ')[0] == str(suc_id):
            return s
    return None


def _render_vendedor_page(df, vendedor):
    """Vista directa de un vendedor (sin filtros)."""
    datos = get_datos_vendedor(df, vendedor, 'CERVEZAS')
    if datos.empty:
        return html.Div(f'Vendedor "{vendedor}" no encontrado', className='empty-state')

    resumen = get_resumen_vendedor(df, vendedor)
    return html.Div([
        _crear_back_link('/'),
        html.H5(
            [vendedor, html.Span(f'  {resumen["pct_tendencia"]}%', className='vendor-pct')],
            className='vendor-name',
        ),
        _crear_seccion_vendedor(df, vendedor),
    ], className='vendor-block')


def _render_supervisor_page(df, supervisor, sucursal=None):
    """Vista de supervisor: su total + lista de vendedores."""
    vendedores = get_vendedores_por_supervisor(df, supervisor, sucursal)
    if not vendedores:
        return html.Div(f'Supervisor "{supervisor}" no encontrado', className='empty-state')

    seccion_sup = _crear_seccion_supervisor(df, supervisor, sucursal)
    indice = _crear_indice_vendedores(vendedores)
    secciones = [_crear_bloque_vendedor(df, v) for v in vendedores]

    back_href = '/'
    if sucursal:
        suc_id = sucursal.split(' - ')[0]
        back_href = f'/sucursal/{suc_id}'

    return html.Div([
        html.Div([
            _crear_back_link(back_href),
            indice,
        ], className='sidebar-panel'),
        html.Div([seccion_sup, *secciones], className='main-content'),
    ], className='dashboard-layout')


def _render_sucursal_page(df, sucursal_param):
    """Vista de sucursal: total + supervisores con resumen."""
    sucursal = _find_sucursal(df, sucursal_param)
    if not sucursal:
        return html.Div(f'Sucursal "{sucursal_param}" no encontrada', className='empty-state')

    seccion_suc = _crear_seccion_sucursal(df, sucursal)
    supervisores = get_supervisores(df, sucursal)

    secciones = []
    for sup in supervisores:
        secciones.append(_crear_seccion_supervisor(df, sup, sucursal))

    return html.Div([_crear_back_link('/'), seccion_suc, *secciones])


def _render_mapa_page(df, vendedor, search=None):
    """Vista de mapa con clientes asignados al vendedor."""
    # Extraer sucursal del query string
    id_sucursal = None
    if search:
        for part in search.lstrip('?').split('&'):
            if part.startswith('sucursal='):
                id_sucursal = unquote(part.split('=', 1)[1])

    # Fallback: obtener sucursal del dataframe
    if not id_sucursal:
        vendor_data = df[df['vendedor'] == vendedor]
        if not vendor_data.empty:
            suc = str(vendor_data.iloc[0]['sucursal'])
            id_sucursal = suc.split(' - ')[0] if ' - ' in suc else None

    if not id_sucursal:
        return html.Div([
            _crear_back_link('/'),
            html.Div(f'Vendedor "{vendedor}" no encontrado', className='empty-state'),
        ])

    try:
        from src.data.db import get_connection
        from src.data.queries import query_clientes_vendedor
        conn = get_connection()
        df_clientes = query_clientes_vendedor(conn, vendedor, id_sucursal)
        conn.close()
    except Exception:
        return html.Div([
            _crear_back_link('/'),
            html.Div('Mapa no disponible sin conexión a BD', className='empty-state'),
        ])

    mapa = crear_mapa(df_clientes, vendedor)
    return html.Div([
        _crear_back_link('/'),
        html.H5(f'Clientes de {vendedor}', className='vendor-name'),
        mapa,
    ])
