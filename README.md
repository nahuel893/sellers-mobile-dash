# Avance Preventa - Mobile Dashboard

Dashboard mobile-first para preventistas. Muestra el avance de ventas vs cupo por grupo de marca, con porcentajes en **tendencia** (proyeccion a fin de mes).

## Preview

<p align="center">
  <img src="docs/screenshot_mobile.png" alt="Dashboard mobile" width="300">
</p>

## Stack

- **Dash** + Plotly (gauges)
- **dash-bootstrap-components** (layout responsive)
- **Pandas** (procesamiento de datos)
- **PostgreSQL** capa Gold (Data Warehouse - Medallion Architecture)

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Abrir `http://localhost:8050` en el navegador.

## Estructura

```
├── app.py              # App principal Dash
├── config.py           # Configuracion (marcas, colores, dias)
├── mock_data.py        # Datos mock para desarrollo
├── requirements.txt    # Dependencias
└── assets/
    └── styles.css      # Estilos mobile-first
```
