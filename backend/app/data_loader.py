import pandas as pd
from sqlalchemy import text
from app.database import get_db

def get_event_data_as_string():
    with get_db() as db:
        # Get receptacle events
        receptacle_events = db.execute(text("""
            SELECT event_timestamp, facility, next_facility, event_details
            FROM receptacle_event
            ORDER BY event_timestamp DESC
            LIMIT 50
        """)).fetchall()

        # Get mail item events
        mail_events = db.execute(text("""
            SELECT event_timestamp, facility, next_facility, event_details
            FROM mail_item_event
            ORDER BY event_timestamp DESC
            LIMIT 50
        """)).fetchall()

    # Combine results
    combined = [dict(row) for row in receptacle_events + mail_events]
    
    # Create DataFrame
    df = pd.DataFrame(combined)
    return df.to_string(index=False)

def get_event_data_as_df():
    return pd.DataFrame(columns=[
        "event_timestamp", "facility", "next_facility", "event_details"
    ])  # Actual implementation same as above but returns DataFrame