"""
Script to check for unrealized consents in TADA data
for GoalFirstAgent (TA) and ConsentFirstAgent (DA)
"""

import pandas as pd
import json
import re
from pathlib import Path

def extract_experiment_info(config_filename):
    """Extract experiment name and configuration from config filename."""
    # Remove _config.json suffix
    name = config_filename.replace('_config.json', '')
    
    # Pattern: {experiment_name}_(seed_{N})_seed_{N}:_{agent_config}_{timestamp}
    match = re.match(r'(.+?)_\(seed_(\d+)\)_seed_\2:_(.+?)_(\d{8}_\d{6})$', name)
    
    if match:
        exp_name = match.group(1)
        seed = match.group(2)
        agent_config = match.group(3)
        timestamp_date = match.group(4).split('_')[0]
        return exp_name, agent_config, seed, timestamp_date
    
    return None, None, None, None

def load_agent_data(experiment_name, experiment_date):
    """Load agent-level data for TADA experiment."""
    results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")
    
    # Find all config files
    config_files = []
    
    # Check main configs directory
    main_configs_dir = results_dir / "configs"
    if main_configs_dir.exists():
        config_files.extend(list(main_configs_dir.glob("*.json")))
    
    # Check experiment-specific subdirectories
    exp_subdir = results_dir / f"{experiment_name}_{experiment_date}"
    if exp_subdir.exists():
        exp_configs_dir = exp_subdir / "configs"
        if exp_configs_dir.exists():
            config_files.extend(list(exp_configs_dir.glob("*.json")))
            print(f"Found experiment-specific configs in: {exp_configs_dir}")
    
    # Also search all subdirectories
    for subdir in results_dir.iterdir():
        if subdir.is_dir():
            exp_configs_dir = subdir / "configs"
            if exp_configs_dir.exists():
                matching_files = []
                for config_file in exp_configs_dir.glob("*.json"):
                    exp_name, agent_config, seed, file_date = extract_experiment_info(config_file.name)
                    if exp_name == experiment_name and file_date == experiment_date:
                        matching_files.append(config_file)
                
                if matching_files:
                    config_files.extend(matching_files)
                    print(f"Found matching configs in subdirectory: {exp_configs_dir} ({len(matching_files)} files)")
    
    # Collect agent-level data
    agent_data_list = []
    
    for config_file in config_files:
        exp_name, agent_config, seed, timestamp_date = extract_experiment_info(config_file.name)
        
        if exp_name is None:
            continue
        
        if exp_name != experiment_name:
            continue
        
        if timestamp_date != experiment_date:
            continue
        
        # Load config
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            continue
        
        # Find agent file
        config_name = config_file.stem
        prefix = config_name.rsplit('_', 1)[0]
        
        # Look for agent file
        agent_file = None
        main_data_dir = results_dir / "data"
        if main_data_dir.exists():
            agent_file = main_data_dir / f"{prefix}_agents.csv"
        
        if not agent_file or not agent_file.exists():
            # Check experiment-specific subdirectory
            exp_subdir = results_dir / f"{experiment_name}_{experiment_date}"
            if exp_subdir.exists():
                exp_data_dir = exp_subdir / "data"
                if exp_data_dir.exists():
                    agent_file = exp_data_dir / f"{prefix}_agents.csv"
        
        if not agent_file or not agent_file.exists():
            # Search all subdirectories
            for subdir in results_dir.iterdir():
                if subdir.is_dir():
                    exp_data_dir = subdir / "data"
                    if exp_data_dir.exists():
                        test_file = exp_data_dir / f"{prefix}_agents.csv"
                        if test_file.exists():
                            agent_file = test_file
                            break
        
        if agent_file and agent_file.exists():
            try:
                agent_df = pd.read_csv(agent_file)
                
                # Get final step
                step_col = 'Step' if 'Step' in agent_df.columns else agent_df.columns[0]
                steps = pd.to_numeric(agent_df[step_col], errors='coerce')
                last_step = steps.max()
                final_agent_values = agent_df[steps == last_step].copy()
                
                # Add metadata
                final_agent_values["seed"] = seed
                final_agent_values["agent_config"] = agent_config
                
                agent_data_list.append(final_agent_values)
            except Exception as e:
                print(f"Error processing {prefix}: {e}")
                continue
    
    if len(agent_data_list) == 0:
        print("No agent data collected.")
        return None
    
    all_agent_values_df = pd.concat(agent_data_list)
    
    # Extract goal_first_count from agent_config (format: "goal_first-consent_first-0-0")
    all_agent_values_df["goal_first_count"] = all_agent_values_df["agent_config"].str.split("-").str[0].astype(int)
    
    return all_agent_values_df

