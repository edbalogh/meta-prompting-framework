from nicegui import ui
import uuid, requests, os
from templates.chatbot.log_callback_handler import NiceGuiLogElementCallbackHandler
from langchain_core.messages.human import HumanMessage

API_URL = os.environ['API_URL']

class ChatBot:
    def __init__(self, agent, extract_fn, thread_id = None):
        self.agent = agent
        self.thread_id = thread_id
        self.extract_fn = extract_fn
        self.message_container = None
        self.text = None
        self.log = None

    def clear(self) -> None:
        self.message_container.clear()

    def load_thread(self, thread_id) -> None:
        self.thread_id = thread_id
        self.message_container.clear()

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
        if not self.thread_id:
            self.thread_id = str(uuid.uuid4())
            name = self.thread_id  # TODO give name based on question
            self.save_conversation(name)
            
        question = self.text.value
        self.text.value = ''

        with self.message_container:
            ui.chat_message(
                text=question, name='You', sent=True
            ).props(
                add='bg-color=blue-1 float=right',
            ).style(
                add='align-self: flex-end',
            )
            response_message = ui.chat_message(name='Bot', sent=False, text_html=True).props(add='bg-color=grey-1')

            spinner = ui.spinner(type='dots')
            self.message_container.scroll_to(percent=100, duration=0)

            response = ''
            thread = {"configurable": {"thread_id": self.thread_id}, 'callbacks': [NiceGuiLogElementCallbackHandler(self.log)]}
            payload = {"messages": [HumanMessage(content=question)], "turn_count": 0}

            async for chunk in self.agent.astream(payload, thread, stream_mode="values"):
                node_response = next(iter(chunk.values()))
                for bot_message in node_response['messages']:
                    response = self.extract_fn(bot_message)
                    print(f"response: {response}", flush=True)
                    with response_message:
                        ui.markdown(response)

                self.message_container.scroll_to(percent=100, duration=0)
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
