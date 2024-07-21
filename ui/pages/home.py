import os
from nicegui import APIRouter, ui
from langserve import RemoteRunnable

from templates.page_layout import page_layout
from templates.chatbot.chat import bot

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
    ui.page_title('Acxiom Automapping POC')
    agent = RemoteRunnable(f"{API_URL}/agents/meta-prompter")

    thread_id = ui.input(label="Thread Id", value="1")
    bot(agent, thread_id.value, parse_response_fn)

    page_layout()

