from openai import OpenAI

# Set the API key "OPENAI_API_KEY" in the environment variables
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[
        {"role": "user", "content": "Hello !"}
    ]
)

print(response.choices[0].message.content)
