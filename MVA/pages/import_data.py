from nicegui import ui, events, app
from io import BytesIO, StringIO
from utilities.pd_utilities import normalize, display_df
import pandas as pd
import pathlib
import asyncio
import theme


#Amphetamine calibration curve: 5 levels x 9 replicates (3 curves on each of 3 days).
#The trailing space in the analyte column name is part of the header.
EXAMPLE_PATH = './static/Amph_example_dataset.xlsx'
EXAMPLE_COLS = ['Conc', 'Area amphetamine ', 'Area amphetamineD6 ISTD']
EXAMPLE_NAME = 'Amphetamine'
EXAMPLE_UNIT = 'ppb'
EXAMPLE_ISTD_CONC = 100.0


def info_expander():
    with ui.dialog() as dialog, ui.card(align_items='center').style("background-color: #84fa84; padding:20px; border-radius: 5px").classes('width:200px'):
        dialog.open()
        ui.markdown('_Here is a dataset template!_<br />'
                    '**AA analyte** requires analyte signal values. **Conc.** requires spiked concentration values. **AA ISTD** requires ISTD signal values.'
                    '\n\n If ISTD is not available, include a list of 1 in **AA ISTD** column.'
                    '\n\nThe dataset can include as many calibration points as needed. Similarly, any number of calibration curves can be used, as long as the same number of curves is used consistently each day. Note that you can have multiple columns, each representing a different analyte. <br />'
                    'Please enter the data collected day by day, starting with all calibrators from curve A, then curve B, and so on. Each calibration curve is labeled with a letter, from A to I.')
        ui.button('Download template', on_click=lambda: ui.download('./static/example.xlsx'))
        btn1 = ui.button('Close', on_click=dialog.close).props('flat')
        btn1.tailwind.align_self('end')
        btn1.on_click(dialog.close)
        btn1.on_click(dialog.clear)


