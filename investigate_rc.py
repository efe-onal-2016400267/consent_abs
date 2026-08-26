#!/usr/bin/env python3
"""Investigate resource conflicts column mismatch."""

import pandas as pd

# Check the problematic file - the one with 37% difference
agent_file = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/data/monitoring_vs_goal_based_analysis_(seed_123)_seed_123:_0-1000-0-0_20251105_102206_agents.csv"

agent_df = pd.read_csv(agent_file)

print("="*80)
print("AGENT CSV STRUCTURE INVESTIGATION")
print("="*80)

print(f"\nTotal rows: {len(agent_df)}")
print(f"Max Step: {agent_df['Step'].max()}")

# Check how many rows per step
rows_per_step = agent_df.groupby('Step').size()
print(f"\nRows per step (should all be 1000):")
print(f"  Min: {rows_per_step.min()}")
print(f"  Max: {rows_per_step.max()}")
print(f"  Median: {rows_per_step.median()}")
print(f"  Unique values: {rows_per_step.unique()}")

# Check final step in detail
max_step = agent_df['Step'].max()
final_agents = agent_df[agent_df['Step'] == max_step].copy()

print(f"\nAt final step ({max_step}):")
print(f"  Total rows: {len(final_agents)}")
print(f"  Agent personas:")
print(agent_df[agent_df['Step'] == max_step]['Agent Persona'].value_counts())

# Check if resource conflicts column has data
print(f"\nResource Conflicts column:")
print(f"  dtype: {agent_df['Resource Conflicts'].dtype}")
print(f"  Total sum (all data): {agent_df['Resource Conflicts'].sum()}")
print(f"  Total sum (final step): {final_agents['Resource Conflicts'].sum()}")
print(f"  Mean (final step): {final_agents['Resource Conflicts'].mean():.2f}")
print(f"  Non-zero count: {(agent_df['Resource Conflicts'] > 0).sum()}")

# Check if this is a per-agent accumulation
print(f"\nPer-agent resource conflicts at final step:")
for agent_id in final_agents['AgentID'].head(10):
    agent_history = agent_df[agent_df['AgentID'] == agent_id].sort_values('Step')
    rc_values = agent_history['Resource Conflicts'].values
    print(f"  Agent {agent_id}: {rc_values[-1]} (steps: {len(rc_values)})")

# Compare with model
model_file = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/data/monitoring_vs_goal_based_analysis_(seed_123)_seed_123:_0-1000-0-0_20251105_102206_model.csv"
model_df = pd.read_csv(model_file)

print(f"\nModel data comparison:")
print(f"  Final model step: {model_df.iloc[-1].iloc[0]}")
print(f"  Total Resource Conflicts (model): {model_df.iloc[-1]['Total Resource Conflicts']}")

# Theory: are Resource Conflicts per-agent cumulative values?
print(f"\nTheory test: Are Resource Conflicts per-agent CUMULATIVE?")
print(f"  If we sum all agent.RC at final step: {final_agents['Resource Conflicts'].sum()}")
print(f"  Model reports: {model_df.iloc[-1]['Total Resource Conflicts']}")
print(f"  Difference: {final_agents['Resource Conflicts'].sum() - model_df.iloc[-1]['Total Resource Conflicts']}")

print("\n" + "="*80)
