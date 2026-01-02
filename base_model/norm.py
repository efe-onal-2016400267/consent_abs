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

    def is_fulfilled(self, agent=None, counter=False, caller=None):
        """
        Function to check if the norm is fulfilled.
        Will be overriden in each child class.
        """
        pass

    def is_violated(self, agent=None, counter=False, caller=None):
        """
        Function to check if the norm is violated.
        Will be overriden in each child class.
        """
        pass

    def activation_update(self, agent=None, counter=False, caller=None):
        """
        This function should run at each step for all inactive norms
        So that if the activation conditions are met (c_det for AU, p for CO) we can activate the norm
        Called from ConsentChefAgent.norm_state_update
        """
        pass

    def condition_checker(self, cond_list, agent=None, counter=False, caller=None):
        """
        Function that checks if a list of conditions match the environment state
        """
        all_match = True
        for cond in cond_list:
            if self.model.state.is_true(cond.name) != cond.truth:
                all_match = False
        return all_match
    
    def clone(self, agent=None, counter=False):
        """
        Returns a new instance of the norm object.
        To be implemented in AU and CO child classes.
        Called from ConsentChefAgent.request_consent.
        """
        pass


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

    def activation_update(self, agent=None, counter=False, caller=None):
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
        if det and not (self.active or self.violated or self.fulfilled):
            self.active = True
            self.ever_active = True
            if agent and counter:
                agent.norm_state_counter["AU"]["ever_active"] = agent.norm_state_counter["AU"]["ever_active"] + 1
            if caller == "model" and counter:
                self.model.norm_state_counter["AU"]["ever_active"] = self.model.norm_state_counter["AU"]["ever_active"] + 1

        # Did it expire:
        exp = self.condition_checker(self.c_exp)
        if exp and (self.active or self.fulfilled): # A fulfilled AU can expire too. An expired AU cannot be fulfilled any more.
            self.active = False
            self.expired = True
            # For us, an expired AU is also violated
            self.violated = False
            

            if agent and counter:
                agent.norm_state_counter["AU"]["expired"] = agent.norm_state_counter["AU"]["expired"] + 1
                #if self.fulfilled:
                #    agent.norm_state_counter["AU"]["fulfilled"] = agent.norm_state_counter["AU"]["fulfilled"] - 1
            if caller == "model" and counter:
                self.model.norm_state_counter["AU"]["expired"] = self.model.norm_state_counter["AU"]["expired"] + 1
                #if self.fulfilled:
                #    self.model.norm_state_counter["AU"]["fulfilled"] = self.model.norm_state_counter["AU"]["fulfilled"] - 1
            self.fulfilled = False

    def is_violated(self, agent=None, counter=False, caller=None):
        """
        Checks if an AU is violated. That is, atoms in p (t=<p, r>) become true although the AU is not active.
        """
        done = self.condition_checker([self.t.p])
        exp = self.condition_checker(self.c_exp)
        if (done and not self.active and not self.fulfilled and not self.expired) or (done and self.fulfilled and self.expired) or (done and self.expired) or (done and exp):
            self.violated = True
            self.active = False
            self.fulfilled = False

            if agent and counter:
                agent.norm_state_counter["AU"]["violated"] = agent.norm_state_counter["AU"]["violated"] + 1
            if caller == "model" and counter:
                self.model.norm_state_counter["AU"]["violated"] = self.model.norm_state_counter["AU"]["violated"] + 1
            return True
        return False

    def is_fulfilled(self, agent=None, counter=False, caller=None):
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
            self.active = False
            if agent and counter:
                agent.norm_state_counter["AU"]["fulfilled"] = agent.norm_state_counter["AU"]["fulfilled"] + 1
            if caller == "model" and counter:
                self.model.norm_state_counter["AU"]["fulfilled"] = self.model.norm_state_counter["AU"]["fulfilled"] + 1
            return True
        else:
            return False
        
    def clone(self, agent=None, counter=False):
        """
        Returns a new instance of the norm object.
        To be implemented in AU and CO child classes.
        Called from ConsentChefAgent.request_consent.
        """
        # We don't need to clone the atoms (c) since atoms are global.
        # We don't need to clone the actions (t) since it contains an atom and a resource. The atom is global and the resource will never change.
        AU_clone = Authorization(model=self.model,
                                 g=self.g,
                                 r=self.r,
                                 c=self.c,
                                 t=self.t)
        return AU_clone


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

    def activation_update(self, agent=None, counter=False, caller=None):
        """
        A commitment should be active once the antecedent turns true.
        Called from ConsentChefAgent.norm_state_update
        """
        
        # det
        det = self.condition_checker([self.p])
        if det and not self.active:
            self.active = True
            self.ever_active = True
            if agent and counter:
                agent.norm_state_counter["CO"]["ever_active"] = agent.norm_state_counter["CO"]["ever_active"] + 1
            if caller == "model" and counter:
                self.model.norm_state_counter["CO"]["ever_active"] = self.model.norm_state_counter["CO"]["ever_active"] + 1
        # TODO: Do we need expiration? No?

    def is_violated(self, agent=None, counter=False, caller=None):
        """
        Checks if a CO is violated. If g_R was not performed before the deadline
        """
        exp_step = self.g_R.valid_to
        done = self.condition_checker([self.g_R])
        if not done and self.model.steps > exp_step:
            self.active = False
            self.violated = True

            if agent and counter:
                agent.norm_state_counter["CO"]["violated"] = agent.norm_state_counter["CO"]["violated"] + 1
            if caller == "model" and counter:
                self.model.norm_state_counter["CO"]["violated"] = self.model.norm_state_counter["CO"]["violated"] + 1
            return True
        return False

    def is_fulfilled(self, agent=None, counter=False, caller=None):
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

            if agent and counter:
                agent.norm_state_counter["CO"]["fulfilled"] = agent.norm_state_counter["CO"]["fulfilled"] + 1
            if caller == "model" and counter:
                self.model.norm_state_counter["CO"]["fulfilled"] = self.model.norm_state_counter["CO"]["fulfilled"] + 1
            return True
        return False
    
    def clone(self, agent=None, counter=False):
        """
        Returns a new instance of the norm object.
        To be implemented in AU and CO child classes.
        Called from ConsentChefAgent.request_consent.
        """
        # We don't need to copy p and g_R since they are atoms and atoms are global.
        clone_CO = Commitment(model=self.model,
                              g=self.g,
                              r=self.r,
                              p=self.p,
                              g_R=self.g_R)
        return clone_CO
