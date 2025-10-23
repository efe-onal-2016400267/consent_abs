import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1] 
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


from config import GOAL_FILE_PATH, TEST_CASE_PATH, TEST, MAX_STEP_COUNT, ConsentFirstAgent_COUNT, FiftyFiftyAgent_COUNT, GoalFirstAgent_COUNT, CO_exp_step, AU_exp_step, MonitoringAgent_COUNT, random_exp_times, max_random_AU_exp_step, min_random_AU_exp_step, max_random_CO_exp_step, min_random_CO_exp_step, print_state, print_execution
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
from agent_personas.monitoring_agent import MonitoringAgent
from model_level_collectors import (model_level_remaining_goals, 
                                    model_level_accomplished_goals, 
                                    model_level_active_consents,
                                    model_level_fulfilled_consents,
                                    model_level_violated_consents,
                                    model_level_unrealized_consents,
                                    model_level_deferred_consents,
                                    model_level_total_consents_activations_hist, 
                                    model_level_AU_activations_hist,
                                    model_level_active_AU,
                                    model_level_AU_expirations,
                                    model_level_AU_fulfilments,
                                    model_level_AU_vioaltions,
                                    model_level_CO_activations_hist,
                                    model_level_active_CO,
                                    model_level_CO_fulfilments,
                                    model_level_CO_violations,
                                    model_level_resource_conflicts,
                                    model_level_resource_conflict_accomplished_counter_goals)


