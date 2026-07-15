import pandas as pd
import numpy as np
import warnings
from nicegui import ui, app
from typing import Literal, Optional
from utilities.pd_utilities import comb_intra, gen_combinations, means_data, group_days
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.formula.api import ols, wls





def grouping(df: pd.DataFrame):
    groups = {}
    n = df['Calibrator'].nunique()
    for i in range(1, n+1):
        group = df.loc[df['Calibrator'] == i, 'y'].values
        if len(group) > 0:
            groups[i] = group
    return groups


def levene_test(df: pd.DataFrame):
        groups = grouping(df)

        if not groups:
            raise ValueError('No calibration data left to test: the leave-one-out training set is empty.')

        #A single replicate per level leaves the within-level variance undefined, so fall back
        #to OLS explicitly rather than leaning on scipy returning NaN.
        if min(len(group) for group in groups.values()) < 2:
            return pd.DataFrame({'p-value': [np.nan], 'Outcome': ['Homoscedastic']}), 'Homoscedastic'

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
    groups = grouping(df)
    LLOQ = min(groups.keys())
    ULOQ = max(groups.keys())
    #ddof=1: numpy's default ddof=0 only cancels out of the ratio when the two levels carry
    #the same number of replicates.
    var_lloq = groups[LLOQ].var(ddof=1)
    if var_lloq == 0:
        p = 1
    else:
        f = groups[ULOQ].var(ddof=1)/var_lloq
        dfn = groups[ULOQ].size-1
        dfd = groups[LLOQ].size-1
        p = 1-stats.f.cdf(f, dfn, dfd)

    if not np.isfinite(p):
        ui.notify('The input data is constant. The F-test may not be valid.', type='warning')
        outcome_f = 'Homoscedastic'
    elif p <= 0.05:
        outcome_f = 'Heteroscedastic'
    else:
        outcome_f = 'Homoscedastic'

    f_df = {'p-value':[round(p,4)],'Outcome':[outcome_f]}
    f_df = pd.DataFrame(f_df)

    return f_df        
    

def weight_sel(df: pd.DataFrame):
    if app.storage.user['sced_test'] == 'Heteroscedastic':
        #Sorted by x so the levels line up with the groupby('x') variances below.
        x_levels = np.sort(df['x'].unique())
        weights = pd.DataFrame({
            'W_no_weight': np.ones(len(x_levels)),
            'W_1/x': 1/x_levels,
            'W_1/x2': 1/(x_levels**2),
        })
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

        if weight.isin([0]).any():
            weight = weights['W_no_weight']
            result = 'No weight'

        variance = pd.DataFrame(variance)

        #Map by concentration, not positionally: unbalanced designs would otherwise put
        #weights on the wrong rows.
        df['Weight'] = df['x'].map(pd.Series(weight.values, index=x_levels))
    
    elif app.storage.user['sced_test'] == 'Homoscedastic':
        variance = ''
        result = ''
        weight = ''

    return variance, result, weight
        
def kde(x):
    kde = sm.nonparametric.KDEUnivariate(x).fit()
    return kde

def shapiro_wilk(model):
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

    #On a tie the quadratic term brings no significant improvement, so keep the simpler model.
    result = 'Quadratic' if F_mandel > F_critic else 'Linear'

    #Not the final verdict: double_check() can still overturn it downstream.
    mandel_summary = pd.DataFrame({
        'F-Mandel' : [F_mandel],
        'F-critic' : [F_critic],
        'Mandel outcome': [f'{result}']
    })

    return result, mandel_summary

def double_check(lin_mod, quad_mod):
    #Paired on the ABSOLUTE residuals. On the signed ones the test is vacuous: both fits carry an
    #intercept, so both residual sets sum to zero and the paired test returns t = 0, p = 1 always.
    t_test = stats.ttest_rel(np.abs(lin_mod.wresid), np.abs(quad_mod.wresid))
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

