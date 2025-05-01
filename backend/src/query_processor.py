import re
from typing import Dict, Any
import pandas as pd
from src.data_processing import load_and_clean_data  # Add this import

class QueryHandler:
    def __init__(self, qa_chain):
        self.qa = qa_chain
        self.df = qa_chain.df  # Add dataframe reference

    def _extract_package_id(self, query: str) -> str:
        match = re.search(r'\b[1A]\d{11}\b', query)
        return match.group(0) if match else None

    def _package_status(self, package_id: str) -> Dict[str, Any]:
        # Properly indented code block
        package_data = self.df[self.df['MAILITM_FID'] == package_id]
        
        if package_data.empty:
            return {"error": f"Package {package_id} not found"}
            
        timeline = package_data.sort_values('date')[['date', 'EVENT_TYPE_NM', 'établissement_postal']]
        last_event = timeline.iloc[-1]

        status = "Inconnu"
        if "Livraison" in last_event['EVENT_TYPE_NM']:
            status = "Livré"
        elif "tentative" in last_event['EVENT_TYPE_NM']:
            status = "En tentative"
        else:
            status = "En transit"

        return {
            "package_id": package_id,
            "status": status,
            "last_event": {
                "date": last_event['date'],
                "event": last_event['EVENT_TYPE_NM'],
                "location": last_event['établissement_postal']
            },
            "timeline": timeline.to_dict('records')
        }

    def handle_query(self, query: str) -> Dict[str, Any]:
        package_id = self._extract_package_id(query)
        
        if package_id:
            return self._package_status(package_id)
        elif "statistiques" in query.lower():
            return self._generate_statistics(query)
        else:
            return self.qa.invoke(query)

    def _generate_statistics(self, query: str) -> Dict[str, Any]:
        # Add proper indentation here
        return {"response": "Statistics feature under development"}