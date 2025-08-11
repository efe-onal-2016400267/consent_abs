from base_agent import BaseChefAgent
from atom import Atom

class ConsentChefAgent(BaseChefAgent):
    """
    ConsentChefAgent can comply with consent.
    Hence it implements/overrides related functions so that it can update truth values, etc.
    """
    def __init__(self, model, cell, goals=..., sovereigned_resources=...):
        super().__init__(model, cell, goals, sovereigned_resources)

        # maybe some lists to keep track of the related propositions.
    
    def interpret_goals(self):
        """ 
        The agent needs to interpret its goals and needs to use the handler to accomplish that goal. 
        Override the function from BaseChefAgent so that we now update the state as well.
        """
        if not self.remaining_goals:
            return
        
        for goal in self.remaining_goals[:]:
            self.current_goal = goal
            for subgoal in goal[1]:
                res_type = subgoal.split("_")[1]
                # try obtaining required resources for the goal
                self.resource_finder(res_type)

            # check goal accomplishment.
            if self.check_goal_accomplisment():
                print(f"Agent: {self.unique_id} accomplished goal: {self.current_goal[0]}.")
                # If the agent has acquired all the resources, it should complete the goal
                self.accomplished_goals.append(self.current_goal)
                # Remove the goal from remanining goals, update resources that will be needed in the future
                self.remaining_goals.remove(self.current_goal)
                # TODO: Implement goal related proposition update
                self.model.state.set_true(Atom(name=f"{self.unique_id}-"))
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

            
            break # treat only 1 goal at each tick
