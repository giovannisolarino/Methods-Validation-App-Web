from app.startup import startup
from nicegui import ui, native, app

app.native.settings['ALLOW_DOWNLOADS'] = True
app.native.settings['window_title'] = 'MVA'
app.add_static_files('/icons', 'static/icons')
app.add_static_files('/static', 'static')


app.on_startup(startup)
ui.run(host="0.0.0.0", port=8080, favicon='icons/logo.ico', title="MVA", storage_secret='XXX') #add you personal storage secret
    
