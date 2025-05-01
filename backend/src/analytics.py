from datetime import datetime, timedelta
import pandas as pd

class LogisticsAnalytics:
    def __init__(self, df):
        self.df = df
        
    def delivery_stats(self, location=None, time_window=30):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_window)
        
        filtered = self.df[
            (self.df['date'] >= start_date) & 
            (self.df['date'] <= end_date)
        ]
        
        if location:
            filtered = filtered[filtered['établissement_postal'] == location]
            
        stats = {
            'total': filtered['MAILITM_FID'].nunique(),
            'delivered': filtered[filtered['EVENT_TYPE_NM'].str.contains('Livraison')]['MAILITM_FID'].nunique(),
            'avg_delivery_time': self._calculate_avg_delivery_time(filtered)
        }
        return stats

    def _calculate_avg_delivery_time(self, data):
        delivery_times = []
        for package_id, group in data.groupby('MAILITM_FID'):
            if 'Livraison' in group['EVENT_TYPE_NM'].values:
                start = group['date'].min()
                end = group[group['EVENT_TYPE_NM'] == 'Livraison']['date'].max()
                delivery_times.append((end - start).total_seconds() / 3600)
        return pd.Series(delivery_times).mean() if delivery_times else 0

    def detect_delays(self, threshold_days=5):  # <- Make sure colon is present
        current_time = datetime.now()
        delayed = []
        
        for package_id, group in self.df.groupby('MAILITM_FID'):
            latest_event = group.iloc[-1]
            time_diff = (current_time - latest_event['date']).days
            
            if time_diff > threshold_days and 'Livraison' not in latest_event['EVENT_TYPE_NM']:
                delayed.append({
                    'package_id': package_id,
                    'last_status': latest_event['EVENT_TYPE_NM'],
                    'days_delayed': time_diff,
                    'current_location': latest_event['établissement_postal']
                })
        
        return pd.DataFrame(delayed)

    def route_optimization(self):
        failure_analysis = self.df[self.df['EVENT_TYPE_NM'].str.contains('tentative')]
        
        return (
            failure_analysis.groupby(['établissement_postal', 'next_établissement_postal'])
            .size()
            .reset_index(name='failure_count')
            .sort_values('failure_count', ascending=False)
        )