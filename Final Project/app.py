'''
Ashton Mayo-Beavers
Agent Based Modeling - Final Project
Innovation Diusion Analysis of Digital Colonialism:An Agent-Based Approach to Modeling Cultural
Resistance to Digital Colonialism
app.py 

'''
import solara
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from model import DigitalColonialismModel
from agent import ReceivingAgent


# Reactive model state
model_ref = solara.Reactive(None)
step_count = solara.Reactive(0)
adopted_over_time = solara.Reactive([])
banned_over_time = solara.Reactive([])
collapsed_over_time = solara.Reactive([])
wellbeing_over_time = solara.Reactive([])

def step_model():
    if model_ref.value:
        model_ref.value.step()
        step_count.value += 1
        
        # Count all agent states
        adopted = sum(1 for a in model_ref.value.agents if isinstance(a, ReceivingAgent) and a.adopted)
        banned = sum(1 for a in model_ref.value.agents if isinstance(a, ReceivingAgent) and a.banned)
        collapsed = sum(1 for a in model_ref.value.agents if isinstance(a, ReceivingAgent) and a.collapsed)
        
        # Calculate average wellbeing
        receiving_agents = [a for a in model_ref.value.agents if isinstance(a, ReceivingAgent)]
        avg_wellbeing = sum(a.wellbeing for a in receiving_agents) / len(receiving_agents) if receiving_agents else 50
        
        # Ensure all arrays are updated together
        current_adopted = list(adopted_over_time.value)
        current_banned = list(banned_over_time.value)
        current_collapsed = list(collapsed_over_time.value)
        current_wellbeing = list(wellbeing_over_time.value)

        
        current_adopted.append(adopted)
        current_banned.append(banned)
        current_collapsed.append(collapsed)
        current_wellbeing.append(avg_wellbeing)
        
        adopted_over_time.value = current_adopted
        banned_over_time.value = current_banned
        collapsed_over_time.value = current_collapsed
        wellbeing_over_time.value = current_wellbeing
        
        # display iteration stats
        print(f"Step {step_count.value}: Adopted={adopted}, Number Deployed={len(model_ref.value.tech_agent.deployed_agents)+1}, Banned={banned}, Collapsed={collapsed}, Avg Wellbeing={avg_wellbeing:.1f}, Tech Dominance={model_ref.value.tech_agent.tech_dominance:.1f}")  # Debug info


@solara.component
def Page():
    solara.Title("Digital Colonialism Simulator")

    # UI state
    num_agents = solara.use_reactive(50)
    implementation_cost = solara.use_reactive(5.0)
    cultural_fit = solara.use_reactive(0.8)
    deployment_policy = solara.use_reactive("random")
    tech_dominance = solara.use_reactive(3.0)

    # Sidebar controls
    with solara.Sidebar():
        solara.Markdown("## Model Controls")
        solara.IntSlider("Number of Receiving Agents", value=num_agents, min=10, max=200)
        solara.FloatSlider("Implementation Cost", value=implementation_cost, min=1.0, max=10.0)
        solara.FloatSlider("Cultural Fit", value=cultural_fit, min=0.1, max=1.0)
        solara.FloatSlider("Tech Dominance", value=tech_dominance, min=1.0, max=5.0)
        solara.Select("Deployment Policy", value=deployment_policy, values=["all", "random", "filtered"])

    # Create model key for memoization
    model_key = f"{num_agents.value}-{implementation_cost.value}-{cultural_fit.value}-{deployment_policy.value}-{tech_dominance.value}"

    # Function to create model
    def create_model():
        step_count.value = 0
        adopted_over_time.value = []
        banned_over_time.value = []
        collapsed_over_time.value = []
        wellbeing_over_time.value = []
        return DigitalColonialismModel(
            num_receiving_agents=num_agents.value,
            implementation_cost=implementation_cost.value,
            cultural_fit=cultural_fit.value,
            deployment_policy=deployment_policy.value,
            tech_dominance=tech_dominance.value
        )

    # Memoized model creation
    model = solara.use_memo(create_model, dependencies=[model_key])
    model_ref.set(model)

    # Long-term burst function for long-term effect oberservations
    def run_burst():
        """Run 50 steps for longer term results"""
        for _ in range(50):
            step_model()

    def reset_model():
        step_count.value = 0
        adopted_over_time.value = []
        banned_over_time.value = []
        collapsed_over_time.value = []
        wellbeing_over_time.value = []
        new_model = DigitalColonialismModel(
            num_receiving_agents=num_agents.value,
            implementation_cost=implementation_cost.value,
            cultural_fit=cultural_fit.value,
            deployment_policy=deployment_policy.value,
            tech_dominance=tech_dominance.value
        )
        model_ref.set(new_model)

    # Control buttons for speed
    with solara.Row():
        solara.Button("Step 1x", on_click=step_model)
        solara.Button("Step 10x", on_click=lambda: [step_model() for _ in range(10)])
        solara.Button("Run 50x", on_click=run_burst)
        solara.Button("Reset", on_click=reset_model)

    # Display components
    with solara.Column():
        NetworkPlot()
        with solara.Row():
            TimeSeriesChart()
            WellbeingChart()


