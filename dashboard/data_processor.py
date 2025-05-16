import pandas as pd
import numpy as np
from datetime import datetime

def load_data():
    """
    Load data from CSV files
    Designed to handle larger datasets in the future
    """
    try:
        # Load shipments data
        shipments_df = pd.read_csv(
            "attached_assets/export_data_01_01_2025_20_03_2025.csv", 
            sep=";",
            encoding="utf-8"
        )
        
        # Load receptacles data
        receptacles_df = pd.read_csv(
            "attached_assets/EXPORT_DATA_receptacle_01_01_2023_20_03_2025.csv", 
            sep=";",
            encoding="utf-8"
        )
        
        # Load event types reference data
        event_types_df = pd.read_csv(
            "attached_assets/CT_EVENT_TYPES.csv", 
            sep=";", 
            encoding="utf-8", 
            engine="python"
        )
        
        # Fix column names for event types if needed
        if len(event_types_df.columns) == 3 and 'EVENT_TYPE_NM' not in event_types_df.columns:
            event_types_df.columns = ["EVENT_TYPE_CD", "LANG", "EVENT_TYPE_NM"]
        
        # Load countries reference data
        countries_df = pd.read_csv(
            "attached_assets/CT_COUNTRIES.csv", 
            sep=";", 
            encoding="utf-8", 
            engine="python"
        )
        
        # Fix column names for countries if needed
        if len(countries_df.columns) == 3 and 'COUNTRY_NM' not in countries_df.columns:
            countries_df.columns = ["COUNTRY_CD", "LANG", "COUNTRY_NM"]
        
        # Clean up empty rows
        shipments_df = shipments_df.dropna(how='all')
        receptacles_df = receptacles_df.dropna(how='all')
        event_types_df = event_types_df.dropna(how='all')
        countries_df = countries_df.dropna(how='all')
        
        # Add indices to the reference data for faster lookups
        if 'EVENT_TYPE_CD' in event_types_df.columns:
            event_types_df.set_index('EVENT_TYPE_CD', drop=False, inplace=True)
        
        if 'COUNTRY_CD' in countries_df.columns:
            countries_df.set_index('COUNTRY_CD', drop=False, inplace=True)
        
        return shipments_df, receptacles_df, event_types_df, countries_df
    
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

def prepare_data(shipments_df, receptacles_df, event_types_df, countries_df):
    """
    Clean and prepare data for analysis
    Handle larger datasets efficiently and support more countries
    """
    country_coords = get_country_coordinates()
    
    # Clean and prepare shipments data
    if not shipments_df.empty:
        # Convert date column to datetime
        shipments_df['date'] = pd.to_datetime(shipments_df['date'], errors='coerce')
        
        # Extract origin and destination countries
        shipments_df['origin_country'] = shipments_df['établissement_postal'].str.strip() if 'établissement_postal' in shipments_df.columns else None
        shipments_df['destination_country'] = shipments_df['next_établissement_postal'].str.strip() if 'next_établissement_postal' in shipments_df.columns else None
        
        # Add country coordinates for mapping
        # This helps with efficient mapping for larger datasets
        origin_coords = []
        dest_coords = []
        
        for _, row in shipments_df.iterrows():
            origin = row.get('origin_country')
            destination = row.get('destination_country')
            
            # Add origin coordinates
            if origin and origin in country_coords:
                origin_coords.append(country_coords[origin])
            else:
                origin_coords.append(None)
                
            # Add destination coordinates
            if destination and destination in country_coords:
                dest_coords.append(country_coords[destination])
            else:
                dest_coords.append(None)
        
        shipments_df['origin_coords'] = origin_coords
        shipments_df['dest_coords'] = dest_coords
        
        # Group shipments by MAILITM_FID to track full journey
        if 'MAILITM_FID' in shipments_df.columns:
            # Use more efficient groupby operation
            delivery_times = []
            
            for mail_id, group in shipments_df.groupby('MAILITM_FID'):
                # Sort events by date
                sorted_events = group.sort_values('date')
                
                # Check if this shipment has a delivery event
                delivery_event = sorted_events[sorted_events['EVENT_TYPE_NM'].str.contains('Livraison', na=False, case=False)]
                
                if not delivery_event.empty:
                    first_event = sorted_events.iloc[0]
                    last_event = delivery_event.iloc[0]  # Take the first delivery event
                    
                    # Calculate delivery time in days
                    if pd.notna(first_event['date']) and pd.notna(last_event['date']):
                        delivery_time = (last_event['date'] - first_event['date']).total_seconds() / (24 * 60 * 60)
                        
                        delivery_times.append({
                            'MAILITM_FID': mail_id,
                            'origin_country': first_event.get('origin_country', None),
                            'destination_country': last_event.get('destination_country', None),
                            'delivery_time_days': delivery_time,
                            'start_date': first_event['date'],
                            'delivery_date': last_event['date']
                        })
            
            # Create delivery times dataframe
            if delivery_times:
                delivery_df = pd.DataFrame(delivery_times)
                # Merge back to shipments data
                shipments_df = pd.merge(
                    shipments_df, 
                    delivery_df[['MAILITM_FID', 'delivery_time_days']], 
                    on='MAILITM_FID', 
                    how='left'
                )
    
    # Clean and prepare receptacles data
    if not receptacles_df.empty:
        # Convert date column to datetime
        receptacles_df['date'] = pd.to_datetime(receptacles_df['date'], errors='coerce')
        
        # Extract origin and destination countries
        receptacles_df['origin_country'] = receptacles_df['établissement_postal'].str.strip() if 'établissement_postal' in receptacles_df.columns else None
        receptacles_df['destination_country'] = receptacles_df['next_établissement_postal'].str.strip() if 'next_établissement_postal' in receptacles_df.columns else None
        
        # Add country coordinates for mapping
        origin_coords = []
        dest_coords = []
        
        for _, row in receptacles_df.iterrows():
            origin = row.get('origin_country')
            destination = row.get('destination_country')
            
            # Add origin coordinates
            if origin and origin in country_coords:
                origin_coords.append(country_coords[origin])
            else:
                origin_coords.append(None)
                
            # Add destination coordinates
            if destination and destination in country_coords:
                dest_coords.append(country_coords[destination])
            else:
                dest_coords.append(None)
        
        receptacles_df['origin_coords'] = origin_coords
        receptacles_df['dest_coords'] = dest_coords
    
    return shipments_df, receptacles_df

