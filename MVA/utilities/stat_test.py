import pandas as pd
import numpy as np
import warnings
from scikit_posthocs import posthoc_tukey
from statannotations.Annotator import Annotator
from nicegui import ui, app
from typing import Literal, Optional
from utilities.pd_utilities import comb_intra, gen_combinations, means_data, group_days
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper
from statsmodels.formula.api import ols, wls





def grouping(df: pd.DataFrame):
    #Groupby calibrators
    groups = {}
    n = df['Calibrator'].nunique()
    for i in range(1, n+1):
        group = df.loc[df['Calibrator'] == i, 'y'].values
        if len(group) > 0:
            groups[i] = group
    return groups


def levene_test(df: pd.DataFrame):
    #Levene test for heteroscedasticity
        groups = grouping(df)
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        res = stats.levene(*groups.values(), center='mean')
        warnings.filterwarnings("default", category=RuntimeWarning)
        if np.isnan(res.statistic) or np.isnan(res.pvalue):
            outcome = 'Homoscedastic'
        elif isinstance(res.statistic, np.float64) and np.isinf(res.statistic):
            outcome = 'Homoscedastic'
        else:
            if res.pvalue <= 0.05:
                outcome = 'Heteroscedastic'
            elif res.pvalue > 0.05:
                outcome = 'Homoscedastic'
    
        levenedf = {'p-value':[round(res.pvalue, 4)],'Outcome':[outcome]}
        levenedf = pd.DataFrame(levenedf)       
        return levenedf, outcome


def f_test_sced(df: pd.DataFrame):
    #F-test for heteroscedasticity
    groups = grouping(df)
    LLOQ = min(groups.keys())
    ULOQ = max(groups.keys())
    if groups[LLOQ].var() == 0:
        p = 1
    else:
        f = groups[ULOQ].var()/groups[LLOQ].var() 
        dfn = groups[ULOQ].size-1  
        dfd = groups[LLOQ].size-1  
        p = 1-stats.f.cdf(f, dfn, dfd)
    if p <= 0.05:
        outcome_f = 'Heteroscedastic'
    elif p > 0.05:
        outcome_f = 'Homoscedastic'
    
    if not np.isfinite(p):
        ui.notify('The input data is constant. The F-test may not be valid.', type='warning')
    
    f_df = {'p-value':[round(p,4)],'Outcome':[outcome_f]}
    f_df = pd.DataFrame(f_df)

    return f_df        
    

def weight_sel(df: pd.DataFrame):
    #Variance evaluation for weight selection
    if app.storage.user['sced_test'] == 'Heteroscedastic':
        df['W_no_weight'] = df['x']
        df['W_1/x'] = 1/df['x']
        df['W_1/x2'] = 1/(df['x']**2)
        weights = df.iloc[:,-3:].reset_index(drop=True).drop_duplicates().reset_index(drop=True)
        Sum_no_weight = np.sqrt(weights['W_no_weight']).sum()
        Sum_1_x = np.sqrt(weights['W_1/x']).sum()
        Sum_1_x2 = np.sqrt(weights['W_1/x2']).sum()
        var=df.groupby('x')['y'].var().values
        weights['V_no_weight'] = var * (weights['W_no_weight']/(Sum_no_weight)**2)
        weights['V_1_x'] = var * (weights['W_1/x']/(Sum_1_x)**2)
        weights['V_1_x2'] = var * (weights['W_1/x2']/(Sum_1_x2)**2)
        variance=weights[['V_no_weight','V_1_x','V_1_x2']].var()
        weight_min_var = variance.idxmin()
        variance = pd.DataFrame(variance, columns=['Variance value'])
        variance.rename(index={'V_no_weight':'No weight', 
                               'V_1_x':'1/x',
                                'V_1_x2':'1/x\u00b2'}, inplace=True)
        variance['Weight type'] = variance.index 
        variance['Variance value'] = variance['Variance value'].apply(lambda val: "{:.2e}".format(val) if pd.notnull(val) else val)
        if weight_min_var == 'V_no_weight':
            weight = weights['W_no_weight']
            result = 'No weight'
        elif weight_min_var == 'V_1_x':
            weight = weights['W_1/x']
            result = '1/x'
        elif weight_min_var == 'V_1_x2':
            weight = weights['W_1/x2']
            result = '1/x\u00b2'

        if weight.isin([0]).any().any():
            weight = weights['W_no_weight']
            result = 'No weight'

        variance = pd.DataFrame(variance)
        
        rep = df['Calibrator'].value_counts()
        weight_df = np.repeat(weight, rep)
        weight_df.index = df.index
        df['Weight'] = weight_df
    
    elif app.storage.user['sced_test'] == 'Homoscedastic':
        variance = ''
        result = ''
        weight = ''

    return variance, result, weight
        
