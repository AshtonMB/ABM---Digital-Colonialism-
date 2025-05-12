# agent.py = agent definitions

from mesa import Agent

# Two Different Types of Agents
#   1) Tech/Digital Superpower Agent (Dominant) 
#   2) Recipient Culture Agent

class DigitalDeployAgent(Agent):
    def __init__(self,model,tech_dominance,deployment_policy="all"): # deployment policy default
        super().__init__(model)
        self.tech_dominance = tech_dominance # maybe on a scale from 1 to 5
        self.deployment_policy = deployment_policy # incorporate into GUI so that it can be choosen between: all, random, or agents of specific attributes 

    #   deployment logic method
    def deployment_targets(self):
        # all condition
        # random condition
        # filtered high access digital score condition
    def tech_dominance(self):
        # if a certain amount of agents collapse or ban --> reduce tech dominance score

class ReceivingAgent(Agent):
    '''
    Represents the community/region/culture that recieves the digital technology
    Determines whether to adopt or ban based in tuility and post-adoption effects
    '''
    def __init__(self,model,cultural_resilience,infrastructure_strength,
                 community_wellbeing,adoption_threshold,digital_access_score):
        super().__init__(model)
        self.cultural_resilience = cultural_resilience # resistance to cultural change
        self.infrastructure_strength = infrastructure_strength # ability to implement/sustain tech
        self.community_wellbeing= community_wellbeing # impacted by tech over time
        self.adoption_threshold = adoption_threshold # individual resistance
        self.digital_access_score = digital_access_score # respresents their position in the digital divide
        self.adopted = False # boolean state of choosing to adopt tech
        self.banned = False # boolean state of choosing to ban tech after observing effects
        self.collapse = False # collapse status 
        
    
    def receive_tech(self):
        # update status of agent receiving the tech
        # trigger adoption decision 
    def decide_to_adopt(self):
        # implementation cost of technology and cultural fit 
        # Adopt if (Perceived Utility + Neighbor Influence - Cultural Resilience) > Adoption Threshold
    def assess_impact(self):
        # after adoption, update attributes 
        # may trigger ban decision 
    def decide_to_ban(self):
        # impact thresholds are assessed, if crossed agent bans tech