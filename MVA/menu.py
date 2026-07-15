from nicegui import ui

#label, icon, route, and the frame() navtitle the page passes so the active entry can be marked.
PAGES = [
    ('Import data', 'upload_file', '/import_data/', 'Import data'),
    ('Calibration', 'r_analytics', '/linearity/', 'Linearity'),
    ('LOD and LOQ', 'r_science', '/lod_n_loq/', 'LOD and LOQ'),
    ('Precision', 'ads_click', '/precision/', 'Precision'),
    ('Accuracy', 'verified', '/accuracy/', 'Accuracy'),
    ('Additional parameters', 'tune', '/add_params/', 'Additional parameters'),
]


def menu(active: str = '') -> None:
    ui.button.default_style('justify-content: center; border-radius: 10px')
    ui.button.default_classes(replace='text-black')
    with ui.grid():
        for label, icon, path, navtitle in PAGES:
            btn = ui.button(label, icon=icon, on_click=lambda p=path: ui.navigate.to(p))
            if navtitle == active:
                btn.props('color=primary').classes(replace='text-white')
            else:
                btn.props('flat')
