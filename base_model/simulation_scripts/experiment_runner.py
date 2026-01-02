#!/usr/bin/env python3
"""
Experiment Runner - A flexible script to run experiments with configurable settings.
This script allows you to define experiment configurations and feed them to the simulator.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime

# Set this to the experiment JSON you want to run when executing from the IDE
EXPERIMENT_CONFIG_PATH = (
    Path(__file__).resolve().parent / "experiment_configs" / "sample_experiment.json"
)

# Optional: adjust sys.path if needed (not required when running from IDE in repo root)
# sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulator import Simulator

class ExperimentRunner:
    """
    A flexible experiment runner that can load configurations from files or create them programmatically.
    """
    
    def __init__(self, results_dir="simulation_results"):
        """
        Initialize the experiment runner.
        
        Args:
            results_dir (str): Directory to save results
        """
        self.simulator = Simulator(results_dir)
        self.results_dir = Path(results_dir)
        
    def load_experiment_from_file(self, config_file):
        """
        Load experiment configuration from a JSON or YAML file.
        
        Args:
            config_file (str): Path to configuration file
            
        Returns:
            dict: Experiment configuration
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {config_path.suffix}")
        
        return config
    
    def create_sensitivity_analysis_experiment(self, 
                                            experiment_name="Consent or Goal Sensitivity Analysis",
                                            agent_counts=None,
                                            max_steps=1000,
                                            early_stop_steps=50,
                                            seeds=None,
                                            goal_file_path=None,
                                            test_case_path=None):
        """
        Create a sensitivity analysis experiment with different agent ratios.
        
        Args:
            experiment_name (str): Name of the experiment
            agent_counts (list): List of tuples (consent_first, goal_first, fifty_fifty, monitoring)
            max_steps (int): Maximum number of steps
            early_stop_steps (int): Steps to wait before early stopping
            seeds (list): List of seeds to run
            goal_file_path (str): Path to goal file
            test_case_path (str): Path to test case file
            
        Returns:
            dict: Experiment configuration
        """
        if agent_counts is None:
            # Default agent count configurations
            agent_counts = [
                (1000, 0, 0, 0),    # All consent-first
                (900, 100, 0, 0),   # Mostly consent-first
                (800, 200, 0, 0),
                (700, 300, 0, 0),
                (600, 400, 0, 0),
                (500, 500, 0, 0),   # Equal split
                (400, 600, 0, 0),
                (300, 700, 0, 0),
                (200, 800, 0, 0),
                (100, 900, 0, 0),
                (0, 1000, 0, 0),    # All goal-first
            ]
        
        if seeds is None:
            seeds = [2, 13, 24, 35, 42, 123, 413, 456, 789, 999]  # Default seeds
        
        if goal_file_path is None:
            goal_file_path = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/goals/goal_tree.yaml"
        
        if test_case_path is None:
            test_case_path = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/test_cases/test_007_01_CONSENT_BASED_AU_fulfilment_viol_expiry_activation.yaml"
        
        configurations = []
        
        for consent_first, goal_first, fifty_fifty, monitoring in agent_counts:
            config_name = f"{consent_first}-{goal_first}-{fifty_fifty}-{monitoring}"
            
            config = {
                'name': config_name,
                'parameters': {
                    'seed': None,  # Will be set per seed
                    'GOAL_FILE_PATH': goal_file_path,
                    'TEST_CASE_PATH': test_case_path,
                    'TEST': False,
                    'MAX_STEP_COUNT': max_steps,
                    'ConsentFirstAgent_COUNT': consent_first,
                    'GoalFirstAgent_COUNT': goal_first,
                    'FiftyFiftyAgent_COUNT': fifty_fifty,
                    'MonitoringAgent_COUNT': monitoring,
                    'CO_exp_step': 5,
                    'AU_exp_step': 3,
                    'random_exp_times': False,
                    'max_random_AU_exp_step': 7,
                    'min_random_AU_exp_step': 3,
                    'max_random_CO_exp_step': 7,
                    'min_random_CO_exp_step': 3,
                    'print_state': False,
                    'print_execution': False
                }
            }
            configurations.append(config)
        
        experiment_config = {
            'name': experiment_name,
            'model_type': 'ConsentModel',
            'max_steps': max_steps,
            'early_stop_steps': early_stop_steps,
            'early_stop': True,
            'configurations': configurations
        }
        
        return experiment_config
    
    def create_custom_experiment(self, name, configurations, model_type='ConsentModel', **kwargs):
        """
        Create a custom experiment with specified configurations.
        
        Args:
            name (str): Experiment name
            configurations (list): List of configuration dictionaries
            model_type (str): Type of model to use
            **kwargs: Additional experiment parameters
            
        Returns:
            dict: Experiment configuration
        """
        experiment_config = {
            'name': name,
            'model_type': model_type,
            'configurations': configurations,
            **kwargs
        }
        
        return experiment_config
    
    def run_experiment_from_config(self, experiment_config, multi_seed=True):
        """
        Run an experiment from a configuration dictionary.
        
        Args:
            experiment_config (dict): Experiment configuration
            multi_seed (bool): Whether to run multiple seeds
            
        Returns:
            list: Experiment results
        """
        print(f"🚀 Starting Experiment: {experiment_config['name']}")
        print("=" * 60)
        
        if multi_seed and 'seeds' in experiment_config:
            # Run multi-seed experiment
            seeds = experiment_config['seeds']
            base_config = {k: v for k, v in experiment_config.items() if k != 'seeds'}
            results = self.simulator.run_multi_seed_experiment(base_config, seeds)
        else:
            # Run single experiment
            results = self.simulator.run_experiment(experiment_config)
        
        return results
    
    def save_experiment_config(self, experiment_config, filename=None):
        """
        Save experiment configuration to a file.
        
        Args:
            experiment_config (dict): Experiment configuration
            filename (str, optional): Filename to save to. If None, generates based on experiment name.
        """
        if filename is None:
            safe_name = experiment_config['name'].replace(' ', '_').lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"experiment_config_{safe_name}_{timestamp}.json"
        
        config_path = self.results_dir / filename
        
        with open(config_path, 'w') as f:
            json.dump(experiment_config, f, indent=2)
        
        print(f"📁 Experiment configuration saved to: {config_path}")
        return config_path

def main():
    """
    Run using the EXPERIMENT_CONFIG_PATH variable (no CLI args needed).
    """
    # Initialize experiment runner
    runner = ExperimentRunner(results_dir="simulation_results")

    # Load experiment configuration from the variable
    if not EXPERIMENT_CONFIG_PATH or not Path(EXPERIMENT_CONFIG_PATH).exists():
        print("❌ EXPERIMENT_CONFIG_PATH is not set or file does not exist:", EXPERIMENT_CONFIG_PATH)
        return

    experiment_config = runner.load_experiment_from_file(str(EXPERIMENT_CONFIG_PATH))
    print(f"📋 Loaded experiment configuration from: {EXPERIMENT_CONFIG_PATH}")

    # Run the experiment
    try:
        results = runner.run_experiment_from_config(experiment_config, multi_seed=True)
        print(f"\n✅ Experiment completed successfully!")
        print(f"📊 Total configurations run: {len(results)}")
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        raise

if __name__ == "__main__":
    main()
