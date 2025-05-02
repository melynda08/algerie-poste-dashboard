from flask import Blueprint, request, jsonify, g, current_app, send_from_directory
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AppUser, Conversation, UserQueryHistory
from datetime import datetime
import uuid
import pandas as pd
import plotly.express as px
import base64
import os
from .auth import generate_token, verify_user_credentials, login_required, get_authenticated_user
from .history import save_to_history
from .gemini import ask_gemini, ask_gemini_with_csv_data
from .csv_processor import save_uploaded_csv, get_csv_data, get_all_user_csvs, get_csv_as_string
from .data_loader import get_event_data_from_csv, search_logistics_data, get_csv_metadata
from .visualization import VisualizationGenerator
from app.rag_model import RAGModel

# Import from config properly
from app.config import get_config

main = Blueprint('main', __name__)

# Define these constants here instead of importing them
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
EMBEDDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'embeddings')

# Get csv_data_cache from csv_processor
from app.csv_processor import csv_data_cache

@main.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    env_status = {
        "GEMINI_API_KEY": "Set" if os.getenv('GEMINI_API_KEY') else "Not set",
        "OPENAI_API_KEY": "Set" if os.getenv('OPENAI_API_KEY') else "Not set",
        "TOGETHER_API_KEY": "Set" if os.getenv('TOGETHER_API_KEY') else "Not set",
        "HUGGINGFACE_API_KEY": "Set" if os.getenv('HUGGINGFACE_API_KEY') else "Not set",
    }
    
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "environment": env_status
    })

@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password required"}), 400

    user = verify_user_credentials(data['email'], data['password'])
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(str(user['user_id']))
    return jsonify({
        "token": token,
        "user_id": str(user['user_id']),
        "role": user['role'],
        "expires_in": "24 hours"
    })

