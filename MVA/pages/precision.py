import theme
import pandas as pd
from utilities.pd_utilities import means_data, curves_per_day, count_curves
from utilities.stat_test import precision_routine
from nicegui import ui, app, events


def enough_curves(df, days: int, what: str):
    #Intra-day leave-one-out drops one curve and fits the model on the rest,
    #so a day holding a single curve leaves nothing to fit.
    per_day = curves_per_day(df, days)
    if per_day.min() < 2:
        ui.notify(f'Intra-day {what} needs at least two calibration curves per day. '
                  f'{df["Alpha"].nunique()} curves spread over {days} days leaves a day with {per_day.min()}.',
                  type='warning', position='center', timeout=0, close_button='OK')
        return False
    return True


def help_func():
    #Show info about precision routine
    ui.html('<style>.multi-line-notification { white-space: pre-line; font-weight: bold;}</style>')
    ui.notify('Precision is evaluated on all calibration points using backcalculation. \n'
                'Backcalculation is performed with a leave-one-out method, iterated over every fold. \n'
                'Intra-day precision leaves out one curve at a time: the model is built on the remaining \n'
                'curves of the same day, and the left-out curve is predicted. The CV% is then computed \n'
                'across the curves of that day, level by level. \n'
                'Inter-day precision leaves out one whole day at a time: the model is built on the curves \n'
                'of the remaining days, and every curve of the left-out day is predicted. The CV% is then \n'
                'computed across all the curves of the validation, level by level.'
                ,position='center', timeout=0, multi_line=True, close_button='OK', type='warning' ,classes='multi-line-notification')


def blocked(container, msg: str, what: str):
    #A wrong number of days silently regroups the curves and yields plausible but wrong
    #numbers, biased towards passing. Refusing to compute is safer than reporting them.
    with container:
        with ui.card(align_items='center').style('background-color: #E97451; max-width: 600px'):
            ui.icon('error')
            ui.markdown(f'**{msg}**')
            ui.markdown(f'{what.capitalize()} is not computed until the declared design '
                        'matches the dataset.')


def design_mismatch(curves, days):
    #Nothing is derived from the declared design, the grouping comes from the number of
    #days alone, so the two inputs are only cross-checked against the dataset.
    #Returns the complaint, or None when the design is consistent or not yet declared.
    total = app.storage.user.get('n_curves')
    if total is None or not curves or not days:
        return None
    curves, days = int(curves), int(days)
    declared = curves * days
    if declared != total:
        return f'{curves} curves x {days} days = {declared}, but the dataset holds {total} curves.'
    return None


def warn_mismatch(curves, days):
    msg = design_mismatch(curves, days)
    if msg:
        ui.notify(msg, position='center', type='warning', timeout=0, close_button='OK')


def handle_warning(e: events.ValueChangeEventArguments):
    #Fires on the 'curves for each day' field.
    if e.value is None:
        return
    curves = int(e.value)

    if curves < 1:
        ui.notify('At least one calibration curve per day is needed.',
                  position='center', type='warning', timeout=0, close_button='OK')
        return

    if curves == 1:
        ui.notify('A single curve per day leaves nothing to fit once leave-one-out drops it, '
                  'so intra-day precision and accuracy cannot be computed.',
                  position='center', type='warning', timeout=0, close_button='OK')
    elif curves == 2:
        ui.notify('With two curves per day, leave-one-out builds the model on a single curve. '
                  'Within-level variance is then undefined, so heteroscedasticity cannot be tested '
                  'intra-day and OLS is used by default.',
                  position='center', type='warning', timeout=0, close_button='OK')

    warn_mismatch(curves, app.storage.user.get('days'))


def handle_days(e: events.ValueChangeEventArguments):
    #Fires on the 'days of validation' field. Reading days off the event rather than
    #storage: bind_value_to has not necessarily propagated by the time this runs.
    warn_mismatch(app.storage.user.get('curves_per_day'), e.value)


