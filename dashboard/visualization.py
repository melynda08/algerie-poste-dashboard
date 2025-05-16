import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_shipment_map(shipment_data):
    """
    Create a modern, interactive map visualization of postal routes between countries
    Designed to handle larger datasets and more countries
    """
    from data_processor import get_country_coordinates
    
    if shipment_data.empty:
        # Return an empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': "No data available for map visualization",
                'font': {'size': 24, 'color': '#212529'}
            },
            template="plotly_white"
        )
        return fig
    
    # Get country coordinates from the enhanced database
    country_coords = get_country_coordinates()
    
    # Check if origin_country and destination_country columns exist
    if 'origin_country' not in shipment_data.columns or 'destination_country' not in shipment_data.columns:
        # Try to use établissement_postal and next_établissement_postal instead
        if 'établissement_postal' in shipment_data.columns and 'next_établissement_postal' in shipment_data.columns:
            shipment_data['origin_country'] = shipment_data['établissement_postal']
            shipment_data['destination_country'] = shipment_data['next_établissement_postal']
        else:
            # Return empty figure if we can't determine routes
            fig = go.Figure()
            fig.update_layout(
                title={
                    'text': "No route data available for map visualization",
                    'font': {'size': 24, 'color': '#212529'}
                },
                template="plotly_white"
            )
            return fig
    
    # Get unique origin-destination pairs with counts
    # Make this more efficient for larger datasets
    route_counts = shipment_data.groupby(['origin_country', 'destination_country']).size().reset_index(name='count')
    
    # Limit to top 100 routes for performance with large datasets
    if len(route_counts) > 100:
        route_counts = route_counts.sort_values('count', ascending=False).head(100)
    
    # Create a base map with modern styling
    fig = go.Figure()
    
    # Create color scale for routes based on count
    max_count = route_counts['count'].max()
    min_count = route_counts['count'].min()
    
    # Add each route as a curved line with gradient color
    for idx, row in route_counts.iterrows():
        origin = row['origin_country']
        destination = row['destination_country']
        
        # Skip if we don't have coordinates for either origin or destination
        if (origin not in country_coords) or (destination not in country_coords):
            continue
        
        # Get coordinates
        orig_coords = country_coords[origin]
        dest_coords = country_coords[destination]
        
        # Calculate normalized count for sizing and coloring
        norm_count = (row['count'] - min_count) / (max_count - min_count) if max_count > min_count else 0.5
        
        # Line width based on count (normalized)
        width = 1.5 + (norm_count * 4)  # Scale from 1.5 to 5.5
        
        # Calculate the color based on count - blue gradient
        color_r = int(65 + (norm_count * 0))      # Fixed at 65
        color_g = int(105 + (norm_count * 60))    # 105-165
        color_b = int(225 - (norm_count * 0))     # Fixed at 225
        line_color = f'rgb({color_r},{color_g},{color_b})'
        
        # Calculate intermediate points for curved paths
        lons = [orig_coords['lon'], dest_coords['lon']]
        lats = [orig_coords['lat'], dest_coords['lat']]
        
        # Add the route line with custom hoverinfo
        fig.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
                mode='lines',
                line=dict(
                    width=width,
                    color=line_color,
                    dash='solid'  # Solid lines
                ),
                opacity=0.8,
                hoverinfo='text',
                text=f"{origin} → {destination}<br>{row['count']} shipments",
                name=f"{origin} → {destination}"
            )
        )
    
    # Add markers for each location with improved styling
    locations = []
    lats = []
    lons = []
    sizes = []
    texts = []
    hover_texts = []
    
    # Count shipments per location (for marker size)
    all_locs = pd.concat([
        shipment_data['origin_country'].dropna(),
        shipment_data['destination_country'].dropna()
    ])
    
    loc_counts = all_locs.value_counts().to_dict()
    
    # Prepare marker data
    for loc, count in loc_counts.items():
        if loc in country_coords:
            locations.append(loc)
            lats.append(country_coords[loc]['lat'])
            lons.append(country_coords[loc]['lon'])
            sizes.append(count)
            texts.append(loc)
            hover_texts.append(f"<b>{loc}</b><br>{count} shipments")
    
    # Normalize sizes
    max_size = max(sizes) if sizes else 1
    min_size = min(sizes) if sizes else 1
    # More subtle size variation
    sizes = [8 + (25 * ((s - min_size) / (max_size - min_size))) for s in sizes] if max_size > min_size else [15] * len(sizes)
    
    # Add markers with improved styling
    fig.add_trace(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            text=hover_texts,
            mode='markers+text',
            textposition='top center',
            textfont=dict(
                family="Arial, sans-serif",
                size=10,
                color="rgba(0, 0, 0, 0.7)"
            ),
            marker=dict(
                size=sizes,
                color='#3182CE',  # Modern blue
                opacity=0.85,
                line=dict(width=1, color='white'),
                gradient=dict(
                    type='radial',
                    color='rgb(255, 255, 255)'
                ),
                symbol='circle'
            ),
            name='Postal Locations',
            hoverinfo='text'
        )
    )
    
    # Update map layout with modern styling
    fig.update_geos(
        projection_type="orthographic",  # More modern 3D globe view
        showland=True,
        landcolor="#f8f9fa",  # Light grey land
        showocean=True,
        oceancolor="#e6f2ff",  # Light blue ocean
        showlakes=True,
        lakecolor="#e6f2ff",
        showcountries=True,
        countrycolor="#d3d3d3",
        showcoastlines=True,
        coastlinecolor="#d3d3d3",
        showframe=False,
        bgcolor='rgba(255, 255, 255, 0)'  # Transparent background
    )
    
    fig.update_layout(
        title={
            'text': "International Postal Routes",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#212529', 'family': 'Arial, sans-serif'}
        },
        showlegend=False,
        height=700,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='rgba(255, 255, 255, 0)',  # Transparent background
        plot_bgcolor='rgba(255, 255, 255, 0)',   # Transparent background
        geo=dict(
            bgcolor='rgba(255, 255, 255, 0)'     # Transparent background
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=[
                    dict(
                        args=[{"geo.projection.type": "orthographic"}],
                        label="3D Globe",
                        method="relayout"
                    ),
                    dict(
                        args=[{"geo.projection.type": "natural earth"}],
                        label="Flat Map",
                        method="relayout"
                    ),
                    dict(
                        args=[{"geo.projection.type": "mercator"}],
                        label="Mercator",
                        method="relayout"
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=0.1,
                yanchor="bottom",
                bgcolor="#F8F9FA",
                bordercolor="#dee2e6",
                font=dict(color="#212529")
            )
        ],
        annotations=[
            dict(
                x=0.01,
                y=0.01,
                xref="paper",
                yref="paper",
                text="Select Map Type:",
                showarrow=False,
                font=dict(size=12, color="#495057")
            )
        ]
    )
    
    return fig

def create_event_type_distribution(shipment_data):
    """
    Create a modern chart showing the distribution of event types
    """
    if shipment_data.empty or 'EVENT_TYPE_NM' not in shipment_data.columns:
        # Return an empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': "No data available for event type distribution",
                'font': {'size': 24, 'color': '#212529'}
            },
            template="plotly_white"
        )
        return fig
    
    # Count events by type
    event_counts = shipment_data['EVENT_TYPE_NM'].value_counts().reset_index()
    event_counts.columns = ['Event Type', 'Count']
    
    # Limit to top 20 events for better visualization
    if len(event_counts) > 20:
        event_counts = event_counts.sort_values('Count', ascending=False).head(20)
    
    # Sort by count ascending for horizontal bar chart
    event_counts = event_counts.sort_values('Count', ascending=True)
    
    # Prepare custom color gradient
    max_count = event_counts['Count'].max()
    min_count = event_counts['Count'].min()
    
    # Create custom colors for each bar based on count
    colors = []
    for count in event_counts['Count']:
        # Normalize the count
        norm_count = (count - min_count) / (max_count - min_count) if max_count > min_count else 0.5
        
        # Calculate color - blue gradient
        color_r = int(65 + (norm_count * 0))      # Fixed at 65
        color_g = int(105 + (norm_count * 60))    # 105-165
        color_b = int(225 - (norm_count * 0))     # Fixed at 225
        colors.append(f'rgba({color_r},{color_g},{color_b},0.8)')
    
    # Create bar chart with modern styling
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=event_counts['Count'],
            y=event_counts['Event Type'],
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(
                    width=1,
                    color='rgba(255, 255, 255, 0.5)'
                )
            ),
            text=event_counts['Count'],
            textposition='auto',
            hoverinfo='text',
            hovertext=[f"<b>{event}</b><br>{count} events" for event, count in zip(event_counts['Event Type'], event_counts['Count'])],
        )
    )
    
    # Update layout with modern styling
    fig.update_layout(
        title={
            'text': "Distribution of Event Types",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#212529', 'family': 'Arial, sans-serif'}
        },
        yaxis={
            'categoryorder': 'total ascending',
            'title': None,
            'showgrid': False,
            'showline': False,
            'tickfont': {'size': 12, 'color': '#495057', 'family': 'Arial, sans-serif'}
        },
        xaxis={
            'title': {
                'text': 'Number of Events',
                'font': {'size': 14, 'color': '#495057', 'family': 'Arial, sans-serif'}
            },
            'showgrid': True,
            'gridcolor': 'rgba(242, 242, 242, 0.8)',
            'zeroline': False
        },
        height=600,
        margin=dict(l=0, r=20, t=50, b=20),
        paper_bgcolor='rgba(255, 255, 255, 0)',  # Transparent background
        plot_bgcolor='rgba(255, 255, 255, 0)',   # Transparent background
        template="plotly_white",
        hoverlabel=dict(
            bgcolor="#F8F9FA",
            font_size=12,
            font_family="Arial, sans-serif"
        )
    )
    
    # Add hover effect
    fig.update_traces(
        hoverlabel=dict(
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='#dee2e6'
        ),
        hovertemplate='%{hovertext}<extra></extra>'
    )
    
    return fig