def kde(x):
    #Compute KDE with default parameters
    kde = sm.nonparametric.KDEUnivariate(x).fit()
    return kde

def shapiro_wilk(model):
    #Perform Shapiro-Wilk test on model residuals
    stat, pval = stats.shapiro(model.wresid)
    if pval < 0.05:
        info = 'Residuals don\'t follow normal distribution'
    elif pval > 0.05: 
        info = 'Residuals follow normal distribution'
    
    shapiro_data = pd.DataFrame({'Test statistic': [stat],
                                 'pvalue' : [pval]})
    
    return info, shapiro_data

def f_test(group1, group2):
    f = np.var(group1, ddof=1)/np.var(group2, ddof=1)
    nun = group1.size-1
    dun = group2.size-1
    p_value = 1-stats.f.cdf(f, nun, dun)
    return p_value



def mandel_test(lin_mod, quad_mod):
    S_q = quad_mod.ssr/quad_mod.df_resid
    S_l = lin_mod.ssr/lin_mod.df_resid 
    F_mandel = ((lin_mod.nobs-2)*S_l - (quad_mod.nobs-3)*S_q)/S_q
    F_critic = stats.f.ppf(q=1-0.05, dfn = 1, dfd=quad_mod.df_resid)

    if F_mandel > F_critic:
        result = 'Quadratic'
    
    elif F_mandel < F_critic:
        result = 'Linear'

    mandel_summary = pd.DataFrame({
        'F-Mandel' : [F_mandel],
        'F-critic' : [F_critic],
        'Result': [f'Best model is {result}']
    })

    return result, mandel_summary

def double_check(lin_mod, quad_mod):
    t_test = stats.ttest_rel(lin_mod.wresid, quad_mod.wresid)
    ftest = f_test(lin_mod.wresid, quad_mod.wresid)

    if t_test.pvalue > 0.01 and ftest > 0.01:
        result = 'Linear'
        data_stat = pd.DataFrame({
                't-test pvalue' : [t_test.pvalue],
                'F-test pvalue' : [ftest]
            })
    else:
        result = None
        data_stat = None
        
    return result, data_stat

def model_wls(df:pd.DataFrame, means: pd.DataFrame, weight: pd.Series):
    #WLS model
    up = (max(means.x))+(max(means.x)-min(means.x))
    extended_x = np.linspace(-0.5, up, 10)

    wls_lin_means = wls(formula = 'y ~ x',data=means, weights=weight).fit()
    wls_lin_raw = wls(formula='y ~ x', data=df, weights=df['Weight']).fit()
    line_wls_lin_means = wls_lin_means.params['Intercept'] + wls_lin_means.params['x']*means.x
    line_wls_lin_raw = wls_lin_raw.params['Intercept'] + wls_lin_raw.params['x']*extended_x
    equation_lin = f"y = {wls_lin_means.params['Intercept']:.4f} + {wls_lin_means.params['x']:.4f}x"
    r_squared_lin = f"R\u00b2: {wls_lin_means.rsquared:.4f}"
    

    wls_quad_means = wls(formula='y ~ x + I(x**2)', data=means, weights=weight).fit()
    wls_quad_raw = wls(formula='y ~ x + I(x**2)', data=df, weights=df['Weight']).fit()
    line_wls_quad_means = wls_quad_means.params['Intercept'] + wls_quad_means.params['x']*means.x + wls_quad_means.params['I(x ** 2)']*((means.x)**2)
    line_wls_quad_raw = wls_quad_raw.params['Intercept'] + wls_quad_raw.params['x']*extended_x + wls_quad_means.params['I(x ** 2)']*((extended_x)**2)
    equation_quad = f"y = {wls_quad_means.params['Intercept']:.4f} + {wls_quad_means.params['x']:.4f}x + {wls_quad_means.params['I(x ** 2)']:.4f}x\u00b2"
    r_squared_quad = f"R\u00b2: {wls_quad_means.rsquared:.4f}"


    
    return {
        'wls_lin' : wls_lin_means,
        'wls_lin_raw' : wls_lin_raw,
        'line_wls_lin' : line_wls_lin_means,
        'line_wls_lin_raw' : line_wls_lin_raw,
        'equation_lin' : equation_lin,
        'r_squared_lin' : r_squared_lin,
        'wls_quad' : wls_quad_means,
        'wls_quad_raw' : wls_quad_raw,
        'line_wls_quad' : line_wls_quad_means,
        'line_wls_quad_raw' : line_wls_quad_raw,
        'equation_quad' : equation_quad,
        'r_squared_quad' : r_squared_quad
    }


