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
        # Create stated goal g_R: the main goal the agent wants to accomplish
        # For now let g_Rs violate after 3 steps
        
        g_R = Atom(name=f"Agent{self.unique_id}-{self.current_goal[0]}---", agent_id=self.unique_id, truth=True, valid_from=self.model.steps, valid_to=self.model.steps + 1)
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
        N = self.negotiate(other=other, res=res, g_R=g_R, p=p, au_exp_step=self.model.steps + 2, co_exp_step=self.model.steps + 1)
        instances = [CI_g, CI_r, CI_m]
        if N:
            agreement = True
            for CI in instances:
                CI.N = N
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
                CI.update_norm_activations() # First lets see states of the norms
                violated = CI.is_violated()
                fulfilled = CI.is_fulfilled()
                unrealized = CI.is_unrealized()
                reneg = CI.is_renegotiate()
                active = CI.is_active()

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
                CI.update_norm_activations() # First lets see states of the norms
                violated = CI.is_violated()
                fulfilled = CI.is_fulfilled()
                unrealized = CI.is_unrealized()
                reneg = CI.is_renegotiate()
                active = CI.is_active()

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
        other.current_borrowed_resources.remove(CI.res)
        other.all_resources_self_use.remove(CI.res)
        agent.lent_away_resources.remove(CI.res)
        # Update model.state.
        agent.model.state.set_false(Atom(name=f"Agent{other.unique_id}--use_{CI.res.type}--", agent_id=other.unique_id))
        agent.model.state.print_state()
        # Delete expiration condition, it was created solely for the consent, it is not epistemic.
        exp_atoms = [atom for key, atom in self.model.state.atoms.items() if "EXP" in atom.name and atom.agent_id==other.unique_id and atom.resource_id==CI.res.name]
        for exp_atom in exp_atoms[:]:
            self.model.state.atoms.pop(exp_atom.name)
        # Remove the consent from living consents list.
        # agent.model.living_consents.remove(CI)
        # agent.remove_CI_by_id(agent.model.living_consents, CI.id)
        # Remove the consent from given/received lists of the two agents.
        # Do we really need to remove from these two lists?
        # We could just keep them with terminal states.
        # agent.consents_given.remove(CI)
        # other.consents_received.remove(CI)
        print(f"Consent violation treated by consent giver: {agent.unique_id}, for resource: {CI.res.name} borrowed by: {other.unique_id}")

    def treat_consent_fulfilment(self, agent, other, CI):
        """
        Differently 
        """
        # Delete expiration condition, it was created solely for the consent, it is not epistemic.
        exp_atoms = [atom for key, atom in self.model.state.atoms.items() if "EXP" in atom.name and atom.agent_id==other.unique_id and atom.resource_id==CI.res.name]
        for exp_atom in exp_atoms[:]:
            self.model.state.atoms.pop(exp_atom.name)
        # Remove the consent from living consents list.
        # agent.model.living_consents.remove(CI)
        # agent.remove_CI_by_id(agent.model.living_consents, CI.id)
        # Remove the consent from given/received lists of the two agents.
        # agent.consents_given.remove(CI)
        # other.consents_received.remove(CI)
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
    
    def remove_CI_by_id(self, consent_list, id):
        """
        DEPRICATED
        Removes a CI from a list. Since we have different object instances for the same consent instance,
        we can't just remove the object. For example, while removing from model.living_consents, we need the id.
        Called from self.treat_consent_fulfillment, self.treat_consent_violation.
        """
        consent_list[:] = [CI for CI in consent_list if CI.id != id]

