import random
import logging
from agent import Agent

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
        return f"Environment Description: {self.description}\nRules: {self.rules}\n Each agent have access to the action history perform on the environnement."

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
        
    def log_private(self, agent: Agent, action_details: dict, result: str):
        # Give feedback on action result of a specific agent (private)
        log_entry = {'agent_id': agent.id, 'action': action_details, 'result': result}
        agent.messages.append({'role': 'system', 'content': result})
        
        logging.info(f"Environment Action Result for {agent.id}: {log_entry}")
        
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

class LoupGarouEnvironment(BaseEnvironment):
    """Loup-Garou environment with 8 agents."""
    def __init__(self, description, rules, roles: dict):
        super().__init__(description, rules)
        self.roles = roles or {}
        self.alive = set(self.roles.keys())
        self.wolves = {aid for aid, r in self.roles.items() if r.lower().startswith('loup')}
        self.seer = next((aid for aid, r in self.roles.items() if r.lower().startswith('voyante')), None)
        self.witch = next((aid for aid, r in self.roles.items() if r.lower().startswith('sorci')), None)
        self.cupid = next((aid for aid, r in self.roles.items() if r.lower().startswith('cupid')), None)

        self.used_save = False
        self.used_poison = False
        self.couple = None  # tuple (a,b)

        # Night and day buffers
        self.night_kill_votes = {}   # target_id -> count (from wolves)
        self.pending_kill = None
        self.day_votes = {}          # agent_id -> target_id
        
        self.state = 'day'
        self.step_during_day = 4
        self.step_during_night = 2
        
        self._get_summary()


    def _get_summary(self):
        """Return a summary of the current state of the game."""
        logging.info("-------------------------")
        logging.info(f"Is it currently {self.state}")
        self.log( {
            'alive': len(list(self.alive)),
            'wolves': len(list(self.wolves)),
            'seer': 1 if self.seer in self.alive else 0,
            'witch': 1 if self.witch in self.alive else 0,
            'cupid': 1 if self.cupid in self.alive else 0,
            'used_save': 1 if self.used_save else 0,
            'used_poison': 1 if self.used_poison else 0,
            'state': self.state,
            'step_remaining_until_night': self.step_during_night - (self.step % self.step_during_night) if self.state == 'day' else 0,
            'step_remaining_until_day': self.step_during_day - (self.step % self.step_during_day) if self.state == 'night' else 0,
        })
        logging.info("-------------------------")

    def env_step(self):
        """Advance the environment by one step. Called once per global step."""
        super().env_step()
        # Alternate day and night based on step count
        total_cycle_steps = self.step_during_day + self.step_during_night
        cycle_position = self.step % total_cycle_steps
        if cycle_position < self.step_during_day:
            self.state = 'day'
        else:
            self.state = 'night'

        self._get_summary()
    
    def env_step_turn(self):
        """Called each agent turn."""
        super().env_step_turn()
        
    def _eliminate(self, target_id: str, cause: str):
        if target_id not in self.alive:
            return
        self.alive.remove(target_id)
        self.actions.append(f"Elimination: {target_id} ({self.roles.get(target_id, 'Unknown')}) due to {cause}.")
        logging.info(f"Elimination: {target_id} ({self.roles.get(target_id, 'Unknown')}) due to {cause}.")
        # Couple death chain
        if self.couple and target_id in self.couple:
            other = self.couple[0] if self.couple[1] == target_id else self.couple[1]
            if other in self.alive:
                self.alive.remove(other)
                self.actions.append(f"Elimination: {other} (partner of {target_id}) due to grief (couple rule).")
                logging.info(f"Elimination: {other} (partner of {target_id}) due to grief (couple rule).")

        self._check_win()

    def _resolve_night(self):
        if not self.night_kill_votes:
            return
        # pick most voted target by wolves
        target, _ = max(self.night_kill_votes.items(), key=lambda kv: kv[1])
        self.pending_kill = target
        # If not saved, eliminate
        if self.pending_kill and self.pending_kill in self.alive:
            self._eliminate(self.pending_kill, cause='wolves at night')
        # reset buffers
        self.night_kill_votes.clear()
        self.pending_kill = None

    def _resolve_day(self):
        if not self.day_votes:
            return
        # count votes -> target counts
        tally = {}
        for voter, tgt in self.day_votes.items():
            if voter in self.alive and tgt in self.alive:
                tally[tgt] = tally.get(tgt, 0) + 1
        if not tally:
            self.day_votes.clear()
            return
        # pick max; if tie, no elimination
        sorted_votes = sorted(tally.items(), key=lambda kv: kv[1], reverse=True)
        if len(sorted_votes) > 1 and sorted_votes[0][1] == sorted_votes[1][1]:
            self.actions.append("Day vote tie: nobody is eliminated.")
            logging.info("Day vote tie: nobody is eliminated.")
        else:
            target, _ = sorted_votes[0]
            self._eliminate(target, cause='village vote at day')
        self.day_votes.clear()

    def _check_win(self):
        alive_wolves = [a for a in self.alive if a in self.wolves]
        alive_villagers = [a for a in self.alive if a not in self.wolves]
        if not alive_wolves:
            self.log("Village wins: all werewolves are eliminated!")
            self.is_finished = True
        elif len(alive_wolves) >= len(alive_villagers):
            self.log("Werewolves win: they are in majority!")
            self.is_finished = True

    def get_context(self):
        base = super().get_context()
        roles_hint = ", ".join([f"{aid}:{role}" for aid, role in self.roles.items()])
        return base + f"\nKnown Roles (for environment reference): {roles_hint}"

    def get_prompt(self):
        day_left = self.step_during_day - (self.step % (self.step_during_day + self.step_during_night))
        if (self.state == 'night'):
            return f"It is currently day in the game. You have {day_left} steps of day left to inspect, discuss and vote. "
        return f"It is currently Night in the game."

    def perform_action(self, agent, action_details):
        if self.is_finished:
            return
        super().perform_action(agent, action_details)
        env_action = action_details.get('env_action')
        params = action_details.get('params', {}) or {}

        # Cupidon: only first use
        if env_action == 'propose_couple':
            if agent.id != self.cupid:
                self.log(f"{agent.id} attempted 'propose_couple' but is not Cupidon.")
                return
            if self.couple:
                self.log("Couple already defined; ignoring.")
                return
            a = params.get('a')
            b = params.get('b')
            if a in self.alive and b in self.alive and a != b:
                self.couple = (a, b)
                self.log(f"Couple formed between {a} and {b} by Cupidon {agent.id}.")
            else:
                self.log("Invalid couple proposal; ignored.")
            return

        # Night actions
        if env_action == 'kill':
            if self.state != 'night': # only log
                logging.info(f"{agent.id} attempted 'kill' but it is not night.")
                return
            if agent.id not in self.wolves:
                logging.info(f"{agent.id} attempted 'kill' but is not a Werewolf.")
                return
            target = params.get('target')
            if target in self.alive and target not in self.wolves:
                self.night_kill_votes[target] = self.night_kill_votes.get(target, 0) + 1
                # If all alive wolves voted, resolve immediately
                alive_wolves = len([a for a in self.alive if a in self.wolves])
                if sum(self.night_kill_votes.values()) >= alive_wolves:
                    # witch may save later; we resolve now unless saved
                    self._resolve_night()
            else:
                self.log("Invalid kill target; must be an alive non-wolf.")
            return

        if env_action == 'inspect':
            if agent.id != self.seer:
                self.log(f"{agent.id} attempted 'inspect' but is not the Seer.")
                return
            target = params.get('target')
            role = self.roles.get(target, 'Unknown')
            self.log(f"Voyante reveals role of {target}: {role} (to all logs).")
            return

        if env_action == 'save':
            if agent.id != self.witch or self.used_save:
                self.log(f"{agent.id} attempted 'save' but cannot (not witch or already used).")
                return
            # Cancel the last pending kill if any (simple model)
            if self.pending_kill and self.pending_kill in self.alive:
                self.log(f"Sorcière saves {self.pending_kill} from death.")
                self.pending_kill = None
            self.used_save = True
            return

        if env_action == 'poison':
            if agent.id != self.witch or self.used_poison:
                self.log(f"{agent.id} attempted 'poison' but cannot (not witch or already used).")
                return
            target = params.get('target')
            if target in self.alive:
                self._eliminate(target, cause='witch poison at night')
                self.used_poison = True
            else:
                self.log("Invalid poison target (not alive).")
            return

        # Day action
        if env_action == 'vote':
            target = params.get('target')
            if agent.id not in self.alive or target not in self.alive:
                self.log("Invalid vote (voter or target not alive).")
                return
            self.day_votes[agent.id] = target
            # If all alive have voted, resolve immediately
            if len(self.day_votes) >= len(self.alive):
                self._resolve_day()
            return

        self.log(f"Action '{env_action}' not recognized in LoupGarou environment.")

def get_environment_by_name(name, env_config):
    """Factory function to get an environment instance by name."""
    if name == 'secret_number_mission':
        return SecretNumberEnvironment(
            description=env_config['description'],
            rules=env_config['rules']
        )
    if name == 'loup_garou':
        return LoupGarouEnvironment(
            description=env_config.get('description', ''),
            rules=env_config.get('rules', ''),
            roles=env_config.get('roles', {})
        )

    return BaseEnvironment(
        description=env_config.get('description', 'No description.'),
        rules=env_config.get('rules', 'No rules.')
    )
