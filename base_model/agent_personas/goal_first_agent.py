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

    def check_received_consents(self):
        """
        It doesn't do anything when received consent is violated.
        """
        return

    def check_given_consents(self):
        """
        It doesn't do anything when given consent is violated.
        """
        return