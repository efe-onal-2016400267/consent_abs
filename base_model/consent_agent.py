from base_agent import BaseChefAgent
from atom import Atom
from norm import Authorization, Commitment
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

    def negotiate(self, other:"ConsentChefAgent", res, g_R, p):
        """
        Consent negotiation function.
        Called from self.request_consent.
        """
        # Let giver agent g dont negotiatie at all for now
        # TODO: Implement negotiation strategies
        # TODO: What are c_det and c_exp going to be?
        # c_exp might be time related. Or we can add need atoms. If the owner need the resource back, expiretaion condition becomes true.
        agreement = True
        if agreement:
            c_det = []
            # A dummy c_exp for the 
            c_exp = [Atom(name=f"Agent99---", agent_id=self.unique_id, truth=True)]
            AU = Authorization(model=self.model, g=other.unique_id, r=self.unique_id, c=tuple((c_det, c_exp)), t=Action(p=p, r=res))
            CO = Commitment(model=self.model, g=other.unique_id, r=self.unique_id, p=p, g_R=g_R)
            return [AU, CO]
        return []
    
    def request_consent(self, other, res):
        """
        Function that requests consent from another agent.
        CI = <g, r, N, g_R, t>
        t = <p, r>
        """
         # Create stated goal g_R: the main goal the agent wants to accomplish
        g_R = Atom(name=f"Agent{self.unique_id}-{self.current_goal[0]}---", agent_id=self.unique_id, truth=True)
        # Create action t = <p, r> 
        t = tuple((Atom(name=f"Agent{self.unique_id}--use_{res.type}--", agent_id=self.unique_id, truth=True), res))
        p = t[0]
        CI = ConsentInstance(g=other, r=self, N=None, g_R=g_R, t=t)

        agreement = False
        # Perform negotiation
        N = self.negotiate(other=other, res=res, g_R=g_R, p=p)
        if N:
            agreement = True
            CI.N = N
            CI.state = "ACTIVE"
        else:
            agreemet = False
            CI.state = "DEFERRED"
       
        self.consents_received.append(CI)
        other.consents_given.append(CI)
        self.last_consent_received = CI
        self.model.consent_history.append(CI)

        return CI

    def check_given_consents(self):
        """
        Function that checks and updated consent state given by the agent.
        Update is handled in the functions of ConsentInstance.
        """
        for CI in self.consents_given:
            # Call consent functions
            violated = CI.is_violated()
            fulfilled = CI.is_fulfilled()
            unrealized = CI.is_unrealized()
            reneg = CI.is_renegotiate()
            active = CI.is_active()

            # TODO: What happens when the agent realizes that consent was violated for example.

    def check_received_consents(self):
        """
        Function that checks the consent states received by the agent.
        """
        for CI in self.consents_received:
            # Call consent functions
            violated = CI.is_violated()
            fulfilled = CI.is_fulfilled()
            unrealized = CI.is_unrealized()
            reneg = CI.is_renegotiate()
            active = CI.is_active()

    def norm_state_update(self):
        """
        At each step all agents should update the states of the norms they have for the consents they have received and given.
        They should do it at the beginning of the step.
        So this function is called from self.step.
        """
        # Given consents, to keep track of your own resources
        # Received consents, to be able to inform your behavior, maybe self will release the resource if consent is violated.
        # TODO: TEST: Of course some norms will be checked for activation twice in this case. That should be ok.
        for CI in self.consents_given + self.consents_received:
            for norm in CI.N:
                norm.activation_update()
        

