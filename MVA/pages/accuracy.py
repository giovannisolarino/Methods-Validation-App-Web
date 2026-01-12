from nicegui import ui, app, events
from utilities.pd_utilities import means_data
from utilities.stat_test import accuracy_routine
from pages.precision import handle_warning
import pandas as pd
import theme



def intra_day():
    #Display intraday table
    intra_day_table.clear()
    CVs = []
    days = int(app.storage.user['days'])
    for i in range(days):
        CV = accuracy_routine(df=df,n_days=days,type='intra',num=i)
        last_column = CV.iloc[:,-1]
        CVs.append(last_column)

    istd_conc = app.storage.user['istd_conc']

    CV_global = pd.concat(CVs, axis=1).round(2)
    CV_global['bias mean %'] = CV_global.mean(axis=1).round(2)
    CV_global['Concentration'] = (means['x']*istd_conc).values
    pop = CV_global.pop('Concentration')
    CV_global.insert(0, 'Concentration', pop)
    CV_global.to_json('./.nicegui/accuracy_intra.json')
    with intra_day_table:
        table = ui.table.from_pandas(CV_global.round(2), title='Intra-day accuracy')
        table.classes(replace='text-align: center')
        table.style('border: 1px solid #9ec239')
        table.add_slot('body-cell-bias mean %', '''
            <q-td key="bias mean %" :props="props">
            <q-badge :color="Math.abs(props.value) < '''f'{max_opt.value}' '''? 'green' : (props.value <'''f'{max_acpt.value}'''' ? 'yellow' : 'red')">
            {{ props.value }}
            </q-badge>
            </q-td>
            ''')
        
def inter_day():
    #Display interday table
    inter_day_table.clear()
    days = int(app.storage.user['days'])
    istd_conc = app.storage.user['istd_conc']
    if days is not None and days != 1:
        CV_inter = accuracy_routine(df, days,'inter')
        CV_inter.to_json('./.nicegui/accuracy_inter.json')
        with inter_day_table:
            tab_inter = ui.table.from_pandas(CV_inter.round(2), title='Inter-day accuracy')
            tab_inter.classes(replace='text-align: center')
            tab_inter.style('border: 1px solid #9ec239')
            tab_inter.add_slot('body-cell-bias%', '''
            <q-td key="bias%" :props="props">
            <q-badge :color="Math.abs(props.value) < '''f'{max_opt.value}' '''? 'green' : (props.value <'''f'{max_acpt.value}'''' ? 'yellow' : 'red')">
            {{ props.value }}
            </q-badge>
            </q-td>
            ''')
    elif days == 1:
        ui.notify('Not enough days to evaluate interday accuracy! Only intra-day accuracy will be evaluated.', position='center', type='warning',  timeout=0, close_button='OK')


def help_func():
    #Show info about precision routine
    ui.html('<style>.multi-line-notification { white-space: pre-line; font-weight: bold;}</style>')
    ui.notify('Accuracy is evaluated on all calibration points using backcalculation. \n'
                'Backcalculation is performed with a leave-one-out method,\n'
                'where n-1 curves are used to build the model, and the remaining curve is used for prediction. \n'
                'The process is iterated over all possible combinations. For intraday precision, \n' 
                'only the curves obtained on the same day are used, while for interday precision, the iteration includes curves obtained on different days.'
                ,position='center', timeout=0, multi_line=True, close_button='OK', type='warning' ,classes='multi-line-notification')


def intra_inter():
    days = int(app.storage.user['days'])
    if days is not None:    
        intra_day()
        inter_day()







def accuracy():
    global df, intra_day_table, max_opt, max_acpt, means, inter_day_table
    try:
        df = pd.read_json(app.storage.user['df'])
        means = means_data(df)
        conc_name = app.storage.user['conc_name']
    except:
        df = None
        ui.notify('Data not found', type='negative', position='center')
    with theme.frame('Accuracy'):
        ui.markdown('## **Accuracy**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        if df is not None:
            with ui.row():
                ui.button(icon='help', on_click=help_func).props('flat').tooltip('How we calculate accuracy?')
                ui.number('Number of curves for each day', precision=0, on_change=handle_warning).style('width: 300px')
                ui.element('div').style('width: 50px; visibility: hidden;')
                sel_days = ui.number(label='Days of validation',value=None, precision=0).bind_value_to(app.storage.user, 'days').style('width: 200px').on_value_change(intra_inter)
                sel_days.tooltip('Make sure that the same number of curves was obtained on each day')
                ui.element('div').style('width: 50px; visibility: hidden;')
                with ui.expansion('Personalize your acceptability criteria!', icon='settings_suggest').style('border:1px solid black; width: 350px'):
                    with ui.column():
                        ui.label('Max optimal value (green values)')
                        ui.element('div').style('height: 20px; visibility: hidden;')
                        max_opt = ui.slider(min=0, max=30, step=1, value=20, on_change=intra_inter).props('label-always')
                        ui.separator().props("color=black size=1px")
                        ui.label('Max acceptable value (yellow values)')
                        ui.element('div').style('height: 20px; visibility: hidden;')
                        max_acpt = ui.slider(min=0, max=30, step=1, value=25, on_change=intra_inter).props('label-always')
                
            intra_day_table = ui.element('div').style('width: 600px; height: 500px')
            ui.separator().props("color=black size=1px")
            inter_day_table = ui.element('div').style('width: 1000px; height: 600px')
            ui.separator().props("color=black size=1px")

            