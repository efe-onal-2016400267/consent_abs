#!/usr/bin/env python3
"""Verify data consistency across config, model, and agent CSVs."""

import json
import pandas as pd

# Sample file from goal_vs_monitoring analysis
config_file = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/configs/monitoring_vs_goal_based_analysis_(seed_789)_seed_789:_0-600-0-400_20251105_102206_config.json"
model_file = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/data/monitoring_vs_goal_based_analysis_(seed_789)_seed_789:_0-600-0-400_20251105_102206_model.csv"
agent_file = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results/monitoring_vs_goal_based_analysis_20251105/data/monitoring_vs_goal_based_analysis_(seed_789)_seed_789:_0-600-0-400_20251105_102206_agents.csv"

print("="*80)
print("VERIFICATION OF DATA CONSISTENCY")
print("="*80)

# 1. Check config
with open(config_file, 'r') as f:
    config = json.load(f)

params = config['parameters']
goal_first = params.get('GoalFirstAgent_COUNT', 0)
monitoring = params.get('MonitoringAgent_COUNT', 0)
total = goal_first + monitoring

print("\n1. CONFIG AGENT COUNTS:")
print(f"   GoalFirstAgent: {goal_first}")
print(f"   MonitoringAgent: {monitoring}")
print(f"   Total: {total}")

# 2. Check model data
model_df = pd.read_csv(model_file)
print(f"\n2. MODEL DATA:")
print(f"   Total rows: {len(model_df)}")
final_row = model_df.iloc[-1]
print(f"   Final step: {final_row.iloc[0]}")
print(f"   Total Accomplished Goals (final): {final_row['Total Accomplished Goals']}")
print(f"   Total Remaining Goals (final): {final_row['Total Remaining Goals']}")
print(f"   Total Resource Conflicts (final): {final_row['Total Resource Conflicts']}")

# 3. Check agent data
agent_df = pd.read_csv(agent_file)
max_step = agent_df['Step'].max()
agents_final = agent_df[agent_df['Step'] == max_step].copy()

print(f"\n3. AGENT DATA:")
print(f"   Max step in agent file: {max_step}")
print(f"   Rows at final step: {len(agents_final)}")

# Agent count breakdown
gf_agents = agents_final[agents_final['Agent Persona'] == 'GoalFirstAgent']
m_agents = agents_final[agents_final['Agent Persona'] == 'MonitoringAgent']

print(f"   GoalFirstAgent at final: {len(gf_agents)} (expected: {goal_first})")
print(f"   MonitoringAgent at final: {len(m_agents)} (expected: {monitoring})")
print(f"   ✓ MATCH" if len(gf_agents) == goal_first and len(m_agents) == monitoring else "   ✗ MISMATCH")

# 4. Cross-check model vs agent aggregations
print(f"\n4. CROSS-CHECK MODEL VS AGENT AGGREGATIONS:")

gf_accomplished = gf_agents['Accomplished Goals'].sum()
m_accomplished = m_agents['Accomplished Goals'].sum()
total_accomplished_agent_sum = gf_accomplished + m_accomplished

print(f"   Model Total Accomplished Goals: {final_row['Total Accomplished Goals']:.0f}")
print(f"   Agent sum Accomplished Goals: {total_accomplished_agent_sum:.0f}")
print(f"   ✓ MATCH" if abs(total_accomplished_agent_sum - final_row['Total Accomplished Goals']) < 1 else f"   ✗ MISMATCH (diff: {abs(total_accomplished_agent_sum - final_row['Total Accomplished Goals']):.0f})")

# 5. Agent-level metrics averaging
print(f"\n5. AGENT-LEVEL METRIC AVERAGES:")
print(f"   Avg accomplished goals (GoalFirstAgent): {gf_agents['Accomplished Goals'].mean():.3f}")
print(f"   Avg accomplished goals (MonitoringAgent): {m_agents['Accomplished Goals'].mean():.3f}")

# Check resource conflicts
gf_rc = gf_agents['Resource Conflicts'].sum()
m_rc = m_agents['Resource Conflicts'].sum()
total_rc_agent_sum = gf_rc + m_rc

print(f"\n   Model Total Resource Conflicts: {final_row['Total Resource Conflicts']:.0f}")
print(f"   Agent sum Resource Conflicts: {total_rc_agent_sum:.0f}")
print(f"   ✓ MATCH" if abs(total_rc_agent_sum - final_row['Total Resource Conflicts']) < 1 else f"   ✗ MISMATCH (diff: {abs(total_rc_agent_sum - final_row['Total Resource Conflicts']):.0f})")

print("\n" + "="*80)
