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
        self.current_borrowed_resources = []


    def interpret_goals(self):
        """ The agent needs to interpret its goals and needs to use a handler to accomplish that goal. """
        if not self.goals:
            return


        


        