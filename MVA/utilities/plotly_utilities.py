import sys
import copy
from nicegui import ui
import matplotlib
if getattr(sys, 'frozen', False):
    matplotlib.use('svg')
import pandas as pd
import numpy as np
import io
from PIL import Image
from typing import Literal, Optional
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

#Deep copy: pio.templates['simple_white'] is the shared built-in.
MVA_TEMPLATE = copy.deepcopy(pio.templates['simple_white'])
MVA_TEMPLATE.layout.font.size = 16                  #legend, hover, anything unspecified
MVA_TEMPLATE.layout.title.font.size = 24
MVA_TEMPLATE.layout.xaxis.title.font.size = 20
MVA_TEMPLATE.layout.yaxis.title.font.size = 20
MVA_TEMPLATE.layout.xaxis.tickfont.size = 16
MVA_TEMPLATE.layout.yaxis.tickfont.size = 16
pio.templates['mva'] = MVA_TEMPLATE
pio.templates.default = 'mva'

#Re-applied inside kde_resid() on every call: plt.style.use() there resets rcParams.
MPL_FONTS = {'font.size': 14, 'axes.titlesize': 18, 'axes.labelsize': 16,
             'xtick.labelsize': 13, 'ytick.labelsize': 13}

#scale=4 on a 1200x800 figure is a 4800x3200 PNG, ~300 dpi at full page width. Without it the
#modebar's camera icon exports at the on-screen pixel size.
PLOT_CONFIG = {
    'displaylogo': False,
    'toImageButtonOptions': {'format': 'png', 'scale': 4, 'filename': 'MVA_plot'},
}


def hd_plot(fig, filename: Optional[str] = None, format: str = 'png'):
    '''
    Render a Plotly figure with the high-resolution download button enabled. Use instead of
    ui.plotly(), which never sets a config, so the modebar exports at its defaults.

    Params:
        fig: Plotly Graph Object Figure
        filename: name of the downloaded file, defaults to the figure title
        format: 'png' for a raster image, 'svg' for a vector one (scale is then irrelevant)

    Returns:
        The ui.plotly element
    '''

    config = copy.deepcopy(PLOT_CONFIG)
    config['toImageButtonOptions']['format'] = format
    title = fig.layout.title.text
    config['toImageButtonOptions']['filename'] = filename or (title.replace(' ', '_') if title else 'MVA_plot')
    return ui.plotly({**fig.to_plotly_json(), 'config': config})
from statsmodels.graphics.gofplots import qqplot
from statsmodels.formula.api import ols, wls

def make_biplot(df: pd.DataFrame, means: pd.DataFrame):
    '''
    Create Plotly Graph Object figure to display raw and mean data.

    Params:
        df: Pandas Dataframe containg raw data
        means: Pandas DataFrame containing mean data

    Returns:
        Plotly Graph Object Figure
    '''
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['x'], y=df['y'], mode='markers',
                marker=dict(symbol='square', color='red', opacity=0.5), name='Data raw'))
    fig.update_traces(hovertemplate='(%{x}, %{y:.2f}) <br>CAL %{text}<extra></extra>', text=df.index)
    fig.add_trace(go.Scatter(x=means['x'], y=means['y'], mode='markers',
                         marker=dict(symbol='circle', color='blue', size=10), name='Data means',hovertemplate='(%{x}, %{y:.2f}) <br>CAL %{text}<extra></extra>', text=means.index))
    fig.update_layout(
            title_text='Calibration plot',
            title_x = 0.5,
            xaxis_title='Concentration ratio',
            yaxis_title='Signal ratio',
            height=400,
            width=600,
            showlegend=True
            )
    fig.update_yaxes(range=[0, max(df.y)+np.mean(np.diff(np.sort(df.y)))])
    return fig

def uloq_lloq_graph(df: pd.DataFrame):
        '''
        Create Plotly Graph Object figure to display ULOQ and LLOQ.

        Params:
            df: Pandas DataFrame with raw data
        
        Returns:
            Plotly Graph Object Figure
        '''
        min_calibrator = df['Calibrator'].min()
        max_calibrator = df['Calibrator'].max()
        min_calibrator = df[df['Calibrator'].isin([min_calibrator])]
        max_calibrator = df[df['Calibrator'].isin([max_calibrator])]
        min_calibrator = pd.DataFrame(min_calibrator)
        max_calibrator = pd.DataFrame(max_calibrator)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=min_calibrator['x'], y=min_calibrator['y'], mode='markers',
                             marker=dict(symbol='square', color='green'), name='LLOQ',hovertemplate='CAL %{text}<extra></extra>', text=min_calibrator.index))
        fig.add_trace(go.Scatter(x=max_calibrator['x'], y=max_calibrator['y'], mode='markers',
                             marker=dict(symbol='triangle-up', color='red'), name='ULOQ',hovertemplate='CAL %{text}<extra></extra>', text=max_calibrator.index))
        fig.update_layout(
            title_text='LLOQ-ULOQ Comparison',
            title_x = 0.5,
            xaxis_title='Concentration ratio',
            yaxis_title='Signal ratio',
            height=400,
            width=600,
            showlegend=True
            )
        return fig

