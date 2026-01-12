from nicegui import ui


def menu() -> None:
    ui.button.default_style('justify-content: center; border-radius: 10px')
    ui.button.default_classes(replace='text-black')
    with ui.grid():
        ui.button('Import data', icon='upload_file', on_click=lambda: ui.navigate.to('/import_data/')).props('flat')
        ui.button('Calibration', icon='r_analytics', on_click=lambda: ui.navigate.to('/linearity/')).props('flat')
        ui.button('LOD and LOQ', icon='r_science', on_click=lambda: ui.navigate.to('/lod_n_loq/')).props('flat')
        ui.button('Precision', icon='ads_click', on_click=lambda: ui.navigate.to('/precision/')).props('flat')
        ui.button('Accuracy', icon='verified',on_click=lambda: ui.navigate.to('/accuracy/')).props('flat')
        ui.button('Additional parameters', icon='tune', on_click=lambda: ui.navigate.to('/add_params/')).props('flat')