def model_ols(df:pd.DataFrame, means: pd.DataFrame):
    #OLS model
    up = (max(means.x))+(max(means.x)-min(means.x))
    extended_x = np.linspace(-0.5, up, 10)

    ols_lin_means = ols(formula = 'y ~ x',data=means).fit()
    ols_lin_raw = ols(formula='y ~ x', data=df).fit()
    line_ols_lin_means = ols_lin_means.params['Intercept'] + ols_lin_means.params['x']*means.x
    line_ols_lin_raw = ols_lin_raw.params['Intercept'] + ols_lin_raw.params['x']*extended_x
    equation_lin = f"y = {ols_lin_means.params['Intercept']:.4f} + {ols_lin_means.params['x']:.4f}x"
    r_squared_lin = f"R\u00b2: {ols_lin_means.rsquared:.4f}"
    

    ols_quad_means = ols(formula='y ~ x + I(x**2)', data=means).fit()
    ols_quad_raw = ols(formula='y ~ x + I(x**2)', data=df).fit()
    line_ols_quad_means = ols_quad_means.params['Intercept'] + ols_quad_means.params['x']*means.x + ols_quad_means.params['I(x ** 2)']*((means.x)**2)
    line_ols_quad_raw = ols_quad_raw.params['Intercept'] + ols_quad_raw.params['x']*extended_x + ols_quad_means.params['I(x ** 2)']*((extended_x)**2)
    equation_quad = f"y = {ols_quad_means.params['Intercept']:.4f} + {ols_quad_means.params['x']:.4f}x + {ols_quad_means.params['I(x ** 2)']:.4f}x\u00b2"
    r_squared_quad = f"R\u00b2: {ols_quad_means.rsquared:.4f}"


    
    return {
        'ols_lin' : ols_lin_means,
        'ols_lin_raw' : ols_lin_raw,
        'line_ols_lin' : line_ols_lin_means,
        'line_ols_lin_raw' : line_ols_lin_raw,
        'equation_lin' : equation_lin,
        'r_squared_lin' : r_squared_lin,
        'ols_quad' : ols_quad_means,
        'ols_quad_raw' : ols_quad_raw,
        'line_ols_quad' : line_ols_quad_means,
        'line_ols_quad_raw' : line_ols_quad_raw,
        'equation_quad' : equation_quad,
        'r_squared_quad' : r_squared_quad
    }


