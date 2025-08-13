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
    def __init__(self, model, g, r):
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
        Called from ConsentChefAgent.norm_state_update
        """
        pass

    def condition_checker(self, cond_list):
        """
        Function that checks if a list of conditions match the environment state
        """
        all_match = True
        for cond in cond_list:
            if self.model.state.is_true(cond.name) != cond.truth:
                all_match = False
        return all_match


class Authorization(Norm):
    """
    An authorization has a consent giver (g), a consent receiver (r), a tuple of activation conditions (c), and an associated action t
    """
    def __init__(self, model, g, r, c, t):
        super().__init__(model, g, r)
        self.type = "AU"
        self.expired = False # AUs can expire
        self.c = c
        self.t = t
        self.c_det = self.c[0]
        self.c_exp = self.c[1]

    def activation_update(self):
        """
        For each condition, check if their required values are the same as their values in model state
        A condition is an Atom instance with a truth value T or F
        Called from ConsentChefAgent.norm_state_update
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
            self.expired = True

    def is_violated(self):
        """
        Checks if an AU is violated. That is, atoms in p (t=<p, r>) are become true although the AU is not active.
        """
        done = self.condition_checker([self.t.p])
        if done and not self.active and not self.is_fulfilled:
            self.violated = True
            self.active = False
            return True
        return False

    def is_fulfilled(self):
        """
        Checks if an AU was ever fulfilled (if post condition p of action t was true when the AU was active)
        If an AU is fulfilled, it cannot be violated again
        Called from self.is_violated
        """
        done = self.condition_checker([self.t.p])
        if done and self.active:
            self.fulfilled = True
            self.active = False


class Commitment(Norm):
    """
    A commitment has a consent giver (g), a consent receiver (r), an antecedent (p), and a consequent stated goal (g_R)
    g_R is an atom of shape <agent_id>-<goal_name>--

    TODO:
    How is a CO violated. 
    In the paper its said that if p holds and g_R doesn't, then CO is violated. 
    But shouldn't there be time between when the antecedent turns true and then the consequent turns true.
    """


    def __init__(self, model, g, r, p, g_R):
        super().__init__(model, g, r)

        self.p = p
        self.g_R = g_R
        self.type = "CO"

    def activation_update(self):
        """
        A commitment should be active once the antecedent turns true.
        Called from ConsentChefAgent.norm_state_update
        """
        
        # det
        det = self.condition_checker([self.p])
        if det and not self.active:
            self.active = True
            self.ever_active = True

        # TODO: Do we need expiration? No?

    def is_violated(self):
        """
        Checks if an AU is violated. That is, atoms in p (t=<p, r>) are become true although the AU is not active.
        """
        pass

    def is_fulfilled(self):
        """
        Checks if a CO was ever fulfilled (if g_R was ever True)
        If an CO is fulfilled, it cannot be violated again
        Called from self.is_violated
        """

        done = self.condition_checker([self.g_R])
        # No need to check for activation, a commitment can be fulfilled before being detached.
        if done:
            self.fulfilled = True
            self.active = False
