import os
import aiohttp
from nicegui import APIRouter, ui
from langserve import RemoteRunnable
from templates.page_layout import page_layout
from templates.chatbot.chat import ChatBot
import asyncio

router = APIRouter()
API_URL = os.environ['API_URL']

async def load_conversations():
    async with aiohttp.ClientSession() as session:
        print(f"GET on {API_URL}api/conversations", flush=True)
        async with session.get(f"{API_URL}api/conversations") as response:
            if response.status == 200:
                data = await response.json()
                print(f"data returned: {data}", flush=True)
                return data
            else:
                print(f"Error loading conversations: {response.status} - {await response.text()}", flush=True)
                return []

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
async def page():
    ui.page_title('Acxiom Automapping POC')
    
    async def load_conversation_list():
        conversations = await load_conversations()
        print(f"conversations: {conversations}")
        conversation_list.clear()
        with conversation_list:
            ui.button(icon='add', on_click=lambda: asyncio.create_task(new_conversation())).props('flat color=primary').classes('w-full')
            for conv in conversations:
                ui.button(conv.get('name') or f"Conversation {conv.get('thread_id')}", on_click=lambda c=conv: asyncio.create_task(load_conversation(c))).props('flat color=primary').classes('w-full')

    agent = RemoteRunnable(f"{API_URL}/agents/meta-prompter")
    bot = ChatBot(agent, parse_response_fn, on_new_conversation=load_conversation_list)
    
    async def new_conversation():
        print("starting new chat")
        bot.reset_thread()

    async def load_conversation(conversation):
        bot.thread_id = conversation['thread_id']
        bot.load_conversation(conversation['thread_id'])

    ui.input(label="Thread Id").bind_value(bot, "thread_id")
    bot.create_ui()

    page_layout()

    with ui.right_drawer(elevated=False, bordered=True).classes('bg-white pl-4 space-y-1') as right_drawer:
        ui.markdown('##### __Conversations__').classes('w-full text-center')
        conversation_list = ui.column().classes('w-full')
        await load_conversation_list()
