from action import Action
from norm import Norm, Authorization, Commitment

class ConsentInstance:
    """
    CI = <g, r, N, g_R, t> where
        g: Consent giver
        r: Consent receiver
        N: List of norms agreed on
        g_R: Stated goal that becomes true after CO is fulfilled. So the main goal of the agent
        t: The action for which the consent is given
    """
    def __init__(self, g, r, N: "Norm", g_R, t:"Action"):
        self.g = g
        self.r = r
        self.N = N
        self.g_R = g_R
        self.t = t
        self.state = "NEGOTIATING" # TODO: unsolicited consent

    def is_violated(self):
        """
        If any norms in N are violated, then ConsentInstance is also violated.
        """
        # If ConsentInstance is already violated, return True.
        if self.state == "VIOLATED":
            return True
        
        # If ConsentInstance hasnt already completed its life
        if self.state not in ("FULFILLED", "UNREALIZED", "DEFERRED"): # Icould just check ACTIVE
            violated = False
            for n in self.N:
                if n.is_violated():
                    violated = True
                    self.state = "VIOLATED"
            return violated
        else:
            return False

    def is_fulfilled(self):
        """
        If all of the norms in N are fulfilled, then ConsentInstance is also fulfilled.
        """

        # If the consent instance is already fulfilled, return true
        if self.state == "FULFILLED":
            return True

        # If the norm was already violated, it cannot be fulfilled.
        if self.state in ("VIOLATED", "UNREALIZED", "DEFERRED"):
            return False
        
        # If any of the norms is not fulfilled, ConsentInstance is not fulfilled either.
        for n in self.N:
            if not n.is_fulfilled():
                return False
            
        # Otherwise, ConsentInstance is fulfilled.
        self.state = "FULFILLED"
        return True

    def is_unrealized(self):
        """
        If any of the AUs in N expire, then ConsentInstance is unrealized.
        """
        if self.state not in ("FULFILLED", "VIOLATED"):
            for n in self.N:
                if n.type == "AU" and n.expired:
                    self.state = "UNREALIZED"
                    return True
        return False

    def is_renegotiate(self):
        """
        TODO: How can we find a use case for renegotiation?
        """
        pass

    def is_active(self):
        return self.state == "ACTIVE"

    