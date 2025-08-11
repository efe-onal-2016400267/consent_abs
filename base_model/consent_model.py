from noconsent_model import NoConsentModel
from state import EnvState
from atom import Atom
from config import GOAL_FILE_PATH, TEST_CASE_PATH, TEST, MAX_STEP_COUNT

from pathlib import Path
import mesa
import numpy as np
from base_agent import BaseChefAgent
from consent_agent import ConsentChefAgent
from resource import Resource
from mesa.experimental.cell_space import OrthogonalVonNeumannGrid
#from mesa.experimental.cell_space.property_layer import PropertyLayer

import yaml



class ConsentModel(NoConsentModel):
    """
    Stateful model.
    The state is going to be a set of propositional atoms.
    """

    def __init__(self, 
                width=50,
                height=50,
                initial_population=100,
                seed = None,
                goal_per_agent = 2,
                resource_per_agent = 2,
                resources = [],
                ):
        
        super().__init__(width, height, initial_population, seed, goal_per_agent, resource_per_agent, resources)

    def create_agents_from_model(self, n):
        """
        A helper function to create agents.
        Called from __init__ function.
        This way, I dont have to override the whole __init__ in ConsentChefAgent class.
        """
        ConsentChefAgent.create_agents(
                self,
                n,
                cell=self.random.choices(self.grid.all_cells.cells, k=n),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.goals_of_agents,
                sovereigned_resources = self.resources_of_agents
            )
        
    def step(self):
        self.agents.do("interpret_goals")

model = ConsentModel(seed=42)

step_count = 0
while 1:
    print(f"-----------STEP: {step_count}--------------")
    model.step()
    step_count += 1
    fin = 1
    for agent in model._all_agents:
        print(f"Agent: {agent.unique_id}, remaining goal count: {len(agent.remaining_goals)}")
        if len(agent.remaining_goals) > 0:
            fin = 0

    if fin or step_count >= MAX_STEP_COUNT:
        break
