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
import dash_daq
import statistics as st

from app import graphingRegion, margin

#Internal package with functions and classes
import call_gen_demo as cgd
from call_generator_distribution import agentAggMetrics, overallMetrics

from rq import Queue
from worker import conn
from rq import get_current_job

app = dash.Dash(meta_tags=[{'name':"viewport", 'content':"width=device-width, initial-scale=1"}])
app.title = 'Blended Call Optimizer'

server = app.server

# app.head = [
#    html.Link(
#        href='https://kit.fontawesome.com/dab9468bc6.js',
#        type='text/javascript'
#    )]

#-------------------------------
#App Layout

#<nav class="navbar navbar-light bg-light">
#  <span class="navbar-brand mb-0 h1">Navbar</span>
#</nav>
footnote_markdown = '''
Created by: Aveedibya Dey | [Contact Me/Leave Feedback](https://aveedibyadey.typeform.com/to/guGq1P) | See other creations: [Call Center Ops Simulation](https://operationsimulation.herokuapp.com/), [Regression Simulator](https://regressionsimulator.herokuapp.com/), [Forecasting Tool](https://ultimateforecastingtool.herokuapp.com/)
    '''

app.layout = html.Div([

                html.Div("Call Allocation Optimizer", className='container-fluid display-4 text-center pt-2', style={'height': '', 'padding-left': '0px', 'color': 'gray', 'font-family': 'Ubuntu'}),

                html.Div("Design. Tweak. Optimize.", className='continer-fluid h3 mt-2 text-center', style={'height': '', 'padding-right': '0px', 'color': 'gray', 'font-family': 'Ubuntu'}),

#                html.Hr(style={'width': '20%', 'size': '5vh'}, className='mt-0 pt-0'),

                html.Div([


                html.Nav([html.Span("1-Define Call Distribution: ", className='navbar-brand mb-0 h1')], className='navbar navbar-dark bg-dark', style={'background-color': 'rgba()'}),

                html.Div([html.H6("Enter Simulation Parameters:", className='card-title col-md-12'),
                                                     html.Div([html.Label('Number of Agents:'),
                                                               dcc.Input(id='agent-count', type='number', step=1, placeholder='Example = 3', className='form-control')], className='form-group col-md-4'),
                                                    html.Div([html.Label('Peak Call Count (half-hr interval):'),
                                                               dcc.Input(id='call-level', type='number', min=0, step=1, placeholder='Example = 10', className='form-control')], className='form-group col-md-4'),
                                                    html.Div([html.Label('AHT Range:'),html.Br(),
                                                               dcc.Input(id='aht-range-from', type='number', step=1, placeholder='From', className='form-control', style={'width': '42%', 'display': 'inline-block'}),
                                                               html.P(" - ", style={'text-align': 'center', 'width': '5%', 'display': 'inline-block'}),
                                                                dcc.Input(id='aht-range-to', type='number', step=1, placeholder='To', className='form-control', style={'width': '42%', 'display': 'inline-block'})], className='form-group col-md-4')
                        ], className='row mt-2 mx-2'),

                html.Div([html.H6("Define Call Distirbutions:", className='card-title col-md-12'),
                                                     html.Div([html.Label('Call Types (Enter names separated by commas):'),
                                                               dcc.Input(id='call-types', type='text', placeholder='Default = Inbound, Outbound', disabled=True, className='form-control')], className='form-group col-md-6'),
                                                    html.Div([html.Label('Call Type Distributions (Fractional values separated by commas):'),
                                                               dcc.Input(id='call-proportion', type='text', placeholder='Default = 0.3, 0.7', disabled=True, className='form-control')], className='form-group col-md-6'),
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

                html.Div([html.Div("Auto-populate all inputs:", className='col-md-2 my-2 pt-2 pl-2 pr-0 text-muted small', style={'text-align': 'right'}),
                          html.Div(children=dash_daq.BooleanSwitch(id='autopopulate-switch', on=False), className='col-md-2 my-2 pt-2 pr-2 pl-0')
                          ], className='row'),

                html.Div([html.Button(id="run-simulation-btn", children=[html.Div(id='run-simulation', children="Run Call Allocation Simulation", style={'display': 'inline-block'}, className='pr-3'),
                                    html.I(id='wait-for-results', className='fas fa-cog fa-spin', style={'display': 'none'})
                                    ], className='btn btn-outline-info btn-block col'),
                          ], className='row mx-2'),

#                html.Hr(),

                html.Div(id='result-section',
                         children=dcc.Loading(children=[

                            html.Nav(id='result-header', children=[html.Span(id='result-header-title', children="Results of your call allocation process:", className='navbar-brand mb-0 h1')], className='navbar navbar-dark bg-dark mt-4', style={'display': 'none'}),

                            html.Div([html.Div(id='intermediate-values', style={'display': 'none'}),
                                        html.Div(id='allocation-results'),

                                        html.H5(id='result-header-1', children='Overall Metrics:', className='my-3', style={'display': 'none'}),

                                        html.Div(id='overall-metrics', children=[], className='row'),

                                        html.H5(id='result-header-2', children='Average Agent Metrics:', className='my-3', style={'display': 'none'}),

                                        html.Div(id='agent-metrics', children=[], className='row'),

                                        html.Div(id='result-chart-area', children=[html.Div(dcc.Graph(id='agent-idle-times', config={'displayModeBar': False}), className='col-md-4'),
                                                  html.Div(dcc.Graph(id='agent-switches', config={'displayModeBar': False}), className='col-md-4'),
                                                  html.Div(dcc.Graph(id='call-distribution', config={'displayModeBar': False}), className='col-md-4'),
                                                  html.Div([html.Div(id='call-costs-chart', children=dcc.Graph(id='call-costs', config={'displayModeBar': False}))], className='col-md-9 my-4'),
                                                  html.Div([html.Div(id='cost-view-tile', children=[html.Label("Filter Cost Type:"),
                                                                      dcc.Dropdown(id='cost-filter', options=[
                                                                                            {'label': 'Total Cost', 'value': 0},
                                                                                            {'label': 'Select Cost Type', 'value': 1}], value=0, className='')], className='my-2'), html.Br(),
                                                            html.Div(id='cost-type-tile', children=[html.Label("Select Cost Type:"),
                                                                      dcc.RadioItems(id='cost-selector', options=[
                                                                                    {'label': ' Agent Idle Cost ', 'value': 'idle_cost'},
                                                                                    {'label': ' Switching Cost ', 'value': 'switch_cost'},
                                                                                    {'label': ' Skewness Cost ', 'value': 'skewness_cost'}
                                                                                ], value='idle_cost')], className='my-2'), html.Br(),
                                                            html.Div(id='filter-agent-tile', children=[html.Label("Filter Agent:"),
                                                                      dcc.Dropdown(id='filter-agent', multi=True)
                                                                    ], className='my-2')
                                                            ], className='col mt-5')
                                                 ], className='row'),

                                        html.Div(id='cost-design-button', children=[html.Button("See My Cost Function", id='see-cost-function', className='btn btn-outline-secondary btn-block col')], className='row mt-4 mx-2'),

                                        html.Div(id='cost-design-block', children=[


                                                html.Div([html.Nav(html.Span("Your Designed Algorithm:", className='navbar-brand mb-0 h1'), className='navbar navbar-dark bg-dark mt-4'),
                                                          html.Div(dcc.Markdown(id='cost-function-text'), className='mt-3')
                                                          ]),
                                                ]),


                                        html.Br(), html.Br(),

                                        html.Div(id='table', style={'display': 'none'})

                                    ], className='mx-4')

                        ], type='cube', fullscreen=False), style={'display': 'none'}),

            ], className='container my-4 bg-white shadow py-3 rounded border'),

            html.Div([html.Span([html.Span("Designed with lots of ", style={'display': 'inline-block', 'padding-right': '5px'}),
                                 html.I(className='fas fa-mug-hot', style={'display': 'inline-block', 'padding-bottom': '2px'})
                                 ]),
                      dcc.Markdown(footnote_markdown)], className='text-center mt-3 mb-0 py-3 bg-light container-fluid', style={'height': '50px', 'font-size': '0.8em'}),
                
            dcc.Interval(id='interval-component', interval=1*2000, n_intervals=0, max_intervals=0), 

        ], className='bg-light py-3', style={'font-family': 'Ubuntu'})


#------------------------------
#Custome Function/Variable definitions

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


cost_function_design = '''###### Design you cost function for contact allocation in the following manner:

For any new contact method (incbound/outbound connect) use these steps to determine the best agent to allocate the next call.

 1. Filter agents who are free when the next call (or other contact method) arrives. If no agent is free when the call arrives, then pick the agent
who will be free to take the call next. This ensures low call wait time for the customers.


 2. If more than one agent is available to take the call, use the formula below to calculate the cost of assgining the next call to each of the available agents.
 Further, pick the agent with the maximum cost at the time of allocation.

   {0:.1%} x (Agent Idle Time/Total Signed-In Time) + {0:.1%} x (Call Type Switching Time/Brand Promise Wait Time) + {0:.1%} x (1 - (Percent Calls Handled of Each Type/Proportion of this Call Type for All Calls))

    '''
#-------------------------------
#App Callback Functions

@app.callback([Output('cost-function-text', 'children'),
               Output('cost-design-block', 'style'),
               Output('cost-design-button', 'style')],
              [Input('see-cost-function', 'n_clicks'),
               Input('weight-factor-idle', 'value'),
               Input('weight-factor-switch', 'value'),
               Input('weight-factor-dist', 'value'),
               Input('allocation-method', 'value'),
               Input('result-header', 'style')
               ])

def show_Cost_function(n_clicks, wt_idle, wt_switch, wt_dist, allocation_method, result_style):
    if n_clicks is not None and allocation_method==1:
        return cost_function_design.format(wt_idle, wt_switch, wt_dist), {'display': ''}, {'display': result_style['display']}
    else:
        if allocation_method == 0:
            return cost_function_design.format(0, 0, 0), {'display': 'none'}, {'display': 'none'}
        else:
            return cost_function_design.format(0, 0, 0), {'display': 'none'}, {'display': result_style['display']}


@app.callback([Output('cost-allocation-desc', 'children'),
               Output('result-header-title', 'children'),
               Output('call-costs-chart', 'style')],
              [Input('allocation-method', 'value')])

def show_call_allocation_desc(allocation_method):
    if allocation_method == 1:
        #Cost Based Calculations
        return "Systematic cost based strategy uses an intelligent cost function to assign calls to agents. It is comprised of\
                the following parameters, and you can change these parameters and their individual weights to allow the cost function\
                to pay more or less attention to certain parameter. This strategy will allow you to optimize agent metrics across all\
                agents, hence, reducing variations in these metrics across different agents. Simulation process may take longer time to run\
                as the cost function is optimized for each call during the simulation run.",\
                "Results: Simulation based on cost allocation is shown below:",\
                {'display': ''}
    else:
        return "Random allocation strategy will randomly select available agents and assign calls to them. This is often used in many call allocation\
                systems by default. This can result in high variations in different metrics across agents, and is not a suitable method if you want to\
                ensure all agents receive fair treatment against various business goals you measure. The simulation process is quicker to run in this case\
                as there is no cost function to optimize for every call.",\
                "Results: Simulation based on random allocation is shown below:",\
                {'display': 'none'}

@app.callback(Output('result-section', 'style'),
              [Input('run-simulation-btn', 'n_clicks')])

def show_result_section(n_clicks):
    if n_clicks is not None:
        return {'display': ''}
    else:
        return {'display': 'None'}

agent_tbl = None


@app.callback([Output('table', 'children'),
                Output('agent-metrics', 'children'),
                Output('overall-metrics', 'children'),
                Output('result-header', 'style'),
                Output('result-header-1', 'style'),
                Output('result-header-2', 'style'),
                Output('result-chart-area', 'style'),
                Output('agent-idle-times', 'figure'),
                Output('agent-switches', 'figure'),
                Output('call-distribution', 'figure'),
                Output('run-simulation', 'children'),
                Output('wait-for-results', 'style'),
                Output('interval-component', 'max_intervals')
                ],
                [Input('run-simulation-btn', 'n_clicks'),
                 Input('interval-component', 'n_intervals')
                 ],
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

def calculate_metrics(n_clicks, n_intervals, allocation_method, switching_cost, agent_count, call_level, aht_from, aht_to, weight_idle, weight_switch, weight_dist):

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

        #-------------------------------
        #Testing Queueing functions:

        q = Queue(connection=conn)
        # result = q.enqueue(cgd.agent_table, 'http://heroku.com')
        #-------------------------------

        call_tbl = cgd.call_table(intvl_st_time, intvl_call_count, aht_range)

        global agent_tbl

        if agent_tbl == None:
            agent_tbl = q.enqueue(cgd.agent_table, int(agent_count), call_tbl, use_cost_calculation=allocation_method,\
                                    weight_idle=weight_idle, weight_dist=weight_dist,\
                                    weight_switch=weight_switch, call_switch_agent_time=int(switching_cost))
            
            print(">>>--->>>--- Job Id is: ", agent_tbl.key)
            #Retrieve this job: Job.fetch(job_id, connection=conn)
            #agent_tbl.meta['progress_status'] = 'Building Agent Table'
            #agent_tbl.save()

            return '', '', '', {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {}, {}, {}, 'Running your simulation! Click again to check for output in few seconds.', {'display': 'inline-block'}, 0

        else:
            #print("Agent Table >>---->> is of type:", type(agent_tbl.result), agent_tbl)
            #print(">---------->\n >>-->> Printing job meta: ", agent_tbl.meta['progress_status'], '\n>---------->')
            agent_tbl = agent_tbl.result
            
            if agent_tbl is not None:
                #Check if job is complete and result is not None
                if allocation_method == 1:
                    costTable = agent_tbl[1]
                    agent_tbl = agent_tbl[0]
                else:
                    costTable = pd.DataFrame()
    
                agent_metrics = agentAggMetrics(agent_tbl)
                overall_metrics = overallMetrics(agent_tbl)
    
                agent_tbl = None
    
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
                graphingRegionMargins = go.layout.Margin(l=80,r=10, b=40, t=40, pad=20)
    
    
    
                return costTable.to_json(date_format='iso', orient='split'),\
                        agent_metrics_to_display, overall_metrics_to_display,\
                        {'display': ''},\
                        {'display': ''},\
                        {'display': ''},\
                        {'display': ''},\
                        {'data': idle_traces,
                         'layout': go.Layout(
                                 title='Agent Idle Time (% of overall time)',
                                 xaxis={'zeroline': False, 'showgrid': False, 'showticklabels': False},
                                 yaxis={'zeroline': True, 'showgrid': True, 'range': [0.9*min(agent_metrics['idle_time']), 1.1*max(agent_metrics['idle_time'])], 'tickformat': ",.1%"},
                                 margin= graphingRegionMargins,
                                 font=dict(family='Ubuntu', size=12)
                                 )
                         },\
                        {'data': switch_traces,
                         'layout': go.Layout(
                                 title='Number of Call Type switches',
                                 xaxis={'zeroline': False, 'showgrid': False, 'showticklabels': False},
                                 yaxis={'zeroline': True, 'showgrid': True, 'range': [0.9*min(agent_metrics['number_of_switches']), 1.1*max(agent_metrics['number_of_switches'])], 'tickformat': ""},
                                 margin= graphingRegionMargins,
                                 font=dict(family='Ubuntu', size=12)
                                 )
                         },\
                        {'data': dist_traces,
                         'layout': go.Layout(
                                 barmode='stack',
                                 title='Call distribution by agent',
                                 showlegend=False,
                                 xaxis={'showticklabels': False},
                                 yaxis={'tickformat': ",.1%"},
                                 margin= graphingRegionMargins,
                                 font=dict(family='Ubuntu', size=12)
                                 )},\
                        'Re-Run Call Allocation Simulation', {'display': 'none'},\
                        0
    else:
        return '', '', '', {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {}, {}, {}, 'Run Call Allocation Simulation', {'display': 'none'}, 0

#------------------
#Show/Hide the cost graph depending on type chosen
@app.callback(Output('allocation-cost-tile', 'style'),
              [Input('allocation-method', 'value')]
              )

def show_hide_tile(allocation_method):
    if allocation_method == 1:
        return {'display': ''}
    else:
        return {'display': 'none'}

#------------------
#Setting Defaults here
@app.callback([Output('agent-count', 'value'),
               Output('call-level', 'value'),
               Output('aht-range-from', 'value'),
               Output('aht-range-to', 'value'),
               Output('factor-switch', 'value'),
               Output('weight-factor-idle', 'value'),
               Output('weight-factor-switch', 'value'),
               Output('weight-factor-dist', 'value')],
               [Input('autopopulate-switch', 'on')])

def autopoulate_defaults(autopopulate_option):
    if autopopulate_option==True:
        return 2, 3, 100, 150, 7, 0.33, 0.33, 0.33
    else:
        return '', '', '', '', '', '', '', ''


#Views of the cost table
@app.callback([Output('call-costs', 'figure'),
               Output('cost-type-tile', 'style'),
               Output('filter-agent-tile', 'style'),
               Output('cost-view-tile', 'style')],
              [Input('table', 'children'),
               Input('allocation-method', 'value'),
               Input('cost-filter', 'value'),
               Input('cost-selector', 'value'),
               Input('filter-agent', 'value')
               ])

def cost_table_views(cost_table_json, allocation_method, cost_filter, cost_type, filter_by_agent):
    #-------------------
    #Cost Allocation Chart
    if allocation_method == 1 and cost_table_json is not None and cost_table_json != '':
        print("---->>---", cost_table_json)
        costTable = pd.read_json(cost_table_json, orient='split')
        allocation_traces = []

        if filter_by_agent is not None:
            if set(filter_by_agent) <= set(costTable['agent_index'].drop_duplicates().tolist()):
                agent_list_to_iterate_on = filter_by_agent
        else:
            agent_list_to_iterate_on = costTable['agent_index'].drop_duplicates().tolist()

        for agent_index in agent_list_to_iterate_on:

            if cost_filter == 0:
                cost_to_display = costTable[costTable['agent_index']==agent_index]['assignment_cost']
                display_type_of_cost_tile = {'display': 'none'}
            else:
                cost_to_display = costTable[costTable['agent_index']==agent_index][cost_type]
                display_type_of_cost_tile = {'display': ''}

            allocation_traces.append(go.Scatter(
                    x=costTable[costTable['agent_index']==agent_index].reset_index().index,
                    y=cost_to_display,
                    mode='lines',
                    name='Agent ' + str(agent_index),
                    line = dict(width = 4),
                    #marker = dict(size = 8),
                    opacity = 0.8
                    ))

        plot_costs_data = {'data': allocation_traces,
                     'layout': go.Layout(title='Cost Function Iteration Over Calls',
                                         margin=go.layout.Margin(l=80,r=10, b=40, t=40, pad=20),
                                         xaxis={'tickformat': ",.2"},
                                         font=dict(family='Ubuntu', size=12),
                                         legend=dict(x=0.8,
                                                     y=1,
                                                     traceorder='normal',
                                                     font=dict(
                                                        family='Ubuntu',
                                                        size=12,
                                                        color='#000'
                                                        ),
                                                    bgcolor='#E2E2E2',
                                                    bordercolor='#FFFFFF',
                                                    borderwidth=2
                                                )
                                         )}

        return plot_costs_data, display_type_of_cost_tile, {'display': ''}, {'display': ''}
    else:
        return {'data': []}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

#Agent Filtering
@app.callback(Output('filter-agent', 'options'),
              [Input('table', 'children'),
               Input('allocation-method', 'value')
               ])

def populate_agent_filter(cost_table_json, allocation_method):
    #-------------------
    #Cost Allocation Chart
    if allocation_method == 1 and cost_table_json is not None and cost_table_json != '':
        costTable = pd.read_json(cost_table_json, orient='split')
        filter_agent_options = []

        for agent_index in costTable['agent_index'].drop_duplicates().tolist():
            filter_agent_options.append({'label': 'Agent ' + str(agent_index), 'value': agent_index})

        return filter_agent_options
    else:
        return []



#-------------------------------
#External CSS Links
external_css = ["https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css",
                "https://fonts.googleapis.com/css?family=Ubuntu&display=swap",
                "/assets/appcss.css"]

for css in external_css:
    app.css.append_css({"external_url": css})

app.scripts.append_script({"external_url": "https://kit.fontawesome.com/dab9468bc6.js"})

if __name__ == '__main__':
    app.run_server(debug=True)
