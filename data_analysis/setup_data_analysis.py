import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages for data analysis."""
    requirements = [
        'pandas',
        'numpy',
        'scikit-learn',
        'matplotlib',
        'seaborn',
        'pyspark',
        'pyhive',
        'impyla',
        'powerbiclient',
        'tableau-api-lib',
        'knime-python',
        'spss-python'
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")

def setup_directories():
    """Create necessary directories for data analysis."""
    directories = [
        'data/raw',
        'data/processed',
        'data/visualizations',
        'data/models',
        'notebooks',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_config_files():
    """Create configuration files for various tools."""
    configs = {
        'config/spark_config.json': {
            "spark.driver.memory": "2g",
            "spark.executor.memory": "4g",
            "spark.sql.shuffle.partitions": "200"
        },
        'config/database_config.json': {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "database": "queryiq"
            },
            "mysql": {
                "host": "localhost",
                "port": 3306,
                "database": "queryiq"
            }
        }
    }
    
    for file_path, config in configs.items():
        with open(file_path, 'w') as f:
            import json
            json.dump(config, f, indent=4)
        print(f"✓ Created config file: {file_path}")

def main():
    print("Setting up QueryIQ Data Analysis Environment...")
    install_requirements()
    setup_directories()
    create_config_files()
    print("\nSetup completed successfully! ✨")

if __name__ == "__main__":
    main() 