#!/usr/bin/env python3
"""Check resource conflicts discrepancy across multiple seeds."""

import json
import pandas as pd
from pathlib import Path

results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")

# Find all config files from one analysis
analysis_dir = results_dir / "monitoring_vs_goal_based_analysis_20251105"
if not analysis_dir.exists():
    print(f"Directory not found: {analysis_dir}")
    exit(1)

configs_dir = analysis_dir / "configs"
data_dir = analysis_dir / "data"

config_files = list(configs_dir.glob("*.json"))
print(f"Found {len(config_files)} config files in {analysis_dir.name}")

mismatches = []
for config_file in sorted(config_files)[:5]:  # Check first 5
    config_name = config_file.stem
    prefix = config_name.rsplit('_', 1)[0]
    
    model_file = data_dir / f"{prefix}_model.csv"
    agent_file = data_dir / f"{prefix}_agents.csv"
    
    if not model_file.exists() or not agent_file.exists():
        continue
    
    # Load data
    with open(config_file) as f:
        config = json.load(f)
    
    model_df = pd.read_csv(model_file)
    agent_df = pd.read_csv(agent_file)
    
    model_rc = model_df.iloc[-1]['Total Resource Conflicts']
    
    # Get agent Sum
    max_step = agent_df['Step'].max()
    agents_final = agent_df[agent_df['Step'] == max_step]
    agent_rc_sum = agents_final['Resource Conflicts'].sum()
    
    diff = agent_rc_sum - model_rc
    pct_diff = (diff / model_rc * 100) if model_rc > 0 else 0
    
    result = "✓" if abs(diff) < 1 else "✗"
    
    print(f"{result} {config_file.name[:60]:60s} | Model: {model_rc:7.0f} | Agent Sum: {agent_rc_sum:7.0f} | Diff: {diff:6.0f} ({pct_diff:5.1f}%)")
    
    if abs(diff) > 0:
        mismatches.append((config_name, diff, pct_diff))

if mismatches:
    print(f"\n⚠️  Found {len(mismatches)} mismatches (showing first 5)")
else:
    print("\n✓ All checked files match perfectly")
