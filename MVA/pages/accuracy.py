from nicegui import ui, app, events
from utilities.pd_utilities import means_data, count_curves
from utilities.stat_test import accuracy_routine
from pages.precision import handle_warning, handle_days, enough_curves, design_mismatch, blocked
import pandas as pd
import theme


def help_func():
    ui.html('<style>.multi-line-notification { white-space: pre-line; font-weight: bold;}</style>')
    ui.notify('Accuracy is evaluated on all calibration points using backcalculation. \n'
                'Backcalculation is performed with a leave-one-out method, iterated over every fold. \n'
                'Intra-day accuracy leaves out one curve at a time: the model is built on the remaining \n'
                'curves of the same day, and the left-out curve is predicted. The bias% is then computed \n'
                'from the mean of the curves of that day, level by level. \n'
                'Inter-day accuracy leaves out one whole day at a time: the model is built on the curves \n'
                'of the remaining days, and every curve of the left-out day is predicted. The bias% is then \n'
                'computed from the mean of all the curves of the validation, level by level.'
                ,position='center', timeout=0, multi_line=True, close_button='OK', type='warning' ,classes='multi-line-notification')


def accuracy():
    try:
        df = pd.read_json(app.storage.user['df'])
        means = means_data(df)
        app.storage.user['n_curves'] = count_curves(df)
    except:
        df = None

    def intra_day():
        intra_day_table.clear()
        CVs = []
        days = app.storage.user.get('days')
        if days is None:
            return
        days = int(days)
        if not enough_curves(df, days, 'accuracy'):
            return
        for i in range(days):
            CV = accuracy_routine(df=df, n_days=days, type='intra', num=i)
            CVs.append(CV.iloc[:, -1])

        istd_conc = app.storage.user['istd_conc']

        CV_global = pd.concat(CVs, axis=1).round(2)
        CV_global['bias mean %'] = CV_global.mean(axis=1).round(2)
        CV_global['Concentration'] = (means['x']*istd_conc).values
        pop = CV_global.pop('Concentration')
        CV_global.insert(0, 'Concentration', pop)
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
        inter_day_table.clear()
        days = app.storage.user.get('days')
        if days is None:
            return
        days = int(days)
        if days != 1:
            CV_inter = accuracy_routine(df, days, 'inter')
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

    def intra_inter():
        days = app.storage.user.get('days')
        if days is None:
            return
        msg = design_mismatch(app.storage.user.get('curves_per_day'), days)
        if msg:
            intra_day_table.clear()
            inter_day_table.clear()
            blocked(intra_day_table, msg, 'accuracy')
            return
        intra_day()
        inter_day()

    with theme.frame('Accuracy'):
        ui.markdown('## **Accuracy**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        if df is not None:
            with ui.row():
                ui.button(icon='help', on_click=help_func).props('flat').tooltip('How we calculate accuracy?')
                ui.number('Number of curves for each day', precision=0, on_change=handle_warning) \
                    .bind_value(app.storage.user, 'curves_per_day').style('width: 300px')
                ui.element('div').style('width: 50px; visibility: hidden;')
                sel_days = ui.number(label='Days of validation', precision=0).bind_value(app.storage.user, 'days').style('width: 200px').on_value_change(intra_inter)
                sel_days.on_value_change(handle_days)
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
            #Render straight away when the design is already in storage: bind_value prefills the
            #fields but does not fire on_value_change, so nothing would compute otherwise.
            intra_inter()
        else:
            theme.data_required_prompt()
