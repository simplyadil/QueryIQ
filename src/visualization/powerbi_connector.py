import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta
import os

class PowerBIConnector:
    def __init__(self, data_dir='data/processed'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_performance_data(self):
        """Prepare query performance data for PowerBI visualization."""
        try:
            # Read all parquet files in the processed directory
            dfs = []
            for file in self.data_dir.glob('*.parquet'):
                df = pd.read_parquet(file)
                dfs.append(df)
            
            if not dfs:
                print("No performance data found")
                return None
            
            # Combine all data
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Add time-based features
            combined_df['hour'] = combined_df['timestamp'].dt.hour
            combined_df['day'] = combined_df['timestamp'].dt.day
            combined_df['month'] = combined_df['timestamp'].dt.month
            
            # Calculate performance metrics
            combined_df['performance_score'] = 1 / (combined_df['mean_exec_time'] + 1)
            
            # Save as CSV for PowerBI
            output_file = self.data_dir / 'query_performance.csv'
            combined_df.to_csv(output_file, index=False)
            
            print(f"Prepared {len(combined_df)} records for PowerBI visualization")
            return combined_df
            
        except Exception as e:
            print(f"Error preparing performance data: {e}")
            raise
    
    def create_performance_report(self):
        """Create a PowerBI report template."""
        try:
            report_template = {
                "name": "Query Performance Dashboard",
                "pages": [
                    {
                        "name": "Overview",
                        "visuals": [
                            {
                                "type": "line_chart",
                                "title": "Query Performance Over Time",
                                "x_axis": "timestamp",
                                "y_axis": "mean_exec_time",
                                "filters": ["query_type"]
                            },
                            {
                                "type": "bar_chart",
                                "title": "Top 10 Slowest Queries",
                                "x_axis": "query",
                                "y_axis": "mean_exec_time",
                                "limit": 10
                            },
                            {
                                "type": "scatter_plot",
                                "title": "Query Complexity vs Execution Time",
                                "x_axis": "query_complexity",
                                "y_axis": "mean_exec_time",
                                "color": "query_type"
                            }
                        ]
                    },
                    {
                        "name": "Optimization Analysis",
                        "visuals": [
                            {
                                "type": "table",
                                "title": "Query Optimization Opportunities",
                                "columns": [
                                    "query",
                                    "mean_exec_time",
                                    "query_complexity",
                                    "optimization_suggestions"
                                ]
                            },
                            {
                                "type": "gauge",
                                "title": "Overall Query Performance Score",
                                "value": "performance_score",
                                "target": 0.8
                            }
                        ]
                    }
                ]
            }
            
            # Save report template
            template_file = self.data_dir / 'powerbi_template.json'
            with open(template_file, 'w') as f:
                json.dump(report_template, f, indent=2)
            
            print(f"Created PowerBI report template at {template_file}")
            return report_template
            
        except Exception as e:
            print(f"Error creating performance report: {e}")
            raise
    
    def update_visualizations(self):
        """Update PowerBI visualizations with latest data."""
        try:
            # Prepare latest data
            df = self.prepare_performance_data()
            if df is None:
                return
            
            # Create report template
            report = self.create_performance_report()
            
            print("PowerBI visualizations updated successfully")
            return True
            
        except Exception as e:
            print(f"Error updating visualizations: {e}")
            raise

def main():
    connector = PowerBIConnector()
    try:
        # Update visualizations
        connector.update_visualizations()
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main() 