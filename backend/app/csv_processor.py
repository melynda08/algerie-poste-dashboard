import os
import pandas as pd
import io
from typing import Dict, List, Optional, Union
import uuid
from werkzeug.utils import secure_filename

# Directory for storing uploaded CSV files
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dictionary to store loaded dataframes in memory
csv_data_cache: Dict[str, pd.DataFrame] = {}

def save_uploaded_csv(file, user_id: str) -> str:
    """Save an uploaded CSV file and return its unique identifier"""
    filename = secure_filename(file.filename)
    # Create unique ID for this upload
    file_id = str(uuid.uuid4())
    # Create user directory if it doesn't exist
    user_dir = os.path.join(UPLOAD_FOLDER, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Save file with unique ID prefix
    file_path = os.path.join(user_dir, f"{file_id}_{filename}")
    file.save(file_path)
    
    # Load and cache the dataframe
    try:
        df = pd.read_csv(file_path)
        csv_data_cache[file_id] = df
        return file_id
    except Exception as e:
        # If there's an error loading the CSV, delete the file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise ValueError(f"Error processing CSV file: {str(e)}")

def get_csv_data(file_id: str, user_id: Optional[str] = None) -> pd.DataFrame:
    """Get dataframe from cache or load it from file"""
    # Check if dataframe is in cache
    if file_id in csv_data_cache:
        return csv_data_cache[file_id]
    
    # If not in cache, try to load from file
    if user_id:
        user_dir = os.path.join(UPLOAD_FOLDER, user_id)
        # Find the file with the matching ID prefix
        for filename in os.listdir(user_dir):
            if filename.startswith(f"{file_id}_"):
                file_path = os.path.join(user_dir, filename)
                df = pd.read_csv(file_path)
                csv_data_cache[file_id] = df
                return df
    
    raise FileNotFoundError(f"CSV file with ID {file_id} not found")

def get_all_user_csvs(user_id: str) -> List[Dict[str, str]]:
    """Get list of all CSV files uploaded by a user"""
    user_dir = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_dir):
        return []
    
    csv_files = []
    for filename in os.listdir(user_dir):
        if filename.endswith('.csv'):
            file_id = filename.split('_')[0]
            original_name = '_'.join(filename.split('_')[1:])
            csv_files.append({
                'file_id': file_id,
                'filename': original_name,
                'upload_path': os.path.join(user_dir, filename)
            })
    
    return csv_files

def stream_csv_chunks(file_path: str, chunk_size: int = 10000):
    """Stream a CSV file in chunks to handle large files"""
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        yield chunk

def get_csv_as_string(file_id: str, user_id: str, max_rows: int = 100) -> str:
    """Get CSV data as a formatted string for context"""
    df = get_csv_data(file_id, user_id)
    # Limit to max_rows to avoid context length issues
    if len(df) > max_rows:
        df = df.head(max_rows)
    return df.to_string(index=False)

def search_csv_data(file_id: str, user_id: str, query: str) -> pd.DataFrame:
    """Search CSV data for relevant information based on query"""
    df = get_csv_data(file_id, user_id)
    
    # Simple search implementation - can be enhanced with more sophisticated techniques
    results = pd.DataFrame()
    
    # Search in all string columns
    for col in df.select_dtypes(include=['object']).columns:
        matches = df[df[col].astype(str).str.contains(query, case=False, na=False)]
        results = pd.concat([results, matches])
    
    # Remove duplicates
    results = results.drop_duplicates()
    
    return results
