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
step_details = solara.Reactive([])


def step_model():
    if model_ref.value:
        # Store pre-step state for comparison
        pre_step_states = {}
        for agent in model_ref.value.agents:
            if isinstance(agent, ReceivingAgent):
                pre_step_states[agent.unique_id] = {
                    'adopted': agent.adopted,
                    'banned': agent.banned,
                    'collapsed': agent.collapsed,
                    'wellbeing': agent.wellbeing,
                    'was_targeted': agent.was_targeted
                }
        
        # Execute the step
        model_ref.value.step()
        step_count.value += 1
        
        # Analyze what changed and why
        changes = []
        for agent in model_ref.value.agents:
            if isinstance(agent, ReceivingAgent):
                pre = pre_step_states[agent.unique_id]
                if (agent.adopted != pre['adopted'] or 
                    agent.banned != pre['banned'] or 
                    agent.collapsed != pre['collapsed']):
                    
                    change_type = ""
                    reason = ""
                    if agent.adopted and not pre['adopted']:
                        change_type = "ADOPTED"
                        # Simple adoption factors
                        utility = agent.calculate_perceived_utility()
                        peer_inf = agent.calculate_peer_influence()
                        score = utility + peer_inf - agent.cultural_resilience
                        reason = f"score {score:.2f} > threshold {agent.adoption_threshold:.2f}"
                    elif agent.banned and not pre['banned']:
                        if pre['adopted']:
                            change_type = "BANNED (post-adoption)"
                            reason = f"personal wellbeing declined"
                        else:
                            change_type = "BANNED (network-based)"
                            reason = f"observed neighbor suffering"
                    elif agent.collapsed and not pre['collapsed']:
                        change_type = "COLLAPSED"
                        reason = f"wellbeing or infrastructure too low"
                    
                    changes.append({
                        'agent_id': agent.unique_id,
                        'change': change_type,
                        'wellbeing': f"{pre['wellbeing']:.1f} → {agent.wellbeing:.1f}",
                        'infrastructure': f"{agent.infrastructure_strength:.1f}",
                        'was_targeted': agent.was_targeted,
                        'reason': reason
                    })
        
        # Count current states
        adopted = sum(1 for a in model_ref.value.agents if isinstance(a, ReceivingAgent) and a.adopted)
        banned = sum(1 for a in model_ref.value.agents if isinstance(a, ReceivingAgent) and a.banned)
        collapsed = sum(1 for a in model_ref.value.agents if isinstance(a, ReceivingAgent) and a.collapsed)
        
        # Update tracking arrays - ensure all three are updated together
        current_adopted = list(adopted_over_time.value)
        current_banned = list(banned_over_time.value)
        current_collapsed = list(collapsed_over_time.value)
        
        current_adopted.append(adopted)
        current_banned.append(banned)
        current_collapsed.append(collapsed)
        
        # Update all three simultaneously to prevent length mismatches
        adopted_over_time.value = current_adopted
        banned_over_time.value = current_banned  
        collapsed_over_time.value = current_collapsed
        
        print(f"Step {step_count.value}: Adopted={adopted}, Banned={banned}, Collapsed={collapsed}")  # Debug info
        
        # Store step details
        step_info = {
            'step': step_count.value,
            'adopted': adopted,
            'banned': banned,
            'collapsed': collapsed,
            'changes': changes,
            'tech_dominance': model_ref.value.tech_agent.tech_dominance
        }
        
        current_details = list(step_details.value)
        current_details.append(step_info)
        step_details.value = current_details[-10:]  # Keep last 10 steps


@solara.component
def Page():
    solara.Title("Digital Colonialism Simulator - Diagnostic Mode")

    # UI state
    num_agents = solara.use_reactive(20)  # Smaller for easier tracking
    implementation_cost = solara.use_reactive(5.0)
    cultural_fit = solara.use_reactive(0.8)
    deployment_policy = solara.use_reactive("random")

    # Sidebar controls
    with solara.Sidebar():
        solara.Markdown("## Model Controls")
        solara.IntSlider("Number of Receiving Agents", value=num_agents, min=5, max=50)
        solara.FloatSlider("Implementation Cost", value=implementation_cost, min=1.0, max=10.0)
        solara.FloatSlider("Cultural Fit", value=cultural_fit, min=0.1, max=1.0)
        solara.Select("Deployment Policy", value=deployment_policy, values=["all", "random", "filtered"])

    # Create model key for memoization
    model_key = f"{num_agents.value}-{implementation_cost.value}-{cultural_fit.value}-{deployment_policy.value}"

    # Function to create model
    def create_model():
        step_count.value = 0
        adopted_over_time.value = []
        banned_over_time.value = []
        collapsed_over_time.value = []
        step_details.value = []
        return DigitalColonialismModel(
            num_receiving_agents=num_agents.value,
            implementation_cost=implementation_cost.value,
            cultural_fit=cultural_fit.value,
            deployment_policy=deployment_policy.value
        )

    # Memoized model creation
    model = solara.use_memo(create_model, dependencies=[model_key])
    model_ref.set(model)

    def reset_model():
        step_count.value = 0
        adopted_over_time.value = []
        banned_over_time.value = []
        collapsed_over_time.value = []
        step_details.value = []
        new_model = DigitalColonialismModel(
            num_receiving_agents=num_agents.value,
            implementation_cost=implementation_cost.value,
            cultural_fit=cultural_fit.value,
            deployment_policy=deployment_policy.value
        )
        model_ref.set(new_model)

    # Control buttons
    with solara.Row():
        solara.Button("Step Once", on_click=step_model)
        solara.Button("Step 5x", on_click=lambda: [step_model() for _ in range(5)])
        solara.Button("Reset", on_click=reset_model)

    # Main display
    with solara.Columns([1, 1]):
        with solara.Column():
            NetworkPlot()
            TimeSeriesChart()
        with solara.Column():
            StepDetails()
            AgentStatus()