@solara.component
def NetworkPlot():
    if not model_ref.value or not hasattr(model_ref.value, 'network'):
        solara.Markdown("*Network plot will appear here*")
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    
    try:
        G = model_ref.value.network
        pos = nx.spring_layout(G, seed=42)

        agent_colors = []
        for node in G.nodes():
            # Find the corresponding agent
            agent = None
            for a in model_ref.value.receiving_agents:
                if a.unique_id == node:
                    agent = a
                    break
            '''
            collapsed node = black
            adopted node = green
            banned node = red
            not adopted node = blue
            '''
            if agent:
                if getattr(agent, 'collapsed', False):
                    agent_colors.append("black")
                elif getattr(agent, 'banned', False):
                    agent_colors.append("red")
                elif getattr(agent, 'adopted', False):
                    agent_colors.append("green")
                else:
                    agent_colors.append("lightblue")
            else:
                agent_colors.append("gray")

        nx.draw(G, pos, node_color=agent_colors, with_labels=True, 
                node_size=300, ax=ax, edge_color='lightgray', font_size=8, font_weight='bold')
        
        # Show current tech dominance in title
        tech_dom = model_ref.value.tech_agent.tech_dominance if hasattr(model_ref.value, 'tech_agent') else 'N/A'
        ax.set_title(f"Network at Step {step_count.value} (Tech Dominance: {tech_dom:.1f})")
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='lightblue', label='Not Adopted'),
            Patch(facecolor='green', label='Adopted'),
            Patch(facecolor='red', label='Banned'),
            Patch(facecolor='black', label='Collapsed')
        ]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
    except Exception as e:
        ax.text(0.5, 0.5, f"Network visualization error: {str(e)}", 
                transform=ax.transAxes, ha='center', va='center')
    
    plt.tight_layout()
    solara.FigureMatplotlib(fig)


@solara.component
def WellbeingChart():
    fig, ax = plt.subplots(figsize=(8, 4))
    
    wellbeing_data = wellbeing_over_time.value
    
    if len(wellbeing_data) > 0:
        steps = list(range(len(wellbeing_data)))
        ax.plot(steps, wellbeing_data, label="Average Wellbeing", color="blue", linewidth=3)
        
        # Add reference lines
        ax.axhline(y=50, color='orange', linestyle='--', alpha=0.7, label='Ban Threshold')
        ax.axhline(y=25, color='red', linestyle='--', alpha=0.7, label='Collapse Threshold')
        
        ax.set_title(f"Community Wellbeing Over Time (Step {step_count.value})")
        ax.set_xlabel("Simulation Step")
        ax.set_ylabel("Average Wellbeing")
        ax.set_ylim(0, 100)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Show current wellbeing value
        if wellbeing_data:
            current_wellbeing = wellbeing_data[-1]
            ax.text(0.02, 0.98, f"Current: {current_wellbeing:.1f}", 
                   transform=ax.transAxes, va='top', ha='left',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    else:
        ax.text(0.5, 0.5, "Run the simulation to see wellbeing data", 
                transform=ax.transAxes, ha='center', va='center', fontsize=12)
        ax.set_title("Community Wellbeing Over Time")
        ax.set_xlabel("Simulation Step")
        ax.set_ylabel("Average Wellbeing")
        ax.set_ylim(0, 100)
    
    solara.FigureMatplotlib(fig)


@solara.component
def TimeSeriesChart():
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Ensure all arrays have the same length to avoid plotting errors
    adopted_data = adopted_over_time.value
    banned_data = banned_over_time.value
    collapsed_data = collapsed_over_time.value
    
    if len(adopted_data) > 0 and len(banned_data) > 0 and len(collapsed_data) > 0:
        min_length = min(len(adopted_data), len(banned_data), len(collapsed_data))
        steps = list(range(min_length))
        
        ax.plot(steps, adopted_data[:min_length], label="Adopted", color="green", linewidth=2, marker='o')
        ax.plot(steps, banned_data[:min_length], label="Banned", color="red", linewidth=2, marker='s')
        ax.plot(steps, collapsed_data[:min_length], label="Collapsed", color="black", linewidth=2, marker='^')
        
        ax.set_title(f"Technology Adoption Over Time (Step {step_count.value})")
        ax.set_xlabel("Simulation Step")
        ax.set_ylabel("Number of Agents")
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, "Run the simulation to see data", 
                transform=ax.transAxes, ha='center', va='center', fontsize=12)
        ax.set_title("Technology Adoption Over Time")
        ax.set_xlabel("Simulation Step")
        ax.set_ylabel("Number of Agents")
    
    solara.FigureMatplotlib(fig)
