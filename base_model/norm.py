from consent_agent import ConsentChefAgent
from action import Action
from consent_model import ConsentModel

"""
* Can an AU be violated?
    It can be violated if the action is taken after the authorization has expired.
    So we need to activate it whenever the c_det becomes true and deactivate it whenever c_exp is true.
    If they are both true, then in a single instant the AU is activated and then deactivated.
"""

class Norm:
    """
    Base class for norms.
    Each norm has a consent giver (g) and a consent receiver (r) who are ConsentChefAgents
    """
    def __init__(self, model: "ConsentModel", g:"ConsentChefAgent", r:"ConsentChefAgent"):
        self.g = g
        self.r = r
        self.model = model
        self.active = False
        self.violated = False

    def is_fulfilled(self):
        """
        Function to check if the norm is fulfilled.
        Will be overriden in each child class.
        """
        pass

    def is_violated(self):
        """
        Function to check if the norm is violated.
        Will be overriden in each child class.
        """
        pass

    def activate(self):
        """
        This function should run at each step for all inactive norms
        So that if the activation conditions are met (c_det for AU, p for CO) we can activate the norm
        """
        pass


class Authorization(Norm):
    """
    An authorization has a consent giver (g), a consent receiver (r), a tuple of activation conditions (c), and an associated action t
    """
    def __init__(self, model: "ConsentModel", g, r, c, t):
        super().__init__(model, g, r)
        self.expired = False # AUs can expire

        self.c = c
        self.c_det = self.c[0]
        self.c_exp = self.c[1]

    def activate(self):
        """
        For each condition, check if their required values are the same as their values in model state
        A condition is an Atom instance with a truth value T or F
        """
        for cond in self.c_det:
            # If any of the atoms in the c_det and current model state dont match: do NOT activate.
            # If all atoms match, activate
            if self.model.state.is_true(cond.atom_name) != cond.truth:
                break
        self.activate = True


class Commitment(Norm):
    """
    A commitment has a consent giver (g), a consent receiver (r), an antecedent (p), and a consequent stated goal (g_R)
    g_R is an atom of shape <agent_id>-<goal_name>--
    """
    def __init__(self, model, g, r, p, g_R):
        super().__init__(model, g, r)

        self.p = p
        self.g_R = g_R