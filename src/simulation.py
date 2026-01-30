import yaml
import os
import sys
import logging
import datetime
from agent import Agent
from environments import get_environment_by_name

class Simulation:
    def __init__(self, settings_path: str):
        # Load Settings
        with open(settings_path, 'r') as file:
            settings = yaml.safe_load(file)

        self.name = settings.get('name', 'DefaultSim')
        self.context = settings.get('context', 'Default context.')
        self.agents = []
        self.steps = settings.get('steps', 3)
        self.output_dir = os.path.join(".", "outputs", self.name)
        
        # Setup Logging
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"simulation_{timestamp}.log"
        log_path = os.path.join(self.output_dir, log_filename)

        logging.getLogger("httpx").setLevel(logging.WARNING)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.handlers = []

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(stream_handler)

        file_handler = logging.FileHandler(log_path, 'w', 'utf-8')
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(file_handler)

        self.log_path = log_path

        # Load Environment
        env_path = os.path.join(os.path.dirname(settings_path), 'environments.yaml')
        with open(env_path, 'r') as file:
            all_environments = yaml.safe_load(file)
        
        env_config = all_environments.get(self.name)
        if not env_config:
            raise ValueError(f"Environment '{self.name}' not found in environments.yaml")
        
        self.environment = get_environment_by_name(self.name, env_config)

        # Load Agents
        self.load_agents(settings, env_config)
        
    def load_agents(self, settings, env_config):
        agents_param = settings.get('agents', [])
        agent_ids = [agent['id'] for agent in agents_param]
        
        base_context = self.context + f" You are participating in the '{self.name}' task."
        env_context = self.environment.get_context()
        
        for agent_param in agents_param:
            
            agent_id = agent_param['id']
            agent_model = agent_param['model']
            
            logging.info(f"Loading agent: {agent_model} as {agent_id}")
            
            agent_context = " Here is a list of the existing agents: " + ", ".join(agent_ids) + ". " + "You are agent " + agent_param['id'] + ". "
            
            private_info = ""
            for info in env_config.get('initial_info', []):
                if info.get('target_agent_id') == agent_id:
                    private_info = f"Private Information for you, you can share it with other agents: {info.get('info')}"
                    break

            full_context = f"{base_context}\n{env_context}\n{agent_context}\n{private_info}"
            
            states = agent_param.get('states', {})
            
            if not states:
                states_string = ""
            else:
                states_string = f"Your initial states are: " + ", ".join([f"{key}: {value}" for key, value in states.items()]) + "."
            
            # print("\n\n Agent State: ", states_string)
            # logging.info(f"Agent {agent_id} has the following context: {full_context}")
            
            self.agents.append(Agent(
                model=agent_model,
                id=agent_id,
                personality=agent_param['personality'],
                state=states_string,
                context=full_context,
                nb_actions=env_config.get('nb_actions', 1)
                ))
    
    def _get_agent_by_id(self, agent_id):
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def handle_agent_action(self, agent: Agent, action_list_json: dict):
        # print("\n\n Action JSON: ", action_list_json)

        for act in action_list_json:
            if self.environment.is_finished:
                logging.info("Environment finished; skipping remaining actions")
                break

            action = act.get('action')
            if action == 'message':
                target_ids = act.get('target_agent_ids')
                if not target_ids:
                    # Fallback for backward compatibility or hallucination
                    single_target = act.get('target_agent_id')
                    if single_target:
                        target_ids = [single_target]
                    else:
                        target_ids = []

                message = act.get('message')
                
                for target_id in target_ids:
                    target_agent = self._get_agent_by_id(target_id)

                    if target_agent:
                        logging.info(f"Agent {agent.id} -> {target_id}: {message}")
                        target_agent.messages.append({'role': 'user', 'content': f"You received a message from {agent.id}: {message}"})
                    else:
                        logging.info(f"Agent {agent.id} tried to message non-existent agent {target_id}")

            elif action == 'think':
                thought = act.get('thought')
                logging.info(f"Agent {agent.id} thinks: {thought}")

            elif action == 'interact_env':
                # Pass the whole action object to the environment handler
                self.environment.perform_action(agent, act)

            else:
                # Fallback: Treat unknown actions as environment interactions (e.g. "vote")
                logging.info(f"Agent {agent.id} used shorthand action '{action}'. converting to interact_env.")
                
                # Construct a compatible action object
                fallback_action = {
                    'action': 'interact_env',
                    'env_action': action,
                    'params': act.get('params', act) # Use existing params or the whole dict
                }
                self.environment.perform_action(agent, fallback_action)

    def run_simulation(self):
        try:
            starting_time = datetime.datetime.now()
            logging.info("\n--- Starting Simulation ---")
            final_step = 0
            for i in range(self.steps):
                if self.environment.is_finished:
                    logging.info("\n--- Environment signals simulation end ---")
                    break
                final_step = i

                starting_step = datetime.datetime.now()
                logging.info(f"\n--- Step {i+1}/{self.steps} ---")
                
                for agent in self.agents:
                    logging.info(f"\nAgent {agent.id} :")
                    
                    prompt = self.environment.get_actions() + " Based on the situation, what is your next action? (think, message, or interact_env)"
                    action_list_json = agent.generate(prompt)
                    self.handle_agent_action(agent, action_list_json)
                    
                    self.environment.env_step_turn()
                
                self.environment.env_step()
                    
                ending_step = datetime.datetime.now()
                logging.info(f"\nStep duration: {ending_step - starting_step}")
                
            ending_time = datetime.datetime.now()
            
            logging.info("\n--- Simulation Finished ---")
            logging.info(f"Simulation duration: {ending_time - starting_time}")
            
            logging.info(f"Final Step: {final_step + 1}/{self.steps}")
        
        finally:
            logging.shutdown()
            print(f"Simulation log saved to {self.log_path}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        settings_file_path = sys.argv[1]
        sim = Simulation(settings_file_path)
        sim.run_simulation()
    else:
        print("Usage: python simulation.py path_to_yaml")
        sys.exit(1)