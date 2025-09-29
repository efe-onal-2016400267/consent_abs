# OK. We start with agent personas.

"""
No-consent agent. Always prioritizes the goal: Even after consent violation or unrealization, keeps the resource. So its goal oriented. DOES IT RELEASE THE RESOURCE IF IT NEEDS IT FOR ANOTHER GOAL?

Consent agent. Always prioritizes the consent: If there is a violation or unrealization, it returns the related resource. DOES IT RELEASE THE RESURCE IF IT NEEDS IT FOR ANOTHER GOAL? Well if it didn't violate, it can? OR should I start by making everyone return the resource once the goal is met?

50-50 consent agent. Behaves like consent agent half of the time, behaves like no-consent agent half of the time.
OR should I start by making everyone return the resource once the goal is met?
"""


# So now giver cannot take the item any more.
# Its about receivers.
from consent_agent import ConsentChefAgent

class GoalFirstAgent(ConsentChefAgent):
    """
    Goal first agent. Always prioritizes the goal: If there is a violation or unrealization, it does not care, 
    doesnt relase the related resource.
    """
    def __init__(self, model, cell, goals=..., sovereigned_resources=...):
        super().__init__(model, cell, goals, sovereigned_resources)

        self.agent_persona = "GoalFirstAgent"

    def check_received_consents(self):
        """
        It doesn't do anything when received consent is violated.
        """
        return

    def check_given_consents(self):
        """
        Function that checks and updated consent state given by the agent.
        Update is handled in the functions of ConsentInstance.
        Agents check for the violations of the consents they have given.
        After accomplishing a goal, they should update the states of the received consents.
        """
        for CI in self.consents_given[:]:
            if CI.state in ("ACTIVE", "FULFILLED"):
                # Call consent functions
                CI.update_norm_activations(agent=self) # First lets see states of the norms
                violated = CI.is_violated(agent=self)
                fulfilled = CI.is_fulfilled(agent=self)
                unrealized = CI.is_unrealized(agent=self)
                reneg = CI.is_renegotiate(agent=self)
                active = CI.is_active(agent=self)