"""
Inicialización de la app Dash y ensamblaje de componentes.
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

from src.data.data_loader import get_dataframe
from src.services.ventas_service import get_sucursales
from src.layouts.header import crear_header
from src.layouts.filters import crear_filtros
from src.callbacks.dashboard_callbacks import register_callbacks

# ============================================================
# Datos
# ============================================================
DF = get_dataframe()

# ============================================================
# App
# ============================================================
app = dash.Dash(
    __name__,
    assets_folder='../assets',
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1"},
    ],
)
app.title = "Avance Preventa"

# ============================================================
# Layout
# ============================================================
app.layout = dbc.Container([
    crear_header(),
    crear_filtros(get_sucursales(DF)),
    html.Div(id='dashboard-content'),
], fluid=True, className='app-container')

# ============================================================
# Callbacks
# ============================================================
register_callbacks(DF)
