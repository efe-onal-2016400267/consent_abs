from noconsent_model import NoConsentModel
from config import GOAL_FILE_PATH, TEST_CASE_PATH, TEST, MAX_STEP_COUNT

from consent_agent import ConsentChefAgent



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
                goal_per_agent = 3,
                resource_per_agent = 3,
                resources = [],
                ):
        
        super().__init__(width, height, initial_population, seed, goal_per_agent, resource_per_agent, resources)
        # To hold a history of all the ConsentInstances, will be used to count the number of fulfillments, violations, etc.
        self.consent_history = []
        self.living_consents = []

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
        # Agents update the states of the norms of the consents they have given and received.
        # This could be done by the model as well?
        # self.agents.do("norm_state_update") : DEPRICATED

        self.agents.do("update_exp_cond")
        # Agents check the states of the consents they have given or received.
        # TODO: They should change behavour based on current consent state.
        self.agents.do("check_given_consents")
        # The actual step function that runs the agent, interpret_goals.
        self.agents.do("interpret_goals")   

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
        break