import theme
import asyncio
import pandas as pd
from utilities.pd_utilities import means_data, display_df
from utilities.plotly_utilities import make_biplot, uloq_lloq_graph, show_model, residual_graph, kde_resid, q_qplot
from utilities.stat_test import (levene_test, f_test_sced, weight_sel, model_wls, model_ols,
                                 shapiro_wilk, select_model, double_check)
from nicegui import ui, app


def update_name_button(button: ui.dropdown_button, new_text: str):
    button.set_text(new_text)


def linearity():
    #Per-user state (dataframe, fitted models, plot containers) is local to the page function.
    #As module globals a second client opening this page rebound the first client's models and
    #wrote its plots into the first client's containers.
    try:
        df = pd.read_json(app.storage.user['df'])
    except:
        df = None
        ui.notify('Data not found', type='negative', position='center')

    async def waiting():
        with ui.row() as spin_row:
            ui.spinner(size='lg')
            ui.label("Processing graph...").classes('text-bold')
        await asyncio.sleep(2)
        ui.plotly(cal_plot)
        spin_row.delete()

    #WLS and OLS drove two near-identical copies of every handler below. The only difference is
    #the key prefix in the results dict, so `kind` carries it and one copy serves both.
    def best_model():
        #Perform Mandel's test (with the residual double check) and show the best model
        update_name_button(dpbutton, 'Best calibration model')
        mandel, mandel_summary = select_model(results, kind)
        data_stat = None
        if mandel == 'Quadratic':
            _, data_stat = double_check(results[f'{kind}_lin_raw'], results[f'{kind}_quad_raw'])

        if mandel == 'Quadratic':
            best_summary = pd.DataFrame({
                'Params': ['Intercept', 'x', 'x²'],
                'Params value': results[f'{kind}_quad'].params,
                'pvalue': results[f'{kind}_quad'].pvalues,
            })
            model = show_model(df, means,
                               line_means=results[f'line_{kind}_quad'],
                               line_raw=results[f'line_{kind}_quad_raw'],
                               model='Quadratic',
                               equation=results['equation_quad'],
                               r_squared=results['r_squared_quad'])
        else:
            best_summary = pd.DataFrame({
                'Params': ['Intercept', 'x'],
                'Params value': results[f'{kind}_lin'].params,
                'pvalue': results[f'{kind}_lin'].pvalues,
            })
            model = show_model(df, means,
                               line_means=results[f'line_{kind}_lin'],
                               line_raw=results[f'line_{kind}_lin_raw'],
                               model='Linear',
                               equation=results['equation_lin'],
                               r_squared=results['r_squared_lin'])

        with plot:
            plot.clear()
            ui.markdown('### Best Model')
            with ui.row():
                ui.table.from_pandas(mandel_summary.round(2), title='Mandel test').classes(replace='text-align: center').props('flat').style('width:350px')
                ui.element('div').style('width: 300px; visibility: hidden;')
                if data_stat is not None:
                    with ui.card(align_items='center').tooltip('Additional t-test anf F-test to compare models\' residuals (α = 0.01)'):
                        ui.markdown('#### Double check on residuals')
                        ui.icon('info')
                        ui.markdown('''Since models\' residuals are statistically identical,
                                    </br>
                                    the simplest model will be chosen as best model.
                                    ''')
                        ui.table.from_pandas(data_stat.round(4)).classes(replace='text-align: center').props('flat').style('width:300px')
            ui.table.from_pandas(best_summary.round(4)).classes(replace='text-align: center').props('flat').style('width:350px')
            ui.plotly(model)

    def show_plot(trend: str):
        #trend is 'lin' or 'quad'
        label, name = ('Linear', 'lin') if trend == 'lin' else ('Quadratic', 'quad')
        update_name_button(dpbutton, f'{label} model')

        model = show_model(df, means,
                           line_means=results[f'line_{kind}_{name}'],
                           line_raw=results[f'line_{kind}_{name}_raw'],
                           model=label,
                           equation=results[f'equation_{name}'],
                           r_squared=results[f'r_squared_{name}'])
        residuals = residual_graph(means, model=results[f'{kind}_{name}'], trend=label)
        qqplot = q_qplot(model=results[f'{kind}_{name}_raw'], df=df)
        info, shap = shapiro_wilk(model=results[f'{kind}_{name}_raw'])

        params = ['Intercept', 'x', 'x²'] if name == 'quad' else ['Intercept', 'x']
        summary = pd.DataFrame({
            'Params': params,
            'Params value': results[f'{kind}_{name}'].params,
            'pvalue': results[f'{kind}_{name}'].pvalues,
        })

        with plot:
            plot.clear()
            ui.markdown(f'### {label} Model')
            with ui.row():
                ui.table.from_pandas(summary.round(4)).classes(replace='text-align: center').style('width: 400px').props('flat')
                ui.space()
                table_shap = ui.table.from_pandas(shap.round(4), title='Shapiro-Wilk test on residuals').classes(replace='text-align: center').style('width: 400px').props('flat')
                table_shap.add_slot('body-cell-pvalue', '''
                    <q-td key="pvalue" :props="props">
                    <q-badge :color="props.value < 0.05 ? 'red' : 'green'">
                    {{ props.value }}
                    </q-badge>
                    </q-td>
                    ''')
                with ui.card(align_items='center').style('background-color:#84fa84').classes('top-padding: 50px'):
                    ui.icon('info')
                    ui.markdown(f'**{info}**')
            ui.plotly(model)
            with ui.row():
                ui.plotly(residuals)
                kde_resid(model=results[f'{kind}_{name}_raw'], trend=label)
            ui.plotly(qqplot)

    with theme.frame('Linearity'):
        ui.markdown('## **Calibration study**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        if df is not None:
            with ui.card():
                with ui.grid(columns=2):
                    ui.table.from_pandas(display_df(df), pagination=5, title=app.storage.user['name']).classes(replace='text-align: center').props('flat')
                    means = means_data(df)
                    cal_plot = make_biplot(df, means)
                    ui.timer(0, callback=waiting, once=True)

            #HETEROSCEDASTICITY TESTING
            ui.separator().props("color=black size=1px").style('width: 85vw')
            ui.markdown('## _Heteroscedasticy testing_')
            with ui.card():
                with ui.tabs() as tabs:
                    ui.tab('L', label='Levene Test')
                    ui.tab('F', label='F-test ULOQ LLOQ')
                    ui.tab('W', 'Weight selection')
                with ui.tab_panels(tabs, value='L').style('min-height: 400px; width: 900px'):
                    with ui.tab_panel('L'):
                        levene, outcome_levene = levene_test(df)
                        app.storage.user['sced_test'] = outcome_levene
                        ui.table.from_pandas(levene, title='Levene test').classes(replace='text-align: center').props('flat')
                    with ui.tab_panel('F'):
                        f_sced = f_test_sced(df)
                        app.storage.user['f_sced'] = f_sced.iloc[0,1]
                        graph_uloq_lloq = uloq_lloq_graph(df)
                        with ui.row():
                            ui.table.from_pandas(f_sced, title='F-test').classes(replace='text-align: center').style('max-height: 200px; max-width: 200px').props('flat')
                            ui.plotly(graph_uloq_lloq)
                    with ui.tab_panel('W'):
                        variance, result, weight = weight_sel(df)
                        if isinstance(variance, pd.DataFrame):
                            app.storage.user['weight_result'] = result
                            with ui.row():
                                ui.table.from_pandas(variance).classes(replace='text-center')
                                with ui.card(align_items=['center']).style('background-color:#84fa84'):
                                    ui.icon('info')
                                    ui.markdown(f'''Minimum variance is obtained with **{result}**,
                                                </br>
                                                hence this will be used as weight in WLS model''')
                        else:
                            with ui.card(align_items=['center']).style('background-color: #84fa84'):
                                ui.icon('info')
                                ui.markdown('Weighting is not needed since data show homoscedasticity')

            #CALIBRATION MODEL
            ui.separator().props("color=black size=1px").style('width: 85vw')
            ui.markdown('## _Calibration model_')
            with ui.card():
                if isinstance(variance, pd.DataFrame):
                    ui.markdown('### _Weighted Least Squares - WLS_')
                    kind = 'wls'
                    results = model_wls(df, means, weight)
                else:
                    ui.markdown('### Ordinary Least Squares - OLS')
                    kind = 'ols'
                    results = model_ols(df, means)

                with ui.dropdown_button('Best calibration model', icon='settings', split=True, auto_close=True) as dpbutton:
                    ui.item('Best calibration model', on_click=best_model).props(add='clickable = True')
                    ui.item('Linear model', on_click=lambda: show_plot('lin')).props(add='clickable = True')
                    ui.item('Quadratic model', on_click=lambda: show_plot('quad')).props(add='clickable = True')
                with ui.element('div') as plot:
                    best_model()
