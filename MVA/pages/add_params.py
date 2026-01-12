from nicegui import ui, app, events
import pandas as pd
import theme
import pathlib
from io import BytesIO
import statsmodels.api as sm
from utilities.pd_utilities import mat_eff_gen, matrix_effect, rec_gen, recovery_calc







def handle_upload_rec(e: events.UploadEventArguments) :
    global rec_df
    allowed_ext = ['.xlsx', '.xls']
    file_name = e.name
    
    file = e.content.read()
    extension = pathlib.Path(file_name).suffix
    try:
        if extension in ['.xlsx', '.xls']:
            file = BytesIO(file)
            rec_df = pd.read_excel(file, header=0)
            rec_df, complete_rec = recovery_calc(rec_df)
            complete_rec.to_json('./.nicegui/recovery.json')
            with pd.ExcelWriter('./.nicegui/recovery.xlsx') as writer:
                rec_df.to_excel(writer, sheet_name='Recovery', index=False)
                complete_rec.to_excel(writer, sheet_name='Average Recovery', index=False)
            with ui.row():
                ui.table.from_pandas(rec_df.round(2), title='Recovery table')
                ui.table.from_pandas(complete_rec.round(2), title='Average Recovery')
                ui.button('Download recovery table', on_click = lambda: ui.download('./.nicegui/recovery.xlsx'))
        else:
            raise Exception
        

        

    except:
        if extension not in allowed_ext:
            ui.notify('You have selected wrong file extension', type='warning', position='center')
        else:
            ui.notify('Something went wrong!', type='negative', position='center')




def handle_upload(e: events.UploadEventArguments) :
    global mat_df
    allowed_ext = ['.xlsx', '.xls']
    file_name = e.name
    
    file = e.content.read()
    extension = pathlib.Path(file_name).suffix
    try:
        if extension in ['.xlsx', '.xls']:
            file = BytesIO(file)
            mat_df = pd.read_excel(file, header=0)
            mat_df, complete = matrix_effect(mat_df)
            complete.to_json('./.nicegui/matrix.json')
            with pd.ExcelWriter('./.nicegui/mat_eff.xlsx') as writer:
                mat_df.to_excel(writer, sheet_name='Matrix Effect', index=False)
                complete.to_excel(writer, sheet_name='Average Matrix Effect', index=False)
            with ui.row():
                ui.table.from_pandas(mat_df.round(2), title='Matrix Effect table')
                ui.table.from_pandas(complete.round(2), title='Average Matrix Effect')
                ui.button('Download matrix effect table', on_click = lambda: ui.download('./.nicegui/mat_eff.xlsx'))
        else:
            raise Exception
        

        

    except:
        if extension not in allowed_ext:
            ui.notify('You have selected wrong file extension', type='warning', position='center')
        else:
            ui.notify('Something went wrong!', type='negative', position='center')





async def gen_temp_rec(e: events.ValueChangeEventArguments):
    #Generate recovery's template
    if e.value is not None:
        levels = lev_rec.value
        replicates = rep_rec.value
        if levels is not None and replicates is not None:
            path = rec_gen(levels=int(levels), replicates=int(replicates))
            with ui.element('div') as button_div:
                button_div.clear()
                ui.element('div').style('height: 30px; visibility: hidden;')
                btn = ui.button('Download matrix effect template', on_click=lambda:ui.download(path)).tooltip('Fill the template with your data')

                await btn.clicked()
                with up_col_rec:
                    up_col_rec.clear()
                    ui.element('div').style('width: 50px; visibility: hidden;')
                    ui.upload(label='Upload matrix effect file', auto_upload=True, on_upload=handle_upload_rec)






async def gen_temp(e: events.ValueChangeEventArguments):
    #Generate matrix effext's template
    if e.value is not None:
        levels = lev.value
        replicates = rep.value
        if levels is not None and replicates is not None:
            path = mat_eff_gen(levels=int(levels), replicates=int(replicates))
            with ui.element('div') as button_div:
                button_div.clear()
                ui.element('div').style('height: 30px; visibility: hidden;')
                btn = ui.button('Download matrix effect template', on_click=lambda:ui.download(path)).tooltip('Fill the template with your data')

                await btn.clicked()
                with up_col:
                    up_col.clear()
                    ui.element('div').style('width: 50px; visibility: hidden;')
                    ui.upload(label='Upload matrix effect file', auto_upload=True, on_upload=handle_upload)








def switch_handle(e: events.ValueChangeEventArguments):
    if e.value == True:
        selector.set_visibility(False)
        with up_col:
            ui.upload(label='Upload matrix effect file', auto_upload=True, on_upload=handle_upload)
    
    elif e.value == False:
        selector.set_visibility(True)
        up_col.clear()


def switch_handle_rec(e: events.ValueChangeEventArguments):
    if e.value == True:
        selector_rec.set_visibility(False)
        with up_col_rec:
            ui.upload(label='Upload recovery file', auto_upload=True, on_upload=handle_upload_rec)
    
    elif e.value == False:
        selector_rec.set_visibility(True)
        up_col_rec.clear()




        



def add_params():
    global div_num, lev, rep, up_col, selector, selector_rec, lev_rec, rep_rec, up_col_rec
    with theme.frame('Additional parameters'):
        ui.markdown('## **Additional parameters**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        
        with ui.card():
            with ui.tabs() as tabs:
                ui.tab('mat', label='Matrix Effect', icon='percent')
                ui.tab('rec', label='Recovery', icon='science')
            with ui.tab_panels(tabs, value='mat').classes('w-full'):
                with ui.tab_panel('mat'):
                    ui.markdown('##### Matrix effect')
                    with ui.row():
                        with ui.column():
                            ui.switch('Template already downloaded?', on_change=switch_handle)
                            with ui.element('div') as selector:
                                lev = ui.select([2,3], label='Number of levels to evaluate matrix effect', value=None, on_change=gen_temp).style('width:350px')
                                rep = ui.number('Replicates per level', value=None, on_change=gen_temp).style('width:200px')
                        up_col = ui.column()
                with ui.tab_panel('rec'):
                    ui.markdown('##### Recovery')
                    with ui.row():
                        with ui.column():
                            ui.switch('Template already downloaded?', on_change=switch_handle_rec)
                            with ui.element('div') as selector_rec:
                                lev_rec = ui.select([2,3], label='Number of levels to evaluate recovery', value=None, on_change=gen_temp_rec).style('width:350px')
                                rep_rec = ui.number('Replicates per level', value=None, on_change=gen_temp_rec).style('width:200px')
                            up_col_rec = ui.column()