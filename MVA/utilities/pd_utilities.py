import string
import math
import pandas as pd
import numpy as np
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

    df.dropna(inplace=True)
    df['Alpha'] = df.groupby(f'{selected_col[0]}').cumcount().astype(int) + 1
    df['Alpha'] = df['Alpha'].apply(letters).astype(str)
    a = np.array(df[f'{selected_col[0]}'].unique())
    a = list(enumerate(a, start=1))
    df['Num'] = df[f'{selected_col[0]}'].apply(lambda x: next((indice for indice, valore in a if valore == x), np.nan)).astype(str)
    df['Points'] = df['Num'] + df['Alpha']
    df = df.filter(['Points',f'{selected_col[0]}',f'{selected_col[1]}', f'{selected_col[2]}'])
    df.dropna(inplace=True)
    df.sort_values(by=['Points'], inplace=True)
    numeric_columns = df.select_dtypes(include=[np.number]).columns.drop(df.columns[1])
    df[numeric_columns] = df[numeric_columns].apply(lambda x: x.apply(lambda val: "{:.2e}".format(val) if pd.notnull(val) else val))
    df.set_index(df.columns[0], inplace=True)
    df.index.name = None
    df['ID'] = df.index
    df = df[['ID', f'{selected_col[0]}', f'{selected_col[1]}', f'{selected_col[2]}']]
    df['x'] = df[f'{selected_col[0]}']/istd_conc
    df['y'] = (df[f'{selected_col[1]}'].astype(float))/(df[f'{selected_col[2]}'].astype(float))
    df['y'] = df['y'].apply(lambda val: "{:.2e}".format(val) if pd.notnull(val) else val)
    
    return df

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
    dim_groups = math.ceil(len(uniques_cal) / days)
    map_groups = {}
    for i, letter in enumerate(uniques_cal):
        group_number = (i // dim_groups) + 1
        map_groups[letter] = group_number

    df['Day'] = df['Alpha'].map(map_groups)

    return df


def gen_combinations(curves: list):
    '''
    Generate combinations between curves to perform leave-one-out method.

    Params:
        curves: list of curves named with letters
    
        Returns:
            List of all possible combinations and the excluded curve in each combination 
    '''

    combinations = []
    for i in range(len(curves)):
        combination = curves[:i] + curves[i+1:]
        missing_element = curves[i]
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


def mat_eff_gen(levels:int, replicates:int):
    '''
    Generate Matrix effect excell template.

    Parmas:
        levels: number of different concentration's levels
        replicates: number of replicates for each level

    Returns:
        Path in which excell file was generated
    '''
    if levels == 2:
        lev = ['low']*replicates + ['high'] * replicates
    elif levels == 3:
        lev = ['low']*replicates + ['medium'] * replicates + ['high'] * replicates
    
    mat_eff = pd.DataFrame({
        'Levels':lev,
        'Matrix': [None]*(levels*replicates),
        'No-Matrix': [None]*(levels*replicates),
    })

    path = "./.nicegui/matrix_effect_template.xlsx"
    mat_eff.to_excel(path, index=False)

    return path


def rec_gen(levels:int, replicates:int):
    '''
    Generate recovery excell template.

    Parmas:
        levels: number of different concentration's levels
        replicates: number of replicates for each level

    Returns:
        Path in which excell file was generated
    '''
    if levels == 2:
        lev = ['low']*replicates + ['high'] * replicates
    elif levels == 3:
        lev = ['low']*replicates + ['medium'] * replicates + ['high'] * replicates
    
    mat_eff = pd.DataFrame({
        'Levels':lev,
        'Before': [None]*(levels*replicates),
        'After': [None]*(levels*replicates),
    })

    path = "./.nicegui/recovery_template.xlsx"
    mat_eff.to_excel(path, index=False)

    return path




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


