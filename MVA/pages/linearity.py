import theme
import asyncio
import os
import pandas as pd
from datetime import date
from utilities.os_utilities import create_documents_directory
from utilities.pd_utilities import means_data
from utilities.plotly_utilities import make_biplot, uloq_lloq_graph, show_model, residual_graph, kde_resid, q_qplot
from utilities.stat_test import (levene_test, f_test_sced, weight_sel, model_wls, model_ols,
                                 shapiro_wilk, mandel_test, double_check)
from nicegui import ui, app
import statsmodels.api as sm

async def waiting():
    with ui.row() as spin_row:
        ui.spinner(size='lg')
        ui.label("Processing graph...").classes('text-bold')
    await asyncio.sleep(2)
    ui.plotly(cal_plot)
    spin_row.delete()

    






def update_name_button(button: ui.dropdown_button, new_text: str):
    button.set_text(new_text)





def best_wls_model():
    global best
    #Perform Mandel-Test and show best WLS model
    update_name_button(dpbutton, 'Best calibration model')
    mandel, mandel_summary = mandel_test(wls_results['wls_lin_raw'], wls_results['wls_quad_raw'])
    data_stat = None
    if mandel == 'Quadratic':
        result, data_stat = double_check(wls_results['wls_lin_raw'], wls_results['wls_quad_raw'])
        best_summary = pd.DataFrame({
                                    'Params' : ['Intercept', 'x', 'x\u00b2'],
                                    'Params value' : wls_results['wls_quad'].params,
                                    'pvalue' : wls_results['wls_quad'].pvalues
                                    })
        best_model = show_model(df, means,
                        line_means=wls_results['line_wls_quad'],
                        line_raw= wls_results['line_wls_quad_raw'],
                        model = 'Quadratic',
                        equation = wls_results['equation_quad'],
                        r_squared=wls_results['r_squared_quad'])
        best = wls_results['wls_quad']
        
        
        
        
        if result == 'Linear':
            best_summary = pd.DataFrame({
                                    'Params' : ['Intercept', 'x'],
                                    'Params value':wls_results['wls_lin'].params,
                                    'pvalue' : wls_results['wls_lin'].pvalues
                                    })
            best_model = show_model(df, means,                                          
                        line_means=wls_results['line_wls_lin'],
                        line_raw=wls_results['line_wls_lin_raw'],
                        model='Linear',
                        equation=wls_results['equation_lin'],
                        r_squared=wls_results['r_squared_lin'])
            best = wls_results['wls_lin']    


    elif mandel == 'Linear':
        best_summary = pd.DataFrame({
                                    'Params' : ['Intercept', 'x'],
                                    'Params value':wls_results['wls_lin'].params,
                                    'pvalue' : wls_results['wls_lin'].pvalues
                                    })
        best_model = show_model(df, means,                                          
                        line_means=wls_results['line_wls_lin'],
                        line_raw=wls_results['line_wls_lin_raw'],
                        model='Linear',
                        equation=wls_results['equation_lin'],
                        r_squared=wls_results['r_squared_lin'])
        best = wls_results['wls_lin']
                            
        
    with plot:
        plot.clear()
        ui.markdown('### Best Model')
        with ui.row():
            ui.table.from_pandas(mandel_summary.round(2), title='Mandel test').classes(replace='text-align: center').props('flat').style('width:350px')
            ui.element('div').style('width: 300px; visibility: hidden;')
            if data_stat is not None:
                with ui.card(align_items='center').tooltip('Additional t-test anf F-test to compare models\' residuals (\u03B1 = 0.01)'):
                    ui.markdown('#### Double check on residuals')
                    ui.icon('info')
                    ui.markdown('''Since models\' residuals are statistically identical,
                                </br>
                                the simplest model will be chosen as best model.
                                ''')
                    ui.table.from_pandas(data_stat.round(4)).classes(replace='text-align: center').props('flat').style('width:300px')
        ui.table.from_pandas(best_summary.round(4)).classes(replace='text-align: center').props('flat').style('width:350px')
        ui.plotly(best_model)



