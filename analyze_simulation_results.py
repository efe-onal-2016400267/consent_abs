#!/usr/bin/env python3
"""
Analysis script for simulation results showing how metrics change with agent ratios.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import re

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_simulation_data():
    """Load all simulation data and extract agent ratios."""
    results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")
    configs_dir = results_dir / "configs"
    data_dir = results_dir / "data"
    
    # Find all config files
    config_files = list(configs_dir.glob("*.json"))
    
    simulation_data = []
    
    for config_file in config_files:
        # Load config
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Extract agent counts
        params = config['parameters']
        consent_first = params.get('ConsentFirstAgent_COUNT', 0)
        goal_first = params.get('GoalFirstAgent_COUNT', 0)
        fifty_fifty = params.get('FiftyFiftyAgent_COUNT', 0)
        total_agents = consent_first + goal_first + fifty_fifty
        
        # Calculate ratios
        consent_ratio = consent_first / total_agents if total_agents > 0 else 0
        goal_ratio = goal_first / total_agents if total_agents > 0 else 0
        fifty_fifty_ratio = fifty_fifty / total_agents if total_agents > 0 else 0
        
        # Find corresponding model data file
        config_name = config_file.stem
        print(f"config_name: {config_name}")
        prefix = config_name.rsplit('_', 1)[0]
        print(f"prefix: {prefix}")
        model_file = data_dir / f"{prefix}_model.csv"
        
        if model_file.exists():
            # Load model data
            model_df = pd.read_csv(model_file)
            
            # Get final values (last row)
            final_values = model_df.iloc[-1]
            
            simulation_data.append({
                'config_name': config_name,
                'consent_first_count': consent_first,
                'goal_first_count': goal_first,
                'fifty_fifty_count': fifty_fifty,
                'total_agents': total_agents,
                'accomplished_goals': final_values['Total Accomplished Goals'],
                'remaining_goals': final_values['Total Remaining Goals'],
                'violated_consents': final_values['Total Violated Consents'],
                'total_consents': final_values['Total Consents'],
                'resource_conflicts': final_values['Total Resource Conflicts'],
                'max_steps': config.get('max_steps', 1000)
            })
        else:
            print(f"Warning: Model data file not found for {config_name}")
    
    return pd.DataFrame(simulation_data)

def create_agent_ratio_analysis():
    """Create comprehensive analysis of how metrics change with agent ratios."""
    
    # Load data
    df = load_simulation_data()
    
    if df.empty:
        print("No simulation data found!")
        return
    
    # Sort by goal_first_count for consistent plotting
    df = df.sort_values('goal_first_count')
    
    print("Simulation Data Summary:")
    print(df[['config_name', 'consent_first_count', 'goal_first_count', 'fifty_fifty_count', 
              'accomplished_goals', 'remaining_goals', 'violated_consents', 'resource_conflicts']].to_string())
    
    # Create the analysis plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Simulation Results: Impact of Agent Ratios on Goal Achievement, Consent Violations, and Resource Conflicts', 
                 fontsize=16, fontweight='bold')
    
    # 1. Accomplished Goals vs Agent Ratio
    ax1 = axes[0, 0]
    ax1.plot(df['goal_first_count'], df['accomplished_goals'], 'o-', linewidth=2, markersize=8, 
             label='Accomplished Goals', color='green')
    ax1.set_xlabel('Goal-First Agent Count')
    ax1.set_ylabel('Total Accomplished Goals')
    ax1.set_title('Accomplished Goals vs Agent Ratio')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Add annotations for key points
    for i, row in df.iterrows():
        if row['goal_first_count'] in [0.0, 0.5, 1.0]:  # Key ratio points
            ax1.annotate(f'{int(row["accomplished_goals"])}', 
                        (row['goal_first_count'], row['accomplished_goals']),
                        textcoords="offset points", xytext=(0,10), ha='center')
    
    # 2. Remaining Goals vs Agent Ratio
    ax2 = axes[0, 1]
    ax2.plot(df['goal_first_count'], df['remaining_goals'], 'o-', linewidth=2, markersize=8, 
             label='Remaining Goals', color='red')
    ax2.set_xlabel('Goal-First Agent Ratio')
    ax2.set_ylabel('Total Remaining Goals')
    ax2.set_title('Remaining Goals vs Agent Ratio')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add annotations for key points
    for i, row in df.iterrows():
        if row['goal_first_count'] in [0.0, 0.5, 1.0]:  # Key ratio points
            ax2.annotate(f'{int(row["remaining_goals"])}', 
                        (row['goal_first_count'], row['remaining_goals']),
                        textcoords="offset points", xytext=(0,10), ha='center')
    
    # 3. Consent Violations vs Agent Ratio
    ax3 = axes[1, 0]
    ax3.plot(df['goal_first_count'], df['violated_consents'], 'o-', linewidth=2, markersize=8, 
             label='Consent Violations', color='orange')
    ax3.set_xlabel('Goal-First Agent Ratio')
    ax3.set_ylabel('Total Consent Violations')
    ax3.set_title('Consent Violations vs Agent Ratio')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Add annotations for key points
    for i, row in df.iterrows():
        if row['goal_first_count'] in [0.0, 0.5, 1.0]:  # Key ratio points
            ax3.annotate(f'{int(row["violated_consents"])}', 
                        (row['goal_first_count'], row['violated_consents']),
                        textcoords="offset points", xytext=(0,10), ha='center')
    
    # 4. Resource Conflicts vs Agent Ratio
    ax4 = axes[1, 1]
    ax4.plot(df['goal_first_count'], df['resource_conflicts'], 'o-', linewidth=2, markersize=8, 
             label='Resource Conflicts', color='purple')
    ax4.set_xlabel('Goal-First Agent Count')
    ax4.set_ylabel('Total Resource Conflicts')
    ax4.set_title('Resource Conflicts vs Agent Ratio')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    # Add annotations for key points
    for i, row in df.iterrows():
        if row['goal_first_count'] in [0.0, 0.5, 1.0]:  # Key ratio points
            ax4.annotate(f'{int(row["resource_conflicts"])}', 
                        (row['goal_first_count'], row['resource_conflicts']),
                        textcoords="offset points", xytext=(0,10), ha='center')
    
    plt.tight_layout()
    
    # Save the plot
    output_path = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Analysis plot saved to: {output_path}")
    
    # Show the plot
    plt.show()
    
    # Create detailed summary table
    print("\n" + "="*80)
    print("DETAILED ANALYSIS SUMMARY")
    print("="*80)
    
    summary_df = df[['goal_first_count', 'consent_first_count', 'goal_first_count', 
                     'accomplished_goals', 'remaining_goals', 'violated_consents', 'resource_conflicts']].copy()
    summary_df['goal_first_count'] = summary_df['goal_first_count'].round(2)
    summary_df['efficiency'] = (summary_df['accomplished_goals'] / 
                               (summary_df['accomplished_goals'] + summary_df['remaining_goals'])).round(3)
    summary_df['violation_rate'] = (summary_df['violated_consents'] / 
                                   summary_df['accomplished_goals']).round(3)
    summary_df['conflict_rate'] = (summary_df['resource_conflicts'] / 
                                  summary_df['accomplished_goals']).round(3)
    
    print(summary_df.to_string(index=False))
    
    # Key insights
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    
    max_accomplished_idx = df['accomplished_goals'].idxmax()
    min_remaining_idx = df['remaining_goals'].idxmin()
    min_violations_idx = df['violated_consents'].idxmin()
    min_conflicts_idx = df['resource_conflicts'].idxmin()
    
    print(f"• Maximum accomplished goals: {df.loc[max_accomplished_idx, 'accomplished_goals']} "
          f"at {df.loc[max_accomplished_idx, 'goal_first_count']:.1%} goal-first ratio")
    print(f"• Minimum remaining goals: {df.loc[min_remaining_idx, 'remaining_goals']} "
          f"at {df.loc[min_remaining_idx, 'goal_first_count']:.1%} goal-first ratio")
    print(f"• Minimum consent violations: {df.loc[min_violations_idx, 'violated_consents']} "
          f"at {df.loc[min_violations_idx, 'goal_first_count']:.1%} goal-first ratio")
    print(f"• Minimum resource conflicts: {df.loc[min_conflicts_idx, 'resource_conflicts']} "
          f"at {df.loc[min_conflicts_idx, 'goal_first_count']:.1%} goal-first ratio")
    
    # Calculate correlation coefficients
    corr_accomplished = df['goal_first_count'].corr(df['accomplished_goals'])
    corr_remaining = df['goal_first_count'].corr(df['remaining_goals'])
    corr_violations = df['goal_first_count'].corr(df['violated_consents'])
    corr_conflicts = df['goal_first_count'].corr(df['resource_conflicts'])
    
    print(f"\n• Correlation with goal-first count:")
    print(f"  - Accomplished goals: {corr_accomplished:.3f}")
    print(f"  - Remaining goals: {corr_remaining:.3f}")
    print(f"  - Consent violations: {corr_violations:.3f}")
    print(f"  - Resource conflicts: {corr_conflicts:.3f}")

if __name__ == "__main__":
    create_agent_ratio_analysis()
