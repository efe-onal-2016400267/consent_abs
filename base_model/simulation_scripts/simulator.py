#!/usr/bin/env python3
"""
Simulator - A comprehensive script to run the consent model with different configurations
and save results for analysis.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
import yaml

# Ensure the base_model directory is on sys.path (parent of simulation_scripts)
BASE_MODEL_DIR = Path(__file__).resolve().parent.parent
if str(BASE_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_MODEL_DIR))

from models.model import ConsentModel
from config import GOAL_FILE_PATH, TEST_CASE_PATH, MAX_STEP_COUNT

# Optional: Set this to a JSON/YAML file to load experiments externally
# Default points to sample_experiment.json next to this script
EXPERIMENTS_FILE_PATH = (Path(__file__).resolve().parent / "experiment_configs" / "monitoring_vs_consent_based.json")

class Simulator:
    """
    A simulator class to run experiments with different model configurations.
    """
    
    def __init__(self, results_dir="results"):
        """
        Initialize the simulator.
        
        Args:
            results_dir (str): Directory to save results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of results
        (self.results_dir / "data").mkdir(exist_ok=True)
        (self.results_dir / "configs").mkdir(exist_ok=True)
        (self.results_dir / "logs").mkdir(exist_ok=True)
    
    def run_single_simulation(self, config, model_type="ConsentModel"):
        """
        Run a single simulation with given configuration.
        
        Args:
            config (dict): Configuration parameters
            model_type (str): Type of model to run ("ConsentModel" or "NoConsentModel")
            
        Returns:
            dict: Results including dataframes and metadata
        """
        print(f"Running {model_type} with config: {config['name']}")
        
        # Create model instance
        if model_type == "ConsentModel":
            # Filter parameters to the set accepted by ConsentModel to keep JSON shape minimal
            allowed_keys = {
                'seed',
                'GOAL_FILE_PATH', 'TEST_CASE_PATH', 'TEST', 'MAX_STEP_COUNT',
                'ConsentFirstAgent_COUNT', 'GoalFirstAgent_COUNT', 'FiftyFiftyAgent_COUNT', 'MonitoringAgent_COUNT'
            }
            filtered_params = {k: v for k, v in config.get('parameters', {}).items() if k in allowed_keys}
            model = ConsentModel(**filtered_params)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Run simulation
        step_count = 0
        early_stop_steps = config.get('early_stop_steps', -1)
        unchanged_steps = 0 # We'll keep the number of consecutive steps where no new goals were accomplished.
        last_goal_count = -1
        while step_count < config.get('max_steps', MAX_STEP_COUNT):
            step_count += 1
            model.step()
            
            # Check for early stopping
            # If no additional goals were accomplished in the last N steps,
            # Stop the simulation.
            if config.get('early_stop', True):
                # Check if all agents have no remaining goals
                all_goals_done = all(len(agent.remaining_goals) == 0 for agent in model.agents)
                if all_goals_done:
                    print(f"  All goals completed at step {step_count}")
                    break
                
                # Early stopping.
                model_vars = model.datacollector.get_model_vars_dataframe()
                goal_count = model_vars['Total Remaining Goals'].iloc[-1]
                if last_goal_count == goal_count:
                    unchanged_steps += 1
                else:
                    unchanged_steps = 0
                if unchanged_steps >= early_stop_steps:
                    print(f"  No new goals accomplished in the last {early_stop_steps} steps. Stopping at step {step_count}")
                    break

                last_goal_count = goal_count

                if step_count % 25 == 0:
                    print(f"  Step {step_count} of {config.get('max_steps', MAX_STEP_COUNT)}")
        
        # Collect results
        agent_vars = model.datacollector.get_agent_vars_dataframe()
        model_vars = model.datacollector.get_model_vars_dataframe()
        
        results = {
            'config': config,
            'model_type': model_type,
            'agent_data': agent_vars,
            'model_data': model_vars,
            'summary': {
                'steps_run': step_count,
                'timestamp': datetime.now().isoformat()
            }
        }

        return results
    
    def save_results(self, results, filename_prefix="simulation", timestamp=None, output_root=None):
        """
        Save simulation results to files.
        
        Args:
            results (dict): Results from run_single_simulation
            filename_prefix (str): Prefix for output files
            timestamp (str, optional): Timestamp string to use for filenames. If None, generates a new one.
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_name = results['config']['name'].replace(' ', '_').lower()
        # Decide root output directory
        root_dir = Path(output_root) if output_root else self.results_dir
        # Ensure subdirectories exist
        (root_dir / "data").mkdir(parents=True, exist_ok=True)
        (root_dir / "configs").mkdir(parents=True, exist_ok=True)
        (root_dir / "logs").mkdir(parents=True, exist_ok=True)
        
        # Save dataframes
        agent_file = root_dir / "data" / f"{filename_prefix}_{config_name}_{timestamp}_agents.csv"
        model_file = root_dir / "data" / f"{filename_prefix}_{config_name}_{timestamp}_model.csv"
        
        results['agent_data'].to_csv(agent_file)
        results['model_data'].to_csv(model_file)
        
        # Save configuration
        config_file = root_dir / "configs" / f"{filename_prefix}_{config_name}_{timestamp}_config.json"
        with open(config_file, 'w') as f:
            json.dump(results['config'], f, indent=2)
        
        # Save summary
        summary_file = root_dir / "logs" / f"{filename_prefix}_{config_name}_{timestamp}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(results['summary'], f, indent=2)
        
        print(f"  Results saved:")
        print(f"    Agent data: {agent_file}")
        print(f"    Model data: {model_file}")
        print(f"    Config: {config_file}")
        print(f"    Summary: {summary_file}")
        
        return {
            'agent_file': str(agent_file),
            'model_file': str(model_file),
            'config_file': str(config_file),
            'summary_file': str(summary_file)
        }
    
    def run_experiment(self, experiment_config, experiment_root: Path | None = None, experiment_timestamp: str | None = None):
        """
        Run a full experiment with multiple configurations.
        
        Args:
            experiment_config (dict): Experiment configuration
        """
        print(f"🧪 Running Experiment: {experiment_config['name']}")
        print("=" * 60)
        
        # Generate a single timestamp for all files in this experiment (unless provided)
        if experiment_timestamp is None:
            experiment_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Compute or ensure experiment root folder under simulation_results: <experiment_name>_<date>
        if experiment_root is None:
            date_only = datetime.now().strftime("%Y%m%d")
            experiment_name_safe = experiment_config['name'].replace(' ', '_').lower()
            experiment_root = self.results_dir / f"{experiment_name_safe}_{date_only}"
        (Path(experiment_root) / "data").mkdir(parents=True, exist_ok=True)
        (Path(experiment_root) / "configs").mkdir(parents=True, exist_ok=True)
        (Path(experiment_root) / "logs").mkdir(parents=True, exist_ok=True)
        
        experiment_results = []
        
        for config in experiment_config['configurations']:
            print(f"\n--- Configuration: {config['name']} ---")
            
            # Ensure per-config execution settings inherit from experiment-level defaults
            cfg = dict(config)  # shallow copy is enough for our keys
            cfg.setdefault('max_steps', experiment_config.get('max_steps', MAX_STEP_COUNT))
            cfg.setdefault('early_stop', experiment_config.get('early_stop', True))
            cfg.setdefault('early_stop_steps', experiment_config.get('early_stop_steps', 50))

            # Run simulation
            results = self.run_single_simulation(cfg, experiment_config.get('model_type', 'ConsentModel'))
            
            # Save results with the shared experiment timestamp
            file_paths = self.save_results(
                results,
                experiment_config['name'].replace(' ', '_').lower(),
                timestamp=experiment_timestamp,
                output_root=experiment_root
            )
            
            # Add file paths to results
            results['files'] = file_paths
            experiment_results.append(results)
        
        # Save experiment summary (without DataFrames for JSON serialization)
        experiment_summary = {
            'experiment_name': experiment_config['name'],
            'model_type': experiment_config.get('model_type', 'ConsentModel'),
            'timestamp': datetime.now().isoformat(),
            'configurations': len(experiment_config['configurations']),
            'results': [
                {
                    'config': result['config'],
                    'model_type': result['model_type'],
                    'summary': result['summary'],
                    'files': result.get('files', {})
                }
                for result in experiment_results
            ]
        }
        
        summary_file = Path(experiment_root) / "logs" / f"experiment_{experiment_config['name'].replace(' ', '_').lower()}_{experiment_timestamp}.json"
        if experiment_summary:
            with open(summary_file, 'w') as f:
                json.dump(experiment_summary, f, indent=2)
            
            print(f"\n✅ Experiment completed! Summary saved to: {summary_file}")
        return experiment_results
    
    def run_multi_seed_experiment(self, base_experiment_config, seeds):
        """
        Run the same experiment for multiple seeds.
        
        Args:
            base_experiment_config (dict): Base experiment configuration (without specific seeds)
            seeds (list): List of seeds to run experiments for
            
        Returns:
            list: List of experiment results for all seeds
        """
        print(f"Running Multi-Seed Experiment: {base_experiment_config['name']}")
        print(f"Seeds: {seeds}")
        print("=" * 60)
        
        # Generate timestamp and shared experiment root for all seeds
        multi_seed_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_only = datetime.now().strftime("%Y%m%d")
        experiment_name_safe = base_experiment_config['name'].replace(' ', '_').lower()
        shared_experiment_root = self.results_dir / f"{experiment_name_safe}_{date_only}"
        (shared_experiment_root / "data").mkdir(parents=True, exist_ok=True)
        (shared_experiment_root / "configs").mkdir(parents=True, exist_ok=True)
        (shared_experiment_root / "logs").mkdir(parents=True, exist_ok=True)
        
        all_seed_results = []
        
        for seed in seeds:
            print(f"\n🔢 Running for seed: {seed}")
            print("-" * 40)
            
            # Create seed-specific experiment config
            seed_experiment_config = self._create_seed_experiment_config(base_experiment_config, seed)
            
            # Run experiment for this seed (each seed experiment gets its own timestamp)
            seed_results = self.run_experiment(
                seed_experiment_config,
                experiment_root=shared_experiment_root,
                experiment_timestamp=multi_seed_timestamp
            )
            all_seed_results.extend(seed_results)
        
        # Save multi-seed summary (without DataFrames for JSON serialization)
        multi_seed_summary = {
            'experiment_name': f"{base_experiment_config['name']} (Multi-Seed)",
            'model_type': base_experiment_config.get('model_type', 'ConsentModel'),
            'seeds_used': seeds,
            'total_configurations': len(all_seed_results),
            'timestamp': datetime.now().isoformat(),
            'seed_results': [
                {
                    'config': result['config'],
                    'model_type': result['model_type'],
                    'summary': result['summary'],
                    'files': result.get('files', {})
                }
                for result in all_seed_results
            ]
        }
        
        summary_file = shared_experiment_root / "logs" / f"multi_seed_{base_experiment_config['name'].replace(' ', '_').lower()}_{multi_seed_timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(multi_seed_summary, f, indent=2)
        
        print(f"\n🎯 Multi-seed experiment completed! Summary saved to: {summary_file}")
        return all_seed_results
    
    def _create_seed_experiment_config(self, base_config, seed):
        """
        Create a seed-specific experiment configuration by updating all parameter seeds.
        
        Args:
            base_config (dict): Base experiment configuration
            seed (int): Seed value to use
            
        Returns:
            dict: Seed-specific experiment configuration
        """
        import copy
        seed_config = copy.deepcopy(base_config)
        seed_config['name'] = f"{base_config['name']} (Seed {seed})"
        
        # Update all configurations to use the specified seed
        for config in seed_config['configurations']:
            config['parameters']['seed'] = seed
            # Update config name to include seed
            config['name'] = f"Seed {seed}: {config['name']}"
        
        return seed_config

def create_sample_experiments():
    """
    Create sample experiment configurations.
    """
    experiments = {
        'consent_or_goal_sensitivity': {
            'name': 'Consent or Goal Sensitivity Analysis',
            'model_type': 'ConsentModel',
            'configurations': [
                {
                    'name': '1000-0-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 1000, 'GoalFirstAgent_COUNT': 0, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '900-100-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 900, 'GoalFirstAgent_COUNT': 100, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '800-200-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 800, 'GoalFirstAgent_COUNT': 200, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '700-300-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 700, 'GoalFirstAgent_COUNT': 300, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '600-400-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 600, 'GoalFirstAgent_COUNT': 400, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '500-500-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 500, 'GoalFirstAgent_COUNT': 500, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '400-600-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 400, 'GoalFirstAgent_COUNT': 600, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '300-700-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 300, 'GoalFirstAgent_COUNT': 700, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '200-800-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 200, 'GoalFirstAgent_COUNT': 800, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '100-900-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 100, 'GoalFirstAgent_COUNT': 900, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                },
                {
                    'name': '0-1000-0',
                    'parameters': {'seed': None, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 0, 'GoalFirstAgent_COUNT': 1000, 'FiftyFiftyAgent_COUNT': 0, 'MonitoringAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True,
                    'early_stop_steps': 50,
                }
            ]
        }
    }
    
    return experiments

def load_experiments_from_file(path):
    """Load one or more experiments from a JSON/YAML file.
    Supports:
    - A single experiment object with configurations (wrapped into a dict)
    - A list of experiment objects (converted to a dict keyed by experiment name)
    - An object with key 'experiments' mapping names to experiment objects
    """
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Experiments file not found: {cfg_path}")
    with open(cfg_path, 'r') as f:
        if cfg_path.suffix.lower() in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    # Single experiment object
    if isinstance(data, dict) and 'configurations' in data:
        return {data.get('name', 'external_experiment'): data}

    # Experiments under a root key
    if isinstance(data, dict) and 'experiments' in data and isinstance(data['experiments'], dict):
        return data['experiments']

    # List of experiments
    if isinstance(data, list):
        result = {}
        for exp in data:
            if isinstance(exp, dict) and 'configurations' in exp:
                name = exp.get('name', f"exp_{len(result)+1}")
                result[name] = exp
        if result:
            return result

    raise ValueError("Unsupported experiments file format. Provide a single experiment object, a list of experiments, or an object with 'experiments'.")

def main():
    """
    Main function to run the simulator.
    """
    print("🚀 MESA Consent Model Simulator")
    print("=" * 50)
    
    # Create simulator instance
    simulator = Simulator(results_dir="simulation_results")
    
    # Get experiments: prefer external file if present
    if EXPERIMENTS_FILE_PATH and EXPERIMENTS_FILE_PATH.exists():
        print(f"📄 Loading experiments from: {EXPERIMENTS_FILE_PATH}")
        experiments = load_experiments_from_file(EXPERIMENTS_FILE_PATH)
    else:
        experiments = create_sample_experiments()
    
    print("\nAvailable experiments:")
    for i, (key, exp) in enumerate(experiments.items(), 1):
        print(f"  {i}. {exp['name']} ({len(exp['configurations'])} configurations)")
    
    # Define seeds to run experiments for
    seeds = [2, 13, 24, 35, 42, 123, 413, 456, 789, 999]
    
    print(f"\n🌱 Running experiments for seeds: {seeds}")
    
    # Run multi-seed experiments
    for exp_key, exp_config in experiments.items():
        print(f"\n{'='*60}")
        simulator.run_multi_seed_experiment(exp_config, seeds)
    
    print(f"\n🎉 All multi-seed simulations completed! Results saved in: {simulator.results_dir}")

if __name__ == "__main__":
    main()
