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
import pandasql as ps

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Specify the experiment name and date to analyze
# Set experiment_name to None to analyze all experiments
experiment_name = "goal_vs_consent_based_analysis"
experiment_date = "20251119"  # Format: YYYYMMDD
# Note: The actual data is in the directory: consent_first_vs_goal_first_full_analysis_20251013

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
        timestamp_date = match.group(4).split('_')[0]
        return exp_name, agent_config, seed, timestamp_date
    
    return None, None, None

def create_figures_directory(experiment_name, experiment_date):
    """Create figures directory for the experiment if it doesn't exist."""
    results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")
    
    # Find the experiment directory (it might have a different name than expected)
    experiment_dir = None
    for subdir in results_dir.iterdir():
        if subdir.is_dir():
            # Check if this directory contains files matching our experiment name and date
            configs_dir = subdir / "configs"
            if configs_dir.exists():
                for config_file in configs_dir.glob("*.json"):
                    exp_name, agent_config, seed, file_date = extract_experiment_info(config_file.name)
                    if exp_name == experiment_name and file_date == experiment_date:
                        experiment_dir = subdir
                        break
                if experiment_dir:
                    break
    
    if experiment_dir:
        figures_dir = experiment_dir / "figures"
        figures_dir.mkdir(exist_ok=True)
        return figures_dir
    else:
        # Fallback: create in main results directory
        figures_dir = results_dir / "figures"
        figures_dir.mkdir(exist_ok=True)
        return figures_dir