def check_unrealized_consents(df):
    """Check for unrealized consents for TAs and DAs."""
    print("=" * 80)
    print("Checking for Unrealized Consents in TADA Data")
    print("=" * 80)
    
    # Filter for TAs (GoalFirstAgent) and DAs (ConsentFirstAgent)
    df_ta = df[df["Agent Persona"] == "GoalFirstAgent"].copy()
    df_da = df[df["Agent Persona"] == "ConsentFirstAgent"].copy()
    
    print(f"\nTotal agents:")
    print(f"  GoalFirstAgent (TA): {len(df_ta)}")
    print(f"  ConsentFirstAgent (DA): {len(df_da)}")
    
    # Check for unrealized consents as R (Receiver)
    print("\n" + "=" * 80)
    print("Unrealized Consents as R (Receiver):")
    print("=" * 80)
    
    ta_unrealized_r = df_ta["Number of Consents as R Unrealized"]
    da_unrealized_r = df_da["Number of Consents as R Unrealized"]
    
    print(f"\nGoalFirstAgent (TA) - Consents as R Unrealized:")
    print(f"  Total agents with unrealized consents: {(ta_unrealized_r > 0).sum()}")
    print(f"  Total unrealized consents: {ta_unrealized_r.sum()}")
    print(f"  Mean per agent: {ta_unrealized_r.mean():.4f}")
    print(f"  Max per agent: {ta_unrealized_r.max()}")
    print(f"  Min per agent: {ta_unrealized_r.min()}")
    
    print(f"\nConsentFirstAgent (DA) - Consents as R Unrealized:")
    print(f"  Total agents with unrealized consents: {(da_unrealized_r > 0).sum()}")
    print(f"  Total unrealized consents: {da_unrealized_r.sum()}")
    print(f"  Mean per agent: {da_unrealized_r.mean():.4f}")
    print(f"  Max per agent: {da_unrealized_r.max()}")
    print(f"  Min per agent: {da_unrealized_r.min()}")
    
    # Check for unrealized consents as G (Giver)
    print("\n" + "=" * 80)
    print("Unrealized Consents as G (Giver):")
    print("=" * 80)
    
    ta_unrealized_g = df_ta["Number of Consents as G Unrealized"]
    da_unrealized_g = df_da["Number of Consents as G Unrealized"]
    
    print(f"\nGoalFirstAgent (TA) - Consents as G Unrealized:")
    print(f"  Total agents with unrealized consents: {(ta_unrealized_g > 0).sum()}")
    print(f"  Total unrealized consents: {ta_unrealized_g.sum()}")
    print(f"  Mean per agent: {ta_unrealized_g.mean():.4f}")
    print(f"  Max per agent: {ta_unrealized_g.max()}")
    print(f"  Min per agent: {ta_unrealized_g.min()}")
    
    print(f"\nConsentFirstAgent (DA) - Consents as G Unrealized:")
    print(f"  Total agents with unrealized consents: {(da_unrealized_g > 0).sum()}")
    print(f"  Total unrealized consents: {da_unrealized_g.sum()}")
    print(f"  Mean per agent: {da_unrealized_g.mean():.4f}")
    print(f"  Max per agent: {da_unrealized_g.max()}")
    print(f"  Min per agent: {da_unrealized_g.min()}")
    
    # Summary by goal_first_count
    print("\n" + "=" * 80)
    print("Summary by goal_first_count:")
    print("=" * 80)
    
    summary = df.groupby(["goal_first_count", "Agent Persona"]).agg({
        "Number of Consents as R Unrealized": ["sum", "mean", "max"],
        "Number of Consents as G Unrealized": ["sum", "mean", "max"]
    }).round(4)
    
    print("\nUnrealized Consents Summary:")
    print(summary)
    
    # Check if there are any unrealized consents at all
    print("\n" + "=" * 80)
    print("Overall Summary:")
    print("=" * 80)
    
    total_ta_r_unrealized = ta_unrealized_r.sum()
    total_da_r_unrealized = da_unrealized_r.sum()
    total_ta_g_unrealized = ta_unrealized_g.sum()
    total_da_g_unrealized = da_unrealized_g.sum()
    
    print(f"\nTotal Unrealized Consents:")
    print(f"  GoalFirstAgent (TA) as R: {total_ta_r_unrealized}")
    print(f"  ConsentFirstAgent (DA) as R: {total_da_r_unrealized}")
    print(f"  GoalFirstAgent (TA) as G: {total_ta_g_unrealized}")
    print(f"  ConsentFirstAgent (DA) as G: {total_da_g_unrealized}")
    
    has_unrealized = (total_ta_r_unrealized > 0 or total_da_r_unrealized > 0 or 
                     total_ta_g_unrealized > 0 or total_da_g_unrealized > 0)
    
    if has_unrealized:
        print("\n✓ YES: There ARE unrealized consents in the TADA data")
    else:
        print("\n✗ NO: There are NO unrealized consents in the TADA data")
    
    return df_ta, df_da

if __name__ == "__main__":
    # Load TADA data
    experiment_name = "goal_vs_consent_based_analysis"
    experiment_date = "20251107"
    
    print(f"Loading TADA data for experiment: {experiment_name}, date: {experiment_date}")
    df = load_agent_data(experiment_name, experiment_date)
    
    if df is not None:
        print(f"\nLoaded {len(df)} agent records")
        check_unrealized_consents(df)
    else:
        print("Failed to load data")

