import theme
import asyncio
from utilities.pd_utilities import means_data
from utilities.stat_test import hub_vox, levene_test, weight_sel
from utilities.plotly_utilities import conf_lm
import pandas as pd
import numpy as np
from nicegui import ui, app, events

def change_loq(e: events.ValueChangeEventArguments):
    #Handle changes in using first calibrator as LOQ
    if e.value == True:
        first_point = df[f'{conc_name}'].min()
        df_lod['LOQ'] = first_point
        app.storage.user['loq'] = first_point
        with lod_table:
            lod_table.clear()
            ui.table.from_pandas(df_lod.round(2), title='Hubaux and Vos calculation').classes(replace='text-align: center').props('flat').style('width:300px; height:200px')
    
    else:
        lod_df = pd.DataFrame({
            'LOD' : [lod],
            'LOQ' : [loq]
        })
        app.storage.user['loq'] = loq
        with lod_table:
            lod_table.clear()
            ui.table.from_pandas(lod_df.round(2), title='Hubaux and Vos calculation').classes(replace='text-align: center').props('flat').style('width:300px; height:200px')


async def show_hub_vox():
    #Show Hubaux and Vos table, handle change in points and alpha value
    global df_lod, lod_table, lod, loq
    card.clear()
    card_plot.clear()
    with card:
        ui.skeleton(width='300px', height='200px')
        await asyncio.sleep(3)
        lod, loq = hub_vox(ncal=cal_num.value, conf=alpha.value, df=df, means=means, result_weight=result_weight)
        card.clear()
        df_lod = pd.DataFrame({
            'LOD' : [lod],
            'LOQ' : [loq]
        })
        app.storage.user['lod'] = lod
        app.storage.user['loq'] = loq
        with ui.card().props('flat') as lod_table:
            ui.table.from_pandas(df_lod.round(2), title='Hubaux and Vos calculation').classes(replace='text-align: center').props('flat').style('width:300px; height:200px')

        with ui.row():
            ui.checkbox('Use first calibration point as LOQ', on_change=change_loq)
            ui.html('<style>.multi-line-notification { white-space: pre-line; font-weight: bold;}</style>')
            ui.button(icon='info', on_click=lambda: ui.notify('The LOQ is obtained by multiplying the LOD value by two. \n'
                                                                'However, this method lacks statistical validation, \n'
                                                                'so its use should be followed by experimental verification. \n'
                                                                'A better alternative is to define the LOQ as the concentration level of the first calibration point, \n' 
                                                                'provided that the optimal criteria for precision and accuracy are satisfied.'
                                                              ,position='center', timeout=0, type='warning', multi_line=True, close_button='OK', classes='multi-line-notification')).props('flat')    


        if loq > df[f'{conc_name}'].min():
            await asyncio.sleep(1.2)
            ui.notify('Computed LOQ is higher than your first calibration point!', position='center', timeout=0, close_button='OK', type='warning')


        if lod > df[f'{conc_name}'].min():
            await asyncio.sleep(1.2)
            ui.notify('Computed LOD is higher than your first calibration point!', position='center', timeout=0, close_button='OK', type='warning')

    if isinstance(weight, pd.Series):
        fig = conf_lm(conf=alpha.value, df=means, weight=weight, ncal=cal_num.value)
    else:
        fig = conf_lm(conf=alpha.value, df=means, ncal=cal_num.value)
    
    with card_plot:
        card_plot.clear()
        spin = ui.spinner('bars', thickness=10, size='3em')
        await asyncio.sleep(4)
        spin.delete()
        with ui.card():
            ui.plotly(fig)

            
    

