import os
from nicegui import APIRouter, ui
from langserve import RemoteRunnable
from templates.page_layout import page_layout
from templates.chatbot.chat import ChatBot

router = APIRouter()
API_URL = os.environ['API_URL']


def parse_response_fn(bot_message):
    bot_data_str = ""

    print(f"bot_message: {bot_message}, type={type(bot_message)}", flush=True)
    if type(bot_message) != tuple:
        if type(bot_message) == dict:
            if bot_message.get('messages', '') != '':
                for m in bot_message.get('messages'):
                    bot_data_str += m.get('content', '') + "\n"

        bot_data_str += "\n\n"

    return bot_data_str

@router.page('/')
def page():
    
    def new_conversation():
        print("starting new chat")
        bot.reset_thread()

    ui.page_title('Acxiom Automapping POC')
    
    agent = RemoteRunnable(f"{API_URL}/agents/meta-prompter")
    bot = ChatBot(agent, parse_response_fn)
    
    ui.input(label="Thread Id").bind_value(bot, "thread_id")
    bot.create_ui()

    page_layout()

    with ui.right_drawer(elevated=False, bordered=True).classes('bg-white pl-4 space-y-1') as right_drawer:
        ui.markdown('##### __Conversations__').classes('w-full text-center')
        with ui.list().classes('w-full') as latest_chats:
            with ui.item():
                ui.button(icon='add', on_click=new_conversation)
