import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json
from datetime import datetime, timedelta

class PerformanceMonitor:
    def __init__(self, data_dir='data/processed'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_performance_data(self, days_back=7):
        """Load performance data from parquet files."""
        try:
            # Read all parquet files in the processed directory
            dfs = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for file in self.data_dir.glob('*.parquet'):
                df = pd.read_parquet(file)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df[df['timestamp'] >= cutoff_date]
                dfs.append(df)
            
            if not dfs:
                print("No performance data found")
                return None
            
            # Combine all data
            combined_df = pd.concat(dfs, ignore_index=True)
            return combined_df
            
        except Exception as e:
            print(f"Error loading performance data: {e}")
            return None
    
    def generate_performance_report(self, days_back=7):
        """Generate a simple performance report."""
        df = self.load_performance_data(days_back)
        if df is None:
            return
        
        print("\n" + "="*60)
        print("QUERY PERFORMANCE REPORT")
        print("="*60)
        
        # Basic statistics
        print(f"\n📊 Performance Statistics (Last {days_back} days):")
        print(f"Total queries analyzed: {len(df)}")
        print(f"Average execution time: {df['mean_exec_time'].mean():.2f}ms")
        print(f"Median execution time: {df['mean_exec_time'].median():.2f}ms")
        print(f"Max execution time: {df['mean_exec_time'].max():.2f}ms")
        
        # Top slowest queries
        print(f"\n🐌 Top 5 Slowest Queries:")
        slowest = df.nlargest(5, 'mean_exec_time')[['query', 'mean_exec_time', 'calls']]
        for idx, row in slowest.iterrows():
            query_preview = row['query'][:80] + "..." if len(row['query']) > 80 else row['query']
            print(f"  {row['mean_exec_time']:.2f}ms - {query_preview}")
        
        # Query complexity analysis
        if 'query_complexity' in df.columns:
            print(f"\n🔍 Query Complexity Analysis:")
            print(f"Average complexity: {df['query_complexity'].mean():.2f}")
            print(f"Most complex query: {df['query_complexity'].max()}")
        
        # Performance trends
        if len(df) > 1:
            df_sorted = df.sort_values('timestamp')
            print(f"\n📈 Performance Trends:")
            print(f"First query: {df_sorted['timestamp'].iloc[0]}")
            print(f"Last query: {df_sorted['timestamp'].iloc[-1]}")
            
            # Calculate trend
            if len(df_sorted) > 10:
                recent_avg = df_sorted.tail(10)['mean_exec_time'].mean()
                older_avg = df_sorted.head(10)['mean_exec_time'].mean()
                trend = "improving" if recent_avg < older_avg else "degrading"
                print(f"Performance trend: {trend}")
    
    def save_report(self, days_back=7, output_file=None):
        """Save performance report to file."""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'data/processed/performance_report_{timestamp}.txt'
        
        # Redirect print output to file
        import sys
        original_stdout = sys.stdout
        
        with open(output_file, 'w') as f:
            sys.stdout = f
            self.generate_performance_report(days_back)
            sys.stdout = original_stdout
        
        print(f"Performance report saved to: {output_file}")

def main():
    monitor = PerformanceMonitor()
    
    # Generate report for last 7 days
    monitor.generate_performance_report(days_back=7)
    
    # Save report
    monitor.save_report(days_back=7)

if __name__ == "__main__":
    main() 