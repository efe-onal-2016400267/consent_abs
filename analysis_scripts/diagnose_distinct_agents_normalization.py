#!/usr/bin/env python3
"""Diagnostic script to check distinct agents interacted normalization."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Import the analysis modules
import goal_vs_monitoring_model_and_agent_level_analysis as gvma
import goal_vs_consent_model_and_agent_level_analysis as gvca


def diagnose_distinct_agents_normalization():
    """Check raw values, simulation lengths, and normalized values for both experiments."""
    
    print("=" * 80)
    print("DIAGNOSTIC: Distinct Agents Interacted Normalization")
    print("=" * 80)
    
    # Load data for both experiments
    print("\n1. Loading data for goal_vs_monitoring...")
    df_ta_va, _ = gvma.load_simulation_data(
        experiment_name=gvma.experiment_name,
        experiment_date=gvma.experiment_date
    )
    
    print("2. Loading data for goal_vs_consent...")
    df_ta_da, _ = gvca.load_simulation_data(
        experiment_name=gvca.experiment_name,
        experiment_date=gvca.experiment_date
    )
    
    # Prepare summaries
    print("\n3. Preparing summaries...")
    
    # TA-VA (goal_vs_monitoring)
    agent_metrics_ta_va = [
        'avg_distinct_agents_interacted_r_goal_first_agent',
        'avg_distinct_agents_interacted_r_monitoring_agent',
        'avg_distinct_agents_interacted_g_goal_first_agent',
        'avg_distinct_agents_interacted_g_monitoring_agent',
        'avg_steps_overall',
        'goal_first_count',
        'monitoring_count'
    ]
    
    grouped_ta_va = df_ta_va.groupby(['experiment_name', 'agent_config'])
    summary_ta_va = grouped_ta_va[agent_metrics_ta_va].mean().reset_index()
    summary_ta_va = summary_ta_va.merge(
        grouped_ta_va[['goal_first_count', 'avg_steps_overall']].mean().reset_index(),
        on=['experiment_name', 'agent_config'],
        suffixes=('', '_config')
    )
    summary_ta_va = summary_ta_va.sort_values('goal_first_count')
    summary_ta_va['ta_ratio'] = summary_ta_va['goal_first_count'] / (summary_ta_va['goal_first_count'] + summary_ta_va['monitoring_count'])
    
    # TA-DA (goal_vs_consent)
    agent_metrics_ta_da = [
        'avg_distinct_agents_interacted_r_goal_first_agent',
        'avg_distinct_agents_interacted_r_consent_first_agent',
        'avg_distinct_agents_interacted_g_goal_first_agent',
        'avg_distinct_agents_interacted_g_consent_first_agent',
        'avg_steps_overall',
        'goal_first_count',
        'consent_first_count'
    ]
    
    grouped_ta_da = df_ta_da.groupby(['experiment_name', 'agent_config'])
    summary_ta_da = grouped_ta_da[agent_metrics_ta_da].mean().reset_index()
    summary_ta_da = summary_ta_da.merge(
        grouped_ta_da[['goal_first_count', 'avg_steps_overall']].mean().reset_index(),
        on=['experiment_name', 'agent_config'],
        suffixes=('', '_config')
    )
    summary_ta_da = summary_ta_da.sort_values('goal_first_count')
    summary_ta_da['ta_ratio'] = summary_ta_da['goal_first_count'] / (summary_ta_da['goal_first_count'] + summary_ta_da['consent_first_count'])
    
    # Print diagnostics
    print("\n" + "=" * 80)
    print("TA-VA (goal_vs_monitoring) Analysis")
    print("=" * 80)
    print(f"\nNumber of configurations: {len(summary_ta_va)}")
    print(f"\nSimulation Length (avg_steps_overall):")
    print(f"  Min: {summary_ta_va['avg_steps_overall'].min():.1f}")
    print(f"  Max: {summary_ta_va['avg_steps_overall'].max():.1f}")
    print(f"  Mean: {summary_ta_va['avg_steps_overall'].mean():.1f}")
    print(f"  Std: {summary_ta_va['avg_steps_overall'].std():.1f}")
    
    print(f"\nRaw Distinct Agents Interacted as R (GoalFirstAgent):")
    print(f"  Min: {summary_ta_va['avg_distinct_agents_interacted_r_goal_first_agent'].min():.2f}")
    print(f"  Max: {summary_ta_va['avg_distinct_agents_interacted_r_goal_first_agent'].max():.2f}")
    print(f"  Mean: {summary_ta_va['avg_distinct_agents_interacted_r_goal_first_agent'].mean():.2f}")
    
    print(f"\nRaw Distinct Agents Interacted as R (MonitoringAgent):")
    print(f"  Min: {summary_ta_va['avg_distinct_agents_interacted_r_monitoring_agent'].min():.2f}")
    print(f"  Max: {summary_ta_va['avg_distinct_agents_interacted_r_monitoring_agent'].max():.2f}")
    print(f"  Mean: {summary_ta_va['avg_distinct_agents_interacted_r_monitoring_agent'].mean():.2f}")
    
    # Calculate normalized values
    steps_ta_va = pd.to_numeric(summary_ta_va['avg_steps_overall'], errors='coerce').replace(0, np.nan)
    norm_gf_r_ta_va = summary_ta_va['avg_distinct_agents_interacted_r_goal_first_agent'] / steps_ta_va
    norm_m_r_ta_va = summary_ta_va['avg_distinct_agents_interacted_r_monitoring_agent'] / steps_ta_va
    
    print(f"\nNormalized Distinct Agents Interacted as R per Step (GoalFirstAgent):")
    print(f"  Min: {norm_gf_r_ta_va.min():.4f}")
    print(f"  Max: {norm_gf_r_ta_va.max():.4f}")
    print(f"  Mean: {norm_gf_r_ta_va.mean():.4f}")
    
    print(f"\nNormalized Distinct Agents Interacted as R per Step (MonitoringAgent):")
    print(f"  Min: {norm_m_r_ta_va.min():.4f}")
    print(f"  Max: {norm_m_r_ta_va.max():.4f}")
    print(f"  Mean: {norm_m_r_ta_va.mean():.4f}")
    
    # Check correlation with TA ratio
    print(f"\nCorrelation with TA Ratio:")
    print(f"  Steps vs TA Ratio: {summary_ta_va['avg_steps_overall'].corr(summary_ta_va['ta_ratio']):.3f}")
    print(f"  Raw GF R vs TA Ratio: {summary_ta_va['avg_distinct_agents_interacted_r_goal_first_agent'].corr(summary_ta_va['ta_ratio']):.3f}")
    print(f"  Raw M R vs TA Ratio: {summary_ta_va['avg_distinct_agents_interacted_r_monitoring_agent'].corr(summary_ta_va['ta_ratio']):.3f}")
    print(f"  Norm GF R vs TA Ratio: {norm_gf_r_ta_va.corr(summary_ta_va['ta_ratio']):.3f}")
    print(f"  Norm M R vs TA Ratio: {norm_m_r_ta_va.corr(summary_ta_va['ta_ratio']):.3f}")
    
    print("\n" + "=" * 80)
    print("TA-DA (goal_vs_consent) Analysis")
    print("=" * 80)
    print(f"\nNumber of configurations: {len(summary_ta_da)}")
    print(f"\nSimulation Length (avg_steps_overall):")
    print(f"  Min: {summary_ta_da['avg_steps_overall'].min():.1f}")
    print(f"  Max: {summary_ta_da['avg_steps_overall'].max():.1f}")
    print(f"  Mean: {summary_ta_da['avg_steps_overall'].mean():.1f}")
    print(f"  Std: {summary_ta_da['avg_steps_overall'].std():.1f}")
    
    print(f"\nRaw Distinct Agents Interacted as R (GoalFirstAgent):")
    print(f"  Min: {summary_ta_da['avg_distinct_agents_interacted_r_goal_first_agent'].min():.2f}")
    print(f"  Max: {summary_ta_da['avg_distinct_agents_interacted_r_goal_first_agent'].max():.2f}")
    print(f"  Mean: {summary_ta_da['avg_distinct_agents_interacted_r_goal_first_agent'].mean():.2f}")
    
    print(f"\nRaw Distinct Agents Interacted as R (ConsentFirstAgent):")
    print(f"  Min: {summary_ta_da['avg_distinct_agents_interacted_r_consent_first_agent'].min():.2f}")
    print(f"  Max: {summary_ta_da['avg_distinct_agents_interacted_r_consent_first_agent'].max():.2f}")
    print(f"  Mean: {summary_ta_da['avg_distinct_agents_interacted_r_consent_first_agent'].mean():.2f}")
    
    # Calculate normalized values
    steps_ta_da = pd.to_numeric(summary_ta_da['avg_steps_overall'], errors='coerce').replace(0, np.nan)
    norm_gf_r_ta_da = summary_ta_da['avg_distinct_agents_interacted_r_goal_first_agent'] / steps_ta_da
    norm_cf_r_ta_da = summary_ta_da['avg_distinct_agents_interacted_r_consent_first_agent'] / steps_ta_da
    
    print(f"\nNormalized Distinct Agents Interacted as R per Step (GoalFirstAgent):")
    print(f"  Min: {norm_gf_r_ta_da.min():.4f}")
    print(f"  Max: {norm_gf_r_ta_da.max():.4f}")
    print(f"  Mean: {norm_gf_r_ta_da.mean():.4f}")
    
    print(f"\nNormalized Distinct Agents Interacted as R per Step (ConsentFirstAgent):")
    print(f"  Min: {norm_cf_r_ta_da.min():.4f}")
    print(f"  Max: {norm_cf_r_ta_da.max():.4f}")
    print(f"  Mean: {norm_cf_r_ta_da.mean():.4f}")
    
    # Check correlation with TA ratio
    print(f"\nCorrelation with TA Ratio:")
    print(f"  Steps vs TA Ratio: {summary_ta_da['avg_steps_overall'].corr(summary_ta_da['ta_ratio']):.3f}")
    print(f"  Raw GF R vs TA Ratio: {summary_ta_da['avg_distinct_agents_interacted_r_goal_first_agent'].corr(summary_ta_da['ta_ratio']):.3f}")
    print(f"  Raw CF R vs TA Ratio: {summary_ta_da['avg_distinct_agents_interacted_r_consent_first_agent'].corr(summary_ta_da['ta_ratio']):.3f}")
    print(f"  Norm GF R vs TA Ratio: {norm_gf_r_ta_da.corr(summary_ta_da['ta_ratio']):.3f}")
    print(f"  Norm CF R vs TA Ratio: {norm_cf_r_ta_da.corr(summary_ta_da['ta_ratio']):.3f}")
    
    # Create comparison table
    print("\n" + "=" * 80)
    print("Comparison Table: Values by TA Ratio")
    print("=" * 80)
    
    print("\nTA-VA (goal_vs_monitoring):")
    print(f"{'TA Ratio':<10} {'Steps':<10} {'Raw GF R':<12} {'Raw M R':<12} {'Norm GF R':<12} {'Norm M R':<12}")
    print("-" * 80)
    for idx, row in summary_ta_va.iterrows():
        print(f"{row['ta_ratio']:<10.2f} {row['avg_steps_overall']:<10.1f} "
              f"{row['avg_distinct_agents_interacted_r_goal_first_agent']:<12.2f} "
              f"{row['avg_distinct_agents_interacted_r_monitoring_agent']:<12.2f} "
              f"{norm_gf_r_ta_va.iloc[idx]:<12.4f} "
              f"{norm_m_r_ta_va.iloc[idx]:<12.4f}")
    
    print("\nTA-DA (goal_vs_consent):")
    print(f"{'TA Ratio':<10} {'Steps':<10} {'Raw GF R':<12} {'Raw CF R':<12} {'Norm GF R':<12} {'Norm CF R':<12}")
    print("-" * 80)
    for idx, row in summary_ta_da.iterrows():
        print(f"{row['ta_ratio']:<10.2f} {row['avg_steps_overall']:<10.1f} "
              f"{row['avg_distinct_agents_interacted_r_goal_first_agent']:<12.2f} "
              f"{row['avg_distinct_agents_interacted_r_consent_first_agent']:<12.2f} "
              f"{norm_gf_r_ta_da.iloc[idx]:<12.4f} "
              f"{norm_cf_r_ta_da.iloc[idx]:<12.4f}")
    
    # Create visualization
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Distinct Agents Interacted Normalization Diagnostic', fontsize=16, fontweight='bold')
    
    # TA-VA: Steps vs TA Ratio
    ax = axes[0, 0]
    ax.plot(summary_ta_va['ta_ratio'], summary_ta_va['avg_steps_overall'], 'o-', linewidth=2, markersize=6)
    ax.set_xlabel('TA Ratio')
    ax.set_ylabel('Simulation Length (Steps)')
    ax.set_title('TA-VA: Simulation Length vs TA Ratio')
    ax.grid(True, alpha=0.3)
    
    # TA-VA: Raw values
    ax = axes[0, 1]
    ax.plot(summary_ta_va['ta_ratio'], summary_ta_va['avg_distinct_agents_interacted_r_goal_first_agent'], 
            'o-', linewidth=2, markersize=6, label='GoalFirstAgent', color='red')
    ax.plot(summary_ta_va['ta_ratio'], summary_ta_va['avg_distinct_agents_interacted_r_monitoring_agent'], 
            's-', linewidth=2, markersize=6, label='MonitoringAgent', color='blue')
    ax.set_xlabel('TA Ratio')
    ax.set_ylabel('Raw Distinct Agents Interacted as R')
    ax.set_title('TA-VA: Raw Values vs TA Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # TA-VA: Normalized values
    ax = axes[0, 2]
    ax.plot(summary_ta_va['ta_ratio'], norm_gf_r_ta_va, 
            'o-', linewidth=2, markersize=6, label='GoalFirstAgent', color='red')
    ax.plot(summary_ta_va['ta_ratio'], norm_m_r_ta_va, 
            's-', linewidth=2, markersize=6, label='MonitoringAgent', color='blue')
    ax.set_xlabel('TA Ratio')
    ax.set_ylabel('Normalized Distinct Agents Interacted as R per Step')
    ax.set_title('TA-VA: Normalized Values vs TA Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # TA-DA: Steps vs TA Ratio
    ax = axes[1, 0]
    ax.plot(summary_ta_da['ta_ratio'], summary_ta_da['avg_steps_overall'], 'o-', linewidth=2, markersize=6)
    ax.set_xlabel('TA Ratio')
    ax.set_ylabel('Simulation Length (Steps)')
    ax.set_title('TA-DA: Simulation Length vs TA Ratio')
    ax.grid(True, alpha=0.3)
    
    # TA-DA: Raw values
    ax = axes[1, 1]
    ax.plot(summary_ta_da['ta_ratio'], summary_ta_da['avg_distinct_agents_interacted_r_goal_first_agent'], 
            'o-', linewidth=2, markersize=6, label='GoalFirstAgent', color='red')
    ax.plot(summary_ta_da['ta_ratio'], summary_ta_da['avg_distinct_agents_interacted_r_consent_first_agent'], 
            's-', linewidth=2, markersize=6, label='ConsentFirstAgent', color='green')
    ax.set_xlabel('TA Ratio')
    ax.set_ylabel('Raw Distinct Agents Interacted as R')
    ax.set_title('TA-DA: Raw Values vs TA Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # TA-DA: Normalized values
    ax = axes[1, 2]
    ax.plot(summary_ta_da['ta_ratio'], norm_gf_r_ta_da, 
            'o-', linewidth=2, markersize=6, label='GoalFirstAgent', color='red')
    ax.plot(summary_ta_da['ta_ratio'], norm_cf_r_ta_da, 
            's-', linewidth=2, markersize=6, label='ConsentFirstAgent', color='green')
    ax.set_xlabel('TA Ratio')
    ax.set_ylabel('Normalized Distinct Agents Interacted as R per Step')
    ax.set_title('TA-DA: Normalized Values vs TA Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_path = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/analysis_scripts") / "distinct_agents_normalization_diagnostic.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n\nDiagnostic plot saved to: {output_path}")
    plt.show()
    
    print("\n" + "=" * 80)
    print("Diagnostic Complete")
    print("=" * 80)


if __name__ == "__main__":
    diagnose_distinct_agents_normalization()