def hub_vox(ncal:int, conf:float, df:pd.DataFrame, means:pd.DataFrame, result_weight:str):
    #Hubaux and Vos algorithm:
    input_istd = app.storage.user['istd_conc']       

    if result_weight == 'No weight':
        n_weights = (df.x[df['Calibrator']<=ncal]*input_istd)
        s_wi = np.sum(means.x[:ncal]*input_istd)
        a = means.x[:ncal]*input_istd
    elif result_weight == '1/x':
        n_weights = 1/((df.x[df['Calibrator']<=ncal]*input_istd))
        s_wi = np.sum(1/((means.x[:ncal]*input_istd)))
        a = (1/((means.x[:ncal]*input_istd)))
    elif result_weight == '':
        n_weights = np.ones(len(df.x[df['Calibrator']<=ncal]*input_istd))
        s_wi = np.sum(means.x[:ncal]*input_istd)
        a = means.x[:ncal]*input_istd
    elif result_weight == '1/x²':
        n_weights = 1/((df.x[df['Calibrator']<=ncal]*input_istd)**2)
        s_wi = np.sum(1/((means.x[:ncal]*input_istd)**2))
        a = (1/((means.x[:ncal]*input_istd)**2))

    w_i_x_i = n_weights*(df.iloc[:,1][df['Calibrator']<=ncal])
    x_w = (np.sum(w_i_x_i))/np.sum(n_weights)
    regr = ols(formula='y ~ x',data=df[df['Calibrator']<=ncal]).fit()
    S_y_x = np.sqrt(np.sum((regr.resid**2)*n_weights)/regr.df_resid)
    s_term = 1/(s_wi)*ncal
    b = np.sum((a*(means.x[:ncal] - (x_w*input_istd))**2))*ncal
    t_term = ((-x_w)**2)/b
    rad = np.sqrt(1+s_term+t_term)
    s_y0 = S_y_x*rad
    t = stats.t.ppf(1-conf, regr.df_resid)
    x_lod = (t * s_y0)/regr.params['x'] * input_istd
    x_loq = x_lod * 2

    return x_lod, x_loq



def precision_routine(df: pd.DataFrame, n_days: int, type:Literal['intra', 'inter'], num: Optional[int]=None):
    #Calculate precision (intra and inter) executing the previous linearity routine
    group_days(df, n_days)
    combos = comb_intra(df, n_days)
    if type == 'intra':
        cal = combos[num]['Alpha'].unique().tolist()
        id_col = 'Alpha'
    else:
        cal = df['Day'].unique().tolist()
        id_col = 'Day'
    combinations = gen_combinations(cal)
    prediction = []
    for combination, missing in combinations:
        new_data = df[df[f'{id_col}'].isin(combination)]
        y_val = df[df[f'{id_col}'].isin([missing])].y
        levendedf, outcome= levene_test(df=new_data)
        app.storage.user['sced_test'] = outcome
        variance, result, weight = weight_sel(new_data)
        means_combo = means_data(new_data)
        if isinstance(variance, pd.DataFrame):
            wls_results = model_wls(new_data, means_combo, weight)
            mandel, mandel_summary = mandel_test(wls_results['wls_lin'], wls_results['wls_quad'])
            if mandel == 'Linear':
                model = wls_results['wls_lin']
                x_pred = np.abs((y_val - model.params['Intercept'])/model.params['x'])

            elif mandel == 'Quadratic':
                model = wls_results['wls_quad']
                delta = ((model.params['x'])**2) - (4*model.params['I(x ** 2)']*(model.params['Intercept']-y_val))
                delta = abs(delta)
                x_pred = np.abs((-model.params['x']+np.sqrt(delta))/(2*model.params['I(x ** 2)']))


        else:
            ols_results = model_ols(new_data, means_combo)
            mandel, mandel_summary = mandel_test(ols_results['ols_lin'], ols_results['ols_quad'])
        

            
            if mandel == 'Linear':
                model = ols_results['ols_lin']
                x_pred = np.abs((y_val - model.params['Intercept'])/model.params['x'])


            elif mandel == 'Quadratic':
                model = ols_results['ols_quad']
                delta = ((model.params['x'])**2) - (4*model.params['I(x ** 2)']*(model.params['Intercept']-y_val))
                delta = abs(delta)
                x_pred = np.abs((-model.params['x']+np.sqrt(delta))/(2*model.params['I(x ** 2)']))

        
        
        
    
        
        
        if type == 'inter':
            istd_conc = app.storage.user['istd_conc']
            prediction.append(x_pred)
            pred = pd.DataFrame(prediction)
            pred = pred.T
            pred['Alpha'] = df['Alpha']
            names = pred['Alpha'].unique().tolist()
            dfs = [x for _, x in pred.groupby('Alpha')[['y', 'Alpha']]]
            columns=[]
            for i in range(len(dfs)):
                dfs[i].reset_index(drop=True, inplace=True)
                dfs[i].dropna(axis=1,inplace=True)
                dfs[i]['y'] = dfs[i]['y']*istd_conc
                col = dfs[i]['y'].rename(f'{names[i]}')
                columns.append(col)
            pred = pd.concat(columns, axis=1)
            pred['CV%'] = (pred.std(axis=1)/pred.mean(axis=1)) * 100
        else:
            prediction.append(x_pred.values)
            pred = pd.DataFrame(prediction)
            pred = pred.T
            pred[f'CV Day {num+1}%'] = (pred.std(axis=1)/pred.mean(axis=1)) * 100
        

    return pred




