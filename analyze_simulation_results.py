#!/usr/bin/env python3
"""
Analysis script for simulation results showing how metrics change with agent ratios.
Averages results across all seeds for each experiment configuration.
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

# Specify the experiment name to analyze (set to None to analyze all experiments)
experiment_name = "consent_or_goal_sensitivity_analysis"

def extract_experiment_info(config_filename):
    """Extract experiment name and configuration from config filename.
    
    Example: consent_or_goal_sensitivity_analysis_(seed_2)_seed_2:_0-1000-0_20251013_165148_config.json
    Returns: ('consent_or_goal_sensitivity_analysis', '0-1000-0', '2')
    """
    # Remove _config.json suffix
    name = config_filename.replace('_config.json', '')
    
    # Pattern: {experiment_name}_(seed_{N})_seed_{N}:_{agent_config}_{timestamp}
    # Match the experiment name (everything before _(seed_)
    match = re.match(r'(.+?)_\(seed_(\d+)\)_seed_\2:_(.+?)_(\d{8}_\d{6})$', name)
    
    if match:
        exp_name = match.group(1)
        seed = match.group(2)
        agent_config = match.group(3)
        timestamp = match.group(4)
        return exp_name, agent_config, seed
    
    return None, None, None

def load_simulation_data(experiment_name=None):
    """Load all simulation data and extract agent ratios."""
    results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")
    configs_dir = results_dir / "configs"
    data_dir = results_dir / "data"
    
    # Find all config files
    config_files = list(configs_dir.glob("*.json"))
    
    simulation_data = []
    
    for config_file in config_files:
        # Extract experiment info from filename
        exp_name, agent_config, seed = extract_experiment_info(config_file.name)
        
        # Skip if we can't parse the filename or if it doesn't match the desired experiment
        if exp_name is None:
            print(f"Warning: Could not parse filename: {config_file.name}")
            continue
        
        if experiment_name is not None and exp_name != experiment_name:
            continue
        
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
        prefix = config_name.rsplit('_', 1)[0]
        model_file = data_dir / f"{prefix}_model.csv"
        
        if model_file.exists():
            # Load model data
            model_df = pd.read_csv(model_file)

            # Calculate CI state ratios
            # Handle division by zero
            model_df["Consent Violation Ratio"] = model_df["Total Violated Consents"] / model_df["Total Consent Activations"].replace(0, np.nan)
            model_df["Consent Fulfillment Ratio"] = model_df["Total Fulfilled Consents"] / model_df["Total Consent Activations"].replace(0, np.nan)
            model_df["Consent Unrealized Ratio"] = model_df["Total Unrealized Consents"] / model_df["Total Consent Activations"].replace(0, np.nan)
            model_df["Consent Deferred Ratio"] = model_df["Total Deferred Consents"] / model_df["Total Consent Activations"].replace(0, np.nan)
            model_df["Resource Conflict Counter Goal Accomplishment Ratio"] = model_df["Total Resource Conflicts"] / model_df["Total Resource Conflict Accomplished Counter Goals"].replace(0, np.nan)
            
            # Exclude the last early_stop_steps - 1 steps before getting final values
            early_stop_steps = config.get('early_stop_steps', 0)
            if early_stop_steps > 1:
                # Exclude the last (early_stop_steps - 1) rows
                steps_to_exclude = early_stop_steps - 1
                if len(model_df) > steps_to_exclude:
                    model_df = model_df.iloc[:-steps_to_exclude]
            
            # Get final values (last row after exclusion)
            final_values = model_df.iloc[-1]
            
            simulation_data.append({
                'experiment_name': exp_name,
                'agent_config': agent_config,
                'seed': seed,
                'config_name': config_name,
                'consent_first_count': consent_first,
                'goal_first_count': goal_first,
                'fifty_fifty_count': fifty_fifty,
                'total_agents': total_agents,
                'accomplished_goals': final_values['Total Accomplished Goals'],
                'remaining_goals': final_values['Total Remaining Goals'],
                'violated_consents': final_values['Total Violated Consents'],
                'total_consents': final_values['Total Consent Activations'],
                'resource_conflicts': final_values['Total Resource Conflicts'],
                'counter_goal_accomplishments': final_values['Total Resource Conflict Accomplished Counter Goals'],
                'consent_violation_ratio': final_values['Consent Violation Ratio'],
                'consent_fulfillment_ratio': final_values['Consent Fulfillment Ratio'],
                'consent_unrealized_ratio': final_values['Consent Unrealized Ratio'],
                'consent_deferred_ratio': final_values['Consent Deferred Ratio'],
                'resource_conflict_counter_goal_accomplishment_ratio': final_values['Resource Conflict Counter Goal Accomplishment Ratio'],
                'max_steps': config.get('max_steps', 1000)
            })
        else:
            print(f"Warning: Model data file not found for {config_name}")
    
    return pd.DataFrame(simulation_data)

def create_agent_ratio_analysis(experiment_name=None):
    """Create comprehensive analysis of how metrics change with agent ratios.
    
    This function averages results across all seeds for each experiment configuration.
    """
    
    # Load data
    df = load_simulation_data(experiment_name=experiment_name)
    
    if df.empty:
        print("No simulation data found!")
        return
    
    # Group by experiment_name and agent_config, then calculate mean and std
    metrics_to_average = [
        'consent_first_count', 'goal_first_count', 'fifty_fifty_count', 'total_agents',
        'accomplished_goals', 'remaining_goals', 'violated_consents', 'total_consents',
        'resource_conflicts', 'counter_goal_accomplishments',
        'consent_violation_ratio', 'consent_fulfillment_ratio', 
        'consent_unrealized_ratio', 'consent_deferred_ratio',
        'resource_conflict_counter_goal_accomplishment_ratio'
    ]
    
    # Calculate mean and standard error for each metric
    grouped = df.groupby(['experiment_name', 'agent_config'])
    
    mean_df = grouped[metrics_to_average].mean().reset_index()
    std_df = grouped[metrics_to_average].std().reset_index()
    sem_df = grouped[metrics_to_average].sem().reset_index()  # Standard error of mean
    count_df = grouped.size().reset_index(name='num_seeds')
    
    # Merge the dataframes
    df_summary = mean_df.copy()
    for col in metrics_to_average:
        df_summary[f'{col}_std'] = std_df[col]
        df_summary[f'{col}_sem'] = sem_df[col]
    df_summary = df_summary.merge(count_df, on=['experiment_name', 'agent_config'])
    
    # Sort by goal_first_count for consistent plotting
    df_summary = df_summary.sort_values('goal_first_count')
    
    print(f"\nAnalyzing Experiment: {df_summary['experiment_name'].iloc[0]}")
    print(f"Number of seeds per configuration: {df_summary['num_seeds'].iloc[0]}")
    print("\nAveraged Simulation Data Summary:")
    print(df_summary[['agent_config', 'consent_first_count', 'goal_first_count', 'fifty_fifty_count', 
              'accomplished_goals', 'remaining_goals', 'violated_consents', 'resource_conflicts']].to_string())
    
    # Create the analysis plots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    exp_name_display = df_summary['experiment_name'].iloc[0].replace('_', ' ').title()
    fig.suptitle(f'{exp_name_display}\n(Averaged across {df_summary["num_seeds"].iloc[0]} seeds)', 
                 fontsize=16, fontweight='bold')
    
    # 1. Accomplished Goals vs Agent Ratio
    ax1 = axes[0, 0]
    ax1.errorbar(df_summary['goal_first_count'], df_summary['accomplished_goals'], 
                 yerr=df_summary['accomplished_goals_sem'], 
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Accomplished Goals', color='green')
    ax1.set_xlabel('Goal-First Agent Count', fontsize=11)
    ax1.set_ylabel('Total Accomplished Goals', fontsize=11)
    ax1.set_title('Accomplished Goals vs Agent Ratio', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 2. Remaining Goals vs Agent Ratio
    ax2 = axes[0, 1]
    ax2.errorbar(df_summary['goal_first_count'], df_summary['remaining_goals'], 
                 yerr=df_summary['remaining_goals_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Remaining Goals', color='red')
    ax2.set_xlabel('Goal-First Agent Count', fontsize=11)
    ax2.set_ylabel('Total Remaining Goals', fontsize=11)
    ax2.set_title('Remaining Goals vs Agent Ratio', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. Consent Violations vs Agent Ratio
    ax3 = axes[1, 0]
    ax3.errorbar(df_summary['goal_first_count'], df_summary['consent_violation_ratio'], 
                 yerr=df_summary['consent_violation_ratio_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Consent Violation Ratio', color='orange')
    ax3.set_xlabel('Goal-First Agent Count', fontsize=11)
    ax3.set_ylabel('Consent Violation Ratio', fontsize=11)
    ax3.set_title('Consent Violation Ratio vs Agent Ratio', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. Resource Conflicts vs Agent Ratio
    ax4 = axes[1, 1]
    ax4.errorbar(df_summary['goal_first_count'], df_summary['resource_conflicts'], 
                 yerr=df_summary['resource_conflicts_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Resource Conflicts', color='purple')
    ax4.set_xlabel('Goal-First Agent Count', fontsize=11)
    ax4.set_ylabel('Total Resource Conflicts', fontsize=11)
    ax4.set_title('Resource Conflicts vs Agent Ratio', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend()

    # 5. Counter Goal Accomplishments vs Agent Ratio
    ax5 = axes[0, 2]
    ax5.errorbar(df_summary['goal_first_count'], df_summary['counter_goal_accomplishments'], 
                 yerr=df_summary['counter_goal_accomplishments_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Counter Goal Accomplishments', color='brown')
    ax5.set_xlabel('Goal-First Agent Count', fontsize=11)
    ax5.set_ylabel('Total Counter Goal Accomplishments', fontsize=11)
    ax5.set_title('Counter Goal Accomplishments vs Agent Ratio', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.legend()

    # 6. Resource Conflicts / Counter Goal Accomplishments vs Agent Ratio
    ax6 = axes[1, 2]
    ax6.errorbar(df_summary['goal_first_count'], df_summary['resource_conflict_counter_goal_accomplishment_ratio'], 
                 yerr=df_summary['resource_conflict_counter_goal_accomplishment_ratio_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Resource Conflict / Counter Goal Ratio', color='darkblue')
    ax6.set_xlabel('Goal-First Agent Count', fontsize=11)
    ax6.set_ylabel('Resource Conflict / Counter Goal Ratio', fontsize=11)
    ax6.set_title('Resource Conflict / Counter Goal Ratio vs Agent Ratio', fontsize=12, fontweight='bold')
    ax6.grid(True, alpha=0.3)
    ax6.legend()

    plt.tight_layout()
    
    # Save the plot
    exp_name_clean = df_summary['experiment_name'].iloc[0]
    output_path = f"/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_analysis_{exp_name_clean}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nAnalysis plot saved to: {output_path}")
    
    # Show the plot
    plt.show()
    
    # Create detailed summary table
    print("\n" + "="*100)
    print("DETAILED ANALYSIS SUMMARY (AVERAGED ACROSS SEEDS)")
    print("="*100)
    
    summary_table = df_summary[['agent_config', 'consent_first_count', 'goal_first_count', 
                     'accomplished_goals', 'accomplished_goals_sem',
                     'remaining_goals', 'remaining_goals_sem',
                     'violated_consents', 'violated_consents_sem',
                     'resource_conflicts', 'resource_conflicts_sem']].copy()
    
    # Round values for readability
    for col in summary_table.columns:
        if col != 'agent_config':
            summary_table[col] = summary_table[col].round(2)
    
    summary_table['efficiency'] = (summary_table['accomplished_goals'] / 
                               (summary_table['accomplished_goals'] + summary_table['remaining_goals'])).round(3)
    
    print(summary_table.to_string(index=False))
    
    # Key insights
    print("\n" + "="*100)
    print("KEY INSIGHTS (BASED ON AVERAGED DATA)")
    print("="*100)
    
    max_accomplished_idx = df_summary['accomplished_goals'].idxmax()
    min_remaining_idx = df_summary['remaining_goals'].idxmin()
    min_violations_idx = df_summary['violated_consents'].idxmin()
    min_conflicts_idx = df_summary['resource_conflicts'].idxmin()
    
    print(f"• Maximum accomplished goals: {df_summary.loc[max_accomplished_idx, 'accomplished_goals']:.1f} "
          f"± {df_summary.loc[max_accomplished_idx, 'accomplished_goals_sem']:.1f} "
          f"(at {int(df_summary.loc[max_accomplished_idx, 'goal_first_count'])} goal-first agents)")
    print(f"• Minimum remaining goals: {df_summary.loc[min_remaining_idx, 'remaining_goals']:.1f} "
          f"± {df_summary.loc[min_remaining_idx, 'remaining_goals_sem']:.1f} "
          f"(at {int(df_summary.loc[min_remaining_idx, 'goal_first_count'])} goal-first agents)")
    print(f"• Minimum consent violations: {df_summary.loc[min_violations_idx, 'violated_consents']:.1f} "
          f"± {df_summary.loc[min_violations_idx, 'violated_consents_sem']:.1f} "
          f"(at {int(df_summary.loc[min_violations_idx, 'goal_first_count'])} goal-first agents)")
    print(f"• Minimum resource conflicts: {df_summary.loc[min_conflicts_idx, 'resource_conflicts']:.1f} "
          f"± {df_summary.loc[min_conflicts_idx, 'resource_conflicts_sem']:.1f} "
          f"(at {int(df_summary.loc[min_conflicts_idx, 'goal_first_count'])} goal-first agents)")
    
    # Calculate correlation coefficients (using averaged data)
    corr_accomplished = df_summary['goal_first_count'].corr(df_summary['accomplished_goals'])
    corr_remaining = df_summary['goal_first_count'].corr(df_summary['remaining_goals'])
    corr_violations = df_summary['goal_first_count'].corr(df_summary['violated_consents'])
    corr_conflicts = df_summary['goal_first_count'].corr(df_summary['resource_conflicts'])
    
    print(f"\n• Correlation with goal-first agent count:")
    print(f"  - Accomplished goals: {corr_accomplished:.3f}")
    print(f"  - Remaining goals: {corr_remaining:.3f}")
    print(f"  - Consent violations: {corr_violations:.3f}")
    print(f"  - Resource conflicts: {corr_conflicts:.3f}")

if __name__ == "__main__":
    create_agent_ratio_analysis(experiment_name=experiment_name)
