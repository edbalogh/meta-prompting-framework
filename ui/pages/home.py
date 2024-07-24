import os
from nicegui import APIRouter, ui
from langserve import RemoteRunnable
from templates.page_layout import page_layout
from templates.chatbot.chat import ChatBot
from models.conversation import ConversationModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, desc
from database import engine

router = APIRouter()
API_URL = os.environ['API_URL']
DATABASE_URL = os.environ['DATABASE_URL']

# engine is now imported from database.py, so we can remove this line


def load_conversations():
    with Session(engine) as session:
        conversations = session.query(ConversationModel).order_by(desc(ConversationModel.created_at)).limit(10).all()
    return conversations

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
    ui.page_title('Acxiom Automapping POC')
    
    agent = RemoteRunnable(f"{API_URL}/agents/meta-prompter")
    bot = ChatBot(agent, parse_response_fn)
    
    def new_conversation():
        print("starting new chat")
        bot.reset_thread()
        load_conversation_list()

    def load_conversation(conversation):
        bot.thread_id = conversation.id
        bot.load_conversation(conversation.id)

    def load_conversation_list():
        conversations = load_conversations()
        conversation_list.clear()
        with conversation_list:
            ui.button(icon='add', on_click=new_conversation).props('flat color=primary').classes('w-full')
            for conv in conversations:
                ui.button(conv.name or f"Conversation {conv.id}", on_click=lambda c=conv: load_conversation(c)).props('flat color=primary').classes('w-full')

    ui.input(label="Thread Id").bind_value(bot, "thread_id")
    bot.create_ui()

    page_layout()

    with ui.right_drawer(elevated=False, bordered=True).classes('bg-white pl-4 space-y-1') as right_drawer:
        ui.markdown('##### __Conversations__').classes('w-full text-center')
        conversation_list = ui.column().classes('w-full')
        load_conversation_list()
