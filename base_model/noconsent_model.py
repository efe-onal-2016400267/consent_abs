from pathlib import Path
import mesa
import numpy as np
from base_agent import BaseChefAgent
from resource import Resource
from mesa.experimental.cell_space import OrthogonalVonNeumannGrid
#from mesa.experimental.cell_space.property_layer import PropertyLayer

import yaml

GOAL_FILE_PATH = "./goals/goal_tree.yaml"
TEST_CASE_PATH = "./test_cases/test_001_2.yaml"
TEST = False
MAX_STEP_COUNT = 100

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

        if TEST:
            with open(TEST_CASE_PATH, 'r') as f:
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

                BaseChefAgent.create_agents(
                    self,
                    len(test_case_data),
                    cell=self.random.choices(self.grid.all_cells.cells, k=len(test_case_data)),
                    # Now I need to feed goals and sovereign resources at random.
                    goals = self.goals_of_agents,
                    sovereigned_resources = self.resources_of_agents
                )
        else:
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
            # TODO: But we need to make these resources instances of the resource class. How would we do that?
            self.goals_of_agents = []
            self.resources_of_agents = []
            for agent_index in range(initial_population):
                self.goals_of_agents.append(self.random.sample(self.goals, k=self.goal_per_agent))

                # Sample resource types (e.g., 'egg', 'oven')
                resource_types = self.random.sample(self.resources, k=self.resource_per_agent)

                # Create Resource instances and assign ownership
                resource_instances = [
                    Resource(name=f"{res_type}_{agent_index+1}_{i}", owner=agent_index+1, type=res_type)
                    for i, res_type in enumerate(resource_types)
                ]
                self.resources_of_agents.append(resource_instances)

            BaseChefAgent.create_agents(
                self,
                initial_population,
                cell=self.random.choices(self.grid.all_cells.cells, k=initial_population),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.goals_of_agents,
                sovereigned_resources = self.resources_of_agents
            )

    def step(self):
        self.agents.do("interpret_goals")

"""   
model = NoConsentModel(seed=42)

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
"""