def accuracy_routine(df: pd.DataFrame, n_days: int, type:Literal['intra', 'inter'], num: Optional[int]=None):
    #Calculate precision (intra and inter) executing the previous linearity routine
    group_days(df, n_days)
    combos = comb_intra(df, n_days)
    if type == 'intra':
        cal = combos[num]['Alpha'].unique().tolist()
        id_col = 'Alpha'
    else:
        cal = df['Day'].unique().tolist()
        id_col = 'Day'
    combinations = gen_combinations(cal)
    prediction = []
    for combination, missing in combinations:
        new_data = df[df[f'{id_col}'].isin(combination)]
        y_val = df[df[f'{id_col}'].isin([missing])].y
        levendedf, outcome= levene_test(df=new_data)
        app.storage.user['sced_test'] = outcome
        variance, result, weight = weight_sel(new_data)
        means_combo = means_data(new_data)
        if isinstance(variance, pd.DataFrame):
            wls_results = model_wls(new_data, means_combo, weight)
            mandel, mandel_summary = mandel_test(wls_results['wls_lin'], wls_results['wls_quad'])
            if mandel == 'Linear':
                model = wls_results['wls_lin']
                x_pred = np.abs((y_val - model.params['Intercept'])/model.params['x'])

            elif mandel == 'Quadratic':
                model = wls_results['wls_quad']
                delta = ((model.params['x'])**2) - (4*model.params['I(x ** 2)']*(model.params['Intercept']-y_val))
                delta = abs(delta)
                x_pred = np.abs((-model.params['x']+np.sqrt(delta))/(2*model.params['I(x ** 2)']))


        else:
            ols_results = model_ols(new_data, means_combo)
            mandel, mandel_summary = mandel_test(ols_results['ols_lin'], ols_results['ols_quad'])
        

            
            if mandel == 'Linear':
                model = ols_results['ols_lin']
                x_pred = np.abs((y_val - model.params['Intercept'])/model.params['x'])


            elif mandel == 'Quadratic':
                model = ols_results['ols_quad']
                delta = ((model.params['x'])**2) - (4*model.params['I(x ** 2)']*(model.params['Intercept']-y_val))
                delta = abs(delta)
                x_pred = np.abs((-model.params['x']+np.sqrt(delta))/(2*model.params['I(x ** 2)']))

        
        
        
    
        
        istd_conc = app.storage.user['istd_conc']
        if type == 'inter':
            
            prediction.append(abs(x_pred))
            pred = pd.DataFrame(prediction)
            pred = pred.T
            pred['Alpha'] = df['Alpha']
            names = pred['Alpha'].unique().tolist()
            dfs = [x for _, x in pred.groupby('Alpha')[['y', 'Alpha']]]
            columns=[]
            for i in range(len(dfs)):
                dfs[i].reset_index(drop=True, inplace=True)
                dfs[i].dropna(axis=1,inplace=True)
                dfs[i]['y'] = dfs[i]['y']*istd_conc
                col = dfs[i]['y'].rename(f'{names[i]}')
                columns.append(col)
            pred = pd.concat(columns, axis=1)
            pred['Mean'] = pred.mean(axis=1)
            pred['Concentration'] = ((means_combo.x) * istd_conc).values
            pred['bias%'] = (1-(pred['Concentration']/pred['Mean'])) * 100
            pop = pred.pop('Concentration')
            pred.insert(0, 'Concentration', pop)
            pred.drop(columns=['Mean'], inplace=True)
        else:
            prediction.append(abs(x_pred.values))
            pred = pd.DataFrame(prediction)
            pred = pred.T
            pred = pred * istd_conc
            pred['Mean'] = pred.mean(axis=1)
            pred['Concentration'] = ((means_combo.x)*istd_conc).values
            pred[f'bias Day {num+1}%'] = (1-(pred['Concentration']/pred['Mean'])) * 100
            pred.drop(columns=['Mean', 'Concentration'], inplace=True)
        

    return pred         