def load_simulation_data(experiment_name=None, experiment_date=None):
    """Load all simulation data and extract agent ratios."""
    results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")
    
    # Find all config files - check both main directories and experiment-specific subdirectories
    config_files = []
    
    # Check main configs directory
    main_configs_dir = results_dir / "configs"
    if main_configs_dir.exists():
        config_files.extend(list(main_configs_dir.glob("*.json")))
    
    # Check experiment-specific subdirectories
    if experiment_name and experiment_date:
        exp_subdir = results_dir / f"{experiment_name}_{experiment_date}"
        if exp_subdir.exists():
            exp_configs_dir = exp_subdir / "configs"
            if exp_configs_dir.exists():
                config_files.extend(list(exp_configs_dir.glob("*.json")))
                print(f"Found experiment-specific configs in: {exp_configs_dir}")
    
    # Also search all subdirectories for files that match the experiment name and date
    if experiment_name and experiment_date:
        for subdir in results_dir.iterdir():
            if subdir.is_dir():
                exp_configs_dir = subdir / "configs"
                if exp_configs_dir.exists():
                    # Check if any files in this directory match our criteria
                    matching_files = []
                    for config_file in exp_configs_dir.glob("*.json"):
                        exp_name, agent_config, seed, file_date = extract_experiment_info(config_file.name)
                        if exp_name == experiment_name and file_date == experiment_date:
                            matching_files.append(config_file)
                    
                    if matching_files:
                        config_files.extend(matching_files)
                        print(f"Found matching configs in subdirectory: {exp_configs_dir} ({len(matching_files)} files)")
    
    simulation_data = []
    timestamp_date = None
    
    for config_file in config_files:
        # Extract experiment info from filename
        exp_name, agent_config, seed, timestamp_date = extract_experiment_info(config_file.name)
        
        # Skip if we can't parse the filename or if it doesn't match the desired experiment
        if exp_name is None:
            print(f"Warning: Could not parse filename: {config_file.name}")
            continue
        
        if experiment_name is not None and exp_name != experiment_name:
            continue
        
        # Filter by experiment date if specified
        if experiment_date is not None and timestamp_date != experiment_date:
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
        
        # Look for data files in multiple locations
        model_file = None
        agent_file = None
        
        # List of directories to check for data files
        data_dirs_to_check = []
        
        # Check main data directory first
        main_data_dir = results_dir / "data"
        if main_data_dir.exists():
            data_dirs_to_check.append(main_data_dir)
        
        # Check experiment-specific subdirectory
        if experiment_name and experiment_date:
            exp_subdir = results_dir / f"{experiment_name}_{experiment_date}"
            if exp_subdir.exists():
                exp_data_dir = exp_subdir / "data"
                if exp_data_dir.exists():
                    data_dirs_to_check.append(exp_data_dir)
        
        # Also search all subdirectories for data files that match the experiment name and date
        if experiment_name and experiment_date:
            for subdir in results_dir.iterdir():
                if subdir.is_dir():
                    exp_data_dir = subdir / "data"
                    if exp_data_dir.exists() and exp_data_dir not in data_dirs_to_check:
                        # Check if any files in this directory match our criteria
                        # We'll check by looking for files with the same prefix as our config file
                        data_dirs_to_check.append(exp_data_dir)
        
        # Find the first directory that contains the required files
        for data_dir in data_dirs_to_check:
            model_file = data_dir / f"{prefix}_model.csv"
            agent_file = data_dir / f"{prefix}_agents.csv"
            if model_file.exists() and agent_file.exists():
                break
        
        if model_file and model_file.exists():
            # Load model data
            model_df = pd.read_csv(model_file)
            agent_df = pd.read_csv(agent_file)

            # Calculate CI state ratios
            # Handle division by zero
            model_df["Consent Violation Ratio"] = model_df["Total Violated Consents"] / model_df["Total Consent Activations"].replace(0, np.nan)
            model_df["Consent Fulfillment Ratio"] = model_df["Total Fulfilled Consents"] / model_df["Total Consent Activations"].replace(0, np.nan)
            model_df["Consent Unrealized Ratio"] = model_df["Total Unrealized Consents"] / model_df["Total Consent Activations"].replace(0, np.nan)
            model_df["Consent Deferred Ratio"] = model_df["Total Deferred Consents"] / model_df["Total Consent Activations"].replace(0, np.nan)
            model_df["Resource Conflict Counter Goal Accomplishment Ratio"] = model_df["Total Resource Conflicts"] / model_df["Total Resource Conflict Accomplished Counter Goals"].replace(0, np.nan)
            
            # Exclude the last early_stop_steps - 1 steps before getting final values
            # But here we should also check if no additional goals were really accomplished after the early stop steps.
            early_stop_steps = config.get('early_stop_steps', 0)
            if early_stop_steps > 1:
                # Exclude the last (early_stop_steps - 1) rows
                steps_to_exclude = early_stop_steps - 1
                distinct_agent_count_q = """SELECT COUNT(DISTINCT AgentID) as AGENT_COUNT FROM agent_df WHERE Step = 1"""
                distinct_agent_count = ps.sqldf(distinct_agent_count_q, locals())["AGENT_COUNT"][0]
                if len(model_df) > steps_to_exclude and model_df.iloc[-steps_to_exclude]['Total Accomplished Goals'] == model_df.iloc[-1]['Total Accomplished Goals']:
                    model_df = model_df.iloc[:-steps_to_exclude]
                    agent_df = agent_df.iloc[:-steps_to_exclude*distinct_agent_count]
                    
            
            # Get final values (last distinct_agent_count rows after exclusion)
            final_agent_values = agent_df.iloc[-distinct_agent_count:]
            
            # Calculate agent-level metrics for each agent type
            consent_first_mask = final_agent_values['Agent Persona'] == 'ConsentFirstAgent'
            goal_first_mask = final_agent_values['Agent Persona'] == 'GoalFirstAgent'
            
            # Calculate consent-related metrics from the available columns
            # Note: The CSV has different column names than expected
            avg_accomplished_goals_consent_first_agent = final_agent_values[consent_first_mask]['Accomplished Goals'].mean() if consent_first_mask.any() else 0
            avg_accomplished_goals_goal_first_agent = final_agent_values[goal_first_mask]['Accomplished Goals'].mean() if goal_first_mask.any() else 0
            avg_remaining_goals_consent_first_agent = final_agent_values[consent_first_mask]['Remaining Goals'].mean() if consent_first_mask.any() else 0
            avg_remaining_goals_goal_first_agent = final_agent_values[goal_first_mask]['Remaining Goals'].mean() if goal_first_mask.any() else 0
            avg_resource_conflicts_consent_first_agent = final_agent_values[consent_first_mask]['Resource Conflicts'].mean() if consent_first_mask.any() else 0
            avg_resource_conflicts_goal_first_agent = final_agent_values[goal_first_mask]['Resource Conflicts'].mean() if goal_first_mask.any() else 0
            avg_counter_goal_accomplishments_consent_first_agent = final_agent_values[consent_first_mask]['Counter Conflict Goal Accomplishments'].mean() if consent_first_mask.any() else 0
            avg_counter_goal_accomplishments_goal_first_agent = final_agent_values[goal_first_mask]['Counter Conflict Goal Accomplishments'].mean() if goal_first_mask.any() else 0
            
            # Calculate counter goal per resource conflict ratio by summing first, then dividing
            # This gives the aggregate ratio across all agents of each persona type
            if consent_first_mask.any():
                total_counter_goals_cf = final_agent_values[consent_first_mask]['Counter Conflict Goal Accomplishments'].sum()
                total_resource_conflicts_cf = final_agent_values[consent_first_mask]['Resource Conflicts'].sum()
                avg_counter_goal_per_resource_conflict_ratio_consent_first_agent = (total_counter_goals_cf / total_resource_conflicts_cf) if total_resource_conflicts_cf > 0 else 0
            else:
                avg_counter_goal_per_resource_conflict_ratio_consent_first_agent = 0
                
            if goal_first_mask.any():
                total_counter_goals_gf = final_agent_values[goal_first_mask]['Counter Conflict Goal Accomplishments'].sum()
                total_resource_conflicts_gf = final_agent_values[goal_first_mask]['Resource Conflicts'].sum()
                avg_counter_goal_per_resource_conflict_ratio_goal_first_agent = (total_counter_goals_gf / total_resource_conflicts_gf) if total_resource_conflicts_gf > 0 else 0
            else:
                avg_counter_goal_per_resource_conflict_ratio_goal_first_agent = 0
            
            # Calculate consent metrics from available columns
            # Separately for R (Receiver) and G (Giver) and agent type.
            total_consents_consent_first_r = final_agent_values[consent_first_mask]['Number of Consents as R'].mean() if consent_first_mask.any() else 0
            total_consents_consent_first_g = final_agent_values[consent_first_mask]['Number of Consents as G'].mean() if consent_first_mask.any() else 0
            total_consents_goal_first_r = final_agent_values[goal_first_mask]['Number of Consents as R'].mean() if goal_first_mask.any() else 0
            total_consents_goal_first_g = final_agent_values[goal_first_mask]['Number of Consents as G'].mean() if goal_first_mask.any() else 0
            violated_consents_consent_first_r = final_agent_values[consent_first_mask]['Number of Consents as R Violated'].mean() if consent_first_mask.any() else 0
            violated_consents_consent_first_g = final_agent_values[consent_first_mask]['Number of Consents as G Violated'].mean() if consent_first_mask.any() else 0
            violated_consents_goal_first_r = final_agent_values[goal_first_mask]['Number of Consents as R Violated'].mean() if goal_first_mask.any() else 0
            violated_consents_goal_first_g = final_agent_values[goal_first_mask]['Number of Consents as G Violated'].mean() if goal_first_mask.any() else 0
            
            fulfilled_consents_consent_first_r = final_agent_values[consent_first_mask]['Number of Consents as R Fulfilled'].mean() if consent_first_mask.any() else 0
            fulfilled_consents_consent_first_g = final_agent_values[consent_first_mask]['Number of Consents as G Fulfilled'].mean() if consent_first_mask.any() else 0
            fulfilled_consents_goal_first_r = final_agent_values[goal_first_mask]['Number of Consents as R Fulfilled'].mean() if goal_first_mask.any() else 0
            fulfilled_consents_goal_first_g = final_agent_values[goal_first_mask]['Number of Consents as G Fulfilled'].mean() if goal_first_mask.any() else 0
            
            # Calculate ratios (avoid division by zero)
            avg_consent_violation_ratio_consent_first_r = (violated_consents_consent_first_r / total_consents_consent_first_r) if total_consents_consent_first_r > 0 else 0
            avg_consent_violation_ratio_consent_first_g = (violated_consents_consent_first_g / total_consents_consent_first_g) if total_consents_consent_first_g > 0 else 0
            avg_consent_violation_ratio_goal_first_r = (violated_consents_goal_first_r / total_consents_goal_first_r) if total_consents_goal_first_r > 0 else 0
            avg_consent_violation_ratio_goal_first_g = (violated_consents_goal_first_g / total_consents_goal_first_g) if total_consents_goal_first_g > 0 else 0
            
            avg_consent_fulfillment_ratio_consent_first_r = (fulfilled_consents_consent_first_r / total_consents_consent_first_r) if total_consents_consent_first_r > 0 else 0
            avg_consent_fulfillment_ratio_consent_first_g = (fulfilled_consents_consent_first_g / total_consents_consent_first_g) if total_consents_consent_first_g > 0 else 0
            avg_consent_fulfillment_ratio_goal_first_r = (fulfilled_consents_goal_first_r / total_consents_goal_first_r) if total_consents_goal_first_r > 0 else 0
            avg_consent_fulfillment_ratio_goal_first_g = (fulfilled_consents_goal_first_g / total_consents_goal_first_g) if total_consents_goal_first_g > 0 else 0
        
            
            # Resource conflict counter goal accomplishment ratio (conflicts per counter goal)
            # Note: This divides averages, which is acceptable for this metric
            avg_resource_conflict_counter_goal_accomplishment_ratio_consent_first_agent = (avg_resource_conflicts_consent_first_agent / avg_counter_goal_accomplishments_consent_first_agent) if avg_counter_goal_accomplishments_consent_first_agent > 0 else 0
            avg_resource_conflict_counter_goal_accomplishment_ratio_goal_first_agent = (avg_resource_conflicts_goal_first_agent / avg_counter_goal_accomplishments_goal_first_agent) if avg_counter_goal_accomplishments_goal_first_agent > 0 else 0
            
            # Note: Counter goal per resource conflict ratio is calculated above per-agent then averaged
            
            # Calculate interaction and timing metrics
            avg_finished_step_consent_first_agent = final_agent_values[consent_first_mask]['Finished Step'].mean() if consent_first_mask.any() else 0
            avg_finished_step_goal_first_agent = final_agent_values[goal_first_mask]['Finished Step'].mean() if goal_first_mask.any() else 0
            avg_longest_idle_time_consent_first_agent = final_agent_values[consent_first_mask]['Longest Idle Time'].mean() if consent_first_mask.any() else 0
            avg_longest_idle_time_goal_first_agent = final_agent_values[goal_first_mask]['Longest Idle Time'].mean() if goal_first_mask.any() else 0
            avg_distinct_agents_interacted_r_consent_first_agent = final_agent_values[consent_first_mask]['Number of Distinct Agents Interacted as R'].mean() if consent_first_mask.any() else 0
            avg_distinct_agents_interacted_r_goal_first_agent = final_agent_values[goal_first_mask]['Number of Distinct Agents Interacted as R'].mean() if goal_first_mask.any() else 0
            avg_distinct_agents_interacted_g_consent_first_agent = final_agent_values[consent_first_mask]['Number of Distinct Agents Interacted as G'].mean() if consent_first_mask.any() else 0
            avg_distinct_agents_interacted_g_goal_first_agent = final_agent_values[goal_first_mask]['Number of Distinct Agents Interacted as G'].mean() if goal_first_mask.any() else 0
            # New: total idle time per agent
            avg_total_idle_time_consent_first_agent = final_agent_values[consent_first_mask]['Total Idle Time'].mean() if consent_first_mask.any() else 0
            avg_total_idle_time_goal_first_agent = final_agent_values[goal_first_mask]['Total Idle Time'].mean() if goal_first_mask.any() else 0
            
            # Calculate steps for this run as the last value of the Step/index column
            if not model_df.empty:
                if 'Step' in model_df.columns:
                    avg_steps_overall = int(pd.to_numeric(model_df['Step'], errors='coerce').dropna().iloc[-1])
                else:
                    first_col = model_df.columns[0]
                    avg_steps_overall = int(pd.to_numeric(model_df[first_col], errors='coerce').dropna().iloc[-1])
            else:
                avg_steps_overall = np.nan
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
                'max_steps': config.get('max_steps', 1000),
                'avg_steps_overall': avg_steps_overall,
                'avg_accomplished_goals_consent_first_agent': avg_accomplished_goals_consent_first_agent,
                'avg_accomplished_goals_goal_first_agent': avg_accomplished_goals_goal_first_agent,
                'avg_remaining_goals_consent_first_agent': avg_remaining_goals_consent_first_agent,
                'avg_remaining_goals_goal_first_agent': avg_remaining_goals_goal_first_agent,
                # R (Receiver) specific metrics
                'avg_total_consents_consent_first_r': total_consents_consent_first_r,
                'avg_total_consents_goal_first_r': total_consents_goal_first_r,
                'avg_violated_consents_consent_first_r': violated_consents_consent_first_r,
                'avg_violated_consents_goal_first_r': violated_consents_goal_first_r,
                'avg_fulfilled_consents_consent_first_r': fulfilled_consents_consent_first_r,
                'avg_fulfilled_consents_goal_first_r': fulfilled_consents_goal_first_r,
                'avg_consent_violation_ratio_consent_first_r': avg_consent_violation_ratio_consent_first_r,
                'avg_consent_violation_ratio_goal_first_r': avg_consent_violation_ratio_goal_first_r,
                'avg_consent_fulfillment_ratio_consent_first_r': avg_consent_fulfillment_ratio_consent_first_r,
                'avg_consent_fulfillment_ratio_goal_first_r': avg_consent_fulfillment_ratio_goal_first_r,
                
                # G (Giver) specific metrics
                'avg_total_consents_consent_first_g': total_consents_consent_first_g,
                'avg_total_consents_goal_first_g': total_consents_goal_first_g,
                'avg_violated_consents_consent_first_g': violated_consents_consent_first_g,
                'avg_violated_consents_goal_first_g': violated_consents_goal_first_g,
                'avg_fulfilled_consents_consent_first_g': fulfilled_consents_consent_first_g,
                'avg_fulfilled_consents_goal_first_g': fulfilled_consents_goal_first_g,
                'avg_consent_violation_ratio_consent_first_g': avg_consent_violation_ratio_consent_first_g,
                'avg_consent_violation_ratio_goal_first_g': avg_consent_violation_ratio_goal_first_g,
                'avg_consent_fulfillment_ratio_consent_first_g': avg_consent_fulfillment_ratio_consent_first_g,
                'avg_consent_fulfillment_ratio_goal_first_g': avg_consent_fulfillment_ratio_goal_first_g,
                
                # General agent metrics
                'avg_resource_conflicts_consent_first_agent': avg_resource_conflicts_consent_first_agent,
                'avg_resource_conflicts_goal_first_agent': avg_resource_conflicts_goal_first_agent,
                'avg_counter_goal_accomplishments_consent_first_agent': avg_counter_goal_accomplishments_consent_first_agent,
                'avg_counter_goal_accomplishments_goal_first_agent': avg_counter_goal_accomplishments_goal_first_agent,
                'avg_resource_conflict_counter_goal_accomplishment_ratio_consent_first_agent': avg_resource_conflict_counter_goal_accomplishment_ratio_consent_first_agent,
                'avg_resource_conflict_counter_goal_accomplishment_ratio_goal_first_agent': avg_resource_conflict_counter_goal_accomplishment_ratio_goal_first_agent,
                'avg_counter_goal_per_resource_conflict_ratio_consent_first_agent': avg_counter_goal_per_resource_conflict_ratio_consent_first_agent,
                'avg_counter_goal_per_resource_conflict_ratio_goal_first_agent': avg_counter_goal_per_resource_conflict_ratio_goal_first_agent,
                
                # Interaction and timing metrics
                'avg_finished_step_consent_first_agent': avg_finished_step_consent_first_agent,
                'avg_finished_step_goal_first_agent': avg_finished_step_goal_first_agent,
                'avg_longest_idle_time_consent_first_agent': avg_longest_idle_time_consent_first_agent,
                'avg_longest_idle_time_goal_first_agent': avg_longest_idle_time_goal_first_agent,
                'avg_distinct_agents_interacted_r_consent_first_agent': avg_distinct_agents_interacted_r_consent_first_agent,
                'avg_distinct_agents_interacted_r_goal_first_agent': avg_distinct_agents_interacted_r_goal_first_agent,
                'avg_distinct_agents_interacted_g_consent_first_agent': avg_distinct_agents_interacted_g_consent_first_agent,
                'avg_distinct_agents_interacted_g_goal_first_agent': avg_distinct_agents_interacted_g_goal_first_agent,
                # New: total idle time
                'avg_total_idle_time_consent_first_agent': avg_total_idle_time_consent_first_agent,
                'avg_total_idle_time_goal_first_agent': avg_total_idle_time_goal_first_agent,
            })
        else:
            print(f"Warning: Model data file not found for {config_name}")
    
    return pd.DataFrame(simulation_data), timestamp_date

