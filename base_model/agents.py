import mesa
import seaborn as sns
import numpy as np
import pandas as pd

from mesa.experimental.cell_space import CellAgent
import math

# TODO: Right now, if the agent cannot find a resource, th goal still gets accomplished. Gotta fix that.
# TODO: Functions for printing resource lists properly.

"""
1.  So at each step, an agent can accomplish 1 goal 
    by collecting all resources it needs in a single step for a single goal.
    This will enable us to get rid of deadlocks. Otherwise, if at each step they can obtain only 1 resource,
    they may end up in a lock for ever.

2. As soon as an agent collects all resources for a goal, the goal is deemed accomplished.
    When the goal is accomplished in a step, in the next step the agent checks if it still needs the resource in any of its future goals,
    if so it does not release it and keeps using it in the next step.
    This way, prohibitions will be meaningful. Giver can prohibit receiver from using the resource in a second recipe.
    Commitments and authorizations inherently make sense.

3. If the agent cannot obtain all resources for the current goal, it simply waits. But the resources it manages to obtain become
    unavailable for other agents.

4. But how are we going to use consent in this scheme? Maybe if an agent will use a resource, they wont give to other agents?

"""

def get_distance(cell_1, cell_2):
    """
    Returns the eucledian distance between two cells.
    Used in resource_finder function.
    """

    x1, y1 = cell_1.coordinate
    x2, y2 = cell_2.coordinate

    dx = x1 - x2
    dy = y1 - y2

    return math.sqrt(dx ** 2 + dy ** 2)

"""

I made available resources types of ingredients, oven, and stove. This way it will be easy to come up with goals.
Different agents will aim to cook different dishes.
If they do not own the ingredient they need, they have to take it from another agent. First without consent, then with.

"""

# So different agents will own different resources.
# Different agents will have different goals.
# These goals will require certain resources.
# How should I implement these goals tho.


