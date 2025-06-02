# Postal Analytics Platform - Complete Documentation

## Overview

NexaDash is a comprehensive data analysis ecosystem designed for Algérie Poste, combining interactive data visualization with AI-powered conversational analytics. The platform consists of two main components:

1. **International Postal Tracking Dashboard** - Interactive Streamlit-based visualization tool
2. **RAG Analytics Platform** - AI-powered conversational interface with natural language querying

This integrated solution enables deep exploration of postal routes, event types, delivery times, and shipment flow patterns through both traditional dashboards and conversational AI interfaces.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Postal Analytics Platform                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   Streamlit         │    │      RAG Analytics              │ │
│  │   Dashboard         │◄──►│      Platform                   │ │
│  │   (Port 5002)       │    │   ┌─────────────────────────┐   │ │
│  │                     │    │   │  React Frontend         │   │ │
│  │ • Route Maps        │    │   │  (Port 3000)            │   │ │
│  │ • Event Analysis    │    │   └─────────────────────────┘   │ │
│  │ • Delivery Times    │    │   ┌─────────────────────────┐   │ │
│  │ • Flow Diagrams     │    │   │  Flask Backend          │   │ │
│  └─────────────────────┘    │   │  (Port 5000)            │   │ │
│                              │   └─────────────────────────┘   │ │
│                              └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                       │
                              ┌─────────────────┐
                              │   External APIs │
                              │ • OpenAI/Gemini│
                              │ • Embedding     │
                              │   Models        │
                              └─────────────────┘
```

---

## Part 1: International Postal Tracking Dashboard

### Project Structure

```
dashboard/
├── app.py                 # Main Streamlit application
├── data_processor.py      # Data loading and preprocessing
├── visualization.py       # All Plotly visualization functions
├── README.md              # Project documentation
└── attached_assets/       # Directory with required CSV files
```

### Quick Start

#### Step 1: Navigate to the dashboard directory
```bash
cd /home/melynda/algerie_post_ai/dashboard
```

#### Step 2: Launch the Streamlit app
```bash
streamlit run app.py
```

> The dashboard runs by default on port **5002**.

### Features and Functionality

#### User Interface and Filtering
- **Date Range Picker**: Filter data by date range
- **Country Selector**: Multi-country selection for origin/destination
- **Event Type Selector**: Choose one or more postal event types
- **RAG Integration Buttons**: Direct access to AI assistant (http://localhost:3000)

#### Visualizations
- **Postal Routes Map**: Interactive map with top 100 routes, color-coded by volume
- **Event Type Distribution**: Bar chart of event frequency analysis
- **Delivery Time Analysis**: Histogram and box plots of delivery durations
- **Shipment Flow Diagram**: Sankey diagram showing flow between facilities

### Data Pipeline

#### 1. Data Loading (`data_processor.py`)
- `load_data()`: Loads multiple CSV files with validation
- `prepare_data()`: Parses dates, standardizes countries, adds coordinates, calculates delivery times

#### 2. Data Visualization (`visualization.py`)
- `create_shipment_map(...)`: Interactive route mapping
- `create_event_type_distribution(...)`: Event frequency charts
- `create_delivery_time_chart(...)`: Delivery time analysis
- `create_route_flow_chart(...)`: Sankey flow diagrams

### Required CSV Files

Place the following files in `attached_assets/`:
- `export_data_01_01_2025_20_03_2025.csv`
- `EXPORT_DATA_receptacle_01_01_2023_20_03_2025.csv`
- `CT_EVENT_TYPES.csv`
- `CT_COUNTRIES.csv`

---

## Part 2: RAG Analytics Platform

### System Overview

A Retrieval-Augmented Generation (RAG) platform that enables natural language interaction with postal data through conversational AI and dynamic visualizations.

### Key Features

| Feature | Description |
|---------|-------------|
| **Natural Language Chat** | AI-powered conversations about uploaded data |
| **Dynamic Visualizations** | Auto-generated charts from text prompts |
| **Multi-Model Support** | Local/OpenAI/TogetherAI/HuggingFace embeddings |
| **Conversation History** | Persistent chat sessions with search |
| **File Management** | CSV upload/delete with preview capabilities |

### Technical Architecture

#### Frontend Structure (React + TypeScript)

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   ├── pages/             # Main application pages
│   │   ├── LoginPage.tsx          # JWT-based authentication
│   │   ├── DashboardPage.tsx      # System overview
│   │   ├── FilesPage.tsx          # CSV management
│   │   ├── ChatPage.tsx           # AI conversation interface
│   │   ├── VisualizationPage.tsx  # Chart generation
│   │   ├── HistoryPage.tsx        # Conversation archive
│   │   └── SettingsPage.tsx       # Configuration
│   ├── contexts/          # React Context providers
│   └── utils/             # Helper functions
└── package.json
```

#### Backend Structure (Flask + Python)

```
backend/
├── app.py                       # Flask application entry point
├── routes/                      # API route handlers
├── models/                      # SQLAlchemy models
├── rag_chain.py                 # RAG logic for embedding + LLM
├── embed_config.py              # Embedding model loaders
├── llm_config.py                # LLM API wrappers
├── prompt_router.py             # Prompt classification logic
├── data/                        # User-uploaded CSV files
├── faiss_index/                 # FAISS vector store
├── .env                         # Environment variables
└── requirements.txt
```

