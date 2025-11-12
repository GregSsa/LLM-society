import ollama
import json

class Agent:
    def __init__(self,
        model = 'phi',
        id = "",
        state = "", # pas utilisé pour l'instant
        personality = "You are a helpful assistant.", # pas utilisé pour l'instant
        contexte="You are an AI model designed to interact with other agents in a society simulation.",
        environment = None, # pas utilisé pour l'instant
        nb_actions=1
        ):
        
        self.model = model
        self.id = id
        self.state = state
        self.personality = personality
        self.contexte = contexte
        self.environment = environment
        self.nb_actions = nb_actions
        
            # Your personality is: {self.personality}.
            # Your current state is: {self.state}.
            # Global environment info: {self.environment}.
        system_prompt = f"""{self.contexte}
            You must communicate with other agents by generating a JSON object.
            The JSON object must have the following structure:
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
            "env_action": <Action name>, "params": <Parameters for the action>
            }}
            You can only perform {self.nb_actions} action(s) per turn.
            """
        
        self.messages = [{'role': 'system', 'content': system_prompt}]
    
    def generate(self, prompt):
        self.messages.append({'role': 'user', 'content': prompt})
        
        #print("\n\n\n\nTEST ", self.messages)
        
        response = ollama.chat(
            model=self.model,
            messages=self.messages,
            format='json',
            )

        assistant_response = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': assistant_response})
        
        try:
            # Analyser la réponse JSON
            action_json = json.loads(assistant_response)
            return action_json
        except json.JSONDecodeError:
            # print(f"Agent {self.id} produced invalid JSON: {assistant_response}")
            return {"action": "think", "thought": "I failed to produce valid JSON."}