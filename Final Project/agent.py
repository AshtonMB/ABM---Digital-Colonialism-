'''
Ashton Mayo-Beavers
Agent Based Modeling - Final Project
Innovation Diusion Analysis of Digital Colonialism:An Agent-Based Approach to Modeling Cultural
Resistance to Digital Colonialism
agent.py 

'''
from mesa import Agent, Model
import random

class ReceivingAgent(Agent):
    '''
    Represents the community/region/culture that receives the digital technology
    Determines whether to adopt or ban based on utility and post-adoption effects
    '''
    def __init__(self, model, cultural_resilience, infrastructure_strength,
                 adoption_threshold, digital_access_score):
        super().__init__(model)
        self.cultural_resilience = cultural_resilience # resistance to cultural change 0.05-.8
        self.infrastructure_strength = infrastructure_strength # ability to implement/sustain tech 2-12
        self.adoption_threshold = adoption_threshold # individual resistance .2-1.0
        self.digital_access_score = digital_access_score # represents their position in the digital divide .1-.7
        
        self.adopted = False # boolean state of choosing to adopt tech
        self.banned = False # boolean state of choosing to ban tech after observing effects
        self.collapsed = False # collapse status 

        # --- Wellbeing Tracking ---
        self.wellbeing = 100
        # Tracks historical wellbeing to determine if tech should be banned post-adoption
        self.past_wellbeing = []
        self.ban_threshold = 65 # ban sooner when things go bad
        self.ban_window = 3 # faster decisions
        self.survival_threshold = 35 # collapse sooner
        self.was_targeted = True
        
    def step(self):
        # Skip banned agents; execute decision cycle for adoption and track wellbeing impact
        if self.banned or self.collapsed: 
            return

        # Always update wellbeing, but only consider adoption if targeted
        if getattr(self, 'was_targeted', False):
            self.decide_to_adopt()
        
        self.update_wellbeing()  # Always update wellbeing regardless of targeting
        self.track_wellbeing_and_ban()
        self.check_collapse()

    def decide_to_adopt(self):
        # adoption logic
        if self.adopted or self.banned:
            return # already adopted
        
        perceived_utility = self.calculate_perceived_utility()
        peer_influence = self.calculate_peer_influence()
        cultural_resis = float(self.cultural_resilience)
        #  reduced cultural resistance impact
        # .5 so deduction of cultural resistance isnt absolute
        #  Originally: adoption_score = perceived_utility + peer_influence - self.cultural_resilience

        adoption_score = perceived_utility + peer_influence - (cultural_resis * 0.5)
        
        # Add some randomness and threshold modeling superpower influence/power (advertising, incentives, pressue, etc)
        randomness = self.model.random.uniform(-0.2, 0.3)  # Slight positive bias
        final_score = adoption_score + randomness
        
        if final_score > float(self.adoption_threshold):
            self.adopted = True
            print(f"Agent {self.unique_id}: ADOPTED Score: {final_score:.2f} > {self.adoption_threshold:.2f}")
        else:
            print(f"Agent {self.unique_id}: NON-ADOPTED Score: {final_score:.2f} < {self.adoption_threshold:.2f}")
 
    def calculate_perceived_utility(self):
        # utility calculation
        cost = self.model.implementation_cost
        cultural_fit = self.model.cultural_fit
        
        # Base utility 
        # Formula: (self.infrastructure_strength / cost) * cultural_fit * self.digital_access_score
        base_utility = (self.infrastructure_strength / cost) * cultural_fit * self.digital_access_score
        
        # Multiply by tech dominance for superpower influence
        tech_boost = 1 + (self.model.tech_dominance / 10)  # 1.1x to 1.5x multiplier
        
        # Add minimum utility floor
        # prevents complete adoption impossibility
        utility = max(0.3, base_utility * tech_boost)  # At least 0.3 utility, because runs resulted in too low thresholds
        
        return utility

    def calculate_peer_influence(self):
        # Uses network neighbors (Watts-Strogatz) to determine adoption influence
        if not hasattr(self.model, 'network') or self.unique_id not in self.model.network:
            return 0  # No network influence if not in network
            
        neighbors_ids = list(self.model.network.neighbors(self.unique_id))
        neighbors = []
        for neighbor_id in neighbors_ids:
            for agent in self.model.receiving_agents:
                if agent.unique_id == neighbor_id:
                    neighbors.append(agent)
                    break
        
        if len(neighbors) == 0:
            return 0
        
        adopters = [n for n in neighbors if hasattr(n, "adopted") and n.adopted]
        banned = [n for n in neighbors if hasattr(n, "banned") and n.banned]
        
        # Stronger peer influence
        positive_influence = len(adopters) * 0.4  # Stronger positive influence
        negative_influence = len(banned) * 0.3    # Moderate negative influence
        
        return (positive_influence - negative_influence) / len(neighbors)

    def update_wellbeing(self):
        if self.adopted:
            # High risk, high reward for adopters
            delta = (self.infrastructure_strength - 5) * 4  # 4x multiplier for visualization 
            self.wellbeing += delta
            
            # infrastructure degradation
            self.infrastructure_strength -= 0.4  # tech wear
            
            # Random tech failures --> tech dependence 
            if self.model.random.random() < 0.08:  # 8% chance of tech crisis (arbitrary value)
                crisis_damage = self.model.random.uniform(15, 30)
                self.wellbeing -= crisis_damage
                print(f"Agent {self.unique_id}: TECH CRISIS -{crisis_damage:.1f} wellbeing")
        else:
            # digital divide effects
            decline = 2.5 + self.model.random.uniform(0, 2.0)  # 2.5-4.5 per step
            self.wellbeing -= decline

        # Clamp wellbeing to [0, 100]
        self.wellbeing = max(0, min(100, self.wellbeing))

    def track_wellbeing_and_ban(self):
        """
        Agents can ban technology in two ways:
        1. Post-adoption: After adopting and experiencing personal negative effects
        2. Network-based: After observing negative outcomes among adopted neighbors
        """
        # Track personal wellbeing for post-adoption banning
        self.past_wellbeing.append(self.wellbeing)
        if len(self.past_wellbeing) > self.ban_window:
            self.past_wellbeing.pop(0)
        
        # POST-ADOPTION BANNING: If agent adopted but experienced negative effects
        if self.adopted and len(self.past_wellbeing) == self.ban_window:
            avg_personal_wellbeing = sum(self.past_wellbeing) / self.ban_window
            if avg_personal_wellbeing < self.ban_threshold:
                self.banned = True
                self.adopted = False
                print(f"Agent {self.unique_id}: POST-ADOPTION BAN - wellbeing {avg_personal_wellbeing:.1f}")
                return
        
        # NETWORK-BASED BANNING: Observe neighbors' experiences
        if self.banned or not hasattr(self.model, 'network') or self.unique_id not in self.model.network:
            return
            
        neighbors_ids = list(self.model.network.neighbors(self.unique_id))
        neighbors = []
        for neighbor_id in neighbors_ids:
            for agent in self.model.receiving_agents:
                if agent.unique_id == neighbor_id:
                    neighbors.append(agent)
                    break
        
        if len(neighbors) == 0:
            return
        
        # network banning
        adopted_neighbors = [n for n in neighbors if n.adopted and not n.banned and not n.collapsed]
        collapsed_neighbors = [n for n in neighbors if n.collapsed]
        
        # Immediate panic if neighbor collapsed
        if len(collapsed_neighbors) > 0:
            self.banned = True
            self.adopted = False
            print(f"Agent {self.unique_id}: PANIC BAN - neighbor collapsed.")
            return
        
        if len(adopted_neighbors) >= 1:  # Only need 1 adopted neighbor
            suffering_neighbors = [n for n in adopted_neighbors if n.wellbeing < 70]
            
            if len(suffering_neighbors) > 0:
                self.banned = True
                self.adopted = False
                print(f"Agent {self.unique_id}: NETWORK BAN - {len(suffering_neighbors)} neighbors suffering")

    def check_collapse(self):
        if self.wellbeing < self.survival_threshold:
            self.collapsed = True
            self.adopted = False
            self.banned = True
            print(f"Agent {self.unique_id}: COLLAPSED! Wellbeing: {self.wellbeing:.1f}")

