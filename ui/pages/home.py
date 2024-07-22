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
            if bot_message.get('content') != "":
                bot_data_str += bot_message.get('content') + "\n"
            if bot_message.get('raw'):
                bot_message_content = bot_message.get('raw')

                if type(bot_message_content) == dict:
                    print(bot_message_content)

        if type(bot_message).__name__ == 'AIMessage':
            bot_message_content = bot_message.content
            if type(bot_message_content) == str:
                bot_data_str += bot_message_content + "\n"
            elif type(bot_message_content) == list:
                for content_item in bot_message_content:
                    if content_item.get('type'):
                        content_item_type = content_item.get('type')
                        if content_item_type == 'text':
                            bot_data_str += content_item.get('text') + "\n"
                        elif content_item_type == 'tool_use':
                            if content_item.get('name') == 'create_df_from_cypher':
                                bot_data_str += "```cypher\n" + content_item.get('input').get('cypher_query') + "\n```\n"
                            elif content_item.get('name') == 'code_interpreter':
                                bot_data_str += "```python\n" + content_item.get('input').get('code') + "\n```\n"

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
