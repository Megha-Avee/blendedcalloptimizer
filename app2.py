#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 24 13:55:25 2019
@author: Aveedibya Dey
"""
import numpy as np
import datetime as dt
import pandas as pd
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import dash_table
import statistics as st

from app import graphingRegion, margin

#Internal package with functions and classes
import call_gen_demo as cgd
from call_generator_distribution import agentAggMetrics, overallMetrics

app = dash.Dash()
app.title = 'Blended Call Optimizer'
#server = app.server

#-------------------------------
#App Layout
app.layout = html.Div([
                html.Div([html.H5("Step 1: Define Call Distribution: ")], className=''),
                
                html.Div(),

                html.Hr(),

                html.Div([html.H5("Step 2: Define Cost Parameters for Cost Allocation Function: ")], className=''),

                #Start: Input Cost Parameters
                html.Div(html.Div([html.Label('Select your allocation method:'),
                                    dcc.Dropdown(id='allocation-method', options=[
                                            {'label': 'Random Allocation', 'value': 0},
                                            {'label': 'Systematic Cost Based Allocation', 'value': 1}], value=1)], className='col'), className='row'),

                html.Div([html.Div(html.Div(html.Div([
                            html.H5("Agent Idle Cost", className='card-title'),
                            html.P("Cost associated with idle time will be accounted using this factor.", className='card-text'),
                            html.Div([html.Label('Factor = ',),
                                        dcc.Input(id='factor-1', type='number', step=1, placeholder='7/30', className='form-control')], className='form-group'),
                            html.Div([html.Label('Weight = ',),
                                        dcc.Input(id='weight-factor-1', type='number', step=0.1, placeholder='0.5', className='form-control')], className='form-group')
                        ], className='card-body'), className='card shadow-sm'), className='col-4'),

                        html.Div(html.Div(html.Div([
                            html.H5("Switching Cost", className='card-title'),
                            html.P("Cost associated with switching between various contact methods will be accounted by this factor.", className='card-text'),
                            html.Div([html.Label('Factor = ',),
                                        dcc.Input(id='factor-2', type='number', step=1, placeholder='7/30', className='form-control')], className='form-group'),
                            html.Div([html.Label('Weight = ',),
                                        dcc.Input(id='weight-factor-2', type='number', step=0.1, placeholder='0.5', className='form-control')], className='form-group')
                        ], className='card-body'), className='card shadow-sm'), className='col-4'),

                        html.Div(html.Div(html.Div([
                            html.H5("Distribution Skewness Cost", className='card-title'),
                            html.P("Cost associated with skewed distribution of calls will be accounted by this factor.", className='card-text'),
                            html.Div([html.Label('Factor = ',),
                                        dcc.Input(id='factor-3', type='number', step=1, placeholder='7/30', className='form-control')], className='form-group'),
                            html.Div([html.Label('Weight = ',),
                                        dcc.Input(id='weight-factor-3', type='number', step=0.1, placeholder='0.5', className='form-control')], className='form-group')
                        ], className='card-body'), className='card shadow-sm'), className='col-4'),
                ], className='row mt-4'),
                #End: Input Cost Paramenters

                html.Hr(),

                html.Div([html.Button("Run Call Allocation Simulation", id='run-simulation', className='btn btn-outline-info btn-block')]),

                html.Hr(),

                dcc.Loading(children=[
                        
                html.Div([html.H5(id='result-header', children="Results: Simulation based on cost allocation is shown below: ", style={'display': 'none'})], className=''),

                html.Div(id='intermediate-values', style={'display': 'none'}),
                html.Div(id='allocation-results'),

                html.H5(id='result-header-1', children='Overall Metrics:', className='my-3', style={'display': 'none'}),

                html.Div(id='overall-metrics', children=[], className='row'),

                html.H5(id='result-header-2', children='Average Agent Metrics:', className='my-3', style={'display': 'none'}),

                html.Div(id='agent-metrics', children=[], className='row'),

                html.Div([html.Div(dcc.Graph(id='agent-idle-times', config={'displayModeBar': False}, figure=graphingRegion(225, margin={'l':0, 'b':0, 'r':0, 't':0})), className='col-4'),
                          html.Div(dcc.Graph(id='agent-switches', config={'displayModeBar': False}, figure=graphingRegion(225, margin)), className='col-4'),
                          html.Div(dcc.Graph(id='call-distribution', config={'displayModeBar': False}, figure=graphingRegion(225, margin)), className='col-4'),
                          html.Div(dcc.Graph(id='call-costs', config={'displayModeBar': False}, figure=graphingRegion(225, margin)), className='col')
                         ], className='row'),


                html.Br(), html.Br(),
                
                dash_table.DataTable(id='table')], type='cube'),

            ], className='container')


#-------------------------------

def metrics_display(agent_metrics):
    return [html.Div([html.H6('Number of Agents:'), html.P(str(len(agent_metrics)), className='display-4')], className='col mx-1 text-center alert alert-info'),
         html.Div([html.H6('Call Distribution (Inbound):'),
                    html.P("{0:.1%}".format(agent_metrics['inbound'].mean()), className='display-4'),
                    html.Br(),
                    html.H6('Std. Deviation:'),
                    html.P("{0:.1%}".format(st.pstdev(agent_metrics['inbound'])), className='display-4')], className='col mx-1 text-center alert alert-info'),
         html.Div([html.H6('Call Distribution (Outbound):'),
                    html.P("{0:.1%}".format(agent_metrics['outbound'].mean()), className='display-4'),
                    html.Br(),
                    html.H6('Std. Deviation:'),
                    html.P("{0:.1%}".format(st.pstdev(agent_metrics['outbound'])), className='display-4')], className='col mx-1 text-center alert alert-info'),
         html.Div([html.H6('Number of Call Switches:'),
                    html.P(str(round(agent_metrics['number_of_switches'].mean(),1)), className='display-4'),
                    html.Br(),
                    html.H6('Std. Deviation:'),
                    html.P(str(round(st.pstdev(agent_metrics['number_of_switches']),1)), className='display-4')], className='col mx-1 text-center alert alert-info')]

def overall_metrics_display(overall_metrics):
    return [html.Div([html.H6('Total Call Count:'), html.P(overall_metrics['total_call_count'], className='display-4')], className='col mx-1 text-center alert alert-secondary'),
             html.Div([html.H6('Call Distribution (Inbound):'), html.P("{0:.1%}".format(overall_metrics['call_count_by_type'][0]/sum(overall_metrics['call_count_by_type'])), className='display-4')], className='col mx-1 text-center alert alert-secondary'),
             html.Div([html.H6('Call Distribution (Outbound):'), html.P("{0:.1%}".format(overall_metrics['call_count_by_type'][1]/sum(overall_metrics['call_count_by_type'])), className='display-4')], className='col mx-1 text-center alert alert-secondary'),
             html.Div([html.H6('Avg. Wait Time (sec):'), html.P(str(round(overall_metrics['avg_call_wait'],1)), className='display-4')], className='col mx-1 text-center alert alert-secondary')
             ]

#-------------------------------
#App Callback Functions

@app.callback([Output('table', 'data'), Output('table', 'columns'),
                Output('agent-metrics', 'children'),
                Output('overall-metrics', 'children'),
                Output('result-header', 'style'),
                Output('result-header-1', 'style'),
                Output('result-header-2', 'style'),
                Output('agent-idle-times', 'figure'),
                Output('agent-switches', 'figure'),
                Output('call-distribution', 'figure'),
                Output('call-costs', 'figure')],
              [Input('run-simulation', 'n_clicks'),
               Input('allocation-method', 'value')])

def calculate_metrics(n_clicks, allocation_method):
    
    if n_clicks is not None:
        intvl_avg_calls = list(range(0,24,1)) + list(range(24,0,-1))
        intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
        max_intvl_calls = 2
        intvl_avg_calls = [x*max_intvl_calls/max(intvl_avg_calls) for x in intvl_avg_calls]
        intvl_st_time_day = [(dt.datetime(2018,1,1,0,0,0) + dt.timedelta(minutes= +30*x))  for x in range(len(intvl_avg_calls))]
        intvl_st_time = [dt.time(x.hour, x.minute, x.second) for x in intvl_st_time_day]
        intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
        intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
        
        #Inputs to be taken from user
        #--------------------
        aht_range = [300, 400]
        agent_count = 2
        
        call_tbl = cgd.call_table(intvl_st_time, intvl_call_count, aht_range)
        if allocation_method == 1:
            agent_tbl = cgd.agent_table(int(agent_count), call_tbl, use_cost_calculation=allocation_method)
            costTable = agent_tbl[1]
            agent_tbl = agent_tbl[0]
            
        agent_metrics = agentAggMetrics(agent_tbl)
        overall_metrics = overallMetrics(agent_tbl)

        agent_metrics_to_display = metrics_display(agent_metrics)
        overall_metrics_to_display = overall_metrics_display(overall_metrics)
        
        #plot agent metrics
        #-------------------
        idle_traces = []
        
        idle_traces.append(go.Bar(
                x=agent_metrics['agent_index'],
                y=agent_metrics['idle_time'],
                text=['Agent ' + str(agent_metrics['agent_index'][x]) + ' idles for: ' + "{0:.1%}".format(agent_metrics['idle_time'][x]) for x in agent_metrics.index.tolist()],
                hoverinfo='text',
                marker=dict(
                        color='rgb(58,200,225)',
                        line=dict(
                                color='rgb(8,48,107)',
                                width=1.5),
                                ),
                name="Agent Idle Times (% of total time)",
                opacity=0.6
                ))
                        
        #-------------------
        #plot call distribution
        call_types = ['inbound', 'outbound']
        
        #plot call switches
        #-------------------
        switch_traces = []
        
        switch_traces.append(go.Bar(
                x=agent_metrics['agent_index'],
                y=agent_metrics['number_of_switches'],
                text=['Agent ' + str(agent_metrics['agent_index'][x]) + ' switched call types ' + "{} times".format(agent_metrics['number_of_switches'][x]) for x in agent_metrics.index.tolist()],
                hoverinfo='text',
                marker=dict(
                        color='rgb(222,45,38)',
                        line=dict(
                                color='rgb(222,45,38)',
                                width=1.5),
                                ),
                name="Agent Call Switches",
                opacity=0.6
                ))
        #-------------------
        #plot call distributions
        dist_traces = []
        
        for calltypes in call_types:
            dist_traces.append(go.Bar(
                    x=agent_metrics['agent_index'],
                    y=agent_metrics[calltypes],
                    text=['Agent ' + str(agent_metrics['agent_index'][x]) + ' took ' + "{0:.1%} ".format(agent_metrics[calltypes][x]) + calltypes for x in agent_metrics.index.tolist()],
                    hoverinfo='text',
                    name="Contact Type: " + calltypes,
                    opacity=0.6
                    ))

        #-------------------
        graphingRegionMargins = go.layout.Margin(l=80,r=10, b=20, t=40, pad=20)
        
        #-------------------
        #Cost Allocation Chart
        if allocation_method == 1:
            allocation_traces = []
        
            for agent_index in costTable['agent_index'].drop_duplicates().tolist():
                allocation_traces.append(go.Scatter(
                        x=costTable[costTable['agent_index']==agent_index].reset_index().index,
                        y=costTable[costTable['agent_index']==agent_index]['assignment_cost'],
                        mode='lines+markers'))
            
            plot_costs_data = {'data': allocation_traces,
                         'layout': go.Layout()}
        else:
            plot_costs_data ={}
        
        

        return agent_metrics.to_dict('records'),\
                [{"name": i, "id": i} for i in agent_metrics.columns],\
                agent_metrics_to_display, overall_metrics_to_display,\
                {'display': ''},\
                {'display': ''},\
                {'display': ''},\
                {'data': idle_traces, 
                 'layout': go.Layout(
                         title='Agent Idle Time (% of overall time)',
                         xaxis={'zeroline': False, 'showgrid': False, 'showticklabels': False},
                         yaxis={'zeroline': True, 'showgrid': True, 'range': [0.9*min(agent_metrics['idle_time']), 1.1*max(agent_metrics['idle_time'])], 'tickformat': ",.1%"},
                         margin= graphingRegionMargins,
                         font=dict(family='Arial', size=12)
                         )
                 },\
                {'data': switch_traces, 
                 'layout': go.Layout(
                         title='Number of Call Type switches',
                         xaxis={'zeroline': False, 'showgrid': False, 'showticklabels': True},
                         yaxis={'zeroline': True, 'showgrid': True, 'range': [0.9*min(agent_metrics['number_of_switches']), 1.1*max(agent_metrics['number_of_switches'])], 'tickformat': ""},
                         margin= graphingRegionMargins,
                         font=dict(family='Arial', size=12)
                         )
                 },\
                {'data': dist_traces,
                 'layout': go.Layout(
                         barmode='stack',
                         title='Call distribution by agent',
                         showlegend=False,
                         yaxis={'tickformat': ",.1%"},
                         margin= graphingRegionMargins,
                         font=dict(family='Arial', size=12)
                         )},\
                 plot_costs_data
    else:
        return '','', '', '', {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {}, {}, {}, {}

#-------------------------------
#External CSS Links
external_css = ["https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"]

for css in external_css:
    app.css.append_css({"external_url": css})


if __name__ == '__main__':
    app.run_server(debug=True)
