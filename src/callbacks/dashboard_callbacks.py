"""Callbacks del dashboard principal."""
from urllib.parse import unquote

from dash import html, callback, Input, Output

from src.data.data_loader import get_dataframe
from src.services.ventas_service import (
    get_sucursales, get_supervisores, get_vendedores_por_supervisor,
)
from src.layouts.filters import crear_filtros
from src.callbacks.views import (
    from_slug, find_sucursal,
    crear_category_toggle, crear_indice_vendedores,
    crear_seccion_sucursal, crear_seccion_supervisor, crear_bloque_vendedor,
    render_vendedor_page, render_supervisor_page,
    render_sucursal_page, render_mapa_page,
)


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


def register_callbacks():
    """Registra todos los callbacks del dashboard."""

    @callback(
        Output('page-content', 'children'),
        Input('url', 'pathname'),
        Input('url', 'search'),
    )
    def router(pathname, search):
        """Renderiza la vista según la URL."""
        df = get_dataframe()
        vista, param = _parse_url(pathname)

        if vista == 'home':
            sucursales = get_sucursales(df)
            return html.Div([
                html.Div([
                    crear_filtros(sucursales),
                    crear_category_toggle(),
                    html.Div(id='sidebar-index'),
                ], className='sidebar-panel'),
                html.Div(id='dashboard-content', className='main-content'),
            ], className='dashboard-layout')

        if vista == 'vendedor':
            return render_vendedor_page(df, from_slug(param))

        if vista == 'supervisor':
            sucursal = None
            if search:
                for part in search.lstrip('?').split('&'):
                    if part.startswith('sucursal='):
                        suc_id = unquote(part.split('=', 1)[1])
                        sucursal = find_sucursal(df, suc_id)
            return render_supervisor_page(df, from_slug(param), sucursal)

        if vista == 'sucursal':
            return render_sucursal_page(df, param)

        if vista == 'mapa':
            return render_mapa_page(df, from_slug(param), search)

        return html.Div('Página no encontrada', className='empty-state')

    @callback(
        Output('dropdown-supervisor', 'options'),
        Output('dropdown-supervisor', 'value'),
        Input('dropdown-sucursal', 'value'),
    )
    def actualizar_supervisores(sucursal):
        df = get_dataframe()
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
        df = get_dataframe()
        seccion_suc = crear_seccion_sucursal(df, sucursal) if sucursal else None
        seccion_sup = crear_seccion_supervisor(df, supervisor, sucursal) if supervisor else None

        vendedores = get_vendedores_por_supervisor(df, supervisor, sucursal) if supervisor else []
        if not vendedores:
            parts = [s for s in [seccion_suc, seccion_sup] if s is not None]
            return html.Div(parts) if parts else html.Div('Sin vendedores', className='empty-state'), None

        indice = crear_indice_vendedores(vendedores)
        secciones = [crear_bloque_vendedor(df, v) for v in vendedores]

        parts = [s for s in [seccion_suc, seccion_sup] if s is not None]
        return html.Div([*parts, *secciones]), indice
