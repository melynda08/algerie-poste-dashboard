import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
from typing import Dict, Any, List, Optional
import re

class VisualizationGenerator:
    """Generate visualizations based on user prompts and CSV data"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        self.date_cols = [col for col in df.columns if df[col].dtype == 'datetime64[ns]']
        
        # Try to convert string columns to datetime
        for col in self.categorical_cols:
            try:
                pd.to_datetime(df[col])
                self.date_cols.append(col)
            except:
                pass
    
    def _extract_columns_from_prompt(self, prompt: str) -> Dict[str, List[str]]:
        """Extract column names mentioned in the prompt"""
        columns = {
            'x': [],
            'y': [],
            'color': [],
            'size': []
        }
        
        # Check for columns in the prompt
        for col in self.df.columns:
            if col.lower() in prompt.lower():
                # Determine role based on column type and context
                if col in self.numeric_cols:
                    if 'count' in col.lower() or 'sum' in col.lower() or 'total' in col.lower():
                        columns['y'].append(col)
                    elif len(columns['x']) == 0 and (col in self.date_cols or 'date' in col.lower() or 'time' in col.lower()):
                        columns['x'].append(col)
                    elif len(columns['y']) == 0:
                        columns['y'].append(col)
                    elif len(columns['size']) == 0 and ('size' in prompt.lower() or 'bubble' in prompt.lower()):
                        columns['size'].append(col)
                    else:
                        columns['y'].append(col)
                else:
                    if len(columns['x']) == 0:
                        columns['x'].append(col)
                    elif len(columns['color']) == 0 and ('color' in prompt.lower() or 'group' in prompt.lower()):
                        columns['color'].append(col)
                    else:
                        columns['color'].append(col)
        
        # If no columns were found, use defaults
        if not columns['x'] and self.df.columns.size > 0:
            columns['x'] = [self.df.columns[0]]
        if not columns['y'] and len(self.numeric_cols) > 0:
            columns['y'] = [self.numeric_cols[0]]
            
        return columns
    
    def _detect_chart_type(self, prompt: str) -> str:
        """Detect the type of chart requested in the prompt"""
        prompt = prompt.lower()
        
        if any(term in prompt for term in ['bar', 'column', 'histogram']):
            return 'bar'
        elif any(term in prompt for term in ['line', 'trend', 'time series']):
            return 'line'
        elif any(term in prompt for term in ['scatter', 'bubble', 'point']):
            return 'scatter'
        elif any(term in prompt for term in ['pie', 'donut', 'circle']):
            return 'pie'
        elif any(term in prompt for term in ['box', 'boxplot']):
            return 'box'
        elif any(term in prompt for term in ['heatmap', 'heat map', 'correlation']):
            return 'heatmap'
        elif any(term in prompt for term in ['sunburst', 'hierarchy']):
            return 'sunburst'
        else:
            # Default to bar chart if no specific type is detected
            return 'bar'
    
    def generate_visualization(self, prompt: str) -> Dict[str, Any]:
        """Generate a visualization based on the user prompt"""
        chart_type = self._detect_chart_type(prompt)
        columns = self._extract_columns_from_prompt(prompt)
        
        title = f"Visualization of {', '.join(columns['y'])} by {', '.join(columns['x'])}"
        if "title" in prompt.lower():
            # Try to extract a title from the prompt
            title_match = re.search(r'title[:\s]+([^\.]+)', prompt, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
        
        fig = None
        
        try:
            if chart_type == 'bar':
                if len(columns['y']) > 1:
                    # Multiple y columns - grouped bar chart
                    fig = px.bar(
                        self.df, 
                        x=columns['x'][0], 
                        y=columns['y'],
                        color=columns['color'][0] if columns['color'] else None,
                        barmode='group',
                        title=title
                    )
                else:
                    # Single y column - regular bar chart
                    fig = px.bar(
                        self.df, 
                        x=columns['x'][0], 
                        y=columns['y'][0],
                        color=columns['color'][0] if columns['color'] else None,
                        title=title
                    )
            
            elif chart_type == 'line':
                fig = px.line(
                    self.df, 
                    x=columns['x'][0], 
                    y=columns['y'],
                    color=columns['color'][0] if columns['color'] else None,
                    title=title
                )
            
            elif chart_type == 'scatter':
                fig = px.scatter(
                    self.df, 
                    x=columns['x'][0], 
                    y=columns['y'][0],
                    color=columns['color'][0] if columns['color'] else None,
                    size=columns['size'][0] if columns['size'] else None,
                    title=title
                )
            
            elif chart_type == 'pie':
                fig = px.pie(
                    self.df, 
                    names=columns['x'][0], 
                    values=columns['y'][0],
                    title=title
                )
            
            elif chart_type == 'box':
                fig = px.box(
                    self.df, 
                    x=columns['x'][0], 
                    y=columns['y'][0],
                    color=columns['color'][0] if columns['color'] else None,
                    title=title
                )
            
            elif chart_type == 'heatmap':
                # For heatmap, we need to pivot the data
                if len(columns['x']) > 0 and len(columns['y']) > 0:
                    pivot_df = self.df.pivot_table(
                        index=columns['x'][0],
                        columns=columns['color'][0] if columns['color'] else columns['y'][0],
                        values=columns['y'][0] if columns['color'] else columns['y'][1] if len(columns['y']) > 1 else None,
                        aggfunc='mean'
                    )
                    fig = px.imshow(
                        pivot_df,
                        title=title
                    )
                else:
                    # Fallback to correlation heatmap
                    corr_df = self.df[self.numeric_cols].corr()
                    fig = px.imshow(
                        corr_df,
                        title="Correlation Heatmap"
                    )
            
            elif chart_type == 'sunburst':
                # For sunburst, we need at least 2 categorical columns
                path = columns['x'] + columns['color']
                if len(path) < 2:
                    # Add more columns if needed
                    for col in self.categorical_cols:
                        if col not in path:
                            path.append(col)
                            if len(path) >= 3:  # Limit to 3 levels for readability
                                break
                
                fig = px.sunburst(
                    self.df,
                    path=path[:3],  # Limit to 3 levels for readability
                    values=columns['y'][0] if columns['y'] else None,
                    title=title
                )
            
            if fig:
                img_bytes = fig.to_image(format="png")
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                return {
                    "image": f"data:image/png;base64,{img_b64}",
                    "chart_type": chart_type,
                    "title": title
                }
            else:
                return {"error": "Could not generate visualization"}
                
        except Exception as e:
            return {"error": f"Error generating visualization: {str(e)}"}
