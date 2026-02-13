"""Componente header con título, fecha y días."""
from dash import html
from config import DIAS_HABILES, DIAS_TRANSCURRIDOS, DIAS_RESTANTES


def crear_header():
    """Header del dashboard con info de días hábiles."""
    return html.Div([
        html.H4('Avance Preventa', className='header-title'),
        html.Div([
            html.Span('Viernes, 13 de febrero de 2026', className='header-date'),
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
    ], className='header-section')