def create_delivery_time_chart(shipment_data):
    """
    Create a modern chart showing delivery time analysis
    """
    if shipment_data.empty or 'MAILITM_FID' not in shipment_data.columns:
        # Return an empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': "No data available for delivery time analysis",
                'font': {'size': 24, 'color': '#212529'}
            },
            template="plotly_white"
        )
        return fig
    
    # Check if delivery_time_days is already calculated
    if 'delivery_time_days' in shipment_data.columns:
        # Use pre-calculated delivery times
        delivery_times = []
        
        for mail_id, group in shipment_data.groupby('MAILITM_FID'):
            delivery_time = group['delivery_time_days'].max()  # Take the max value (should be the same for all rows)
            
            if pd.notna(delivery_time):
                # Get just one row to extract origin/destination
                sample_row = group.iloc[0]
                
                # Get origin and destination if available
                origin = sample_row.get('origin_country', None)
                destination = sample_row.get('destination_country', None)
                
                delivery_times.append({
                    'MAILITM_FID': mail_id,
                    'origin': origin,
                    'destination': destination,
                    'days': delivery_time
                })
    else:
        # Group shipments by ID and calculate delivery time
        delivery_times = []
        
        for mail_id, group in shipment_data.groupby('MAILITM_FID'):
            sorted_events = group.sort_values('date')
            
            if len(sorted_events) >= 2:  # Need at least two events to calculate time
                first_event = sorted_events.iloc[0]
                last_event = sorted_events.iloc[-1]
                
                # Calculate time difference in days
                if pd.notna(first_event['date']) and pd.notna(last_event['date']):
                    time_diff = (last_event['date'] - first_event['date']).total_seconds() / (24 * 60 * 60)
                    
                    # Get origin and destination if available
                    origin = first_event.get('origin_country', None)
                    destination = last_event.get('destination_country', None)
                    
                    delivery_times.append({
                        'MAILITM_FID': mail_id,
                        'origin': origin,
                        'destination': destination,
                        'days': time_diff
                    })
    
    if not delivery_times:
        # Return an empty figure if no delivery times calculated
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': "No delivery time data available",
                'font': {'size': 24, 'color': '#212529'}
            },
            template="plotly_white"
        )
        return fig
    
    # Create dataframe from delivery times
    delivery_df = pd.DataFrame(delivery_times)
    
    # Create combined visualization for delivery times
    fig = make_subplots(
        rows=2, 
        cols=1,
        subplot_titles=(
            "Delivery Time Distribution (All Routes)",
            "Delivery Time Analysis by Top Routes"
        ),
        vertical_spacing=0.1,
        row_heights=[0.35, 0.65]
    )
    
    # Add histogram to the top subplot
    histnorm_data = go.Histogram(
        x=delivery_df['days'],
        nbinsx=20,
        marker_color='rgba(65, 105, 225, 0.7)',
        marker_line=dict(
            color='white',
            width=1
        ),
        hovertemplate='%{x:.1f} days<br>Count: %{y}<extra></extra>'
    )
    
    fig.add_trace(histnorm_data, row=1, col=1)
    
    # Add a fitted normal distribution curve
    if len(delivery_df) >= 5:  # Only add if we have enough data
        import numpy as np
        from scipy import stats
        
        # Calculate normal distribution parameters
        mean = delivery_df['days'].mean()
        std = delivery_df['days'].std()
        
        # Generate points for the curve
        x = np.linspace(delivery_df['days'].min(), delivery_df['days'].max(), 100)
        
        if not np.isnan(mean) and not np.isnan(std) and std != 0:
            # Calculate PDF
            y = stats.norm.pdf(x, mean, std)
            
            # Scale to match the histogram height
            max_count = np.histogram(delivery_df['days'], bins=20)[0].max()
            y = y * (max_count / y.max())
            
            curve = go.Scatter(
                x=x,
                y=y,
                mode='lines',
                line=dict(
                    color='rgba(220, 53, 69, 0.8)',
                    width=2,
                    dash='dash'
                ),
                name='Fitted Distribution',
                hoverinfo='skip'
            )
            
            fig.add_trace(curve, row=1, col=1)
    
    # Box plots for the bottom subplot (by route)
    if 'origin' in delivery_df.columns and 'destination' in delivery_df.columns:
        # Create route column
        delivery_df['route'] = delivery_df.apply(
            lambda x: f"{x['origin']} → {x['destination']}" if pd.notna(x['origin']) and pd.notna(x['destination']) else "Unknown",
            axis=1
        )
        
        # Keep only the top routes by frequency
        route_counts = delivery_df['route'].value_counts()
        
        # Get top routes with at least 2 shipments, max 10 routes
        top_routes = [route for route in route_counts.index.tolist() if route_counts[route] >= 2][:10]
        
        if top_routes:
            filtered_df = delivery_df[delivery_df['route'].isin(top_routes)]
            
            # Get custom colors for each route
            num_routes = len(top_routes)
            route_colors = [f'rgba(65, {105 + int(i*(150/max(num_routes,1)))}, 225, 0.7)' for i in range(num_routes)]
            
            # Add box plots for each route
            for i, route in enumerate(top_routes):
                route_data = filtered_df[filtered_df['route'] == route]
                
                box = go.Box(
                    x=route_data['days'],
                    name=route,
                    marker_color=route_colors[i],
                    boxmean=True,  # Shows the mean as a dashed line
                    boxpoints='outliers',  # Only show outliers
                    line=dict(
                        width=2
                    ),
                    hoverinfo='all',
                    hovertemplate=f'<b>{route}</b><br>Median: %{{median:.1f}} days<br>Mean: %{{mean:.1f}} days<br>Q1: %{{q1:.1f}} days<br>Q3: %{{q3:.1f}} days<extra></extra>'
                )
                
                fig.add_trace(box, row=2, col=1)
        else:
            # Add a message if no routes have enough data
            fig.add_annotation(
                text="Not enough data for route analysis",
                xref="x2", yref="y2",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(
                    size=14,
                    color="gray"
                ),
                row=2, col=1
            )
    
    # Update subplot layouts
    fig.update_xaxes(
        title_text="Delivery Time (Days)",
        title=dict(font=dict(size=14, color='#495057')),
        showgrid=True,
        gridcolor='rgba(242, 242, 242, 0.8)',
        zeroline=False,
        row=1, col=1
    )
    
    fig.update_yaxes(
        title_text="Number of Shipments",
        title=dict(font=dict(size=14, color='#495057')),
        showgrid=True,
        gridcolor='rgba(242, 242, 242, 0.8)',
        zeroline=False,
        row=1, col=1
    )
    
    fig.update_xaxes(
        title_text="Delivery Time (Days)",
        title=dict(font=dict(size=14, color='#495057')),
        showgrid=True,
        gridcolor='rgba(242, 242, 242, 0.8)',
        zeroline=False,
        row=2, col=1
    )
    
    # Update overall layout with modern styling
    fig.update_layout(
        title={
            'text': "Delivery Time Analysis",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#212529', 'family': 'Arial, sans-serif'}
        },
        height=800,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(255, 255, 255, 0)',  # Transparent background
        plot_bgcolor='rgba(255, 255, 255, 0)',   # Transparent background
        template="plotly_white",
        hoverlabel=dict(
            bgcolor="#F8F9FA",
            font_size=12,
            font_family="Arial, sans-serif"
        ),
        showlegend=False
    )
    
    return fig

