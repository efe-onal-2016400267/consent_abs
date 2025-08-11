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
        self.ever_active = False
        self.fulfilled = False

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

    def activation_update(self):
        """
        This function should run at each step for all inactive norms
        So that if the activation conditions are met (c_det for AU, p for CO) we can activate the norm
        """
        pass

    def condition_checker(self, cond_list):
        """
        Function that checks if a list of conditions match the environment state
        """
        all_match = True
        for cond in cond_list:
            if self.model.state.is_true(cond.atom_name) != cond.truth:
                all_match = False
        return all_match


class Authorization(Norm):
    """
    An authorization has a consent giver (g), a consent receiver (r), a tuple of activation conditions (c), and an associated action t
    """
    def __init__(self, model: "ConsentModel", g, r, c, t):
        super().__init__(model, g, r)
        self.expired = False # AUs can expire

        self.c = c
        self.t = t
        self.c_det = self.c[0]
        self.c_exp = self.c[1]

    def activation_update(self):
        """
        For each condition, check if their required values are the same as their values in model state
        A condition is an Atom instance with a truth value T or F
        """
        # Did it detach:
        det = self.condition_checker(self.c_det)
        if det and not self.active:
            self.active = True
            self.ever_active = True

        # Did it expire:
        exp = self.condition_checker(self.c_exp)
        if exp and self.active:
            self.active = False

    def is_violated(self):
        """
        Checks if an AU is violated. That is, atoms in p (t=<p, r>) are become true although the AU is not active.
        """
        done = self.condition_checker(self.t.p)
        if done and not self.active and not self.is_fulfilled:
            self.violated = True

    def is_fulfilled(self):
        """
        Checks if an AU was ever fulfilled (if post condition p of action t was true when the AU was active)
        If an AU is fulfilled, it cannot be violated again
        Called from self.is_violated
        """
        done = self.condition_checker(self.t.p)
        if done and self.active:
            self.fulfilled = True


class Commitment(Norm):
    """
    A commitment has a consent giver (g), a consent receiver (r), an antecedent (p), and a consequent stated goal (g_R)
    g_R is an atom of shape <agent_id>-<goal_name>--
    """
    def __init__(self, model, g, r, p, g_R):
        super().__init__(model, g, r)

        self.p = p
        self.g_R = g_R