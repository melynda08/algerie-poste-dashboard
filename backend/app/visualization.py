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
        
        # Fix encoding issues in column names
        self.df.columns = [self._fix_encoding(col) for col in self.df.columns]
        
        # Detect column types
        self.numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        self.date_cols = [col for col in df.columns if df[col].dtype == 'datetime64[ns]']
        
        # Try to convert string columns to datetime with explicit format detection
        for col in self.categorical_cols[:]:  # Use a copy to avoid modification during iteration
            if 'date' in col.lower() or 'time' in col.lower() or 'day' in col.lower():
                # Try to detect common date formats
                date_formats = [
                    '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', 
                    '%Y/%m/%d', '%b %d %Y', '%d %b %Y', '%B %d %Y',
                    '%d %B %Y', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S'
                ]
                
                # Get a sample of non-null values for format detection
                sample = df[col].dropna().iloc[:10] if not df[col].dropna().empty else []
                
                for date_format in date_formats:
                    try:
                        # Try to parse using the specific format
                        pd.to_datetime(sample, format=date_format)
                        # If successful, convert the entire column
                        self.df[col] = pd.to_datetime(df[col], format=date_format, errors='coerce')
                        self.date_cols.append(col)
                        # Remove from categorical columns
                        self.categorical_cols.remove(col)
                        break
                    except (ValueError, TypeError):
                        continue
                
                # If no specific format worked, try with dateutil parser but suppress warnings
                if col not in self.date_cols:
                    try:
                        import warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            self.df[col] = pd.to_datetime(df[col], errors='coerce')
                        if not pd.isna(self.df[col]).all():  # Only keep if some values were parsed
                            self.date_cols.append(col)
                            # Remove from categorical columns if conversion successful
                            if col in self.categorical_cols:
                                self.categorical_cols.remove(col)
                    except:
                        pass
    
    def _fix_encoding(self, text):
        """Fix encoding issues in text"""
        if not isinstance(text, str):
            return text
            
        # Replace common encoding issues
        replacements = {
            'Ã©': 'é',
            'Ã¨': 'è',
            'Ã': 'à',
            'Ã®': 'î',
            'Ã´': 'ô',
            'Ã¹': 'ù',
            'Ã§': 'ç',
            'Ãª': 'ê',
            'Ã«': 'ë',
            'Ã¯': 'ï',
            'Ã¼': 'ü',
            'Ã¶': 'ö',
            'Ã¤': 'ä',
            'Ã±': 'ñ',
            'Ã¡': 'á',
            'Ã³': 'ó',
            'Ãº': 'ú',
            'Ã­': 'í',
            'â€™': "'",
            'â€œ': '"',
            'â€': '"',
            'â€"': '–',
            'â€"': '—',
            'Â°': '°',
            'Â²': '²',
            'Â³': '³',
            'Â©': '©',
            'Â®': '®',
            'â„¢': '™',
            'Â£': '£',
            'â‚¬': '€',
            'Â¥': '¥',
            'Â¢': '¢',
            'Â½': '½',
            'Â¼': '¼',
            'Â¾': '¾',
            'Â±': '±',
            'Ã—': '×',
            'Ã·': '÷',
            'Â¹': '¹',
            'Â²': '²',
            'Â³': '³',
            'Â¦': '¦',
            'Â§': '§',
            'Â¨': '¨',
            'Â´': '´',
            'Âµ': 'µ',
            'Â¸': '¸',
            'Â»': '»',
            'Â«': '«',
            'Â¿': '¿',
            'Â¡': '¡',
            'Â·': '·',
            'Â¬': '¬',
            'Â®': '®',
            'Â¯': '¯',
            'Â°': '°',
            'Â±': '±',
            'Â²': '²',
            'Â³': '³',
            'Â´': '´',
            'Âµ': 'µ',
            'Â¶': '¶',
            'Â·': '·',
            'Â¸': '¸',
            'Â¹': '¹',
            'Âº': 'º',
            'Â»': '»',
            'Â¼': '¼',
            'Â½': '½',
            'Â¾': '¾',
            'Â¿': '¿',
            'Ã€': 'À',
            'Ã‚': 'Â',
            'Ãƒ': 'Ã',
            'Ã„': 'Ä',
            'Ã…': 'Å',
            'Ã†': 'Æ',
            'Ã‡': 'Ç',
            'Ãˆ': 'È',
            'Ã‰': 'É',
            'ÃŠ': 'Ê',
            'Ã‹': 'Ë',
            'ÃŒ': 'Ì',
            'Ã': 'Í',
            'ÃŽ': 'Î',
            'Ã': 'Ï',
            'Ã': 'Ð',
            'Ã"': 'Ó',
            'Ã"': 'Ô',
            'Ã•': 'Õ',
            'Ã–': 'Ö',
            'Ã—': '×',
            'Ã˜': 'Ø',
            'Ã™': 'Ù',
            'Ãš': 'Ú',
            'Ã›': 'Û',
            'Ãœ': 'Ü',
            'Ã': 'Ý',
            'Ãž': 'Þ',
            'ÃŸ': 'ß',
            'Ã ': 'à',
            'Ã¡': 'á',
            'Ã¢': 'â',
            'Ã£': 'ã',
            'Ã¤': 'ä',
            'Ã¥': 'å',
            'Ã¦': 'æ',
            'Ã§': 'ç',
            'Ã¨': 'è',
            'Ã©': 'é',
            'Ãª': 'ê',
            'Ã«': 'ë',
            'Ã¬': 'ì',
            'Ã­': 'í',
            'Ã®': 'î',
            'Ã¯': 'ï',
            'Ã°': 'ð',
            'Ã±': 'ñ',
            'Ã²': 'ò',
            'Ã³': 'ó',
            'Ã´': 'ô',
            'Ãµ': 'õ',
            'Ã¶': 'ö',
            'Ã·': '÷',
            'Ã¸': 'ø',
            'Ã¹': 'ù',
            'Ãº': 'ú',
            'Ã»': 'û',
            'Ã¼': 'ü',
            'Ã½': 'ý',
            'Ã¾': 'þ',
            'Ã¿': 'ÿ'
        }
        
        # Replace all occurrences
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        
        # Also fix the pattern of 'e' characters that appear when UTF-8 is misinterpreted
        if re.search(r'e[Ee]+[Vv]e[Ee]+', text):
            # This is likely a corrupted special character - use a simpler name
            parts = text.split('_')
            if len(parts) > 1:
                return parts[-1]  # Use the last part of the name
            else:
                return text.replace('e', '').replace('E', '')
        
        return text
    
    def _fix_data_encoding(self, df):
        """Fix encoding issues in dataframe string columns"""
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: self._fix_encoding(x) if isinstance(x, str) else x)
        return df
    
    def _extract_columns_from_prompt(self, prompt: str) -> Dict[str, List[str]]:
        """Extract column names mentioned in the prompt with improved accuracy"""
        columns = {
            'x': [],
            'y': [],
            'color': [],
            'size': []
        }
        
        # Convert prompt to lowercase for case-insensitive matching
        prompt_lower = prompt.lower()
        
        # First check if we have columns in the dataframe
        if not self.df.columns.size:
            return columns
        
        # First, look for explicit column assignments in the prompt
        # Examples: "x-axis: date", "y axis: count", "color by: status"
        x_match = re.search(r'x(?:-axis|\s+axis)?[\s:]+([a-zA-Z0-9_\s]+)', prompt_lower)
        y_match = re.search(r'y(?:-axis|\s+axis)?[\s:]+([a-zA-Z0-9_\s]+)', prompt_lower)
        color_match = re.search(r'colou?r(?:\s+by)?[\s:]+([a-zA-Z0-9_\s]+)', prompt_lower)
        size_match = re.search(r'size(?:\s+by)?[\s:]+([a-zA-Z0-9_\s]+)', prompt_lower)
        
        # Create a scoring function to find the best column match
        def find_best_column_match(text, available_columns):
            best_score = 0
            best_match = None
            text = text.strip().lower()
            
            # Check for exact matches first
            for col in available_columns:
                col_lower = col.lower()
                if col_lower == text:
                    return col
            
            # Check for partial matches
            for col in available_columns:
                col_lower = col.lower()
                
                # Contained match with word boundaries
                if re.search(r'\b' + re.escape(text) + r'\b', col_lower):
                    score = len(text) / len(col_lower) + 0.5  # Boost score for this type of match
                    if score > best_score:
                        best_score = score
                        best_match = col
                
                # Column name contains the text
                elif text in col_lower:
                    score = len(text) / len(col_lower)
                    if score > best_score:
                        best_score = score
                        best_match = col
                
                # Text contains the column name
                elif col_lower in text:
                    score = len(col_lower) / len(text)
                    if score > best_score:
                        best_score = score
                        best_match = col
            
            # Only return matches with reasonable confidence
            return best_match if best_score > 0.3 else None
        
        # Process explicit matches if found
        available_cols = list(self.df.columns)
        
        if x_match:
            x_col_text = x_match.group(1).strip()
            x_col = find_best_column_match(x_col_text, available_cols)
            if x_col:
                columns['x'].append(x_col)
        
        if y_match:
            y_col_text = y_match.group(1).strip()
            y_col = find_best_column_match(y_col_text, available_cols)
            if y_col:
                columns['y'].append(y_col)
        
        if color_match:
            color_col_text = color_match.group(1).strip()
            color_col = find_best_column_match(color_col_text, available_cols)
            if color_col:
                columns['color'].append(color_col)
        
        if size_match:
            size_col_text = size_match.group(1).strip()
            size_col = find_best_column_match(size_col_text, available_cols)
            if size_col:
                columns['size'].append(size_col)
        
        # Special handling for common visualization requests
        if 'pie chart' in prompt_lower or 'distribution' in prompt_lower:
            # For pie charts, look for keywords like "of X by Y" or "of X across Y"
            distribution_match = re.search(r'(?:of|by|across|for)\s+([a-zA-Z0-9_\s]+)', prompt_lower)
            if distribution_match:
                category_text = distribution_match.group(1).strip()
                category_col = find_best_column_match(category_text, available_cols)
                if category_col and not columns['x']:
                    columns['x'].append(category_col)
        
        if 'top' in prompt_lower and 'events' in prompt_lower:
            # Look for event-related columns
            event_cols = [col for col in available_cols if 'event' in col.lower()]
            if event_cols and not columns['x']:
                columns['x'].append(event_cols[0])
        
        # If explicit assignments weren't found, look for columns mentioned in the prompt
        if not any([columns['x'], columns['y'], columns['color'], columns['size']]):
            # Find all columns mentioned in the prompt
            mentioned_columns = []
            for col in available_cols:
                col_lower = col.lower()
                # Look for the column name as a whole word
                if re.search(r'\b' + re.escape(col_lower) + r'\b', prompt_lower):
                    mentioned_columns.append((col, prompt_lower.find(col_lower), 1.0))  # (column, position, exactness)
                # Also check for partial matches (but with lower exactness)
                elif col_lower in prompt_lower:
                    mentioned_columns.append((col, prompt_lower.find(col_lower), 0.5))
            
            # Sort by exactness (descending) and position (ascending)
            mentioned_columns.sort(key=lambda x: (-x[2], x[1]))
            matched_columns = [col for col, _, _ in mentioned_columns]
            
            # Infer chart type from prompt to help with column assignment
            inferred_chart = self._detect_chart_type(prompt)
            
            # Assign columns based on data types and chart context
            for col in matched_columns:
                # Skip columns already assigned
                if col in columns['x'] or col in columns['y'] or col in columns['color'] or col in columns['size']:
                    continue
                
                # Determine role based on column type and context
                if col in self.numeric_cols:
                    # For scatter plots, first numeric is x, second is y
                    if inferred_chart == 'scatter' and not columns['x'] and not any(x in self.numeric_cols for x in columns['x']):
                        columns['x'].append(col)
                    # For bar charts with a categorical x already, this is y
                    elif inferred_chart in ['bar', 'bar-grouped', 'bar-stacked'] and columns['x'] and columns['x'][0] in self.categorical_cols:
                        if not columns['y']:
                            columns['y'].append(col)
                    # Otherwise numeric columns typically go to y-axis
                    elif not columns['y']:
                        columns['y'].append(col)
                    elif 'size' in prompt_lower and not columns['size']:
                        columns['size'].append(col)
                    else:
                        columns['y'].append(col)  # Add as additional y if needed
                elif col in self.date_cols or 'date' in col.lower() or 'time' in col.lower():
                    # Date/time columns typically go to x-axis
                    if not columns['x']:
                        columns['x'].append(col)
                    elif not columns['color']:
                        columns['color'].append(col)
                else:
                    # Categorical columns go to x-axis or color
                    if not columns['x']:
                        columns['x'].append(col)
                    elif not columns['color']:
                        columns['color'].append(col)
        
        # Special handling for destination requests
        if 'destination' in prompt_lower or 'dest' in prompt_lower:
            # Look for destination-related columns
            dest_cols = [col for col in self.df.columns if any(term in col.lower() for term in ['destination', 'dest', 'to', 'arrival', 'target', 'next'])]
            if dest_cols:
                # If we found destination columns, use the first one for x-axis
                columns['x'] = [dest_cols[0]]
                # For y-axis, use count or a numeric column
                if not columns['y'] and self.numeric_cols:
                    count_cols = [col for col in self.numeric_cols if any(term in col.lower() for term in ['count', 'sum', 'total', 'amount'])]
                    if count_cols:
                        columns['y'] = [count_cols[0]]
                    else:
                        columns['y'] = [self.numeric_cols[0]]
                # If no numeric columns, create a count column
                if not columns['y']:
                    self.df['count'] = 1
                    columns['y'] = ['count']
                    self.numeric_cols.append('count')

        # If we still don't have necessary columns, make intelligent guesses
        if not columns['x'] and self.df.columns.size > 0:
            # Prefer date columns for x-axis
            date_cols = [col for col in self.df.columns if col in self.date_cols or 'date' in col.lower() or 'time' in col.lower()]
            if date_cols:
                columns['x'] = [date_cols[0]]
            # Then categorical columns
            elif self.categorical_cols:
                columns['x'] = [self.categorical_cols[0]]
            # Fall back to first column
            else:
                columns['x'] = [self.df.columns[0]]
                
        if not columns['y'] and len(self.numeric_cols) > 0:
            # For y-axis, prefer count/sum/total columns
            count_cols = [col for col in self.numeric_cols if any(term in col.lower() for term in ['count', 'sum', 'total', 'amount'])]
            if count_cols:
                columns['y'] = [count_cols[0]]
            else:
                columns['y'] = [self.numeric_cols[0]]
        
        # If we have no numeric columns but need a y-axis, create a count column
        if not columns['y'] and columns['x']:
            self.df['count'] = 1
            columns['y'] = ['count']
            self.numeric_cols.append('count')
            
        # Special handling for time-based requests
        if any(term in prompt_lower for term in ['month', 'monthly', 'per month']):
            # Look for date columns
            date_cols = [col for col in self.df.columns if col in self.date_cols or 'date' in col.lower() or 'time' in col.lower()]
            if date_cols:
                # If we found date columns, use the first one for x-axis
                date_col = date_cols[0]
                # Convert to datetime if not already
                if not pd.api.types.is_datetime64_dtype(self.df[date_col]):
                    try:
                        self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
                    except:
                        pass
                
                # Create a month column for aggregation
                month_col = f"{date_col}_month"
                self.df[month_col] = self.df[date_col].dt.to_period('M').astype(str)
                columns['x'] = [month_col]
                self.categorical_cols.append(month_col)
        
        return columns
    
    def _detect_chart_type(self, prompt: str) -> str:
        """Detect the type of chart requested in the prompt with improved accuracy"""
        prompt_lower = prompt.lower()
        
        # Look for explicit chart type requests
        if re.search(r'\b(bar|column|histogram)\b', prompt_lower):
            # Check if it's a horizontal bar chart
            if 'horizontal' in prompt_lower or 'horiz' in prompt_lower:
                return 'bar-horizontal'
            # Check if it's a grouped or stacked bar chart
            elif 'stacked' in prompt_lower:
                return 'bar-stacked'
            elif 'grouped' in prompt_lower or 'group' in prompt_lower:
                return 'bar-grouped'
            else:
                return 'bar'
        elif re.search(r'\b(line|trend|time series)\b', prompt_lower):
            return 'line'
        elif re.search(r'\b(scatter|bubble|point|correlation)\b', prompt_lower):
            return 'scatter'
        elif re.search(r'\b(pie|donut|circle|distribution|percentage)\b', prompt_lower):
            return 'pie'
        elif re.search(r'\b(box|boxplot|whisker|outlier)\b', prompt_lower):
            return 'box'
        elif re.search(r'\b(heat ?map|correlation matrix)\b', prompt_lower):
            return 'heatmap'
        elif re.search(r'\b(sunburst|hierarchy|hierarchical|tree ?map|drill down|breakdown)\b', prompt_lower):
            return 'sunburst'
        
        # Check the data structure and column types to inform chart selection
        columns_info = self._extract_columns_from_prompt(prompt)
        
        # If we have date column as x-axis, likely a line chart
        if columns_info['x'] and columns_info['x'][0] in self.date_cols:
            if 'over time' in prompt_lower or 'by date' in prompt_lower or 'trend' in prompt_lower:
                return 'line'
        
        # If few categories and talking about distribution, pie chart
        if columns_info['x'] and columns_info['x'][0] in self.categorical_cols:
            if self.df[columns_info['x'][0]].nunique() <= 10:
                if any(term in prompt_lower for term in ['proportion', 'percentage', 'share', 'distribution']):
                    return 'pie'
        
        # If comparing categories, bar chart
        if columns_info['x'] and columns_info['x'][0] in self.categorical_cols:
            if any(term in prompt_lower for term in ['compare', 'comparison', 'versus', 'vs']):
                return 'bar'
        
        # If looking at relationships between numeric variables, scatter plot
        if (columns_info['x'] and columns_info['y'] and 
            columns_info['x'][0] in self.numeric_cols and 
            columns_info['y'][0] in self.numeric_cols):
            if any(term in prompt_lower for term in ['relationship', 'correlation', 'scatter', 'against']):
                return 'scatter'
        
        # If no explicit chart type is detected, infer from context and data
        # Time series data suggests line chart
        if any(term in prompt_lower for term in ['over time', 'by date', 'by month', 'by year', 'trend']):
            return 'line'
        # Comparison suggests bar chart
        elif any(term in prompt_lower for term in ['compare', 'comparison', 'versus', 'vs']):
            return 'bar'
        # Distribution suggests histogram or box plot
        elif any(term in prompt_lower for term in ['distribution', 'spread', 'range']):
            return 'box'
        # Relationship suggests scatter plot
        elif any(term in prompt_lower for term in ['relationship', 'correlation', 'against']):
            return 'scatter'
        # Proportion suggests pie chart
        elif any(term in prompt_lower for term in ['proportion', 'percentage', 'share']):
            return 'pie'
        # Hierarchy suggests sunburst
        elif any(term in prompt_lower for term in ['hierarchy', 'breakdown', 'drill down']):
            return 'sunburst'
        else:
            # Default to bar chart if no specific type is detected
            return 'bar'
    
    def generate_visualization(self, prompt: str) -> Dict[str, Any]:
        """Generate a visualization based on the user prompt with improved accuracy"""
        try:
            print(f"Generating visualization for prompt: {prompt}")
            
            chart_type = self._detect_chart_type(prompt)
            print(f"Detected chart type: {chart_type}")
            
            columns = self._extract_columns_from_prompt(prompt)
            print(f"Extracted columns: {columns}")
            
            # Handle "top N" requests
            top_n_match = re.search(r'top\s+(\d+)', prompt.lower())
            top_n = int(top_n_match.group(1)) if top_n_match else None
            
            # Extract title from prompt or generate a descriptive one
            title_match = re.search(r'title[:\s]+([^\.]+)', prompt, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
            else:
                # Generate a more descriptive title based on the chart type and columns
                if chart_type == 'bar':
                    title = f"Distribution of {columns['y'][0] if columns['y'] else 'Count'} by {columns['x'][0] if columns['x'] else 'Category'}"
                elif chart_type == 'line':
                    title = f"Trend of {columns['y'][0] if columns['y'] else 'Value'} over {columns['x'][0] if columns['x'] else 'Time'}"
                elif chart_type == 'scatter':
                    title = f"Relationship between {columns['x'][0] if columns['x'] else 'X'} and {columns['y'][0] if columns['y'] else 'Y'}"
                elif chart_type == 'pie':
                    title = f"Distribution of {columns['y'][0] if columns['y'] else 'Values'} across {columns['x'][0] if columns['x'] else 'Categories'}"
                else:
                    title = f"Visualization of {', '.join(columns['y'])} by {', '.join(columns['x'])}"
            
            # Prepare data - handle missing values and type conversions
            df = self.df.copy()
            
            # Fix encoding issues in string columns
            df = self._fix_data_encoding(df)
            
            # Convert categorical columns to category type for better plotting
            for col in columns['x'] + columns['color']:
                if col in df.columns and col in self.categorical_cols:
                    if df[col].nunique() <= 30:  # Only convert if reasonable number of categories
                        df[col] = df[col].astype('category')
            
            # Handle missing values appropriately based on chart type
            for col in columns['x'] + columns['color']:
                if col in df.columns and df[col].dtype in ['object', 'category']:
                    if pd.api.types.is_categorical_dtype(df[col]):
                        if 'Unknown' not in df[col].cat.categories:
                            df[col] = df[col].cat.add_categories('Unknown')
                    df[col] = df[col].fillna('Unknown')
            
            for col in columns['y'] + columns['size']:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(0)
            
            # Create aggregations if needed based on the visualization type
            df_agg = None
            if chart_type in ['bar', 'bar-grouped', 'bar-stacked', 'pie', 'sunburst']:
                # For these chart types, we often want to aggregate data
                if len(columns['x']) > 0 and len(columns['y']) > 0:
                    print(f"Performing aggregation for {chart_type} chart")
                    try:
                        # Determine appropriate aggregation function
                        agg_func = 'sum'  # Default
                        if 'average' in prompt.lower() or 'mean' in prompt.lower() or 'avg' in prompt.lower():
                            agg_func = 'mean'
                        elif 'count' in prompt.lower():
                            agg_func = 'count'
                        elif 'max' in prompt.lower():
                            agg_func = 'max'
                        elif 'min' in prompt.lower():
                            agg_func = 'min'
                        
                        # Group by x (and color if available)
                        group_cols = [col for col in columns['x'] + columns['color'] if col in df.columns]
                        if group_cols:
                            if columns['y'][0] == 'count' and 'count' not in df.columns:
                                # Create a count column if it doesn't exist
                                df['count'] = 1
                            
                            # Perform aggregation
                            df_agg = df.groupby(group_cols)[columns['y']].agg(agg_func).reset_index()
                            print(f"Aggregated data shape: {df_agg.shape}")
                    except Exception as agg_err:
                        print(f"Aggregation error: {str(agg_err)}")
            
            # Use aggregated data if available, otherwise use original
            plot_df = df_agg if df_agg is not None else df
            
            # Handle top N filtering
            if top_n and columns['x'] and columns['y'] and columns['x'][0] in plot_df.columns:
                print(f"Filtering for top {top_n} values")
                # Sort by the y column and take top N
                if columns['y'][0] in plot_df.columns:
                    plot_df = plot_df.sort_values(by=columns['y'][0], ascending=False).head(top_n)
                    print(f"Filtered to top {top_n} values, data shape: {plot_df.shape}")
            
            # Limit data size for better visualization
            max_rows = 1000
            if len(plot_df) > max_rows:
                print(f"Limiting data from {len(plot_df)} to {max_rows} rows")
                if any(col in self.date_cols for col in columns['x']):
                    # For time series, sample preserving time patterns
                    date_col = next(col for col in columns['x'] if col in self.date_cols)
                    plot_df = plot_df.sort_values(by=date_col)
                    plot_df = plot_df.iloc[::max(1, len(plot_df)//max_rows)]
                else:
                    # For other charts, take a representative sample, but keep top categories
                    if len(columns['x']) > 0 and columns['x'][0] in self.categorical_cols:
                        # Get counts for categorical column
                        value_counts = plot_df[columns['x'][0]].value_counts()
                        # Keep all rows for top categories, sample the rest
                        if len(value_counts) > 10:
                            top_cats = value_counts.nlargest(10).index
                            top_df = plot_df[plot_df[columns['x'][0]].isin(top_cats)]
                            other_df = plot_df[~plot_df[columns['x'][0]].isin(top_cats)]
                            if len(other_df) > max_rows - len(top_df):
                                other_df = other_df.sample(n=max(1, max_rows-len(top_df)))
                            plot_df = pd.concat([top_df, other_df])
                    else:
                        # Simple random sample
                        plot_df = plot_df.sample(n=max_rows, random_state=42)
            
            # Log the columns being used for the visualization
            print(f"Chart columns - x: {columns['x']}, y: {columns['y']}, color: {columns['color']}")
            
            # For line charts with time data, limit to a reasonable number of lines
            if chart_type == 'line' and columns['color'] and len(columns['color']) > 0:
                color_col = columns['color'][0]
                if color_col in plot_df.columns:
                    # Count unique values in color column
                    unique_colors = plot_df[color_col].nunique()
                    # If too many unique values, limit to top N by frequency
                    if unique_colors > 10:
                        top_colors = plot_df[color_col].value_counts().nlargest(10).index
                        plot_df = plot_df[plot_df[color_col].isin(top_colors)]
            
            fig = None
            
            # Create appropriate visualization based on chart type
            if chart_type == 'bar' or chart_type == 'bar-grouped' or chart_type == 'bar-horizontal':
                # For horizontal bar charts, we need to swap x and y
                orientation = 'h' if chart_type == 'bar-horizontal' else 'v'
                
                # Create better labels for axes
                x_label = columns['x'][0].replace('_', ' ').title() if columns['x'] else "Category"
                y_label = columns['y'][0].replace('_', ' ').title() if columns['y'] else "Value"
                
                if len(columns['y']) > 1 and chart_type != 'bar-horizontal':
                    # Multiple y columns - grouped bar chart
                    fig = px.bar(
                        plot_df, 
                        x=columns['x'][0], 
                        y=columns['y'],
                        color=columns['color'][0] if columns['color'] else None,
                        barmode='group',
                        orientation=orientation,
                        labels={
                            columns['x'][0]: x_label,
                            **{col: col.replace('_', ' ').title() for col in columns['y']},
                            **{col: col.replace('_', ' ').title() for col in columns['color'] if col in plot_df.columns}
                        }
                    )
                else:
                    # Single y column - regular bar chart
                    # For horizontal bar charts, swap x and y
                    if chart_type == 'bar-horizontal':
                        fig = px.bar(
                            plot_df, 
                            x=columns['y'][0],
                            y=columns['x'][0],
                            color=columns['color'][0] if columns['color'] else None,
                            orientation=orientation,
                            labels={
                                columns['y'][0]: y_label,
                                columns['x'][0]: x_label,
                                **{col: col.replace('_', ' ').title() for col in columns['color'] if col in plot_df.columns}
                            }
                        )
                        # Sort bars if requested or for top N
                        if top_n or 'sort' in prompt.lower() or 'order' in prompt.lower():
                            fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    else:
                        fig = px.bar(
                            plot_df, 
                            x=columns['x'][0], 
                            y=columns['y'][0],
                            color=columns['color'][0] if columns['color'] else None,
                            orientation=orientation,
                            labels={
                                columns['x'][0]: x_label,
                                columns['y'][0]: y_label,
                                **{col: col.replace('_', ' ').title() for col in columns['color'] if col in plot_df.columns}
                            }
                        )
                        
                        # Sort bars if requested or for top N
                        if top_n or 'sort' in prompt.lower() or 'order' in prompt.lower():
                            if 'descending' in prompt.lower() or 'desc' in prompt.lower():
                                fig.update_layout(xaxis={'categoryorder':'total descending'})
                            else:
                                fig.update_layout(xaxis={'categoryorder':'total ascending'})
            
            elif chart_type == 'bar-stacked':
                # For stacked bar charts, we need proper aggregation
                if len(columns['x']) > 0 and len(columns['y']) > 0:
                    # If we have a color column, use it for stacking
                    stack_col = columns['color'][0] if columns['color'] else None
                    
                    # Create better labels for axes
                    x_label = columns['x'][0].replace('_', ' ').title()
                    y_label = columns['y'][0].replace('_', ' ').title() if columns['y'][0] != 'count' else 'Count'
                    
                    if stack_col:
                        # Create proper aggregation for stacked bar
                        try:
                            # Determine appropriate aggregation function
                            agg_func = 'sum'  # Default
                            if 'average' in prompt.lower() or 'mean' in prompt.lower() or 'avg' in prompt.lower():
                                agg_func = 'mean'
                            elif 'count' in prompt.lower() or 'frequency' in prompt.lower():
                                agg_func = 'count'
                            
                            # Create count column if needed
                            if agg_func == 'count' and 'count' not in df.columns:
                                df['count'] = 1
                                y_col = 'count'
                            else:
                                y_col = columns['y'][0]
                            
                            # Group by x and stack column
                            df_agg = df.pivot_table(
                                index=columns['x'][0],
                                columns=stack_col,
                                values=y_col,
                                aggfunc=agg_func,
                                fill_value=0
                            ).reset_index()
                            
                            # Melt the dataframe for plotting
                            id_vars = [columns['x'][0]]
                            value_vars = [col for col in df_agg.columns if col != columns['x'][0]]
                            plot_df = pd.melt(df_agg, id_vars=id_vars, value_vars=value_vars, 
                                            var_name=stack_col, value_name='count')
                            
                            # Update y column to use the count
                            columns['y'] = ['count']
                            
                            print(f"Created stacked bar data with shape: {plot_df.shape}")
                            
                            # Create the stacked bar chart
                            fig = px.bar(
                                plot_df, 
                                x=columns['x'][0], 
                                y='count',
                                color=stack_col,
                                barmode='stack',
                                labels={
                                    columns['x'][0]: x_label,
                                    'count': 'Frequency' if agg_func == 'count' else y_label,
                                    stack_col: stack_col.replace('_', ' ').title()
                                }
                            )
                        except Exception as stack_err:
                            print(f"Error creating stacked bar chart: {str(stack_err)}")
                            # Fall back to regular stacked bar
                            fig = px.bar(
                                plot_df, 
                                x=columns['x'][0], 
                                y=columns['y'][0],
                                color=stack_col,
                                barmode='stack',
                                labels={
                                    columns['x'][0]: x_label,
                                    columns['y'][0]: y_label,
                                    stack_col: stack_col.replace('_', ' ').title()
                                }
                            )
                    else:
                        # If no color column specified but stacked requested, try to find a suitable column
                        potential_stack_cols = [col for col in self.categorical_cols 
                                               if col != columns['x'][0] and col in df.columns 
                                               and df[col].nunique() <= 15]
                        
                        if potential_stack_cols:
                            stack_col = potential_stack_cols[0]
                            columns['color'] = [stack_col]
                            
                            # Recursively call this section with the new color column
                            return self.generate_visualization(prompt)
                        else:
                            # Fall back to regular bar chart if no suitable stacking column
                            fig = px.bar(
                                plot_df, 
                                x=columns['x'][0], 
                                y=columns['y'][0],
                                labels={
                                    columns['x'][0]: x_label,
                                    columns['y'][0]: y_label
                                }
                            )
                else:
                    return {"error": "Need both x and y columns for stacked bar chart"}
            
            elif chart_type == 'line':
                # Create better labels for axes
                x_label = columns['x'][0].replace('_', ' ').title() if columns['x'] else "Time"
                y_label = columns['y'][0].replace('_', ' ').title() if columns['y'] else "Value"
                
                # For line charts with frequency/count by time period
                if 'frequency' in prompt.lower() or 'count' in prompt.lower() or any(term in prompt.lower() for term in ['per month', 'monthly', 'per day', 'daily']):
                    try:
                        # Identify the date column
                        date_col = columns['x'][0]
                        
                        # Identify the category column (if any)
                        category_col = columns['color'][0] if columns['color'] else None
                        
                        # Determine the time period
                        if 'month' in prompt.lower():
                            period = 'M'
                            period_name = 'Month'
                        elif 'day' in prompt.lower():
                            period = 'D'
                            period_name = 'Day'
                        elif 'week' in prompt.lower():
                            period = 'W'
                            period_name = 'Week'
                        elif 'year' in prompt.lower():
                            period = 'Y'
                            period_name = 'Year'
                        else:
                            # Default to month
                            period = 'M'
                            period_name = 'Month'
                        
                        # Convert date column to datetime if needed
                        if not pd.api.types.is_datetime64_dtype(df[date_col]):
                            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                        
                        # Create period column
                        period_col = f"{date_col}_{period}"
                        df[period_col] = df[date_col].dt.to_period(period).astype(str)
                        
                        # Create count column
                        df['count'] = 1
                        
                        # Group by period and category (if any)
                        if category_col:
                            # For each category, count by time period
                            agg_df = df.groupby([period_col, category_col])['count'].sum().reset_index()
                            
                            # Limit to top 10 categories to avoid overcrowding
                            if agg_df[category_col].nunique() > 10:
                                top_cats = agg_df.groupby(category_col)['count'].sum().nlargest(10).index
                                agg_df = agg_df[agg_df[category_col].isin(top_cats)]
                            
                            fig = px.line(
                                agg_df,
                                x=period_col,
                                y='count',
                                color=category_col,
                                labels={
                                    period_col: period_name,
                                    'count': 'Count/Frequency',
                                    category_col: category_col.replace('_', ' ').title()
                                },
                                markers=True
                            )
                        else:
                            # Just count by time period
                            agg_df = df.groupby(period_col)['count'].sum().reset_index()
                            
                            fig = px.line(
                                agg_df,
                                x=period_col,
                                y='count',
                                labels={
                                    period_col: period_name,
                                    'count': 'Count/Frequency'
                                },
                                markers=True
                            )
                        
                        # Sort by time period
                        fig.update_xaxes(categoryorder='category ascending')
                        
                    except Exception as time_err:
                        print(f"Error creating time-based line chart: {str(time_err)}")
                        # Fall back to regular line chart
                        fig = px.line(
                            plot_df, 
                            x=columns['x'][0], 
                            y=columns['y'][0],
                            color=columns['color'][0] if columns['color'] else None,
                            labels={
                                columns['x'][0]: x_label,
                                columns['y'][0]: y_label,
                                **{col: col.replace('_', ' ').title() for col in columns['color'] if col in plot_df.columns}
                            },
                            markers=True
                        )
                else:
                    # Regular line chart
                    # For line charts, ensure x-axis is sorted if it's a date
                    if columns['x'][0] in self.date_cols or pd.api.types.is_datetime64_dtype(plot_df[columns['x'][0]]):
                        plot_df = plot_df.sort_values(by=columns['x'][0])
                    
                    # Check if we should connect null values
                    connect_nulls = 'connect' in prompt.lower() or 'gap' not in prompt.lower()
                    
                    # If we have a color column, limit to top 10 categories to avoid overcrowding
                    if columns['color'] and len(columns['color']) > 0:
                        color_col = columns['color'][0]
                        if color_col in plot_df.columns and plot_df[color_col].nunique() > 10:
                            # Get top 10 categories by frequency
                            top_cats = plot_df[color_col].value_counts().nlargest(10).index
                            plot_df = plot_df[plot_df[color_col].isin(top_cats)]
                    
                    # For line charts, we need to aggregate data if there are multiple values per x-value
                    if columns['x'] and columns['y']:
                        x_col = columns['x'][0]
                        y_col = columns['y'][0]
                        
                        # Check if we need to aggregate
                        if plot_df.groupby(x_col)[y_col].count().max() > 1:
                            # Determine aggregation function
                            agg_func = 'mean'  # Default for line charts
                            
                            # Group by x and color (if available)
                            group_cols = [x_col]
                            if columns['color'] and len(columns['color']) > 0:
                                group_cols.append(columns['color'][0])
                            
                            # Perform aggregation
                            plot_df = plot_df.groupby(group_cols)[y_col].agg(agg_func).reset_index()
                    
                    fig = px.line(
                        plot_df, 
                        x=columns['x'][0], 
                        y=columns['y'],
                        color=columns['color'][0] if columns['color'] else None,
                        labels={
                            columns['x'][0]: x_label,
                            **{col: col.replace('_', ' ').title() for col in columns['y']},
                            **{col: col.replace('_', ' ').title() for col in columns['color'] if col in plot_df.columns}
                        },
                        line_shape='linear',
                        render_mode='svg',  # Better for line charts
                        markers=True if len(plot_df) < 100 else False  # Only show markers for smaller datasets
                    )
                    
                    # Set appropriate connect gaps option
                    if not connect_nulls:
                        fig.update_traces(connectgaps=False)
            
            elif chart_type == 'scatter':
                # Create better labels for axes
                x_label = columns['x'][0].replace('_', ' ').title() if columns['x'] else "X"
                y_label = columns['y'][0].replace('_', ' ').title() if columns['y'] else "Y"
                
                fig = px.scatter(
                    plot_df, 
                    x=columns['x'][0], 
                    y=columns['y'][0],
                    color=columns['color'][0] if columns['color'] else None,
                    size=columns['size'][0] if columns['size'] else None,
                    labels={
                        columns['x'][0]: x_label,
                        columns['y'][0]: y_label,
                        **{col: col.replace('_', ' ').title() for col in columns['color'] if col in plot_df.columns},
                        **{col: col.replace('_', ' ').title() for col in columns['size'] if col in plot_df.columns}
                    },
                    opacity=0.7  # Add some transparency for overlapping points
                )
                
                # Add trendline if appropriate
                if 'trend' in prompt.lower() or 'regression' in prompt.lower() or 'correlation' in prompt.lower():
                    try:
                        fig.update_traces(mode='markers')
                        # Check if x is numeric for trendline
                        x_col = columns['x'][0]
                        if pd.api.types.is_numeric_dtype(plot_df[x_col]) and not pd.api.types.is_datetime64_dtype(plot_df[x_col]):
                            # Add trendline using plotly express
                            trend_fig = px.scatter(
                                plot_df, 
                                x=x_col, 
                                y=columns['y'][0],
                                trendline='ols',  # Ordinary Least Squares regression
                                trendline_color_override='red'
                            )
                            
                            # Add trendline trace to original figure
                            for trace in trend_fig.data:
                                if hasattr(trace, 'mode') and trace.mode == 'lines':
                                    trace.name = 'Trend line'
                                    trace.line.dash = 'dash'
                                    fig.add_trace(trace)
                    except Exception as trend_err:
                        print(f"Error adding trendline: {str(trend_err)}")
            
            elif chart_type == 'pie':
                # For pie charts, we need to aggregate the data if not already done
                if df_agg is None:
                    # Aggregate the data
                    if columns['x'] and columns['y']:
                        agg_df = plot_df.groupby(columns['x'][0])[columns['y'][0]].sum().reset_index()
                    else:
                        return {"error": "Need both category and value columns for pie chart"}
                else:
                    agg_df = plot_df
                
                # Limit to top categories for pie chart (too many slices is unreadable)
                if len(agg_df) > 15:
                    # Get top 14 categories by value
                    sorted_df = agg_df.sort_values(by=columns['y'][0], ascending=False)
                    top_df = sorted_df.head(14)
                    # Sum the rest as 'Other'
                    other_value = sorted_df.iloc[14:][columns['y'][0]].sum()
                    # Only add 'Other' if it's not too dominant
                    if other_value < sorted_df[columns['y'][0]].sum() * 0.5:
                        other_df = pd.DataFrame({
                            columns['x'][0]: ['Other'],
                            columns['y'][0]: [other_value]
                        })
                        agg_df = pd.concat([top_df, other_df])
                    else:
                        # If 'Other' would be too dominant, show more categories
                        agg_df = sorted_df.head(30)
                
                # Create better labels
                names_label = columns['x'][0].replace('_', ' ').title()
                values_label = columns['y'][0].replace('_', ' ').title()
                
                fig = px.pie(
                    agg_df, 
                    names=columns['x'][0], 
                    values=columns['y'][0],
                    hole=0.4 if 'donut' in prompt.lower() else 0,  # Create donut chart if requested
                    color_discrete_sequence=px.colors.qualitative.Plotly,
                    labels={
                        columns['x'][0]: names_label,
                        columns['y'][0]: values_label
                    }
                )
                
                # Improve pie chart appearance
                fig.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    sort=False  # Preserve the order from the dataframe
                )
            
            elif chart_type == 'box':
                # Create better labels for axes
                x_label = columns['x'][0].replace('_', ' ').title() if columns['x'] else "Category"
                y_label = columns['y'][0].replace('_', ' ').title() if columns['y'] else "Value"
                
                fig = px.box(
                    plot_df, 
                    x=columns['x'][0] if columns['x'] else None, 
                    y=columns['y'][0],
                    color=columns['color'][0] if columns['color'] else None,
                    labels={
                        **{col: col.replace('_', ' ').title() for col in columns['x'] if col in plot_df.columns},
                        **{col: col.replace('_', ' ').title() for col in columns['y'] if col in plot_df.columns},
                        **{col: col.replace('_', ' ').title() for col in columns['color'] if col in plot_df.columns}
                    },
                    points='outliers'  # Only show outlier points
                )
            
            elif chart_type == 'heatmap':
                # For heatmap, we need to pivot the data
                if len(columns['x']) > 0 and len(columns['y']) > 0:
                    try:
                        # If we have both x and y, use them for the pivot
                        if len(columns['color']) > 0:
                            # If we have color, use it as the pivot value
                            pivot_df = plot_df.pivot_table(
                                index=columns['x'][0],
                                columns=columns['y'][0],
                                values=columns['color'][0],
                                aggfunc='mean'
                            )
                        else:
                            # Otherwise, count occurrences
                            if 'count' not in plot_df.columns:
                                plot_df['count'] = 1
                            
                            pivot_df = plot_df.pivot_table(
                                index=columns['x'][0],
                                columns=columns['y'][0],
                                values='count',
                                aggfunc='sum'
                            )
                        
                        # Limit size of heatmap for readability
                        if pivot_df.shape[0] > 20 or pivot_df.shape[1] > 20:
                            # Take top categories by frequency
                            row_counts = plot_df[columns['x'][0]].value_counts().nlargest(20).index
                            col_counts = plot_df[columns['y'][0]].value_counts().nlargest(20).index
                            pivot_df = pivot_df.loc[
                                pivot_df.index.isin(row_counts),
                                pivot_df.columns.isin(col_counts)
                            ]
                        
                        # Create better labels
                        x_label = columns['y'][0].replace('_', ' ').title()
                        y_label = columns['x'][0].replace('_', ' ').title()
                        
                        fig = px.imshow(
                            pivot_df,
                            labels=dict(x=x_label, y=y_label, color="Value"),
                            color_continuous_scale='Viridis',
                            aspect="auto"  # Maintain aspect ratio based on shape
                        )
                        
                        # Add text annotations for clarity
                        annotations = []
                        for i, index in enumerate(pivot_df.index):
                            for j, column in enumerate(pivot_df.columns):
                                value = pivot_df.iloc[i, j]
                                if pd.notna(value):
                                    annotations.append(
                                        dict(
                                            x=column,
                                            y=index,
                                            text=str(round(value, 1)),
                                            showarrow=False,
                                            font=dict(color="white" if value > pivot_df.values.mean() else "black")
                                        )
                                    )
                        
                        fig.update_layout(annotations=annotations)
                    
                    except Exception as heatmap_err:
                        print(f"Error creating heatmap: {str(heatmap_err)}")
                        # Fallback to correlation heatmap
                        try:
                            numeric_cols = [col for col in self.numeric_cols if col in plot_df.columns]
                            if len(numeric_cols) >= 2:
                                corr_df = plot_df[numeric_cols].corr()
                                fig = px.imshow(
                                    corr_df,
                                    title="Correlation Heatmap",
                                    labels=dict(x="Features", y="Features", color="Correlation"),
                                    color_continuous_scale='RdBu_r',
                                    zmin=-1, zmax=1
                                )
                                
                                # Add correlation values as text
                                annotations = []
                                for i, x in enumerate(corr_df.columns):
                                    for j, y in enumerate(corr_df.index):
                                        annotations.append(
                                            dict(
                                                x=x,
                                                y=y,
                                                text="{:.2f}".format(corr_df.iloc[j, i]),
                                                showarrow=False,
                                                font=dict(color="white" if abs(corr_df.iloc[j, i]) > 0.5 else "black")
                                            )
                                        )
                                
                                fig.update_layout(annotations=annotations)
                        except Exception as corr_err:
                            print(f"Error creating correlation heatmap: {str(corr_err)}")
                            return {"error": "Could not create heatmap visualization"}
                else:
                    # Fallback to correlation heatmap of numeric columns
                    numeric_cols = [col for col in self.numeric_cols if col in plot_df.columns]
                    if len(numeric_cols) >= 2:
                        corr_df = plot_df[numeric_cols].corr()
                        fig = px.imshow(
                            corr_df,
                            title="Correlation Heatmap",
                            labels=dict(x="Features", y="Features", color="Correlation"),
                            color_continuous_scale='RdBu_r',
                            zmin=-1, zmax=1
                        )
                    else:
                        return {"error": "Not enough numeric columns for correlation heatmap"}
            
            elif chart_type == 'sunburst':
                # For sunburst, we need at least 2 categorical columns
                path = columns['x'] + (columns['color'] if columns['color'] else [])
                if len(path) < 2:
                    # Add more columns if needed
                    for col in self.categorical_cols:
                        if col not in path and col in plot_df.columns:
                            path.append(col)
                            if len(path) >= 3:  # Limit to 3 levels for readability
                                break
                
                # Ensure we have values
                values_col = columns['y'][0] if columns['y'] else None
                if not values_col or values_col not in plot_df.columns:
                    plot_df['count'] = 1
                    values_col = 'count'
                
                # Limit categories for better visualization
                clean_df = plot_df.copy()
                for col in path:
                    if col in clean_df.columns and clean_df[col].nunique() > 15:
                        # Keep top 14 categories and group others
                        top_cats = clean_df[col].value_counts().nlargest(14).index.tolist()
                        clean_df.loc[~clean_df[col].isin(top_cats), col] = 'Other'
                
                # Make sure all path columns actually exist in the dataframe
                valid_path = [col for col in path if col in clean_df.columns]
                if len(valid_path) >= 2:
                    # Create better labels
                    path_labels = {col: col.replace('_', ' ').title() for col in valid_path}
                    
                    fig = px.sunburst(
                        clean_df,
                        path=valid_path[:3],  # Limit to 3 levels for readability
                        values=values_col,
                        title=title,
                        color_discrete_sequence=px.colors.qualitative.Plotly,
                        labels=path_labels
                    )
                else:
                    return {"error": "Not enough categorical columns for sunburst chart"}
            
            if fig:
                # Improve overall appearance
                fig.update_layout(
                    template='plotly_white',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=40, r=40, t=60, b=40),
                    title=dict(
                        text=title,
                        x=0.5,  # Center the title
                        xanchor='center'
                    )
                )
                
                # Adjust axes for better readability
                fig.update_xaxes(title_font=dict(size=14), tickfont=dict(size=12))
                fig.update_yaxes(title_font=dict(size=14), tickfont=dict(size=12))
                
                # Better handling of categorical axes
                for axis in ['x', 'y']:
                    cols = columns[axis]
                    if cols and cols[0] in self.categorical_cols:
                        if axis == 'x':
                            # If many categories, rotate x labels for better readability
                            if plot_df[cols[0]].nunique() > 8:
                                fig.update_xaxes(tickangle=45)
                
                # Generate image with appropriate size
                img_bytes = fig.to_image(format="png", width=1000, height=600, scale=2)
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                
                print(f"Successfully generated {chart_type} visualization")
                
                return {
                    "image": f"data:image/png;base64,{img_b64}",
                    "chart_type": chart_type,
                    "title": title
                }
            else:
                print("No figure was created")
                return {"error": "Could not generate visualization"}
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating visualization: {str(e)}")
            print(error_details)
            return {"error": f"Error generating visualization: {str(e)}"}

# Test the visualization generator with sample data
if __name__ == "__main__":
    # Create sample data similar to the provided snippet
    data = {
        "RECPTCL_FID": ["USORDADZALGDAUN30050001900005", "USORDADZALGDAUN30050001900005", "USORDADZALGDAUN30050001900005", 
                        "USORDADZALGDAUN30102003900026", "FRCDGADZALGDAUN40553006010061", "FRCDGADZALGDAUN32487005010095"],
        "MAILITM_FID": ["0000420016941", "0000689914049", "0000700051000", "0031069949200", "1A02349441537", "1A09158628029"],
        "EVENT_TYPE_NM": ["Expédition d'envoi à l'étranger (EDI-reçu)"] * 6,
        "date": ["2023-07-04 05:00:00.000", "2023-07-04 05:00:00.000", "2023-07-04 05:00:00.000", 
                "2023-12-04 05:00:00.000", "2024-12-19 11:05:00.000", "2023-12-01 07:45:00.000"],
        "établissement_postal": [""] * 6,
        "EVENT_TYPE_CD": [12] * 6,
        "next_établissement_postal": ["ALGÉRIE"] * 6
    }
    
    df = pd.DataFrame(data)
    
    # Add more data for better visualization testing
    # Add more destinations
    more_destinations = ["MAROC", "TUNISIE", "FRANCE", "ESPAGNE", "ITALIE"]
    more_dates = ["2023-08-15 10:30:00.000", "2023-09-22 14:45:00.000", "2023-10-05 09:15:00.000", 
                 "2023-11-18 16:20:00.000", "2024-01-07 08:50:00.000"]
    
    for i in range(20):
        dest = more_destinations[i % len(more_destinations)]
        date = more_dates[i % len(more_dates)]
        new_row = {
            "RECPTCL_FID": f"TESTID{i:05d}",
            "MAILITM_FID": f"MAIL{i:010d}",
            "EVENT_TYPE_NM": "Expédition d'envoi à l'étranger (EDI-reçu)",
            "date": date,
            "établissement_postal": "",
            "EVENT_TYPE_CD": 12,
            "next_établissement_postal": dest
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Initialize the visualization generator
    viz_generator = VisualizationGenerator(df)
    
    # Test with different prompts
    test_prompts = [
        "Show me a bar chart of shipments by destination",
        "Create a line chart showing shipments over time",
        "Generate a pie chart of shipment distribution by destination",
        "Show the top 5 destinations in a bar chart",
        "Create a visualization of shipments by month"
    ]
    
    for prompt in test_prompts:
        print("\n" + "="*50)
        print(f"Testing prompt: {prompt}")
        result = viz_generator.generate_visualization(prompt)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Success! Generated {result['chart_type']} chart with title: {result['title']}")
            # The base64 image would be displayed in a real application
            print(f"Image data length: {len(result['image'])}")
