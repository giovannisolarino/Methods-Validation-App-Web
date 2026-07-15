from nicegui import ui, app, events
import pandas as pd
import theme
import pathlib
from io import BytesIO
from utilities.pd_utilities import template_xlsx, tables_xlsx, matrix_effect, recovery_calc


#Matrix effect and recovery are the same workflow twice over, so both tabs are driven by the one
#panel() below and differ only in these specs.
MATRIX = {
    'name': 'matrix effect',
    'columns': ('Matrix', 'No-Matrix'),
    'compute': matrix_effect,
    'sheets': ('Matrix Effect', 'Average Matrix Effect'),
    'titles': ('Matrix Effect table', 'Average Matrix Effect'),
    'filename': 'matrix_effect.xlsx',
}

RECOVERY = {
    'name': 'recovery',
    'columns': ('Before', 'After'),
    'compute': recovery_calc,
    'sheets': ('Recovery', 'Average Recovery'),
    'titles': ('Recovery table', 'Average Recovery'),
    'filename': 'recovery.xlsx',
}


def panel(spec: dict):
    ui.markdown(f'##### {spec["name"].capitalize()}')

    def handle_upload(e: events.UploadEventArguments):
        if pathlib.Path(e.name).suffix not in ('.xlsx', '.xls'):
            ui.notify('You have selected wrong file extension', type='warning', position='center')
            return
        try:
            raw = pd.read_excel(BytesIO(e.content.read()), header=0)
            table, complete = spec['compute'](raw)
        except Exception as err:
            ui.notify(f'Could not read the {spec["name"]} file: {err}',
                      type='negative', position='center')
            return

        #Bytes, not a file under .nicegui/: every user would share that one path and a download
        #could serve somebody else's results.
        workbook = tables_xlsx(dict(zip(spec['sheets'], (table, complete))))
        with results:
            results.clear()
            with ui.row():
                ui.table.from_pandas(table.round(2), title=spec['titles'][0])
                ui.table.from_pandas(complete.round(2), title=spec['titles'][1])
                ui.button(f'Download {spec["name"]} table',
                          on_click=lambda: ui.download(workbook, spec['filename']))

    async def gen_temp(e: events.ValueChangeEventArguments):
        if levels.value is None or replicates.value is None:
            return
        template = template_xlsx(levels=int(levels.value),
                                 replicates=int(replicates.value),
                                 columns=spec['columns'])
        with template_div:
            template_div.clear()
            btn = ui.button(f'Download {spec["name"]} template',
                            on_click=lambda: ui.download(template, f'{spec["name"]}_template.xlsx')) \
                    .tooltip('Fill the template with your data')
            await btn.clicked()
            show_uploader()

    def show_uploader():
        with up_col:
            up_col.clear()
            ui.upload(label=f'Upload {spec["name"]} file', auto_upload=True, on_upload=handle_upload)

    def switch_handle(e: events.ValueChangeEventArguments):
        selector.set_visibility(not e.value)
        if e.value:
            show_uploader()
        else:
            up_col.clear()

    with ui.row():
        with ui.column():
            ui.switch('Template already downloaded?', on_change=switch_handle)
            with ui.element('div') as selector:
                levels = ui.select([2, 3], label=f'Number of levels to evaluate {spec["name"]}',
                                   value=None, on_change=gen_temp).style('width:350px')
                replicates = ui.number('Replicates per level', value=None,
                                       on_change=gen_temp).style('width:200px')
                template_div = ui.element('div')
        up_col = ui.column()
    results = ui.element('div')


def add_params():
    with theme.frame('Additional parameters'):
        ui.markdown('## **Additional parameters**')
        ui.separator().props("color=black size=2px").style('width: 85vw')

        with ui.card():
            with ui.tabs() as tabs:
                ui.tab('mat', label='Matrix Effect', icon='percent')
                ui.tab('rec', label='Recovery', icon='science')
            with ui.tab_panels(tabs, value='mat').classes('w-full'):
                with ui.tab_panel('mat'):
                    panel(MATRIX)
                with ui.tab_panel('rec'):
                    panel(RECOVERY)
