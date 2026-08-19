
from sqlalchemy import exc
import streamlit as st
import pandas as pd

from datetime import datetime, timedelta



TIME_FORMAT = "%Y-%m-%d"

# Configuraciones globales predeterminadas de tu app
DEFAULT_COLUMN_CONFIG = {
    "link_yt": st.column_config.LinkColumn(
        label="YouTube",
        display_text="Ver video",
        help="Abrir video en YouTube"
    ),
    "tempo": st.column_config.NumberColumn(
        label="Tempo",
        format="%d BPM"
    )
}

def show_normalized_df(df: pd.DataFrame, extra_config: dict = None, **kwargs):
    """
    Renderiza un dataframe en Streamlit aplicando automáticamente
    las configuraciones de enlaces, formatos y estilos base.
    """
    config_final = DEFAULT_COLUMN_CONFIG.copy()
    if extra_config:
        config_final.update(extra_config)
        
    # Parámetros por defecto para todas las tablas del dashboard
    defaults = {
        "use_container_width": True,
        "hide_index": True,
        "column_config": config_final
    }
    defaults.update(kwargs)
    
    return st.dataframe(df, **defaults)


def get_next_sunday_date(date:str=None)->str:
    """
    Calculates the next sunday for a given date
    date in format YYYY/MM/DD

    default = today
    """
    if date:
        today_obj = datetime.strptime(date, TIME_FORMAT)

    else:
        today_obj = datetime.now()


    sunday_num = 7 #7th day of the week is sundar
    today_weekday = today_obj.isoweekday() #in ISO, monday is 1 NOT 0

    days_diff = sunday_num - today_weekday 
    next_sunday_date = today_obj + timedelta(days=days_diff)
    return next_sunday_date.strftime(TIME_FORMAT)

if __name__ == "__main__":
    print(get_next_sunday_date())
    print(get_next_sunday_date("2026-04-24"))