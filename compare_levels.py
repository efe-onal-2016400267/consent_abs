#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

# Load corresponding model file
agent_file = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/data/monitoring_vs_goal_based_analysis_(seed_789)_seed_789:_0-600-0-400_20251105_102206_agents.csv")
model_file = agent_file.parent / agent_file.name.replace('_agents.csv', '_model.csv')

agent_df = pd.read_csv(agent_file)
model_df = pd.read_csv(model_file)

print("=" * 80)
print("COMPARING MODEL-LEVEL vs AGENT-LEVEL DATA")
print("=" * 80)
print()

# Get final values
final_step = agent_df['Step'].max()
model_final = model_df.iloc[-1]  # Last row
agent_final = agent_df[agent_df['Step'] == final_step]

print(f"Final step: {final_step}")
print(f"Total simulation steps: {len(model_df)}")
print(f"Unique agents: {agent_df['AgentID'].nunique()}")
print()

print(f"Model-level Total Resource Conflicts (final step): {model_final['Total Resource Conflicts']}")
print(f"Agent-level sum of Resource Conflicts (final step): {agent_final['Resource Conflicts'].sum()}")
print(f"Agent-level mean of Resource Conflicts (final step): {agent_final['Resource Conflicts'].mean():.2f}")
print()

# Check if sum == model value or if there's a mismatch
model_rc = model_final['Total Resource Conflicts']
agent_sum_rc = agent_final['Resource Conflicts'].sum()
ratio = agent_sum_rc / model_rc if model_rc > 0 else 0
print(f"Ratio (agent sum / model total): {ratio:.2f}x")
print()

# Check other metrics for comparison
print("Comparing other metrics:")
print(f"Model Total Accomplished Goals: {model_final['Total Accomplished Goals']}")
print(f"Agent sum of Accomplished Goals: {agent_final['Accomplished Goals'].sum()}")
print()

print(f"Model Total Counter Goals: {model_final['Total Resource Conflict Accomplished Counter Goals']}")
print(f"Agent sum of Counter Goals: {agent_final['Counter Conflict Goal Accomplishments'].sum()}")
print()

# Check agent breakdown by persona
print("Agent breakdown by Persona (at final step):")
for persona in agent_final['Agent Persona'].unique():
    persona_agents = agent_final[agent_final['Agent Persona'] == persona]
    count = len(persona_agents)
    rc_sum = persona_agents['Resource Conflicts'].sum()
    rc_mean = persona_agents['Resource Conflicts'].mean()
    print(f"  {persona}: {count} agents, RC sum={rc_sum}, RC mean={rc_mean:.2f}")
