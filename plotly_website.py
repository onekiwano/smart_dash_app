# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 16:03:01 2023

@author: Manu
"""

import numpy as np
import os 
from datetime import datetime
import dash_bootstrap_components as dbc

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
# https://towardsdatascience.com/how-to-create-a-plotly-visualization-and-embed-it-on-websites-517c1a78568b
# Import libraries
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px

data_end = {'now':'2023-03-25-20-20-20'}

FILENAME = os.path.realpath(__file__)
CDIR = os.path.dirname(FILENAME)
DATADIR = os.path.abspath(os.path.join(CDIR, '..', '..', 'data'))
CRYPTODIR = os.path.join(DATADIR, 'crypto')
os.makedirs(CRYPTODIR, exist_ok=True)


dca_strategies_name = ['Standard DCA',
                  'Smart DCA: contained',
                  'Smart DCA: unlished',
                 ] 

dca_strategies = ['dca_1',
                  'sigmoid',
                  'dca_ratio'
                 ] 

dic_strategy_names = {dca_strategies_name[i]:dca_strategies[i] for i in range(len(dca_strategies))}

# Create the Dash app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets,
           suppress_callback_exceptions=True,
           prevent_initial_callbacks=True)
server = app.server

# Set up the app layout
title = dcc.Markdown(children='# DCA simulations')
cum_ret = dcc.Markdown(children='')
base_value = dbc.Input(value=25, min=0)

dca_dropdown = dcc.Dropdown(options=dca_strategies_name,
                            value='Standard DCA',
                            clearable=False)
list_years = [(2018 + i) for i in range(6)]
startdate_dropdown = dcc.Dropdown(list_years, value=2022, clearable=False)
enddate_dropdown = dcc.Dropdown(list_years, value=2023, clearable=False)
window_slider = dcc.Slider(50, 300, step=50, value=50, 
                           id='window-slider')
period_slider = dcc.Slider(1, 20, step=3, value=1, id='period-slider')
window_slider = dcc.Slider(50, 300, step=50, value=50, 
                           id='window-slider')
graph_price = dcc.Graph(figure={})
graph_amount = dcc.Graph(figure={})

disp = lambda title, obj, **kwargs: html.Div(children=[html.H1(children=title),
                                             obj], 
                                             style={"width":"100%"},
                                             **kwargs)

app.layout = dbc.Container([
                    dbc.Row([
                    dbc.Col([disp('', title)], width=6)], 
                    justify='center'),
                    html.Br(),
                    dbc.Row([
                    dbc.Col([disp('Start year', startdate_dropdown)], width=6),
                    dbc.Col([disp('End year', enddate_dropdown)], width=6),
                    ]),
                    html.Br(),
                    dbc.Row([
                    dbc.Col([disp('', graph_price)], width=12),
                    ]),
                    dbc.Row([
                    dbc.Col([disp('', graph_amount)], width=8),
                    dbc.Col([disp('Strategy', dca_dropdown),
                             disp('Window length (day)', window_slider),
                             disp('Period (day)', period_slider),
                             disp('Maximum per day ($)', base_value)], width=4),
                    ]),
                    html.Br(),
                    dbc.Row([
                    dbc.Col([disp('Summary:', cum_ret)], width=12),
                    ]),
                ])                     

crypto_pair = 'BTCUSDT'
# Set up the callback function
@app.callback(
    Output(component_id=graph_price, component_property='figure'),
    Output(component_id=graph_amount, component_property='figure'),
    Output(component_id=cum_ret, component_property='children'),
    Input(component_id=base_value, component_property='value'),
    Input(component_id=period_slider, component_property='value'),
    Input(component_id=window_slider, component_property='value'),
    Input(component_id=dca_dropdown, component_property='value'),
    Input(component_id=startdate_dropdown, component_property='value'),
    Input(component_id=enddate_dropdown, component_property='value'),
)
def update_graph(base, period, window, title_strat='Standard DCA', start_year=2022, end_year=2023):
    # Load the dataset
    time = 'now'
    name_strat = dic_strategy_names[title_strat]
    if 'ratio' in name_strat:
        name_strat = name_strat + '^6'
    if ('sigmoid' in name_strat) or ('ratio' in name_strat):
        name_strat = name_strat + f'_EMA{window}'
    end_date = data_end[time]
    crypto_df = pd.read_csv(f"results/{time}_{end_date}_{crypto_pair}_{name_strat}.csv")
    crypto_df = crypto_df.dropna()
    
    # Apply period
    period = int(period)
    crypto_df.loc[crypto_df.index % period != 0, 'Modulators'] = 0
    crypto_df['Amounts'] = int(base) * crypto_df['Modulators']
    
    # Select time
    start_date = datetime(start_year, 3, 20, 21).timestamp()*1000
    end_date = datetime(end_year, 3, 20, 21).timestamp()*1000
    crypto_df = crypto_df.loc[(start_date < crypto_df['TimeStamp']) &
                              (crypto_df['TimeStamp'] < end_date), :]
    
    # Compute cumulative return
    budgets = crypto_df['Amounts'] * crypto_df['Close']
    total_budget = budgets.sum()
    crypto_boughts = crypto_df['Amounts'] / crypto_df['Close']
    total_boughts = crypto_boughts.sum()
    wealth = total_boughts * crypto_df['Close'].values[-1]
    total_budget = crypto_df['Amounts'].sum()
    cm = np.round(wealth/total_budget, 3)
    total_budget = np.round(total_budget, 1)
    crypto_boughts = np.round(total_boughts, 4)
    wealth = np.round(wealth, 1)
    avg_price = np.round(total_budget/crypto_boughts, 1)
    summary = f"|CM| |Wealth| |Spent| |Crypto| |Average price|\n \
           |-------|--|-------|--|-------|--|-------|--|-----|\n \
           |{cm}| |{wealth}$| |{total_budget}$| |{crypto_boughts}| |{avg_price}$|"
    
    
    # Plot the price
    price_fig = px.line(crypto_df,
                        x='Date', y='Close',
                        title=f'{crypto_pair[:3]} price in USD',
                        labels={"Close": "Price ($)"})
    
    # plot amount boughts over time
    amt_fig = px.line(crypto_df,
                      x='Date', y='Amounts',
                      title=f'Amounts bought for {title_strat} strategy',)
    return price_fig, amt_fig, summary


# Run local server
if __name__ == '__main__':
    app.run_server(debug=False, port=8060, host='0.0.0.0')
