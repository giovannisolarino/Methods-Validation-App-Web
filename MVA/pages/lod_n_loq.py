import theme
import asyncio
from utilities.pd_utilities import means_data
from utilities.stat_test import hub_vox, levene_test, weight_sel
from utilities.plotly_utilities import conf_lm
import pandas as pd
from nicegui import ui, app, events


LOQ_INFO = ('The LOQ is obtained by multiplying the LOD value by two. \n'
            'However, this method lacks statistical validation, \n'
            'so its use should be followed by experimental verification. \n'
            'A better alternative is to define the LOQ as the concentration level of the first calibration point, \n'
            'provided that the optimal criteria for precision and accuracy are satisfied.')


def lod_loq():
    #Per-user state (dataframe, computed LOD/LOQ, cards) is local to the page function, so
    #concurrent clients each get their own. As module globals one user's run overwrote another's.
    try:
        df = pd.read_json(app.storage.user['df'])
        means = means_data(df)
        conc_name = app.storage.user['conc_name']
    except:
        df = None
        ui.notify('Data not found', type='negative', position='center')

    #Mutable box for the results, so the checkbox handler can read what show_hub_vox computed.
    state = {}

    def change_loq(e: events.ValueChangeEventArguments):
        #Handle changes in using first calibrator as LOQ
        if e.value:
            loq = df[f'{conc_name}'].min()
        else:
            loq = state['loq']
        app.storage.user['loq'] = loq
        table = pd.DataFrame({'LOD': [state['lod']], 'LOQ': [loq]})
        with state['lod_table']:
            state['lod_table'].clear()
            ui.table.from_pandas(table.round(2), title='Hubaux and Vos calculation').classes(replace='text-align: center').props('flat').style('width:300px; height:200px')

    async def show_hub_vox():
        #Show Hubaux and Vos table, handle change in points and alpha value.
        #ncal falls back to 3 when the dataset carries only three calibration levels, which is
        #also the only choice the radio offers in that case.
        ncal = int(cal_num.value) if cal_num is not None else 3
        card.clear()
        card_plot.clear()
        with card:
            ui.skeleton(width='300px', height='200px')
            await asyncio.sleep(3)
            lod, loq = hub_vox(ncal=ncal, conf=alpha.value, df=df, means=means, result_weight=result_weight)
            card.clear()
            state['lod'], state['loq'] = lod, loq
            app.storage.user['lod'] = lod
            app.storage.user['loq'] = loq
            df_lod = pd.DataFrame({'LOD': [lod], 'LOQ': [loq]})
            with ui.card().props('flat') as lod_table:
                state['lod_table'] = lod_table
                ui.table.from_pandas(df_lod.round(2), title='Hubaux and Vos calculation').classes(replace='text-align: center').props('flat').style('width:300px; height:200px')

            with ui.row():
                ui.checkbox('Use first calibration point as LOQ', on_change=change_loq)
                ui.html('<style>.multi-line-notification { white-space: pre-line; font-weight: bold;}</style>')
                ui.button(icon='info', on_click=lambda: ui.notify(LOQ_INFO, position='center', timeout=0,
                                                                  type='warning', multi_line=True,
                                                                  close_button='OK',
                                                                  classes='multi-line-notification')).props('flat')

            #Notifying straight away: sleeping first lets the user navigate away, and the
            #notification then targets a client NiceGUI has already deleted.
            if loq > df[f'{conc_name}'].min():
                ui.notify('Computed LOQ is higher than your first calibration point!', position='center', timeout=0, close_button='OK', type='warning')

            if lod > df[f'{conc_name}'].min():
                ui.notify('Computed LOD is higher than your first calibration point!', position='center', timeout=0, close_button='OK', type='warning')

        if isinstance(weight, pd.Series):
            fig = conf_lm(conf=alpha.value, df=means, weight=weight, ncal=ncal)
        else:
            fig = conf_lm(conf=alpha.value, df=means, ncal=ncal)

        with card_plot:
            card_plot.clear()
            spin = ui.spinner('bars', thickness=10, size='3em')
            await asyncio.sleep(4)
            spin.delete()
            with ui.card():
                ui.plotly(fig)

    with theme.frame('LOD and LOQ'):
        ui.markdown('## **LOD and LOQ - Hubaux and Vos Method**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        if df is not None:
            levenedf, outcome = levene_test(df)
            app.storage.user['sced_test'] = outcome
            variance, result_weight, weight = weight_sel(df)
            cal_num = None
            with ui.grid(columns='auto 2fr'):
                alpha = ui.number('Statical significance level', value=0.05, on_change=show_hub_vox).bind_value_to(app.storage.user, 'alpha')
                if df['Calibrator'].nunique() > 3:
                    with ui.column():
                        ui.label('Number of calibrators to use in Hubaux and Vos algorithm')
                        cal_num = ui.radio([3, 4], value=3, on_change=show_hub_vox).props('inline')
                else:
                    ui.element('div').style('width: 200px; visibility: hidden;')
                card = ui.card()
                card_plot = ui.element('div')
                ui.timer(0, callback=show_hub_vox, once=True)
