import os
from nicegui import ui, app
import theme
import all_pages
import home_page


def clear_user_storage() -> None:
    '''
    Drop every persisted session, so a local launch starts with no dataset in memory.

    Local runs only: on a shared server this would sign every user out on each restart.

    Deleting the session files is what gives the clean slate. app.storage.user is scoped to a
    request and cannot be emptied from here, and app.storage.clear() would remove the .nicegui
    directory the app downloads out of.
    '''

    for leftover in app.storage.path.glob('storage-user-*.json'):
        leftover.unlink(missing_ok=True)


def startup() -> None:

    if os.environ.get('MVA_SERVER') != '1':
        clear_user_storage()

    all_pages.create()

    @ui.page('/')
    def index_page() -> None:


        with theme.frame('Homepage'):
            home_page.about()