@solara.component
def NetworkPlot():
    if not model_ref.value or not hasattr(model_ref.value, 'network'):
        solara.Markdown("*Network plot will appear here*")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    
    try:
        G = model_ref.value.network
        pos = nx.spring_layout(G, seed=42)

        agent_colors = []
        for node in G.nodes():
            agent = None
            for a in model_ref.value.receiving_agents:
                if a.unique_id == node:
                    agent = a
                    break
            
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
                node_size=300, ax=ax, edge_color='lightgray', font_size=8)
        ax.set_title(f"Network at Step {step_count.value}")
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='lightblue', label='Not Adopted'),
            Patch(facecolor='green', label='Adopted'),
            Patch(facecolor='red', label='Banned'),
            Patch(facecolor='black', label='Collapsed')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
    except Exception as e:
        ax.text(0.5, 0.5, f"Network error: {str(e)}", 
                transform=ax.transAxes, ha='center', va='center')
    
    solara.FigureMatplotlib(fig)


@solara.component
def TimeSeriesChart():
    fig, ax = plt.subplots(figsize=(8, 4))
    
    adopted_data = adopted_over_time.value
    banned_data = banned_over_time.value
    collapsed_data = collapsed_over_time.value
    
    # Ensure all arrays have the same length to avoid plotting errors
    if len(adopted_data) > 0 and len(banned_data) > 0 and len(collapsed_data) > 0:
        min_length = min(len(adopted_data), len(banned_data), len(collapsed_data))
        steps = list(range(min_length))
        
        ax.plot(steps, adopted_data[:min_length], label="Adopted", color="green", linewidth=2, marker='o')
        ax.plot(steps, banned_data[:min_length], label="Banned", color="red", linewidth=2, marker='s')
        ax.plot(steps, collapsed_data[:min_length], label="Collapsed", color="black", linewidth=2, marker='^')
        
        ax.set_title(f"Agent States Over Time (Step {step_count.value})")
        ax.set_xlabel("Simulation Step")
        ax.set_ylabel("Number of Agents")
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, "Run simulation to see data", 
                transform=ax.transAxes, ha='center', va='center')
        ax.set_title("Agent States Over Time")
        ax.set_xlabel("Simulation Step")
        ax.set_ylabel("Number of Agents")
    
    solara.FigureMatplotlib(fig)


@solara.component
def StepDetails():
    solara.Markdown("## Recent Step Details")
    
    if len(step_details.value) == 0:
        solara.Markdown("*No steps taken yet*")
        return
    
    # Show last few steps
    for step_info in reversed(step_details.value[-3:]):
        with solara.Card(f"Step {step_info['step']}", margin=1):
            solara.Markdown(f"**Adopted:** {step_info['adopted']} | **Banned:** {step_info['banned']} | **Collapsed:** {step_info['collapsed']}")
            solara.Markdown(f"**Tech Dominance:** {step_info['tech_dominance']:.1f}")
            
            if step_info['changes']:
                solara.Markdown("**Changes:**")
                for change in step_info['changes']:
                    solara.Markdown(f"- Agent {change['agent_id']}: {change['change']}")
                    if change['reason']:
                        solara.Markdown(f"  *{change['reason']}*")
                    solara.Markdown(f"  Wellbeing: {change['wellbeing']}, Infrastructure: {change['infrastructure']}, Targeted: {change['was_targeted']}")
            else:
                solara.Markdown("*No state changes*")


@solara.component
def AgentStatus():
    solara.Markdown("## Current Agent Status")
    
    if not model_ref.value:
        solara.Markdown("*No model loaded*")
        return
    
    # Create a summary table
    agent_data = []
    for agent in model_ref.value.receiving_agents:
        # Get basic neighbor info
        neighbor_info = "No neighbors"
        if hasattr(model_ref.value, 'network') and agent.unique_id in model_ref.value.network:
            neighbors_ids = list(model_ref.value.network.neighbors(agent.unique_id))
            neighbors = []
            for neighbor_id in neighbors_ids:
                for n in model_ref.value.receiving_agents:
                    if n.unique_id == neighbor_id:
                        neighbors.append(n)
                        break
            
            if neighbors:
                adopted_neighbors = [n for n in neighbors if n.adopted and not n.banned]
                banned_neighbors = [n for n in neighbors if n.banned]
                neighbor_info = f"{len(neighbors)} total: {len(adopted_neighbors)} adopted, {len(banned_neighbors)} banned"
        
        agent_data.append({
            'ID': agent.unique_id,
            'State': ('Collapsed' if agent.collapsed else 
                     'Banned' if agent.banned else 
                     'Adopted' if agent.adopted else 'None'),
            'Wellbeing': f"{agent.wellbeing:.1f}",
            'Infrastructure': f"{agent.infrastructure_strength:.1f}",
            'Cultural Resistance': f"{agent.cultural_resilience:.2f}",
            'Digital Access': f"{agent.digital_access_score:.2f}",
            'Neighbors': neighbor_info,
            'Targeted': agent.was_targeted
        })
    
    df = pd.DataFrame(agent_data)
    solara.DataFrame(df, items_per_page=10)