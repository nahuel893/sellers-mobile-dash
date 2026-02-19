"""
Mock data para desarrollo del dashboard.
Simula la estructura que vendrá de la capa Gold.
"""
import pandas as pd

# ============================================================
# Datos mock: cupos y ventas por vendedor / grupo de marca
# ============================================================

_datos = [
    # ---- CERVEZAS ----
    # Supervisor BADIE
    # FACUNDO CACERES
    ('FACUNDO CACERES', 'BADIE', 'CERVEZAS', 'SALTA',          1769, 4713),
    ('FACUNDO CACERES', 'BADIE', 'CERVEZAS', 'HEINEKEN',          25,   46),
    ('FACUNDO CACERES', 'BADIE', 'CERVEZAS', 'IMPERIAL',           6,   16),
    ('FACUNDO CACERES', 'BADIE', 'CERVEZAS', 'MILLER',            13,   31),
    ('FACUNDO CACERES', 'BADIE', 'CERVEZAS', 'MULTICERVEZAS',     12,   57),
    ('FACUNDO CACERES', 'BADIE', 'CERVEZAS', 'IMPORTADAS',         0,    5),
    # PEREIRA ARMANDO
    ('PEREIRA ARMANDO', 'BADIE', 'CERVEZAS', 'SALTA',            812, 2210),
    ('PEREIRA ARMANDO', 'BADIE', 'CERVEZAS', 'HEINEKEN',          26,   68),
    ('PEREIRA ARMANDO', 'BADIE', 'CERVEZAS', 'IMPERIAL',          22,   47),
    ('PEREIRA ARMANDO', 'BADIE', 'CERVEZAS', 'MILLER',            18,   55),
    ('PEREIRA ARMANDO', 'BADIE', 'CERVEZAS', 'MULTICERVEZAS',     18,   42),
    ('PEREIRA ARMANDO', 'BADIE', 'CERVEZAS', 'IMPORTADAS',         0,   16),
    # EZEQUIEL CACHAGUA
    ('EZEQUIEL CACHAGUA', 'BADIE', 'CERVEZAS', 'SALTA',        1572, 3980),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'CERVEZAS', 'HEINEKEN',       14,   32),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'CERVEZAS', 'IMPERIAL',        4,   18),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'CERVEZAS', 'MILLER',          9,   25),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'CERVEZAS', 'MULTICERVEZAS',   5,   13),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'CERVEZAS', 'IMPORTADAS',      0,    8),
    # GILDA VELAZCO
    ('GILDA VELAZCO', 'BADIE', 'CERVEZAS', 'SALTA',            1435, 3950),
    ('GILDA VELAZCO', 'BADIE', 'CERVEZAS', 'HEINEKEN',           23,   64),
    ('GILDA VELAZCO', 'BADIE', 'CERVEZAS', 'IMPERIAL',           40,   94),
    ('GILDA VELAZCO', 'BADIE', 'CERVEZAS', 'MILLER',              8,   37),
    ('GILDA VELAZCO', 'BADIE', 'CERVEZAS', 'MULTICERVEZAS',      16,   85),
    ('GILDA VELAZCO', 'BADIE', 'CERVEZAS', 'IMPORTADAS',          0,    0),
    # PATRICIA CARRIZO
    ('PATRICIA CARRIZO', 'BADIE', 'CERVEZAS', 'SALTA',          912, 3000),
    ('PATRICIA CARRIZO', 'BADIE', 'CERVEZAS', 'HEINEKEN',         15,   39),
    ('PATRICIA CARRIZO', 'BADIE', 'CERVEZAS', 'IMPERIAL',          7,   18),
    ('PATRICIA CARRIZO', 'BADIE', 'CERVEZAS', 'MILLER',           10,   23),
    ('PATRICIA CARRIZO', 'BADIE', 'CERVEZAS', 'MULTICERVEZAS',    21,   52),
    ('PATRICIA CARRIZO', 'BADIE', 'CERVEZAS', 'IMPORTADAS',        0,   57),
    # MONICA GOMEZ
    ('MONICA GOMEZ', 'BADIE', 'CERVEZAS', 'SALTA',              475, 1305),
    ('MONICA GOMEZ', 'BADIE', 'CERVEZAS', 'HEINEKEN',             38,   86),
    ('MONICA GOMEZ', 'BADIE', 'CERVEZAS', 'IMPERIAL',             60,   89),
    ('MONICA GOMEZ', 'BADIE', 'CERVEZAS', 'MILLER',               40,   59),
    ('MONICA GOMEZ', 'BADIE', 'CERVEZAS', 'MULTICERVEZAS',        30,   57),
    ('MONICA GOMEZ', 'BADIE', 'CERVEZAS', 'IMPORTADAS',            0,    6),
    # DARIO LUPATY
    ('DARIO LUPATY', 'BADIE', 'CERVEZAS', 'SALTA',             1281, 3060),
    ('DARIO LUPATY', 'BADIE', 'CERVEZAS', 'HEINEKEN',             18,   75),
    ('DARIO LUPATY', 'BADIE', 'CERVEZAS', 'IMPERIAL',             21,   44),
    ('DARIO LUPATY', 'BADIE', 'CERVEZAS', 'MILLER',               17,   37),
    ('DARIO LUPATY', 'BADIE', 'CERVEZAS', 'MULTICERVEZAS',        25,   41),
    ('DARIO LUPATY', 'BADIE', 'CERVEZAS', 'IMPORTADAS',            0,    0),
    # RUIZ MARCELO
    ('RUIZ MARCELO', 'BADIE', 'CERVEZAS', 'SALTA',              942, 3350),
    ('RUIZ MARCELO', 'BADIE', 'CERVEZAS', 'HEINEKEN',             29,   73),
    ('RUIZ MARCELO', 'BADIE', 'CERVEZAS', 'IMPERIAL',             45,   72),
    ('RUIZ MARCELO', 'BADIE', 'CERVEZAS', 'MILLER',               34,   62),
    ('RUIZ MARCELO', 'BADIE', 'CERVEZAS', 'MULTICERVEZAS',        22,   41),
    ('RUIZ MARCELO', 'BADIE', 'CERVEZAS', 'IMPORTADAS',            4,   42),

    # Supervisor LOPEZ
    # CARLOS MENDEZ
    ('CARLOS MENDEZ', 'LOPEZ', 'CERVEZAS', 'SALTA',            2100, 4500),
    ('CARLOS MENDEZ', 'LOPEZ', 'CERVEZAS', 'HEINEKEN',           45,   80),
    ('CARLOS MENDEZ', 'LOPEZ', 'CERVEZAS', 'IMPERIAL',           30,   55),
    ('CARLOS MENDEZ', 'LOPEZ', 'CERVEZAS', 'MILLER',             22,   45),
    ('CARLOS MENDEZ', 'LOPEZ', 'CERVEZAS', 'MULTICERVEZAS',      18,   40),
    ('CARLOS MENDEZ', 'LOPEZ', 'CERVEZAS', 'IMPORTADAS',          5,   10),
    # MARIA FERNANDEZ
    ('MARIA FERNANDEZ', 'LOPEZ', 'CERVEZAS', 'SALTA',          1800, 3800),
    ('MARIA FERNANDEZ', 'LOPEZ', 'CERVEZAS', 'HEINEKEN',         32,   60),
    ('MARIA FERNANDEZ', 'LOPEZ', 'CERVEZAS', 'IMPERIAL',         28,   50),
    ('MARIA FERNANDEZ', 'LOPEZ', 'CERVEZAS', 'MILLER',           15,   35),
    ('MARIA FERNANDEZ', 'LOPEZ', 'CERVEZAS', 'MULTICERVEZAS',    20,   45),
    ('MARIA FERNANDEZ', 'LOPEZ', 'CERVEZAS', 'IMPORTADAS',        8,   15),

    # ---- MULTICCU (solo totales, sin desglose por marca) ----
    ('FACUNDO CACERES',   'BADIE', 'MULTICCU', None, 320, 850),
    ('PEREIRA ARMANDO',   'BADIE', 'MULTICCU', None, 180, 520),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'MULTICCU', None, 250, 680),
    ('GILDA VELAZCO',     'BADIE', 'MULTICCU', None, 290, 750),
    ('PATRICIA CARRIZO',  'BADIE', 'MULTICCU', None, 150, 430),
    ('MONICA GOMEZ',      'BADIE', 'MULTICCU', None, 210, 580),
    ('DARIO LUPATY',      'BADIE', 'MULTICCU', None, 270, 640),
    ('RUIZ MARCELO',      'BADIE', 'MULTICCU', None, 195, 560),
    ('CARLOS MENDEZ',     'LOPEZ', 'MULTICCU', None, 380, 900),
    ('MARIA FERNANDEZ',   'LOPEZ', 'MULTICCU', None, 310, 720),

    # ---- AGUAS DANONE (solo totales, sin desglose por marca) ----
    ('FACUNDO CACERES',   'BADIE', 'AGUAS_DANONE', None, 145, 400),
    ('PEREIRA ARMANDO',   'BADIE', 'AGUAS_DANONE', None,  85, 250),
    ('EZEQUIEL CACHAGUA', 'BADIE', 'AGUAS_DANONE', None, 120, 320),
    ('GILDA VELAZCO',     'BADIE', 'AGUAS_DANONE', None, 160, 380),
    ('PATRICIA CARRIZO',  'BADIE', 'AGUAS_DANONE', None,  70, 210),
    ('MONICA GOMEZ',      'BADIE', 'AGUAS_DANONE', None, 100, 290),
    ('DARIO LUPATY',      'BADIE', 'AGUAS_DANONE', None, 130, 310),
    ('RUIZ MARCELO',      'BADIE', 'AGUAS_DANONE', None,  90, 270),
    ('CARLOS MENDEZ',     'LOPEZ', 'AGUAS_DANONE', None, 200, 450),
    ('MARIA FERNANDEZ',   'LOPEZ', 'AGUAS_DANONE', None, 170, 380),
]


def get_mock_dataframe():
    """Retorna DataFrame con datos crudos de ventas y cupos."""
    df = pd.DataFrame(_datos, columns=[
        'vendedor', 'supervisor', 'categoria', 'grupo_marca', 'ventas', 'cupo'
    ])
    df['sucursal'] = '1 - CASA CENTRAL'
    from data.data_loader import _calcular_columnas_derivadas
    return _calcular_columnas_derivadas(df)