def best_ols_model():
    global best
    #Perform Mandel-Test and show best OLS model
    update_name_button(dpbutton, 'Best calibration model')
    mandel, mandel_summary = mandel_test(ols_results['ols_lin_raw'], ols_results['ols_quad_raw'])
    data_stat = None
    if mandel == 'Quadratic':
        result, data_stat = double_check(ols_results['ols_lin_raw'], ols_results['ols_quad_raw'])
        best_summary = pd.DataFrame({
                                    'Params' : ['Intercept', 'x', 'x\u00b2'],
                                    'Params value' : ols_results['ols_quad'].params,
                                    'pvalue' : ols_results['ols_quad'].pvalues
                                    })
        best_model = show_model(df, means,
                        line_means=ols_results['line_ols_quad'],
                        line_raw= ols_results['line_ols_quad_raw'],
                        model = 'Quadratic',
                        equation = ols_results['equation_quad'],
                        r_squared=ols_results['r_squared_quad'])
        best = ols_results['ols_quad']
 
        
        
        
        if result == 'Linear':
            best_summary = pd.DataFrame({
                                    'Params' : ['Intercept', 'x'],
                                    'Params value':ols_results['ols_lin'].params,
                                    'pvalue' : ols_results['ols_lin'].pvalues
                                    })
            best_model = show_model(df, means,                                          
                        line_means=ols_results['line_ols_lin'],
                        line_raw=ols_results['line_ols_lin_raw'],
                        model='Linear',
                        equation=ols_results['equation_lin'],
                        r_squared=ols_results['r_squared_lin'])
            best = ols_results['ols_lin']
              


    elif mandel == 'Linear':
        best_summary = pd.DataFrame({
                                    'Params' : ['Intercept', 'x'],
                                    'Params value':ols_results['ols_lin'].params,
                                    'pvalue' : ols_results['ols_lin'].pvalues
                                    })
        best_model = show_model(df, means,                                          
                        line_means=ols_results['line_ols_lin'],
                        line_raw=ols_results['line_ols_lin_raw'],
                        model='Linear',
                        equation=ols_results['equation_lin'],
                        r_squared=ols_results['r_squared_lin'])
        best = ols_results['ols_lin']


                         
        
    with plot:
        plot.clear()
        ui.markdown('### Best Model')
        with ui.row():
            ui.table.from_pandas(mandel_summary.round(2), title='Mandel test').classes(replace='text-align: center').props('flat').style('width:350px')
            ui.element('div').style('width: 300px; visibility: hidden;')
            if data_stat is not None:
                with ui.card(align_items='center').tooltip('Additional t-test anf F-test to compare models\' residuals (\u03B1 = 0.01)'):
                    ui.markdown('#### Double check on residuals')
                    ui.icon('info')
                    ui.markdown('''Since models\' residuals are statistically identical,
                                </br>
                                the simplest model will be chosen as best model.
                                ''')
                    ui.table.from_pandas(data_stat.round(4)).classes(replace='text-align: center').props('flat').style('width:300px')
        ui.table.from_pandas(best_summary.round(4)).classes(replace='text-align: center').props('flat').style('width:350px')
        ui.plotly(best_model)






def show_wls_plot(type:str):
        #WLS PLOT
        if type == 'lin':
            update_name_button(dpbutton, 'Linear model')
            model = show_model(df, means,                                          
                        line_means=wls_results['line_wls_lin'],
                        line_raw=wls_results['line_wls_lin_raw'],
                        model='Linear',
                        equation=wls_results['equation_lin'],
                        r_squared=wls_results['r_squared_lin'])
            residuals = residual_graph(means, model=wls_results['wls_lin'], trend='Linear')
            qqplot = q_qplot(model=wls_results['wls_lin_raw'], df=df)
            info, shap = shapiro_wilk(model=wls_results['wls_lin_raw'])

            

            with plot:
                plot.clear()
                ui.markdown('### Linear Model')
                summary = pd.DataFrame({
                    'Params' : ['Intercept', 'x'],
                    'Params value':wls_results['wls_lin'].params,
                    'pvalue' : wls_results['wls_lin'].pvalues
                    
                })
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
                    kde_resid(model=wls_results['wls_lin_raw'], trend='Linear')
                ui.plotly(qqplot)
                
                
                

        elif type == 'quad':
            update_name_button(dpbutton, 'Quadratic model')
            model = show_model(df, means,
                        line_means=wls_results['line_wls_quad'],
                        line_raw= wls_results['line_wls_quad_raw'],
                        model = 'Quadratic',
                        equation = wls_results['equation_quad'],
                        r_squared=wls_results['r_squared_quad'])
            residuals = residual_graph(means, model=wls_results['wls_lin'], trend='Quadratic')
            qqplot = q_qplot(model=wls_results['wls_quad_raw'], df=df)
            info, shap = shapiro_wilk(model=wls_results['wls_quad_raw'])
        
            with plot:
                plot.clear()
                ui.markdown('### Quadratic Model')
                summary = pd.DataFrame({
                    'Params' : ['Intercept', 'x', 'x\u00b2'],
                    'Params value' : wls_results['wls_quad'].params,
                    'pvalue' : wls_results['wls_quad'].pvalues
                })
                with ui.row():
                    ui.table.from_pandas(summary.round(4)).classes(replace='text-align: center').style('width: 400px').props('flat')
                    ui.space()
                    table_shap=ui.table.from_pandas(shap.round(4), title='Shapiro-Wilk test on residuals').classes(replace='text-align: center').style('width: 400px').props('flat')
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
                    kde_resid(model=wls_results['wls_quad_raw'], trend='Quadratic')
                ui.plotly(qqplot)





