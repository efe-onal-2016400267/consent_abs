from pathlib import Path
import mesa
import numpy as np
from agents import ChefAgent
from resource import Resource
from mesa.experimental.cell_space import OrthogonalVonNeumannGrid
#from mesa.experimental.cell_space.property_layer import PropertyLayer

import yaml

GOAL_FILE_PATH = "./goals/goal_tree.yaml"

class NoConsentModel(mesa.Model):
    """
    Model class with no consent reasoning.
    """

    def __init__(self, 
                width=50,
                height=50,
                initial_population=100,
                seed = None,
                goal_per_agent = 2,
                resource_per_agent = 2,
                resources = []
                ):
        super().__init__(seed=seed)

        # initiate width and height of the grid
        self.width = width
        self.height = height
        self.goal_per_agent = goal_per_agent
        self.resource_per_agent = resource_per_agent
        self.resources = resources
        self.running = True
        self.grid = OrthogonalVonNeumannGrid(
            (self.width, self.height), torus=False, random=self.random
        )

        # Read the yaml file first to get the goals
        with open(GOAL_FILE_PATH, 'r') as f:
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
        self.goals_of_agents = []
        self.resources_of_agents = []
        for _ in range(initial_population):
            self.goals_of_agents.append(self.random.sample(self.goals, k=self.goal_per_agent))
            self.resources_of_agents.append(self.random.sample(self.resources, k=self.resource_per_agent))

        ChefAgent.create_agents(
            self,
            initial_population,
            cell=self.random.choices(self.grid.all_cells.cells, k=initial_population),
            # Now I need to feed goals and sovereign resources at random.
            goals = self.goals_of_agents,
            sovereigned_resources = self.resources_of_agents
        )

    def step(self):
        self.agents.do("print_goals_and_resources")
        self.agents.do("interpret_goals")

    
model = NoConsentModel(seed=42)
model.step()