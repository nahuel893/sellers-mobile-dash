"""Componente de filtros (dropdowns)."""
from dash import html, dcc


def crear_filtros(sucursales):
    """Dropdowns de sucursal y supervisor."""
    return html.Div([
        html.Div([
            html.Div([
                html.Label('Sucursal', className='filter-label'),
                dcc.Dropdown(
                    id='dropdown-sucursal',
                    options=[{'label': s, 'value': s} for s in sucursales],
                    value=sucursales[0] if sucursales else None,
                    clearable=False,
                    className='filter-dropdown',
                ),
            ], className='filter-group'),
            html.Div([
                html.Label('Supervisor', className='filter-label'),
                dcc.Dropdown(
                    id='dropdown-supervisor',
                    clearable=False,
                    className='filter-dropdown',
                ),
            ], className='filter-group'),
        ], className='filters-row'),
    ], className='filters-section')
