import ollama
import json

class Agent:
    def __init__(self,
        model = 'phi',
        id = "",
        state = "",
        personality = "You are a helpful assistant.",
        contexte="You are an AI model designed to interact with other agents in a society simulation.",
        environment = "",
        ):
        
        self.model = model
        self.id = id
        self.state = state
        self.personality = personality
        self.contexte = contexte
        self.environment = environment
        
        system_prompt = f"""{self.contexte}
            Your ID is "{self.id}".
            Your personality is: {self.personality}.
            Your current state is: {self.state}.
            Global environment info: {self.environment}.

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
            You can only perform one action.
            """
        
        self.messages = [{'role': 'system', 'content': system_prompt}]
    
    def generate(self, prompt):
        self.messages.append({'role': 'user', 'content': prompt})
        
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
            print(f"Agent {self.id} produced invalid JSON: {assistant_response}")
            return {"action": "think", "thought": "I failed to produce valid JSON."}