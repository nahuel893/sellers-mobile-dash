"""
Dashboard Avance Preventa - Mobile First
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

from src.data.mock_data import get_mock_dataframe
from src.services.ventas_service import get_supervisores
from src.layouts.header import crear_header
from src.layouts.filters import crear_filtros
from src.callbacks.dashboard_callbacks import register_callbacks

# ============================================================
# Datos
# ============================================================
DF = get_mock_dataframe()

# ============================================================
# App
# ============================================================
app = dash.Dash(
    __name__,
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
    crear_filtros(get_supervisores(DF)),
    html.Div(id='dashboard-content'),
], fluid=True, className='app-container')

# ============================================================
# Callbacks
# ============================================================
register_callbacks(DF)

# ============================================================
# Run
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
