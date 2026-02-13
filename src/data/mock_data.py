"""
Mock data para desarrollo del dashboard.
Simula la estructura que vendrá de la capa Gold.
"""
import pandas as pd
from config import DIAS_HABILES, DIAS_TRANSCURRIDOS, DIAS_RESTANTES

# ============================================================
# Datos mock: cupos y ventas por vendedor / grupo de marca
# ============================================================

_datos = [
    # Supervisor BADIE
    # FACUNDO CACERES
    ('FACUNDO CACERES', 'BADIE', 'SALTA',          1769, 4713),
    ('FACUNDO CACERES', 'BADIE', 'HEINEKEN',          25,   46),
    ('FACUNDO CACERES', 'BADIE', 'IMPERIAL',           6,   16),
    ('FACUNDO CACERES', 'BADIE', 'MILLER',            13,   31),
    ('FACUNDO CACERES', 'BADIE', 'MULTICERVEZAS',     12,   57),
    ('FACUNDO CACERES', 'BADIE', 'IMPORTADAS',         0,    5),
    # PEREIRA ARMANDO
    ('PEREIRA ARMANDO', 'BADIE', 'SALTA',            812, 2210),
    ('PEREIRA ARMANDO', 'BADIE', 'HEINEKEN',          26,   68),
    ('PEREIRA ARMANDO', 'BADIE', 'IMPERIAL',          22,   47),
    ('PEREIRA ARMANDO', 'BADIE', 'MILLER',            18,   55),
    ('PEREIRA ARMANDO', 'BADIE', 'MULTICERVEZAS',     18,   42),
    ('PEREIRA ARMANDO', 'BADIE', 'IMPORTADAS',         0,   16),
    # EZEQUIEL CACHAGUA
    ('EZEQUIEL CACHAGUA', 'BADIE', 'SALTA',        1572, 3980),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'HEINEKEN',       14,   32),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'IMPERIAL',        4,   18),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'MILLER',          9,   25),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'MULTICERVEZAS',   5,   13),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'IMPORTADAS',      0,    8),
    # GILDA VELAZCO
    ('GILDA VELAZCO', 'BADIE', 'SALTA',            1435, 3950),
    ('GILDA VELAZCO', 'BADIE', 'HEINEKEN',           23,   64),
    ('GILDA VELAZCO', 'BADIE', 'IMPERIAL',           40,   94),
    ('GILDA VELAZCO', 'BADIE', 'MILLER',              8,   37),
    ('GILDA VELAZCO', 'BADIE', 'MULTICERVEZAS',      16,   85),
    ('GILDA VELAZCO', 'BADIE', 'IMPORTADAS',          0,    0),
    # PATRICIA CARRIZO
    ('PATRICIA CARRIZO', 'BADIE', 'SALTA',          912, 3000),
    ('PATRICIA CARRIZO', 'BADIE', 'HEINEKEN',         15,   39),
    ('PATRICIA CARRIZO', 'BADIE', 'IMPERIAL',          7,   18),
    ('PATRICIA CARRIZO', 'BADIE', 'MILLER',           10,   23),
    ('PATRICIA CARRIZO', 'BADIE', 'MULTICERVEZAS',    21,   52),
    ('PATRICIA CARRIZO', 'BADIE', 'IMPORTADAS',        0,   57),
    # MONICA GOMEZ
    ('MONICA GOMEZ', 'BADIE', 'SALTA',              475, 1305),
    ('MONICA GOMEZ', 'BADIE', 'HEINEKEN',             38,   86),
    ('MONICA GOMEZ', 'BADIE', 'IMPERIAL',             60,   89),
    ('MONICA GOMEZ', 'BADIE', 'MILLER',               40,   59),
    ('MONICA GOMEZ', 'BADIE', 'MULTICERVEZAS',        30,   57),
    ('MONICA GOMEZ', 'BADIE', 'IMPORTADAS',            0,    6),
    # DARIO LUPATY
    ('DARIO LUPATY', 'BADIE', 'SALTA',             1281, 3060),
    ('DARIO LUPATY', 'BADIE', 'HEINEKEN',             18,   75),
    ('DARIO LUPATY', 'BADIE', 'IMPERIAL',             21,   44),
    ('DARIO LUPATY', 'BADIE', 'MILLER',               17,   37),
    ('DARIO LUPATY', 'BADIE', 'MULTICERVEZAS',        25,   41),
    ('DARIO LUPATY', 'BADIE', 'IMPORTADAS',            0,    0),
    # RUIZ MARCELO
    ('RUIZ MARCELO', 'BADIE', 'SALTA',              942, 3350),
    ('RUIZ MARCELO', 'BADIE', 'HEINEKEN',             29,   73),
    ('RUIZ MARCELO', 'BADIE', 'IMPERIAL',             45,   72),
    ('RUIZ MARCELO', 'BADIE', 'MILLER',               34,   62),
    ('RUIZ MARCELO', 'BADIE', 'MULTICERVEZAS',        22,   41),
    ('RUIZ MARCELO', 'BADIE', 'IMPORTADAS',            4,   42),

    # Supervisor LOPEZ (otro supervisor de ejemplo)
    # CARLOS MENDEZ
    ('CARLOS MENDEZ', 'LOPEZ', 'SALTA',            2100, 4500),
    ('CARLOS MENDEZ', 'LOPEZ', 'HEINEKEN',           45,   80),
    ('CARLOS MENDEZ', 'LOPEZ', 'IMPERIAL',           30,   55),
    ('CARLOS MENDEZ', 'LOPEZ', 'MILLER',             22,   45),
    ('CARLOS MENDEZ', 'LOPEZ', 'MULTICERVEZAS',      18,   40),
    ('CARLOS MENDEZ', 'LOPEZ', 'IMPORTADAS',          5,   10),
    # MARIA FERNANDEZ
    ('MARIA FERNANDEZ', 'LOPEZ', 'SALTA',          1800, 3800),
    ('MARIA FERNANDEZ', 'LOPEZ', 'HEINEKEN',         32,   60),
    ('MARIA FERNANDEZ', 'LOPEZ', 'IMPERIAL',         28,   50),
    ('MARIA FERNANDEZ', 'LOPEZ', 'MILLER',           15,   35),
    ('MARIA FERNANDEZ', 'LOPEZ', 'MULTICERVEZAS',    20,   45),
    ('MARIA FERNANDEZ', 'LOPEZ', 'IMPORTADAS',        8,   15),
]


def get_mock_dataframe():
    """Retorna DataFrame con datos crudos de ventas y cupos."""
    df = pd.DataFrame(_datos, columns=[
        'vendedor', 'supervisor', 'grupo_marca', 'ventas', 'cupo'
    ])
    df['falta'] = df['cupo'] - df['ventas']
    df['tendencia'] = (df['ventas'] * DIAS_HABILES / DIAS_TRANSCURRIDOS).round(0)
    df['pct_tendencia'] = (
        (df['tendencia'] / df['cupo'].replace(0, float('nan'))) * 100
    ).fillna(0).round(0).astype(int)
    df['vta_diaria_necesaria'] = (
        df['falta'] / DIAS_RESTANTES
    ).round(1)
    return df