def create_route_flow_chart(shipment_data):
    """
    Create a modern Sankey diagram showing flow of shipments between postal facilities
    """
    if shipment_data.empty or 'établissement_postal' not in shipment_data.columns or 'next_établissement_postal' not in shipment_data.columns:
        # Return an empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': "No data available for route flow analysis",
                'font': {'size': 24, 'color': '#212529'}
            },
            template="plotly_white"
        )
        return fig
    
    # Filter out rows where we don't have both origin and destination
    flow_data = shipment_data.dropna(subset=['établissement_postal', 'next_établissement_postal'])
    
    if flow_data.empty:
        # Return an empty figure if no flow data
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': "No route flow data available",
                'font': {'size': 24, 'color': '#212529'}
            },
            template="plotly_white"
        )
        return fig
    
    # Count flows between facilities
    flow_counts = flow_data.groupby(['établissement_postal', 'next_établissement_postal']).size().reset_index(name='count')
    
    # Limit to top 50 flows for better visualization and performance with large datasets
    if len(flow_counts) > 50:
        flow_counts = flow_counts.sort_values('count', ascending=False).head(50)
    
    # Get unique facilities from the filtered flow counts
    origin_facilities = flow_counts['établissement_postal'].unique()
    dest_facilities = flow_counts['next_établissement_postal'].unique()
    all_facilities = list(set(list(origin_facilities) + list(dest_facilities)))
    
    # Create a mapping of facility names to indices
    facility_to_idx = {facility: i for i, facility in enumerate(all_facilities)}
    
    # Prepare Sankey diagram data
    source = [facility_to_idx[origin] for origin in flow_counts['établissement_postal']]
    target = [facility_to_idx[dest] for dest in flow_counts['next_établissement_postal']]
    value = flow_counts['count'].tolist()
    
    # Create custom hover text
    hover_text = [f"{orig} → {dest}<br>{count} shipments" 
                 for orig, dest, count in zip(flow_counts['établissement_postal'], 
                                             flow_counts['next_établissement_postal'],
                                             flow_counts['count'])]
    
    # Generate a color palette for nodes - blue theme with gradient
    node_colors = [f'rgba(65, {105 + int(i*(150/max(len(all_facilities),1)))}, 225, 0.8)' 
                  for i in range(len(all_facilities))]
    
    # Generate link colors based on value - also using blue gradient
    max_count = flow_counts['count'].max()
    min_count = flow_counts['count'].min()
    
    link_colors = []
    for count in flow_counts['count']:
        # Calculate normalized count
        norm_count = (count - min_count) / (max_count - min_count) if max_count > min_count else 0.5
        
        # Calculate color based on count - blue gradient
        color_r = int(65 + (norm_count * 0))      # Fixed at 65
        color_g = int(105 + (norm_count * 60))    # 105-165
        color_b = int(225 - (norm_count * 0))     # Fixed at 225
        link_colors.append(f'rgba({color_r},{color_g},{color_b},0.5)')  # Semi-transparent
    
    # Create the Sankey diagram with improved styling
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=20,
            line=dict(
                color='rgba(255, 255, 255, 0.5)',
                width=0.5
            ),
            label=all_facilities,
            color=node_colors,
            hovertemplate='%{label}<br>Total shipments: %{value}<extra></extra>'
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>Shipments: %{value}<extra></extra>'
        )
    )])
    
    # Update layout with modern styling
    fig.update_layout(
        title={
            'text': "Shipment Flow Between Postal Facilities",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#212529', 'family': 'Arial, sans-serif'}
        },
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color="#495057"
        ),
        height=700,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(255, 255, 255, 0)',  # Transparent background
        plot_bgcolor='rgba(255, 255, 255, 0)',   # Transparent background
        template="plotly_white",
        hoverlabel=dict(
            bgcolor="#F8F9FA",
            font_size=12,
            font_family="Arial, sans-serif",
            bordercolor="#dee2e6"
        )
    )
    
    # Add explanatory annotation
    if len(flow_counts) > 50:
        fig.add_annotation(
            text="Showing top 50 busiest routes",
            xref="paper", yref="paper",
            x=0.5, y=1.05,
            showarrow=False,
            font=dict(
                size=12,
                color="#6c757d"
            )
        )
    
    return fig
