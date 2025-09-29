from atom import Atom

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

5. An agent cannot get the same goal twice. Handled by using random.sample in NoConsentModel class.

"""

"""

I made available resources types of ingredients, oven, and stove. This way it will be easy to come up with goals.
Different agents will aim to cook different dishes.
If they do not own the ingredient they need, they have to take it from another agent. First without consent, then with.

"""


class BaseChefAgent(CellAgent):
    """Base agent that needs to cook certain dishes and owns some resources. """

    def __init__(self, 
                 model,
                 cell,
                 goals = [],
                 sovereigned_resources = []
                 ):
        
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
        self.num_remaining_goals = len(self.remaining_goals) # to be reported
        self.num_accomplished_goals = len(self.accomplished_goals) # to be reported
        self.num_resource_conflicts = 0 # to be reported - when agent cannot accomplish goal due to another agent holding a resource that this agent owns AND the related consent is VIOLATED


    def interpret_goals(self):
        """ The agent needs to interpret its goals and needs to use the handler to accomplish that goal. """
        self.check_received_consents()
        if not self.remaining_goals:
            return
        
        for goal in self.remaining_goals[:]:
            self.current_goal = goal
            resource_conflict_this_goal = False
            for subgoal in goal[1]:
                res_type = subgoal.split("_")[1]
                # try obtaining required resources for the goal
                resource_found, conflict_type = self.resource_finder(res_type)
                if not resource_found and conflict_type == 'sovereign_conflict':
                    # Only count as conflict if agent owns the resource but cannot access it
                    resource_conflict_this_goal = True
                    break  # No need to check other subgoals once we find a conflict

            # Once all resources are acquired, update norm states if self is a ConsentChefAgent
            # Done here because norms will find their actual states after the resources were acquired and related atoms were reflected into model.state.
            self.norm_activation_update()

            # TODO: check goal accomplishment.
            if self.check_goal_accomplisment():
                #print(f"Agent: {self.unique_id} accomplished goal: {self.current_goal[0]}.")
                # If the agent has acquired all the resources, it should complete the goal
                self.accomplished_goals.append(self.current_goal)
                # Remove the goal from remanining goals, update resources that will be needed in the future, update model state.
                self.remaining_goals.remove(self.current_goal)
                # After the goal lists are updated, we call the goal count update function for reporting
                self.goal_count_update()
                #print(f"Number of remaning goals for agent {self.unique_id}: {self.num_remaining_goals}")
                #print(f"Number of accomplished goals for agent {self.unique_id}: {self.num_accomplished_goals}")
                # We dont feed res.name here because the atom is a main goal atom.
                self.model.state.set_true(Atom(name=f"Agent{self.unique_id}-{self.current_goal[0]}---", agent_id=self.unique_id))
                # After accomplishing a goal, an agent should update the states of the CI's it has received
                self.check_received_consents() # Will do this even if there is no goal accomplishment, after this block
                self.current_goal = None
                #self.model.state.print_state()

                # Resource release was here, moved it to resource release function
                
                # Once all resources are released, update norm states again, if self is a ConsentChefAgent
                self.norm_activation_update()
                #self.treat_future_AU_expiry()
            else:
                #print(f"Agent: {self.unique_id} could not accomplish the goal: {self.current_goal[0]}")
                # Track resource conflicts when goal cannot be accomplished
                if resource_conflict_this_goal:
                    self.num_resource_conflicts += 1
                #self.treat_future_AU_expiry()
                # Before the step ends for the agent, check for AU expiry.
                # This will be based on personas
                # self.check_received_consents()
                self.goal_count_update()
                pass
            

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
        
        Returns:
            tuple: (found: bool, conflict_type: str)
            - found: True if resource was acquired, False otherwise
            - conflict_type: 'sovereign_conflict' if agent owns resource but it's unavailable,
                           'no_resource' if no resource of this type exists anywhere
        """

        # Well since this is already reasource finder, it can be found in self.current_borrowed resources.
        # Any changes in the goal completion scheme will be handled from self.goal_interpreter.
        # Borrowed from other agents and not yet released.
        for res in self.current_borrowed_resources:
            if res.type == res_type:
                #print(f"Agent: {self.unique_id}, has already borrowed {res.name}, owned by {res.owner}")
                return True, None
        
        # Owned by the agent, currently in use by the agent.
        for res in self.sovereigned_resources_self_use:
            if res.type == res_type:
                #print(f"Agent: {self.unique_id}, has already acquired its own resource: {res.name}, owned by: {res.owner}")
                return True, None
            
        # Owned by the agent, currently used by nobody
        for res in self.sovereigned_resources_available[:]:
            if res.type == res_type:
                #print(f"Agent: {self.unique_id}, has just acquired resource: {res.name}, owned by: {res.owner}")
                res.in_use_by = self
                if res in self.sovereigned_resources_available:
                    self.sovereigned_resources_available.remove(res)
                self.sovereigned_resources_self_use.append(res)
                self.all_resources_self_use.append(res)
                # Update the state with the subgoal
                self.model.state.set_true(Atom(name=f"Agent{self.unique_id}--use_{res.type}--", agent_id=self.unique_id, resource_id=res.name))
                #self.model.state.print_state()
                return True, None
            
        # Check if agent owns any resource of this type but it's being used by someone else
        for res in self.lent_away_resources:
            if res.type == res_type:
                # Agent owns this resource but it's being used by someone else
                # Check if there's a VIOLATED consent instance for this resource
                if self.has_violated_consent_for_resource(res):
                    #print(f"Agent: {self.unique_id}, owns resource {res.name} but it's being used by {res.in_use_by.unique_id} and consent is VIOLATED")
                    return False, 'sovereign_conflict'
                else:
                    # Resource is lent but consent is not violated - this is not a conflict
                    #print(f"Agent: {self.unique_id}, owns resource {res.name} but it's being used by {res.in_use_by.unique_id} but consent is not violated")
                    return False, 'no_resource'
            
        # Get the closest available resource of this type
        # 1. Get a list of all the agents, that hold one of the required type of resource, which is also non-acquired
        # Get a list of all the agents with distances.
        agent_distances = self.get_agent_distances()
        # Sort in ascending order by distance
        sorted_agents = sorted(agent_distances, key=lambda x: x[1])
        for agent, dist in sorted_agents:
            # 2. If the resource is not in use, request for a consent, if you get it, acquire the resource.
            res = self.check_available_resource_of_agent(res_type=res_type, agent=agent)
            if res:
                has_consent = self.request_consent(other=agent, res=res)
                if has_consent:
                    #print(f"Agent: {self.unique_id}, has just acquired resource: {res.name}, owned by: {res.owner}")
                    res.in_use_by = self
                    if res in agent.sovereigned_resources_available:
                        agent.sovereigned_resources_available.remove(res)
                    agent.lent_away_resources.append(res)
                    self.current_borrowed_resources.append(res)
                    self.all_resources_self_use.append(res)
                    self.model.state.set_true(Atom(name=f"Agent{self.unique_id}--use_{res.type}--", agent_id=self.unique_id, resource_id=res.name))
                    #self.model.state.print_state()
                    return True, None
        
        # If we reach here, no resource of the required type was found anywhere
        #print(f"Agent: {self.unique_id}, tried to acquire resource: {res_type}, but could not find any available.")
        return False, 'no_resource'
            
        
    def check_available_resource_of_agent(self, res_type, agent: "BaseChefAgent"):
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
                agent_distances.append((agent, self.get_distance(self.cell, agent.cell)))
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
        """
        This function checks if the agent has accomplished the current goal by checking if all resources for all subgoals were acquired.
        Called from self.interpret_goals.
        """
        all_resource_types_used = [r.type for r in self.all_resources_self_use]

        for subgoal in self.current_goal[1]:
            if subgoal.split("_")[1] not in all_resource_types_used:
                return False
        return True

    def get_distance(self, cell_1, cell_2):
        """
        Returns the eucledian distance between two cells.
        Used in resource_finder function.
        """

        x1, y1 = cell_1.coordinate
        x2, y2 = cell_2.coordinate

        dx = x1 - x2
        dy = y1 - y2

        return math.sqrt(dx ** 2 + dy ** 2)

    def print_goals_and_resources(self):
        print(f"Agent: {self.unique_id}, coords: {self.cell.coordinate}")
        print(f"Agent: {self.unique_id}, resources: {self.sovereigned_resources}, goals: {self.remaining_goals}")

    def negotiate(self, other=None, res=None, g_R=None, p=None, au_exp_step=None, co_exp_step=None):
        pass

    def request_consent(self, other:"BaseChefAgent", res):
        """
        Function that request consent from another agent.
        Will be overriden in ConsentChefAgent class.
        """
        return True
    
    def check_given_consents(self):
        """
        Function that checks and updated consent state given by the agent.
        Update is handled in the functions of ConsentInstance.
        Agents check for the violations of the consents they have given.
        After accomplishing a goal, they should update the states of the received consents.
        """
        pass

    def check_received_consents(self):
        """
        Function that checks the consent states received by the agent.
        Called after goal accomplishment in BaseChefAgent.interpret_goals.
        """
        pass

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
        pass

    def norm_activation_update(self):
        """
        At each step all agents should update the states of the norms they have for the consents they have received and given.
        Once all resources are acquired, update norm states if self is a ConsentChefAgent.
        Done after the resource transactions because norms will find their actual states after the resources were acquired and related atoms were reflected into model.state.
        Called from BaseChefAgent.interpret goals, after all resources tried to be acquired.
        """
        pass

    def update_exp_cond(self, res):
        """
        At the beginning of each step, an agent should check if it needs to update any expiration conditions.
        An expiration condition states that the resource must be released before a certain step of the simulation.
        At CI state check that occurs in every step, this expiration is carried to AU, which is carried to CI.
        TODO: EXP atoms should be deleted after the norm state was updated.
        Called from self.model.step() function.
        """
        pass

    def get_exp_atoms(self):
        """
        Returns the exp atom list concerning the agent along with the related epistemic atoms.
        Called from self.update_exp_cond function.
        """
        pass

    def remove_CI_by_id(self, consent_list, id):
        """
        Removes a CI from a list. Since we have different object instances for the same consent instance,
        we can't just remove the object. For example, while removing from model.living_consents, we need the id.
        Called from ConsentChefAgent.treat_consent_fulfillment, self.treat_consent_violation.
        """
        pass

    def goal_count_update(self):
        """
        Update accomplished and remaining goal counts to be reported.
        """

        self.num_accomplished_goals = len(self.accomplished_goals)
        self.num_remaining_goals = len(self.remaining_goals)
        # Note: num_resource_conflicts is already updated when conflicts occur

    def expiry_check(self):
        """
        Checks if any AUs will expire in the next step. If so, release such resources.
        This will execute at the end of the step for the agent.
        We will make this specific for one of the personas.
        Its implemented now to be able to test AU expiry and AU violation.
        """
        pass

    def treat_future_AU_expiry(self):
        """
        This function will be different for different personas.
        Some agents dont care if AU expires.
        Some return the resource if the realize AU will expire in the next step.
        For now, lets just return it.
        """
        pass

    def unrealization_check(self):
        """
        At the end of the step the agent should check if there are any unrealized consents.
        """
        pass

    def check_active_consent_for_resource(self, consent_list, res):
        """
        Once the agent releases a resource due to future expiry, it shouldn't be able to create a
            new consent instance for the same resource, if R or G still has an active CI for that resource.
        So, this function returns active CIs given a CI list and resource.
        """
        pass

    def has_violated_consent_for_resource(self, res):
        """
        Check if there's a VIOLATED consent instance related to the given resource.
        This is used to determine if a resource conflict should be counted.
        
        Args:
            res: Resource instance to check for violated consents
            
        Returns:
            bool: True if there's a VIOLATED consent for this resource, False otherwise
        """
        # Check consents given by this agent for this resource
        for consent in getattr(self, 'consents_given', []):
            if hasattr(consent, 'res') and consent.res == res and consent.state == "VIOLATED":
                return True
        
        return False

    def release_resources(self):
        """
        We are going to have 2 phases:
        1. Goal accomplishing phase
        2. Resource releasing phase
        We had to do this so that the atoms are updated at the same time for R, G, and the model.
        Called after all agents interpret their goals.
        """

        self.all_required_future_resources = self.initialize_required_future_resources()
        # If the resource wont be needed again, release it.
        for res in self.all_resources_self_use[:]:
            if res.type not in self.all_required_future_resources:
                #print(f"Agent: {self.unique_id} has released resource: {res.name}, owned by: {res.owner}")
                res.in_use_by = None
                if res in self.all_resources_self_use:
                    self.all_resources_self_use.remove(res)

                # Make related subgoal atoms False
                self.model.state.set_false(Atom(name=f"Agent{self.unique_id}--use_{res.type}--", agent_id=self.unique_id))
                #self.model.state.print_state()
                        
                # other is the owner of the resource.
                other = self.model._all_agents[res.owner - 1]
                # If its your resource, make it available.
                if other == self:
                    self.sovereigned_resources_available.append(res)
                    if res in self.sovereigned_resources_self_use:
                        self.sovereigned_resources_self_use.remove(res)
                # If its other's resource, make it available.
                else:
                    if res in self.current_borrowed_resources:
                        self.current_borrowed_resources.remove(res)
                    other.sovereigned_resources_available.append(res)
                    if res in other.lent_away_resources:
                        other.lent_away_resources.remove(res)
                    # If the agent has released another agent's resource, then it should update the expiration conditions.
                    # self.update_exp_cond(res)