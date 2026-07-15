import os
from app.startup import startup
from nicegui import ui, app

#Server mode is opt-in, so a plain `python main.py` gives the local behaviour unconfigured.
SERVER = os.environ.get('MVA_SERVER') == '1'

#The secret signs the session cookie, and that cookie keys each user's stored dataset: a shared,
#known secret on a public server lets a forged cookie read somebody else's data.
STORAGE_SECRET = os.environ.get('MVA_STORAGE_SECRET')
if SERVER and not STORAGE_SECRET:
    raise SystemExit('MVA_SERVER=1 requires MVA_STORAGE_SECRET, set it to a private random string '
                     '(e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).')

app.native.settings['ALLOW_DOWNLOADS'] = True
app.native.settings['window_title'] = 'MVA'
app.add_static_files('/icons', 'static/icons')
app.add_static_files('/static', 'static')


app.on_startup(startup)

#reload defaults to True in NiceGUI: on a server a touched file restarts the process and drops
#every live session.
ui.run(host="0.0.0.0", port=8080, favicon='static/icons/logo.ico', title="MVA",
       storage_secret=STORAGE_SECRET or 'mva-local-development-secret',
       reload=False)
