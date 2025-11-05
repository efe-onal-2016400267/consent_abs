#!/usr/bin/env python3
"""
Diagnostics: Validate that consent violations as Receiver (R) align with
counter goal accomplishments at the agent level.

- Loads all *_agents.csv under simulation_results/**/data
- For each run (config), looks at the last step per agent
- Aggregates by Agent Persona (ConsentFirstAgent, MonitoringAgent, GoalFirstAgent)
  and reports cases where:
    avg(Number of Consents as R Violated) == 0 but
    avg(Counter Conflict Goal Accomplishments) > 0

Usage:
  python diagnostics_consent_r_violations_vs_counter_goals.py
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import re


def find_agent_csvs(root: Path) -> list[Path]:
    agent_csvs = []
    for sub in root.rglob("*_agents.csv"):
        # skip non-data locations if any
        if "simulation_results" in str(sub) and "data" in str(sub.parent):
            agent_csvs.append(sub)
    return sorted(agent_csvs)


def extract_config_id(p: Path) -> str:
    # Use stem up to the last underscore before suffix like _agents.csv
    # Example: monitoring_vs_consent_based_analysis_(seed_2)_seed_2:_0-0-0-1000_20251023_175952_agents.csv
    return p.stem.replace("_agents", "")


def analyze_file(agent_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(agent_csv)
    if df.empty:
        return pd.DataFrame()

    # Determine last step value (first column may be Step or unnamed index)
    step_col = "Step" if "Step" in df.columns else df.columns[0]
    steps = pd.to_numeric(df[step_col], errors="coerce")
    last_step = steps.max()
    last_rows = df[steps == last_step].copy()

    # Ensure numeric for target columns
    num_cols = [
        "Counter Conflict Goal Accomplishments",
        "Number of Consents as R Violated",
    ]
    for c in num_cols:
        if c in last_rows.columns:
            last_rows[c] = pd.to_numeric(last_rows[c], errors="coerce").fillna(0)

    last_rows["config_id"] = extract_config_id(agent_csv)
    return last_rows


def main():
    # Allow optional argument to point to a specific simulation_results directory
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).expanduser().resolve()
    else:
        root = Path("/Users/efeonal/py_envs/MESA_thesis/consent_abs/simulation_results")
    agent_csvs = find_agent_csvs(root)
    if not agent_csvs:
        print("No agent CSVs found.")
        return

    frames = []
    for csv in agent_csvs:
        try:
            frames.append(analyze_file(csv))
        except Exception as e:
            print(f"Error reading {csv}: {e}")

    if not frames:
        print("No data assembled from agent CSVs.")
        return

    all_last = pd.concat(frames, ignore_index=True)
    if all_last.empty:
        print("No last-step rows assembled.")
        return

    group_cols = ["config_id", "Agent Persona"]
    agg = all_last.groupby(group_cols).agg(
        avg_counter_goals=("Counter Conflict Goal Accomplishments", "mean"),
        avg_violations_r=("Number of Consents as R Violated", "mean"),
        agent_count=("AgentID", "nunique") if "AgentID" in all_last.columns else (step_col, "count"),
    ).reset_index()

    inconsistent = agg[(agg["avg_violations_r"] == 0) & (agg["avg_counter_goals"] > 0)]

    print("\n=== Diagnostics: R Violations vs Counter Goals (last-step, averaged per config/persona) ===")
    print(agg.head(20).to_string(index=False))

    if inconsistent.empty:
        print("\nNo inconsistencies: Every persona with counter goals > 0 also has some R violations.")
    else:
        print(f"\nFound {len(inconsistent)} config/persona pairs with 0 R-violations but >0 counter goals:")
        print(inconsistent.to_string(index=False))

        # Show a few raw rows for the first offending config/persona
        sample = inconsistent.iloc[0]
        cfg = sample["config_id"]
        persona = sample["Agent Persona"]
        raw = all_last[(all_last["config_id"] == cfg) & (all_last["Agent Persona"] == persona)]
        cols = [
            "AgentID",
            "Counter Conflict Goal Accomplishments",
            "Number of Consents as R Violated",
            "Number of Consents as G Violated" if "Number of Consents as G Violated" in all_last.columns else None,
        ]
        cols = [c for c in cols if c is not None and c in raw.columns]
        print("\nSample offending last-step agent rows:")
        print(raw[cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()


