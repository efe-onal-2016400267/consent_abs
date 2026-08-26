#!/usr/bin/env python3
"""Check if Counter Goal Accomplishments has the same cumulative issue."""

import pandas as pd

agent_file = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/data/monitoring_vs_goal_based_analysis_(seed_123)_seed_123:_0-1000-0-0_20251105_102206_agents.csv"
model_file = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/data/monitoring_vs_goal_based_analysis_(seed_123)_seed_123:_0-1000-0-0_20251105_102206_model.csv"

agent_df = pd.read_csv(agent_file)
model_df = pd.read_csv(model_file)

max_step = agent_df['Step'].max()
agents_final = agent_df[agent_df['Step'] == max_step]

print("="*80)
print("CHECKING COUNTER GOAL ACCOMPLISHMENTS COLUMN")
print("="*80)

# Check model value
model_rc_cga = model_df.iloc[-1]['Total Resource Conflict Accomplished Counter Goals']
agent_cga_sum = agents_final['Counter Conflict Goal Accomplishments'].sum()

print(f"\nModel - Total Resource Conflict Accomplished Counter Goals: {model_rc_cga}")
print(f"Agent sum - Counter Conflict Goal Accomplishments: {agent_cga_sum}")
print(f"Difference: {agent_cga_sum - model_rc_cga}")

# Check if cumulative
print(f"\nPer-agent Counter Goal Accomplishments at final step:")
for agent_id in agents_final['AgentID'].head(10):
    agent_history = agent_df[agent_df['AgentID'] == agent_id].sort_values('Step')
    cga_values = agent_history['Counter Conflict Goal Accomplishments'].values
    print(f"  Agent {agent_id}: {cga_values[-1]} (final value)")

# Check Accomplished Goals (known to be correct aggregate)
print(f"\n\nCOMPARE WITH ACCOMPLISHED GOALS (should be correct aggregate):")
model_ag = model_df.iloc[-1]['Total Accomplished Goals']
agent_ag_sum = agents_final['Accomplished Goals'].sum()

print(f"Model - Total Accomplished Goals: {model_ag}")
print(f"Agent sum - Accomplished Goals: {agent_ag_sum}")
print(f"Difference: {agent_ag_sum - model_ag}")

if abs(agent_ag_sum - model_ag) < 1:
    print("✓ These MATCH - so Accomplished Goals is correctly aggregated")

print("\n" + "="*80)
