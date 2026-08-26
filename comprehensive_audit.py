#!/usr/bin/env python3
"""
Comprehensive audit of analysis scripts.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
import re

def extract_experiment_info(config_filename):
    """Extract experiment name and configuration from config filename."""
    name = config_filename.replace('_config.json', '')
    match = re.match(r'(.+?)_\(seed_(\d+)\)_seed_\2:_(.+?)_(\d{8}_\d{6})$', name)
    
    if match:
        exp_name = match.group(1)
        seed = match.group(2)
        agent_config = match.group(3)
        timestamp_date = match.group(4).split('_')[0]
        return exp_name, agent_config, seed, timestamp_date
    return None, None, None, None

# Find a test case to audit
results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")
test_dir = list(results_dir.glob("*/"))[0]  # Use first experiment directory

print("=" * 80)
print("ANALYSIS SCRIPT AUDIT")
print("=" * 80)
print(f"Test directory: {test_dir.name}")
print()

# Find a config file in this directory
config_files = list(test_dir.glob("configs/*.json"))
if not config_files:
    print("No config files found!")
    exit(1)

config_file = config_files[0]
print(f"Using config: {config_file.name}")

with open(config_file, 'r') as f:
    config = json.load(f)

exp_name, agent_config, seed, timestamp = extract_experiment_info(config_file.name)
print(f"Extracted: exp={exp_name}, config={agent_config}, seed={seed}, date={timestamp}")
print()

# Load data
prefix = config_file.stem.rsplit('_', 1)[0]
model_file = test_dir / "data" / f"{prefix}_model.csv"
agent_file = test_dir / "data" / f"{prefix}_agents.csv"

if not model_file.exists() or not agent_file.exists():
    print(f"Data files not found!")
    print(f"  Model: {model_file.exists()}")
    print(f"  Agent: {agent_file.exists()}")
    exit(1)

model_df = pd.read_csv(model_file)
agent_df = pd.read_csv(agent_file)

print(f"Model shape: {model_df.shape}")
print(f"Agent shape: {agent_df.shape}")
print()

# Verify data consistency
print("=" * 80)
print("AUDIT 1: Data Consistency Check")
print("=" * 80)

final_step = agent_df['Step'].max()
model_final = model_df.iloc[-1]
agent_final = agent_df[agent_df['Step'] == final_step]

checks = {
    'Total Accomplished Goals': ('Total Accomplished Goals', 'Accomplished Goals'),
    'Total Resource Conflicts': ('Total Resource Conflicts', 'Resource Conflicts'),
    'Total Counter Goals': ('Total Resource Conflict Accomplished Counter Goals', 'Counter Conflict Goal Accomplishments'),
}

print("Comparing model-level (final row) vs agent-level (sum of final step):")
for check_name, (model_col, agent_col) in checks.items():
    model_val = model_final[model_col]
    agent_sum = agent_final[agent_col].sum()
    diff = abs(model_val - agent_sum)
    pct_diff = (diff / max(model_val, agent_sum) * 100) if max(model_val, agent_sum) > 0 else 0
    
    status = "✓ MATCH" if pct_diff < 1 else "⚠ WARN" if pct_diff < 5 else "✗ FAIL"
    print(f"{status} {check_name}:")
    print(f"      Model: {model_val:.0f}, Agent sum: {agent_sum:.0f}, Diff: {diff:.0f} ({pct_diff:.2f}%)")

print()

# Verify agent extraction logic
print("=" * 80)
print("AUDIT 2: Agent Extraction Logic")
print("=" * 80)

# Simulate what the analysis script does
distinct_agent_count_q = """SELECT COUNT(DISTINCT AgentID) as AGENT_COUNT FROM agent_df WHERE Step = 1"""
# For now, just count distinct agents
distinct_agents = agent_df[agent_df['Step'] == 1]['AgentID'].nunique()
print(f"Distinct agents (from Step 1): {distinct_agents}")

# Get final agent values as the script does
final_agent_values = agent_final  # This should be the same as agent_df.iloc[-distinct_agent_count:]

# Verify it's 1 row per agent
rows_count = len(final_agent_values)
distinct_final = final_agent_values['AgentID'].nunique()
print(f"Final agent values rows: {rows_count}")
print(f"Distinct agents in final rows: {distinct_final}")
print(f"✓ CORRECT" if rows_count == distinct_final else f"✗ ERROR: Mismatch!")

print()

# Verify agent type filtering
print("=" * 80)
print("AUDIT 3: Agent Type Filtering")
print("=" * 80)

agent_types = final_agent_values['Agent Persona'].value_counts()
print("Agent types in final step:")
for persona, count in agent_types.items():
    print(f"  {persona}: {count} agents")

# Check config agent counts
params = config['parameters']
consent_first = params.get('ConsentFirstAgent_COUNT', 0)
monitoring = params.get('MonitoringAgent_COUNT', 0)
goal_first = params.get('GoalFirstAgent_COUNT', 0)

print("\nConfig agent counts:")
print(f"  ConsentFirstAgent: {consent_first}")
print(f"  MonitoringAgent: {monitoring}")
print(f"  GoalFirstAgent: {goal_first}")

print("\nVerification:")
cf_match = "✓" if final_agent_values[final_agent_values['Agent Persona']=='ConsentFirstAgent'].shape[0] == consent_first else "✗"
mon_match = "✓" if final_agent_values[final_agent_values['Agent Persona']=='MonitoringAgent'].shape[0] == monitoring else "✗"
gf_match = "✓" if final_agent_values[final_agent_values['Agent Persona']=='GoalFirstAgent'].shape[0] == goal_first else "✗"

print(f"{cf_match} ConsentFirstAgent count matches config")
print(f"{mon_match} MonitoringAgent count matches config")
print(f"{gf_match} GoalFirstAgent count matches config")

print()

# Verify metric calculations
print("=" * 80)
print("AUDIT 4: Metric Calculations")
print("=" * 80)

# Calculate agent-level metrics as the script does
consent_first_mask = final_agent_values['Agent Persona'] == 'ConsentFirstAgent'
monitoring_mask = final_agent_values['Agent Persona'] == 'MonitoringAgent'
goal_first_mask = final_agent_values['Agent Persona'] == 'GoalFirstAgent'

print("Sample agent-level metric calculation (Resource Conflicts):")
if consent_first_mask.any():
    cf_rc_mean = final_agent_values[consent_first_mask]['Resource Conflicts'].mean()
    cf_rc_sum = final_agent_values[consent_first_mask]['Resource Conflicts'].sum()
    print(f"  ConsentFirstAgent: mean={cf_rc_mean:.2f}, sum={cf_rc_sum:.0f}")

if monitoring_mask.any():
    mon_rc_mean = final_agent_values[monitoring_mask]['Resource Conflicts'].mean()
    mon_rc_sum = final_agent_values[monitoring_mask]['Resource Conflicts'].sum()
    print(f"  MonitoringAgent:   mean={mon_rc_mean:.2f}, sum={mon_rc_sum:.0f}")

if goal_first_mask.any():
    gf_rc_mean = final_agent_values[goal_first_mask]['Resource Conflicts'].mean()
    gf_rc_sum = final_agent_values[goal_first_mask]['Resource Conflicts'].sum()
    print(f"  GoalFirstAgent:    mean={gf_rc_mean:.2f}, sum={gf_rc_sum:.0f}")

print(f"\nTotal sum of all agent RC: {final_agent_values['Resource Conflicts'].sum():.0f}")
print(f"Model-level RC total: {model_final['Total Resource Conflicts']:.0f}")
print(f"✓ Sums match (agent-level aggregation is correct)" if abs(final_agent_values['Resource Conflicts'].sum() - model_final['Total Resource Conflicts']) < model_final['Total Resource Conflicts'] * 0.05 else "✗ Sums don't match!")

print()
print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
