import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union, Literal, Set
import os
import json
import pickle
import faiss
from tqdm import tqdm
import requests
from sentence_transformers import SentenceTransformer
import torch
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for storing embeddings and indices
EMBEDDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'embeddings')
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

class RAGModel:
    """
    Enhanced RAG (Retrieval Augmented Generation) model using FAISS and embeddings
    Supports multiple embedding providers:
    - Sentence Transformers (local)
    - OpenAI
    - Together AI
    - Hugging Face
    """
    
    def __init__(self, 
                 embedding_provider: str = "local",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG model
        
        Args:
            embedding_provider: Which embedding provider to use: "local", "openai", "together", "huggingface"
            embedding_model: The name/ID of the embedding model to use
        """
        self.embedding_provider = embedding_provider.lower()
        self.embedding_model_name = embedding_model
        
        # Get API keys from environment
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.together_api_key = os.getenv('TOGETHER_API_KEY')
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        
        # Set default embedding dimensions based on common models
        self.embedding_dims = {
            "openai": 1536,  # For text-embedding-3-small
            "together": 1024,  # For e5-large-v2
            "huggingface": 768,  # For most base models
            "local": 384,  # For all-MiniLM-L6-v2
        }
        
        # Initialize the appropriate embedding method
        self._setup_embedding_provider()
        
        self.index = None
        self.documents = []
        self.chunk_size = 100  # Default chunk size for processing large datasets
        
        # Store original dataframe for hybrid search
        self.original_df = None
        
        # Store metadata about the dataset for better retrieval
        self.metadata = {
            "event_codes": set(),
            "event_types": {},
            "postal_establishments": set(),
            "mail_items": set()
        }
    
    def _setup_embedding_provider(self):
        """Setup the selected embedding provider"""
        
        # Default to local if requested provider not available
        if self.embedding_provider == "openai" and not self.openai_api_key:
            logger.warning("OpenAI API key not found. Falling back to local embeddings.")
            self.embedding_provider = "local"
            
        elif self.embedding_provider == "together" and not self.together_api_key:
            logger.warning("Together AI API key not found. Falling back to local embeddings.")
            self.embedding_provider = "local"
            
        elif self.embedding_provider == "huggingface" and not self.huggingface_api_key:
            logger.warning("HuggingFace API key not found. Falling back to local embeddings.")
            self.embedding_provider = "local"
        
        # Initialize the proper embedding method based on provider
        if self.embedding_provider == "local":
            self._init_local_model()
        else:
            # For API-based providers, just set the embedding dimension
            self.embedding_dim = self.embedding_dims.get(self.embedding_provider, 768)
            logger.info(f"Using {self.embedding_provider} embeddings with model {self.embedding_model_name}")
        
    def _init_local_model(self):
        """Initialize local embedding model"""
        try:
            self.model = SentenceTransformer(self.embedding_model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded local Sentence Transformer model: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            # Fall back to a basic model if the requested one fails
            try:
                self.embedding_model_name = "all-MiniLM-L6-v2"  # Default fallback model
                self.model = SentenceTransformer(self.embedding_model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                logger.info("Loaded fallback Sentence Transformer model")
            except Exception as e2:
                logger.error(f"Error loading fallback model: {str(e2)}")
                self.model = None
                self.embedding_dim = 384  # Default dimension for all-MiniLM-L6-v2
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embeddings from OpenAI API"""
        try:
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": "text-embedding-3-small"
                }
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error getting OpenAI embedding: {str(e)}")
            # Fall back to local model if OpenAI fails
            if hasattr(self, 'model') and self.model:
                return self.model.encode(text).tolist()
            return [0] * self.embedding_dim  # Return zero vector if all else fails
    
    def _get_together_embedding(self, text: str) -> List[float]:
        """Get embeddings from Together AI API"""
        try:
            response = requests.post(
                "https://api.together.xyz/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.together_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": self.embedding_model_name or "togethercomputer/m2-bert-80M-8k-retrieval"
                }
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error getting Together AI embedding: {str(e)}")
            # Fall back to local model if Together AI fails
            if hasattr(self, 'model') and self.model:
                return self.model.encode(text).tolist()
            return [0] * self.embedding_dim  # Return zero vector if all else fails
    
    def _get_huggingface_embedding(self, text: str) -> List[float]:
        """Get embeddings from HuggingFace Inference API"""
        try:
            api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.embedding_model_name}"
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {self.huggingface_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": text,
                    "options": {"wait_for_model": True}
                }
            )
            response.raise_for_status()
            embeddings = response.json()
            # Huggingface returns a list of lists for each token/sentence
            # When using sentence transformers, we take the first embedding which is the sentence embedding
            if isinstance(embeddings, list) and isinstance(embeddings[0], list):
                return embeddings[0]
            return embeddings
        except Exception as e:
            logger.error(f"Error getting HuggingFace embedding: {str(e)}")
            # Fall back to local model if HuggingFace fails
            if hasattr(self, 'model') and self.model:
                return self.model.encode(text).tolist()
            return [0] * self.embedding_dim  # Return zero vector if all else fails
    
    def _get_embedding_for_text(self, text: str) -> List[float]:
        """Get embedding for a single text string based on selected provider"""
        if self.embedding_provider == "openai":
            return self._get_openai_embedding(text)
        elif self.embedding_provider == "together":
            return self._get_together_embedding(text)
        elif self.embedding_provider == "huggingface":
            return self._get_huggingface_embedding(text)
        else:  # local
            if hasattr(self, 'model') and self.model:
                return self.model.encode(text).tolist()
            return [0] * self.embedding_dim
    
    def _get_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Get embeddings for a batch of texts from selected provider"""
        embeddings = []
        
        # Process in batches
        for i in tqdm(range(0, len(texts), batch_size), desc="Getting embeddings"):
            batch_texts = texts[i:i+batch_size]
            
            try:
                if self.embedding_provider == "local" and hasattr(self, 'model') and self.model:
                    # Local SentenceTransformers - process batch at once
                    batch_embeddings = self.model.encode(batch_texts).tolist()
                    embeddings.extend(batch_embeddings)
                else:
                    # For API providers - process one at a time to handle errors gracefully
                    batch_embeddings = []
                    for text in batch_texts:
                        embedding = self._get_embedding_for_text(text)
                        batch_embeddings.append(embedding)
                    embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Error getting batch embeddings: {str(e)}")
                # Return zero vectors if batch fails
                embeddings.extend([[0] * self.embedding_dim for _ in range(len(batch_texts))])
        
        return np.array(embeddings, dtype=np.float32)
    
    def _extract_dataset_metadata(self, df: pd.DataFrame):
        """
        Extract and store metadata about the dataset for better retrieval
        
        Args:
            df: The DataFrame to extract metadata from
        """
        # Store original dataframe for hybrid search
        self.original_df = df.copy()
        
        # Extract event codes and types
        if 'EVENT_TYPE_CD' in df.columns:
            self.metadata["event_codes"] = set(df['EVENT_TYPE_CD'].dropna().astype(str).unique())
            
            # Create mapping of event codes to event types
            event_type_mapping = {}
            for _, row in df.dropna(subset=['EVENT_TYPE_CD', 'EVENT_TYPE_NM']).iterrows():
                code = str(row['EVENT_TYPE_CD'])
                name = row['EVENT_TYPE_NM']
                if code and name and code not in event_type_mapping:
                    event_type_mapping[code] = name
            
            self.metadata["event_types"] = event_type_mapping
        
        # Extract postal establishments
        if 'établissement_postal' in df.columns:
            self.metadata["postal_establishments"] = set(df['établissement_postal'].dropna().unique())
        
        # Extract mail items
        if 'MAILITM_FID' in df.columns:
            self.metadata["mail_items"] = set(df['MAILITM_FID'].str.strip().dropna().unique())
        
        logger.info(f"Extracted metadata: {len(self.metadata['event_codes'])} event codes, "
                   f"{len(self.metadata['postal_establishments'])} postal establishments, "
                   f"{len(self.metadata['mail_items'])} mail items")
    
    def _preprocess_dataframe(self, df: pd.DataFrame, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Convert DataFrame to text documents with metadata using improved chunking strategy
        
        Args:
            df: The DataFrame to process
            max_rows: Maximum number of rows to process (for large datasets)
            
        Returns:
            List of dictionaries with text and metadata
        """
        # Extract dataset metadata first
        self._extract_dataset_metadata(df)
        
        documents = []
        df_sample = df.head(max_rows) if max_rows else df
        
        # 1. Create individual row documents (for specific item queries)
        for idx, row in df_sample.iterrows():
            # Convert row to string representation
            text_parts = []
            metadata = {"row_idx": idx}
            
            for col, val in row.items():
                if pd.notna(val):
                    text_parts.append(f"{col}: {val}")
                    metadata[col] = val
            
            # Join text parts with newlines for better context
            text = "\n".join(text_parts)
            documents.append({
                "text": text,
                "metadata": metadata,
                "doc_type": "row"
            })
        
        # 2. Create event code summary documents (for event code queries)
        if 'EVENT_TYPE_CD' in df.columns:
            event_code_groups = df.groupby('EVENT_TYPE_CD')
            
            for code, group in event_code_groups:
                # Get the event type name if available
                event_type_name = ""
                if 'EVENT_TYPE_NM' in group.columns:
                    event_names = group['EVENT_TYPE_NM'].dropna().unique()
                    if len(event_names) > 0:
                        event_type_name = event_names[0]
                
                # Create a summary document for this event code
                text_parts = [f"Event Code: {code}"]
                if event_type_name:
                    text_parts.append(f"Event Type Name: {event_type_name}")
                
                text_parts.append("\nExample records with this event code:")
                
                # Add example records (up to 3)
                for i, (_, row) in enumerate(group.head(3).iterrows()):
                    example_parts = []
                    for col, val in row.items():
                        if pd.notna(val) and col not in ['EVENT_TYPE_CD', 'EVENT_TYPE_NM']:
                            example_parts.append(f"{col}: {val}")
                    
                    text_parts.append(f"Example {i+1}: {' | '.join(example_parts)}")
                
                documents.append({
                    "text": "\n".join(text_parts),
                    "metadata": {
                        "event_code": code,
                        "event_type_name": event_type_name,
                        "count": len(group)
                    },
                    "doc_type": "event_code_summary"
                })
        
        # 3. Create postal establishment summary documents
        if 'établissement_postal' in df.columns:
            establishment_groups = df.groupby('établissement_postal')
            
            for establishment, group in establishment_groups:
                if pd.isna(establishment) or establishment == "":
                    continue
                    
                text_parts = [f"Postal Establishment: {establishment}"]
                text_parts.append(f"Number of records: {len(group)}")
                
                # Get event types at this establishment
                if 'EVENT_TYPE_CD' in group.columns and 'EVENT_TYPE_NM' in group.columns:
                    event_types = group[['EVENT_TYPE_CD', 'EVENT_TYPE_NM']].drop_duplicates()
                    text_parts.append("\nEvent types at this establishment:")
                    for _, event_row in event_types.iterrows():
                        if pd.notna(event_row['EVENT_TYPE_CD']) and pd.notna(event_row['EVENT_TYPE_NM']):
                            text_parts.append(f"- Code {event_row['EVENT_TYPE_CD']}: {event_row['EVENT_TYPE_NM']}")
                
                documents.append({
                    "text": "\n".join(text_parts),
                    "metadata": {
                        "establishment": establishment,
                        "count": len(group)
                    },
                    "doc_type": "establishment_summary"
                })
        
        # 4. Create dataset overview document
        overview_parts = ["Dataset Overview:"]
        overview_parts.append(f"Total records: {len(df)}")
        
        # Add event code summary
        if 'EVENT_TYPE_CD' in df.columns:
            event_counts = df['EVENT_TYPE_CD'].value_counts()
            overview_parts.append("\nEvent Code Distribution:")
            for code, count in event_counts.items():
                event_name = ""
                if code in self.metadata["event_types"]:
                    event_name = f" ({self.metadata['event_types'][str(code)]})"
                overview_parts.append(f"- Code {code}{event_name}: {count} records")
        
        # Add establishment summary
        if 'établissement_postal' in df.columns:
            establishment_counts = df['établissement_postal'].value_counts().head(5)
            overview_parts.append("\nTop Postal Establishments:")
            for establishment, count in establishment_counts.items():
                if pd.notna(establishment) and establishment != "":
                    overview_parts.append(f"- {establishment}: {count} records")
        
        # Add date range
        if 'date' in df.columns:
            try:
                min_date = pd.to_datetime(df['date']).min()
                max_date = pd.to_datetime(df['date']).max()
                overview_parts.append(f"\nDate Range: {min_date.date()} to {max_date.date()}")
            except:
                pass
        
        documents.append({
            "text": "\n".join(overview_parts),
            "metadata": {
                "record_count": len(df),
                "column_count": len(df.columns)
            },
            "doc_type": "dataset_overview"
        })
        
        logger.info(f"Created {len(documents)} documents from DataFrame")
        return documents
    
    def _chunk_dataframe(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """
        Split large DataFrame into chunks for processing
        
        Args:
            df: The DataFrame to chunk
            
        Returns:
            List of DataFrame chunks
        """
        if len(df) <= self.chunk_size:
            return [df]
        
        chunks = []
        for i in range(0, len(df), self.chunk_size):
            chunks.append(df.iloc[i:i+self.chunk_size])
        
        return chunks
    
    def index_dataframe(self, df: pd.DataFrame, file_id: str = None, force_rebuild: bool = False) -> bool:
        """
        Index DataFrame for retrieval with FAISS
        
        Args:
            df: DataFrame to index
            file_id: Optional ID to save/load embeddings and index
            force_rebuild: Force rebuild index even if cached version exists
        
        Returns:
            True if indexing was successful
        """
        # Check if we can load from cache
        if file_id and not force_rebuild:
            loaded = self._load_index(file_id)
            if loaded:
                logger.info(f"Loaded existing index for file {file_id}")
                return True
        
        # Process dataset in chunks if it's large
        if len(df) > self.chunk_size:
            logger.info(f"Processing large DataFrame with {len(df)} rows in chunks")
            chunks = self._chunk_dataframe(df)
            
            # Process each chunk
            all_documents = []
            all_embeddings = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                chunk_docs = self._preprocess_dataframe(chunk)
                all_documents.extend(chunk_docs)
                
                # Get embeddings for this chunk
                chunk_texts = [doc["text"] for doc in chunk_docs]
                chunk_embeddings = self._get_embeddings_batch(chunk_texts)
                all_embeddings.append(chunk_embeddings)
            
            # Combine all embeddings
            embeddings = np.vstack(all_embeddings)
            self.documents = all_documents
            
        else:
            # Small dataset - process all at once
            self.documents = self._preprocess_dataframe(df)
            texts = [doc["text"] for doc in self.documents]
            embeddings = self._get_embeddings_batch(texts)
        
        # Create FAISS index
        if len(embeddings) > 0:
            try:
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)
                
                # Create index - using IndexFlatIP for cosine similarity
                self.index = faiss.IndexFlatIP(self.embedding_dim)
                self.index.add(embeddings)
                
                logger.info(f"Created FAISS index with {len(self.documents)} documents")
                
                # Save index if file_id is provided
                if file_id:
                    self._save_index(file_id)
                
                return True
            except Exception as e:
                logger.error(f"Error creating FAISS index: {str(e)}")
                return False
        else:
            logger.error("No embeddings generated")
            return False
    
    def _save_index(self, file_id: str) -> bool:
        """
        Save FAISS index and document data to disk
        
        Args:
            file_id: ID of the file to use in naming
            
        Returns:
            True if save was successful
        """
        if not self.index or not self.documents:
            return False
            
        try:
            file_dir = os.path.join(EMBEDDINGS_DIR, file_id)
            os.makedirs(file_dir, exist_ok=True)
            
            # Save FAISS index
            index_path = os.path.join(file_dir, "index.faiss")
            faiss.write_index(self.index, index_path)
            
            # Save documents
            docs_path = os.path.join(file_dir, "documents.pkl")
            with open(docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
                
            # Save model info
            model_info = {
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name,
                "embedding_dim": self.embedding_dim,
                "document_count": len(self.documents)
            }
            info_path = os.path.join(file_dir, "info.json")
            with open(info_path, 'w') as f:
                json.dump(model_info, f)
                
            logger.info(f"Saved index and documents for file {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            return False
    
    def _load_index(self, file_id: str) -> bool:
        """
        Load FAISS index and document data from disk
        
        Args:
            file_id: ID of the file to load
            
        Returns:
            True if load was successful
        """
        file_dir = os.path.join(EMBEDDINGS_DIR, file_id)
        index_path = os.path.join(file_dir, "index.faiss")
        docs_path = os.path.join(file_dir, "documents.pkl")
        info_path = os.path.join(file_dir, "info.json")
        
        # Check if all files exist
        if not (os.path.exists(index_path) and os.path.exists(docs_path) and os.path.exists(info_path)):
            return False
            
        try:
            # Load model info first to check compatibility
            with open(info_path, 'r') as f:
                model_info = json.load(f)
            
            # Check if dimensions match current model
            # If different embedding model/provider was used, we need to rebuild
            if model_info.get("embedding_dim") != self.embedding_dim:
                logger.warning("Embedding dimension mismatch, rebuilding index")
                return False
                
            # Load index
            self.index = faiss.read_index(index_path)
            
            # Load documents
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
                
            return True
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return False
    
    def _detect_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect the intent of the query to improve retrieval
        
        Args:
            query: The user query
            
        Returns:
            Dictionary with detected intent information
        """
        query_lower = query.lower()
        intent = {
            "is_about_event_code": False,
            "is_about_event_type": False,
            "is_about_establishment": False,
            "is_about_mail_item": False,
            "is_overview_query": False,
            "mentioned_event_codes": set(),
            "mentioned_establishments": set(),
            "mentioned_mail_items": set()
        }
        
        # Extract all numbers from the query to catch potential event codes
        potential_codes = re.findall(r'\b\d+\b', query)
        
        # Check for event code/type intent
        if any(term in query_lower for term in ["event code", "event type", "code", "event"]):
            intent["is_about_event_type"] = True
            
            # Check for specific event codes
            for code in self.metadata["event_codes"]:
                code_str = str(code)
                if code_str in query or f"code {code_str}" in query_lower:
                    intent["is_about_event_code"] = True
                    intent["mentioned_event_codes"].add(code_str)
            
            # Also check all numbers in the query as potential event codes
            for code in potential_codes:
                if code in self.metadata["event_codes"]:
                    intent["is_about_event_code"] = True
                    intent["mentioned_event_codes"].add(code)
        
        # Even if not explicitly asking about event codes, check if numbers match event codes
        elif potential_codes:
            for code in potential_codes:
                if code in self.metadata["event_codes"]:
                    intent["is_about_event_code"] = True
                    intent["is_about_event_type"] = True
                    intent["mentioned_event_codes"].add(code)
        
        # Check for establishment intent
        if any(term in query_lower for term in ["establishment", "postal", "office", "bureau"]):
            intent["is_about_establishment"] = True
            
            # Check for specific establishments
            for establishment in self.metadata["postal_establishments"]:
                if establishment and str(establishment).lower() in query_lower:
                    intent["mentioned_establishments"].add(establishment)
        
        # Check for mail item intent
        if any(term in query_lower for term in ["mail item", "package", "tracking", "shipment", "item"]):
            intent["is_about_mail_item"] = True
            
            # Check for specific mail items (using regex to find alphanumeric IDs)
            mail_item_pattern = r'\b[A-Z0-9]{10,}\b'
            potential_ids = re.findall(mail_item_pattern, query)
            for id_value in potential_ids:
                if id_value in self.metadata["mail_items"]:
                    intent["mentioned_mail_items"].add(id_value)
        
        # Check for overview intent
        if any(term in query_lower for term in ["overview", "summary", "dataset", "data", "contain", "what is", "what's in"]):
            intent["is_overview_query"] = True
        
        return intent
    
    def _keyword_search(self, query: str, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search for specific query intents
        
        Args:
            query: The user query
            intent: The detected query intent
            
        Returns:
            List of relevant documents from keyword search
        """
        results = []
        
        # If no original dataframe, can't do keyword search
        if self.original_df is None:
            return results
        
        # Extract all numbers from the query to catch potential event codes
        potential_codes = re.findall(r'\b\d+\b', query)
        
        # For event code queries, find documents about those specific codes
        if intent["is_about_event_code"] and intent["mentioned_event_codes"]:
            for code in intent["mentioned_event_codes"]:
                # Find event code summary documents
                for doc in self.documents:
                    if doc.get("doc_type") == "event_code_summary" and str(doc["metadata"].get("event_code")) == code:
                        results.append({
                            'content': doc["text"],
                            'metadata': doc["metadata"],
                            'similarity': 1.0,  # High confidence for exact matches
                            'source': 'keyword'
                        })
                
                # If no summary document, find example rows with this code
                if not results:
                    for doc in self.documents:
                        if doc.get("doc_type") == "row" and str(doc["metadata"].get("EVENT_TYPE_CD")) == code:
                            results.append({
                                'content': doc["text"],
                                'metadata': doc["metadata"],
                                'similarity': 0.9,  # High confidence but not a summary
                                'source': 'keyword'
                            })
                            # Limit to a few examples
                            if len(results) >= 3:
                                break
        
        # Check for potential event codes in the query even if not explicitly asking about them
        elif potential_codes:
            for code in potential_codes:
                if code in self.metadata["event_codes"]:
                    # Find event code summary documents
                    for doc in self.documents:
                        if doc.get("doc_type") == "event_code_summary" and str(doc["metadata"].get("event_code")) == code:
                            results.append({
                                'content': doc["text"],
                                'metadata': doc["metadata"],
                                'similarity': 0.95,  # High confidence for exact matches
                                'source': 'keyword_number'
                            })
                    
                    # If no summary document, find example rows with this code
                    if not any(r.get('source') == 'keyword_number' for r in results):
                        for doc in self.documents:
                            if doc.get("doc_type") == "row" and str(doc["metadata"].get("EVENT_TYPE_CD")) == code:
                                results.append({
                                    'content': doc["text"],
                                    'metadata': doc["metadata"],
                                    'similarity': 0.85,  # High confidence but not a summary
                                    'source': 'keyword_number'
                                })
                                # Limit to a few examples
                                if len([r for r in results if r.get('source') == 'keyword_number']) >= 3:
                                    break
        
        # For mail item queries, find documents about those specific items
        elif intent["is_about_mail_item"] and intent["mentioned_mail_items"]:
            for item_id in intent["mentioned_mail_items"]:
                for doc in self.documents:
                    if doc.get("doc_type") == "row" and doc["metadata"].get("MAILITM_FID", "").strip() == item_id:
                        results.append({
                            'content': doc["text"],
                            'metadata': doc["metadata"],
                            'similarity': 1.0,  # High confidence for exact matches
                            'source': 'keyword'
                        })
        
        # For establishment queries, find documents about those specific establishments
        elif intent["is_about_establishment"] and intent["mentioned_establishments"]:
            for establishment in intent["mentioned_establishments"]:
                # Find establishment summary documents
                for doc in self.documents:
                    if doc.get("doc_type") == "establishment_summary" and doc["metadata"].get("establishment") == establishment:
                        results.append({
                            'content': doc["text"],
                            'metadata': doc["metadata"],
                            'similarity': 1.0,  # High confidence for exact matches
                            'source': 'keyword'
                        })
                
                # If no summary document, find example rows with this establishment
                if not results:
                    for doc in self.documents:
                        if doc.get("doc_type") == "row" and doc["metadata"].get("établissement_postal") == establishment:
                            results.append({
                                'content': doc["text"],
                                'metadata': doc["metadata"],
                                'similarity': 0.9,  # High confidence but not a summary
                                'source': 'keyword'
                            })
                            # Limit to a few examples
                            if len(results) >= 3:
                                break
        
        # For overview queries, find the dataset overview document
        elif intent["is_overview_query"]:
            for doc in self.documents:
                if doc.get("doc_type") == "dataset_overview":
                    results.append({
                        'content': doc["text"],
                        'metadata': doc["metadata"],
                        'similarity': 1.0,  # High confidence for exact match
                        'source': 'keyword'
                    })
                    break
        
        # For general event type queries without specific codes
        elif intent["is_about_event_type"] and not intent["mentioned_event_codes"]:
            # Get summaries for all event codes (up to a limit)
            event_summaries = []
            for doc in self.documents:
                if doc.get("doc_type") == "event_code_summary":
                    event_summaries.append({
                        'content': doc["text"],
                        'metadata': doc["metadata"],
                        'similarity': 0.95,  # High confidence for summaries
                        'source': 'keyword'
                    })
            
            # Sort by event code and take top N
            event_summaries.sort(key=lambda x: str(x['metadata'].get('event_code', '')))
            results.extend(event_summaries[:5])  # Limit to 5 event types
        
        return results
    
    def _direct_lookup_event_code(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Perform a direct lookup for event codes in the query
        
        Args:
            query: The user query
            
        Returns:
            Event code information if found, None otherwise
        """
        if self.original_df is None or 'EVENT_TYPE_CD' not in self.original_df.columns:
            return None
            
        # Extract all numbers from the query
        potential_codes = re.findall(r'\b\d+\b', query)
        
        for code in potential_codes:
            # Check if this code exists in our data
            matching_rows = self.original_df[self.original_df['EVENT_TYPE_CD'].astype(str) == code]
            
            if not matching_rows.empty:
                # Get the event type name if available
                event_name = None
                if 'EVENT_TYPE_NM' in matching_rows.columns:
                    event_names = matching_rows['EVENT_TYPE_NM'].dropna().unique()
                    if len(event_names) > 0:
                        event_name = event_names[0]
                
                return {
                    "event_code": code,
                    "event_name": event_name,
                    "count": len(matching_rows)
                }
        
        return None
    
    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context based on query using hybrid search
        
        Args:
            query: The user query
            top_k: Number of contexts to retrieve
        
        Returns:
            List of context documents with similarity scores
        """
        if not self.index or not self.documents:
            return []
        
        try:
            # Initialize results list
            results = []
            
            # 1. Try direct lookup for event codes first
            direct_lookup = self._direct_lookup_event_code(query)
            if direct_lookup:
                # Create a special document for this direct lookup
                direct_text = f"Event Code: {direct_lookup['event_code']}\n"
                if direct_lookup['event_name']:
                    direct_text += f"Event Type Name: {direct_lookup['event_name']}\n"
                direct_text += f"Number of records: {direct_lookup['count']}"
                
                results.append({
                    'content': direct_text,
                    'metadata': direct_lookup,
                    'similarity': 1.0,  # Highest confidence for direct lookups
                    'source': 'direct_lookup'
                })
                
                # Also find the corresponding event code summary document
                for doc in self.documents:
                    if (doc.get("doc_type") == "event_code_summary" and 
                        str(doc["metadata"].get("event_code")) == direct_lookup['event_code']):
                        results.append({
                            'content': doc["text"],
                            'metadata': doc["metadata"],
                            'similarity': 0.99,  # High confidence for exact matches
                            'source': 'direct_lookup_summary'
                        })
                        break
            
            # 2. Detect query intent
            intent = self._detect_query_intent(query)
            logger.info(f"Detected query intent: {intent}")
            
            # 3. Try keyword search for specific intents
            keyword_results = self._keyword_search(query, intent)
            
            # If we got good keyword results, use them
            if keyword_results:
                logger.info(f"Found {len(keyword_results)} results via keyword search")
                results.extend(keyword_results)
            
            # 4. Perform vector search to supplement results
            # Get query embedding
            query_embedding = np.array([self._get_embedding_for_text(query)], dtype=np.float32)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Search index - get more results than needed to ensure diversity
            scores, indices = self.index.search(query_embedding, min(top_k * 3, len(self.documents)))
            
            # Process vector search results
            vector_results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.documents):  # Skip invalid indices
                    continue
                
                doc = self.documents[idx]
                
                # Skip documents we already found via keyword search or direct lookup
                already_included = False
                for existing_doc in results:
                    if existing_doc.get('content') == doc["text"]:
                        already_included = True
                        break
                
                if not already_included:
                    vector_results.append({
                        'content': doc["text"],
                        'metadata': doc["metadata"],
                        'similarity': float(score),
                        'source': 'vector'
                    })
            
            # 5. Add vector results to supplement other results
            results.extend(vector_results)
            
            # 6. For event code queries, ensure diversity of event codes
            if intent["is_about_event_type"] and not intent["mentioned_event_codes"]:
                # Check if we have at least one example of each event code
                covered_codes = set()
                for result in results:
                    if 'event_code' in result['metadata']:
                        covered_codes.add(str(result['metadata']['event_code']))
                    elif 'EVENT_TYPE_CD' in result['metadata']:
                        covered_codes.add(str(result['metadata']['EVENT_TYPE_CD']))
                
                # If we're missing codes, try to add them
                missing_codes = self.metadata["event_codes"] - covered_codes
                if missing_codes and len(results) < top_k * 2:  # Allow going over top_k a bit for diversity
                    for code in missing_codes:
                        # Find a document for this code
                        for doc in self.documents:
                            event_code = None
                            if 'event_code' in doc["metadata"]:
                                event_code = str(doc["metadata"]['event_code'])
                            elif 'EVENT_TYPE_CD' in doc["metadata"]:
                                event_code = str(doc["metadata"]['EVENT_TYPE_CD'])
                            
                            if event_code == str(code):
                                results.append({
                                    'content': doc["text"],
                                    'metadata': doc["metadata"],
                                    'similarity': 0.7,  # Lower confidence but added for diversity
                                    'source': 'diversity'
                                })
                                break
                        
                        # Stop if we've added enough
                        if len(results) >= top_k * 2:
                            break
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Ensure we have at least one result for each mentioned event code
            if intent["is_about_event_code"] and intent["mentioned_event_codes"]:
                final_results = []
                covered_codes = set()
                
                # First add results for mentioned event codes
                for result in results:
                    event_code = None
                    if 'event_code' in result['metadata']:
                        event_code = str(result['metadata']['event_code'])
                    elif 'EVENT_TYPE_CD' in result['metadata']:
                        event_code = str(result['metadata']['EVENT_TYPE_CD'])
                    
                    if event_code in intent["mentioned_event_codes"] and event_code not in covered_codes:
                        final_results.append(result)
                        covered_codes.add(event_code)
                
                # Then add other results up to top_k
                for result in results:
                    if result not in final_results and len(final_results) < top_k:
                        final_results.append(result)
                
                return final_results[:top_k]
            else:
                return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_context_for_query(self, df: pd.DataFrame, query: str, 
                              file_id: str = None, top_k: int = 10, 
                              force_rebuild: bool = False) -> Tuple[str, List[Dict]]:
        """
        Get context for a query from DataFrame
        
        Args:
            df: The DataFrame to search
            query: The query string
            file_id: Optional file ID for caching
            top_k: Number of results to retrieve (increased from default 5 to 10)
            force_rebuild: Force rebuilding the index
            
        Returns:
            A tuple of (formatted_context, raw_results)
        """
        # Index the DataFrame if needed
        if not self.index or force_rebuild:
            success = self.index_dataframe(df, file_id, force_rebuild)
            if not success:
                return "Could not create search index for the data.", []
        
        # Retrieve context using hybrid search
        contexts = self.retrieve_context(query, top_k)
        
        if not contexts:
            return "No relevant context found in the data.", []
        
        # Check for direct event code lookup
        direct_lookup = None
        for ctx in contexts:
            if ctx.get('source') == 'direct_lookup':
                direct_lookup = ctx
                break
        
        # Format context as string with improved structure
        context_str = "Relevant information from the data:\n\n"
        
        # Add direct lookup result first if available
        if direct_lookup:
            context_str += "DIRECT LOOKUP RESULT:\n"
            context_str += direct_lookup['content']
            context_str += "\n\n"
        
        # Add other contexts - using information blocks instead of numbered contexts
        for i, ctx in enumerate(contexts, 1):
            if ctx.get('source') == 'direct_lookup':
                continue  # Skip, already added above
                
            # Add source information for debugging but don't number the contexts
            source_info = f"[Source: {ctx.get('source', 'unknown')}]"
            context_str += f"INFORMATION BLOCK:\n"  # Changed from CONTEXT {i}
            context_str += ctx['content']
            context_str += "\n\n"
        
        # Add metadata about the retrieval process
        context_str += "RETRIEVAL METADATA:\n"
        
        # Count sources
        source_counts = {}
        for ctx in contexts:
            source = ctx.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        context_str += "Sources: " + ", ".join([f"{k} ({v})" for k, v in source_counts.items()]) + "\n"
        
        # Extract event codes mentioned in the context
        event_codes = set()
        for ctx in contexts:
            if 'event_code' in ctx.get('metadata', {}):
                event_codes.add(str(ctx['metadata']['event_code']))
            elif 'EVENT_TYPE_CD' in ctx.get('metadata', {}):
                event_codes.add(str(ctx['metadata']['EVENT_TYPE_CD']))
        
        if event_codes:
            context_str += "Event codes in context: " + ", ".join(sorted(event_codes)) + "\n"
        
        # Extract potential event codes from query
        potential_codes = re.findall(r'\b\d+\b', query)
        if potential_codes:
            context_str += "Numbers in query: " + ", ".join(potential_codes) + "\n"
            
            # Check which ones are valid event codes
            valid_codes = [code for code in potential_codes if code in self.metadata["event_codes"]]
            if valid_codes:
                context_str += "Valid event codes in query: " + ", ".join(valid_codes) + "\n"
        
        return context_str, contexts