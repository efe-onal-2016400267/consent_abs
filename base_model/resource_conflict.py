class ResourceConflict:
    """
    A resource conflict is a conflict between two agents over a resource.
    """
    def __init__(self, res, owner, receiver, activity, R_accomplished_goal_list, birth_step):
        self.res = res
        self.owner = owner
        self.receiver = receiver
        self.activity = activity
        self.R_accomplished_goal_list = R_accomplished_goal_list
        self.birth_step = birth_step
        self.conflict_count = 1

class ResourceConflictGoal:
    """
    A resource conflict goal is a goal that R has accomplished using the resource during the conflict.
    """
    def __init__(self, goal, goal_owner, accomplish_step):
        self.goal = goal
        self.goal_owner = goal_owner
        self.accomplish_step = accomplish_step