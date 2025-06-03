from langchain_core.prompts import PromptTemplate




custom_prompt = PromptTemplate.from_template("""
You are an assistant that helps answer user questions using tools when necessary.
ONLY respond to the user's input. Do not generate new questions or simulate future inputs.
Here is the conversation history:
{chat_history}

Human: {input}
AI:""")
