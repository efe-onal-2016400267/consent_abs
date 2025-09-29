from config import GOAL_FILE_PATH, TEST_CASE_PATH, TEST, MAX_STEP_COUNT
from state import EnvState

from pathlib import Path
import mesa
import numpy as np
from base_agent import BaseChefAgent
from resource import Resource
from mesa.experimental.cell_space import OrthogonalVonNeumannGrid
#from mesa.experimental.cell_space.property_layer import PropertyLayer
import yaml
from model_level_collectors import (model_level_remaining_goals, 
                                    model_level_accomplished_goals, 
                                    model_level_active_consents,
                                    model_level_fulfilled_consents,
                                    model_level_violated_consents,
                                    model_level_unrealized_consents,
                                    model_level_deferred_consents,
                                    model_level_total_consents, 
                                    model_level_AU_activations,
                                    model_level_AU_expirations,
                                    model_level_AU_fulfilments,
                                    model_level_AU_vioaltions,
                                    model_level_CO_activations,
                                    model_level_CO_fulfilments,
                                    model_level_CO_violations)


class NoConsentModel(mesa.Model):
    """
    Model class with no consent reasoning.
    """

    def __init__(self, 
                width=50,
                height=50,
                initial_population=100,
                seed = None,
                goal_per_agent = 3,
                resource_per_agent = 3,
                resources = [],
                GOAL_FILE_PATH = GOAL_FILE_PATH, 
                TEST_CASE_PATH = TEST_CASE_PATH,
                TEST = TEST,
                MAX_STEP_COUNT = MAX_STEP_COUNT
                ):
        super().__init__(seed=seed)
        self.state = EnvState()

         # initiate width and height of the grid
        self.width = width
        self.height = height
        self.goal_per_agent = goal_per_agent
        self.resource_per_agent = resource_per_agent
        self.initial_population = initial_population
        self.resources = resources
        self.GOAL_FILE_PATH = GOAL_FILE_PATH
        self.TEST_CASE_PATH = TEST_CASE_PATH
        self.TEST = TEST
        self.MAX_STEP_COUNT = MAX_STEP_COUNT
        self.running = True
        self.grid = OrthogonalVonNeumannGrid(
            (self.width, self.height), torus=False, random=self.random
        )   

        if self.TEST:
            with open(self.TEST_CASE_PATH, 'r') as f:
                test_case_data = yaml.safe_load(f)["agents"]
                self.goals_of_agents = []
                self.resources_of_agents = []

                for agent in test_case_data:
                    # prepare goal tuples
                    if agent["goals"]:
                        goals = [(g["name"], tuple(g["sub_goals"])) for g in agent["goals"]]
                    else:
                        goals = []
                    self.goals_of_agents.append(goals)

                    # prepare resource tuples
                    # Create Resource instances and assign ownership
                    if agent["resources"]:
                        resource_instances = [
                            Resource(name=r["name"], owner=agent["id"], type=r["type"]) for r in agent["resources"]
                        ]
                    else:
                        resource_instances = []
                    self.resources_of_agents.append(resource_instances)

                # By feeding persona numbers to this function, I can create different types of agents in a single simulation.
                self.create_agents_from_model(n=len(test_case_data))
        else:
            # Read the yaml file first to get the goals
            with open(self.GOAL_FILE_PATH, 'r') as f:
                self.all_goals = yaml.safe_load(f)["goals"]

            # in resources we hold different resource types extractd from distinct subgoals.
            # in goals we hold unique goals and their subgoals.
            self.goals = set()
            self.resources = set()

            for goal in self.all_goals:
                subgoals = tuple(sg["name"] for sg in goal["sub_goals"])
                self.goals.add((goal["name"], subgoals))
                for sub in subgoals:
                    self.resources.add(sub.split("_")[1])

            self.goals = list(self.goals)
            self.resources = list(self.resources)

            # now for each agent, we'll create a different set of goals and resources. Let each agent have 2 goals and 2 resources.
            # TODO: Make sure all resources exist in the model, that is all goals are achievable.
            # TODO: But we need to make these resources instances of the resource class. How would we do that?
            self.goals_of_agents = []
            self.resources_of_agents = []
            for agent_index in range(self.initial_population):
                self.goals_of_agents.append(self.random.sample(self.goals, k=self.goal_per_agent))

                # Sample resource types (e.g., 'egg', 'oven')
                resource_types = self.random.sample(self.resources, k=self.resource_per_agent)

                # Create Resource instances and assign ownership
                resource_instances = [
                    Resource(name=f"{res_type}_{agent_index+1}_{i}", owner=agent_index+1, type=res_type)
                    for i, res_type in enumerate(resource_types)
                ]
                self.resources_of_agents.append(resource_instances)

            self.create_agents_from_model(n=self.initial_population)

        self.datacollector = mesa.DataCollector(
                    agent_reporters={"Accomplished Goals": "num_accomplished_goals", "Remaining Goals": "num_remaining_goals"},
                    model_reporters={"Total Accomplished Goals": model_level_accomplished_goals,
                                      "Total Remaining Goals": model_level_remaining_goals,
                                      "Total Active Consents": model_level_active_consents,
                                      "Total Fulfilled Consents": model_level_fulfilled_consents,
                                      "Total Violated Consents": model_level_violated_consents,
                                      "Total Unrealized Consents": model_level_unrealized_consents,
                                      "Total Deferred Consents": model_level_deferred_consents,
                                      "Total Consents": model_level_total_consents,
                                      "Total AU Activations": model_level_AU_activations,
                                      "Total AU Expirations": model_level_AU_expirations,
                                      "Total AU Violations": model_level_AU_vioaltions,
                                      "Total AU Fulfilments": model_level_AU_fulfilments,
                                      "Total CO Activations": model_level_CO_activations,
                                      "Total CO Violations": model_level_CO_violations,
                                      "Total CO Fulfilments": model_level_CO_fulfilments}
                    )
        # Collect initial state (before any agent actions)
        self.collect_initial_state()

    def step(self):
        self.agents.do("interpret_goals")
        
        # Call parent step method for common data collection logic
        super().step()

    def create_agents_from_model(self, n):
        """
        A helper function to create agents.
        Called from __init__ function.
        This way, I dont have to override the whole init in ConsentChefAgent class.
        """
        BaseChefAgent.create_agents(
                self,
                n,
                cell=self.random.choices(self.grid.all_cells.cells, k=n),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.goals_of_agents,
                sovereigned_resources = self.resources_of_agents
            )