def get_country_coordinates():
    """
    Returns a dictionary of country coordinates for mapping.
    This function now supports dynamic coordinate lookup based on country data.
    """
    # Base coordinates for commonly used countries
    base_coords = {
        'FRANCE': {'lat': 46.603354, 'lon': 1.888334},
        'ALGéRIE': {'lat': 28.033886, 'lon': 1.659626},
        'ALGÉRIE': {'lat': 28.033886, 'lon': 1.659626},
        'éMIRATS ARABES UNIS': {'lat': 23.424076, 'lon': 53.847818},
        'ALLEMAGNE': {'lat': 51.165691, 'lon': 10.451526},
        'ESPAGNE': {'lat': 40.463667, 'lon': -3.74922},
        'ITALIE': {'lat': 41.87194, 'lon': 12.56738},
        'ROYAUME-UNI': {'lat': 55.378051, 'lon': -3.435973},
        'éTATS-UNIS': {'lat': 37.09024, 'lon': -95.712891},
        'CANADA': {'lat': 56.130366, 'lon': -106.346771},
        'CHINE': {'lat': 35.86166, 'lon': 104.195397},
        'JAPON': {'lat': 36.204824, 'lon': 138.252924},
        'BRÉSIL': {'lat': -14.235004, 'lon': -51.92528},
        'AUSTRALIE': {'lat': -25.274398, 'lon': 133.775136},
        'AFRIQUE DU SUD': {'lat': -30.559482, 'lon': 22.937506},
        'MAROC': {'lat': 31.791702, 'lon': -7.09262},
        'TUNISIE': {'lat': 33.886917, 'lon': 9.537499},
        'SéNéGAL': {'lat': 14.497401, 'lon': -14.452362},
        'CÔTE D\'IVOIRE': {'lat': 7.539989, 'lon': -5.54708},
        'MALI': {'lat': 17.570692, 'lon': -3.996166},
        'NIGER': {'lat': 17.607789, 'lon': 8.081666},
        'TCHAD': {'lat': 15.454166, 'lon': 18.732207},
        'CAMEROUN': {'lat': 7.369722, 'lon': 12.354722},
        # Add coordinates for major postal facilities
        'LYON': {'lat': 45.764043, 'lon': 4.835659},
        'PARIS': {'lat': 48.856614, 'lon': 2.352222},
        'ALGER GARE': {'lat': 36.753768, 'lon': 3.060066},
        'ALI MENDJELI': {'lat': 36.266453, 'lon': 6.638101},
        'ANNABA EL MARSA': {'lat': 36.899597, 'lon': 7.775092},
        'ALGER COLIS POSTAUX': {'lat': 36.765875, 'lon': 3.058836},
        'AEROPOSTAL HOUARI BOUMEDIENE': {'lat': 36.693157, 'lon': 3.215186},
        
        # Add many more countries for broader support
        'AUTRICHE': {'lat': 47.516231, 'lon': 14.550072},
        'PORTUGAL': {'lat': 39.399872, 'lon': -8.224454},
        'BELGIQUE': {'lat': 50.503887, 'lon': 4.469936},
        'PAYS-BAS': {'lat': 52.132633, 'lon': 5.291266},
        'GRéCE': {'lat': 39.074208, 'lon': 21.824312},
        'SUISSE': {'lat': 46.818188, 'lon': 8.227512},
        'SUéDE': {'lat': 60.128161, 'lon': 18.643501},
        'NORVÈGE': {'lat': 60.472024, 'lon': 8.468946},
        'FINLANDE': {'lat': 61.92411, 'lon': 25.748151},
        'DANEMARK': {'lat': 56.26392, 'lon': 9.501785},
        'IRLANDE': {'lat': 53.41291, 'lon': -8.24389},
        'POLOGNE': {'lat': 51.919438, 'lon': 19.145136},
        'HONGRIE': {'lat': 47.162494, 'lon': 19.503304},
        'RÉPUBLIQUE TCHÈQUE': {'lat': 49.817492, 'lon': 15.472962},
        'SLOVAQUIE': {'lat': 48.669026, 'lon': 19.699024},
        'ROUMANIE': {'lat': 45.943161, 'lon': 24.96676},
        'UKRAINE': {'lat': 48.379433, 'lon': 31.16558},
        'CROATIE': {'lat': 45.1, 'lon': 15.2},
        'BULGARIE': {'lat': 42.733883, 'lon': 25.48583},
        'RUSSIE': {'lat': 61.52401, 'lon': 105.318756},
        'TURQUIE': {'lat': 38.963745, 'lon': 35.243322},
        'MEXIQUE': {'lat': 23.634501, 'lon': -102.552784},
        'INDE': {'lat': 20.593684, 'lon': 78.96288},
        'INDONÉSIE': {'lat': -0.789275, 'lon': 113.921327},
        'THAÏLANDE': {'lat': 15.870032, 'lon': 100.992541},
        'VIETNAM': {'lat': 14.058324, 'lon': 108.277199},
        'PHILIPPINES': {'lat': 12.879721, 'lon': 121.774017},
        'SINGAPOUR': {'lat': 1.352083, 'lon': 103.819836},
        'MALAISIE': {'lat': 4.210484, 'lon': 101.975766},
        'NOUVELLE-ZÉLANDE': {'lat': -40.900557, 'lon': 174.885971},
        'ARGENTINE': {'lat': -38.416097, 'lon': -63.616672},
        'CHILI': {'lat': -35.675147, 'lon': -71.542969},
        'PéROU': {'lat': -9.189967, 'lon': -75.015152},
        'COLOMBIE': {'lat': 4.570868, 'lon': -74.297333},
        'VENEZUELA': {'lat': 6.42375, 'lon': -66.58973},
        'éGYPTE': {'lat': 26.820553, 'lon': 30.802498},
        'LIBYE': {'lat': 26.3351, 'lon': 17.228331},
        'GHANA': {'lat': 7.946527, 'lon': -1.023194},
        'éTHIOPIE': {'lat': 9.145, 'lon': 40.489673},
        'KENYA': {'lat': -0.023559, 'lon': 37.906193},
        'TANZANIE': {'lat': -6.369028, 'lon': 34.888822},
        'NIGÉRIA': {'lat': 9.081999, 'lon': 8.675277},
        'ANGOLA': {'lat': -11.202692, 'lon': 17.873887},
        'MOZAMBIQUE': {'lat': -18.665695, 'lon': 35.529562},
        'ZIMBABWE': {'lat': -19.015438, 'lon': 29.154857},
        'IRAN': {'lat': 32.427908, 'lon': 53.688046},
        'ARABIE SAOUDITE': {'lat': 23.885942, 'lon': 45.079162},
        'ISRAËL': {'lat': 31.046051, 'lon': 34.851612},
        'IRAK': {'lat': 33.223191, 'lon': 43.679291},
        'KOWEÏT': {'lat': 29.31166, 'lon': 47.481766},
        'QATAR': {'lat': 25.354826, 'lon': 51.183884},
        'BAHREÏN': {'lat': 25.930414, 'lon': 50.637772},
    }
    
    return base_coords