async def show_hub_vox_():
    #Show Hubaux and Vos table, handle change in alpha value (for df with only 3 points)
    global df_lod, lod_table, lod, loq
    card.clear()
    card_plot.clear()
    with card:
        ui.skeleton(width='300px', height='200px')
        lod, loq = hub_vox(ncal=3, conf=alpha.value, df=df, means=means, result_weight=result_weight)
        await asyncio.sleep(3)
        lod, loq = hub_vox(ncal=3, conf=alpha.value, df=df, means=means, result_weight=result_weight)
        app.storage.user['lod'] = lod
        app.storage.user['loq'] = loq
        card.clear()
        df_lod = pd.DataFrame({
            'LOD' : [lod],
            'LOQ' : [loq]
        })
        with ui.card().props('flat') as lod_table:
            ui.table.from_pandas(df_lod.round(2), title='Hubaux and Vos calculation').classes(replace='text-align: center').props('flat').style('width:300px; height:200px')
    
        with ui.row():
            ui.checkbox('Use first calibration point as LOQ', on_change=change_loq)
            ui.html('<style>.multi-line-notification { white-space: pre-line; font-weight: bold;}</style>')
            ui.button(icon='info', on_click=lambda: ui.notify('The LOQ is obtained by multiplying the LOD value by two. \n'
                                                                'However, this method lacks statistical validation, \n'
                                                                'so its use should be followed by experimental verification. \n'
                                                                'A better alternative is to define the LOQ as the concentration level of the first calibration point, \n' 
                                                                'provided that the optimal criteria for precision and accuracy are satisfied.'
                                                              ,position='center', timeout=0, multi_line=True, close_button='OK', type='warning' ,classes='multi-line-notification')).props('flat')

        if loq > df[f'{conc_name}'].min():
            await asyncio.sleep(1.2)
            ui.notify('Computed LOQ is higher than your first calibration point!', position='center', timeout=0, close_button='OK', type='warning')


        if lod > df[f'{conc_name}'].min():
            await asyncio.sleep(1.2)
            ui.notify('Computed LOD is higher than your first calibration point!', position='center', timeout=0, close_button='OK', type='warning')
        
    if isinstance(weight, pd.Series):
        fig = conf_lm(conf=alpha.value, df=means, weight=weight, ncal=3)
    else:
        fig = conf_lm(conf=alpha.value, means=means, ncal=3)
    
    with card_plot:
        card_plot.clear()
        spin = ui.spinner('bars', thickness=10, size='3em')
        await asyncio.sleep(4)
        spin.delete()
        with ui.card():
            ui.plotly(fig)
    




def lod_loq():
    global df, means, alpha, cal_num, card, result_weight, conc_name, weight, card_plot
    try:
        df = pd.read_json(app.storage.user['df'])
        means = means_data(df)
        conc_name = app.storage.user['conc_name']
    except:
        df = None
        ui.notify('Data not found', type='negative', position='center')
    with theme.frame('LOD and LOQ'):
        ui.markdown('## **LOD and LOQ - Hubaux and Vos Method**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        if df is not None:
            levenedf, outcome = levene_test(df)
            app.storage.user['sced_test'] = outcome
            variance, result_weight, weight = weight_sel(df)
            with ui.grid(columns='auto 2fr'):
                
                if df['Calibrator'].nunique() > 3:
                    alpha = ui.number('Statical significance level', value=0.05, on_change=show_hub_vox).bind_value_to(app.storage.user, 'alpha')
                    with ui.column():
                        ui.label('Number of calibrators to use in Hubaux and Vos algorithm')
                        cal_num = ui.radio([3, 4], value=3, on_change=show_hub_vox).props('inline')
                    card = ui.card()
                    card_plot = ui.element('div')
                    ui.timer(0, callback=show_hub_vox, once=True)
                    
                        
                else:
                    alpha = ui.number('Statical significance level', value=0.05, on_change=show_hub_vox_).bind_value_to(app.storage.user, 'alpha')
                    ui.element('div').style('width: 200px; visibility: hidden;')
                    card = ui.card()
                    card_plot = ui.element('div')
                    ui.timer(0, callback=show_hub_vox_, once=True)

                        