class ChefAgent(CellAgent):
    """An agent that needs to cook certain dishes and owns some resources. """

    def __init__(self, 
                 model,
                 cell,
                 goals = [],
                 sovereigned_resources = []
                 ):
        # Pass the parameters to the parent class.
        super().__init__(model)
        self.remaining_goals = goals
        self.current_goal = None
        self.sovereigned_resources = sovereigned_resources
        self.sovereigned_resources_available = sovereigned_resources.copy()
        self.sovereigned_resources_self_use = []
        self.current_borrowed_resources = []
        self.all_resources_self_use = []
        self.lent_away_resources = []
        self.accomplished_goals = []
        self.cell = cell
        self.all_required_future_resources = self.initialize_required_future_resources()


    def interpret_goals(self):
        """ The agent needs to interpret its goals and needs to use a handler to accomplish that goal. """
        if not self.remaining_goals:
            return
        
        for goal in self.remaining_goals[:]:
            self.current_goal = goal
            for subgoal in goal[1]:
                res_type = subgoal.split("_")[1]
                # try obtaining required resources for the goal
                self.resource_finder(res_type)

            # TODO: check goal accomplishment.
            if self.check_goal_accomplisment():
                print(f"Agent: {self.unique_id} accomplished goal: {self.current_goal[0]}.")
                # If the agent has acquired all the resources, it should complete the goal
                self.accomplished_goals.append(self.current_goal)
                # Remove the goal from remanining goals, update resources that will be needed in the future
                self.remaining_goals.remove(self.current_goal)
                self.current_goal = None
                self.all_required_future_resources = self.initialize_required_future_resources()
                # If the resource wont be needed again, release it.
                for res in self.all_resources_self_use[:]:
                    if res.type not in self.all_required_future_resources:
                        print(f"Agent: {self.unique_id} has released resource: {res.name}, owned by: {res.owner}")
                        res.in_use_by = None
                        self.all_resources_self_use.remove(res)
                        
                        # other is the owner of the resource.
                        other = self.model._all_agents[res.owner - 1]
                        # If its your resource, make it available.
                        if other == self:
                            self.sovereigned_resources_available.append(res)
                            self.sovereigned_resources_self_use.remove(res)
                        # If its other's resource, make it available.
                        else:
                            self.current_borrowed_resources.remove(res)
                            other.sovereigned_resources_available.append(res)
                            other.lent_away_resources.remove(res)
            else:
                print(f"Agent: {self.unique_id} could not accomplish the goal: {self.current_goal[0]}")


            # TODO: Before releasing I can do extensive tests by using assesrt statements.
            # Check if the agent has obtained all the resources needed for the goal.
            # Check if the lists are correctly updated at self side, owner side, etc.
            # I'll need to create the test cases myself for this, probably.
            
            break # treat only 1 goal at each tick


    def initialize_required_future_resources(self):
        """
        In __init__, initialize the list of required future resources, as resource type strings.
        Also will be ran after each goal completion.
        """
        required_future_resources = []
        for goal in self.remaining_goals:
            for res in goal[1]:
                if res.split("_")[1] not in required_future_resources:
                    required_future_resources.append(res.split("_")[1])

        return required_future_resources


    def resource_finder(self, res_type):
        """
        This function finds the required resource instance for the goal.
        4. Check resources already borrowed and not yet released.
        3. Check resources owned by the agent and not lent to another.
        2. Check resources borrowed from other agents and currently held.
        1. Check the closest resource owner who hasn't lent the resource.

        Called from self.interpret_resources function.
        """

        # Well since this is already reasource finder, it can be found in self.current_borrowed resources.
        # Any changes in the goal completion scheme will be handled from self.goal_interpreter.
        # Borrowed from other agents and not yet released.
        for res in self.current_borrowed_resources:
            if res.type == res_type:
                print(f"Agent: {self.unique_id}, has already borrowed {res.name}, owned by {res.owner}")
                return
        
        # Owned by the agent, currently in use by the agent.
        for res in self.sovereigned_resources_self_use:
            if res.type == res_type:
                print(f"Agent: {self.unique_id}, has already acquired its own resource: {res.name}, owned by: {res.owner}")
                return
            
        # Owned by the agent, currently used by nobody
        for res in self.sovereigned_resources_available[:]:
            if res.type == res_type:
                # TODO: If this is just the resource finder function, then maybe the following 3 lines should be inside another function.
                # TODO: Check if the loop runs properly, we remove from the list after all.
                print(f"Agent: {self.unique_id}, has just acquired resource: {res.name}, owned by: {res.owner}")
                res.in_use_by = self
                self.sovereigned_resources_available.remove(res)
                self.sovereigned_resources_self_use.append(res)
                self.all_resources_self_use.append(res)
                return
            
        # Get the closest available resource of this type
        # 1. Get a list of all the agents, that hold one of the required type of resource, which is also non-acquired
        # Get a list of all the agents with distances.
        agent_distances = self.get_agent_distances()
        # Sort in ascending order by distance
        sorted_agents = sorted(agent_distances, key=lambda x: x[1])
        for agent, dist in sorted_agents:
            # 2. If the resource is not in use, acquire it.
            res = self.check_available_resource_of_agent(res_type=res_type, agent=agent)
            if res:
                print(f"Agent: {self.unique_id}, has just acquired resource: {res.name}, owned by: {res.owner}")
                res.in_use_by = self
                agent.sovereigned_resources_available.remove(res)
                agent.lent_away_resources.append(res)
                self.current_borrowed_resources.append(res)
                self.all_resources_self_use.append(res)
                return
        print(f"Agent: {self.unique_id}, tried to acquire resource: {res_type}, but could not find any available.")
            
        
    def check_available_resource_of_agent(self, res_type, agent: "ChefAgent"):
        """
        Function that checks if the agent in the arguments owns a resource of type res_type that is also available.
        Called from self.resource_finder function.
        """
        for res in agent.sovereigned_resources_available:
            if res.type == res_type:
                return res
        
        return None
    
    def get_agent_distances(self):
        """
        Returns all agents except self with distances to self.
        Called from self.resource_finder
        """
        all_agents = self.model.agents
        agent_distances = []
        for agent in all_agents:
            if agent != self:
                agent_distances.append((agent, get_distance(self.cell, agent.cell)))
        return agent_distances
    

    def update_required_future_resources(self):
        """
        TODO: Depricated! I can use initialize_required_future_resources instead.
        This function creates a list of all required future resources. 
        It is used to decide if the agent should release an obtained resource.
        It is called after each goal completion.
        """

        # If all goals are accomplished, the agent wont need any resources in the future.
        if not self.remaining_goals:
            self.all_required_future_resources = []
        else:
            for res in self.model.resources:
                res_needed = False
                for goal in self.remaining_goals:
                    if res in goal[1]:
                        res_needed = True
                if not res_needed:
                    self.all_required_future_resources.remove(res)

    def check_goal_accomplisment(self):
        for subgoal in self.current_goal[1]:
            if subgoal.split("_")[1] not in self.all_resources_self_use:
                return False

    def print_goals_and_resources(self):
        print(f"Agent: {self.unique_id}, coords: {self.cell.coordinate}")
        print(f"Agent: {self.unique_id}, resources: {self.sovereigned_resources}, goals: {self.remaining_goals}")