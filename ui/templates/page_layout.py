from nicegui import ui
import requests, os, json
from templates.chatbot.chat import bot
from langserve import RemoteRunnable

API_URL = os.environ["API_URL"]

def page_layout():
    with ui.header(elevated=False).classes('items-center bg-slate-50'):
        with ui.row().classes('w-[100%] justify-between'):
            with ui.row().classes('w-[20%]'):
                ui.image('images/acxiom_logo_navy.png').classes('w-[45%]')
                ui.image('images/axcp_logo_teal.png').classes('w-[30%]')
            ui.button(on_click=lambda: right_drawer.toggle(), icon='chat').props('flat color=blue')
    
    with ui.left_drawer(elevated=False, bordered=True).classes('bg-white pl-4 space-y-1'):
        ui.markdown('##### __Navigation__').classes('w-full text-center')
    
    with ui.right_drawer(elevated=False, bordered=True).classes('bg-white pl-4 space-y-1') as right_drawer:
        ui.markdown('##### __Conversations__').classes('w-full text-center')
        
    with ui.footer().classes('bg-slate-50 w-full justify-center'):
        ui.label('Prototype Mode Enabled').classes('text-slate-900 italic')