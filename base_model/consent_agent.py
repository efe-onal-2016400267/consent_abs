from base_agent import BaseChefAgent
from atom import Atom
from norm import Authorization
from action import Action
from consent import ConsentInstance

class ConsentChefAgent(BaseChefAgent):
    """
    ConsentChefAgent can comply with consent.
    Hence it implements/overrides related functions so that it can update truth values, etc.
    """
    def __init__(self, model, cell, goals=..., sovereigned_resources=...):
        super().__init__(model, cell, goals, sovereigned_resources)

        self.consents_given = []
        self.consents_received = []
        self.last_consent_received = None

        # maybe some lists to keep track of the related propositions.

    def negotiate(self, other:"ConsentChefAgent", res):
        """
        Consent negotiation function.
        Called from self.request_consent.
        """
        # Post condition of the action
        p = Atom(name=f"Agent{self.unique_id}--use_{res.type}--", agent_id=self.unique_id)
        # Let giver agent g dont negotiatie at all for now
        # TODO: Implement negotiation strategies
        # TODO: What are c_det and c_exp going to be?
        # c_exp might be time related. Or we can add need atoms. If the owner need the resource back, expiretaion condition becomes true.
        agreement = True
        if agreement:
            c_det = []
            c_exp = []
            return [Authorization(model=self.model, g=other.unique_id, r=self.unique_id, c=tuple(c_det, c_exp), t=Action(p=p, r=res))]
        return []
    
    def request_consent(self, other, res):
        """
        Function that requests consent from another agent.
        CI = <g, r, N, g_R, t>
        t = <p, r>
        """
         # Create stated goal g_R: the main goal the agent wants to accomplish
        g_R = Atom(name=f"Agent{self.unique_id}-{self.current_goal[0]}---", agent_id=self.unique_id)
        # Create action t = <p, r> 
        t = tuple(Atom(name=f"Agent{self.unique_id}--use_{res.type}--", agent_id=self.unique_id), res)
        CI = ConsentInstance(g=other, r=self, N=None, g_R=g_R, t=t)

        agreement = False
        # Perform negotiation
        N = self.negotiate(other, res)
        if N:
            agreement = True
            CI.N = N
            CI.state = "ACTIVE"
       
        self.consents_received.append(CI)
        other.consents_given.append(CI)
        self.last_consent_received = CI

        return CI

    def check_given_consents(self):
        """
        Function that checks 
        """
        for CI in self.consents_given:
            # Call consent functions
            pass

    def check_received_consents(self):
        pass
