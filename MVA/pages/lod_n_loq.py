import theme
from utilities.pd_utilities import means_data
from utilities.stat_test import hub_vox, levene_test, weight_sel
from utilities.plotly_utilities import conf_lm, hd_plot
import pandas as pd
from nicegui import ui, app, events


LOQ_INFO = ('CCα (decision limit): lowest signal distinguishable from the blank at risk α. \n'
            'CCβ (LOD): lowest concentration reliably detected at risk β, read off the lower calibration band. \n'
            'LOQ: taken as 2×LOD. This lacks statistical validation, \n'
            'so its use should be followed by experimental verification. \n'
            'A better alternative is to define the LOQ as the concentration level of the first calibration point, \n'
            'provided that the optimal criteria for precision and accuracy are satisfied.')

CITATION = ('del Río Bocio FJ, Riu J, Boqué R, Rius FX. Limits of detection in linear regression with '
            'errors in the concentration. J. Chemometrics 2003; 17: 413–421. DOI: 10.1002/cem.818')


def lod_loq():
    try:
        df = pd.read_json(app.storage.user['df'])
        means = means_data(df)
        conc_name = app.storage.user['conc_name']
    except:
        df = None

    #Mutable box for the results, so the checkbox handler can read what show_hub_vox computed.
    state = {}

    def render_lod_table(loq):
        df_lod = pd.DataFrame({'CCα (Decision limit)': [state['cc_alpha']],
                               'CCβ (LOD)': [state['cc_beta']],
                               'LOQ': [loq]})
        ui.table.from_pandas(df_lod.round(2), title='Hubaux and Vos calculation').classes(replace='text-align: center').props('flat').style('width:450px; height:200px')

    def change_loq(e: events.ValueChangeEventArguments):
        loq = df[f'{conc_name}'].min() if e.value else state['loq']
        app.storage.user['loq'] = loq
        with state['lod_table']:
            state['lod_table'].clear()
            render_lod_table(loq)

    async def show_hub_vox():
        #cal_num is None when the dataset carries only three calibration levels, and 3 is then
        #also the only choice the radio would offer.
        ncal = int(cal_num.value) if cal_num is not None else 3
        card.clear()
        card_plot.clear()
        with card:
            ui.skeleton(width='300px', height='200px')
            cc_alpha, cc_beta, loq, band = hub_vox(ncal=ncal, conf=alpha.value, df=df, means=means, result_weight=result_weight)
            card.clear()
            state['cc_alpha'], state['cc_beta'], state['loq'] = cc_alpha, cc_beta, loq
            app.storage.user['lod'] = cc_beta
            app.storage.user['loq'] = loq
            with ui.card().props('flat') as lod_table:
                state['lod_table'] = lod_table
                render_lod_table(loq)

            with ui.row():
                ui.checkbox('Use first calibration point as LOQ', on_change=change_loq)
                ui.html('<style>.multi-line-notification { white-space: pre-line; font-weight: bold;}</style>')
                ui.button(icon='info', on_click=lambda: ui.notify(LOQ_INFO, position='center', timeout=0,
                                                                  type='warning', multi_line=True,
                                                                  close_button='OK',
                                                                  classes='multi-line-notification')).props('flat')
                with ui.dialog() as fig_dialog, ui.card(align_items='center').style('max-width: 720px'):
                    ui.label('Figure 2 — The Hubaux and Vos approach for calculating the limit of detection').classes('text-weight-bold')
                    ui.image('/static/hubaux_vos_fig2.png').style('width: 620px; max-width: 100%')
                    ui.markdown(f'*{CITATION}*  \n[https://doi.org/10.1002/cem.818](https://doi.org/10.1002/cem.818)')
                    ui.button('Close', on_click=fig_dialog.close).props('flat')
                ui.button(icon='menu_book', on_click=fig_dialog.open).props('flat').tooltip('Show Figure 2 from the paper')

            #Notify straight away: sleeping first lets the user navigate away, and the
            #notification then targets a client NiceGUI has already deleted.
            if loq > df[f'{conc_name}'].min():
                ui.notify('Computed LOQ is higher than your first calibration point!', position='center', timeout=0, close_button='OK', type='warning')

            if cc_beta > df[f'{conc_name}'].min():
                ui.notify('Computed LOD is higher than your first calibration point!', position='center', timeout=0, close_button='OK', type='warning')

        with card_plot:
            card_plot.clear()
            spin = ui.spinner('bars', thickness=10, size='3em')
            fig_full = conf_lm(df=means, ncal=ncal, band=band)
            fig_zoom = conf_lm(df=means, ncal=ncal, band=band, zoom=True)
            spin.delete()
            with ui.row():
                with ui.card():
                    hd_plot(fig_full)
                with ui.card():
                    hd_plot(fig_zoom)

    with theme.frame('LOD and LOQ'):
        ui.markdown('## **LOD and LOQ - Hubaux and Vos Method**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        if df is not None:
            levenedf, outcome = levene_test(df)
            app.storage.user['sced_test'] = outcome
            variance, result_weight, weight = weight_sel(df)
            cal_num = None
            with ui.grid(columns='auto 2fr'):
                alpha = ui.number('Statistical significance level', value=0.05, on_change=show_hub_vox).bind_value_to(app.storage.user, 'alpha')
                if df['Calibrator'].nunique() > 3:
                    with ui.column():
                        ui.label('Number of calibrators to use in Hubaux and Vos algorithm')
                        cal_num = ui.radio([3, 4], value=3, on_change=show_hub_vox).props('inline')
                else:
                    ui.element('div').style('width: 200px; visibility: hidden;')
                card = ui.card()
                card_plot = ui.element('div')
                ui.timer(0, callback=show_hub_vox, once=True)
        else:
            theme.data_required_prompt()
