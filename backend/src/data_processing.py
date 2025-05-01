# src/data_processing.py
import pandas as pd

def load_and_clean_data(file_path):
    """Load and clean the logistics data"""
    df = pd.read_csv(
        file_path,
        sep=';',
        encoding='latin-1',
        names=[
            'RECPTCL_FID',
            'MAILITM_FID',
            'EVENT_TYPE_NM',
            'date',
            'établissement_postal',
            'EVENT_TYPE_CD',
            'next_établissement_postal'
        ],
        skiprows=1
    )
    
    # Data cleaning
    df['MAILITM_FID'] = df['MAILITM_FID'].str.strip()
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
    df['établissement_postal'] = df['établissement_postal'].fillna('Unknown')
    
    # Sort by package ID and date
    df = df.sort_values(['MAILITM_FID', 'date'])
    
    return df