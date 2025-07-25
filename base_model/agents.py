import mesa
import seaborn as sns
import numpy as np
import pandas as pd

from mesa.experimental.cell_space import CellAgent
import math


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
        self.goals = goals
        self.current_goal = None
        self.sovereigned_resources = sovereigned_resources
        self.available_sovereigned_resources = []
        self.sovereigned_resources_self_use = []
        self.current_borrowed_resources = []


    def interpret_goals(self):
        """ The agent needs to interpret its goals and needs to use a handler to accomplish that goal. """
        if not self.goals:
            return
        
        # For each subgoal of each goal, call the necessary handler
        # TODO: Do we want any planning logic here?
        for goal in self.goals:
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

    def resource_finder(self, resource_type):
        """
        This function finds the required resource instance for the goal.
        1. Check resources owned by the agent and not lent to another.
        2. Check resources borrowed from other agents and currently held.
        3. Check the closest resource owner who hasn't lent the resource.
        """

        # check resources owned by the agent
        for res in self.available_sovereigned_resources:
            if res.type == resource_type:
                

        


        


        