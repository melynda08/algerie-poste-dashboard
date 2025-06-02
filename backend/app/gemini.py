import os
import requests
import re
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
        if context:
            # Extract potential event codes from the question
            potential_codes = re.findall(r'\b\d+\b', question)
            
            # Check if there's a direct lookup result in the context
            has_direct_lookup = "DIRECT LOOKUP RESULT:" in context
            direct_lookup_info = ""
            
            if has_direct_lookup:
                # Extract the direct lookup information
                direct_lookup_pattern = r"DIRECT LOOKUP RESULT:\s*(.*?)(?:\n\n|\Z)"
                direct_lookup_match = re.search(direct_lookup_pattern, context, re.DOTALL)
                if direct_lookup_match:
                    direct_lookup_info = direct_lookup_match.group(1).strip()
            
            # Remove context numbering from the context
            # Replace patterns like "CONTEXT 1:", "CONTEXT 2:", etc. with just a separator
            cleaned_context = re.sub(r'CONTEXT \d+:\s*', '---\n', context)
            
            # Create the direct lookup section if it exists
            direct_lookup_section = ""
            if direct_lookup_info:
                direct_lookup_section = "IMPORTANT DIRECT LOOKUP RESULT:\n" + direct_lookup_info + "\n\n"
            
            # Create the event codes section
            event_codes_section = ""
            if potential_codes:
                event_codes_section = "IMPORTANT: If the user is asking about event codes " + ", ".join(potential_codes) + ", first check if these exact codes appear in the DIRECT LOOKUP RESULT section before checking the rest of the context."
            else:
                event_codes_section = "IMPORTANT: If the user is asking about specific event codes, first check if these exact codes appear in the DIRECT LOOKUP RESULT section before checking the rest of the context."
            
            # Enhanced structured prompt with clear instructions - avoiding f-string with backslashes
            prompt = """You are a helpful data analysis assistant specializing in postal and shipping data. Your task is to provide accurate, insightful answers based on the provided context information.

USER QUESTION: """ + question + """

""" + direct_lookup_section + """CONTEXT INFORMATION:
""" + cleaned_context + """

INSTRUCTIONS:
1. Base your answer ONLY on the information provided in the context above.
2. ALWAYS prioritize information from the DIRECT LOOKUP RESULT section if present.
3. If the user is asking about a specific event code that appears in the DIRECT LOOKUP RESULT, use that information as your primary source.
4. If a specific event code is mentioned in the question but not found in the context, explicitly state: "The provided text does not contain information about event code X."
5. IMPORTANT: If you see "Event Code X:" in the DIRECT LOOKUP RESULT section, this IS valid information about that event code.
6. Cite specific data points from the context to support your answer.
7. Organize your response in a clear, structured format.
8. DO NOT make up information that isn't supported by the context.
9. DO NOT refer to "Context 1", "Context 2", etc. in your response. Present information as a unified answer without referencing the source contexts by number.

""" + event_codes_section + """

Your response:"""
        else:
            prompt = question
        
        logger.info(f"Sending request to Gemini API with prompt length: {len(prompt)}")
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Reduced temperature for more factual responses
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 2048
            }
        }
        
        response = requests.post(GEMINI_URL, headers=headers, json=payload)
        
        # Log the response status and headers for debugging
        logger.info(f"Gemini API response status: {response.status_code}")
        
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
        
        # Direct lookup for event codes in the question
        event_code_match = re.search(r'\b(\d+)\b', question)
        direct_lookup_info = None
        
        if event_code_match and 'EVENT_TYPE_CD' in df.columns:
            code = event_code_match.group(1)
            # Direct lookup in dataframe
            matching_rows = df[df['EVENT_TYPE_CD'].astype(str) == code]
            if not matching_rows.empty:
                event_name = "Unknown"
                if 'EVENT_TYPE_NM' in matching_rows.columns:
                    event_names = matching_rows['EVENT_TYPE_NM'].dropna().unique()
                    if len(event_names) > 0:
                        event_name = event_names[0]
                
                # Format direct lookup result more prominently
                direct_lookup_info = f"DIRECT LOOKUP RESULT:\nEvent Code {code}: {event_name}\nNumber of records: {len(matching_rows)}\n"
                
                # Add additional information if available
                if 'EVENT_TYPE_DESC' in matching_rows.columns:
                    descriptions = matching_rows['EVENT_TYPE_DESC'].dropna().unique()
                    if len(descriptions) > 0:
                        direct_lookup_info += f"Description: {descriptions[0]}\n"
                
                logger.info(f"Found direct lookup for event code {code}: {event_name}")
        
        # Get context using FAISS-based retrieval with increased top_k
        logger.info(f"Getting context for question: {question}")
        context, results = rag.get_context_for_query(df, question, file_id=file_id, top_k=10)
        
        # Add direct lookup info to context if available
        if direct_lookup_info and direct_lookup_info not in context:
            # Place direct lookup at the beginning of the context for emphasis
            enhanced_context = direct_lookup_info + "\n\n" + context
        else:
            enhanced_context = context
        
        logger.info("Sending query with enhanced context to Gemini")
        logger.info(f"Enhanced context length: {len(enhanced_context)}")
        
        # Check if Gemini API key is set
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not set, cannot proceed with query")
            return "I'm sorry, but I can't process your request because the Gemini API key is not configured. Please contact the administrator."
        
        # Add debugging information if enabled
        debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        if debug_mode:
            logger.info("Debug mode enabled, returning context and response")
            gemini_response = ask_gemini(question, user_id, conversation_id, enhanced_context)
            return f"[DEBUG MODE - CONTEXT]\n{enhanced_context}\n\n[GEMINI RESPONSE]\n{gemini_response}"
        else:
            return ask_gemini(question, user_id, conversation_id, enhanced_context)
    
    except Exception as e:
        logger.error(f"Error in ask_gemini_with_csv_data: {str(e)}")
        logger.error(traceback.format_exc())
        return f"I encountered an error while processing your request: {str(e)}. Please try again later."

def get_event_code_info(df: pd.DataFrame, event_code: str) -> str:
    """
    Get information about a specific event code directly from the dataframe
    
    Args:
        df: The DataFrame to search
        event_code: The event code to look up
        
    Returns:
        Information about the event code
    """
    try:
        if 'EVENT_TYPE_CD' not in df.columns:
            return f"No event code information available in the dataset."
        
        # Find rows with this event code
        matching_rows = df[df['EVENT_TYPE_CD'].astype(str) == event_code]
        
        if matching_rows.empty:
            return f"Event code {event_code} not found in the dataset."
        
        # Get event type name if available
        event_name = "Unknown"
        if 'EVENT_TYPE_NM' in matching_rows.columns:
            event_names = matching_rows['EVENT_TYPE_NM'].dropna().unique()
            if len(event_names) > 0:
                event_name = event_names[0]
        
        # Create a summary
        summary = f"Event Code {event_code}: {event_name}\n"
        summary += f"Number of records: {len(matching_rows)}\n"
        
        # Add example records
        if len(matching_rows) > 0:
            summary += "\nExample record fields:\n"
            example = matching_rows.iloc[0]
            for col, val in example.items():
                if pd.notna(val) and col not in ['EVENT_TYPE_CD', 'EVENT_TYPE_NM']:
                    summary += f"- {col}: {val}\n"
        
        return summary
    
    except Exception as e:
        logger.error(f"Error getting event code info: {str(e)}")
        return f"Error retrieving information for event code {event_code}."