class TechSuperpowerAgent(Agent):
    def __init__(self, model, tech_dominance, deployment_policy='all'):
        super().__init__(model)
        self.tech_dominance = tech_dominance  # 1 to 5 scale
        self.deployment_policy = deployment_policy  # 'all', 'random', 'filtered'
        self.deployed_agents = []

    def step(self):
        # Deploy tech based on policy
        self.deploy_technology()
        # respond to bans
        self.monitor_global_rejection()

    def deploy_technology(self):
        # reset was_targeted for all agents first
        for agent in self.model.agents:
            if isinstance(agent, self.model.ReceivingAgentClass):
                agent.was_targeted = False
                
        receiving_agents = [agent for agent in self.model.agents
                            if isinstance(agent, self.model.ReceivingAgentClass) 
                            and not agent.banned and not agent.collapsed]

        if self.deployment_policy == 'all':
            targets = receiving_agents
        elif self.deployment_policy == 'random':
            high_access = [a for a in receiving_agents if a.digital_access_score >= 0.6]
            low_access = [a for a in receiving_agents if a.digital_access_score < 0.4]
            
            # Target more agents (50% instead of 30%)
            num_to_deploy = max(1, int(len(receiving_agents) * 0.5))  # 50% instead of 30%
            num_high = num_to_deploy // 2
            num_low = num_to_deploy - num_high
            # randomly selecting agents from two roup criteria
            selected_high = self.model.random.sample(high_access, min(len(high_access), num_high))
            selected_low = self.model.random.sample(low_access, min(len(low_access), num_low))

            targets = selected_high + selected_low
        elif self.deployment_policy == 'filtered': # agents with 'high-access'
            targets = [a for a in receiving_agents if a.digital_access_score >= 0.6]
        
        else:
            targets = []

        self.deployed_agents = targets
        for agent in targets:
            agent.was_targeted = True
        print(f"DEPLOYED = {len(self.deployed_agents)+1}")

    def monitor_global_rejection(self):
        """
        Simple dynamic dominance: tech dominance decreases when technology 
        causes widespread problems (bans + collapses), increases when successful
        """
        receiving_agents = [agent for agent in self.model.agents
                            if isinstance(agent, self.model.ReceivingAgentClass)]
        
        if len(receiving_agents) == 0:
            return

        # Count different outcomes
        adopted_count = sum(1 for a in receiving_agents if a.adopted and not a.banned)
        banned_count = sum(1 for a in receiving_agents if a.banned)
        collapsed_count = sum(1 for a in receiving_agents if a.collapsed)
        total_count = len(receiving_agents)
        
        # Calculate success and failure rates
        success_rate = adopted_count / (len(self.deployed_agents)+1)
        failure_rate = (banned_count+collapsed_count) / total_count
        
        # Adjust tech dominance based on outcomes
        if failure_rate > 0.3:  # High failure rate
            dominance_loss = 0.3 * (failure_rate - 0.3)  # Scale with how bad the failure is
            self.tech_dominance = max(1.0, self.tech_dominance - dominance_loss)
            print(f"Tech dominance DECREASED to {self.tech_dominance:.2f} (failure rate: {failure_rate:.1%})")
            
        elif success_rate > 0.4:  # High success rate
            dominance_gain = 0.2 * (success_rate - 0.4)  # Scale with how good the success is
            self.tech_dominance = min(5.0, self.tech_dominance + dominance_gain)
            print(f"Tech dominance INCREASED to {self.tech_dominance:.2f} (success rate: {success_rate:.1%})")
        
        # Gradual recovery toward baseline when outcomes are mixed
        elif 0.1 <= failure_rate < 0.3 and 0.2 < success_rate < 0.4:
            # Slow drift toward baseline (3.0)
            if self.tech_dominance > 3.0:
                self.tech_dominance = max(3.0, self.tech_dominance - 0.05)
            elif self.tech_dominance < 3.0:
                self.tech_dominance = min(3.0, self.tech_dominance + 0.05)

