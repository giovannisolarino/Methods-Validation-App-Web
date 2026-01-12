from nicegui import ui, events, app
from io import BytesIO, StringIO
from utilities.pd_utilities import normalize
import pandas as pd
import numpy as np
import pathlib
import asyncio
import theme



#-----GLOBAL-VARIABLES-----#
df = None
btn = None



#-----ASYNC-FUNCTIONS-----#


async def memory_clear(e: events.ValueChangeEventArguments):
    if e.value is True:
        ui.spinner(size='lg')
        ui.label('Clearing memory...').classes('text-bold')
        await asyncio.sleep(1.5)
        app.storage.user.clear() 
        await asyncio.sleep(0.5)  
        ui.navigate.reload()  

async def clear_df_model():
    global data_col, spin
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

async def clear_error():
    data_col.clear()
    name_input.value = None
    unit_input.value = None
    istd_input.value = None



async def show_df():
    global df, btn, data_col, selected_col, conc, analyte, istd, spin

    # CARICO df dalla sessione utente
    df = pd.read_json(app.storage.user['df'])

    btn.clear()
    with btn:
        spinner = ui.spinner(type='dots', size='lg', thickness=10.0, color='black')
        app.storage.user['conc_name'] = selected_col[0]
        df_model = df[selected_col]
        try:
            df_model = normalize(df=df_model, selected_col=selected_col, istd_conc= app.storage.user['istd_conc'])
        except ValueError as err:
            if str(err) == 'cannot reindex on an axis with duplicate labels':
                ui.notify('Seems you have selected two identical columns!', type='negative', position='center', timeout=0, close_button='OK')
                ui.timer(interval=3, callback=clear_error)
                pass
        await asyncio.sleep(3)
        btn.delete()
        selected_col.clear()
        conc.value = None
        istd.value = None
        analyte.value = None

        app.storage.user['df'] = df_model.to_json()

    with data_col:
        spin = ui.row()
        with ui.row():
            ui.switch('Clear Data', on_change=clear_df_model)
            ui.space()
            ui.button('Go to Calibration', icon='play_circle_filled', on_click=lambda: ui.navigate.to('/linearity/'))
        ui.table.from_pandas(df= df_model, pagination=5, title=app.storage.user['name']).classes(replace='text-align: center')
        exception_handler.clear()
        exception_handler.update()




#-----EVENT-HANDLER-FUNCTIONS-----#

def info_expander():
    with ui.dialog() as dialog, ui.card(align_items='center').style("background-color: #84fa84; padding:20px; border-radius: 5px").classes('width:200px'):
        dialog.open()
        ui.markdown('_Here is a dataset template!_<br />'
                    '**AA analyte** requires analyte signal values. **Conc.** requires spiked concentration values. **AA ISTD** requires ISTD signal values.'
                    '\n\n If ISTD is not available, include a list of 1 in **AA ISTD** column.'
                    '\n\nThe dataset can include as many calibration points as needed. Similarly, any number of calibration curves can be used, as long as the same number of curves is used consistently each day. Note that you can have multiple columns, each representing a different analyte. <br />'
                    'Please enter the data collected day by day, starting with all calibrators from curve A, then curve B, and so on. Each calibration curve is labeled with a letter, from A to I.')
        ui.button('Download template', on_click=lambda: ui.download('./static/example.xlsx')).props('no-caps')
        btn1 = ui.button('Close', on_click=dialog.close).props('flat')
        btn1.tailwind.align_self('end')
        btn1.on_click(dialog.close)
        btn1.on_click(dialog.clear)



def handle_upload(e: events.UploadEventArguments):
    global df, file
    allowed_ext = ['.xlsx', '.xls','.csv', '.txt']
    file_name = e.name

    file = e.content.read()
    extension = pathlib.Path(file_name).suffix
    try:
        if extension in ['.xlsx', '.xls']:
            file = BytesIO(file)
            df = pd.read_excel(file, header=0)
        elif extension in ['.csv','.txt']:
            file = StringIO(file.decode())
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            raise Exception

        original_df = df

        # 🔥 SALVATAGGIO SENZA FILE
        app.storage.user['df'] = df.to_json()
        app.storage.user['original_df'] = original_df.to_json()

    except:
        if extension not in allowed_ext:
            ui.notify('You have selected wrong file extension', type='warning', position='center', timeout=0, close_button='OK')
        else:
            ui.notify('Something went wrong!', type='negative', position='top')