@main.route('/start_conversation', methods=['POST'])
@login_required
def start_conversation():
    db: Session = next(get_db())
    user_id = get_authenticated_user()
    # Create a new conversation for authenticated user
    conv = Conversation(user_id=user_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return jsonify({
        "conversation_id": str(conv.conversation_id),
        "user_id": user_id
    })

@main.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    user_id = get_authenticated_user()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a CSV"}), 400
    
    try:
        file_id = save_uploaded_csv(file, user_id)
        # Get basic metadata about the CSV
        df = get_csv_data(file_id, user_id)
        metadata = {
            'file_id': file_id,
            'filename': file.filename,
            'rows': len(df),
            'columns': list(df.columns),
            'sample': df.head(5).to_dict(orient='records')
        }
        return jsonify({
            "message": "File uploaded successfully",
            "file_id": file_id,
            "metadata": metadata
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/csv_files', methods=['GET'])
@login_required
def list_csv_files():
    user_id = get_authenticated_user()
    files = get_all_user_csvs(user_id)
    return jsonify(files)

@main.route('/csv_metadata/<file_id>', methods=['GET'])
@login_required
def get_file_metadata(file_id):
    user_id = get_authenticated_user()
    try:
        metadata = get_csv_metadata(file_id, user_id)
        return jsonify(metadata)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add a new endpoint to list available local models
@main.route('/embedding_models', methods=['GET'])
@login_required
def list_embedding_models():
    """List available embedding models"""
    from app.local_embeddings import list_available_models
    
    # Get available local models
    local_models = list_available_models()
    
    # Get currently configured model
    from app.config import get_config
    current_provider = get_config("embedding_provider")
    current_model = get_config(f"{current_provider}_model")
    
    return jsonify({
        "current_provider": current_provider,
        "current_model": current_model,
        "local_models": local_models,
        "together_models": [
            "togethercomputer/m2-bert-80M-8k-retrieval",
            "togethercomputer/m2-bert-80M-32k-retrieval"
        ],
        "huggingface_models": [
            "sentence-transformers/all-mpnet-base-v2",
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/multi-qa-mpnet-base-dot-v1"
        ]
    })

@main.route('/embedding_provider', methods=['POST'])
@login_required
def set_embedding_provider():
    """Endpoint to configure which embedding provider to use"""
    data = request.get_json()
    provider = data.get('provider', 'local')  # local, openai, together, huggingface
    model = data.get('model')
    
    # Check if required API key is available
    if provider == 'openai' and not os.getenv('OPENAI_API_KEY'):
        return jsonify({"error": "OpenAI API key not set"}), 400
    elif provider == 'together' and not os.getenv('TOGETHER_API_KEY'):
        return jsonify({"error": "Together API key not set"}), 400
    elif provider == 'huggingface' and not os.getenv('HUGGINGFACE_API_KEY'):
        return jsonify({"error": "HuggingFace API key not set"}), 400
    
    # Store preference in environment variables
    os.environ['EMBEDDING_PROVIDER'] = provider
    if model:
        if provider == 'openai':
            os.environ['OPENAI_MODEL'] = model
        elif provider == 'together':
            os.environ['TOGETHER_MODEL'] = model
        elif provider == 'huggingface':
            os.environ['HUGGINGFACE_MODEL'] = model
        else:
            os.environ['LOCAL_MODEL'] = model
    
    return jsonify({
        "message": f"Embedding provider set to {provider}",
        "model": model or "default"
    })

@main.route('/chat', methods=['POST'])
@login_required
def chat():
    db: Session = next(get_db())
    data = request.get_json()
    question = data.get('question')
    file_id = data.get('file_id')  # CSV file ID
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    if not file_id:
        return jsonify({"error": "File ID is required"}), 400

    user_id = get_authenticated_user()
    conversation_id = data.get('conversation_id')

    # create conversation if missing
    if not conversation_id:
        conv = Conversation(user_id=user_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = str(conv.conversation_id)

    try:
        # Get CSV data
        df = get_csv_data(file_id, user_id)
        
        # Get embedding preferences from environment or request
        embedding_provider = data.get('embedding_provider') or os.getenv('EMBEDDING_PROVIDER', 'local')
        embedding_model = None
        
        if embedding_provider == 'openai':
            embedding_model = os.getenv('OPENAI_MODEL', 'text-embedding-3-small')
        elif embedding_provider == 'together':
            embedding_model = os.getenv('TOGETHER_MODEL', 'togethercomputer/m2-bert-80M-8k-retrieval')
        elif embedding_provider == 'huggingface':
            embedding_model = os.getenv('HUGGINGFACE_MODEL', 'sentence-transformers/all-mpnet-base-v2')
        else:
            embedding_model = os.getenv('LOCAL_MODEL', 'all-MiniLM-L6-v2')
        
        # Check if Gemini API key is set
        if not os.getenv('GEMINI_API_KEY'):
            return jsonify({
                "error": "GEMINI_API_KEY not set in environment variables",
                "response": "I'm sorry, but I can't process your request because the Gemini API key is not configured. Please contact the administrator.",
                "conversation_id": conversation_id,
                "embedding_provider": embedding_provider
            }), 500
        
        # Use RAG model with configured provider
        response = ask_gemini_with_csv_data(question, user_id, conversation_id, df, file_id)
        
        # Save chat history
        save_to_history(db, user_id, conversation_id, question, response, file_id)
        
        return jsonify({
            "response": response,
            "conversation_id": conversation_id,
            "embedding_provider": embedding_provider
        })
    except FileNotFoundError:
        return jsonify({"error": "CSV file not found"}), 404
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(error_traceback)
        return jsonify({
            "error": str(e),
            "traceback": error_traceback if current_app.debug else "Enable debug mode to see traceback",
            "response": f"An error occurred: {str(e)}. Please try again later.",
            "conversation_id": conversation_id
        }), 500

@main.route('/visualize', methods=['POST'])
@login_required
def visualize():
    data = request.json
    file_id = data.get('file_id')
    visualization_prompt = data.get('prompt', '')
    
    if not file_id:
        return jsonify({"error": "File ID is required"}), 400
    
    user_id = get_authenticated_user()
    
    try:
        # Get CSV data
        df = get_csv_data(file_id, user_id)
        
        # If there's a specific visualization prompt, use it
        if visualization_prompt:
            viz_generator = VisualizationGenerator(df)
            result = viz_generator.generate_visualization(visualization_prompt)
            
            if 'error' in result:
                return jsonify({"error": result['error']}), 400
                
            return jsonify({
                "image": result["image"],
                "chart_type": result["chart_type"],
                "title": result["title"],
                "conversation_id": data.get('conversation_id', str(uuid.uuid4()))
            })
        
        # Default visualization if no specific prompt
        # Check if required columns exist
        required_cols = ['origin_facility', 'destination_facility', 'status']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            # If columns are missing, try to use whatever columns are available
            if len(df.columns) >= 3:
                # Use first three columns for visualization
                path_cols = list(df.columns[:3])
                values_col = df.columns[0] if len(df.columns) > 0 else None
            else:
                return jsonify({"error": f"CSV is missing required columns: {missing_cols}"}), 400
        else:
            path_cols = ['origin_facility', 'status', 'destination_facility']
            values_col = 'status'
        
        # Clean data: drop rows where all path columns are null
        df = df.dropna(subset=path_cols, how='all')
        # Fill missing with 'Unknown'
        for col in path_cols:
            df[col] = df[col].fillna('Unknown')
        
        # Create count column if values column doesn't exist
        if values_col not in df.columns:
            df['count'] = 1
            values_col = 'count'
        
        fig = px.sunburst(
            df,
            path=path_cols,
            values=values_col,
            title="Data Visualization"
        )
        
        img_bytes = fig.to_image(format="png")
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return jsonify({
            "image": f"data:image/png;base64,{img_b64}",
            "conversation_id": data.get('conversation_id', str(uuid.uuid4()))
        })
    except FileNotFoundError:
        return jsonify({"error": "CSV file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/conversations/<user_id>', methods=['GET'])
@login_required
def get_user_conversations(user_id):
    db: Session = next(get_db())
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.started_at.desc()).all()

    return jsonify([
        {
            "conversation_id": str(c.conversation_id),
            "started_at": c.started_at.isoformat()
        } for c in conversations
    ])

@main.route('/history/<user_id>', methods=['GET'])
@login_required
def get_user_history(user_id):
    db: Session = next(get_db())
    limit = int(request.args.get('limit', 20))

    history = db.query(UserQueryHistory).filter(
        UserQueryHistory.user_id == user_id
    ).order_by(UserQueryHistory.timestamp.desc()).limit(limit).all()

    return jsonify([
        {
            "question": h.question,
            "response": h.response,
            "timestamp": h.timestamp.isoformat(),
            "conversation_id": str(h.conversation_id),
            "file_id": h.file_id
        } for h in history
    ])

@main.route('/search_csv', methods=['POST'])
@login_required
def search_csv():
    data = request.get_json()
    file_id = data.get('file_id')
    query = data.get('query')
    
    if not file_id or not query:
        return jsonify({"error": "File ID and query are required"}), 400
    
    user_id = get_authenticated_user()
    
    try:
        results = search_logistics_data(file_id, user_id, query)
        return jsonify({
            "results": results.head(100).to_dict(orient='records'),
            "total_matches": len(results)
        })
    except FileNotFoundError:
        return jsonify({"error": "CSV file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/reindex', methods=['POST'])
@login_required
def reindex_file():
    """Force reindex a file with specified embedding provider"""
    data = request.get_json()
    file_id = data.get('file_id')
    provider = data.get('provider', 'local')
    model = data.get('model')
    
    if not file_id:
        return jsonify({"error": "File ID is required"}), 400
    
    user_id = get_authenticated_user()
    
    try:
        # Get CSV data
        df = get_csv_data(file_id, user_id)
        
        # Set up model name based on provider
        if not model:
            if provider == 'openai':
                model = 'text-embedding-3-small'
            elif provider == 'together':
                model = 'togethercomputer/m2-bert-80M-8k-retrieval'
            elif provider == 'huggingface':
                model = 'sentence-transformers/all-mpnet-base-v2'
            else:
                model = 'all-MiniLM-L6-v2'
        
        # Initialize RAG model with selected provider
        rag = RAGModel(embedding_provider=provider, embedding_model=model)
        
        # Force rebuild index
        success = rag.index_dataframe(df, file_id=file_id, force_rebuild=True)
        
        if success:
            return jsonify({
                "message": f"Successfully reindexed file {file_id} with {provider} embeddings",
                "embedding_provider": provider,
                "embedding_model": model
            })
        else:
            return jsonify({"error": "Failed to reindex file"}), 500
        
    except FileNotFoundError:
        return jsonify({"error": "CSV file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/delete_csv/<file_id>', methods=['DELETE'])
@login_required
def delete_csv(file_id):
    user_id = get_authenticated_user()
    
    try:
        # Get the file path
        user_dir = os.path.join(UPLOAD_FOLDER, user_id)
        file_found = False
        file_path = None
        
        for filename in os.listdir(user_dir):
            if filename.startswith(f"{file_id}_"):
                file_path = os.path.join(user_dir, filename)
                file_found = True
                break
        
        if not file_found:
            return jsonify({"error": "File not found"}), 404
        
        # Remove from cache if present
        if file_id in csv_data_cache:
            del csv_data_cache[file_id]
        
        # Delete the file
        os.remove(file_path)
        
        # Delete embeddings directory if it exists
        embeddings_dir = os.path.join(EMBEDDINGS_DIR, file_id)
        if os.path.exists(embeddings_dir):
            import shutil
            shutil.rmtree(embeddings_dir)
        
        return jsonify({"message": "File deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/conversation_messages/<conversation_id>', methods=['GET'])
@login_required
def get_conversation_messages(conversation_id):
    """Get all messages for a specific conversation"""
    db: Session = next(get_db())
    user_id = get_authenticated_user()
    
    try:
        # Verify the conversation belongs to the user
        conversation = db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
        
        # Get all messages for this conversation
        messages = db.query(UserQueryHistory).filter(
            UserQueryHistory.conversation_id == conversation_id
        ).order_by(UserQueryHistory.timestamp.asc()).all()
        
        return jsonify([{
            "question": msg.question,
            "response": msg.response,
            "timestamp": msg.timestamp.isoformat(),
            "file_id": msg.file_id
        } for msg in messages])
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
