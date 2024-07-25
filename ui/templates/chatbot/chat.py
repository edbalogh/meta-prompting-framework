from typing import Dict, List
from langchain_core.messages import AIMessage, BaseMessage, FunctionMessage
from nicegui import ui
import uuid, requests, os, re, httpx
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
from templates.chatbot.log_callback_handler import NiceGuiLogElementCallbackHandler
from langchain_core.messages.human import HumanMessage


API_URL = os.environ['API_URL']


def determine_message_type(content: str, agent_name: str) -> str:
    if agent_name.lower() == "summary agent" and "final answer:" in content.lower():
        return "final_response"
    elif any(keyword in agent_name.lower() for keyword in ["meta-expert", "meta-prompter", "planning"]):
        return "planning"
    else:
        return "expert"

def format_message(content: str) -> dict[str, str]:
    content = content.replace('`', '')
    agent_match = re.match(r'\[AGENT_NAME:\s*([^\]]+)\]', content)
    agent_name = agent_match.group(1).strip() if agent_match else "Unknown Agent"
    body = re.sub(r'\[AGENT_NAME:[^\]]+\]\s*', '', content).strip()
    
    message_type = determine_message_type(content, agent_name)
    
    return {
        "type": message_type,
        "agent_name": agent_name,
        "content": body
    }

def formatting_node(state: Dict[str, List[BaseMessage]], config: Dict) -> Dict[str, List[Dict[str, str]]]:
    formatted_messages = []
    print(f"state={state}", flush=True)
    if isinstance(state, AIMessage) or isinstance(state, FunctionMessage):
        formatted_messages.append(format_message(state.content))
    else:
        for message in state["messages"]:
            if isinstance(message, AIMessage):
                formatted_messages.append(format_message(message.content))

    return {"messages": formatted_messages}


class ChatBot:
    def __init__(self, agent, extract_fn, thread_id=None, on_new_conversation=None):
        self.agent = agent
        self.thread_id = thread_id
        self.extract_fn = extract_fn
        self.message_container = None
        self.text = None
        self.log = None
        self.on_new_conversation = on_new_conversation

    def clear(self) -> None:
        self.message_container.clear()

    def load_thread(self, thread_id) -> None:
        self.thread_id = thread_id
        self.message_container.clear()

    def load_conversation(self, thread_id) -> None:
        self.thread_id = thread_id
        self.message_container.clear()
        # Here you can add logic to load the conversation history if needed

    def reset_thread(self) -> None:
        self.thread_id = None
        self.message_container.clear()

    def get_conversations_from_db(self):
        try:
            response = requests.get(f"{API_URL}/api/conversations")
            response.raise_for_status()
            self.conversations = response.json()
        except requests.RequestException as e:
            print(f"Failed to fetch conversations: {e}")
            self.conversations = []

    def generate_conversation_name(self, question: str) -> str:
        llm = OpenAI(temperature=0.7)
        prompt = PromptTemplate(
            input_variables=["question"],
            template="Generate a very short (max 5 words) name for a conversation that starts with this question: {question}"
        )
        name_chain = LLMChain(llm=llm, prompt=prompt)
        return name_chain.run(question).strip()

    def save_conversation(self, name: str) -> None:
        conversation_data = {
            "thread_id": self.thread_id,
            "name": name
        }
        try:
            response = requests.post(f"{API_URL}/api/conversations", json=conversation_data)
            response.raise_for_status()
            print(f"Conversation '{name}' saved successfully.")
        except requests.RequestException as e:
            print(f"Failed to save conversation '{name}': {e}")


    async def send(self) -> None:
        question = self.text.value
        if not self.thread_id:
            self.thread_id = str(uuid.uuid4())
            name = self.generate_conversation_name(question)
            self.save_conversation(name)
            if self.on_new_conversation:
                await self.on_new_conversation()
        self.text.value = ''

        with self.message_container:
            ui.chat_message(text=question, name='You', sent=True) \
                .props(add='bg-color=blue-1 float=right') \
                .style(add='align-self: flex-end')
            
            response_message = ui.chat_message(name='Bot', sent=False, text_html=True).props(add='bg-color=grey-1')

            spinner = ui.spinner(type='dots')
            self.message_container.scroll_to(percent=100, duration=0)

            response = ''
            config = {"configurable": {"thread_id": self.thread_id}}
            payload = {"messages": [HumanMessage(content=question)], "turn_count": 0}
            log_handler = NiceGuiLogElementCallbackHandler(self.log)
            run_id = str(uuid.uuid4())  # Generate a unique run_id

            try:
                async for chunk in self.agent.astream(payload, config=config, stream_mode="values"):
                    log_handler.on_llm_new_token(token=chunk, run_id=run_id)
                    node_response = next(iter(chunk.values()))
                    for bot_message in node_response['messages']:
                        # Format the chunk
                        formatted_chunk = formatting_node(bot_message, {})
                        response = self.extract_fn(formatted_chunk)
                        with response_message:
                            ui.markdown(response)

                    self.message_container.scroll_to(percent=100, duration=0)
            except httpx.HTTPStatusError as http_err:
                error_message = f"HTTP error occurred: {http_err}"
                print(f"Error in send method: {error_message}", flush=True)
                with response_message:
                    ui.markdown(f"**Error:** An issue occurred while processing your request. Please try again later.")
            except Exception as e:
                error_message = f"An unexpected error occurred: {str(e)}"
                print(f"Error in send method: {error_message}", flush=True)
                with response_message:
                    ui.markdown(f"**Error:** An unexpected error occurred. Please try again or contact support if the issue persists.")
            finally:
                self.message_container.remove(spinner)

    def create_ui(self):
        with ui.column().classes('col-span-6 justify-between h-full w-full'):
            with ui.card().classes('w-full h-[500px] flex flex-grow'):
                with ui.tabs().classes('w-full') as tabs:
                    chat_tab = ui.tab('Chat')
                    logs_tab = ui.tab('Logs')
                with ui.tab_panels(tabs, value=chat_tab).classes('w-full mx-auto flex-grow items-stretch'):
                    with ui.tab_panel(chat_tab).classes('items-stretch'):
                        self.message_container = ui.scroll_area().classes('w-full h-full flex-grow justify-center')
                    with ui.tab_panel(logs_tab):
                        self.log = ui.log().classes('w-full h-full')
            
            with ui.row().classes('w-full self-center h-[10%] justify-between'):
                with ui.row().classes('w-full justify-between'):
                    self.text = ui.input(placeholder='message').props('autofocus rounded outlined input-class=mx-3') \
                        .classes('flex-grow self-center w-[350px]').on('keydown.enter', self.send)
                    ui.button(icon='send', on_click=self.send).classes('self-center w-[40px]').props('rounded').on('keydown.enter', self.send)
                    ui.button(icon='clear', on_click=self.clear, color='red').classes('self-center w-[40px]').props('rounded')

# Usage example:
# chatbot = ChatBot(agent, thread_id, extract_fn)
# chatbot.create_ui()
