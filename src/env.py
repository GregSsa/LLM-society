

import yaml
import os
from agent import Agent
# from metrics import compute_metrics
# from viz import plot_opinions_time_series, scatter_opinion_valence

class Environment:
    def __init__(self, name: str):
        self.name = name
        self.contexte = "You are an AI model designed to interact with other agents in a society simulation. The other agents are: B"
        self.agents = []
        self.load_agents()
        self.steps = 1
        self.outpiut_dir = "../outputs/" + name
        
    def load_agents(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(current_dir, '..', 'settings.yaml')
        
        with open(settings_path, 'r') as file:
            settings = yaml.safe_load(file)
            self.steps = settings['steps']
            agents_param = settings['agents']
            
            agent_ids = [agent['id'] for agent in agents_param]
            self.contexte += ", ".join(agent_ids)

            for agent_param in agents_param:
                print(f"Loading agent: {agent_param['id']}")
                state = "opinion: " + str(agent_param['opinion']) + \
                        ", valence: " + str(agent_param['valence']) + \
                        ", trust: " + str(agent_param['trust']) + \
                        ", openness: " + str(agent_param['openness']) + \
                        ", sociability: " + str(agent_param['sociability'])
                self.agents.append(Agent(
                    model=agent_param['model'],
                    id=agent_param['id'],
                    personality=agent_param['personality'],
                    state=state,
                    contexte=self.contexte,
                    ))
    
    def _get_agent_by_id(self, agent_id):
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def handle_agent_action(self, agent: Agent, action_json: dict):
        action = action_json.get('action')
        if action == 'message':
            target_id = action_json.get('target_agent_id')
            message = action_json.get('message')
            target_agent = self._get_agent_by_id(target_id)
            
            if target_agent:
                print(f"Agent {agent.id} -> {target_id}: {message}")
                # Add message to target agent's history for context in their next turn
                target_agent.messages.append({'role': 'user', 'content': f"You received a message from {agent.id}: {message}"})
            else:
                print(f"Agent {agent.id} tried to message non-existent agent {target_id}")

        elif action == 'think':
            thought = action_json.get('thought')
            print(f"Agent {agent.id} thinks: {thought}")
        else:
            print(f"Agent {agent.id} produced an invalid action: {action}")

    def run_simulation(self):
        print("\n--- Starting Simulation ---")
            
        for i in range(self.steps):
            print(f"\n--- Step {i+1}/{self.steps} ---")
            
            # keep same order for each step for now
            for agent in self.agents:
                prompt = "What is your next action? (you can 'think' or 'message' another agent)"
                action_json = agent.generate(prompt)

                self.handle_agent_action(agent, action_json)
        
        print("\n--- Simulation Finished ---")
        
        # metrics = compute_metrics(self.agents)
        # plot_opinions_time_series(metrics, outpath=self.output_dir)
        # scatter_opinion_valence(self.agents, outpath=self.output_dir)

if __name__ == '__main__':
    env = Environment("SocietySim")
    env.run_simulation()