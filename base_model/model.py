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
                ):
        super().__init__(seed=seed)

        # initiate width and height of the grid
        self.width = width
        self.height = height

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


        ChefAgent.create_agents(
            self,
            initial_population,
            cell=self.random.choices(self.grid.all_cells.cells, k=initial_population),
            # Now I need to feed goals and sovereign resources at random.
            goals = self.random.choices(self.goals, k=initial_population),
            sovereigned_resources = self.random.choices(self.resources, k=initial_population)
        )

    def step(self):
        self.agents.do("print_goals_and_resources")


    
model = NoConsentModel(seed=None)
model.step()