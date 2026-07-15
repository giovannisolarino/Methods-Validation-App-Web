from contextlib import contextmanager

from menu import menu

from nicegui import ui, app


def clear_user_session():
    app.storage.user.clear()
    ui.notify('Session cleared.', type='info', position='top')
    ui.navigate.reload()


def data_required_prompt():
    '''Persistent empty state for pages gated on an imported dataset.'''
    with ui.card(align_items='center').classes('no-shadow border-[1px]').style('background-color: #E97451; margin-top: 20px'):
        ui.icon('info')
        ui.markdown('**No dataset in memory.** Import your data to use this page.')
        ui.button('Go to Import data', icon='upload_file',
                  on_click=lambda: ui.navigate.to('/import_data/'))

@contextmanager
def frame(navtitle: str):
    '''Shared layout for every page: call it as a context manager around the page's content.'''
    ui.colors(primary='#9ec239', secondary='#d9d9d9', accent='#111B1E', positive='#21ba45', negative="#c10015")
    
    ui.add_head_html('''
    <style>
        html, body, #q-app {
            overflow-x: hidden !important;
        }
        aside.q-drawer {
            width: 220px !important;
        }
        @media (max-width: 1200px) {
            aside.q-drawer {
                width: 200px !important;
            }
        }
    </style>
    ''')
    
    with ui.column().classes('min-h-screen w-full overflow-x-hidden'):
        yield

    with ui.header().classes(replace='row items-center') as header:
        ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
        ui.image('/icons/logo_no_bg.png').classes('w-16')
        ui.markdown('<pre>   </pre>')
        ui.html('''
        <style>
            .header {
                text-align:center;
                font-weight: bold;
                font-size: 28px;
                color: white;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }
            .highlight {
                color: #d62121;
                font-weight: bold;
            }
        </style>
        <div class="header"><span class="highlight">M</span>ethods <span class="highlight">V</span>alidation <span class="highlight">A</span>pp</div>
        ''')

    with ui.left_drawer(top_corner=False, bottom_corner=True, fixed=True, bordered=True, elevated=True).style("background-color: #d9d9d9; height:100%") as left_drawer:
        with ui.column().classes('h-full justify-between w-full'):
            with ui.column(align_items='center'):
                ui.label('Menu').style('font-size: 1rem; font-weight: bold')
                with ui.row():
                    ui.button('About', on_click=lambda: ui.navigate.to('/')).props('no-caps flat').classes(replace='text-black')
                    ui.button('Credits', on_click=lambda: ui.navigate.to('/credits/')).props('no-caps flat').classes(replace='text-black')
                ui.separator()
                menu(navtitle)
            
            with ui.column().classes('w-full p-2'):
                ui.separator()
                ui.button('Clear User History', icon='delete', color='red', 
                      on_click=lambda:clear_user_session()).props('no-caps flat').classes('w-full')