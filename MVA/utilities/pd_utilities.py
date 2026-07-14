import string
import pandas as pd
import numpy as np
from io import BytesIO
from nicegui import ui, app
pd.options.mode.chained_assignment = None


def letters(number):
    '''
    Convert numbers (from 1 to 26) in uppercase letters.

    Params:
        number: list of numbers to convert

    Returns:
        Uppercase numbers 
    '''
    if 1 <= number <= 26:
        return string.ascii_uppercase[number - 1]



def normalize(df: pd.DataFrame, selected_col: list, istd_conc):
    '''
    Set alphanumeric index to Pandas DataFrame and normalize analyte's areas and concentrations by ISTD's areas a nd concentrations.
    Add two new columns x and y for normalized concentrations and areas

    Params:
        df: Pandas Dataframe
        selected_col: list of columns selected by user through frontend
        istd_conc: ISTD's concentration
    
    Returns:
        Normalized DataFrame
    '''

    conc_col = f'{selected_col[0]}'

    df.dropna(inplace=True)
    df['Alpha'] = df.groupby(conc_col).cumcount().astype(int) + 1
    df['Alpha'] = df['Alpha'].apply(letters).astype(str)

    #Number the levels by ascending concentration rather than by order of appearance in the
    #file. Everything downstream assumes calibrator 1 is the LLOQ and calibrator k the ULOQ
    #(the F-test on the extremes, Hubaux and Vos), and means_data() reads the levels back
    #sorted by x, so the numbering has to agree with the concentration order.
    levels = {conc: i for i, conc in enumerate(np.sort(df[conc_col].unique()), start=1)}
    df['Level'] = df[conc_col].map(levels)
    df['Num'] = df['Level'].astype(str)
    df['Points'] = df['Num'] + df['Alpha']

    df = df.filter(['Points', 'Level', 'Alpha', conc_col, f'{selected_col[1]}', f'{selected_col[2]}'])
    df.dropna(inplace=True)

    #Sort on (level, curve) as numbers, not on the 'Points' label. 'Points' is a string, so
    #sorting it directly orders '10A' before '2A' and scrambles the levels as soon as there
    #are ten or more of them, while the routines downstream pair rows with concentrations
    #positionally.
    df.sort_values(by=['Level', 'Alpha'], inplace=True)
    df.drop(columns=['Level', 'Alpha'], inplace=True)

    df.set_index(df.columns[0], inplace=True)
    df.index.name = None
    df['ID'] = df.index
    df = df[['ID', f'{selected_col[0]}', f'{selected_col[1]}', f'{selected_col[2]}']]
    df['x'] = df[f'{selected_col[0]}']/istd_conc
    df['y'] = (df[f'{selected_col[1]}'].astype(float))/(df[f'{selected_col[2]}'].astype(float))

    #Signals and the response ratio keep full precision here. Rounding them to a
    #readable number of digits is display_df()'s job, not the data model's.
    return df


def display_df(df: pd.DataFrame, exclude: tuple = ('ID', 'x', 'Calibrator', 'Weight')):
    '''
    Return a copy of a DataFrame with the signal columns rendered in scientific
    notation, for on-screen tables only. The original keeps full precision.

    Params:
        df: Pandas DataFrame
        exclude: columns to leave untouched, on top of the concentration column

    Returns:
        Formatted copy of the DataFrame
    '''

    out = df.copy()
    skip = set(exclude) | {app.storage.user.get('conc_name')}
    for col in out.select_dtypes(include=[np.number]).columns:
        if col not in skip:
            out[col] = out[col].apply(lambda val: "{:.2e}".format(val) if pd.notnull(val) else val)
    return out

def means_data(df: pd.DataFrame):
    '''
    Create a new Pandas DataFrame containing means data

    Params:
        df: Pandas DataFrame

    Returns:
        New Pandas DataFrame
    '''

    df['Calibrator'] = df.index.astype(str).str.split(r'\D+').str[0].astype(int)
    means = df.groupby('x')['y'].mean().reset_index()
    means = pd.DataFrame(means)
    means.index = np.arange(1, len(means) + 1)
    return means

