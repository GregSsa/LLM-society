import os
from openai import OpenAI
import json
import logging


class Agent:
    def __init__(self,
        model: str = 'gpt-5-nano',
        id: str = "",
        state: str = "",  # not used yet
        personality: str = "You are a helpful assistant.",  # not used yet
        context: str = "You are an AI model designed to interact with other agents in a society simulation.",
        environment = None,  # not used yet
        nb_actions: int = 1
        ):
        # Agent attributes
        self.model = model
        self.id = id
        self.state = state
        self.personality = personality
        self.context = context
        self.environment = environment
        self.nb_actions = nb_actions

        # Initialize OpenAI client
        # Ensure OPENAI_API_KEY is set in environment variables
        self.client = OpenAI()

        # Prompt système : demande un objet JSON ou une liste d'objets JSON
        system_prompt = f"""{self.context}
You must communicate with other agents by generating JSON actions.
The response MUST be a JSON array of action objects.
Each action object must have one of the following structures:
{{
  "action": "message",
  "target_agent_ids": ["<ID1>", "<ID2>"],
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
You must use a maximum of {self.nb_actions} action(s) per turn. 
Examples of a Response with 2 actions:
{{ "response": [
  <action>,
  <action>
]}}
"""
        # print(f"\nAgent {self.id} System Prompt: ", system_prompt)
        self.messages = [{'role': 'system', 'content': system_prompt}]

    def generate(self, prompt: str):
        self.messages.append({'role': 'user', 'content': prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            logging.error(f"Error calling OpenAI API for agent {self.id}: {e}")
            return [{"action": "think", "thought": "I failed to communicate with the AI model."}]

        assistant_response = response.choices[0].message.content
        # print(f"\n\n Agent {self.id} Actions: ", assistant_response)
        
        self.messages.append({'role': 'assistant', 'content': assistant_response})

        try:
            parsed = json.loads(assistant_response)
        except json.JSONDecodeError:
            logging.warning(f"Agent {self.id} produced invalid JSON: {assistant_response}")
            return [{"action": "think", "thought": "I failed to produce valid JSON."}]

        action_list = parsed.get("response")
        if action_list is None:
            logging.warning(f"Agent {self.id} returned JSON of unsupported type: {type(parsed)}")
            return [{"action": "think", "thought": "Invalid JSON structure; expected object or list."}]

        # Enforce the per-turn action limit
        if len(action_list) > self.nb_actions:
            logging.warning(f"Agent {self.id} returned {len(action_list)} actions, truncating to {self.nb_actions} allowed ones.")
            action_list = action_list[:self.nb_actions]
        return action_list