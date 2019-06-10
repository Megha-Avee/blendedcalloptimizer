#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 21 23:38:36 2019

@author: avee
"""
import numpy as np
import random
import pandas as pd
import datetime as dt

import call_gen_demo as cgd

import timeit
run_times= {}
from timeit import default_timer as timer

class dynamicCall:
    """
    """
    #call_type = 'inbound'
    
    def __init__(self, aht_range, arrival_intvl, call_proportions=[0.3, 0.7], call_types=['inbound', 'outbound']):
        self.aht_actual = random.randint(aht_range[0], aht_range[1])
        self.call_start_time = dt.time(arrival_intvl.hour, arrival_intvl.minute + random.randint(1,29))
        
        curr_random_selector = random.randint(0,100)/100
        #print(curr_random_selector)
        call_proportions_compare = 0
        for i in range(len(call_proportions)):
            call_proportions_compare += call_proportions[i]
            #print(call_proportions_compare)
            if curr_random_selector <= call_proportions_compare:
                self.call_type = call_types[i]
                break


def calculateAgentCosts(agent_costs, call_types, next_call, agent_tbl, call_switch_agent_time=7.00, call_bp_time=60.00, weight_idle=1, weight_dist=1, weight_switch=1):
    """
    """
    next_call= next_call.reset_index()
    call_distribution_actual, call_distribution_ratios = currentParameters(call_types, agent_tbl)
    
    
    call_count_types = agent_tbl.groupby(['agent_index', 'call_type'])['call_type'].count()
    call_aht_sum = agent_tbl.groupby('agent_index')['call_aht'].sum()
    
    for agent_index in agent_costs['agent_index'].drop_duplicates().tolist():
        print("--->>--- Agent No. ", agent_index)
        #filtered_agent_tbl = agent_tbl[agent_tbl['agent_index']==agent_index]
        
        call_distribution_list = []
        for call_type_names in call_types:
            if True in call_count_types.index.isin([(agent_index, call_type_names)]):
                call_distribution_list.append(call_count_types[agent_index][call_type_names])
            else:
                call_distribution_list.append(1)
        
#        len(filtered_agent_tbl[filtered_agent_tbl['call_type']==call_types[call_type_index]])
        agent_costs['call_skewness'][agent_index] = call_distribution_list
        
        if True in call_aht_sum.index.isin([agent_index]):
            agent_costs['idle_time'][agent_index] = 1 - call_aht_sum[agent_index]/86400
        else:
            agent_costs['idle_time'][agent_index] = 1
        #agent_costs
        
        next_call_type_index = call_types.index(next_call['call_type'][0])

        
        if sum(agent_costs['call_skewness'][agent_index]) > 0:
            distribution_cost_factor = call_distribution_ratios[next_call_type_index] - \
            agent_costs['call_skewness'][agent_index][next_call_type_index]/sum(agent_costs['call_skewness'][agent_index])
        else:
            distribution_cost_factor = 0
            
        #print(distribution_cost_factor)
        
        idleness_cost_factor = agent_costs['idle_time'][agent_index]
        #print(idleness_cost_factor)
        switch_cost_factor = 0
        
#        if agent_costs['last_call_type'].notnull()[agent_index]:
        agent_last_call_type_list = agent_tbl[agent_tbl['agent_index']==agent_index]['call_type'].tail(1).values
        if len(agent_last_call_type_list) > 0:
            agent_last_call_type = agent_last_call_type_list[0]
#            print(">>--->>", agent_last_call_type)
            if call_types.index(agent_last_call_type) != next_call_type_index:
                switch_cost_factor = call_switch_agent_time/call_bp_time
        
        #print(switch_cost_factor)
        agent_costs['switch_cost'][agent_index] = switch_cost_factor*weight_switch
        agent_costs['idle_cost'][agent_index] = idleness_cost_factor*weight_idle
        agent_costs['skewness_cost'][agent_index] = distribution_cost_factor*weight_dist
        agent_costs['assignment_cost'][agent_index] = distribution_cost_factor*weight_dist + idleness_cost_factor*weight_idle + switch_cost_factor*weight_switch
    
    #print("---->>--Agent Costs calculated:\n", agent_costs)
    return agent_costs


def currentParameters(call_types, agent_tbl):
    """
    """
    call_distribution_actual = []
    call_distribution_ratios = []
    
    for call_type_index in range(len(call_types)):
        call_distribution_actual.append(len(agent_tbl[(agent_tbl['call_type']==call_types[call_type_index])]))
     
    for call_type_index in range(len(call_types)):
        if sum(call_distribution_actual) > 0:
            call_distribution_ratios.append(call_distribution_actual[call_type_index]/sum(call_distribution_actual))
        else:
            call_distribution_ratios.append(0)
     
    return call_distribution_actual, call_distribution_ratios


def pickLeastCostlyAgent(agent_status, call_types, next_call, 
                         agent_tbl, call_switch_agent_time=7.00, call_bp_time=60.00, weight_idle=1, weight_dist=1, weight_switch=1):
    """
    """
    agent_costs = pd.DataFrame(columns=['agent_index', 'call_skewness', 'idle_time', \
                                    'last_call_type', 'agent_status', 'idle_cost', 'switch_cost', 'skewness_cost', 'assignment_cost'])  
    
    agent_costs['agent_index'] = range(len(agent_status))
    agent_costs['agent_status'] = agent_status
    
    agent_costs = calculateAgentCosts(agent_costs, call_types, next_call, agent_tbl, call_switch_agent_time, call_bp_time, weight_idle=weight_idle, weight_dist=weight_dist, weight_switch=weight_switch)
    if len(agent_costs[agent_costs['agent_status']==1]) == 0:
        #All agents currently busy
        agent_avail_list = cgd.agentNextAvail(agent_status, agent_table_df=agent_tbl)
        pickedAgent = agent_avail_list.index(min(agent_avail_list))
    else:
        #print("Here is the length:", len(agent_costs[agent_costs['agent_status']==1]))
        pickfromAgents = agent_costs[agent_costs['agent_status']==1]['agent_index'].tolist()
        #print("Pick from these agents: ", pickfromAgents)
        pickedAgent = pickfromAgents[agent_costs[agent_costs['agent_status']==1]['assignment_cost'].tolist().index(max(agent_costs[agent_costs['agent_status']==1]['assignment_cost']))]
    
    #print("------->>----")
    #print(agent_costs)
#    agent_costs['last_call_type'][agent_costs['agent_index']==pickedAgent] = next_call.reset_index()['call_type'][0]
    #print("Here are some details:", agent_costs, agent_costs[agent_costs['agent_index']==pickedAgent]['last_call_type'], pickedAgent, next_call.reset_index()['call_type'][0])
    
    return pickedAgent, agent_costs


def agentAggMetrics(agent_tbl, call_types=['inbound', 'outbound']):
    
    agent_list = agent_tbl['agent_index'].drop_duplicates().tolist()
    col_list = ['agent_index', 'call_aht', 'idle_time', 'number_of_switches']
    for i in call_types:
        col_list.append(i)
    agent_metrics = pd.DataFrame(columns=col_list)
    agent_metrics['agent_index'] = agent_list
    agent_metrics_call_aht = []
    number_of_switches = []
    
    for agent_index in agent_list:
        #print(agent_metrics)
        agent_metrics_call_aht.append(agent_tbl[agent_tbl['agent_index']==agent_index]['call_aht'].sum())
        for call_type_i in call_types:
            agent_metrics.loc[agent_metrics['agent_index']==agent_index, call_type_i] = agent_tbl[(agent_tbl['agent_index']==agent_index) & (agent_tbl['call_type']==call_type_i)]['call_type'].count()/agent_tbl[agent_tbl['agent_index']==agent_index]['call_type'].count()
        
        switch_count_tmp = 0
        for call_index in agent_tbl[agent_tbl['agent_index']==agent_index].index.tolist()[0:-1]:
            if agent_tbl['call_type'][call_index] != agent_tbl['call_type'][call_index+1]:
                switch_count_tmp += 1
        number_of_switches.append(switch_count_tmp)
        #print(number_of_switches)
        
    
    agent_metrics['call_aht'] = agent_metrics_call_aht
    agent_metrics['idle_time'] = 1 - agent_metrics['call_aht']/86400.00
    agent_metrics['number_of_switches'] = number_of_switches
    
    
    
    return agent_metrics

def overallMetrics(agent_tbl, call_types=['inbound', 'outbound']):
    """
    """
    total_call_count = len(agent_tbl)
    avg_call_wait = agent_tbl['call_wait_time_elapsed'].mean()
    call_count_by_type = []
    for call_type in call_types:
        call_count_by_type.append(len(agent_tbl[agent_tbl['call_type']==call_type]))
        
    return {'total_call_count': total_call_count,
            'avg_call_wait': avg_call_wait,
            'call_count_by_type': call_count_by_type}

if __name__ == '__main__':
    intvl_avg_calls = list(range(0,24,1)) + list(range(24,0,-1))
    intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
    max_intvl_calls = 2
    intvl_avg_calls = [x*max_intvl_calls/max(intvl_avg_calls) for x in intvl_avg_calls]
    intvl_st_time_day = [(dt.datetime(2018,1,1,0,0,0) + dt.timedelta(minutes= +30*x))  for x in range(len(intvl_avg_calls))]
    intvl_st_time = [dt.time(x.hour, x.minute, x.second) for x in intvl_st_time_day]
    intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
    intvl_call_count = [np.random.poisson(x) for x in intvl_avg_calls]
    aht_range = [300, 400]
    agent_count = 3
    call_tbl = cgd.call_table(intvl_st_time, intvl_call_count, aht_range)
    
    start = timer()
    agent_tbl = cgd.agent_table(int(agent_count), call_tbl, use_cost_calculation=1)
    print("Total Execution Time (sec): ", round(timer()-start,2))
 
    #call_types=['inbound', 'outbound']
    #cgd.updateAgentStatus(call_tbl['call_start_time'][10], [1,1,1], agent_tbl)
    #agentPicked = pickLeastCostlyAgent([1,1,1], call_types, call_tbl[9:10], agent_tbl)
    #print("Agent picked is: ", agentPicked)
 
 