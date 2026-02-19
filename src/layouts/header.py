"""Componente header con título, fecha y días."""
from datetime import date

from dash import html
from config import DIAS_HABILES, DIAS_TRANSCURRIDOS, DIAS_RESTANTES

_DIAS_SEMANA = [
    'lunes', 'martes', 'miércoles', 'jueves',
    'viernes', 'sábado', 'domingo',
]
_MESES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]


def _fecha_header():
    """Retorna la fecha formateada en español sin depender de locale."""
    hoy = date.today()
    dia_semana = _DIAS_SEMANA[hoy.weekday()]
    mes = _MESES[hoy.month - 1]
    return f'{dia_semana}, {hoy.day} de {mes} de {hoy.year}'.capitalize()


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
