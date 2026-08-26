#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

# Load a sample agent file
file_path = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/data/monitoring_vs_goal_based_analysis_(seed_789)_seed_789:_0-600-0-400_20251105_102206_agents.csv")

df = pd.read_csv(file_path)

print("=" * 80)
print("AGENT CSV STRUCTURE")
print("=" * 80)
print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"Shape: {df.shape}")
print()

print(f"Unique agents: {df['AgentID'].nunique()}")
print(f"Unique steps: {df['Step'].nunique()}")
print(f"Max step: {df['Step'].max()}")
print()

# Check if it's 1 row per agent per step
rows_per_agent = df.groupby('AgentID').size()
print(f"Rows per agent - Min: {rows_per_agent.min()}, Max: {rows_per_agent.max()}, Mean: {rows_per_agent.mean():.1f}")
print()

# Sample first agent over time
agent1 = df[df['AgentID'] == df['AgentID'].unique()[0]].sort_values('Step')
print(f"Sample: First agent ({agent1.iloc[0]['AgentID']}) - Resource Conflicts over time:\n")
print(agent1[['Step', 'Agent Persona', 'Resource Conflicts', 'Accomplished Goals']].head(10).to_string())
print("...")
print(agent1[['Step', 'Agent Persona', 'Resource Conflicts', 'Accomplished Goals']].tail(5).to_string())
print()

# Now check: at final step, how many rows are there?
final_step = df['Step'].max()
final_agents = df[df['Step'] == final_step]
print(f"At final step ({final_step}):")
print(f"  Number of agent rows: {len(final_agents)}")
print(f"  Number of distinct agents: {final_agents['AgentID'].nunique()}")
print(f"  Sum of Resource Conflicts: {final_agents['Resource Conflicts'].sum()}")
print(f"  Mean Resource Conflicts: {final_agents['Resource Conflicts'].mean():.2f}")
