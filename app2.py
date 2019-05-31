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

#<nav class="navbar navbar-light bg-light">
#  <span class="navbar-brand mb-0 h1">Navbar</span>
#</nav>


app.layout = html.Div([
                
                
                html.Nav([html.Span("1-Define Call Distribution: ", className='navbar-brand mb-0 h1')], className='navbar navbar-dark bg-dark', style={'background-color': 'rgba()'}),
                
                html.Div([html.H6("Enter Simulation Parameters:", className='card-title col-12'),
                                                     html.Div([html.Label('Number of Agents:'),
                                                               dcc.Input(id='agent-count', type='number', step=1, placeholder='Example = 3', className='form-control')], className='form-group col-4'),
                                                    html.Div([html.Label('Peak Call Count (half-hr interval):'),
                                                               dcc.Input(id='call-level', type='number', step=1, placeholder='Example = 10', className='form-control')], className='form-group col-4'),
                                                    html.Div([html.Label('AHT Range:'),html.Br(),
                                                               dcc.Input(id='aht-range-from', type='number', step=1, placeholder='From', className='form-control', style={'width': '42%', 'display': 'inline-block'}),
                                                               html.P(" - ", style={'text-align': 'center', 'width': '5%', 'display': 'inline-block'}),
                                                                dcc.Input(id='aht-range-to', type='number', step=1, placeholder='To', className='form-control', style={'width': '42%', 'display': 'inline-block'})], className='form-group col-4')
                        ], className='row mt-2 mx-2'),

                html.Div([html.H6("Define Call Distirbutions:", className='card-title col-12'),
                                                     html.Div([html.Label('Call Types (Enter names separated by commas):'),
                                                               dcc.Input(id='call-types', type='text', placeholder='Example = Inbound, Outbound', disabled=True, className='form-control')], className='form-group col-6'),
                                                    html.Div([html.Label('Call Type Distributions (Fractional values separated by commas):'),
                                                               dcc.Input(id='call-proportion', type='text', placeholder='Example = 0.3, 0.7', disabled=True, className='form-control')], className='form-group col-6'),
                        ], className='row mt-2 mx-2'),
#                html.Hr(),

                html.Nav([html.Span("2-Design Allocation Strategy: ", className='navbar-brand mb-0 h1')], className='navbar navbar-dark bg-dark mt-4'),

                #------
                #Start: Input Cost Parameters
                html.Div(html.Div([html.Label('Select your allocation method:'),
                                    dcc.Dropdown(id='allocation-method', options=[
                                            {'label': 'Random Allocation', 'value': 0},
                                            {'label': 'Systematic Cost Based Allocation', 'value': 1}], value=1)], className='col'), className='row mt-2 mx-2'),

                html.Div(html.Div([html.H6("Your Call Allocation Strategy:"), 
                                  html.P(id="cost-allocation-desc")] #--> Allocation Strategy Description
                                  , className='col'), className='row mx-2 mt-4'),


                html.Div(id='allocation-cost-tile', children=[html.Div(html.Div([
                            html.H5("Agent Idle Cost", className='card-title'),
                            html.P("Cost associated with idle time will be accounted using this factor. This factor is defined by the percentage of time the agent was idle.", className='card-text'),
                            html.Div([html.Label('Factor Defined By:'),
                                        dcc.Input(id='factor-1', type='text', step=1, placeholder='% Time Agent Idle', disabled=True, className='form-control')], className='form-group'),
                            html.Div([html.Label('Weight = ',),
                                        dcc.Input(id='weight-factor-idle', type='number', step=0.1, min=0, max=1, placeholder='0.33', className='form-control')], className='form-group')
                        ], className='card-body'), className='card shadow-sm'),

                        html.Div(html.Div([
                            html.H5("Switching Cost", className='card-title'),
                            html.P("Cost associated with switching between various contact methods will be accounted by this factor.", className='card-text'),
                            html.Div([html.Label('Factor Defined By:'),
                                        dcc.Input(id='factor-switch', type='number', step=1, placeholder='Default = 7 sec', className='form-control')], className='form-group'),
                            html.Div([html.Label('Weight = ',),
                                        dcc.Input(id='weight-factor-switch', type='number', step=0.1, min=0, max=1, placeholder='0.33', className='form-control')], className='form-group')
                        ], className='card-body'), className='card shadow-sm'),

                        html.Div(html.Div([
                            html.H5("Distribution Skewness Cost", className='card-title'),
                            html.P("Cost associated with skewed distribution of calls will be accounted by this factor.", className='card-text'),
                            html.Div([html.Label('Factor Defined By:'),
                                        dcc.Input(id='factor-3', type='number', step=1, placeholder='% Call Type Skewed', disabled=True, className='form-control')], className='form-group'),
                            html.Div([html.Label('Weight = ',),
                                        dcc.Input(id='weight-factor-dist', type='number', step=0.1, min=0, max=1, placeholder='0.33', className='form-control')], className='form-group')
                        ], className='card-body'), className='card shadow-sm'),
                ], className='row mt-2 card-deck mx-2'),
                #End: Input Cost Paramenters
                #------

                html.Div([html.Button("Run Call Allocation Simulation", id='run-simulation', className='btn btn-outline-info btn-block mt-4')]),

                html.Hr(),

                html.Div(id='result-section',children=dcc.Loading(children=[
                        
                html.Nav(id='result-header', children=[html.Span(children="Results: Simulation based on cost allocation is shown below: ",  className='navbar-brand mb-0 h1')], className='navbar navbar-dark bg-dark', style={'display': 'none'}),

                html.Div([html.Div(id='intermediate-values', style={'display': 'none'}),
                html.Div(id='allocation-results'),

                html.H5(id='result-header-1', children='Overall Metrics:', className='my-3', style={'display': 'none'}),

                html.Div(id='overall-metrics', children=[], className='row'),

                html.H5(id='result-header-2', children='Average Agent Metrics:', className='my-3', style={'display': 'none'}),

                html.Div(id='agent-metrics', children=[], className='row'),

                html.Div([html.Div(dcc.Graph(id='agent-idle-times', config={'displayModeBar': False}), className='col-4'),
                          html.Div(dcc.Graph(id='agent-switches', config={'displayModeBar': False}), className='col-4'),
                          html.Div(dcc.Graph(id='call-distribution', config={'displayModeBar': False}), className='col-4'),
                          html.Div(dcc.Graph(id='call-costs', config={'displayModeBar': False}), className='col')
                         ], className='row'),


                html.Br(), html.Br(),
                
                dash_table.DataTable(id='table')], className='mx-4')], type='cube'), style={'display': 'none'}),

            ], className='container my-4')


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


