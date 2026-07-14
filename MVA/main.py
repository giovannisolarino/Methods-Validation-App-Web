import os
from app.startup import startup
from nicegui import ui, app

#MVA runs either as a shared web app or as a copy of the repo on one machine. Server mode is
#opt-in, so cloning the repo and running `python main.py` gives the local behaviour with no
#configuration at all.
SERVER = os.environ.get('MVA_SERVER') == '1'

#The secret signs the session cookie, and that cookie is what keys each user's stored dataset.
#A known, shared secret on a public server lets a forged cookie read somebody else's data, so
#server mode demands a real one rather than quietly falling back to the development default.
STORAGE_SECRET = os.environ.get('MVA_STORAGE_SECRET')
if SERVER and not STORAGE_SECRET:
    raise SystemExit('MVA_SERVER=1 requires MVA_STORAGE_SECRET, set it to a private random string '
                     '(e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).')

app.native.settings['ALLOW_DOWNLOADS'] = True
app.native.settings['window_title'] = 'MVA'
app.add_static_files('/icons', 'static/icons')
app.add_static_files('/static', 'static')


app.on_startup(startup)

#reload defaults to True in NiceGUI: on a server any touched file would restart the process and
#drop every live session.
ui.run(host="0.0.0.0", port=8080, favicon='static/icons/logo.ico', title="MVA",
       storage_secret=STORAGE_SECRET or 'mva-local-development-secret',
       reload=False)
