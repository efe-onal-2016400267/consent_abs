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

class ConsentFirstAgent(ConsentChefAgent):
    """
    Consent agent. Always prioritizes the consent: If there is a violation or unrealization, it returns the related resource. DOES IT RELEASE THE RESURCE IF IT NEEDS IT FOR ANOTHER GOAL? Well if it didn't violate, it can? 
    OR should I start by making everyone return the resource once the goal is met?
    """
    def __init__(self, model, cell, goals=..., sovereigned_resources=...):
        super().__init__(model, cell, goals, sovereigned_resources)

        self.agent_persona = "ConsentFirst"

    def check_given_consents(self):
        """
        For now, givers won't recalaim the resources when there is a violation.
        But the receiver decides what to do.
        So this function will just pass
        """
        return

    def check_received_consents(self):
        """
        For received consent, the agent will return the resource when there is a violation.
        """
        return super().check_received_consents()

    

    