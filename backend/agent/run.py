import logging
from langchain_core.messages import HumanMessage
from utils.llm_setup import get_llm
from chat_agent import build_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

model = get_llm(provider="openai", model_name="gpt-4o")
# model = get_llm(provider="claude", model_name="claude-3-5-sonnet-20240620")

agent = build_agent(model)

# Use streaming with improved output formatting
try:
    complex_query = """
    Provide brief answers to the following questions:
    1. What is the current population of Tokyo, Japan?
    2. What is the chemical formula for table salt?
    3. Who wrote the novel "Pride and Prejudice"?

    Use the available tools to find accurate information for each question. 
    Respond with concise answers, limiting each response to one or two sentences.
    """
    for chunk in agent.stream({"messages": [HumanMessage(content=complex_query)], "error_log": [], "turn_count": 0}):
        for key, value in chunk.items():
            if 'messages' in value:
                for message in value['messages']:
                    print(f"\n{'=' * 40}")
                    print(f"{message.type.capitalize()}:")
                    print(f"{'=' * 40}")
                    print(message.content)
            elif key == 'error_log':
                print(f"\n{'=' * 40}")
                print("Error Log:")
                print(f"{'=' * 40}")
                for error in value:
                    print(error)
            else:
                print(f"\n{'=' * 40}")
                print(f"{key.capitalize()}:")
                print(f"{'=' * 40}")
                for sub_key, sub_value in value.items():
                    print(f"{sub_key}: {sub_value}")
        print("\n" + "-" * 80 + "\n")
except Exception as e:
    logger.exception("An error occurred during execution")
    raise