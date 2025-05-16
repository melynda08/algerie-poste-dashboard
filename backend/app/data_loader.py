import pandas as pd
from app.csv_processor import get_csv_data, get_csv_as_string, search_csv_data
from typing import Optional, List, Dict

def get_event_data_from_csv(file_id: str, user_id: str) -> str:
    """Get event data from CSV file as a formatted string"""
    return get_csv_as_string(file_id, user_id)

def search_logistics_data(file_id: str, user_id: str, query: str) -> pd.DataFrame:
    """Search logistics data in CSV file"""
    return search_csv_data(file_id, user_id, query)

def get_event_data_as_df(file_id: str, user_id: str) -> pd.DataFrame:
    """Get event data from CSV file as a DataFrame"""
    return get_csv_data(file_id, user_id)

def get_csv_metadata(file_id: str, user_id: str) -> Dict:
    """Get metadata about a CSV file"""
    df = get_csv_data(file_id, user_id)
    return {
        'columns': list(df.columns),
        'row_count': len(df),
        'sample': df.head(5).to_dict(orient='records')
    }
