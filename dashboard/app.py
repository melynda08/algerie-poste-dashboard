import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from data_processor import load_data, prepare_data
from visualization import (
    create_shipment_map, 
    create_event_type_distribution, 
    create_delivery_time_chart,
    create_route_flow_chart
)

# Page configuration
st.set_page_config(
    page_title="Postal Tracking Dashboard",
    layout="wide"
)

# Modern dashboard styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #212529;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 6px;
        padding: 10px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f2ff !important;
        color: #0066cc !important;
    }
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .metric-label {
        font-size: 1rem;
        font-weight: 500;
        color: #495057;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0066cc;
    }
    .stSidebar [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    div[data-testid="stVerticalBlock"] > div.stMarkdown p {
        font-size: 1.05rem;
    }
    .rag-button {
        background-color: #0066cc;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 600;
        text-align: center;
        margin: 20px 0;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .rag-button:hover {
        background-color: #0052a3;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📦 International Postal Tracking Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Analyze and visualize international shipment tracking data</div>', unsafe_allow_html=True)

# Add RAG Application Button - Prominent placement at the top
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <a href="http://localhost:3000" target="_blank">
        <div class="rag-button">
            🤖 Open AI-Powered Data Analysis Tool
        </div>
    </a>
    """, unsafe_allow_html=True)

# Load the data
@st.cache_data
def get_data():
    shipments_df, receptacles_df, event_types_df, countries_df = load_data()
    
    # Prepare data for analysis
    shipments_processed, receptacles_processed = prepare_data(
        shipments_df, 
        receptacles_df, 
        event_types_df, 
        countries_df
    )
    
    return shipments_processed, receptacles_processed, event_types_df, countries_df

try:
    shipment_data, receptacle_data, event_types, countries = get_data()
    
    # Sidebar for filters with modern styling
    st.sidebar.markdown("""
        <div style="background-color: #007BFF; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin: 0; color: white; font-size: 1.3rem; font-weight: 600;">Dashboard Filters</h3>
            <p style="margin: 5px 0 0 0; color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">
                Customize your view of the postal data
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Add RAG button in sidebar as well for easy access
    st.sidebar.markdown("""
    <a href="http://localhost:3000" target="_blank">
        <div class="rag-button" style="margin-bottom: 25px;">
            🤖 AI Data Analysis
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    # Date range filter with improved styling
    st.sidebar.markdown("""
        <div style="background-color: #e6f2ff; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
            <p style="margin: 0; font-weight: 500; color: #0066cc;">Date Range Selection</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Calculate date range from data
    min_date = min(
        shipment_data['date'].min() if not shipment_data.empty else datetime.datetime.now(),
        receptacle_data['date'].min() if not receptacle_data.empty else datetime.datetime.now()
    )
    
    max_date = max(
        shipment_data['date'].max() if not shipment_data.empty else datetime.datetime.now(),
        receptacle_data['date'].max() if not receptacle_data.empty else datetime.datetime.now()
    )
    
    # Create a modern date picker
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
        help="Filter data between these dates"
    )
    
    # Show the selected date range
    if len(date_range) == 2:
        st.sidebar.markdown(f"""
            <div style="font-size: 0.9rem; color: #495057; margin-bottom: 20px;">
                Selected period: <span style="color: #0066cc; font-weight: 500;">
                {date_range[0].strftime('%d %b %Y')} - {date_range[1].strftime('%d %b %Y')}
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    # Check if we have two dates
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_shipments = shipment_data[
            (shipment_data['date'].dt.date >= start_date) & 
            (shipment_data['date'].dt.date <= end_date)
        ]
        
        filtered_receptacles = receptacle_data[
            (receptacle_data['date'].dt.date >= start_date) & 
            (receptacle_data['date'].dt.date <= end_date)
        ]
    else:
        filtered_shipments = shipment_data
        filtered_receptacles = receptacle_data
    
    # Country filter using the countries reference file
    # This ensures we show all available countries from the reference file
    # not just those in the current dataset
    st.sidebar.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
    st.sidebar.markdown("""
        <div style="background-color: #e6f2ff; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
            <p style="margin: 0; font-weight: 500; color: #0066cc;">Country Selection</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get all country names from the reference file
    if not countries.empty and 'COUNTRY_NM' in countries.columns:
        # Create a list of country codes and names for the filter
        all_ref_countries = sorted(countries['COUNTRY_NM'].unique().tolist())
        
        # Also include countries that appear in the data but might not be in the reference file
        if 'origin_country' in filtered_shipments.columns and 'destination_country' in filtered_shipments.columns:
            data_countries = set()
            
            # Get countries from shipment data
            if not filtered_shipments.empty:
                data_countries.update(filtered_shipments['origin_country'].dropna().unique())
                data_countries.update(filtered_shipments['destination_country'].dropna().unique())
            
            # Get countries from receptacle data
            if not filtered_receptacles.empty:
                if 'origin_country' in filtered_receptacles.columns:
                    data_countries.update(filtered_receptacles['origin_country'].dropna().unique())
                if 'destination_country' in filtered_receptacles.columns:
                    data_countries.update(filtered_receptacles['destination_country'].dropna().unique())
            
            # Combine reference and data countries
            all_countries = sorted(list(set(all_ref_countries) | data_countries))
        else:
            all_countries = all_ref_countries
        
        # Create the multiselect filter with search capability
        selected_countries = st.sidebar.multiselect(
            "Filter by Countries",
            options=all_countries,
            default=[],
            help="Select one or more countries to filter the data"
        )
        
        # Apply country filter if countries were selected
        if selected_countries:
            if 'origin_country' in filtered_shipments.columns and 'destination_country' in filtered_shipments.columns:
                filtered_shipments = filtered_shipments[
                    (filtered_shipments['origin_country'].isin(selected_countries)) | 
                    (filtered_shipments['destination_country'].isin(selected_countries))
                ]
                
                # Filter receptacles based on selected countries if possible
                if not filtered_receptacles.empty and 'origin_country' in filtered_receptacles.columns and 'destination_country' in filtered_receptacles.columns:
                    filtered_receptacles = filtered_receptacles[
                        (filtered_receptacles['origin_country'].isin(selected_countries)) | 
                        (filtered_receptacles['destination_country'].isin(selected_countries))
                    ]
    
    # Event type filter using the event types reference file
    st.sidebar.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
    st.sidebar.markdown("""
        <div style="background-color: #e6f2ff; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
            <p style="margin: 0; font-weight: 500; color: #0066cc;">Event Type Selection</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get all event types from the reference file
    if not event_types.empty and 'EVENT_TYPE_NM' in event_types.columns:
        # Create a list of event type names for the filter
        all_ref_event_types = sorted(event_types['EVENT_TYPE_NM'].unique().tolist())
        
        # Also include event types that appear in the data but might not be in the reference file
        if 'EVENT_TYPE_NM' in filtered_shipments.columns:
            data_event_types = set()
            
            # Get event types from shipment data
            if not filtered_shipments.empty:
                data_event_types.update(filtered_shipments['EVENT_TYPE_NM'].dropna().unique())
            
            # Get event types from receptacle data
            if not filtered_receptacles.empty and 'EVENT_TYPE_NM' in filtered_receptacles.columns:
                data_event_types.update(filtered_receptacles['EVENT_TYPE_NM'].dropna().unique())
            
            # Combine reference and data event types
            all_event_types = sorted(list(set(all_ref_event_types) | data_event_types))
        else:
            all_event_types = all_ref_event_types
        
        # Create the multiselect filter with search capability
        selected_event_types = st.sidebar.multiselect(
            "Filter by Event Types",
            options=all_event_types,
            default=[],
            help="Select one or more event types to filter the data"
        )
        
        # Apply event type filter if event types were selected
        if selected_event_types:
            if 'EVENT_TYPE_NM' in filtered_shipments.columns:
                filtered_shipments = filtered_shipments[filtered_shipments['EVENT_TYPE_NM'].isin(selected_event_types)]
                
                # Filter receptacles based on selected event types if possible
                if not filtered_receptacles.empty and 'EVENT_TYPE_NM' in filtered_receptacles.columns:
                    filtered_receptacles = filtered_receptacles[filtered_receptacles['EVENT_TYPE_NM'].isin(selected_event_types)]
    
    # Main dashboard content
    st.header("Overview of Postal Shipments")
    
    # Key metrics with modern styling
    st.markdown("""
    <div style="padding: 10px 0px 30px 0px;">
        <div style="height: 2px; background-color: #f0f0f0; margin-bottom: 20px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_shipments = len(filtered_shipments['MAILITM_FID'].unique()) if 'MAILITM_FID' in filtered_shipments.columns else 0
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Total Shipments</div>
            <div class="metric-value">{total_shipments:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_receptacles = len(filtered_receptacles['ECPTCL_FID'].unique()) if 'ECPTCL_FID' in filtered_receptacles.columns else 0
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Total Receptacles</div>
            <div class="metric-value">{total_receptacles:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        countries_count = len(set(filtered_shipments['origin_country'].dropna()) | 
                          set(filtered_shipments['destination_country'].dropna())) if 'origin_country' in filtered_shipments.columns else 0
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Countries Involved</div>
            <div class="metric-value">{countries_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        event_types_count = len(filtered_shipments['EVENT_TYPE_NM'].unique()) if 'EVENT_TYPE_NM' in filtered_shipments.columns else 0
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Event Types</div>
            <div class="metric-value">{event_types_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add another RAG button before the tabs for better visibility
    st.markdown("""
    <div style="padding: 15px 0;">
        <a href="http://localhost:3000" target="_blank">
            <div class="rag-button" style="max-width: 500px; margin: 0 auto;">
                🔍 Explore Data with AI-Powered Analysis Tool
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Postal Routes", "Event Analysis", "Delivery Performance", "Shipment Flow"])
    
    with tab1:
        st.subheader("International Postal Routes")
        shipment_map = create_shipment_map(filtered_shipments)
        st.plotly_chart(shipment_map, use_container_width=True)
    
    with tab2:
        st.subheader("Event Type Distribution")
        event_dist_chart = create_event_type_distribution(filtered_shipments)
        st.plotly_chart(event_dist_chart, use_container_width=True)
        
        # Event timeline
        if not filtered_shipments.empty and 'date' in filtered_shipments.columns and 'EVENT_TYPE_NM' in filtered_shipments.columns:
            st.subheader("Event Timeline")
            
            # Group by date and event type
            timeline_data = filtered_shipments.groupby([pd.Grouper(key='date', freq='D'), 'EVENT_TYPE_NM']).size().reset_index(name='count')
            
            # Create the timeline chart
            fig = px.line(
                timeline_data, 
                x='date', 
                y='count', 
                color='EVENT_TYPE_NM',
                title="Daily Event Frequency",
                labels={"date": "Date", "count": "Number of Events", "EVENT_TYPE_NM": "Event Type"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Delivery Performance Analysis")
        delivery_chart = create_delivery_time_chart(filtered_shipments)
        st.plotly_chart(delivery_chart, use_container_width=True)
        
        # Top origin-destination pairs
        if not filtered_shipments.empty and 'origin_country' in filtered_shipments.columns and 'destination_country' in filtered_shipments.columns:
            st.subheader("Top Origin-Destination Pairs")
            
            pair_counts = filtered_shipments.groupby(['origin_country', 'destination_country']).size().reset_index(name='count')
            pair_counts = pair_counts.sort_values('count', ascending=False).head(10)
            
            fig = px.bar(
                pair_counts, 
                x='count', 
                y=pair_counts.apply(lambda row: f"{row['origin_country']} → {row['destination_country']}", axis=1),
                orientation='h',
                title="Top 10 Shipment Routes",
                labels={"y": "Route", "count": "Number of Shipments"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Shipment Flow Analysis")
        flow_chart = create_route_flow_chart(filtered_shipments)
        st.plotly_chart(flow_chart, use_container_width=True)
        
        # Distribution of shipments by postal facility
        if not filtered_shipments.empty and 'établissement_postal' in filtered_shipments.columns:
            st.subheader("Distribution by Postal Facility")
            
            facility_counts = filtered_shipments['établissement_postal'].value_counts().reset_index()
            facility_counts.columns = ['Facility', 'Count']
            facility_counts = facility_counts.sort_values('Count', ascending=False).head(10)
            
            fig = px.bar(
                facility_counts, 
                x='Count', 
                y='Facility',
                orientation='h',
                title="Top 10 Postal Facilities",
                labels={"Facility": "Postal Facility", "Count": "Number of Events"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Add another RAG button before the raw data section
    st.markdown("""
    <div style="padding: 20px 0;">
        <a href="http://localhost:3000" target="_blank">
            <div class="rag-button" style="max-width: 500px; margin: 0 auto;">
                🤖 Need deeper insights? Try our AI Analysis Tool
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Raw data section with tabs
    st.header("Raw Data")
    
    data_tab1, data_tab2, data_tab3, data_tab4 = st.tabs(["Shipments", "Receptacles", "Event Types", "Countries"])
    
    with data_tab1:
        st.dataframe(filtered_shipments)
    
    with data_tab2:
        st.dataframe(filtered_receptacles)
    
    with data_tab3:
        st.dataframe(event_types)
    
    with data_tab4:
        st.dataframe(countries)

except Exception as e:
    st.error(f"An error occurred while loading the data: {e}")
    st.info("Please check that the CSV files are properly formatted and available.")
    
    # Even if there's an error, still show the RAG button
    st.markdown("""
    <div style="padding: 20px 0;">
        <a href="http://localhost:3000" target="_blank">
            <div class="rag-button" style="max-width: 500px; margin: 0 auto;">
                🤖 Try our AI-Powered Data Analysis Tool
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True)