## gemini.py
import os
import requests
from app.rag_model import RAGModel
import pandas as pd
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not set in environment variables.")
    # Don't raise an error here, we'll handle it in the functions

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1/models/"
    "gemini-1.5-flash:generateContent?key={key}"
).format(key=GEMINI_API_KEY)

headers = {
    "Content-Type": "application/json"
}

def ask_gemini(question: str, user_id: str, conversation_id: str, context: str = None) -> str:
    """Ask Gemini a question with optional context"""
    if not GEMINI_API_KEY:
        logger.error("Cannot call Gemini API: API key not set")
        return "I'm sorry, but I can't process your request because the Gemini API key is not configured. Please contact the administrator."
    
    try:
        prompt = question
        if context:
            prompt = f"Context information:\n{context}\n\nUser question: {question}"
        
        logger.info(f"Sending request to Gemini API with prompt length: {len(prompt)}")
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"User ({user_id}) in conversation ({conversation_id}) asks: {prompt}"}
                    ]
                }
            ]
        }
        
        response = requests.post(GEMINI_URL, headers=headers, json=payload)
        
        # Log the response status and headers for debugging
        logger.info(f"Gemini API response status: {response.status_code}")
        logger.info(f"Gemini API response headers: {response.headers}")
        
        if response.status_code != 200:
            logger.error(f"Gemini API error: {response.text}")
            return f"I encountered an error when processing your request. Status code: {response.status_code}. Please try again later or contact support."
        
        data = response.json()
        
        try:
            return data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format from Gemini API: {e}")
            logger.error(f"Response data: {data}")
            return "I received an unexpected response format. Please try again or contact support."
            
    except Exception as e:
        logger.error(f"Error in ask_gemini: {str(e)}")
        logger.error(traceback.format_exc())
        return "I encountered an error while processing your request. Please try again later."

def ask_gemini_with_csv_data(question: str, user_id: str, conversation_id: str, 
                             df: pd.DataFrame, file_id: str = None) -> str:
    """Ask Gemini a question with context from CSV data using RAG"""
    try:
        # Use local embeddings by default
        embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'local')
        embedding_model = os.getenv('LOCAL_MODEL', 'all-MiniLM-L6-v2')

        # Only use external providers if explicitly configured
        if embedding_provider == "together" and os.getenv('TOGETHER_API_KEY'):
            embedding_model = os.getenv('TOGETHER_MODEL', 'togethercomputer/m2-bert-80M-8k-retrieval')
        elif embedding_provider == "huggingface" and os.getenv('HUGGINGFACE_API_KEY'):
            embedding_model = os.getenv('HUGGINGFACE_MODEL', 'sentence-transformers/all-mpnet-base-v2')
        elif embedding_provider == "openai" and os.getenv('OPENAI_API_KEY'):
            embedding_model = "text-embedding-3-small"
        else:
            # Fall back to local if the requested provider isn't available
            embedding_provider = "local"
            embedding_model = os.getenv('LOCAL_MODEL', 'all-MiniLM-L6-v2')
        
        # Initialize RAG model with selected provider
        logger.info(f"Using {embedding_provider} embeddings with model {embedding_model}")
        rag = RAGModel(embedding_provider=embedding_provider, embedding_model=embedding_model)
        
        # Get context using FAISS-based retrieval
        logger.info(f"Getting context for question: {question}")
        context, _ = rag.get_context_for_query(df, question, file_id=file_id)
        
        logger.info("Sending query with context to Gemini")
        logger.info(f"Context length: {len(context)}")
        
        # Check if Gemini API key is set
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not set, cannot proceed with query")
            return "I'm sorry, but I can't process your request because the Gemini API key is not configured. Please contact the administrator."
        
        return ask_gemini(question, user_id, conversation_id, context)
    
    except Exception as e:
        logger.error(f"Error in ask_gemini_with_csv_data: {str(e)}")
        logger.error(traceback.format_exc())
        return f"I encountered an error while processing your request: {str(e)}. Please try again later."