def show_ols_plot(type:str):
        #OLS PLOT
        if type == 'lin':
            update_name_button(dpbutton, 'Linear model')
            model = show_model(df, means,                                          
                        line_means=ols_results['line_ols_lin'],
                        line_raw=ols_results['line_ols_lin_raw'],
                        model='Linear',
                        equation=ols_results['equation_lin'],
                        r_squared=ols_results['r_squared_lin'])
            residuals = residual_graph(means, model=ols_results['ols_lin'], trend='Linear')
            qqplot = q_qplot(model=ols_results['ols_lin_raw'], df=df)
            info, shap = shapiro_wilk(model=ols_results['ols_lin_raw'])

            

            with plot:
                plot.clear()
                ui.markdown('### Linear Model')
                summary = pd.DataFrame({
                    'Params' : ['Intercept', 'x'],
                    'Params value':ols_results['ols_lin'].params,
                    'pvalue' : ols_results['ols_lin'].pvalues
                    
                })
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
                    kde_resid(model=ols_results['ols_lin_raw'], trend='Linear')
                ui.plotly(qqplot)
                
                
                

        elif type == 'quad':
            update_name_button(dpbutton, 'Quadratic model')
            model = show_model(df, means,
                        line_means=ols_results['line_ols_quad'],
                        line_raw= ols_results['line_ols_quad_raw'],
                        model = 'Quadratic',
                        equation = ols_results['equation_quad'],
                        r_squared=ols_results['r_squared_quad'])
            residuals = residual_graph(means, model=ols_results['ols_lin'], trend='Quadratic')
            qqplot = q_qplot(model=ols_results['ols_quad_raw'], df=df)
            info, shap = shapiro_wilk(model=ols_results['ols_quad_raw'])
        
            with plot:
                plot.clear()
                ui.markdown('### Quadratic Model')
                summary = pd.DataFrame({
                    'Params' : ['Intercept', 'x', 'x\u00b2'],
                    'Params value' : ols_results['ols_quad'].params,
                    'pvalue' : ols_results['ols_quad'].pvalues
                })
                with ui.row():
                    ui.table.from_pandas(summary.round(4)).classes(replace='text-align: center').style('width: 400px').props('flat')
                    ui.space()
                    table_shap=ui.table.from_pandas(shap.round(4), title='Shapiro-Wilk test on residuals').classes(replace='text-align: center').style('width: 400px').props('flat')
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
                    kde_resid(model=ols_results['ols_quad_raw'], trend='Quadratic')
                ui.plotly(qqplot)
                


        



def linearity():

    global df, cal_plot, plot, means, wls_results, ols_results, dpbutton, save_btn
    try:
        df = pd.read_json(app.storage.user['df'])
    except:
        df = None
        ui.notify('Data not found', type='negative', position='center')
    with theme.frame('Linearity'):
        ui.markdown('## **Calibration study**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        if df is not None:
            with ui.card():
                with ui.grid(columns=2):
                        ui.table.from_pandas(df, pagination=5, title=app.storage.user['name']).classes(replace='text-align: center').props('flat')
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
                    wls_results = model_wls(df, means, weight)
                    with ui.dropdown_button('Best calibration model', icon='settings', split=True, auto_close=True) as dpbutton:
                        ui.item('Best calibration model', on_click=best_wls_model).props(add='clickable = True')
                        ui.item('Linear model', on_click=lambda: show_wls_plot(type='lin')).props(add='clickable = True')
                        ui.item('Quadratic model', on_click=lambda: show_wls_plot(type='quad')).props(add='clickable = True')
                    with ui.element('div') as plot:
                        best_wls_model()
                else:
                    ui.markdown('### Ordinary Least Squares - OLS')
                    ols_results = model_ols(df, means)
                    with ui.dropdown_button('Best calibration model', icon='settings', split=True, auto_close=True) as dpbutton:
                        ui.item('Best calibration model', on_click=best_ols_model).props(add='clickable = True')
                        ui.item('Linear model', on_click=lambda: show_ols_plot(type='lin')).props(add='clickable = True')
                        ui.item('Quadratic model', on_click=lambda: show_ols_plot(type='quad')).props(add='clickable = True')
                    with ui.element('div') as plot:
                        best_ols_model()
            
                
            
                



                        
                    
                    
                        
                    






    
