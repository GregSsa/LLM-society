import ollama
import json
import logging


class Agent:
    def __init__(self,
        model: str = 'phi',
        id: str = "",
        state: str = "",  # pas utilisé pour l'instant
        personality: str = "You are a helpful assistant.",  # pas utilisé pour l'instant
        contexte: str = "You are an AI model designed to interact with other agents in a society simulation.",
        environment = None,  # pas utilisé pour l'instant
        nb_actions: int = 1
        ):
        # Attributs de l'agent
        self.model = model
        self.id = id
        self.state = state
        self.personality = personality
        self.contexte = contexte
        self.environment = environment
        self.nb_actions = nb_actions

        # Prompt système : demande un objet JSON ou une liste d'objets JSON
        system_prompt = f"""{self.contexte}
You must communicate with other agents by generating JSON actions.
The response MUST be a JSON array of action objects.
Each action object must have one of the following structures:
{{
  "action": "message",
  "target_agent_id": "<ID of the agent to send the message to>",
  "message": "<Your message content>"
}}
OR
{{
  "action": "think",
  "thought": "<Your internal thought if you don't want to speak>"
}}
OR
{{
  "action": "interact_env",
  "env_action": "<Action name>",
  "params": {{}}
}}
You must use 2 action(s) each turn. 
Examples of a Response with 3 actions:
{{ "generate": [
  <action>,
  <action>,
  <action>
]}}
"""
        # print(f"\nAgent {self.id} System Prompt: ", system_prompt)
        self.messages = [{'role': 'system', 'content': system_prompt}]

    def generate(self, prompt: str):
        self.messages.append({'role': 'user', 'content': prompt})

        response = ollama.chat(
            model=self.model,
            messages=self.messages,
            format='json',
        )

        assistant_response = response['message']['content']
        # print(f"\n\n Agent {self.id} Actions: ", assistant_response)
        
        self.messages.append({'role': 'assistant', 'content': assistant_response})

        try:
            parsed = json.loads(assistant_response)
        except json.JSONDecodeError:
            logging.warning(f"Agent {self.id} produced invalid JSON: {assistant_response}")
            return [{"action": "think", "thought": "I failed to produce valid JSON."}]

        action_list = parsed.get("generate")

        if action_list is None:
            logging.warning(f"Agent {self.id} returned JSON of unsupported type: {type(parsed)}")
            return [{"action": "think", "thought": "Invalid JSON structure; expected object or list."}]

        # Enforce the per-turn action limit
        if len(action_list) > self.nb_actions:
            logging.warning(f"Agent {self.id} returned {len(action_list)} actions, truncating to {self.nb_actions} allowed ones.")
            action_list = action_list[:self.nb_actions]
        return action_list