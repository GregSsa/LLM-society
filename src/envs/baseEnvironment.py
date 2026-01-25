import logging

class BaseEnvironment:
    """Base class for all simulation environments."""
    def __init__(self, description, rules):
        self.description = description
        self.rules = rules
        self.actions = []
        self.is_finished = False
        self.step = 0
        self.turn = 0

    def perform_action(self, agent, action_details):
        """Processes an action from an agent."""
        self.actions.append({'agent_id': agent.id, 'action': action_details})
        logging.info(f"Environment received action from {agent.id}: {action_details}")

    def get_actions(self):
        return f"Environment Received Action: {self.actions}"
    
    def get_prompt(self):
        return self.get_actions()
    
    def get_context(self):
        return f"Environment Description: {self.description}\nRules: {self.rules}\nEach agent has access to the action history performed on the environment."

    def env_step(self):
        # Advance the environment by one step. Called once per global step.
        self.step += 1
    
    def env_step_turn(self):
        # This function is called at each agent turn.
        self.turn += 1
        
    def log(self, message: str):
        # Log a message in the environment log
        self.actions.append(message)
        logging.info(message)
        
    def log_private(self, agent, action_details: dict, result: str):
        # Give feedback on action result of a specific agent (private)
        log_entry = {'agent_id': agent.id, 'action': action_details, 'result': result}
        agent.messages.append({'role': 'system', 'content': result})
        
        logging.info(f"Environment Action Result for {agent.id}: {log_entry}")