### Installation Guide

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the Flask server
python app.py
```

### Configuration

Create a `.env` file in the backend directory:

```ini
# Authentication
SECRET_KEY=your_random_string
JWT_EXPIRE_HOURS=24

# Embeddings
EMBEDDING_PROVIDER=local # local/openai/together/huggingface
LOCAL_MODEL=all-MiniLM-L6-v2

# API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
TOGETHER_API_KEY=...
HF_API_KEY=...

# Database
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### API Reference

#### Authentication
- `POST /login` - User authentication
- `POST /start_conversation` - Initialize chat session

#### File Management
- `POST /upload_csv` - Upload CSV files
- `GET /csv_files` - List uploaded files
- `GET /csv_metadata/{file_id}` - Get file metadata
- `DELETE /delete_csv/{file_id}` - Delete CSV file

#### Chat & Search
- `POST /chat` - Process natural language queries
- `POST /search_csv` - Search within CSV data

#### Visualization
- `POST /visualize` - Generate charts from prompts
- `POST /add_visualization_to_dashboard` - Save visualizations
- `GET /dashboard_visualizations` - Retrieve saved charts
- `DELETE /dashboard_visualizations/{visualization_id}` - Remove charts

#### Embedding & Configuration
- `GET /embedding_models` - List available models
- `POST /embedding_provider` - Switch embedding provider
- `POST /reindex` - Rebuild vector index

#### History
- `GET /conversations/{user_id}` - User conversation list
- `GET /history/{user_id}` - Chat history
- `GET /conversation_messages/{conversation_id}` - Message details

---

## Functional Workflows

### 1. CSV Processing and Indexing
1. User uploads CSV file through the interface
2. System validates file format and structure
3. Data is processed and indexed for semantic search
4. Metadata extraction and display
5. Confirmation of successful processing

### 2. AI-Powered Chat Analysis
1. User selects a CSV file from the list
2. User asks questions in natural language
3. System retrieves relevant context from indexed data
4. LLM generates contextual, data-driven answers
5. Response displayed with conversation history saved

### 3. Visualization Generation
1. User selects target CSV file
2. User enters visualization prompt (e.g., "Show me delivery times by country")
3. System analyzes prompt and data structure
4. Appropriate chart type selected automatically
5. Interactive visualization generated and displayed
6. Option to save to dashboard or download

---

## Dependencies

### Dashboard Dependencies
```bash
pip install streamlit pandas plotly numpy scipy
```

### RAG Platform Dependencies
```bash
# Backend
pip install flask flask-cors pandas python-dotenv python-dateutil requests
pip install sentence-transformers faiss-cpu openai

# Frontend
npm install react react-router-dom typescript axios
```

---

## Integration Points

The two systems are designed to work together seamlessly:

1. **Cross-Navigation**: Dashboard includes prominent buttons linking to RAG interface
2. **Shared Data**: Both systems can work with the same CSV datasets
3. **Complementary Analysis**: Traditional visualizations + conversational insights
4. **Unified User Experience**: Consistent design patterns and workflows

---

## Deployment

### Development Environment
- **Streamlit Dashboard**: http://localhost:5002
- **RAG Frontend**: http://localhost:3000  
- **RAG Backend API**: http://localhost:5000

### Production Considerations
- Configure CORS settings for production domains
- Set up proper authentication and session management
- Implement rate limiting for API endpoints
- Configure SSL certificates for HTTPS
- Set up monitoring and logging

---

## Sample Usage

### Example Chat Query
```json
{
  "query": "What are the average delivery times to European countries?",
  "response": "Based on the CSV data, average delivery times to European countries are: France (5.2 days), Germany (6.1 days), Spain (7.3 days). Express shipping reduces these times by approximately 40%.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440002",
  "embedding_provider": "local"
}
```

### Example Visualization Prompt
- "Create a bar chart showing shipment volumes by destination country"
- "Show me delivery time trends over the last 6 months"
- "Generate a pie chart of event types distribution"

---

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure ports 3000, 5000, and 5002 are available
2. **Missing CSV Files**: Verify all required files are in `attached_assets/`
3. **API Key Issues**: Check environment variables are properly set
4. **Memory Issues**: Large CSV files may require increased system memory

### Error Handling
- Missing files display user-friendly error messages
- API failures gracefully degrade with fallback responses
- RAG system remains accessible even if dashboard encounters issues

---

## Contributing

1. Fork the repository
2. Create feature branches for new functionality
3. Follow existing code style and patterns
4. Add tests for new features
5. Update documentation as needed

---

## License

This project is part of the NexaDash 2025 platform for Algérie Poste. All rights reserved.

---

## Support

For technical support or questions:
- Check the troubleshooting section above
- Review API documentation for backend integration
- Ensure all dependencies are properly installed
- Verify environment configuration matches requirements

This comprehensive platform provides postal analysts and developers with powerful tools to explore, search, and visualize logistics data through both traditional dashboards and cutting-edge conversational AI interfaces.