def content():
    with theme.frame('Import data'):

        #Mutable box so the handlers can rebind the widgets they create for each other.
        ui_state = {'btn': None}

        async def show_df():
            df = pd.read_json(app.storage.user['df'])

            ui_state['btn'].clear()
            with ui_state['btn']:
                ui.spinner(type='dots', size='lg', thickness=10.0, color='black')
                app.storage.user['conc_name'] = selected_col[0]
                try:
                    df_model = normalize(df=df[selected_col], selected_col=selected_col,
                                         istd_conc=app.storage.user['istd_conc'])
                except ValueError as err:
                    if str(err) == 'cannot reindex on an axis with duplicate labels':
                        message = 'Seems you have selected two identical columns!'
                    else:
                        message = f'Could not process the selected columns: {err}'
                    ui.notify(message, type='negative', position='center', timeout=0, close_button='OK')
                    ui.timer(interval=3, callback=clear_error)
                    #Leave the stored dataframe untouched: df_model is still un-normalized here.
                    reset_form()
                    return
                await asyncio.sleep(3)
                reset_form()

                app.storage.user['df'] = df_model.to_json()

            with data_col:
                with ui.row():
                    ui.switch('Clear Data', on_change=clear_df_model)
                    ui.space()
                    ui.button('Go to Calibration', icon='play_circle_filled', on_click=lambda: ui.navigate.to('/linearity/'))
                ui.table.from_pandas(df=display_df(df_model), pagination=5, title=app.storage.user['name']).classes(replace='text-align: center')
                exception_handler.clear()
                exception_handler.update()

        def reset_form():
            if ui_state['btn'] is not None:
                ui_state['btn'].delete()
                ui_state['btn'] = None
            selected_col.clear()
            conc.value = None
            istd.value = None
            analyte.value = None

        async def clear_error():
            data_col.clear()
            name_input.value = None
            unit_input.value = None
            istd_input.value = None

        async def clear_df_model():
            with spin:
                ui.spinner(size='lg', thickness=10.0)
                ui.label('Deleting dataframe...').classes('text-bold')
            await asyncio.sleep(2)
            spin.clear()
            data_col.clear()
            name_input.value = None
            unit_input.value = None
            istd_input.value = None
            ui.notify('Dataframe deleted', position='top', type='info')

        async def memory_clear(e: events.ValueChangeEventArguments):
            if e.value is True:
                ui.spinner(size='lg')
                ui.label('Clearing memory...').classes('text-bold')
                await asyncio.sleep(1.5)
                app.storage.user.clear()
                await asyncio.sleep(0.5)
                ui.navigate.reload()

        def handle_upload(e: events.UploadEventArguments):
            allowed_ext = ['.xlsx', '.xls', '.csv', '.txt']
            extension = pathlib.Path(e.name).suffix
            raw = e.content.read()
            try:
                if extension in ['.xlsx', '.xls']:
                    df = pd.read_excel(BytesIO(raw), header=0)
                elif extension in ['.csv', '.txt']:
                    df = pd.read_csv(StringIO(raw.decode()), sep=None, engine='python')
                else:
                    raise Exception

                app.storage.user['df'] = df.to_json()
                app.storage.user['original_df'] = df.to_json()

            except:
                if extension not in allowed_ext:
                    ui.notify('You have selected wrong file extension', type='warning', position='center', timeout=0, close_button='OK')
                else:
                    ui.notify('Something went wrong!', type='negative', position='top')

        def df_sel():
            nonlocal conc, analyte, istd, name_input, unit_input, istd_input, selected_col

            df = pd.read_json(app.storage.user['df'])
            selected_col = []

            def handle_selection():
                selected_col[:] = [conc.value, analyte.value, istd.value]

                if None in selected_col:
                    return
                with first_row:
                    with ui.button(on_click=show_df).style('width:450px; height:50px').props('no-caps') as btn:
                        ui.label('Show data')
                    btn.set_visibility(visible=False)
                    ui_state['btn'] = btn

            def handle_input():
                name_input.bind_value_to(app.storage.user, 'name')
                unit_input.bind_value_to(app.storage.user, 'unit')
                istd_input.bind_value_to(app.storage.user, 'istd_conc')

            async def handle_istd():
                if 'istd_conc' in app.storage.user and ui_state['btn'] is not None:
                    await asyncio.sleep(1.7)
                    ui_state['btn'].set_visibility(visible=True)

            if df is None:
                return

            columns = df.columns.values.tolist()
            with selections:
                conc = ui.select(columns, label='Select concentration column', on_change=handle_selection).classes('position:fixed')
                analyte = ui.select(columns, label='Select analyte signal column', on_change=handle_selection).classes('position:fixed')
                istd = ui.select(columns, label='Select ISTD signal column', on_change=handle_selection).classes('possition:fixed')

            with num_input:
                name_input = ui.input('Analyte name', on_change=handle_input).props('clearable')
                unit_input = ui.input('Measurement unit', on_change=handle_input).props('clearable')
                istd_input = ui.number('ISTD concentration', format='%.2f', on_change=handle_istd).props('clearable')

        def change_checkbox(e: events.ValueChangeEventArguments):
            if e.value is True:
                app.storage.user['df'] = app.storage.user['original_df']
                df_sel()

        def load_example():
            '''Load the bundled Amphetamine dataset and pre-fill the import form.'''
            try:
                df = pd.read_excel(EXAMPLE_PATH, header=0)
            except Exception as err:
                ui.notify(f'Could not load the example dataset: {err}', type='negative', position='center', timeout=0, close_button='OK')
                return

            missing = [c for c in EXAMPLE_COLS if c not in df.columns]
            if missing:
                ui.notify(f'Example dataset is missing the columns {missing}', type='negative', position='center', timeout=0, close_button='OK')
                return

            app.storage.user['df'] = df.to_json()
            app.storage.user['original_df'] = df.to_json()
            app.storage.user['name'] = EXAMPLE_NAME
            app.storage.user['unit'] = EXAMPLE_UNIT
            app.storage.user['istd_conc'] = EXAMPLE_ISTD_CONC

            #Rebuild the form from scratch, otherwise a second click stacks a duplicate set of
            #selects and a duplicate 'Show data' button.
            if ui_state['btn'] is not None:
                ui_state['btn'].delete()
                ui_state['btn'] = None
            selections.clear()
            num_input.clear()
            data_col.clear()
            exception_handler.clear()

            df_sel()

            #Order matters: the three selects build the 'Show data' button once all of
            #them are set, and handle_istd only reveals a button that already exists.
            name_input.value = EXAMPLE_NAME
            unit_input.value = EXAMPLE_UNIT
            conc.value = EXAMPLE_COLS[0]
            analyte.value = EXAMPLE_COLS[1]
            istd.value = EXAMPLE_COLS[2]
            istd_input.value = EXAMPLE_ISTD_CONC

            ui.notify(f'Example dataset loaded: {EXAMPLE_NAME} ({EXAMPLE_ISTD_CONC:g} {EXAMPLE_UNIT} ISTD). Press "Show data" to continue.',
                      type='positive', position='top', timeout=6000)

        def clean_uploader():
            app.storage.user.pop('df', None)
            app.storage.user.pop('original_df', None)
            ui_state['btn'] = None
            selections.clear()
            num_input.clear()
            data_col.clear()
            exception_handler.clear()
            spin.clear()

        conc = analyte = istd = None
        name_input = unit_input = istd_input = None
        selected_col = []

        with ui.column(align_items='center'):
            ui.markdown('## **Upload and manage data**')

        ui.separator().props("color=black size=2px").style('width: 90vw')

        with ui.grid(columns=2) as first_row:
            uploader = ui.upload(label="Import data (allowed extension .csv, .txt, .xlsx/.xls)", on_upload=handle_upload, auto_upload=True).classes(replace='w-full')
            uploader.on_upload(df_sel)
            uploader.on("removed", clean_uploader)
            with ui.column():
                ui.button('Info', icon='info', on_click=info_expander, color='green').style('width: 150px; height: 20px;').props('no-caps')
                example_button = ui.button('Load example dataset', icon='science', on_click=load_example, color='green').style('width: 250px;').props('no-caps')
                example_button.tooltip(f'{EXAMPLE_NAME} calibration curve: 5 levels, 3 curves per day over 3 days')

            selections = ui.element('div').classes('col-span-1')
            num_input = ui.element('div').classes('col-span-1').style('padding-left:100px')

        spin = ui.row()
        data_col = ui.element('div')
        exception_handler = ui.element('div')

        if 'df' in app.storage.user:
            name = app.storage.user.get('name')
            with exception_handler:
                with ui.card().classes('no-shadow border-[1px]').style('background-color: #84fa84'):
                    ui.label(f'{name} dataset in memory!')
                ui.checkbox('Change analyte', on_change=change_checkbox)
                ui.checkbox('Clear memory', on_change=memory_clear)
        else:
            with exception_handler:
                with ui.card().classes('no-shadow border-[1px]').style('background-color: #E97451'):
                    ui.label('No datasets in memory!')
