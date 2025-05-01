from langchain_ollama import Ollama
from langchain_community.embeddings import OllamaEmbeddings  # Instead of GPT4All
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from .data_processing import load_and_clean_data

# Add these imports
from .data_processing import load_and_clean_data
import pandas as pd

class LogisticsAI:
    def __init__(self, data_path):
        # Initialize dataframe
        self.df = load_and_clean_data(data_path)
        
        # Initialize LLM components
        self.llm = Ollama(model="llama2:7b", temperature=0.1)
        self.vector_db = self._create_vector_db()
        
    def _create_vector_db(self):
        """Create vector database from processed data"""
        processed_df = self._preprocess_for_llm()
        embeddings = GPT4AllEmbeddings()
        
        return Chroma.from_texts(
            texts=processed_df['document'].tolist(),
            embedding=embeddings,
            metadatas=processed_df.to_dict('records')
        )
    
    def _preprocess_for_llm(self):
        """Prepare data for LLM context"""
        df = self.df.copy()
        df['document'] = df.apply(
            lambda x: f"Package {x['MAILITM_FID']} | Event: {x['EVENT_TYPE_NM']} | "
                      f"Location: {x['établissement_postal']} | Date: {x['date']}",
            axis=1
        )
        return df
    
    def get_qa_chain(self):
        """Create QA chain"""
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_db.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )