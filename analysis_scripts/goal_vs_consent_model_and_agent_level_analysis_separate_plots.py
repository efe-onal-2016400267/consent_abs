#!/usr/bin/env python3
"""
Variant of the goal-vs-consent analysis script that saves every plot as its own
image file. It reuses the data-loading helpers from the consolidated plotting
script but writes out one figure per metric instead of multi-panel dashboards.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

import goal_vs_consent_model_and_agent_level_analysis as base_analysis


# Adopt the same default experiment selection as the consolidated script.
experiment_name = base_analysis.experiment_name
experiment_date = base_analysis.experiment_date


plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


def _figures_dir(subfolder: str = "separate_plots") -> Path:
    """Return/create the figures directory for the separate-plot exports."""

    base_dir = base_analysis.create_figures_directory(experiment_name, experiment_date)
    target = base_dir / subfolder
    target.mkdir(exist_ok=True)
    return target


def _prepare_simulation_summary() -> pd.DataFrame:
    """Load and aggregate model-level metrics exactly as in the base script."""

    df, _ = base_analysis.load_simulation_data(
        experiment_name=experiment_name,
        experiment_date=experiment_date,
    )

    if df.empty:
        raise RuntimeError("No simulation data found for the requested experiment.")

    metrics_to_average = [
        'consent_first_count', 'goal_first_count', 'fifty_fifty_count', 'total_agents',
        'accomplished_goals', 'remaining_goals', 'violated_consents', 'total_consents',
        'resource_conflicts', 'counter_goal_accomplishments',
        'consent_violation_ratio', 'consent_fulfillment_ratio',
        'consent_unrealized_ratio', 'consent_deferred_ratio',
        'resource_conflict_counter_goal_accomplishment_ratio', 'avg_steps_overall'
    ]

    grouped = df.groupby(['experiment_name', 'agent_config'])
    mean_df = grouped[metrics_to_average].mean().reset_index()
    std_df = grouped[metrics_to_average].std().reset_index()
    sem_df = grouped[metrics_to_average].sem().reset_index()
    count_df = grouped.size().reset_index(name='num_seeds')

    df_summary = mean_df.copy()
    for col in metrics_to_average:
        df_summary[f'{col}_std'] = std_df[col]
        df_summary[f'{col}_sem'] = sem_df[col]

    df_summary = df_summary.merge(count_df, on=['experiment_name', 'agent_config'])
    df_summary = df_summary.sort_values('goal_first_count')

    return df_summary


def create_agent_ratio_analysis_separate():
    """Create one image per model-level metric vs. agent ratio."""

    df_summary = _prepare_simulation_summary()
    figures_dir = _figures_dir('model_level_separate')

    exp_name_clean = df_summary['experiment_name'].iloc[0]
    ratio = df_summary['goal_first_count'] / df_summary['total_agents']

    # Single-line error-bar plots.
    single_series_specs = [
        {
            'metric': 'accomplished_goals',
            'sem': 'accomplished_goals_sem',
            'color': 'green',
            'label': 'Accomplished Goals',
            'ylabel': 'Total Accomplished Goals',
            'title': 'Accomplished Goals vs Agent Ratio',
            'filename': 'simulation_analysis_accomplished_goals'
        },
        {
            'metric': 'remaining_goals',
            'sem': 'remaining_goals_sem',
            'color': 'red',
            'label': 'Remaining Goals',
            'ylabel': 'Total Remaining Goals',
            'title': 'Remaining Goals vs Agent Ratio',
            'filename': 'simulation_analysis_remaining_goals'
        },
        {
            'metric': 'consent_violation_ratio',
            'sem': 'consent_violation_ratio_sem',
            'color': 'orange',
            'label': 'Consent Violation Ratio',
            'ylabel': 'Consent Violation Ratio',
            'title': 'Consent Violation Ratio vs Agent Ratio',
            'filename': 'simulation_analysis_consent_violation_ratio'
        },
        {
            'metric': 'resource_conflicts',
            'sem': 'resource_conflicts_sem',
            'color': 'purple',
            'label': 'Resource Conflicts',
            'ylabel': 'Total Resource Conflicts',
            'title': 'Resource Conflicts vs Agent Ratio',
            'filename': 'simulation_analysis_resource_conflicts'
        },
        {
            'metric': 'counter_goal_accomplishments',
            'sem': 'counter_goal_accomplishments_sem',
            'color': 'brown',
            'label': 'Counter Goal Accomplishments',
            'ylabel': 'Total Counter Goal Accomplishments',
            'title': 'Counter Goal Accomplishments vs Agent Ratio',
            'filename': 'simulation_analysis_counter_goal_accomplishments'
        },
    ]

    for spec in single_series_specs:
        fig, ax = plt.subplots(figsize=(7.5, 5))
        ax.errorbar(
            ratio,
            df_summary[spec['metric']],
            yerr=df_summary[spec['sem']],
            fmt='o-', linewidth=2, markersize=8, capsize=5,
            color=spec['color'], label=spec['label']
        )
        ax.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=13, fontweight='bold')
        ax.set_ylabel(spec['ylabel'], fontsize=13, fontweight='bold')
        ax.set_title(spec['title'], fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        output = figures_dir / f"{spec['filename']}_{exp_name_clean}.png"
        fig.tight_layout()
        fig.savefig(output, dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Dual-axis figure (kept as a single image, already unique in the base script).
    fig, ax_steps = plt.subplots(figsize=(7.5, 5))
    ax_goals = ax_steps.twinx()

    line1 = ax_steps.errorbar(
        ratio,
        df_summary['avg_steps_overall'],
        yerr=df_summary['avg_steps_overall_sem'],
        fmt='o-', linewidth=2, markersize=8, capsize=5,
        label='Average Simulation Length', color='purple'
    )
    line2 = ax_goals.errorbar(
        ratio,
        df_summary['accomplished_goals'],
        yerr=df_summary['accomplished_goals_sem'],
        fmt='s-', linewidth=2, markersize=8, capsize=5,
        label='Total Accomplished Goals', color='green'
    )

    ax_steps.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=13)
    ax_steps.set_ylabel('Average Steps', fontsize=13, color='purple')
    ax_goals.set_ylabel('Total Accomplished Goals', fontsize=13, color='green')
    ax_steps.tick_params(axis='y', labelcolor='purple')
    ax_goals.tick_params(axis='y', labelcolor='green')
    ax_steps.set_title('Average Steps & Accomplished Goals vs Agent Ratio', fontsize=14, fontweight='bold')
    ax_steps.grid(True, alpha=0.3)
    ax_steps.legend([line1[0], line2[0]], ['Average Simulation Length', 'Total Accomplished Goals'], loc='upper right')

    dual_output = figures_dir / f"simulation_analysis_steps_and_goals_{exp_name_clean}.png"
    fig.tight_layout()
    fig.savefig(dual_output, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Normalized general metrics per step (formerly a 1x2 figure).
    steps = pd.to_numeric(df_summary['avg_steps_overall'], errors='coerce').replace(0, np.nan)
    norm_specs = [
        {
            'numerator': 'resource_conflicts',
            'sem': 'resource_conflicts_sem',
            'color': 'purple',
            'label': 'Resource Conflicts per Step',
            'ylabel': 'Resource Conflicts per Step',
            'title': 'Resource Conflicts per Step vs Agent Ratio',
            'filename': 'simulation_analysis_resource_conflicts_per_step'
        },
        {
            'numerator': 'counter_goal_accomplishments',
            'sem': 'counter_goal_accomplishments_sem',
            'color': 'brown',
            'label': 'Counter Goal Accomplishments per Step',
            'ylabel': 'Counter Goal Accomplishments per Step',
            'title': 'Counter Goal Accomplishments per Step vs Agent Ratio',
            'filename': 'simulation_analysis_counter_goal_accomplishments_per_step'
        }
    ]

    for spec in norm_specs:
        fig, ax = plt.subplots(figsize=(7.5, 5))
        values = df_summary[spec['numerator']] / steps
        errors = df_summary[spec['sem']] / steps

        ax.errorbar(
            ratio, values, yerr=errors,
            fmt='o-', linewidth=2, markersize=8, capsize=5,
            label=spec['label'], color=spec['color']
        )
        ax.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=11)
        ax.set_ylabel(spec['ylabel'], fontsize=11)
        ax.set_title(spec['title'], fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        output = figures_dir / f"{spec['filename']}_{exp_name_clean}.png"
        fig.tight_layout()
        fig.savefig(output, dpi=300, bbox_inches='tight')
        plt.close(fig)


def create_cumulative_plots_separate():
    """Create cumulative accomplished-goals figures per ratio (one file per ratio)."""

    df, _ = base_analysis.load_simulation_data(
        experiment_name=experiment_name,
        experiment_date=experiment_date,
    )

    if df.empty:
        raise RuntimeError("No simulation data found for the requested experiment.")

    figures_dir = _figures_dir('cumulative_by_ratio')
    results_dir = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")

    def _find_agent_file(prefix: str):
        main_data = results_dir / "data"
        candidate = main_data / f"{prefix}_agents.csv"
        if candidate.exists():
            return candidate
        for sub in results_dir.iterdir():
            if sub.is_dir():
                data_dir = sub / "data"
                alt = data_dir / f"{prefix}_agents.csv"
                if data_dir.exists() and alt.exists():
                    return alt
        return None

    unique_cfgs = df.groupby(['agent_config']).agg({
        'consent_first_count': 'mean',
        'goal_first_count': 'mean'
    }).reset_index().sort_values('goal_first_count')

    for _, cfg_row in unique_cfgs.iterrows():
        cfg = cfg_row['agent_config']
        seed_rows = df[df['agent_config'] == cfg]
        gf_series = []
        cf_series = []

        for _, srow in seed_rows.iterrows():
            config_name = srow.get('config_name')
            if not isinstance(config_name, str):
                continue
            prefix = config_name.rsplit('_', 1)[0]
            afile = _find_agent_file(prefix)
            if afile is None:
                continue

            adf = pd.read_csv(afile)
            step_col = 'Step' if 'Step' in adf.columns else adf.columns[0]
            if 'Agent Persona' not in adf.columns or 'Accomplished Goals' not in adf.columns:
                continue

            gf = adf[adf['Agent Persona'] == 'GoalFirstAgent'].groupby(step_col)['Accomplished Goals'].mean().sort_index()
            cf = adf[adf['Agent Persona'] == 'ConsentFirstAgent'].groupby(step_col)['Accomplished Goals'].mean().sort_index()

            if not gf.empty:
                gf_series.append(gf)
            if not cf.empty:
                cf_series.append(cf)

        if not gf_series and not cf_series:
            continue

        fig, ax = plt.subplots(figsize=(8, 5))
        if gf_series:
            all_steps_gf = sorted(set().union(*(s.index.tolist() for s in gf_series)))
            gf_aligned = [s.reindex(all_steps_gf, method='ffill').fillna(0) for s in gf_series]
            gf_values = pd.concat(gf_aligned, axis=1).mean(axis=1)
            ax.plot(gf_values.index, gf_values.values, 'r-', label='Teleological Agent (per agent)')
        if cf_series:
            all_steps_cf = sorted(set().union(*(s.index.tolist() for s in cf_series)))
            cf_aligned = [s.reindex(all_steps_cf, method='ffill').fillna(0) for s in cf_series]
            cf_values = pd.concat(cf_aligned, axis=1).mean(axis=1)
            ax.plot(cf_values.index, cf_values.values, 'g-', label='Deontic Agent (per agent)')

        ax.set_xlabel('Step')
        ax.set_ylabel('Cumulative Accomplished Goals per Agent')
        ax.set_title(
            f"TA:{int(round(cfg_row['goal_first_count']))} / "
            f"DA:{int(round(cfg_row['consent_first_count']))}"
        )
        ax.grid(True, alpha=0.3)
        ax.legend()

        filename = f"agent_level_cumulative_goals_{cfg.replace('-', '_')}.png"
        fig.tight_layout()
        fig.savefig(figures_dir / filename, dpi=300, bbox_inches='tight')
        plt.close(fig)


def _prepare_agent_summary():
    """Aggregate agent-level metrics exactly as in the base script."""

    df, _ = base_analysis.load_simulation_data(
        experiment_name=experiment_name,
        experiment_date=experiment_date,
    )

    if df.empty:
        raise RuntimeError("No simulation data found for the requested experiment.")

    agent_metrics_to_average = [
        'avg_accomplished_goals_consent_first_agent', 'avg_accomplished_goals_goal_first_agent',
        'avg_remaining_goals_consent_first_agent', 'avg_remaining_goals_goal_first_agent',
        'avg_total_consents_consent_first_r', 'avg_total_consents_goal_first_r',
        'avg_violated_consents_consent_first_r', 'avg_violated_consents_goal_first_r',
        'avg_fulfilled_consents_consent_first_r', 'avg_fulfilled_consents_goal_first_r',
        'avg_consent_violation_ratio_consent_first_r', 'avg_consent_violation_ratio_goal_first_r',
        'avg_consent_fulfillment_ratio_consent_first_r', 'avg_consent_fulfillment_ratio_goal_first_r',
        'avg_total_consents_consent_first_g', 'avg_total_consents_goal_first_g',
        'avg_violated_consents_consent_first_g', 'avg_violated_consents_goal_first_g',
        'avg_fulfilled_consents_consent_first_g', 'avg_fulfilled_consents_goal_first_g',
        'avg_consent_violation_ratio_consent_first_g', 'avg_consent_violation_ratio_goal_first_g',
        'avg_consent_fulfillment_ratio_consent_first_g', 'avg_consent_fulfillment_ratio_goal_first_g',
        'avg_resource_conflicts_consent_first_agent', 'avg_resource_conflicts_goal_first_agent',
        'avg_counter_goal_accomplishments_consent_first_agent', 'avg_counter_goal_accomplishments_goal_first_agent',
        'avg_resource_conflict_counter_goal_accomplishment_ratio_consent_first_agent',
        'avg_resource_conflict_counter_goal_accomplishment_ratio_goal_first_agent',
        'avg_counter_goal_per_resource_conflict_ratio_consent_first_agent',
        'avg_counter_goal_per_resource_conflict_ratio_goal_first_agent',
        'avg_total_idle_time_consent_first_agent', 'avg_total_idle_time_goal_first_agent',
        'avg_finished_step_consent_first_agent', 'avg_finished_step_goal_first_agent',
        'avg_longest_idle_time_consent_first_agent', 'avg_longest_idle_time_goal_first_agent',
        'avg_distinct_agents_interacted_r_consent_first_agent', 'avg_distinct_agents_interacted_r_goal_first_agent',
        'avg_distinct_agents_interacted_g_consent_first_agent', 'avg_distinct_agents_interacted_g_goal_first_agent'
    ]

    grouped = df.groupby(['experiment_name', 'agent_config'])
    mean_df = grouped[agent_metrics_to_average].mean().reset_index()
    std_df = grouped[agent_metrics_to_average].std().reset_index()
    sem_df = grouped[agent_metrics_to_average].sem().reset_index()
    count_df = grouped.size().reset_index(name='num_seeds')

    summary = mean_df.copy()
    for col in agent_metrics_to_average:
        summary[f'{col}_std'] = std_df[col]
        summary[f'{col}_sem'] = sem_df[col]

    summary = summary.merge(count_df, on=['experiment_name', 'agent_config'])

    config_columns = ['consent_first_count', 'goal_first_count', 'fifty_fifty_count', 'total_agents', 'avg_steps_overall']
    for col in config_columns:
        if col in df.columns:
            config_mean = df.groupby(['experiment_name', 'agent_config'])[col].mean().reset_index()
            summary = summary.merge(config_mean, on=['experiment_name', 'agent_config'])

    summary = summary.sort_values('goal_first_count')
    return summary


def create_agent_level_analysis_separate():
    """Create individual images for each agent-level metric."""

    df_agent = _prepare_agent_summary()
    figures_dir = _figures_dir('agent_level_separate')

    exp_name_clean = df_agent['experiment_name'].iloc[0]
    ratio = df_agent['goal_first_count'] / df_agent['total_agents']
    gf_mask = df_agent['goal_first_count'] > 0
    cf_mask = df_agent['consent_first_count'] > 0
    steps = pd.to_numeric(df_agent['avg_steps_overall'], errors='coerce').replace(0, np.nan)

    def save_dual_series_plot(filename, title, ylabel, cf_series, gf_series, cf_sem=None, gf_sem=None):
        fig, ax = plt.subplots(figsize=(7.5, 5))

        if cf_sem is not None and gf_sem is not None:
            ax.errorbar(ratio[cf_mask], cf_series[cf_mask], yerr=cf_sem[cf_mask],
                        fmt='o-', linewidth=2, markersize=6, capsize=4,
                        label='Deontic Agent', color='green')
            ax.errorbar(ratio[gf_mask], gf_series[gf_mask], yerr=gf_sem[gf_mask],
                        fmt='s-', linewidth=2, markersize=6, capsize=4,
                        label='Teleological Agent', color='red')
        else:
            ax.plot(ratio[cf_mask], cf_series[cf_mask], 'o-', linewidth=2, markersize=6,
                    label='Deontic Agent', color='green')
            ax.plot(ratio[gf_mask], gf_series[gf_mask], 's-', linewidth=2, markersize=6,
                    label='Teleological Agent', color='red')

        ax.set_xlabel('Teleological Agent Ratio (Teleological:All)', fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        fig.tight_layout()
        fig.savefig(figures_dir / f"{filename}_{exp_name_clean}.png", dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Receiver (R) metrics.
    save_dual_series_plot(
        filename='agent_level_R_violated_consents_per_agent',
        title='Violated Consents as Receiver per Agent Type',
        ylabel='Avg Violated Consents as R per Agent',
        cf_series=df_agent['avg_violated_consents_consent_first_r'],
        gf_series=df_agent['avg_violated_consents_goal_first_r'],
        cf_sem=df_agent['avg_violated_consents_consent_first_r_sem'],
        gf_sem=df_agent['avg_violated_consents_goal_first_r_sem']
    )

    save_dual_series_plot(
        filename='agent_level_R_total_consents_per_agent',
        title='Total Consents as Receiver per Agent Type',
        ylabel='Avg Total Consents as R per Agent',
        cf_series=df_agent['avg_total_consents_consent_first_r'],
        gf_series=df_agent['avg_total_consents_goal_first_r'],
        cf_sem=df_agent['avg_total_consents_consent_first_r_sem'],
        gf_sem=df_agent['avg_total_consents_goal_first_r_sem']
    )

    save_dual_series_plot(
        filename='agent_level_R_consent_violation_ratio',
        title='Consent Violation Ratio as Receiver per Agent Type',
        ylabel='Avg Consent Violation Ratio as R per Agent',
        cf_series=df_agent['avg_consent_violation_ratio_consent_first_r'],
        gf_series=df_agent['avg_consent_violation_ratio_goal_first_r'],
        cf_sem=df_agent['avg_consent_violation_ratio_consent_first_r_sem'],
        gf_sem=df_agent['avg_consent_violation_ratio_goal_first_r_sem']
    )

    save_dual_series_plot(
        filename='agent_level_R_consent_fulfillment_ratio',
        title='Consent Fulfillment Ratio as Receiver per Agent Type',
        ylabel='Avg Consent Fulfillment Ratio as R per Agent',
        cf_series=df_agent['avg_consent_fulfillment_ratio_consent_first_r'],
        gf_series=df_agent['avg_consent_fulfillment_ratio_goal_first_r'],
        cf_sem=df_agent['avg_consent_fulfillment_ratio_consent_first_r_sem'],
        gf_sem=df_agent['avg_consent_fulfillment_ratio_goal_first_r_sem']
    )

    # Giver (G) metrics.
    save_dual_series_plot(
        filename='agent_level_G_violated_consents_per_agent',
        title='Violated Consents as Giver per Agent Type',
        ylabel='Avg Violated Consents as G per Agent',
        cf_series=df_agent['avg_violated_consents_consent_first_g'],
        gf_series=df_agent['avg_violated_consents_goal_first_g'],
        cf_sem=df_agent['avg_violated_consents_consent_first_g_sem'],
        gf_sem=df_agent['avg_violated_consents_goal_first_g_sem']
    )

    save_dual_series_plot(
        filename='agent_level_G_total_consents_per_agent',
        title='Total Consents as Giver per Agent Type',
        ylabel='Avg Total Consents as G per Agent',
        cf_series=df_agent['avg_total_consents_consent_first_g'],
        gf_series=df_agent['avg_total_consents_goal_first_g'],
        cf_sem=df_agent['avg_total_consents_consent_first_g_sem'],
        gf_sem=df_agent['avg_total_consents_goal_first_g_sem']
    )

    save_dual_series_plot(
        filename='agent_level_G_consent_violation_ratio',
        title='Consent Violation Ratio as Giver per Agent Type',
        ylabel='Avg Consent Violation Ratio as G per Agent',
        cf_series=df_agent['avg_consent_violation_ratio_consent_first_g'],
        gf_series=df_agent['avg_consent_violation_ratio_goal_first_g'],
        cf_sem=df_agent['avg_consent_violation_ratio_consent_first_g_sem'],
        gf_sem=df_agent['avg_consent_violation_ratio_goal_first_g_sem']
    )

    save_dual_series_plot(
        filename='agent_level_G_consent_fulfillment_ratio',
        title='Consent Fulfillment Ratio as Giver per Agent Type',
        ylabel='Avg Consent Fulfillment Ratio as G per Agent',
        cf_series=df_agent['avg_consent_fulfillment_ratio_consent_first_g'],
        gf_series=df_agent['avg_consent_fulfillment_ratio_goal_first_g'],
        cf_sem=df_agent['avg_consent_fulfillment_ratio_consent_first_g_sem'],
        gf_sem=df_agent['avg_consent_fulfillment_ratio_goal_first_g_sem']
    )

    # General performance metrics.
    save_dual_series_plot(
        filename='agent_level_accomplished_goals_per_agent',
        title='Accomplished Goals per Agent Type',
        ylabel='Avg Accomplished Goals per Agent',
        cf_series=df_agent['avg_accomplished_goals_consent_first_agent'],
        gf_series=df_agent['avg_accomplished_goals_goal_first_agent'],
        cf_sem=df_agent['avg_accomplished_goals_consent_first_agent_sem'],
        gf_sem=df_agent['avg_accomplished_goals_goal_first_agent_sem']
    )

    save_dual_series_plot(
        filename='agent_level_remaining_goals_per_agent',
        title='Remaining Goals per Agent Type',
        ylabel='Avg Remaining Goals per Agent',
        cf_series=df_agent['avg_remaining_goals_consent_first_agent'],
        gf_series=df_agent['avg_remaining_goals_goal_first_agent'],
        cf_sem=df_agent['avg_remaining_goals_consent_first_agent_sem'],
        gf_sem=df_agent['avg_remaining_goals_goal_first_agent_sem']
    )

    save_dual_series_plot(
        filename='agent_level_resource_conflicts_per_agent',
        title='Resource Conflicts per Agent Type',
        ylabel='Avg Resource Conflicts per Agent',
        cf_series=df_agent['avg_resource_conflicts_consent_first_agent'],
        gf_series=df_agent['avg_resource_conflicts_goal_first_agent'],
        cf_sem=df_agent['avg_resource_conflicts_consent_first_agent_sem'],
        gf_sem=df_agent['avg_resource_conflicts_goal_first_agent_sem']
    )

    save_dual_series_plot(
        filename='agent_level_counter_goal_accomplishments_per_agent',
        title='Counter Goal Accomplishments per Agent Type',
        ylabel='Avg Counter Goal Accomplishments per Agent',
        cf_series=df_agent['avg_counter_goal_accomplishments_consent_first_agent'],
        gf_series=df_agent['avg_counter_goal_accomplishments_goal_first_agent'],
        cf_sem=df_agent['avg_counter_goal_accomplishments_consent_first_agent_sem'],
        gf_sem=df_agent['avg_counter_goal_accomplishments_goal_first_agent_sem']
    )

    # Total idle time (already separate in base script, keep the same output names).
    save_dual_series_plot(
        filename='agent_level_total_idle_time_per_agent',
        title='Total Idle Time per Agent Type',
        ylabel='Avg Total Idle Time per Agent',
        cf_series=df_agent['avg_total_idle_time_consent_first_agent'],
        gf_series=df_agent['avg_total_idle_time_goal_first_agent'],
        cf_sem=df_agent['avg_total_idle_time_consent_first_agent_sem'],
        gf_sem=df_agent['avg_total_idle_time_goal_first_agent_sem']
    )

    save_dual_series_plot(
        filename='agent_level_total_idle_time_per_agent_per_step',
        title='Total Idle Time per Agent normalized by Steps',
        ylabel='Avg Total Idle Time per Agent per Step',
        cf_series=df_agent['avg_total_idle_time_consent_first_agent'] / steps,
        gf_series=df_agent['avg_total_idle_time_goal_first_agent'] / steps
    )

    # Normalized conflict/counter-goal metrics per step.
    save_dual_series_plot(
        filename='agent_level_resource_conflicts_per_agent_per_step',
        title='Resource Conflicts per Agent normalized by Steps',
        ylabel='Avg Resource Conflicts per Agent per Step',
        cf_series=df_agent['avg_resource_conflicts_consent_first_agent'] / steps,
        gf_series=df_agent['avg_resource_conflicts_goal_first_agent'] / steps
    )

    save_dual_series_plot(
        filename='agent_level_counter_goals_per_agent_per_step',
        title='Counter Goal Accomplishments per Agent normalized by Steps',
        ylabel='Avg Counter Goal Accomplishments per Agent per Step',
        cf_series=df_agent['avg_counter_goal_accomplishments_consent_first_agent'] / steps,
        gf_series=df_agent['avg_counter_goal_accomplishments_goal_first_agent'] / steps
    )

    # Counter Goal Accomplishments per Resource Conflict Ratio.
    save_dual_series_plot(
        filename='agent_level_counter_goal_per_resource_conflict',
        title='Counter Goal Accomplishments per Resource Conflict per Agent Type',
        ylabel='Counter Goal Accomplishments per Resource Conflict',
        cf_series=df_agent['avg_counter_goal_per_resource_conflict_ratio_consent_first_agent'],
        gf_series=df_agent['avg_counter_goal_per_resource_conflict_ratio_goal_first_agent'],
        cf_sem=df_agent['avg_counter_goal_per_resource_conflict_ratio_consent_first_agent_sem'],
        gf_sem=df_agent['avg_counter_goal_per_resource_conflict_ratio_goal_first_agent_sem']
    )

    # Interaction & timing metrics.
    save_dual_series_plot(
        filename='agent_level_average_finished_step',
        title='Average Finished Step per Agent Type',
        ylabel='Avg Finished Step per Agent',
        cf_series=df_agent['avg_finished_step_consent_first_agent'],
        gf_series=df_agent['avg_finished_step_goal_first_agent'],
        cf_sem=df_agent['avg_finished_step_consent_first_agent_sem'],
        gf_sem=df_agent['avg_finished_step_goal_first_agent_sem']
    )

    save_dual_series_plot(
        filename='agent_level_longest_idle_time',
        title='Average Longest Idle Time per Agent Type',
        ylabel='Avg Longest Idle Time per Agent',
        cf_series=df_agent['avg_longest_idle_time_consent_first_agent'],
        gf_series=df_agent['avg_longest_idle_time_goal_first_agent'],
        cf_sem=df_agent['avg_longest_idle_time_consent_first_agent_sem'],
        gf_sem=df_agent['avg_longest_idle_time_goal_first_agent_sem']
    )

    save_dual_series_plot(
        filename='agent_level_distinct_agents_as_receiver',
        title='Average Distinct Agents Interacted as Receiver',
        ylabel='Avg Distinct Agents Interacted as R per Agent',
        cf_series=df_agent['avg_distinct_agents_interacted_r_consent_first_agent'],
        gf_series=df_agent['avg_distinct_agents_interacted_r_goal_first_agent'],
        cf_sem=df_agent['avg_distinct_agents_interacted_r_consent_first_agent_sem'],
        gf_sem=df_agent['avg_distinct_agents_interacted_r_goal_first_agent_sem']
    )

    save_dual_series_plot(
        filename='agent_level_distinct_agents_as_giver',
        title='Average Distinct Agents Interacted as Giver',
        ylabel='Avg Distinct Agents Interacted as G per Agent',
        cf_series=df_agent['avg_distinct_agents_interacted_g_consent_first_agent'],
        gf_series=df_agent['avg_distinct_agents_interacted_g_goal_first_agent'],
        cf_sem=df_agent['avg_distinct_agents_interacted_g_consent_first_agent_sem'],
        gf_sem=df_agent['avg_distinct_agents_interacted_g_goal_first_agent_sem']
    )


def run_all():
    create_agent_ratio_analysis_separate()
    create_cumulative_plots_separate()
    create_agent_level_analysis_separate()


if __name__ == "__main__":
    run_all()


