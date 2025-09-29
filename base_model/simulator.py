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

# Add the base_model directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from models.model import ConsentModel
from config import GOAL_FILE_PATH, TEST_CASE_PATH, MAX_STEP_COUNT

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
            model = ConsentModel(**config['parameters'])
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Run simulation
        step_count = 0
        while step_count < config.get('max_steps', MAX_STEP_COUNT):
            step_count += 1
            model.step()
            
            # Check if simulation should end
            if config.get('early_stop', True):
                # Check if all agents have no remaining goals
                all_goals_done = all(len(agent.remaining_goals) == 0 for agent in model.agents)
                if all_goals_done:
                    print(f"  All goals completed at step {step_count}")
                    break
        
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
    
    def save_results(self, results, filename_prefix="simulation"):
        """
        Save simulation results to files.
        
        Args:
            results (dict): Results from run_single_simulation
            filename_prefix (str): Prefix for output files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_name = results['config']['name'].replace(' ', '_').lower()
        
        # Save dataframes
        agent_file = self.results_dir / "data" / f"{filename_prefix}_{config_name}_{timestamp}_agents.csv"
        model_file = self.results_dir / "data" / f"{filename_prefix}_{config_name}_{timestamp}_model.csv"
        
        results['agent_data'].to_csv(agent_file)
        results['model_data'].to_csv(model_file)
        
        # Save configuration
        config_file = self.results_dir / "configs" / f"{filename_prefix}_{config_name}_{timestamp}_config.json"
        with open(config_file, 'w') as f:
            json.dump(results['config'], f, indent=2)
        
        # Save summary
        summary_file = self.results_dir / "logs" / f"{filename_prefix}_{config_name}_{timestamp}_summary.json"
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
    
    def run_experiment(self, experiment_config):
        """
        Run a full experiment with multiple configurations.
        
        Args:
            experiment_config (dict): Experiment configuration
        """
        print(f"🧪 Running Experiment: {experiment_config['name']}")
        print("=" * 60)
        
        experiment_results = []
        
        for config in experiment_config['configurations']:
            print(f"\n--- Configuration: {config['name']} ---")
            
            # Run simulation
            results = self.run_single_simulation(config, experiment_config.get('model_type', 'ConsentModel'))
            
            # Save results
            file_paths = self.save_results(results, experiment_config['name'].replace(' ', '_').lower())
            
            # Add file paths to results
            results['files'] = file_paths
            experiment_results.append(results)
        
        # Save experiment summary
        experiment_summary = {
            'experiment_name': experiment_config['name'],
            'model_type': experiment_config.get('model_type', 'ConsentModel'),
            'timestamp': datetime.now().isoformat(),
            'configurations': len(experiment_config['configurations']),
            'results': experiment_results
        }
        
        summary_file = self.results_dir / "logs" / f"experiment_{experiment_config['name'].replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(experiment_summary, f, indent=2)
        
        print(f"\n✅ Experiment completed! Summary saved to: {summary_file}")
        return experiment_results

def create_sample_experiments():
    """
    Create sample experiment configurations.
    """
    experiments = {
        'consent_or_goal_sensitivity_seed_42': {
            'name': 'Consent or Goal Sensitivity Analysis',
            'model_type': 'ConsentModel',
            'configurations': [
                {
                    'name': 'Seed 42: 1000-0-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 1000, 'GoalFirstAgent_COUNT': 0, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 900-100-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 900, 'GoalFirstAgent_COUNT': 100, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 800-200-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 800, 'GoalFirstAgent_COUNT': 200, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 700-300-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 700, 'GoalFirstAgent_COUNT': 300, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 600-400-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 600, 'GoalFirstAgent_COUNT': 400, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 500-500-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 500, 'GoalFirstAgent_COUNT': 500, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 400-600-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 400, 'GoalFirstAgent_COUNT': 600, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 300-700-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 300, 'GoalFirstAgent_COUNT': 700, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 200-800-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 200, 'GoalFirstAgent_COUNT': 800, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 100-900-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 100, 'GoalFirstAgent_COUNT': 900, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                },
                {
                    'name': 'Seed 42: 0-1000-0',
                    'parameters': {'seed': 42, 'GOAL_FILE_PATH': GOAL_FILE_PATH, 'TEST_CASE_PATH': TEST_CASE_PATH, 'TEST': False, 'MAX_STEP_COUNT': 1000, 'ConsentFirstAgent_COUNT': 0, 'GoalFirstAgent_COUNT': 1000, 'FiftyFiftyAgent_COUNT': 0},
                    'max_steps': 1000,
                    'early_stop': True
                }
            ]
        }
    }
    
    return experiments

def main():
    """
    Main function to run the simulator.
    """
    print("🚀 MESA Consent Model Simulator")
    print("=" * 50)
    
    # Create simulator instance
    simulator = Simulator(results_dir="simulation_results")
    
    # Get available experiments
    experiments = create_sample_experiments()
    
    print("\nAvailable experiments:")
    for i, (key, exp) in enumerate(experiments.items(), 1):
        print(f"  {i}. {exp['name']} ({len(exp['configurations'])} configurations)")
    
    # For now, run all experiments
    # In a real scenario, you might want to add user input to select specific experiments
    for exp_key, exp_config in experiments.items():
        print(f"\n{'='*60}")
        simulator.run_experiment(exp_config)
    
    print(f"\n🎉 All simulations completed! Results saved in: {simulator.results_dir}")

if __name__ == "__main__":
    main()
