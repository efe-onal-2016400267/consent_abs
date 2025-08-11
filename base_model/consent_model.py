from noconsent_model import NoConsentModel
from state import EnvState
from atom import Atom

from pathlib import Path
import mesa
import numpy as np
from base_agent import BaseChefAgent
from consent_agent import ConsentChefAgent
from resource import Resource
from mesa.experimental.cell_space import OrthogonalVonNeumannGrid
#from mesa.experimental.cell_space.property_layer import PropertyLayer

import yaml

GOAL_FILE_PATH = "./goals/goal_tree.yaml"
TEST_CASE_PATH = "./test_cases/test_001_2.yaml"
TEST = False
MAX_STEP_COUNT = 100

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
                state = EnvState() # Empty state as the model is initialized
                ):
        
        super().__init__(width, height, initial_population, seed, goal_per_agent, resource_per_agent, resources)
        
        self.state = state

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
