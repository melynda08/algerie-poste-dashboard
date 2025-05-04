from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import csv
import pandas as pd
import uuid
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'csv'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Store processing status
processing_jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_csv(file_path, output_path, options=None):
    """
    Preprocess CSV file with configurable options
    """
    if options is None:
        options = {}
    
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Apply preprocessing steps based on options
        if options.get('remove_duplicates', True):
            df = df.drop_duplicates()
            
        if options.get('fill_nulls', True):
            df = df.fillna(options.get('null_value', 0))
            
        if options.get('normalize', False):
            for col in df.select_dtypes(include=['float64', 'int64']).columns:
                df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        
        # Save the processed file
        df.to_csv(output_path, index=False)
        return True, "Processing completed successfully"
    except Exception as e:
        return False, str(e)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        base_filename = os.path.splitext(filename)[0]
        unique_filename = f"{base_filename}_{unique_id}.csv"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Create processing job
        job_id = unique_id
        processing_jobs[job_id] = {
            'id': job_id,
            'original_filename': filename,
            'filename': unique_filename,
            'status': 'uploaded',
            'created_at': time.time(),
            'file_path': file_path,
            'message': 'File uploaded successfully'
        }
        
        return jsonify({
            'job_id': job_id,
            'filename': filename,
            'status': 'uploaded',
            'message': 'File uploaded successfully'
        }), 201
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/preview/<job_id>', methods=['GET'])
def preview_file(job_id):
    if job_id not in processing_jobs:
        return jsonify({'error': 'File not found'}), 404
    
    file_path = processing_jobs[job_id]['file_path']
    try:
        # Read a few rows for preview
        df = pd.read_csv(file_path, nrows=5)
        preview_data = df.to_dict(orient='records')
        columns = list(df.columns)
        
        return jsonify({
            'columns': columns,
            'data': preview_data
        })
    except Exception as e:
        return jsonify({'error': f'Error generating preview: {str(e)}'}), 500

@app.route('/api/process/<job_id>', methods=['POST'])
def process_file(job_id):
    if job_id not in processing_jobs:
        return jsonify({'error': 'File not found'}), 404
    
    # Get processing options from request
    options = request.json if request.is_json else {}
    
    job = processing_jobs[job_id]
    file_path = job['file_path']
    
    # Update job status
    job['status'] = 'processing'
    job['message'] = 'Processing in progress'
    job['options'] = options
    
    # Generate output path
    base_filename = os.path.splitext(job['filename'])[0]
    output_filename = f"{base_filename}_processed.csv"
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    
    # Process the file
    success, message = preprocess_csv(file_path, output_path, options)
    
    if success:
        job['status'] = 'completed'
        job['output_filename'] = output_filename
        job['output_path'] = output_path
        job['completed_at'] = time.time()
        job['message'] = message
    else:
        job['status'] = 'failed'
        job['message'] = message
    
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'message': job['message']
    })

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs_list = []
    for job_id, job in processing_jobs.items():
        jobs_list.append({
            'id': job_id,
            'original_filename': job['original_filename'],
            'status': job['status'],
            'created_at': job['created_at'],
            'message': job.get('message', '')
        })
    return jsonify(jobs_list)

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = processing_jobs[job_id]
    return jsonify({
        'id': job_id,
        'original_filename': job['original_filename'],
        'status': job['status'],
        'created_at': job['created_at'],
        'completed_at': job.get('completed_at'),
        'message': job.get('message', '')
    })

@app.route('/api/download/<job_id>', methods=['GET'])
def download_processed_file(job_id):
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = processing_jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Processing not completed yet'}), 400
    
    return send_from_directory(
        app.config['PROCESSED_FOLDER'], 
        job['output_filename'], 
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)