def precision():
    #The dataframe, the tables and the sliders are locals of this page function, and the
    #handlers below close over them. As module globals they were one shared set for the whole
    #process, so a second user opening this page rebound the first user's dataframe and tables.
    try:
        df = pd.read_json(app.storage.user['df'])
        means = means_data(df)
        app.storage.user['n_curves'] = count_curves(df)
    except:
        df = None
        ui.notify('Data not found', type='negative', position='center')

    def intra_day():
        #Display intraday table
        intra_day_table.clear()
        CVs = []
        days = app.storage.user.get('days')
        if days is None:
            return
        days = int(days)
        if not enough_curves(df, days, 'precision'):
            return
        for i in range(days):
            CV = precision_routine(df=df, n_days=days, type='intra', num=i)
            CVs.append(CV.iloc[:, -1])

        istd_conc = app.storage.user['istd_conc']

        CV_global = pd.concat(CVs, axis=1).round(2)
        CV_global['CV mean %'] = CV_global.mean(axis=1).round(2)
        CV_global['Concentration'] = (means['x']*istd_conc).values
        pop = CV_global.pop('Concentration')
        CV_global.insert(0, 'Concentration', pop)
        with intra_day_table:
            table = ui.table.from_pandas(CV_global.round(2), title='Intra-day precision')
            table.classes(replace='text-align: center')
            table.style('border: 1px solid #9ec239')
            table.add_slot('body-cell-CV mean %', '''
            <q-td key="CV mean %" :props="props">
            <q-badge :color="Math.abs(props.value) < '''f'{max_opt.value}' '''? 'green' : (props.value <'''f'{max_acpt.value}'''' ? 'yellow' : 'red')">
            {{ props.value }}
            </q-badge>
            </q-td>
            ''')

    def inter_day():
        #Display interday table
        inter_day_table.clear()
        days = app.storage.user.get('days')
        if days is None:
            return
        days = int(days)
        istd_conc = app.storage.user['istd_conc']
        if days != 1:
            CV_inter = precision_routine(df, days, 'inter')

            CV_inter['Concentration'] = (means['x']*istd_conc).values
            pop = CV_inter.pop('Concentration')
            CV_inter.insert(0, 'Concentration', pop)
            with inter_day_table:
                tab_inter = ui.table.from_pandas(CV_inter.round(2), title='Inter-day precision')
                tab_inter.classes(replace='text-align: center')
                tab_inter.style('border: 1px solid #9ec239')
                tab_inter.add_slot('body-cell-CV%', '''
                <q-td key="CV%" :props="props">
                <q-badge :color="Math.abs(props.value) < '''f'{max_opt.value}' '''? 'green' : (props.value <'''f'{max_acpt.value}'''' ? 'yellow' : 'red')">
                {{ props.value }}
                </q-badge>
                </q-td>
                ''')
        elif days == 1:
            ui.notify('Not enough days to evaluate interday precision! Only intra-day precision will be evaluated.', position='center', type='warning',  timeout=0, close_button='OK')

    def intra_inter():
        #Handle on-change values to set acceptability criteria
        days = app.storage.user.get('days')
        if days is None:
            return
        msg = design_mismatch(app.storage.user.get('curves_per_day'), days)
        if msg:
            intra_day_table.clear()
            inter_day_table.clear()
            blocked(intra_day_table, msg, 'precision')
            return
        intra_day()
        inter_day()

    with theme.frame('Precision'):
        ui.markdown('## **Precision**')
        ui.separator().props("color=black size=2px").style('width: 85vw')
        if df is not None:
            with ui.row():
                ui.button(icon='help', on_click=help_func).props('flat').tooltip('How we calculate precision?')
                ui.number('Number of curves for each day', precision=0, on_change=handle_warning) \
                    .bind_value(app.storage.user, 'curves_per_day').style('width: 300px')
                ui.element('div').style('width: 50px; visibility: hidden;')
                sel_days = ui.number(label='Days of validation',value=None, precision=0).bind_value_to(app.storage.user, 'days').style('width: 200px').on_value_change(intra_inter)
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
