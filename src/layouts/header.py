"""Componente header con título, fecha y días."""
import locale
from datetime import date

from dash import html
from config import DIAS_HABILES, DIAS_TRANSCURRIDOS, DIAS_RESTANTES

# Intentar locale español para formato de fecha
try:
    locale.setlocale(locale.LC_TIME, 'es_AR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Argentina')
    except locale.Error:
        pass  # Queda en inglés si no hay locale español


def _fecha_header():
    """Retorna la fecha formateada para el header."""
    hoy = date.today()
    return hoy.strftime('%A, %d de %B de %Y').capitalize()


def crear_header():
    """Header del dashboard con info de días hábiles."""
    return html.Div([
        html.Div(id='top'),
        html.H4('Avance Preventa', className='header-title'),
        html.Div([
            html.Span(_fecha_header(), className='header-date'),
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
