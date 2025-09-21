import sys
from pathlib import Path

# Go two levels up: from base_model/models/model.py → base_model/
project_root = Path(__file__).resolve().parents[1]  # <-- now correct
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


from config import GOAL_FILE_PATH, TEST_CASE_PATH, TEST, MAX_STEP_COUNT, ConsentFirstAgent_COUNT, FiftyFiftyAgent_COUNT, GoalFirstAgent_COUNT
from state import EnvState
from pathlib import Path
import mesa
import numpy as np
from resource import Resource
from mesa.experimental.cell_space import OrthogonalVonNeumannGrid
import yaml
from agent_personas.consent_first_agent import ConsentFirstAgent
from agent_personas.fifty_fifty_consent_and_goal_agent import FiftyFiftyAgent
from agent_personas.goal_first_agent import GoalFirstAgent
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


class ConsentModel(mesa.Model):
    """
    Model class with no consent reasoning.
    """

    def __init__(self, 
                width=50,
                height=50,
                initial_population=ConsentFirstAgent_COUNT + GoalFirstAgent_COUNT + FiftyFiftyAgent_COUNT,
                seed = None,
                goal_per_agent = 3,
                resource_per_agent = 3,
                resources = [],
                consent_count = 0, # Will be used as the id.
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
        self.running = True
        self.grid = OrthogonalVonNeumannGrid(
            (self.width, self.height), torus=False, random=self.random
        )

        self.consent_history = []
        self.living_consents = []
        self.consent_count = consent_count

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

                # By feeding persona numbers to this function, I can create different types of agents in a single simulation.
                self.create_agents_from_model(n=len(test_case_data))
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


    def create_agents_from_model(self, n):
        """
        A helper function to create agents.
        Called from __init__ function.
        This way, I dont have to override the whole __init__ in ConsentChefAgent class.
        """
        ConsentFirstAgent.create_agents(
                self,
                ConsentFirstAgent_COUNT,
                cell=self.random.choices(self.grid.all_cells.cells, k=ConsentFirstAgent_COUNT),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.random.sample(self.goals_of_agents, k=ConsentFirstAgent_COUNT),
                sovereigned_resources = self.random.sample(self.resources_of_agents, k=ConsentFirstAgent_COUNT)
            )
        
        GoalFirstAgent.create_agents(
                self,
                GoalFirstAgent_COUNT,
                cell=self.random.choices(self.grid.all_cells.cells, k=GoalFirstAgent_COUNT),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.random.sample(self.goals_of_agents, k=GoalFirstAgent_COUNT),
                sovereigned_resources = self.random.sample(self.resources_of_agents, k=GoalFirstAgent_COUNT)
            )
        
        FiftyFiftyAgent.create_agents(
                self,
                FiftyFiftyAgent_COUNT,
                cell=self.random.choices(self.grid.all_cells.cells, k=FiftyFiftyAgent_COUNT),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.random.sample(self.goals_of_agents, k=FiftyFiftyAgent_COUNT),
                sovereigned_resources = self.random.sample(self.resources_of_agents, k=FiftyFiftyAgent_COUNT)
            )
        
    def check_consent_state(self):
        """
        Checks and updates the states of the CIs in self.living_consents.
        Each agent holds their version of the CIs, but the model holds them as the ground truth.
        """
        for CI in self.living_consents:
            if CI.state == "ACTIVE":
                # Call consent functions
                # Always count for the giver (g) so that we dont count twice.
                CI.update_norm_activations(agent=CI.g, counter=True) # First lets see states of the norms
                violated = CI.is_violated(agent=CI.g, counter=True)
                fulfilled = CI.is_fulfilled(agent=CI.g, counter=True)
                unrealized = CI.is_unrealized(agent=CI.g, counter=True)
                reneg = CI.is_renegotiate(agent=CI.g, counter=True)
                active = CI.is_active(agent=CI.g, counter=True)

        return
    
    def step(self):
        # Agents update the states of the norms of the consents they have given and received.
        # This could be done by the model as well?
        # self.agents.do("norm_state_update") : DEPRICATED

        self.agents.do("update_exp_cond")
        # Agents check the states of the consents they have given or received.
        # TODO: They should change behavour based on current consent state.
        self.agents.do("check_given_consents")
        # The model should check its own Consent instances too
        self.check_consent_state()
        # The actual step function that runs the agent, interpret_goals.
        self.agents.do("interpret_goals")
        self.agents.do("check_given_consents")
        # The model should check its own Consent instances too
        self.check_consent_state()
        self.agents.do("release_resources")
        self.datacollector.collect(self)


model = ConsentModel(seed=42)

step_count = 1
while 1:
    print(f"-----------STEP: {step_count}--------------")
    model.step()
    fin = 1
    step_count += 1
    for agent in model._all_agents:
        print(f"Agent: {agent.unique_id}, remaining goal count: {len(agent.remaining_goals)}")
        if len(agent.remaining_goals) > 0:
            fin = 0

    if fin or step_count >= MAX_STEP_COUNT:
        agent_vars = model.datacollector.get_agent_vars_dataframe()
        model_vars = model.datacollector.get_model_vars_dataframe()
        agent_vars.head()
        break