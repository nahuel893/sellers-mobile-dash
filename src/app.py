"""
Inicialización de la app Dash y ensamblaje de componentes.
"""
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from src.data.data_loader import get_dataframe
from src.layouts.header import crear_header
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
    suppress_callback_exceptions=True,
)
app.title = "Avance Preventa"

# ============================================================
# Layout — shell con routing
# ============================================================
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    crear_header(),
    html.Div(id='page-content'),
], fluid=True, className='app-container')

# ============================================================
# Callbacks
# ============================================================
register_callbacks(DF)

# ============================================================
# Health check (Flask route, no Dash overhead)
# ============================================================
@app.server.route('/health')
def health():
    return 'ok'
