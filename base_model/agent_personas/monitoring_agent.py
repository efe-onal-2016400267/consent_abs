from consent_agent import ConsentChefAgent

class MonitoringAgent(ConsentChefAgent):
    """
    Consent agent. Always prioritizes the consent: If there is a violation or unrealization, it returns the related resource. DOES IT RELEASE THE RESURCE IF IT NEEDS IT FOR ANOTHER GOAL? Well if it didn't violate, it can? 
    OR should I start by making everyone return the resource once the goal is met?
    """
    def __init__(self, model, cell, goals=..., sovereigned_resources=...):
        super().__init__(model, cell, goals, sovereigned_resources)

        self.agent_persona = "MonitoringAgent"



    def treat_future_AU_expiry(self):
            """
            This function will be different for different personas.
            Some agents dont care if AU expires.
            Some return the resource if they realize AU will expire in the next step.
            For now, lets just return it.
            """
            res = None
            owner = None
            ep_of_interest = None
            expiry_detections, ep_atoms = self.AU_expiry_check()
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

                if self.model.print_execution:
                    print(f"Agent: {self.unique_id} has released resource: {res.name}, owned by: {res.owner}")

    def treat_consent_violations(self, agent, other, CI):
        """Only release when we are the borrower; do not reclaim when we are the giver."""
        if agent is self:
            return
        super().treat_consent_violations(agent, other, CI)

    def treat_future_CO_expiry(self):
        """Placeholder for possible CO-expiry-specific behaviour."""
        pass