from nicegui import ui
from templates.chatbot.log_callback_handler import NiceGuiLogElementCallbackHandler
from langchain_core.messages.human import HumanMessage

def bot(agent, thread_id, extract_fn):
    
    async def clear() -> None:
        message_container.clear()

    async def send(thread_id="2") -> None:
        question = text.value
        text.value = ''

        with message_container:
            ui.chat_message(
                text=question, name='You', sent=True
            ).props(
                add='bg-color=blue-1 float=right',
            ).style(
                add='align-self: flex-end',
            )
            response_message = ui.chat_message(
                name='Bot', sent=False, text_html=True).props(add='bg-color=grey-1')

            spinner = ui.spinner(type='dots')
            message_container.scroll_to(percent=100, duration=0)

            response = ''
            thread = {"configurable": {"thread_id": thread_id}, 'callbacks': [NiceGuiLogElementCallbackHandler(log)]}
            payload = {"messages": [HumanMessage(content=question)]}
            async for chunk in agent.astream(payload, thread, stream_mode="values"):

                node_response = next(iter(chunk.values()))
                for bot_message in node_response['messages']:
                    response = extract_fn(bot_message)
                    if response != "":
                        with response_message:
                            ui.markdown(response)

                message_container.scroll_to(percent=100, duration=0)
            message_container.remove(spinner)

    with ui.column().classes('col-span-6 justify-between h-full w-full'):
        with ui.card().classes('w-full min-w-full h-full flex flex-stretch'):
            with ui.tabs().classes('w-full') as tabs:
                chat_tab = ui.tab('Chat')
                logs_tab = ui.tab('Logs')
            with ui.tab_panels(tabs, value=chat_tab).classes('w-full mx-auto flex-grow items-stretch'):
                with ui.tab_panel(chat_tab).classes('items-stretch'):
                    message_container = ui.scroll_area().classes('w-full h-full flex-grow justify-center')
                with ui.tab_panel(logs_tab):
                    log = ui.log().classes('w-full h-full')
        
        with ui.row().classes('w-full self-center h-[10%] justify-between'):
            with ui.row().classes('w-full justify-between'):
                text = ui.input(placeholder='message').props('autofocus rounded outlined input-class=mx-3') \
                    .classes('flex-grow self-center w-[350px]').on('keydown.enter', send)
                ui.button(icon='send', on_click=send).classes('self-center w-[40px]').props('rounded').on('keydown.enter', send)
                ui.button(icon='clear', on_click=clear, color='red').classes('self-center w-[40px]').props('rounded')