def df_sel():
    global df, conc, analyte, istd, selections, columns, name_input, unit_input, istd_input

    df = pd.read_json(app.storage.user['df'])

    def handle_selection():
        global conc_col, analyte_col, istd_col, selected_col, btn
        conc_col = conc.value
        analyte_col = analyte.value
        istd_col = istd.value
        selected_col = []
        selected_col.extend([conc_col, analyte_col, istd_col])

        if None in selected_col:
            pass
        elif len(selected_col) == 3:
            with first_row:
                with ui.button(on_click=show_df).style('width:450px; height:50px').props('no-caps') as btn:
                    ui.label('Show data')
                btn.set_visibility(visible=False)

    def handle_input():
        name_input.bind_value_to(app.storage.user, 'name')
        unit_input.bind_value_to(app.storage.user, 'unit')
        istd_input.bind_value_to(app.storage.user, 'istd_conc')

    async def handle_istd():
        global btn
        if 'istd_conc' in app.storage.user is not None:
            await asyncio.sleep(1.7)
            btn.set_visibility(visible=True)

    if df is not None:
        columns = df.columns.values.tolist()

        with selections:
            conc = ui.select(columns, label='Select concentration column', on_change=handle_selection).classes('position:fixed')
            analyte = ui.select(columns, label='Select analyte signal column', on_change=handle_selection).classes('position:fixed')
            istd = ui.select(columns, label='Select ISTD signal column', on_change=handle_selection).classes('possition:fixed')

        with num_input:
            name_input = ui.input('Analyte name', on_change=handle_input).props('clearable')
            unit_input = ui.input('Measurement unit', on_change=handle_input).props('clearable')
            istd_input = ui.number('ISTD concentration',format='%.2f', on_change=handle_istd).props('clearable')


def change_checkbox(e: events.ValueChangeEventArguments):
    global df
    if e.value == True:

        df = pd.read_json(app.storage.user['original_df'])
        app.storage.user['df'] = app.storage.user['original_df']

        return df_sel()



def clean_uploader():
    global df, uploader, selections, columns, file, spin, data_col
    df = None
    app.storage.user.pop('df', None)
    app.storage.user.pop('original_df', None)

    columns.clear()
    selections.clear()
    selections.update()
    num_input.clear()
    num_input.update()
    file = None
    data_col.clear()
    data_col.update()
    exception_handler.clear()
    exception_handler.update()
    try:
        spin.clear()
    except NameError:
        pass



#-----PAGE-CONTENT-----#
def content():
    with theme.frame('Import data'):
        global df, data_col, uploader, selections, first_row, num_input, exception_handler, re_df
        with ui.column(align_items='center'):
            ui.markdown('## **Upload and manage data**')

        ui.separator().props("color=black size=2px").style('width: 90vw')

        with ui.grid(columns=2) as first_row:
            uploader = ui.upload(label="Import data (allowed extension .csv, .txt, .xlsx/.xls)",on_upload=handle_upload, auto_upload=True).classes(replace='w-full')
            uploader.on_upload(df_sel)
            uploader.on("removed", clean_uploader)
            info_button = ui.button('Info', icon='info', on_click=info_expander, color='green').style('width: 150px; height: 20px;').props('no-caps')

            selections = ui.element('div').classes('col-span-1')
            num_input = ui.element('div').classes('col-span-1').style('padding-left:100px')

        data_col= ui.element('div')
        exception_handler = ui.element('div')

        try:
            if 'df' in app.storage.user:
                df = pd.read_json(app.storage.user['df'])
            else:
                df = None

            name = app.storage.user.get('name')
            if df is not None:
                with exception_handler:
                    with ui.card().classes('no-shadow border-[1px]').style('background-color: #84fa84'):
                        ui.label(f'{name} dataset in memory!')
                    ui.checkbox('Change analyte', on_change=change_checkbox)
                    ui.checkbox('Clear memory', on_change=memory_clear)

        except:
            with exception_handler:
                with ui.card().classes('no-shadow border-[1px]').style('background-color: #E97451'):
                    ui.label('No datasets in memory!')