def select_model(results: dict, kind: Literal['wls', 'ols']):
    #Mandel's test runs on the models fitted to the raw points, n = k*l, as in Eq. (3) of Alladio
    #et al.; on the level means instead it leaves 2 residual dof and a different F-critic.
    #Returns (verdict, Mandel's summary, the double check's numbers when the override fired).
    mandel, summary = mandel_test(results[f'{kind}_lin_raw'], results[f'{kind}_quad_raw'])
    data_stat = None
    if mandel == 'Quadratic':
        fallback, data_stat = double_check(results[f'{kind}_lin_raw'], results[f'{kind}_quad_raw'])
        if fallback == 'Linear':
            mandel = 'Linear'
    return mandel, summary, data_stat


def curve_grids(means: pd.DataFrame, n: int = 200):
    #The x grids the fitted lines are evaluated on: means_x spans the calibration range,
    #extended_x extrapolates past the ULOQ. show_model() plots against these same grids, so
    #both sides stay on one definition.
    up = (max(means.x))+(max(means.x)-min(means.x))
    return np.linspace(min(means.x), max(means.x), n), np.linspace(-0.5, up, n)


def model_wls(df:pd.DataFrame, means: pd.DataFrame, weight: pd.Series):
    means_x, extended_x = curve_grids(means)

    #Hand patsy only the columns the formulas name: a user column called I, C or Q shadows the
    #patsy builtin of the same name and breaks I(x**2) below.
    fit_data = df[['x', 'y']]

    wls_lin_means = wls(formula = 'y ~ x',data=means, weights=weight).fit()
    wls_lin_raw = wls(formula='y ~ x', data=fit_data, weights=df['Weight']).fit()
    line_wls_lin_means = wls_lin_means.params['Intercept'] + wls_lin_means.params['x']*means_x
    line_wls_lin_raw = wls_lin_raw.params['Intercept'] + wls_lin_raw.params['x']*extended_x
    equation_lin = f"y = {wls_lin_means.params['Intercept']:.4f} + {wls_lin_means.params['x']:.4f}x"
    #R\u00b2 comes from the raw fit: averaging the replicates away hides the within-level scatter
    #and inflates it.
    r_squared_lin = f"R\u00b2: {wls_lin_raw.rsquared:.4f}"
    

    wls_quad_means = wls(formula='y ~ x + I(x**2)', data=means, weights=weight).fit()
    wls_quad_raw = wls(formula='y ~ x + I(x**2)', data=fit_data, weights=df['Weight']).fit()
    line_wls_quad_means = wls_quad_means.params['Intercept'] + wls_quad_means.params['x']*means_x + wls_quad_means.params['I(x ** 2)']*((means_x)**2)
    line_wls_quad_raw = wls_quad_raw.params['Intercept'] + wls_quad_raw.params['x']*extended_x + wls_quad_raw.params['I(x ** 2)']*((extended_x)**2)
    equation_quad = f"y = {wls_quad_means.params['Intercept']:.4f} + {wls_quad_means.params['x']:.4f}x + {wls_quad_means.params['I(x ** 2)']:.4f}x\u00b2"
    r_squared_quad = f"R\u00b2: {wls_quad_raw.rsquared:.4f}"


    
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
    means_x, extended_x = curve_grids(means)

    #See model_wls.
    fit_data = df[['x', 'y']]

    ols_lin_means = ols(formula = 'y ~ x',data=means).fit()
    ols_lin_raw = ols(formula='y ~ x', data=fit_data).fit()
    line_ols_lin_means = ols_lin_means.params['Intercept'] + ols_lin_means.params['x']*means_x
    line_ols_lin_raw = ols_lin_raw.params['Intercept'] + ols_lin_raw.params['x']*extended_x
    equation_lin = f"y = {ols_lin_means.params['Intercept']:.4f} + {ols_lin_means.params['x']:.4f}x"
    #See model_wls.
    r_squared_lin = f"R\u00b2: {ols_lin_raw.rsquared:.4f}"
    

    ols_quad_means = ols(formula='y ~ x + I(x**2)', data=means).fit()
    ols_quad_raw = ols(formula='y ~ x + I(x**2)', data=fit_data).fit()
    line_ols_quad_means = ols_quad_means.params['Intercept'] + ols_quad_means.params['x']*means_x + ols_quad_means.params['I(x ** 2)']*((means_x)**2)
    line_ols_quad_raw = ols_quad_raw.params['Intercept'] + ols_quad_raw.params['x']*extended_x + ols_quad_raw.params['I(x ** 2)']*((extended_x)**2)
    equation_quad = f"y = {ols_quad_means.params['Intercept']:.4f} + {ols_quad_means.params['x']:.4f}x + {ols_quad_means.params['I(x ** 2)']:.4f}x\u00b2"
    r_squared_quad = f"R\u00b2: {ols_quad_raw.rsquared:.4f}"


    
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
    # Hubaux and Vos algorithm, following Alladio et al., MethodsX 7 (2020) 100919, Eqs (7)-(11).
    # k = ncal levels, l = replicates per level, n = k*l standards. Everything is computed on the
    # NORMALIZED scale (x = conc / C_ISTD) and rescaled to concentration once, at the end.
    input_istd = app.storage.user['istd_conc']
    if not (0 < conf < 0.5):
        raise ValueError(f'conf is the one-sided significance level alpha (e.g. 0.05), got {conf!r}')

    sub   = df[df['Calibrator'] <= ncal]
    x_cal = sub.x
    x_i   = means.x[:ncal]

    # Eq (8) assumes a balanced design: fall back to the most common replicate count when the
    # levels disagree, and say so.
    counts = sub['Calibrator'].value_counts()
    l = int(counts.mode().iat[0])
    if counts.nunique() > 1:
        ui.notify(f'Calibration levels carry different replicate counts {sorted(counts.tolist())}. '
                  f'Hubaux and Vos assumes a balanced design: using l = {l}.',
                  type='warning', position='center', timeout=0, close_button='OK')

    # '' is the homoscedastic case, 'No weight' the heteroscedastic one where the unweighted fit
    # won on variance. Both mean w = 1 everywhere, so the fit below degenerates into OLS.
    if result_weight in ('No weight', ''):
        n_weights = np.ones(len(x_cal))
        a = np.ones(ncal)
    elif result_weight == '1/x':
        n_weights = 1/x_cal
        a = 1/x_i
    elif result_weight == '1/x²':
        n_weights = 1/(x_cal**2)
        a = 1/(x_i**2)
    else:
        raise ValueError(f'Unknown weight type: {result_weight!r}')

    # Make the weights dimensionless, so the standalone 1 in Eq (8) is commensurate with the
    # other two terms and the radical does not depend on the concentration unit.
    n_weights = n_weights/np.mean(n_weights)
    a = a/np.mean(a)

    # Eq (10)
    x_w = np.sum(n_weights*x_cal)/np.sum(n_weights)

    # Eqs (9) and (11): residuals and slope both belong to the weighted curve
    regr = wls(formula='y ~ x', data=sub[['x', 'y']], weights=n_weights).fit()
    S_y_x = np.sqrt(np.sum((regr.resid**2)*n_weights)/regr.df_resid)

    # Eq (8): both sums run over the k levels and carry the l replicates
    s_term = 1/np.sum(l*a)
    t_term = ((-x_w)**2)/np.sum(l*a*(x_i - x_w)**2)
    rad = np.sqrt(1+s_term+t_term)
    s_y0 = S_y_x*rad

    # Eq (7), turned into a concentration through the slope of Eq (11)
    t = stats.t.ppf(1-conf, regr.df_resid)
    x_lod = (t * s_y0)/regr.params['x'] * input_istd
    x_loq = x_lod * 2

    return x_lod, x_loq


def precision_routine(df: pd.DataFrame, n_days: int, type:Literal['intra', 'inter'], num: Optional[int]=None):
    #Backcalculate the calibration points by leave-one-out and express the spread as CV%.
    #'intra' drops one curve of day `num` and refits on the other curves of that day,
    #'inter' drops a whole day and refits on the remaining days.
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
            mandel, _, _ = select_model(wls_results, 'wls')
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
            mandel, _, _ = select_model(ols_results, 'ols')
        

            
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
    #Backcalculate the calibration points by leave-one-out and express the deviation from the
    #spiked concentration as bias%, following Eq. (12) of Alladio et al., MethodsX 7 (2020) 100919.
    #'intra' and 'inter' leave out a curve and a whole day respectively, as in precision_routine.
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
            mandel, _, _ = select_model(wls_results, 'wls')
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
            mandel, _, _ = select_model(ols_results, 'ols')
        

            
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




