"""Componente de filtros (dropdowns)."""
from dash import html, dcc
import dash_bootstrap_components as dbc


def crear_filtros(supervisores):
    """Dropdowns de supervisor y vendedor + checkbox desplegar todos."""
    return html.Div([
        html.Div([
            html.Div([
                html.Label('Supervisor', className='filter-label'),
                dcc.Dropdown(
                    id='dropdown-supervisor',
                    options=[{'label': s, 'value': s} for s in supervisores],
                    value=supervisores[0] if supervisores else None,
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
        ], className='filters-row'),
        dbc.Checklist(
            id='check-desplegar-todos',
            options=[{'label': '  Desplegar todos', 'value': 'todos'}],
            value=[],
            className='check-todos',
            switch=True,
        ),
    ], className='filters-section')
