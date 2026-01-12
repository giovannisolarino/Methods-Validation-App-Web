from nicegui import ui, app
import theme
import all_pages
import home_page

def startup() -> None:


    all_pages.create()

    @ui.page('/')
    def index_page() -> None:
        

        with theme.frame('Homepage'):
            home_page.about()