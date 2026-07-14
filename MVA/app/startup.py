import os
from nicegui import ui, app
import theme
import all_pages
import home_page


def clear_user_storage() -> None:
    '''
    Drop every persisted session, so a local launch starts with no dataset in memory.

    Local runs only. app.storage.user is persisted to .nicegui/storage-user-<session>.json and
    restored on the next launch, which is why running the app locally reopened the previous
    session's dataset. On a shared server the same call would sign every user out on each
    restart, so it stays off there and users clear their own data with the "Clear memory" switch.

    app.storage.user itself is scoped to a request and cannot be emptied from here, and
    app.storage.clear() would remove the .nicegui directory that the app downloads out of, so
    deleting the session files is what actually gives the clean slate.
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
