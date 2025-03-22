import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from powerbiclient import Report, models
import tableau_api_lib
import logging
from pathlib import Path
import json

class DashboardCreator:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Set style for visualizations
        plt.style.use('seaborn')
        sns.set_palette("husl")

    def create_performance_dashboard(self, data_path):
        """Create a comprehensive performance dashboard."""
        try:
            # Load data
            df = pd.read_parquet(data_path)
            
            # Create figure with subplots
            fig = plt.figure(figsize=(15, 10))
            
            # 1. Query Performance Over Time
            ax1 = plt.subplot(221)
            df.groupby('timestamp')['execution_time'].mean().plot(ax=ax1)
            ax1.set_title('Query Performance Over Time')
            ax1.set_xlabel('Time')
            ax1.set_ylabel('Execution Time (ms)')
            
            # 2. Query Type Distribution
            ax2 = plt.subplot(222)
            df['query_type'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax2)
            ax2.set_title('Query Type Distribution')
            
            # 3. Resource Utilization
            ax3 = plt.subplot(223)
            sns.boxplot(x='query_type', y='resource_usage', data=df, ax=ax3)
            ax3.set_title('Resource Usage by Query Type')
            ax3.set_xlabel('Query Type')
            ax3.set_ylabel('Resource Usage (%)')
            
            # 4. Optimization Impact
            ax4 = plt.subplot(224)
            sns.barplot(x='query_type', y='optimization_impact', data=df, ax=ax4)
            ax4.set_title('Optimization Impact by Query Type')
            ax4.set_xlabel('Query Type')
            ax4.set_ylabel('Performance Improvement (%)')
            
            plt.tight_layout()
            plt.savefig('data/visualizations/performance_dashboard.png')
            self.logger.info("Performance dashboard created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating performance dashboard: {str(e)}")
            raise

    def create_powerbi_report(self, data_path):
        """Create a Power BI report."""
        try:
            # Load data
            df = pd.read_parquet(data_path)
            
            # Create Power BI report
            report = Report()
            
            # Add visualizations
            report.add_visualization(
                title="Query Performance Trends",
                type="line",
                data=df.groupby('timestamp')['execution_time'].mean()
            )
            
            report.add_visualization(
                title="Query Type Distribution",
                type="pie",
                data=df['query_type'].value_counts()
            )
            
            report.add_visualization(
                title="Resource Utilization",
                type="bar",
                data=df.groupby('query_type')['resource_usage'].mean()
            )
            
            # Save report
            report.save('data/visualizations/queryiq_report.pbix')
            self.logger.info("Power BI report created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating Power BI report: {str(e)}")
            raise

    def create_tableau_workbook(self, data_path):
        """Create a Tableau workbook."""
        try:
            # Initialize Tableau API
            tableau = tableau_api_lib.TableauRestApiConnection()
            
            # Load data
            df = pd.read_parquet(data_path)
            
            # Create workbook
            workbook = tableau.workbooks.create_workbook(
                name="QueryIQ Analysis",
                project_id="default"
            )
            
            # Add data source
            datasource = workbook.add_datasource(
                name="QueryIQ Data",
                data=df
            )
            
            # Create worksheets
            workbook.create_worksheet(
                name="Performance Trends",
                datasource=datasource,
                viz_type="line"
            )
            
            workbook.create_worksheet(
                name="Query Distribution",
                datasource=datasource,
                viz_type="pie"
            )
            
            # Save workbook
            workbook.save('data/visualizations/queryiq_analysis.twb')
            self.logger.info("Tableau workbook created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating Tableau workbook: {str(e)}")
            raise

    def create_all_visualizations(self, data_path):
        """Create all visualizations."""
        try:
            self.create_performance_dashboard(data_path)
            self.create_powerbi_report(data_path)
            self.create_tableau_workbook(data_path)
            self.logger.info("All visualizations created successfully")
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {str(e)}")
            raise

def main():
    # Initialize dashboard creator
    creator = DashboardCreator()
    
    # Create all visualizations
    data_path = "data/processed/processed_data.parquet"
    creator.create_all_visualizations(data_path)

if __name__ == "__main__":
    main() 