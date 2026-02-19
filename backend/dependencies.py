"""FastAPI dependencies."""
import pandas as pd

from data.data_loader import get_dataframe


def get_df() -> pd.DataFrame:
    """Provee el DataFrame cacheado por día.

    get_dataframe() maneja la invalidación diaria del cache internamente.
    Usar como dependency permite override en tests con mock data.
    """
    return get_dataframe()