def create_agent_ratio_analysis(experiment_name=None, experiment_date=None):
    """Create comprehensive analysis of how metrics change with agent ratios.
    
    This function averages results across all seeds for each experiment configuration.
    """
    print(f"Analyzing experiment: {experiment_name}, date: {experiment_date}")
    
    # Create figures directory
    figures_dir = create_figures_directory(experiment_name, experiment_date)
    print(f"Figures will be saved to: {figures_dir}")
    
    # Load data
    df, timestamp_date = load_simulation_data(experiment_name=experiment_name, experiment_date=experiment_date)
    
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
        'resource_conflict_counter_goal_accomplishment_ratio', 'avg_steps_overall'
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
    #exp_name_display = df_summary['experiment_name'].iloc[0].replace('_', ' ').title()
    exp_name_display = "Deontic vs Teleological Agents Comparison".title()
    fig.suptitle(f'{exp_name_display}\n(Averaged across {df_summary["num_seeds"].iloc[0]} seeds)', 
                 fontsize=16, fontweight='bold')
    
    # 1. Accomplished Goals vs Agent Ratio
    ax1 = axes[0, 0]
    ax1.errorbar(df_summary['goal_first_count'] / 1000, df_summary['accomplished_goals'], 
                 yerr=df_summary['accomplished_goals_sem'], 
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='TotalAccomplished Goals', color='green')
    ax1.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=14)
    ax1.set_ylabel('Total Accomplished Goals', fontsize=14)
    ax1.set_title('Total Accomplished Goals vs Agent Ratio', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    # 2. Remaining Goals vs Agent Ratio
    ax2 = axes[0, 1]
    ax2.errorbar(df_summary['goal_first_count'] / 1000, df_summary['remaining_goals'], 
                 yerr=df_summary['remaining_goals_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Remaining Goals', color='red')
    ax2.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=11)
    ax2.set_ylabel('Total Remaining Goals', fontsize=11)
    ax2.set_title('Remaining Goals vs Agent Ratio', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. Consent Violations vs Agent Ratio
    ax3 = axes[1, 0]
    ax3.errorbar(df_summary['goal_first_count'] / 1000, df_summary['consent_violation_ratio'], 
                 yerr=df_summary['consent_violation_ratio_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Consent Violation Ratio', color='orange')
    ax3.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=11)
    ax3.set_ylabel('Consent Violation Ratio', fontsize=11)
    ax3.set_title('Consent Violation Ratio vs Agent Ratio', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. Resource Conflicts vs Agent Ratio
    ax4 = axes[1, 1]
    ax4.errorbar(df_summary['goal_first_count'] / 1000, df_summary['resource_conflicts'], 
                 yerr=df_summary['resource_conflicts_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Resource Conflicts', color='purple')
    ax4.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=11)
    ax4.set_ylabel('Total Resource Conflicts', fontsize=11)
    ax4.set_title('Resource Conflicts vs Agent Ratio', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend()

    # 5. Counter Goal Accomplishments vs Agent Ratio
    ax5 = axes[0, 2]
    ax5.errorbar(df_summary['goal_first_count'] / 1000, df_summary['counter_goal_accomplishments'], 
                 yerr=df_summary['counter_goal_accomplishments_sem'],
                 fmt='o-', linewidth=2, markersize=8, capsize=5,
                 label='Counter Goal Accomplishments', color='brown')
    ax5.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=11)
    ax5.set_ylabel('Total Counter Goal Accomplishments', fontsize=11)
    ax5.set_title('Counter Goal Accomplishments vs Agent Ratio', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.legend()

    # 6. Dual-axis plot: Average Steps and Accomplished Goals vs Agent Ratio
    ax6 = axes[1, 2]
    
    # Create dual y-axes
    ax6_steps = ax6
    ax6_goals = ax6.twinx()
    
    # Plot average steps (left y-axis)
    line1 = ax6_steps.errorbar(df_summary['goal_first_count'] / 1000, df_summary['avg_steps_overall'], 
                               yerr=df_summary['avg_steps_overall_sem'],
                               fmt='o-', linewidth=2, markersize=8, capsize=5,
                               label='Average Steps', color='purple')
    ax6_steps.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=11)
    ax6_steps.set_ylabel('Average Steps', fontsize=11, color='purple')
    ax6_steps.tick_params(axis='y', labelcolor='purple')
    ax6_steps.grid(True, alpha=0.3)
    
    # Plot accomplished goals (right y-axis)
    line2 = ax6_goals.errorbar(df_summary['goal_first_count'] / 1000, df_summary['accomplished_goals'], 
                               yerr=df_summary['accomplished_goals_sem'],
                               fmt='s-', linewidth=2, markersize=8, capsize=5,
                               label='Accomplished Goals', color='green')
    ax6_goals.set_ylabel('Total Accomplished Goals', fontsize=11, color='green')
    ax6_goals.tick_params(axis='y', labelcolor='green')
    
    # Set title
    ax6_steps.set_title('Average Steps & Accomplished Goals vs Agent Ratio', fontsize=12, fontweight='bold')
    
    # Create combined legend
    ax6_steps.legend([line1[0], line2[0]], ['Average Simulation Length', 'Total Accomplished Goals'], loc='upper right')

    plt.tight_layout()
    
    # Save the plot
    exp_name_clean = df_summary['experiment_name'].iloc[0]
    output_path = figures_dir / f"simulation_analysis_{exp_name_clean}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nAnalysis plot saved to: {output_path}")
    
    # Show the plot
    plt.show()
    
    # NEW FIGURE: Cumulative Accomplished Goals vs Steps per Population Ratio (averaged across seeds)
    results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")

    def _find_agent_file(prefix: str):
        main_data = results_dir / "data"
        p = main_data / f"{prefix}_agents.csv"
        if p.exists():
            return p
        for sub in results_dir.iterdir():
            if sub.is_dir():
                d = sub / "data"
                q = d / f"{prefix}_agents.csv"
                if d.exists() and q.exists():
                    return q
        return None

    unique_cfgs = df.groupby(['agent_config']).agg({
        'consent_first_count': 'mean',
        'goal_first_count': 'mean'
    }).reset_index().sort_values('goal_first_count')

    n_cfg = len(unique_cfgs)
    if n_cfg > 0:
        ncols = 3
        nrows = int(np.ceil(n_cfg / ncols))
        fig_cum, axes_cum = plt.subplots(nrows, ncols, figsize=(6*ncols, 4*nrows), squeeze=False)
        fig_cum.suptitle(f'{exp_name_display} - Cumulative Accomplished Goals vs Steps by Ratio\n(Average across seeds)',
                         fontsize=16, fontweight='bold')

        for idx, (_, cfg_row) in enumerate(unique_cfgs.iterrows()):
            r = idx // ncols
            c = idx % ncols
            ax = axes_cum[r][c]
            cfg = cfg_row['agent_config']

            seed_rows = df[df['agent_config'] == cfg]
            gf_list = []  # GoalFirstAgent per-step cumulative accomplished goals (sum over agents), per seed
            cf_list = []  # ConsentFirstAgent per-step cumulative accomplished goals (sum over agents), per seed
            for _, srow in seed_rows.iterrows():
                if 'config_name' not in srow or not isinstance(srow['config_name'], str):
                    continue
                prefix = srow['config_name'].rsplit('_', 1)[0]
                afile = _find_agent_file(prefix)
                if afile is None:
                    continue
                adf = pd.read_csv(afile)
                step_col = 'Step' if 'Step' in adf.columns else adf.columns[0]
                if 'Agent Persona' not in adf.columns or 'Accomplished Goals' not in adf.columns:
                    continue
                gf = adf[adf['Agent Persona'] == 'GoalFirstAgent'].groupby(step_col)['Accomplished Goals'].mean()
                gf = gf.sort_index()
                cf = adf[adf['Agent Persona'] == 'ConsentFirstAgent'].groupby(step_col)['Accomplished Goals'].mean()
                cf = cf.sort_index()
                gf_list.append(gf)
                cf_list.append(cf)

            if not gf_list and not cf_list:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                ax.axis('off')
                continue

            if gf_list:
                all_steps = sorted(set().union(*(s.index.tolist() for s in gf_list)))
                gf_aligned = []
                for s in gf_list:
                    s = s.reindex(all_steps, method='ffill')
                    s = s.fillna(0)
                    gf_aligned.append(s)
                gf_df = pd.concat(gf_aligned, axis=1)
                gf_mean = gf_df.mean(axis=1)
                ax.plot(gf_mean.index, gf_mean.values, 'r-', label='Teleological Agent (per agent)')
            if cf_list:
                all_steps_cf = sorted(set().union(*(s.index.tolist() for s in cf_list)))
                cf_aligned = []
                for s in cf_list:
                    s = s.reindex(all_steps_cf, method='ffill')
                    s = s.fillna(0)
                    cf_aligned.append(s)
                cf_df = pd.concat(cf_aligned, axis=1)
                cf_mean = cf_df.mean(axis=1)
                ax.plot(cf_mean.index, cf_mean.values, 'g-', label='Deontic Agent (per agent)')

            ax.set_title(f"TA:{int(round(cfg_row['goal_first_count']))} / DA:{int(round(cfg_row['consent_first_count']))}")
            ax.set_xlabel('Step')
            ax.set_ylabel('Cumulative Accomplished Goals per Agent')
            ax.grid(True, alpha=0.3)
            ax.legend()

        for j in range(n_cfg, nrows*ncols):
            r = j // ncols
            c = j % ncols
            axes_cum[r][c].axis('off')

        plt.tight_layout()
        output_path_cum = figures_dir / f"agent_level_cumulative_goals_by_ratio_{exp_name_clean}.png"
        plt.savefig(output_path_cum, dpi=300, bbox_inches='tight')
        print(f"\nCumulative Accomplished Goals by Ratio plot saved to: {output_path_cum}")
        plt.show()

    
    # NEW FIGURE: Normalized (general) by steps: Resource Conflicts and Counter Goals per Step
    fig_norm_gen, axes_norm_gen = plt.subplots(1, 2, figsize=(15, 6))
    fig_norm_gen.suptitle(f'{exp_name_display} - Normalized (General) by Steps\n(Averaged across {df_summary["num_seeds"].iloc[0]} seeds)',
                          fontsize=16, fontweight='bold')

    steps_gen = pd.to_numeric(df_summary['avg_steps_overall'], errors='coerce').replace(0, np.nan)

    # G-N1. Resource Conflicts per Step (general)
    ax_gn1 = axes_norm_gen[0]
    rc_per_step = df_summary['resource_conflicts'] / steps_gen
    rc_per_step_sem = df_summary['resource_conflicts_sem'] / steps_gen
    ax_gn1.errorbar(df_summary['goal_first_count'] / 1000, rc_per_step,
                    yerr=rc_per_step_sem,
                    fmt='o-', linewidth=2, markersize=8, capsize=5,
                    label='Resource Conflicts per Step', color='purple')
    ax_gn1.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=11)
    ax_gn1.set_ylabel('Resource Conflicts per Step', fontsize=11)
    ax_gn1.set_title('Resource Conflicts per Step vs Agent Ratio', fontsize=12, fontweight='bold')
    ax_gn1.grid(True, alpha=0.3)
    ax_gn1.legend()

    # G-N2. Counter Goal Accomplishments per Step (general)
    ax_gn2 = axes_norm_gen[1]
    cg_per_step = df_summary['counter_goal_accomplishments'] / steps_gen
    cg_per_step_sem = df_summary['counter_goal_accomplishments_sem'] / steps_gen
    ax_gn2.errorbar(df_summary['goal_first_count'] / 1000, cg_per_step,
                    yerr=cg_per_step_sem,
                    fmt='o-', linewidth=2, markersize=8, capsize=5,
                    label='Counter Goal Accomplishments per Step', color='brown')
    ax_gn2.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=11)
    ax_gn2.set_ylabel('Counter Goal Accomplishments per Step', fontsize=11)
    ax_gn2.set_title('Counter Goal Accomplishments per Step vs Agent Ratio', fontsize=12, fontweight='bold')
    ax_gn2.grid(True, alpha=0.3)
    ax_gn2.legend()

    plt.tight_layout()
    output_path_norm_gen = figures_dir / f"simulation_analysis_normalized_by_steps_{exp_name_clean}.png"
    plt.savefig(output_path_norm_gen, dpi=300, bbox_inches='tight')
    print(f"\nNormalized (general) analysis plot saved to: {output_path_norm_gen}")
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