class BaseModel(mesa.Model):
    """
    Base model class with common functionality for both ConsentModel and NoConsentModel.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_datacollector()
    
    def setup_datacollector(self):
        """Setup the data collector with common reporters."""
        self.datacollector = mesa.DataCollector(
            agent_reporters={
                           "Agent Persona": "agent_persona",
                           "Accomplished Goals": "num_accomplished_goals", 
                           "Remaining Goals": "num_remaining_goals",
                           "Resource Conflicts": "num_resource_conflicts",
                           "Counter Conflict Goal Accomplishments": "counter_conflict_goal_accomplishments",
                           "Finished Step": "finished_step",
                           "Longest Idle Time": "longest_idle_time",
                           "Number of Distinct Agents Interacted as G": "num_distinct_agents_interacted_as_G",
                           "Number of Distinct Agents Interacted as R": "num_distinct_agents_interacted_as_R",
                           "Number of Consents as R": "num_consents_as_R",
                           "Number of Consents as G": "num_consents_as_G",
                           "Number of Consents as R Violated": "num_consents_as_R_violated",
                           "Number of Consents as R Fulfilled": "num_consents_as_R_fulfilled",
                           "Number of Consents as R Unrealized": "num_consents_as_R_unrealized",
                           "Number of Consents as G Violated": "num_consents_as_G_violated",
                           "Number of Consents as G Fulfilled": "num_consents_as_G_fulfilled",
                           "Number of Consents as G Unrealized": "num_consents_as_G_unrealized"},
            model_reporters={"Total Accomplished Goals": model_level_accomplished_goals,
                              "Total Remaining Goals": model_level_remaining_goals,
                              "Total Resource Conflicts": model_level_resource_conflicts,
                              "Total Resource Conflict Accomplished Counter Goals": model_level_resource_conflict_accomplished_counter_goals,
                              "Total Current Active Consents": model_level_active_consents,
                              "Total Fulfilled Consents": model_level_fulfilled_consents,
                              "Total Violated Consents": model_level_violated_consents,
                              "Total Unrealized Consents": model_level_unrealized_consents,
                              "Total Deferred Consents": model_level_deferred_consents,
                              "Total Consent Activations": model_level_total_consents_activations_hist,
                              "Total AU Activations": model_level_AU_activations_hist,
                              "Total Current Active AU": model_level_active_AU,
                              "Total AU Expirations": model_level_AU_expirations,
                              "Total AU Violations": model_level_AU_vioaltions,
                              "Total AU Fulfilments": model_level_AU_fulfilments,
                              "Total CO Activations": model_level_CO_activations_hist,
                              "Total Current Active CO": model_level_active_CO,
                              "Total CO Violations": model_level_CO_violations,
                              "Total CO Fulfilments": model_level_CO_fulfilments}
        )
    
    def step(self):
        """
        Base step method that handles common data collection logic.
        Subclasses should call super().step() after their specific logic.
        """
        # Update goal counts for all agents before data collection
        self.agents.do("goal_count_update")
        
        # Collect data
        self.datacollector.collect(self)
    
    def collect_initial_state(self):
        """Collect initial state after agent creation."""
        self.agents.do("goal_count_update")
        self.datacollector.collect(self)


class ConsentModel(BaseModel):
    """
    Model class with consent reasoning.
    """

    def __init__(self, 
                width=50,
                height=50,
                seed = None,
                goal_per_agent = 3,
                resource_per_agent = 3,
                resources = [],
                consent_count = 0, # Will be used as the id.
                GOAL_FILE_PATH = GOAL_FILE_PATH, 
                TEST_CASE_PATH = TEST_CASE_PATH,
                TEST = TEST,
                MAX_STEP_COUNT = MAX_STEP_COUNT,
                ConsentFirstAgent_COUNT = ConsentFirstAgent_COUNT,
                GoalFirstAgent_COUNT = GoalFirstAgent_COUNT,
                FiftyFiftyAgent_COUNT = FiftyFiftyAgent_COUNT,
                MonitoringAgent_COUNT = MonitoringAgent_COUNT,
                initial_population=ConsentFirstAgent_COUNT + GoalFirstAgent_COUNT + FiftyFiftyAgent_COUNT + MonitoringAgent_COUNT,
                ):
        super().__init__(seed=seed)
        
        # Ensure deterministic behavior by synchronizing all random number generators
        if seed is not None:
            import numpy as np
            import random
            np.random.seed(seed)
            random.seed(seed)
            # Explicitly set Mesa's random seed
            self.random.seed(seed)
        
        self.state = EnvState()

         # initiate width and height of the grid
        self.width = width
        self.height = height
        self.goal_per_agent = goal_per_agent
        self.resource_per_agent = resource_per_agent
        self.initial_population = initial_population
        self.resources = resources
        self.running = True
        self.GOAL_FILE_PATH = GOAL_FILE_PATH
        self.TEST_CASE_PATH = TEST_CASE_PATH
        self.TEST = TEST
        self.MAX_STEP_COUNT = MAX_STEP_COUNT
        self.ConsentFirstAgent_COUNT = ConsentFirstAgent_COUNT
        self.GoalFirstAgent_COUNT = GoalFirstAgent_COUNT
        self.FiftyFiftyAgent_COUNT = FiftyFiftyAgent_COUNT
        self.MonitoringAgent_COUNT = MonitoringAgent_COUNT
        self.initial_population = self.ConsentFirstAgent_COUNT + self.GoalFirstAgent_COUNT + self.FiftyFiftyAgent_COUNT + self.MonitoringAgent_COUNT
        self.CO_exp_step = CO_exp_step
        self.AU_exp_step = AU_exp_step
        self.random_exp_times = random_exp_times
        self.max_random_AU_exp_step = max_random_AU_exp_step
        self.min_random_AU_exp_step = min_random_AU_exp_step
        self.max_random_CO_exp_step = max_random_CO_exp_step
        self.min_random_CO_exp_step = min_random_CO_exp_step
        self.grid = OrthogonalVonNeumannGrid(
            (self.width, self.height), torus=False, random=self.random
        )

        self.consent_history = []
        self.living_consents = []
        self.consent_count = consent_count

        # For resource conflict counts
        # This will hold conflict objects.
        self.model_level_resource_conflict_list = []
        # Again, for resource conflict counts, we need to track of the goals accomplished by R during the conflict.
        self.model_level_accomplished_counter_goal_list = []

        self.print_state = print_state
        self.print_execution = print_execution

        self.norm_state_counter = {
            "AU": {
                "violated": 0,
                "expired": 0,
                "fulfilled": 0,
                "ever_active": 0,
                "active": 0
            },
            "CO": {
                "violated":0,
                "fulfilled": 0,
                "ever_active": 0,
                "active": 0
            }
        }

        if self.TEST:
            with open(self.TEST_CASE_PATH, 'r') as f:
                test_case_data = yaml.safe_load(f)["agents"]

                for agent in test_case_data:
                    self.goals_of_agents = []
                    self.resources_of_agents = []
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
                    self.create_agents_separately(agent_persona=agent["persona"], goals=self.goals_of_agents, resources=self.resources_of_agents)

                    
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

            # Keep these lists sorted to ensure deterministic behavior
            self.goals = sorted(list(self.goals))
            self.resources = sorted(list(self.resources))

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

        # Collect initial state (before any agent actions)
        self.collect_initial_state()


    def create_agents_separately(self, agent_persona, goals, resources):
        # Ensure deterministic cell selection by sorting cells first
        sorted_cells = sorted(self.grid.all_cells.cells, key=lambda cell: (cell.coordinate[0], cell.coordinate[1]))
        
        if agent_persona == "ConsentFirstAgent":
                        ConsentFirstAgent.create_agents(
                            self,
                            1,
                            cell=self.random.choices(sorted_cells, k=1),
                            # Now I need to feed goals and sovereign resources at random.
                            goals = goals,
                            sovereigned_resources = resources
                        )
        elif agent_persona == "GoalFirstAgent":
                        GoalFirstAgent.create_agents(
                            self,
                            1,
                            cell=self.random.choices(sorted_cells, k=1),
                            # Now I need to feed goals and sovereign resources at random.
                            goals = goals,
                            sovereigned_resources = resources
                        )
        elif agent_persona == "FiftyFiftyAgent":
                        FiftyFiftyAgent.create_agents(
                            self,
                            1,
                            cell=self.random.choices(sorted_cells, k=1),
                            # Now I need to feed goals and sovereign resources at random.
                            goals = goals,
                            sovereigned_resources = resources
                        )
        elif agent_persona == "MonitoringAgent":
                        MonitoringAgent.create_agents(
                            self,
                            1,
                            cell=self.random.choices(sorted_cells, k=1),
                            # Now I need to feed goals and sovereign resources at random.
                            goals = goals,
                            sovereigned_resources = resources
                        )

    def create_agents_from_model(self, n=None):
        """
        A helper function to create agents.
        Called from __init__ function.
        This way, I dont have to override the whole __init__ in ConsentChefAgent class.
        """
        # Ensure deterministic cell selection by sorting cells first
        sorted_cells = sorted(self.grid.all_cells.cells, key=lambda cell: (cell.coordinate[0], cell.coordinate[1]))
        ConsentFirstAgent.create_agents(
                self,
                self.ConsentFirstAgent_COUNT,
                cell=self.random.choices(sorted_cells, k=self.ConsentFirstAgent_COUNT),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.goals_of_agents[:self.ConsentFirstAgent_COUNT],
                sovereigned_resources = self.resources_of_agents[:self.ConsentFirstAgent_COUNT]
            )
        
        GoalFirstAgent.create_agents(
                self,
                self.GoalFirstAgent_COUNT,
                cell=self.random.choices(sorted_cells, k=self.GoalFirstAgent_COUNT),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.goals_of_agents[self.ConsentFirstAgent_COUNT:self.ConsentFirstAgent_COUNT + self.GoalFirstAgent_COUNT],
                sovereigned_resources = self.resources_of_agents[self.ConsentFirstAgent_COUNT:self.ConsentFirstAgent_COUNT + self.GoalFirstAgent_COUNT]
            )
        
        FiftyFiftyAgent.create_agents(
                self,
                self.FiftyFiftyAgent_COUNT,
                cell=self.random.choices(sorted_cells, k=self.FiftyFiftyAgent_COUNT),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.goals_of_agents[self.ConsentFirstAgent_COUNT + self.GoalFirstAgent_COUNT:],
                sovereigned_resources = self.resources_of_agents[self.ConsentFirstAgent_COUNT + self.GoalFirstAgent_COUNT:]
            )

        MonitoringAgent.create_agents(
                self,
                self.MonitoringAgent_COUNT,
                cell=self.random.choices(sorted_cells, k=self.MonitoringAgent_COUNT),
                # Now I need to feed goals and sovereign resources at random.
                goals = self.goals_of_agents[self.ConsentFirstAgent_COUNT + self.GoalFirstAgent_COUNT + self.FiftyFiftyAgent_COUNT:],
                sovereigned_resources = self.resources_of_agents[self.ConsentFirstAgent_COUNT + self.GoalFirstAgent_COUNT + self.FiftyFiftyAgent_COUNT:]
            )
        
    def check_consent_state(self):
        """
        Checks and updates the states of the CIs in self.living_consents.
        Each agent holds their version of the CIs, but the model holds them as the ground truth.
        """
        for CI in self.living_consents:
            if CI.state in ["ACTIVE", "FULFILLED"]:
                # Call consent functions
                # Always count for the giver (g) so that we dont count twice.
                CI.update_norm_activations(agent=CI.g, counter=True, caller="model") # First lets see states of the norms
                violated = CI.is_violated(agent=CI.g, counter=True, caller="model")
                fulfilled = CI.is_fulfilled(agent=CI.g, counter=True, caller="model")
                unrealized = CI.is_unrealized(agent=CI.g, counter=True, caller="model")
                reneg = CI.is_renegotiate(agent=CI.g, counter=True, caller="model")
                active = CI.is_active(agent=CI.g, counter=True, caller="model")

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
        #print(self.state.atoms )
        # Call parent step method for common data collection logic
        super().step()


if __name__ == "__main__":
    model = ConsentModel(seed=42, GOAL_FILE_PATH = GOAL_FILE_PATH, TEST_CASE_PATH = TEST_CASE_PATH, TEST = TEST, MAX_STEP_COUNT = MAX_STEP_COUNT, ConsentFirstAgent_COUNT = ConsentFirstAgent_COUNT, GoalFirstAgent_COUNT = GoalFirstAgent_COUNT, FiftyFiftyAgent_COUNT = FiftyFiftyAgent_COUNT, MonitoringAgent_COUNT = MonitoringAgent_COUNT)
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

        if fin or step_count >= model.MAX_STEP_COUNT:
            agent_vars = model.datacollector.get_agent_vars_dataframe()
            model_vars = model.datacollector.get_model_vars_dataframe()
            model_vars.head()
            agent_vars.to_csv('./base_model/results/agent_data.csv')
            model_vars.to_csv('./base_model/results/model_data.csv')
            break