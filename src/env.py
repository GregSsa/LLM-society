import yaml
import os
import sys
import logging
import datetime
from agent import Agent
# from metrics import compute_metrics
# from viz import plot_opinions_time_series, scatter_opinion_valence

class Environment:
    def __init__(self, settings_path: str):
        with open(settings_path, 'r') as file:
            settings = yaml.safe_load(file)

        self.name = settings.get('name', 'DefaultSim')
        self.contexte = settings.get('context', 'Default context.')
        self.agents = []
        self.steps = settings.get('steps', 3)
        self.output_dir = os.path.join("..", "outputs", self.name)
        
        # Create output directory and set up logging
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"simulation_{timestamp}.log"
        log_path = os.path.join(self.output_dir, log_filename)

        # Silence noisy loggers
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("ollama").setLevel(logging.WARNING)

        # Configure logging to output to both console and file
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.handlers = [] # Clear existing handlers

        # Console handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(stream_handler)

        # File handler
        file_handler = logging.FileHandler(log_path, 'w', 'utf-8')
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(file_handler)

        self.log_path = log_path
        # Load agents after setting up logging
        self.load_agents(settings)
        
    def load_agents(self, settings):
        agents_param = settings.get('agents', [])
        
        agent_ids = [agent['id'] for agent in agents_param]
        full_context = self.contexte + " Here a list of the existing agents : " + ", ".join(agent_ids) + ". "
        
        for agent_param in agents_param:
            
            full_context_perso = full_context + "You are agent " + agent_param['id'] + ". "
            logging.info(f"Loading agent: {agent_param['id']}")
            
            state = "opinion: " + str(agent_param.get('opinion', 0.0)) + \
                    ", valence: " + str(agent_param.get('valence', 0.0)) + \
                    ", trust: " + str(agent_param.get('trust', 0.0)) + \
                    ", openness: " + str(agent_param.get('openness', 0.0)) + \
                    ", sociability: " + str(agent_param.get('sociability', 0.0))
            print("TEST context", full_context_perso)
            
            self.agents.append(Agent(
                model=agent_param['model'],
                id=agent_param['id'],
                personality=agent_param['personality'],
                state=state,
                contexte=full_context_perso,
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
                logging.info(f"Agent {agent.id} -> {target_id}: {message}")
                # Add message to target agent's history for context in their next turn
                target_agent.messages.append({'role': 'user', 'content': f"You received a message from {agent.id}: {message}"})
            else:
                logging.info(f"Agent {agent.id} tried to message non-existent agent {target_id}")

        elif action == 'think':
            thought = action_json.get('thought')
            logging.info(f"Agent {agent.id} thinks: {thought}")
        else:
            logging.info(f"Agent {agent.id} produced an invalid action: {action}")

    def run_simulation(self):
        try:
            starting_time = datetime.datetime.now()
            logging.info("\n--- Starting Simulation ---")
                
            for i in range(self.steps):
                starting_step = datetime.datetime.now()
                
                logging.info(f"\n--- Step {i+1}/{self.steps} ---")
                
                # keep same order for each step for now
                for agent in self.agents:
                    prompt = "What is your next action? (you can 'think' or 'message' another agent)"
                    action_json = agent.generate(prompt)

                    self.handle_agent_action(agent, action_json)
                    
                ending_step = datetime.datetime.now()
                logging.info(f"\nStep duration: {ending_step - starting_step}")
                
            ending_time = datetime.datetime.now()
            
            logging.info("\n--- Simulation Finished ---")
            logging.info(f"Simulation duration: {ending_time - starting_time}")
        
        finally:
            # Clean up logging
            logging.shutdown()
            # Print final message to original stdout
            print(f"Simulation log saved to {self.log_path}")

        # metrics = compute_metrics(self.agents)
        # plot_opinions_time_series(metrics, outpath=self.output_dir)
        # scatter_opinion_valence(self.agents, outpath=self.output_dir)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        settings_file_path = sys.argv[1]
        env = Environment(settings_file_path)
        env.run_simulation()
    else:
        print("Usage: python env.py path_to_yaml")
        sys.exit(1)