def remove_none_from_inputs(user_input):
    if user_input == None:
        user_input = 0.0
    else:
        user_input = float(user_input)
    return user_input
#-------------------------------
#App Callback Functions
    

@app.callback(Output('cost-allocation-desc', 'children'),
              [Input('allocation-method', 'value')])

def show_call_allocation_desc(allocation_method):
    if allocation_method == 1:
        #Cost Based Calculations
        return "Systematic cost based strategy uses an intelligent cost function to assign calls to agents. It is comprised of\
                the following parameters, and you can change these parameters and their individual weights to allow the cost function\
                to pay more or less attention to certain parameter. This startegy will allow you to optimize agent metrics across all\
                agents, hence, reducing variations in these metrics across different agents. Simulation process may take longer time to run\
                as the cost function is optimized for each call during the simulation run."
    else: 
        return "Random allocation strategy will randomly select available agents and assign calls to them. This is often used in many call allocation\
                systems by default. This can result in high variations in different metrics across agents, and is not a suitable method if you want to\
                ensure all agents receive fair treatment against various business goals you measure. The simulation process is quicker to run in this case\
                as there is no cost function to optimize for every call."

@app.callback(Output('result-section', 'style'),
              [Input('run-simulation', 'n_clicks')])

def show_result_section(n_clicks):
    if n_clicks is not None:
        return {'display': ''}

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
                [Input('run-simulation', 'n_clicks')],
                [State('allocation-method', 'value'),
                 State('factor-switch', 'value'),
                 State('agent-count', 'value'),
                 State('call-level', 'value'),
                 State('aht-range-from', 'value'),
                 State('aht-range-to', 'value'),
                 State('weight-factor-idle', 'value'),
                 State('weight-factor-switch', 'value'),
                 State('weight-factor-dist', 'value')]
              )

def calculate_metrics(n_clicks, allocation_method, switching_cost, agent_count, call_level, aht_from, aht_to, weight_idle, weight_switch, weight_dist):
    
    if n_clicks is not None:
        
        weight_idle = remove_none_from_inputs(weight_idle)
        weight_switch = remove_none_from_inputs(weight_switch)
        weight_dist = remove_none_from_inputs(weight_dist)
        switching_cost = remove_none_from_inputs(switching_cost)
       
        #Linear Increasing/Decreasing call average function
        #-------------------
        intvl_avg_calls = list(range(0,24,1)) + list(range(24,0,-1))
        intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
        
        #Interval call scale
        max_intvl_calls = int(call_level)
        intvl_avg_calls = [x*max_intvl_calls/max(intvl_avg_calls) for x in intvl_avg_calls]
        intvl_st_time_day = [(dt.datetime(2018,1,1,0,0,0) + dt.timedelta(minutes= +30*x))  for x in range(len(intvl_avg_calls))]
        intvl_st_time = [dt.time(x.hour, x.minute, x.second) for x in intvl_st_time_day]
        intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
        intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
        
        #Inputs to be taken from user
        #--------------------
        aht_range = [int(aht_from), int(aht_to)]
        agent_count = int(agent_count)
        
        call_tbl = cgd.call_table(intvl_st_time, intvl_call_count, aht_range)
        agent_tbl = cgd.agent_table(int(agent_count), call_tbl, use_cost_calculation=allocation_method,\
                                    weight_idle=weight_idle, weight_dist=weight_dist,\
                                    weight_switch=weight_switch, call_switch_agent_time=int(switching_cost))
        
        if allocation_method == 1:
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
                        mode='lines+markers',
                        name='Agent ' + str(agent_index)
                        ))
            
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


@app.callback(Output('allocation-cost-tile', 'style'), 
              [Input('allocation-method', 'value')]
              )

def show_hide_tile(allocation_method):
    if allocation_method == 1:
        return {'display': ''}
    else:
        return {'display': 'none'}



#-------------------------------
#External CSS Links
external_css = ["https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"]

for css in external_css:
    app.css.append_css({"external_url": css})


if __name__ == '__main__':
    app.run_server(debug=True)
