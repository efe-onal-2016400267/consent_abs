from consent_agent import ConsentChefAgent
from action import Action
from norm import Authorization, Commitment

class ConsentInstance:
    """
    CI = <g, r, N, g_R, t> where
        g: Consent giver
        r: Consent receiver
        N: List of norms agreed on
        g_R: Stated goal that becomes true after CO is fulfilled. So the main goal of the agent
        t: The action for which the consent is given
    """
    def __init__(self, g: "ConsentChefAgent", r: "ConsentChefAgent", N, g_R, t:"Action"):
        self.g = g
        self.r = r
        self.N = N
        self.g_R = g_R
        self.t = t
        self.state = "negotiating" # TODO: unsolicited consent

    def is_violated(self):
        pass

    def is_fulfilled(self):
        pass

    def is_unrealized(self):
        pass

    def is_renegotiate(self):
        pass

    