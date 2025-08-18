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
        # What kind of detachment conditions can there be?
        # For now, we implemented sub_goals as the post conditions of an action 
        # And an AU is activated immediately
        det = self.condition_checker(self.c_det)
        if det and not (self.active or self.violated):
            self.active = True
            self.ever_active = True

        # Did it expire:
        exp = self.condition_checker(self.c_exp)
        if exp and (self.active or self.fulfilled):
            self.active = False
            self.expired = True
            # For us, an expired AU is also violated
            self.violated = True
            self.fulfilled = False

    def is_violated(self):
        """
        Checks if an AU is violated. That is, atoms in p (t=<p, r>) become true although the AU is not active.
        """
        done = self.condition_checker([self.t.p])
        if (done and not self.active) or (done and self.fulfilled and self.expired):
            self.violated = True
            self.active = False
            self.fulfilled = False
            return True
        return False

    def is_fulfilled(self):
        """
        Checks if an AU was ever fulfilled (if post condition p of action t was true when the AU was active)
        Even if an AU is fulfilled it can still be violated because p is true until g_R is true.
        But a violated AU cannot be fulfilled again.
        So when checking we need to do: if fulfilled and not violated
        Called from self.is_violated
        """
        done = self.condition_checker([self.t.p])
        if self.fulfilled:
            return True
        elif done and self.active:
            self.fulfilled = True
            # self.active = False
            return True
        else:
            return False


class Commitment(Norm):
    """
    A commitment has a consent giver (g), a consent receiver (r), an antecedent (p), and a consequent stated goal (g_R)
    g_R is an atom of shape <agent_id>-<goal_name>----

    We can add time limits to stated goals.
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
        Checks if a CO is violated. If g_R was not performed before the deadline
        """
        exp_step = self.g_R.valid_to
        done = self.condition_checker([self.g_R])
        if not done and self.model.steps > exp_step:
            self.active = False
            self.violated = True
            return True
        return False

    def is_fulfilled(self):
        """
        Checks if a CO was ever fulfilled (if g_R was ever True)
        If an CO is fulfilled, it cannot be violated again
        Called from self.is_violated
        """

        done = self.condition_checker([self.g_R])
        due_passed = False
        valid_to = self.g_R.valid_to
        if valid_to and self.model.steps > valid_to:
            due_passed = True

        # No need to check for activation, a commitment can be fulfilled before being detached.
        if done and self.active and not self.violated and not due_passed:
            self.fulfilled = True
            self.active = False
            return True
        return False