def group_days(df: pd.DataFrame, days: int):
    '''
    Create a 'Days' column to existing DataFrame to group calibrators by day.

    Params:
        df: Pandas DataFrame
        days: number of validation's days
    
    Returns:
        Modified Pandas DataFrame
    '''

    conc_name = app.storage.user['conc_name']
    df['Alpha'] = df.groupby(f'{conc_name}').cumcount().astype(int) + 1
    df['Alpha'] = df['Alpha'].apply(letters).astype(str)
    uniques_cal = sorted(df['Alpha'].unique())

    #Splitting the curves into exactly `days` groups. Deriving a group size with
    #ceil() instead produces fewer groups than asked whenever days does not divide
    #the number of curves (9 curves over 4 days gives 3 groups, not 4).
    if days > len(uniques_cal):
        ui.notify(f'{days} days requested but only {len(uniques_cal)} calibration curves are available: '
                  f'using {len(uniques_cal)} days.', type='warning', position='center', timeout=0, close_button='OK')
        days = len(uniques_cal)

    map_groups = {}
    for group_number, group in enumerate(np.array_split(uniques_cal, days), start=1):
        for letter in group:
            map_groups[letter] = group_number

    df['Day'] = df['Alpha'].map(map_groups)

    return df


def count_curves(df: pd.DataFrame):
    '''
    Count the calibration curves in a dataset, i.e. how many times each
    concentration level was replicated.

    Params:
        df: Pandas DataFrame

    Returns:
        Number of curves
    '''

    conc_name = app.storage.user['conc_name']
    return int(df.groupby(f'{conc_name}').size().max())


def curves_per_day(df: pd.DataFrame, days: int):
    '''
    Count the distinct calibration curves assigned to each validation day.

    Params:
        df: Pandas DataFrame
        days: number of validation's days

    Returns:
        Pandas Series indexed by day
    '''

    return group_days(df, days).groupby('Day')['Alpha'].nunique()


def gen_combinations(units: list):
    '''
    Generate the folds of the leave-one-out method.

    The unit left out is a curve (letters, intra-day) or a whole day (numbers, inter-day),
    depending on what the caller passes in.

    Params:
        units: list of the units to iterate over, i.e. curve letters or day numbers

    Returns:
        List of (kept units, left-out unit) pairs, one per fold
    '''

    combinations = []
    for i in range(len(units)):
        combination = units[:i] + units[i+1:]
        missing_element = units[i]
        combinations.append((combination, missing_element))
    return combinations

def comb_intra(df: pd.DataFrame, n_days: int):
    '''
    Separate Pandas DataFrame in multiple DataFrames each with curves obtained in one day.

    Params:
        df: Pandas DataFrame
        n_days: number of validation's days

    Returns:
        List of DataFrames
    '''

    days = df.groupby(['Day'])
    df_day = []
    for i, day in enumerate(days.groups.keys()):
        if i >= n_days:
            break
        df_day.append(days.get_group((day)))
    return df_day


def template_xlsx(levels: int, replicates: int, columns: tuple):
    '''
    Build an empty excel template as bytes, ready to hand straight to ui.download.

    Returning bytes rather than writing to a fixed path under .nicegui/: on a shared server
    two users generating a template at the same time would otherwise overwrite each other's
    file and download the wrong one.

    Params:
        levels: number of different concentration's levels (2 or 3)
        replicates: number of replicates for each level
        columns: the two data column headers, e.g. ('Matrix', 'No-Matrix')

    Returns:
        The .xlsx file as bytes
    '''

    names = ['low', 'medium', 'high'] if levels == 3 else ['low', 'high']
    lev = [name for name in names for _ in range(replicates)]

    template = pd.DataFrame({
        'Levels': lev,
        columns[0]: [None]*(levels*replicates),
        columns[1]: [None]*(levels*replicates),
    })

    buffer = BytesIO()
    template.to_excel(buffer, index=False)
    return buffer.getvalue()


def tables_xlsx(sheets: dict):
    '''
    Write one or more DataFrames to an excel workbook and return it as bytes.

    Params:
        sheets: mapping of sheet name to DataFrame

    Returns:
        The .xlsx file as bytes
    '''

    buffer = BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        for sheet, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet, index=False)
    return buffer.getvalue()




def matrix_effect(df: pd.DataFrame):
    df['Matrix Effect %'] = (df['Matrix']/df['No-Matrix'] * 100).round(2)
    complete = pd.DataFrame(df.groupby('Levels')['Matrix Effect %'].mean())
    complete['Levels'] = complete.index
    pop = complete.pop('Levels')
    complete.insert(0, 'Levels', pop)
    complete['Ion Suppression %'] = complete['Matrix Effect %'] - 100
    df['Ion Suppression %'] = df['Matrix Effect %'] - 100


    return df, complete





def recovery_calc(df: pd.DataFrame):
    df['Recovery %'] = (df['Before']/df['After'] * 100).round(2)
    complete = pd.DataFrame(df.groupby('Levels')['Recovery %'].mean())
    complete['Levels'] = complete.index
    pop = complete.pop('Levels')
    complete.insert(0, 'Levels', pop)
    
    return df, complete


