from nicegui import app, ui
from pages import home

app.include_router(home.router)

ui.run(favicon="images/axcp_icon.png")