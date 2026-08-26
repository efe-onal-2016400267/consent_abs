from action import Action
from norm import Norm, Authorization, Commitment
import copy

class ConsentInstance:
    """
    CI = <g, r, N, g_R, t> where
        g: Consent giver
        r: Consent receiver
        N: List of norms agreed on
        g_R: Stated goal that becomes true after CO is fulfilled. So the main goal of the agent
        t: The action for which the consent is given
    """
    def __init__(self, g, r, N, g_R, t:"Action", res, id, owner, time_step):
        self.g = g
        self.r = r
        self.N = N
        self.g_R = g_R
        self.t = t
        self.res = res
        self.state = "NEGOTIATING" # TODO: unsolicited consent
        # We'll be creating 2 instances for 1 negotiation.
        # The owner can be G or R. They will be the owners of their own instances.
        # And we use an id two bind the two instances of consent.
        self.id = id
        self.owner = owner # The owner is who holds and checks the consent instance.
        self.time_step = time_step


    def is_violated(self, agent=None, counter=False, caller=None):
        """
        If any norms in N are violated, then ConsentInstance is also violated.
        """
        # If ConsentInstance is already violated, return True.
        if self.state == "VIOLATED":
            return True
        
        # If ConsentInstance hasnt already completed its life
        if self.state not in ("UNREALIZED", "DEFERRED"): # I could just check ACTIVE
            violated = False
            for n in self.N:
                if n.is_violated(agent=agent, counter=counter, caller=caller):
                    violated = True
                    self.state = "VIOLATED"
                    history_log = self.get_consent_dict()
                    history_log["state_transition_time_step"] = self.g.model.steps
                    self.g.model.consent_history.append(history_log)
            return violated
        else:
            return False

    def is_fulfilled(self, agent=None, counter=False, caller=None):
        """
        If all of the norms in N are fulfilled, then ConsentInstance is also fulfilled.
        """

        # If the consent instance is already fulfilled, return true
        if self.state == "FULFILLED":
            return True

        # If the norm was already violated, it cannot be fulfilled.
        if self.state in ("VIOLATED", "UNREALIZED", "DEFERRED"):
            return False
        
        # If any of the norms is not fulfilled, ConsentInstance is not fulfilled either.
        for n in self.N:
            if not n.is_fulfilled(agent=agent, counter=counter, caller=caller) or n.is_violated(agent=agent, counter=counter, caller=caller):
                return False
            
        # Otherwise, ConsentInstance is fulfilled.
        self.state = "FULFILLED"
        history_log = self.get_consent_dict()
        history_log["state_transition_time_step"] = self.g.model.steps
        self.g.model.consent_history.append(history_log)
        return True

    def is_unrealized(self, agent=None, counter=False, caller=None):
        """
        If any of the AUs in N expire, then ConsentInstance is unrealized.
        """
        if self.state not in ("FULFILLED", "VIOLATED"):
            for n in self.N:
                if n.type == "AU" and n.expired:
                    self.state = "UNREALIZED"
                    history_log = self.get_consent_dict()
                    history_log["state_transition_time_step"] = self.g.model.steps
                    self.g.model.consent_history.append(history_log)
                    return True
        return False

    def is_renegotiate(self, agent=None, counter=False, caller=None):
        """
        TODO: How can we find a use case for renegotiation?
        """
        pass

    def is_active(self, agent=None, counter=False, caller=None):
        return self.state == "ACTIVE"
    
    def update_norm_activations(self, agent, counter=False, caller=None):
        for n in self.N:
            n.activation_update(agent=agent, counter=counter, caller=caller)

    def get_consent_dict(self):
        au_state = None
        co_state = None
        if self.N[0].violated:
            au_state = "VIOLATED"
        elif self.N[0].fulfilled:
            au_state = "FULFILLED"
        elif self.N[0].active:
            au_state = "ACTIVE"
        elif self.N[0].expired:
            au_state = "FULFILLED"

        if self.N[1].violated:
            co_state = "VIOLATED"
        elif self.N[1].fulfilled:
            co_state = "FULFILLED"
        elif self.N[1].active:
            co_state = "ACTIVE"

        consent = {
            "id": self.id,
            "state_transition_time_step": self.g.model.steps,
            "state": self.state,
            "giver": self.g.unique_id,
            "receiver": self.r.unique_id,
            "action": self.t[0].name,
            "resource": self.t[1].name,
            "stated_goal": self.g_R.name,
            "AU_detachment_condition": self.N[0].c_det,
            "AU_expiration_condition": f"{self.N[0].c_exp[0].name}",
            "AU_state": au_state,
            "CO_antecedent": self.N[1].p.name,
            "CO_consequent": self.N[1].g_R.name,
            "CO_expiration_condition": f"EXP_{self.N[1].g_R.name}",
            "CO_state": co_state
        }

        return consent

    

    """
    print("---"*10)
            
                
                
                

                print("---Related CO---:")
                print(f"Antecedent p: {h_consent.N[1].p.name}")
                print(f"Consequent gR: {h_consent.N[1].g_R.name}")
                print(f"Expiration condition: {h_consent.g_R.valid_from} to {h_consent.g_R.valid_to}")
                if h_consent.N[1].violated:
                    print("CO State: Violated")
                elif h_consent.N[1].fulfilled:
                    print("CO State: Fulfilled")
                elif h_consent.N[1].active:
                    print("CO State: Active")
                print("---"*10)
    
    
    """