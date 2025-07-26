import mesa
import seaborn as sns
import numpy as np
import pandas as pd

from mesa.experimental.cell_space import CellAgent
import math

"""
1.  So at each step, an agent can accomplish 1 goal 
    by collecting all resources it needs in a single step for a single goal.
    This will enable us to get rid of deadlocks. Otherwise, if at each step they can obtain only 1 resource,
    they may end up in a lock for ever.

2. As soon as an agent collects all resources for a goal, the goal is deemed accomplished.
    When the goal is accomplished in a step, in the next step the agent checks if it still needs the resource in any of its future goals,
    if so it does not release it and keeps using it in the next step.
    This way, prohibitions will be meaningful. Giver can prohibit receiver from using the resource in a second recipe.
    Commitments and authorizations inherently make sense.

3. If the agent cannot obtain all resources for the current goal, it simply waits. But the resources it manages to obtain become
    unavailable for other agents.

4. But how are we going to use consent in this scheme? Maybe if an agent will use a resource, they wont give to other agents?

"""

def get_distance(cell_1, cell_2):
    """
    Returns the eucledian distance between two cells.
    Used in resource_finder function.
    """

    x1, y1 = cell_1.coordinate
    x2, y2 = cell_2.coordinate

    dx = x1 - x2
    dy = y1 - y2

    return math.sqrt(dx ** 2 + dy ** 2)

"""

I made available resources types of ingredients, oven, and stove. This way it will be easy to come up with goals.
Different agents will aim to cook different dishes.
If they do not own the ingredient they need, they have to take it from another agent. First without consent, then with.

"""

# So different agents will own different resources.
# Different agents will have different goals.
# These goals will require certain resources.
# How should I implement these goals tho.


class ChefAgent(CellAgent):
    """An agent that needs to cook certain dishes and owns some resources. """

    def __init__(self, 
                 model,
                 cell,
                 goals = [],
                 sovereigned_resources = []
                 ):
        # Pass the parameters to the parent class.
        super().__init__(model)
        self.remaining_goals = goals
        self.current_goal = None
        self.sovereigned_resources = sovereigned_resources
        self.available_sovereigned_resources = []
        self.sovereigned_resources_self_use = []
        self.current_borrowed_resources = []
        self.accomplished_goals = []
        self.cell = cell
        self.all_required_future_resources = self.initialize_required_future_resources()


    def interpret_goals(self):
        """ The agent needs to interpret its goals and needs to use a handler to accomplish that goal. """
        if not self.remaining_goals:
            return
        
        # For each subgoal of each goal, call the necessary handler
        # TODO: We created a single resource finder function, revisit this handler logic.
        # TODO: Do we want any planning logic here?
        for goal in self.remaining_goals:
            for subgoal in goal:
                subgoal_name = subgoal["name"]
                handler = getattr(self, subgoal_name, None)
                if handler:
                    handler()
                else:
                    print(f"No subgoal or handler.")


    #########################################
    #                                       #
    #            Handler functions          #
    #                                       #
    #########################################
    def initialize_required_future_resources(self):
        """
        In __init__, initialize the list of required future resources.
        """
        required_future_resources = []
        for goal in self.remaining_goals:
            for res in goal[1]:
                if res.split("_")[1] not in required_future_resources:
                    required_future_resources.append(res.split("_")[1])

        return required_future_resources

    def update_required_future_resources(self):
        """
        TODO: Depricated! I can use initialize_required_future_resources instead.
        This function creates a list of all required future resources. 
        It is used to decide if the agent should release an obtained resource.
        It is called after each goal completion.
        """

        # If all goals are accomplished, the agent wont need any resources in the future.
        if not self.remaining_goals:
            self.all_required_future_resources = []
        else:
            for res in self.model.resources:
                res_needed = False
                for goal in self.remaining_goals:
                    if res in goal[1]:
                        res_needed = True
                if not res_needed:
                    self.all_required_future_resources.remove(res)




    def resource_finder(self, resource_type):
        """
        This function finds the required resource instance for the goal.
        3. Check resources owned by the agent and not lent to another.
        2. Check resources borrowed from other agents and currently held.
        1. Check the closest resource owner who hasn't lent the resource.
        """
        
        # TODO: when do we release? Can I borrow for one goal and use for 2 goals? That might be an instance of a prohibition.
        
        # Owned by the agent, currently in use by the agent.
        for res in self.sovereigned_resources_self_use:
            if res.type == resource_type:
                return
            
        # Owned by the agent, currently used by nobody
        for res in self.available_sovereigned_resources:
            if res.type == resource_type:
                # TODO: If this is just the resource finder function, then maybe the following 3 lines should be inside another function.
                res.in_use_by = self
                self.available_sovereigned_resources.remove(res)
                self.sovereigned_resources_self_use.append(res)
                return
            
        # Get the closest available resource of this type
        # 1. Get a list of all the agents, that hold one of the required type of resource
        # 2. Get the closest agent
        # 3. Negoiate? and borrow the resource

    def print_goals_and_resources(self):
        print(f"Agent: {self.unique_id}, coords: {self.cell.coordinate}")
        print(f"Agent: {self.unique_id}, resources: {self.sovereigned_resources}, goals: {self.goals}")