def create_agent_level_analysis(experiment_name=None, experiment_date=None):
    """Create analysis of agent-level metrics comparing ConsentFirstAgent and GoalFirstAgent.
    
    This function shows how individual agent performance varies across different configurations.
    """
    print(f"\nCreating Agent-Level Analysis for: {experiment_name}, date: {experiment_date}")
    
    # Create figures directory
    figures_dir = create_figures_directory(experiment_name, experiment_date)
    
    # Load data
    df, timestamp_date = load_simulation_data(experiment_name=experiment_name, experiment_date=experiment_date)
    
    if df.empty:
        print("No simulation data found!")
        return
    
    # Group by experiment_name and agent_config, then calculate mean and std for agent-level metrics
    agent_metrics_to_average = [
        'avg_accomplished_goals_consent_first_agent', 'avg_accomplished_goals_goal_first_agent',
        'avg_remaining_goals_consent_first_agent', 'avg_remaining_goals_goal_first_agent',
        # R (Receiver) specific metrics
        'avg_total_consents_consent_first_r', 'avg_total_consents_goal_first_r',
        'avg_violated_consents_consent_first_r', 'avg_violated_consents_goal_first_r',
        'avg_fulfilled_consents_consent_first_r', 'avg_fulfilled_consents_goal_first_r',
        'avg_consent_violation_ratio_consent_first_r', 'avg_consent_violation_ratio_goal_first_r',
        'avg_consent_fulfillment_ratio_consent_first_r', 'avg_consent_fulfillment_ratio_goal_first_r',
        # G (Giver) specific metrics
        'avg_total_consents_consent_first_g', 'avg_total_consents_goal_first_g',
        'avg_violated_consents_consent_first_g', 'avg_violated_consents_goal_first_g',
        'avg_fulfilled_consents_consent_first_g', 'avg_fulfilled_consents_goal_first_g',
        'avg_consent_violation_ratio_consent_first_g', 'avg_consent_violation_ratio_goal_first_g',
        'avg_consent_fulfillment_ratio_consent_first_g', 'avg_consent_fulfillment_ratio_goal_first_g',
        # General agent metrics
        'avg_resource_conflicts_consent_first_agent', 'avg_resource_conflicts_goal_first_agent',
        'avg_counter_goal_accomplishments_consent_first_agent', 'avg_counter_goal_accomplishments_goal_first_agent',
        'avg_resource_conflict_counter_goal_accomplishment_ratio_consent_first_agent',
        'avg_resource_conflict_counter_goal_accomplishment_ratio_goal_first_agent',
        'avg_counter_goal_per_resource_conflict_ratio_consent_first_agent',
        'avg_counter_goal_per_resource_conflict_ratio_goal_first_agent',
        'avg_total_idle_time_consent_first_agent', 'avg_total_idle_time_goal_first_agent',
        # Interaction and timing metrics
        'avg_finished_step_consent_first_agent', 'avg_finished_step_goal_first_agent',
        'avg_longest_idle_time_consent_first_agent', 'avg_longest_idle_time_goal_first_agent',
        'avg_distinct_agents_interacted_r_consent_first_agent', 'avg_distinct_agents_interacted_r_goal_first_agent',
        'avg_distinct_agents_interacted_g_consent_first_agent', 'avg_distinct_agents_interacted_g_goal_first_agent'
    ]
    
    # Calculate mean and standard error for each agent-level metric
    grouped = df.groupby(['experiment_name', 'agent_config'])
    
    mean_df = grouped[agent_metrics_to_average].mean().reset_index()
    std_df = grouped[agent_metrics_to_average].std().reset_index()
    sem_df = grouped[agent_metrics_to_average].sem().reset_index()
    count_df = grouped.size().reset_index(name='num_seeds')
    
    # Merge the dataframes
    df_agent_summary = mean_df.copy()
    for col in agent_metrics_to_average:
        df_agent_summary[f'{col}_std'] = std_df[col]
        df_agent_summary[f'{col}_sem'] = sem_df[col]
    df_agent_summary = df_agent_summary.merge(count_df, on=['experiment_name', 'agent_config'])
    
    # Add the configuration columns needed for plotting
    config_columns = ['consent_first_count', 'goal_first_count', 'fifty_fifty_count', 'total_agents', 'avg_steps_overall']
    for col in config_columns:
        if col in df.columns:
            config_mean = df.groupby(['experiment_name', 'agent_config'])[col].mean().reset_index()
            df_agent_summary = df_agent_summary.merge(config_mean, on=['experiment_name', 'agent_config'])
    
    # Sort by goal_first_count for consistent plotting
    df_agent_summary = df_agent_summary.sort_values('goal_first_count')

    # Per-series masks: keep other agent's points when one agent count is zero
    x_all = (df_agent_summary['goal_first_count'] / 1000)
    gf_mask = df_agent_summary['goal_first_count'] > 0
    cf_mask = df_agent_summary['consent_first_count'] > 0
    
    print(f"\nAgent-Level Analysis for Experiment: {df_agent_summary['experiment_name'].iloc[0]}")
    print(f"Number of seeds per configuration: {df_agent_summary['num_seeds'].iloc[0]}")
    
    # Create three separate figures for better organization
    
    # FIGURE 1: R (Receiver) specific graphs
    fig_r, axes_r = plt.subplots(2, 2, figsize=(15, 12))
    #exp_name_display = df_agent_summary['experiment_name'].iloc[0].replace('_', ' ').title()
    exp_name_display = "Deontic vs Teleological Agents Comparison".title()
    fig_r.suptitle(f'{exp_name_display} - Agent-Level Analysis: Receiver (R) Perspective\n(Averaged across {df_agent_summary["num_seeds"].iloc[0]} seeds)', 
                   fontsize=16, fontweight='bold')
    
    # R1. Violated Consents as R per Agent
    ax_r1 = axes_r[0, 0]
    ax_r1.errorbar(x_all[cf_mask], df_agent_summary['avg_violated_consents_consent_first_r'][cf_mask], 
                   yerr=df_agent_summary['avg_violated_consents_consent_first_r_sem'][cf_mask], 
                   fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (R)', color='green')
    ax_r1.errorbar(x_all[gf_mask], df_agent_summary['avg_violated_consents_goal_first_r'][gf_mask], 
                   yerr=df_agent_summary['avg_violated_consents_goal_first_r_sem'][gf_mask], 
                   fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (R)', color='red')
    ax_r1.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_r1.set_ylabel('Avg Violated Consents as R per Agent', fontsize=10)
    ax_r1.set_title('Violated Consents as Receiver per Agent Type', fontsize=11, fontweight='bold')
    ax_r1.grid(True, alpha=0.3)
    ax_r1.legend()
    
    # R2. Total Consents as R per Agent
    ax_r2 = axes_r[0, 1]
    ax_r2.errorbar(x_all[cf_mask], df_agent_summary['avg_total_consents_consent_first_r'][cf_mask], 
                   yerr=df_agent_summary['avg_total_consents_consent_first_r_sem'][cf_mask], 
                   fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (R)', color='green')
    ax_r2.errorbar(x_all[gf_mask], df_agent_summary['avg_total_consents_goal_first_r'][gf_mask], 
                   yerr=df_agent_summary['avg_total_consents_goal_first_r_sem'][gf_mask], 
                   fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (R)', color='red')
    ax_r2.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_r2.set_ylabel('Avg Total Consents as R per Agent', fontsize=10)
    ax_r2.set_title('Total Consents as Receiver per Agent Type', fontsize=11, fontweight='bold')
    ax_r2.grid(True, alpha=0.3)
    ax_r2.legend()
    
    # R3. Consent Violation Ratio as R per Agent
    ax_r3 = axes_r[1, 0]
    ax_r3.errorbar(x_all[cf_mask], df_agent_summary['avg_consent_violation_ratio_consent_first_r'][cf_mask], 
                   yerr=df_agent_summary['avg_consent_violation_ratio_consent_first_r_sem'][cf_mask], 
                   fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (R)', color='green')
    ax_r3.errorbar(x_all[gf_mask], df_agent_summary['avg_consent_violation_ratio_goal_first_r'][gf_mask], 
                   yerr=df_agent_summary['avg_consent_violation_ratio_goal_first_r_sem'][gf_mask], 
                   fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (R)', color='red')
    ax_r3.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_r3.set_ylabel('Avg Consent Violation Ratio as R per Agent', fontsize=10)
    ax_r3.set_title('Consent Violation Ratio as Receiver per Agent Type', fontsize=11, fontweight='bold')
    ax_r3.grid(True, alpha=0.3)
    ax_r3.legend()
    
    # R4. Consent Fulfillment Ratio as R per Agent
    ax_r4 = axes_r[1, 1]
    ax_r4.errorbar(x_all[cf_mask], df_agent_summary['avg_consent_fulfillment_ratio_consent_first_r'][cf_mask], 
                   yerr=df_agent_summary['avg_consent_fulfillment_ratio_consent_first_r_sem'][cf_mask], 
                   fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (R)', color='green')
    ax_r4.errorbar(x_all[gf_mask], df_agent_summary['avg_consent_fulfillment_ratio_goal_first_r'][gf_mask], 
                   yerr=df_agent_summary['avg_consent_fulfillment_ratio_goal_first_r_sem'][gf_mask], 
                   fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (R)', color='red')
    ax_r4.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_r4.set_ylabel('Avg Consent Fulfillment Ratio as R per Agent', fontsize=10)
    ax_r4.set_title('Consent Fulfillment Ratio as Receiver per Agent Type', fontsize=11, fontweight='bold')
    ax_r4.grid(True, alpha=0.3)
    ax_r4.legend()
    
    plt.tight_layout()
    
    # Save R figure
    exp_name_clean = df_agent_summary['experiment_name'].iloc[0]
    output_path_r = figures_dir / f"agent_level_analysis_R_{exp_name_clean}.png"
    plt.savefig(output_path_r, dpi=300, bbox_inches='tight')
    print(f"\nAgent-level R (Receiver) analysis plot saved to: {output_path_r}")
    plt.show()
    
    # FIGURE 2: G (Giver) specific graphs
    fig_g, axes_g = plt.subplots(2, 2, figsize=(15, 12))
    fig_g.suptitle(f'{exp_name_display} - Agent-Level Analysis: Giver (G) Perspective\n(Averaged across {df_agent_summary["num_seeds"].iloc[0]} seeds)', 
                   fontsize=16, fontweight='bold')
    
    # G1. Violated Consents as G per Agent
    ax_g1 = axes_g[0, 0]
    ax_g1.errorbar(x_all[cf_mask], df_agent_summary['avg_violated_consents_consent_first_g'][cf_mask], 
                   yerr=df_agent_summary['avg_violated_consents_consent_first_g_sem'][cf_mask], 
                   fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (G)', color='green')
    ax_g1.errorbar(x_all[gf_mask], df_agent_summary['avg_violated_consents_goal_first_g'][gf_mask], 
                   yerr=df_agent_summary['avg_violated_consents_goal_first_g_sem'][gf_mask], 
                   fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (G)', color='red')
    ax_g1.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_g1.set_ylabel('Avg Violated Consents as G per Agent', fontsize=10)
    ax_g1.set_title('Violated Consents as Giver per Agent Type', fontsize=11, fontweight='bold')
    ax_g1.grid(True, alpha=0.3)
    ax_g1.legend()
    
    # G2. Total Consents as G per Agent
    ax_g2 = axes_g[0, 1]
    ax_g2.errorbar(x_all[cf_mask], df_agent_summary['avg_total_consents_consent_first_g'][cf_mask], 
                   yerr=df_agent_summary['avg_total_consents_consent_first_g_sem'][cf_mask], 
                   fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (G)', color='green')
    ax_g2.errorbar(x_all[gf_mask], df_agent_summary['avg_total_consents_goal_first_g'][gf_mask], 
                   yerr=df_agent_summary['avg_total_consents_goal_first_g_sem'][gf_mask], 
                   fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (G)', color='red')
    ax_g2.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_g2.set_ylabel('Avg Total Consents as G per Agent', fontsize=10)
    ax_g2.set_title('Total Consents as Giver per Agent Type', fontsize=11, fontweight='bold')
    ax_g2.grid(True, alpha=0.3)
    ax_g2.legend()
    
    # G3. Consent Violation Ratio as G per Agent
    ax_g3 = axes_g[1, 0]
    ax_g3.errorbar(x_all[cf_mask], df_agent_summary['avg_consent_violation_ratio_consent_first_g'][cf_mask], 
                   yerr=df_agent_summary['avg_consent_violation_ratio_consent_first_g_sem'][cf_mask], 
                   fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (G)', color='green')
    ax_g3.errorbar(x_all[gf_mask], df_agent_summary['avg_consent_violation_ratio_goal_first_g'][gf_mask], 
                   yerr=df_agent_summary['avg_consent_violation_ratio_goal_first_g_sem'][gf_mask], 
                   fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (G)', color='red')
    ax_g3.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_g3.set_ylabel('Avg Consent Violation Ratio as G per Agent', fontsize=10)
    ax_g3.set_title('Consent Violation Ratio as Giver per Agent Type', fontsize=11, fontweight='bold')
    ax_g3.grid(True, alpha=0.3)
    ax_g3.legend()
    
    # G4. Consent Fulfillment Ratio as G per Agent
    ax_g4 = axes_g[1, 1]
    ax_g4.errorbar(x_all[cf_mask], df_agent_summary['avg_consent_fulfillment_ratio_consent_first_g'][cf_mask], 
                   yerr=df_agent_summary['avg_consent_fulfillment_ratio_consent_first_g_sem'][cf_mask], 
                   fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (G)', color='green')
    ax_g4.errorbar(x_all[gf_mask], df_agent_summary['avg_consent_fulfillment_ratio_goal_first_g'][gf_mask], 
                   yerr=df_agent_summary['avg_consent_fulfillment_ratio_goal_first_g_sem'][gf_mask], 
                   fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (G)', color='red')
    ax_g4.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_g4.set_ylabel('Avg Consent Fulfillment Ratio as G per Agent', fontsize=10)
    ax_g4.set_title('Consent Fulfillment Ratio as Giver per Agent Type', fontsize=11, fontweight='bold')
    ax_g4.grid(True, alpha=0.3)
    ax_g4.legend()
    
    plt.tight_layout()
    
    # Save G figure
    output_path_g = figures_dir / f"agent_level_analysis_G_{exp_name_clean}.png"
    plt.savefig(output_path_g, dpi=300, bbox_inches='tight')
    print(f"\nAgent-level G (Giver) analysis plot saved to: {output_path_g}")
    plt.show()
    
    # FIGURE 3: General agent-level performance metrics
    fig_gen, axes_gen = plt.subplots(2, 2, figsize=(15, 12))
    fig_gen.suptitle(f'{exp_name_display} - Agent-Level Analysis: General Performance Metrics\n(Averaged across {df_agent_summary["num_seeds"].iloc[0]} seeds)', 
                     fontsize=16, fontweight='bold')
    
    # Gen1. Accomplished Goals per Agent
    ax_gen1 = axes_gen[0, 0]
    ax_gen1.errorbar(x_all[cf_mask], df_agent_summary['avg_accomplished_goals_consent_first_agent'][cf_mask], 
                     yerr=df_agent_summary['avg_accomplished_goals_consent_first_agent_sem'][cf_mask], 
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent', color='green')
    ax_gen1.errorbar(x_all[gf_mask], df_agent_summary['avg_accomplished_goals_goal_first_agent'][gf_mask], 
                     yerr=df_agent_summary['avg_accomplished_goals_goal_first_agent_sem'][gf_mask], 
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent', color='red')
    ax_gen1.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_gen1.set_ylabel('Avg Accomplished Goals per Agent', fontsize=10)
    ax_gen1.set_title('Accomplished Goals per Agent Type', fontsize=11, fontweight='bold')
    ax_gen1.grid(True, alpha=0.3)
    ax_gen1.legend()
    
    # Gen2. Remaining Goals per Agent
    ax_gen2 = axes_gen[0, 1]
    ax_gen2.errorbar(x_all[cf_mask], df_agent_summary['avg_remaining_goals_consent_first_agent'][cf_mask], 
                     yerr=df_agent_summary['avg_remaining_goals_consent_first_agent_sem'][cf_mask], 
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent', color='green')
    ax_gen2.errorbar(x_all[gf_mask], df_agent_summary['avg_remaining_goals_goal_first_agent'][gf_mask], 
                     yerr=df_agent_summary['avg_remaining_goals_goal_first_agent_sem'][gf_mask], 
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent', color='red')
    ax_gen2.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_gen2.set_ylabel('Avg Remaining Goals per Agent', fontsize=10)
    ax_gen2.set_title('Remaining Goals per Agent Type', fontsize=11, fontweight='bold')
    ax_gen2.grid(True, alpha=0.3)
    ax_gen2.legend()
    
    # Gen3. Resource Conflicts per Agent
    ax_gen3 = axes_gen[1, 0]
    ax_gen3.errorbar(x_all[cf_mask], df_agent_summary['avg_resource_conflicts_consent_first_agent'][cf_mask], 
                     yerr=df_agent_summary['avg_resource_conflicts_consent_first_agent_sem'][cf_mask], 
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent', color='green')
    ax_gen3.errorbar(x_all[gf_mask], df_agent_summary['avg_resource_conflicts_goal_first_agent'][gf_mask], 
                     yerr=df_agent_summary['avg_resource_conflicts_goal_first_agent_sem'][gf_mask], 
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent', color='red')
    ax_gen3.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_gen3.set_ylabel('Avg Resource Conflicts per Agent', fontsize=10)
    ax_gen3.set_title('Resource Conflicts per Agent Type', fontsize=11, fontweight='bold')
    ax_gen3.grid(True, alpha=0.3)
    ax_gen3.legend()
    
    # Gen4. Counter Goal Accomplishments per Agent
    ax_gen4 = axes_gen[1, 1]
    ax_gen4.errorbar(x_all[cf_mask], df_agent_summary['avg_counter_goal_accomplishments_consent_first_agent'][cf_mask], 
                     yerr=df_agent_summary['avg_counter_goal_accomplishments_consent_first_agent_sem'][cf_mask], 
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent', color='green')
    ax_gen4.errorbar(x_all[gf_mask], df_agent_summary['avg_counter_goal_accomplishments_goal_first_agent'][gf_mask], 
                     yerr=df_agent_summary['avg_counter_goal_accomplishments_goal_first_agent_sem'][gf_mask], 
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent', color='red')
    ax_gen4.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_gen4.set_ylabel('Avg Counter Goal Accomplishments per Agent', fontsize=10)
    ax_gen4.set_title('Counter Goal Accomplishments per Agent Type', fontsize=11, fontweight='bold')
    ax_gen4.grid(True, alpha=0.3)
    ax_gen4.legend()
    
    plt.tight_layout()
    
    # Save General figure
    output_path_gen = figures_dir / f"agent_level_analysis_general_{exp_name_clean}.png"
    plt.savefig(output_path_gen, dpi=300, bbox_inches='tight')
    print(f"\nAgent-level General Performance analysis plot saved to: {output_path_gen}")
    plt.show()

    # NEW FIGURE: Total Idle Time per Agent (by persona)
    fig_idle, ax_idle = plt.subplots(1, 1, figsize=(7.5, 5))
    fig_idle.suptitle(f'{exp_name_display} - Agent-Level: Total Idle Time per Agent\n(Averaged across {df_agent_summary["num_seeds"].iloc[0]} seeds)',
                      fontsize=16, fontweight='bold')

    ax_idle.errorbar(x_all[cf_mask], df_agent_summary['avg_total_idle_time_consent_first_agent'][cf_mask],
                     yerr=df_agent_summary['avg_total_idle_time_consent_first_agent_sem'][cf_mask],
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent', color='green')
    ax_idle.errorbar(x_all[gf_mask], df_agent_summary['avg_total_idle_time_goal_first_agent'][gf_mask],
                     yerr=df_agent_summary['avg_total_idle_time_goal_first_agent_sem'][gf_mask],
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent', color='red')
    ax_idle.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_idle.set_ylabel('Avg Total Idle Time per Agent', fontsize=10)
    ax_idle.set_title('Total Idle Time per Agent Type', fontsize=11, fontweight='bold')
    ax_idle.grid(True, alpha=0.3)
    ax_idle.legend()

    plt.tight_layout()
    output_path_idle = figures_dir / f"agent_level_analysis_total_idle_time_{exp_name_clean}.png"
    plt.savefig(output_path_idle, dpi=300, bbox_inches='tight')
    print(f"\nAgent-level Total Idle Time analysis plot saved to: {output_path_idle}")
    plt.show()

    # NEW FIGURE: Total Idle Time per Agent per Step (normalized by steps)
    fig_idle_norm, ax_idle_norm = plt.subplots(1, 1, figsize=(7.5, 5))
    fig_idle_norm.suptitle(f'{exp_name_display} - Agent-Level: Total Idle Time per Step\n(Averaged across {df_agent_summary["num_seeds"].iloc[0]} seeds)',
                           fontsize=16, fontweight='bold')

    steps_idle = pd.to_numeric(df_agent_summary['avg_steps_overall'], errors='coerce').replace(0, np.nan)
    y_cf_idle = (df_agent_summary['avg_total_idle_time_consent_first_agent'] / steps_idle)
    y_gf_idle = (df_agent_summary['avg_total_idle_time_goal_first_agent'] / steps_idle)
    ax_idle_norm.plot(x_all[cf_mask], y_cf_idle[cf_mask], 'o-', linewidth=2, markersize=6, label='Deontic Agent', color='green')
    ax_idle_norm.plot(x_all[gf_mask], y_gf_idle[gf_mask], 's-', linewidth=2, markersize=6, label='Teleological Agent', color='red')
    ax_idle_norm.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_idle_norm.set_ylabel('Avg Total Idle Time per Agent per Step', fontsize=10)
    ax_idle_norm.set_title('Total Idle Time per Agent normalized by Steps', fontsize=11, fontweight='bold')
    ax_idle_norm.grid(True, alpha=0.3)
    ax_idle_norm.legend()

    plt.tight_layout()
    output_path_idle_norm = figures_dir / f"agent_level_analysis_total_idle_time_normalized_{exp_name_clean}.png"
    plt.savefig(output_path_idle_norm, dpi=300, bbox_inches='tight')
    print(f"\nAgent-level Total Idle Time (normalized) analysis plot saved to: {output_path_idle_norm}")
    plt.show()
    
    # FIGURE 5: Normalized per-agent metrics by average steps
    fig_norm, axes_norm = plt.subplots(1, 2, figsize=(15, 6))
    fig_norm.suptitle(f'{exp_name_display} - Agent-Level: Normalized by Steps\n(Averaged across {df_agent_summary["num_seeds"].iloc[0]} seeds)',
                      fontsize=16, fontweight='bold')

    # Guard against divide-by-zero and print diagnostics
    steps = pd.to_numeric(df_agent_summary['avg_steps_overall'], errors='coerce').replace(0, np.nan)
    try:
        print("[DIAG] goal_vs_consent normalized-by-steps checks:")
        print("       min steps:", steps.min())
        print("       min RC CF:", df_agent_summary['avg_resource_conflicts_consent_first_agent'].min())
        print("       min RC GF:", df_agent_summary['avg_resource_conflicts_goal_first_agent'].min())
        norm_cf_tmp = df_agent_summary['avg_resource_conflicts_consent_first_agent'] / steps
        norm_gf_tmp = df_agent_summary['avg_resource_conflicts_goal_first_agent'] / steps
        print("       min norm RC CF:", norm_cf_tmp.min(), "min norm RC GF:", norm_gf_tmp.min())
    except Exception as _e:
        pass

    # N1. Resource Conflicts per Agent per Step
    ax_n1 = axes_norm[0]
    y_cf_rc = (df_agent_summary['avg_resource_conflicts_consent_first_agent'] / steps)
    y_gf_rc = (df_agent_summary['avg_resource_conflicts_goal_first_agent'] / steps)
    ax_n1.plot(x_all[cf_mask], y_cf_rc[cf_mask], 'o-', linewidth=2, markersize=6, label='Deontic Agent', color='green')
    ax_n1.plot(x_all[gf_mask], y_gf_rc[gf_mask], 's-', linewidth=2, markersize=6, label='Teleological Agent', color='red')
    ax_n1.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_n1.set_ylabel('Avg Resource Conflicts per Agent per Step', fontsize=10)
    ax_n1.set_title('Resource Conflicts per Agent normalized by Steps', fontsize=11, fontweight='bold')
    ax_n1.grid(True, alpha=0.3)
    ax_n1.legend()

    # N2. Counter Goal Accomplishments per Agent per Step
    ax_n2 = axes_norm[1]
    y_cf_cg = (df_agent_summary['avg_counter_goal_accomplishments_consent_first_agent'] / steps)
    y_gf_cg = (df_agent_summary['avg_counter_goal_accomplishments_goal_first_agent'] / steps)
    ax_n2.plot(x_all[cf_mask], y_cf_cg[cf_mask], 'o-', linewidth=2, markersize=6, label='Deontic Agent', color='green')
    ax_n2.plot(x_all[gf_mask], y_gf_cg[gf_mask], 's-', linewidth=2, markersize=6, label='Teleological Agent', color='red')
    ax_n2.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_n2.set_ylabel('Avg Counter Goal Accomplishments per Agent per Step', fontsize=10)
    ax_n2.set_title('Counter Goal Accomplishments per Agent normalized by Steps', fontsize=11, fontweight='bold')
    ax_n2.grid(True, alpha=0.3)
    ax_n2.legend()

    plt.tight_layout()
    output_path_norm = figures_dir / f"agent_level_analysis_normalized_by_steps_{exp_name_clean}.png"
    plt.savefig(output_path_norm, dpi=300, bbox_inches='tight')
    print(f"\nAgent-level Normalized-by-Steps analysis plot saved to: {output_path_norm}")
    plt.show()
    
    # NEW FIGURE: Counter Goal Accomplishments per Resource Conflict Ratio
    fig_cg_rc, ax_cg_rc = plt.subplots(1, 1, figsize=(7.5, 5))
    fig_cg_rc.suptitle(f'{exp_name_display} - Agent-Level: Counter Goal Accomplishments per Resource Conflict\n(Averaged across {df_agent_summary["num_seeds"].iloc[0]} seeds)',
                       fontsize=16, fontweight='bold')

    ax_cg_rc.errorbar(x_all[cf_mask], df_agent_summary['avg_counter_goal_per_resource_conflict_ratio_consent_first_agent'][cf_mask],
                     yerr=df_agent_summary['avg_counter_goal_per_resource_conflict_ratio_consent_first_agent_sem'][cf_mask],
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent', color='green')
    ax_cg_rc.errorbar(x_all[gf_mask], df_agent_summary['avg_counter_goal_per_resource_conflict_ratio_goal_first_agent'][gf_mask],
                     yerr=df_agent_summary['avg_counter_goal_per_resource_conflict_ratio_goal_first_agent_sem'][gf_mask],
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent', color='red')
    ax_cg_rc.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_cg_rc.set_ylabel('Counter Goal Accomplishments per Resource Conflict', fontsize=10)
    ax_cg_rc.set_title('Counter Goal Accomplishments per Resource Conflict per Agent Type', fontsize=11, fontweight='bold')
    ax_cg_rc.grid(True, alpha=0.3)
    ax_cg_rc.legend()

    plt.tight_layout()
    output_path_cg_rc = figures_dir / f"agent_level_analysis_counter_goal_per_resource_conflict_{exp_name_clean}.png"
    plt.savefig(output_path_cg_rc, dpi=300, bbox_inches='tight')
    print(f"\nAgent-level Counter Goal per Resource Conflict analysis plot saved to: {output_path_cg_rc}")
    plt.show()
    
    # FIGURE 4: Agent interaction and timing metrics
    fig_interaction, axes_interaction = plt.subplots(2, 2, figsize=(15, 12))
    fig_interaction.suptitle(f'{exp_name_display} - Agent-Level Analysis: Interaction & Timing Metrics\n(Averaged across {df_agent_summary["num_seeds"].iloc[0]} seeds)', 
                             fontsize=16, fontweight='bold')
    
    # Calculate interaction and timing metrics
    interaction_metrics = [
        'avg_finished_step_consent_first_agent', 'avg_finished_step_goal_first_agent',
        'avg_longest_idle_time_consent_first_agent', 'avg_longest_idle_time_goal_first_agent',
        'avg_distinct_agents_interacted_r_consent_first_agent', 'avg_distinct_agents_interacted_r_goal_first_agent',
        'avg_distinct_agents_interacted_g_consent_first_agent', 'avg_distinct_agents_interacted_g_goal_first_agent'
    ]
    
    # Add these metrics to the agent_metrics_to_average list if not already present
    for metric in interaction_metrics:
        if metric not in agent_metrics_to_average:
            agent_metrics_to_average.append(metric)
    
    # Recalculate the summary with the new metrics
    grouped = df.groupby(['experiment_name', 'agent_config'])
    mean_df = grouped[agent_metrics_to_average].mean().reset_index()
    std_df = grouped[agent_metrics_to_average].std().reset_index()
    sem_df = grouped[agent_metrics_to_average].sem().reset_index()
    
    # Merge the dataframes
    df_interaction_summary = mean_df.copy()
    for col in agent_metrics_to_average:
        df_interaction_summary[f'{col}_std'] = std_df[col]
        df_interaction_summary[f'{col}_sem'] = sem_df[col]
    
    # Add the configuration columns needed for plotting
    config_columns = ['consent_first_count', 'goal_first_count', 'fifty_fifty_count', 'total_agents', 'avg_steps_overall']
    for col in config_columns:
        if col in df.columns:
            config_mean = df.groupby(['experiment_name', 'agent_config'])[col].mean().reset_index()
            df_interaction_summary = df_interaction_summary.merge(config_mean, on=['experiment_name', 'agent_config'])
    
    # Sort by goal_first_count for consistent plotting
    df_interaction_summary = df_interaction_summary.sort_values('goal_first_count')

    # Per-series masks for interaction summary
    x_all_int = (df_interaction_summary['goal_first_count'] / 1000)
    gf_mask_int = df_interaction_summary['goal_first_count'] > 0
    cf_mask_int = df_interaction_summary['consent_first_count'] > 0
    
    # Int1. Average Finished Step per Agent
    ax_int1 = axes_interaction[0, 0]
    ax_int1.errorbar(x_all_int[cf_mask_int], df_interaction_summary['avg_finished_step_consent_first_agent'][cf_mask_int], 
                     yerr=df_interaction_summary['avg_finished_step_consent_first_agent_sem'][cf_mask_int], 
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent', color='green')
    ax_int1.errorbar(x_all_int[gf_mask_int], df_interaction_summary['avg_finished_step_goal_first_agent'][gf_mask_int], 
                     yerr=df_interaction_summary['avg_finished_step_goal_first_agent_sem'][gf_mask_int], 
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent', color='red')
    ax_int1.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_int1.set_ylabel('Avg Finished Step per Agent', fontsize=10)
    ax_int1.set_title('Average Finished Step per Agent Type', fontsize=11, fontweight='bold')
    ax_int1.grid(True, alpha=0.3)
    ax_int1.legend()
    
    # Int2. Average Longest Idle Time per Agent
    ax_int2 = axes_interaction[0, 1]
    ax_int2.errorbar(x_all_int[cf_mask_int], df_interaction_summary['avg_longest_idle_time_consent_first_agent'][cf_mask_int], 
                     yerr=df_interaction_summary['avg_longest_idle_time_consent_first_agent_sem'][cf_mask_int], 
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent', color='green')
    ax_int2.errorbar(x_all_int[gf_mask_int], df_interaction_summary['avg_longest_idle_time_goal_first_agent'][gf_mask_int], 
                     yerr=df_interaction_summary['avg_longest_idle_time_goal_first_agent_sem'][gf_mask_int], 
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent', color='red')
    ax_int2.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_int2.set_ylabel('Avg Longest Idle Time per Agent', fontsize=10)
    ax_int2.set_title('Average Longest Idle Time per Agent Type', fontsize=11, fontweight='bold')
    ax_int2.grid(True, alpha=0.3)
    ax_int2.legend()
    
    # Int3. Average Distinct Agents Interacted as R per Agent
    ax_int3 = axes_interaction[1, 0]
    ax_int3.errorbar(x_all_int[cf_mask_int], df_interaction_summary['avg_distinct_agents_interacted_r_consent_first_agent'][cf_mask_int], 
                     yerr=df_interaction_summary['avg_distinct_agents_interacted_r_consent_first_agent_sem'][cf_mask_int], 
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (R)', color='green')
    ax_int3.errorbar(x_all_int[gf_mask_int], df_interaction_summary['avg_distinct_agents_interacted_r_goal_first_agent'][gf_mask_int], 
                     yerr=df_interaction_summary['avg_distinct_agents_interacted_r_goal_first_agent_sem'][gf_mask_int], 
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (R)', color='red')
    ax_int3.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_int3.set_ylabel('Avg Distinct Agents Interacted as R per Agent', fontsize=10)
    ax_int3.set_title('Average Distinct Agents Interacted as Receiver per Agent Type', fontsize=11, fontweight='bold')
    ax_int3.grid(True, alpha=0.3)
    ax_int3.legend()
    
    # Int4. Average Distinct Agents Interacted as G per Agent
    ax_int4 = axes_interaction[1, 1]
    ax_int4.errorbar(x_all_int[cf_mask_int], df_interaction_summary['avg_distinct_agents_interacted_g_consent_first_agent'][cf_mask_int], 
                     yerr=df_interaction_summary['avg_distinct_agents_interacted_g_consent_first_agent_sem'][cf_mask_int], 
                     fmt='o-', linewidth=2, markersize=6, capsize=4, label='Deontic Agent (G)', color='green')
    ax_int4.errorbar(x_all_int[gf_mask_int], df_interaction_summary['avg_distinct_agents_interacted_g_goal_first_agent'][gf_mask_int], 
                     yerr=df_interaction_summary['avg_distinct_agents_interacted_g_goal_first_agent_sem'][gf_mask_int], 
                     fmt='s-', linewidth=2, markersize=6, capsize=4, label='Teleological Agent (G)', color='red')
    ax_int4.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
    ax_int4.set_ylabel('Avg Distinct Agents Interacted as G per Agent', fontsize=10)
    ax_int4.set_title('Average Distinct Agents Interacted as Giver per Agent Type', fontsize=11, fontweight='bold')
    ax_int4.grid(True, alpha=0.3)
    ax_int4.legend()
    
    plt.tight_layout()
    
    # Save Interaction figure
    output_path_interaction = figures_dir / f"agent_level_analysis_interaction_{exp_name_clean}.png"
    plt.savefig(output_path_interaction, dpi=300, bbox_inches='tight')
    print(f"\nAgent-level Interaction & Timing analysis plot saved to: {output_path_interaction}")
    plt.show()
    
    # Create detailed agent-level summary table
    print("\n" + "="*120)
    print("AGENT-LEVEL ANALYSIS SUMMARY (AVERAGED ACROSS SEEDS)")
    print("="*120)
    
    # Create a comparison table for key metrics
    comparison_data = []
    for idx, row in df_agent_summary.iterrows():
        comparison_data.append({
            'Goal_First_Count': int(row['goal_first_count']),
            'Consent_First_Count': int(row['consent_first_count']),
            'CF_Accomplished_Goals': f"{row['avg_accomplished_goals_consent_first_agent']:.2f} ± {row['avg_accomplished_goals_consent_first_agent_sem']:.2f}",
            'GF_Accomplished_Goals': f"{row['avg_accomplished_goals_goal_first_agent']:.2f} ± {row['avg_accomplished_goals_goal_first_agent_sem']:.2f}",
            'CF_Violated_Consents_R': f"{row['avg_violated_consents_consent_first_r']:.2f} ± {row['avg_violated_consents_consent_first_r_sem']:.2f}",
            'GF_Violated_Consents_R': f"{row['avg_violated_consents_goal_first_r']:.2f} ± {row['avg_violated_consents_goal_first_r_sem']:.2f}",
            'CF_Violated_Consents_G': f"{row['avg_violated_consents_consent_first_g']:.2f} ± {row['avg_violated_consents_consent_first_g_sem']:.2f}",
            'GF_Violated_Consents_G': f"{row['avg_violated_consents_goal_first_g']:.2f} ± {row['avg_violated_consents_goal_first_g_sem']:.2f}",
            'CF_Consent_Violation_Ratio_R': f"{row['avg_consent_violation_ratio_consent_first_r']:.3f} ± {row['avg_consent_violation_ratio_consent_first_r_sem']:.3f}",
            'GF_Consent_Violation_Ratio_R': f"{row['avg_consent_violation_ratio_goal_first_r']:.3f} ± {row['avg_consent_violation_ratio_goal_first_r_sem']:.3f}",
            'CF_Resource_Conflicts': f"{row['avg_resource_conflicts_consent_first_agent']:.2f} ± {row['avg_resource_conflicts_consent_first_agent_sem']:.2f}",
            'GF_Resource_Conflicts': f"{row['avg_resource_conflicts_goal_first_agent']:.2f} ± {row['avg_resource_conflicts_goal_first_agent_sem']:.2f}"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))
    
    # Key insights for agent-level analysis
    print("\n" + "="*120)
    print("KEY AGENT-LEVEL INSIGHTS")
    print("="*120)
    
    # Find configurations with best performance for each agent type
    best_cf_accomplished_idx = df_agent_summary['avg_accomplished_goals_consent_first_agent'].idxmax()
    best_gf_accomplished_idx = df_agent_summary['avg_accomplished_goals_goal_first_agent'].idxmax()
    min_cf_violations_r_idx = df_agent_summary['avg_violated_consents_consent_first_r'].idxmin()
    min_gf_violations_r_idx = df_agent_summary['avg_violated_consents_goal_first_r'].idxmin()
    min_cf_violations_g_idx = df_agent_summary['avg_violated_consents_consent_first_g'].idxmin()
    min_gf_violations_g_idx = df_agent_summary['avg_violated_consents_goal_first_g'].idxmin()
    
    print(f"• Best Consent-First Agent performance: {df_agent_summary.loc[best_cf_accomplished_idx, 'avg_accomplished_goals_consent_first_agent']:.2f} "
          f"± {df_agent_summary.loc[best_cf_accomplished_idx, 'avg_accomplished_goals_consent_first_agent_sem']:.2f} goals "
          f"(at {int(df_agent_summary.loc[best_cf_accomplished_idx, 'goal_first_count'])} goal-first agents)")
    print(f"• Best Goal-First Agent performance: {df_agent_summary.loc[best_gf_accomplished_idx, 'avg_accomplished_goals_goal_first_agent']:.2f} "
          f"± {df_agent_summary.loc[best_gf_accomplished_idx, 'avg_accomplished_goals_goal_first_agent_sem']:.2f} goals "
          f"(at {int(df_agent_summary.loc[best_gf_accomplished_idx, 'goal_first_count'])} goal-first agents)")
    print(f"• Lowest Consent-First Agent violations as R: {df_agent_summary.loc[min_cf_violations_r_idx, 'avg_violated_consents_consent_first_r']:.2f} "
          f"± {df_agent_summary.loc[min_cf_violations_r_idx, 'avg_violated_consents_consent_first_r_sem']:.2f} "
          f"(at {int(df_agent_summary.loc[min_cf_violations_r_idx, 'goal_first_count'])} goal-first agents)")
    print(f"• Lowest Goal-First Agent violations as R: {df_agent_summary.loc[min_gf_violations_r_idx, 'avg_violated_consents_goal_first_r']:.2f} "
          f"± {df_agent_summary.loc[min_gf_violations_r_idx, 'avg_violated_consents_goal_first_r_sem']:.2f} "
          f"(at {int(df_agent_summary.loc[min_gf_violations_r_idx, 'goal_first_count'])} goal-first agents)")
    print(f"• Lowest Consent-First Agent violations as G: {df_agent_summary.loc[min_cf_violations_g_idx, 'avg_violated_consents_consent_first_g']:.2f} "
          f"± {df_agent_summary.loc[min_cf_violations_g_idx, 'avg_violated_consents_consent_first_g_sem']:.2f} "
          f"(at {int(df_agent_summary.loc[min_cf_violations_g_idx, 'goal_first_count'])} goal-first agents)")
    print(f"• Lowest Goal-First Agent violations as G: {df_agent_summary.loc[min_gf_violations_g_idx, 'avg_violated_consents_goal_first_g']:.2f} "
          f"± {df_agent_summary.loc[min_gf_violations_g_idx, 'avg_violated_consents_goal_first_g_sem']:.2f} "
          f"(at {int(df_agent_summary.loc[min_gf_violations_g_idx, 'goal_first_count'])} goal-first agents)")

if __name__ == "__main__":
    create_agent_ratio_analysis(experiment_name=experiment_name, experiment_date=experiment_date)
    create_agent_level_analysis(experiment_name=experiment_name, experiment_date=experiment_date)