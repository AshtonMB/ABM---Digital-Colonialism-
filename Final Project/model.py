'''
Ashton Mayo-Beavers
Agent Based Modeling - Final Project
Innovation Diusion Analysis of Digital Colonialism:An Agent-Based Approach to Modeling Cultural
Resistance to Digital Colonialism
model.py 

'''
from mesa.model import Model
from mesa.datacollection import DataCollector
import networkx as nx
import random

from agent import ReceivingAgent, TechSuperpowerAgent


class DigitalColonialismModel(Model):
    '''
    ABM simulating digital colonialism through the lens of tech adoption and culture resistance
    ABM simulating digital colonialism: a tech superpower attempts to diffuse digital technology
    into receiving cultures, which may adopt, resist, or ban the tech based on cultural and infrastructural traits.
    '''
    def __init__(self, num_receiving_agents=50, implementation_cost=5, cultural_fit=0.8,
                 deployment_policy='random', tech_dominance=3.0, network_type='small_world', seed=None):
        super().__init__()
        self.seed = seed or random.randint(0, 99999)
        self.random = random.Random(self.seed)

        self.num_receiving_agents = num_receiving_agents # changed in GUI
        self.implementation_cost = implementation_cost # changed in GUI
        self.cultural_fit = cultural_fit # changed in GUI
        self.deployment_policy = deployment_policy # changed in GUI
        self.tech_dominance = tech_dominance # changed in GUI

        self.ReceivingAgentClass = ReceivingAgent  # Needed for isinstance() checks in agents
        
        # Initialize receiving agents list for reference
        self.receiving_agents = []
        self.init_agents()
        
        # Create network AFTER agents are created to  map properly
        self.create_network(network_type)

        # DataCollector tracks statistics across the model over time
        self.datacollector = DataCollector(
            model_reporters={
                "TotalAdopted": lambda m: sum(1 for a in m.agents if isinstance(a, ReceivingAgent) and a.adopted),
                "TotalBanned": lambda m: sum(1 for a in m.agents if isinstance(a, ReceivingAgent) and a.banned),
                "TotalCollapsed": lambda m: sum(1 for a in m.agents if isinstance(a, ReceivingAgent) and a.collapsed),
                "AvgWellbeing": lambda m: sum(a.wellbeing for a in m.receiving_agents) / len(m.receiving_agents),
                "TechDominance": lambda m: m.tech_agent.tech_dominance
            },
            agent_reporters={
                "Adopted": "adopted",
                "Banned": "banned",
                "Wellbeing": "wellbeing",
                "Collapsed": "collapsed"
            }
        )

    def get_network(self):
        return self.network

    def create_network(self, network_type):
        '''
        Initializes the social network topology.
        Each agent is a node, and edges represent potential influence.
        Only includes receiving agents, not tech superpower agents.
        '''
        if network_type == 'small_world':
            # Create network with sequential node IDs first
            self.network = nx.watts_strogatz_graph(n=len(self.receiving_agents), k=4, p=0.3, seed=self.seed)
            
            # Create mapping from sequential IDs to agent unique_ids
            sequential_to_unique = {i: agent.unique_id for i, agent in enumerate(self.receiving_agents)}
            
            # Relabel nodes to match agent unique_ids
            self.network = nx.relabel_nodes(self.network, sequential_to_unique)

    def init_agents(self):
        '''
        Creates and assigns attributes to all agents with realistic parameter distributions.
        Uses correlated infrastructure and digital access to model economic inequality.
        '''        
        for i in range(self.num_receiving_agents):
            # Determine if this is a privileged or average community
            if self.random.random() < 0.3:  # 30% are "privileged communities"
                infrastructure_strength = float(self.random.uniform(8, 12))
                digital_access_score = float(self.random.uniform(0.7, 1.0))
                community_type = "privileged"
            else:  # 70% are "average communities"  
                infrastructure_strength = float(self.random.uniform(2, 8))
                digital_access_score = float(self.random.uniform(0.2, 0.7))
                community_type = "average"
            
            # Cultural resistance and adoption threshold are independent of wealth
            # (Rich communities can still be culturally resistant, poor communities can be open)
            cultural_resilience = float(self.random.uniform(0.05, 0.8))
            adoption_threshold = float(self.random.uniform(0.1, 1.0))
            
            # Pass parameters as positional arguments S
            agent = ReceivingAgent(
                self,  # model (positional)
                cultural_resilience,  # positional
                infrastructure_strength,  # positional  
                adoption_threshold,  # positional
                digital_access_score  # positional
            )
            
            # Store community type for analysis (optional)
            agent.community_type = community_type
            
            self.agents.add(agent)
            self.receiving_agents.append(agent)

        # Create single TechSuperpower Agent
        tech_agent = TechSuperpowerAgent(
            model=self,
            tech_dominance=self.tech_dominance,
            deployment_policy=self.deployment_policy
        )
        self.agents.add(tech_agent)

        self.tech_agent = tech_agent  # reference for easier access

    def step(self):
        '''
        Execute one simulation step with clean, predictable order:
        1. Collect data
        2. Tech superpower sets targeting  
        3. Receiving agents respond
        '''
        self.datacollector.collect(self)
        
        # Tech superpower acts first (set targeting)
        self.tech_agent.step()
        
        # Then receiving agents act in random order
        receiving_agents = [a for a in self.agents if isinstance(a, ReceivingAgent)]
        self.random.shuffle(receiving_agents)
        for agent in receiving_agents:
            agent.step()