def show_model(df:pd.DataFrame, means:pd.DataFrame, line_means:list, line_raw:list, model: str, equation:str, r_squared: str):
        #The same grids the caller evaluated the two lines on. Recomputing them here would draw
        #the curves against the wrong abscissa as soon as either side changed its grid.
        from utilities.stat_test import curve_grids
        means_x, extended_x = curve_grids(means)
        fig = make_biplot(df, means)
        fig.add_trace(go.Scatter(x=means_x, y=line_means,
                                mode='lines', name=f'{model} data means',
                                line=dict(dash='solid', color='blue')))
        fig.add_trace(go.Scatter(x=extended_x, y=line_raw, mode='lines',
                                name=f'{model} data raw', 
                                line=dict(dash='dot', color='red')))
        
        fig.update_layout(
               title_text= f'Calibration',
               title_x = 0.5,
               height = 800,
               width=1200
        )

        diff = np.diff(df.y)
        fig.update_xaxes(range=[0, max(means.x)+0.5])
        fig.update_yaxes(range=[0, max(df.y)+np.mean(diff)])


        fig.add_annotation(
               x=0.9,
               xref='paper',
               yref='paper',
               text=f'<b>{equation}<b>',
               showarrow=False,
               align='left',
               font=dict(size=20)
        )

        fig.add_annotation(
               x=0.9,
               y=0.45,
               xref='paper',
               yref='paper',
               text=f'<b>{r_squared}<b>',
               showarrow=False,
               align='left',
               font=dict(size=20, color='red')
        )

        return fig  
        
def residual_graph(means: pd.DataFrame, model, trend:str):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=means['x'], y = model.wresid, mode='markers', marker=dict(size=10),
                                hovertemplate='CAL %{text}<extra></extra>', text=means.index))
        fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='Black')
        fig.update_layout(
        title_text=f'{trend} model residuals',
        title_x = 0.4,
        xaxis_title='Concentration ratio',
        yaxis_title='Residuals',    
        height=400,
        width=550,
        showlegend=False
        )
        return fig

def kde_resid(model, trend:str):
        from utilities.stat_test import kde
        kde = kde(x=model.wresid)
        with ui.pyplot().style('width:500px').classes('top-padding: 40px'):
               plt.style.use('seaborn-white')
               plt.rcParams.update(MPL_FONTS)
               plt.plot(kde.support, kde.density)
               plt.xlabel('Residuals')
               plt.ylabel('Density')
               plt.title(f"KDE {trend} model residuals")


def q_qplot(model, df:pd.DataFrame):
        qqplot_data = qqplot(model.wresid, line='s').gca().lines

        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=qqplot_data[0].get_xdata(), y=qqplot_data[0].get_ydata(), mode='markers',
                marker=dict(symbol='square', color='blue', opacity=0.5), name='Residual Quantiles',
                hovertemplate='CAL %{text}<extra></extra>', text=df.index))
        fig.add_trace(go.Scatter(x=qqplot_data[1].get_xdata(),y=qqplot_data[1].get_ydata(), mode='lines', 
                name=f'Theoretical distribution', line=dict(dash='solid', color='red')))
               
        fig.update_layout(
                title_text='Q-Q Plot',
                title_x = 0.4,
                xaxis_title='Theoretical Quantiles',
                yaxis_title='Sample Quantiles',    
                height=600,
                width=800,
                showlegend=True
        )
        return fig






def conf_lm(conf, df:pd.DataFrame,ncal ,weight:Optional[any]=None):
        df = df.iloc[:ncal]

        #The prediction band is a hyperbola in x, so it needs a dense abscissa: drawn only through
        #the calibration levels it becomes straight segments, flattening the waist of the band at
        #x = 0, where the LOD is read off.
        grid = np.linspace(0, max(df.x), 200)
        exog = pd.DataFrame({'x': grid})

        if weight is not None:
                weight = weight.iloc[:ncal]
                #The band is predicted at every grid point, so it needs a weight there too:
                #interpolated between 1 at x = 0 and the per-level weights.
                weight_lod = np.interp(grid, np.append(0, df.x.values), np.append(1, weight.values))
                regr = wls(formula='y ~ x',data= df, weights = weight).fit()
                c_i = regr.get_prediction(exog = exog, transform=True, weights = weight_lod).summary_frame(alpha=conf)

        else:
                regr = ols(formula='y~x', data=df).fit()
                c_i = regr.get_prediction(exog=exog, transform=True).summary_frame(alpha=conf)

        line = regr.params['Intercept'] + regr.params['x']*exog.x
        fig= go.Figure()
        fig.add_trace(go.Scatter(x=df.x, y = df.y, mode='markers', marker=dict(size=8),
                    hovertemplate='CAL %{text}<extra></extra>', text=df.index, name='Data means'))  
        fig.add_trace(go.Scatter(x=exog.x,y=line, mode='lines', line=dict(dash='solid', color='green'), name='Regression line'))
        #Hubaux and Vos is defined on the prediction interval of a future observation,
        #not on the confidence interval of the fitted mean.
        fig.add_trace(go.Scatter(x=exog.x, y=c_i['obs_ci_upper'], mode='lines', line=dict(dash='dash', color='red'), name='Upper prediction interval'))
        fig.add_trace(go.Scatter(x=exog.x, y=c_i['obs_ci_lower'], mode='lines',line=dict(dash='dash', color='blue'), fill='tonexty',
                     fillcolor='rgba(244, 236, 194,0.4)', name='Lower prediction interval'))
        fig.update_layout(
                title_text='Prediction interval',
                title_x = 0.5,
                xaxis_title='Concentration ratio',
                yaxis_title='Signal ratio',    
                height=500,
                width=700,
                showlegend=True
                )
        fig.update_layout(legend=dict(yanchor="bottom", y=-0.5, orientation='h', yref='paper'))

        return fig
