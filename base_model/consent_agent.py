from base_agent import BaseChefAgent
from atom import Atom
from norm import Authorization, Commitment
from action import Action
from consent import ConsentInstance
import copy

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

    def negotiate(self, other:"ConsentChefAgent", res, g_R, p, exp_step):
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
            # c_exp shows until which step the auth is valid.
            # After taking an action, an agent should check.
            # EXP_agentX--use_butter-10-20 the agent must release the rice before step 20. 10 is just the current step where consent is initiated.
            # So the agent should make this atom True after realeasing the resource.
            subgoal_name = p.name.split("-")
            subgoal_name = subgoal_name[2]
            # TODO: implement relative time
            current_step = self.model.steps
            c_exp = [Atom(name=f"EXP-Agent{self.unique_id}--{subgoal_name}--{current_step}-{exp_step}", agent_id=self.unique_id, truth=True, resource_id=res.name, valid_from=self.model.steps, valid_to=exp_step)]
            # Add a copy of the c_exp object to model.state
            c_exp_to_state = [copy.deepcopy(c_exp[0])]
            # in the state, it starts as False. After releasing, we turn it to True so it matches the expiration condition.
            for cond in c_exp_to_state:
                self.model.state.set_false(cond)
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
        # Lets give exp_step as current_step + 10
        N = self.negotiate(other=other, res=res, g_R=g_R, p=p, exp_step=self.model.steps + 1)
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
        Agents check for the violations of the consents they have given.
        After accomplishing a goal, they should update the states of the received consents.
        """
        for CI in self.consents_given:
            # Call consent functions
            CI.update_norm_activations() # First lets see states of the norms
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
            CI.update_norm_activations() # First lets see states of the norms
            violated = CI.is_violated()
            fulfilled = CI.is_fulfilled()
            unrealized = CI.is_unrealized()
            reneg = CI.is_renegotiate()
            active = CI.is_active()

    def norm_activation_update(self):
        """
        At each step all agents should update the states of the norms they have for the consents they have received and given.
        Once all resources are acquired, update norm states if self is a ConsentChefAgent.
        Done after the resource transactions because norms will find their actual states after the resources were acquired and related atoms were reflected into model.state.
        Called from BaseChefAgent.interpret goals, after all resources tried to be acquired.
        """
        # Given consents, to keep track of your own resources
        # Received consents, to be able to inform your behavior, maybe self will release the resource if consent is violated.
        # TODO: TEST: Of course some norms will be checked for activation twice in this case. That should be ok.
        for CI in self.consents_given + self.consents_received:
            for norm in CI.N:
                norm.activation_update()
        

    def update_exp_cond(self):
        """
        At the beginning of each step, an agent should check if it needs to update any expiration conditions.
        An expiration condition states that the resource must be released before a certain step of the simulation.
        At CI state check that occurs in every step, this expiration is carried to AU, which is carried to CI.
        TODO: EXP atoms should be deleted after the norm state was updated.
        Called from self.model.step() function.
        """
        exp_atoms, ep_atoms = self.get_exp_atoms()
        for exp_atom in exp_atoms:
            #if atom.resource_id == res.name and atom.agent_id == self.unique_id:
            for ep_atom in ep_atoms:
                # if the exp atom and ep atom are from the same resource and the deadline has passed, then the exp atom turns true, meaning the AU has expired.
                if ep_atom.resource_id == exp_atom.resource_id and self.model.steps > exp_atom.valid_to:
                    self.model.state.set_true(exp_atom)


    def get_exp_atoms(self):
        """
        Returns the exp atom list concerning the agent along with the related epistemic atoms.
        Called from self.update_exp_cond function.
        """

        # Return exp atoms
        exp_atom_list = []
        ep_atom_list = []
        for atom_name, atom in self.model.state.atoms.items():
            if atom.agent_id == self.unique_id and atom.name.split("-", 1)[0] == "EXP":    
                exp_atom_list.append(atom)
            if atom.agent_id == self.unique_id and atom.name.split("-", 1)[0] != "EXP":
                ep_atom_list.append(atom)
        # Return related epistemic atoms


        return exp_atom_list, ep_atom_list
