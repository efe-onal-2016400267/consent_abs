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
        self.norm_state_counter = {
            "AU": {
                "violated": 0,
                "expired": 0,
                "fulfilled": 0,
                "ever_active": 0
            },
            "CO": {
                "violated":0,
                "fulfilled": 0,
                "ever_active": 0
            }
        }

        # maybe some lists to keep track of the related propositions.

    def negotiate(self, other:"ConsentChefAgent"=None, res=None, g_R=None, p=None, au_exp_step=None, co_exp_step=None):
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
            au_c_exp = [Atom(name=f"EXP-Agent{self.unique_id}--{subgoal_name}--{current_step}-{au_exp_step}", agent_id=self.unique_id, truth=True, resource_id=res.name, valid_from=self.model.steps, valid_to=au_exp_step)]
            # Add a copy of the c_exp object to model.state
            au_c_exp_to_state = [copy.deepcopy(au_c_exp[0])]
            # in the state, it starts as False. After releasing, we turn it to True so it matches the expiration condition.
            for cond in au_c_exp_to_state:
                self.model.state.set_false(cond)

            AU = Authorization(model=self.model, g=other.unique_id, r=self.unique_id, c=tuple((c_det, au_c_exp)), t=Action(p=p, r=res))
            CO = Commitment(model=self.model, g=other.unique_id, r=self.unique_id, p=p, g_R=g_R)
            return [AU, CO]
        return []
    
    def request_consent(self, other, res):
        """
        Function that requests consent from another agent.
        CI = <g, r, N, g_R, t>
        t = <p, r>
        """
        # First check if R or G still has an active consent instance for the resource
        r_active_consent_check = self.check_active_consent_for_resource(self.consents_received, res)
        g_active_consent_check = self.check_active_consent_for_resource(other.consents_given, res)

        if r_active_consent_check or g_active_consent_check:
            return

        # Create stated goal g_R: the main goal the agent wants to accomplish
        # For now let g_Rs violate after 3 steps
        
        g_R = Atom(name=f"Agent{self.unique_id}-{self.current_goal[0]}---", agent_id=self.unique_id, truth=True, valid_from=self.model.steps, valid_to=self.model.steps + 4)
        # Create action t = <p, r> 
        t = tuple((Atom(name=f"Agent{self.unique_id}--use_{res.type}--", agent_id=self.unique_id, truth=True), res))
        p = t[0]
        self.model.consent_count += 1
        # Create consent id. Which is the instance count of the model.
        consent_id = self.model.consent_count
        # 1 instance for the G, 1 for R, 1 for the model.
        # Because what if both agents are wrong about the state of the consent instance. 
        CI_g = ConsentInstance(g=other, r=self, N=None, g_R=g_R, t=t, res=res, id=consent_id, owner=other)
        CI_r = ConsentInstance(g=other, r=self, N=None, g_R=g_R, t=t, res=res, id=consent_id, owner=self)
        CI_m = ConsentInstance(g=other, r=self, N=None, g_R=g_R, t=t, res=res, id=consent_id, owner=None)

        agreement = False
        # Perform negotiation
        N = self.negotiate(other=other, res=res, g_R=g_R, p=p, au_exp_step=self.model.steps + 1, co_exp_step=self.model.steps + 1)
        instances = [CI_g, CI_r, CI_m]
        if N:
            agreement = True
            for CI in instances:
                # Clone the norms
                N_clone = [N[0].clone(), N[1].clone()]
                CI.N = N_clone
                CI.state = "ACTIVE"
        else:
            agreement = False
            for CI in instances:
                CI.state = "DEFERRED"
       
        self.consents_received.append(CI_r)
        other.consents_given.append(CI_g)
        self.last_consent_received = CI_r
        self.model.living_consents.append(CI_m)
        self.model.consent_history.append(CI_m) # might need a 4th instance fr this.

        return agreement

    def check_given_consents(self):
        """
        Function that checks and updated consent state given by the agent.
        Update is handled in the functions of ConsentInstance.
        Agents check for the violations of the consents they have given.
        After accomplishing a goal, they should update the states of the received consents.
        """
        for CI in self.consents_given[:]:
            if CI.state == "ACTIVE":
                # Call consent functions
                CI.update_norm_activations(agent=self) # First lets see states of the norms
                violated = CI.is_violated(agent=self)
                fulfilled = CI.is_fulfilled(agent=self)
                unrealized = CI.is_unrealized(agent=self)
                reneg = CI.is_renegotiate(agent=self)
                active = CI.is_active(agent=self)

                # If given CI is vioalted, the agent treats the issue
                if violated:
                    self.treat_consent_violations(agent=self, other=CI.r, CI=CI)
                # TODO: If fulfilled was never tested!!! I couldnt come up with a usecase because when an agent fulfils a CI (accomplishes a goal) 
                # it automatically updates received consents.
                if fulfilled:
                    self.treat_consent_fulfilment(agent=self, other=CI.r, CI=CI)
        
        return

    def check_received_consents(self):
        """
        Function that checks the consent states received by the agent.
        Called after goal accomplishment in BaseChefAgent.interpret_goals.
        """
        for CI in self.consents_received[:]:
            if CI.state == "ACTIVE":
                # Call consent functions
                CI.update_norm_activations(agent=self) # First lets see states of the norms
                violated = CI.is_violated(agent=self)
                fulfilled = CI.is_fulfilled(agent=self)
                unrealized = CI.is_unrealized(agent=self)
                reneg = CI.is_renegotiate(agent=self)
                active = CI.is_active(agent=self)

                # If received CI is violated agent treats the issue
                # TODO: If violated was never tested!!! I couldnt come up with a usecase.
                if violated:
                    self.treat_consent_violations(agent=CI.g, other=self, CI=CI)
                if fulfilled:
                    self.treat_consent_fulfilment(agent=CI.g, other=self, CI=CI)
        
        return


    def treat_consent_violations(self, agent, other, CI):
        """
        This function will be overriten in different consent agent personas.
        Lets say the base form of the consent agent reclaims the resource and makes necessary changes in necessary agent lists, 
        it also makes the necessary changes in the env state and removes the CI from reveived/given consents lists of the agent
        Called from self.check_given_consents() function.
        That is, an agent takes action as soon as it realizes a consent it has given was violated.
        other is the receiver of the CI and resource.
        agent is the consent giver.
        When we call this function from self.check_received_consents(), we switch agent and other arguments.
        """
        # Treat the resource lists.
        agent.sovereigned_resources_available.append(CI.res)
        if CI.res in other.current_borrowed_resources:
            other.current_borrowed_resources.remove(CI.res)
        if CI.res in other.all_resources_self_use:
            other.all_resources_self_use.remove(CI.res)
        if CI.res in agent.lent_away_resources:
            agent.lent_away_resources.remove(CI.res)
        # Update model.state.
        agent.model.state.set_false(Atom(name=f"Agent{other.unique_id}--use_{CI.res.type}--", agent_id=other.unique_id))
        agent.model.state.print_state()
        # Delete expiration condition, it was created solely for the consent, it is not epistemic.
        exp_atoms = [atom for key, atom in self.model.state.atoms.items() if "EXP" in atom.name and atom.agent_id==other.unique_id and atom.resource_id==CI.res.name]
        for exp_atom in exp_atoms[:]:
            self.model.state.atoms.pop(exp_atom.name)

        print(f"Consent violation treated by consent giver: {agent.unique_id}, for resource: {CI.res.name} borrowed by: {other.unique_id}")

    def treat_consent_fulfilment(self, agent, other, CI):
        """
        Differently 
        """
        # Delete expiration condition, it was created solely for the consent, it is not epistemic.
        exp_atoms = [atom for key, atom in self.model.state.atoms.items() if "EXP" in atom.name and atom.agent_id==other.unique_id and atom.resource_id==CI.res.name]
        for exp_atom in exp_atoms[:]:
            self.model.state.atoms.pop(exp_atom.name)

        print(f"Consent fulfilment treated by consent giver: {agent.unique_id}, for resource: {CI.res.name} borrowed by: {other.unique_id}")

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
        Called from self.expiry_check function.
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
    
    def unrealization_check(self):
        """
        At the end of the step the agent should check if there are any unrealized consents.
        TODO: do we need this one?
        """
        c_exp = None
        for CI in self.consents_received:
            unrealized = False
            if CI.state == "ACTIVE":
                unrealized = CI.is_unrealized(agent=self)
            if unrealized:
                c_exp = CI.N[0].c[1]

        return


    def expiry_check(self):
        """
        Checks if any AUs will expire in the next step. If so, release such resources.
        This will execute at the end of the step for the agent.
        We will make this specific for one of the personas.
        Its implemented now to be able to test AU expiry and AU violation.
        If the agent releases the resource we should delete the expiry atom.
        Called from self.treat_future_AU_expiry().
        """
        # Get the expiration atoms
        exp_atoms, ep_atoms = self.get_exp_atoms()

        # Get the atoms where the agent is the R and expiration step is the next step
        current_step = self.model.steps
        expiry_detections = []
        eps_of_agent = []
        for exp in exp_atoms:
            if exp.agent_id == self.unique_id and exp.valid_to == current_step:
                expiry_detections.append(exp)

        for ep in ep_atoms:
            if ep.agent_id == self.unique_id:
                eps_of_agent.append(ep)

        return expiry_detections, eps_of_agent
    
    def treat_future_AU_expiry(self):
        """
        This function will be different for different personas.
        Some agents dont care if AU expires.
        Some return the resource if the realize AU will expire in the next step.
        For now, lets just return it.
        """
        res = None
        owner = None
        ep_of_interest = None
        expiry_detections, ep_atoms = self.expiry_check()
        for exp in expiry_detections:
            res_id = exp.resource_id
            # Get the ep atom for that resource
            for ep in ep_atoms:
                if res_id == ep.resource_id:
                    ep_of_interest = ep # This will be turned false. exp will be deleted
                    break
            # 1. make ep atom false
            # 2. release the resource
                # 2.1. remove the resource from self.currently_borrowed_resources
                # 2.2. put the resource to the available resources of the owner
            # 3. remove the exp atom
            # 4. The consent instance will stay active if the agent releases but the agent cannot fulfill 
                # the consent since it cannot achieve the stated goal any more.

            # Get the resource object so that we have the owner as an agent object too.
            for res_s in self.current_borrowed_resources:
                if res_s.name == res_id:
                    res = res_s
                    owner = self.model._all_agents[res.owner - 1]
                    break
            
            # We set the epistemic atom to False since the agent has released the resource
            # Now the atom is False, if c_exp becomes true, we should move to the UNREALIZED state for the consent.
            # And this should work for R, G, and the model.
            # So we must keep the expiry atom
            if ep_of_interest:
                self.model.state.set_false(ep_of_interest)
            if res in self.current_borrowed_resources:
                self.current_borrowed_resources.remove(res)
            if owner and res in owner.lent_away_resources:
                owner.lent_away_resources.remove(res)
            if owner and res not in owner.sovereigned_resources_available:
                owner.sovereigned_resources_available.append(res)
            # del self.model.state.atoms[exp.name]

        return
    
    def check_active_consent_for_resource(self, consent_list, res):
        """
        Once the agent releases a resource due to future expiry, it shouldn't be able to create a
            new consent instance for the same resource, if R or G still has an active CI for that resource.
        So, this function returns active CIs given a CI list and resource.
        """
        for CI in consent_list:
            if CI.res == res and CI.state == "ACTIVE":
                return True
        return False


