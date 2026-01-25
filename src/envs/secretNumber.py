import random
import logging
from .baseEnvironment import BaseEnvironment


class SecretNumberEnvironment(BaseEnvironment):
    """Environment for the 'Find the Secret Number' mission."""
    def __init__(self, description, rules):
        super().__init__(description, rules)
        # Choose a random even number greater than 80
        possible_numbers = [n for n in range(81, 100) if n % 2 == 0]
        self.secret_number = random.choice(possible_numbers)
        logging.info(f"Secret number chosen by environment: {self.secret_number}")

    def perform_action(self, agent, action_details):
        # super().perform_action(agent, action_details)
        #logging.info(f"Environment received action from {agent.id}: {action_details}")
        
        env_action = action_details.get('env_action')
        if env_action == 'guess':
            
            guessed_number = action_details.get('params', {}).get('number')
            
            if guessed_number is not None:
                logging.info(f"Agent {agent.id} guesses the number: {guessed_number}")
                if int(guessed_number) == self.secret_number:
                    logging.info(f"SUCCESS! Agent {agent.id} found the secret number {self.secret_number}!")
                    self.is_finished = True
                else:
                    higher = guessed_number < self.secret_number
                    if higher:
                        self.actions.append({'agent_id': agent.id, 'action': action_details, 'result': 'too low'})
                        logging.info(f"FAIL! The guess '{guessed_number}' was too low.")
                    else:
                        self.actions.append({'agent_id': agent.id, 'action': action_details, 'result': 'too high'})
                        logging.info(f"FAIL! The guess '{guessed_number}' was too high.")
            else:
                logging.info(f"Agent {agent.id} attempted to guess but provided no number.")
        
        else:
            logging.info(f"Agent {agent.id} performed an action '{env_action}' that the environment does not handle.")
