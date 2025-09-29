#!/usr/bin/env python3
"""
Create HTML files to view dataframes from CSV files created by model.py
"""

import pandas as pd
import os
from pathlib import Path

def dataframe_to_html(df, title="DataFrame", filename="dataframe.html"):
    """Convert dataframe to HTML and save it"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            h1 {{ color: #333; }}
            .summary {{ background-color: #f0f8ff; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="summary">
            <p><strong>Shape:</strong> {df.shape}</p>
            <p><strong>Columns:</strong> {list(df.columns)}</p>
        </div>
        {df.to_html(classes='dataframe', table_id='dataframe', escape=False)}
    </body>
    </html>
    """
    
    with open(filename, 'w') as f:
        f.write(html_content)
    
    print(f"✅ {title} saved to {filename}")
    print(f"🌐 Open {filename} in your browser to view the data")

def load_csv_and_create_html():
    """Load CSV files created by model.py and create HTML viewers"""
    
    # Check if CSV files exist
    agent_csv_path = './base_model/results/agent_data.csv'
    model_csv_path = './base_model/results/model_data.csv'
    
    if not os.path.exists(agent_csv_path):
        print(f"❌ Agent data CSV not found at: {agent_csv_path}")
        print("💡 Make sure to run your model.py first to generate the CSV files")
        return
    
    if not os.path.exists(model_csv_path):
        print(f"❌ Model data CSV not found at: {model_csv_path}")
        print("💡 Make sure to run your model.py first to generate the CSV files")
        return
    
    print("📂 Loading CSV files...")
    
    try:
        # Load CSV files
        agent_vars = pd.read_csv(agent_csv_path, index_col=[0, 1])  # MultiIndex for Step, AgentID
        model_vars = pd.read_csv(model_csv_path, index_col=0)  # Single index for Step
        
        print(f"✅ Agent data loaded: {agent_vars.shape}")
        print(f"✅ Model data loaded: {model_vars.shape}")
        
        # Create HTML files
        dataframe_to_html(agent_vars, "Agent Data", "./base_model/results/agent_data.html")
        dataframe_to_html(model_vars, "Model Data", "./base_model/results/model_data.html")
        
        # Show summary statistics
        print(f"\n📊 DATA SUMMARY:")
        print(f"   - Total agents: {len(agent_vars.index.get_level_values('AgentID').unique())}")
        print(f"   - Total steps: {len(agent_vars.index.get_level_values('Step').unique())}")
        
        # Show last step data
        last_step = agent_vars.index.get_level_values('Step').max()
        last_step_agents = agent_vars.xs(last_step, level='Step')
        print(f"   - Last step ({last_step}) remaining goals: {last_step_agents['Remaining Goals'].sum()}")
        print(f"   - Last step ({last_step}) accomplished goals: {last_step_agents['Accomplished Goals'].sum()}")
        
        print(f"\n📁 HTML files created:")
        print(f"   - agent_data.html (open in browser)")
        print(f"   - model_data.html (open in browser)")
        
    except Exception as e:
        print(f"❌ Error loading CSV files: {e}")
        print("💡 Make sure the CSV files are properly formatted")

if __name__ == "__main__":
    load_csv_and_create_html()
