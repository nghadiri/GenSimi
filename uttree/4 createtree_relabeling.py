# -*- coding: utf-8 -*-
import os
import pandas as pd
import networkx as nx
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
settings = load_app_settings()

inputdir=settings['directories']['input_dir']+"proc\\"
targetdir=settings['directories']['target_dir']+"proc\\"
ddir=settings['directories']['def_dir']

def hierarchy_pos(G, root, levels=None, width=1., height=1.):
    '''Function to draw a hierarchical tree structure'''
    TOTAL = "total"
    CURRENT = "current"
    
    def make_levels(levels, node=root, currentLevel=0, parent=None):
        """Compute the number of nodes for each level"""
        if not currentLevel in levels:
            levels[currentLevel] = {TOTAL : 0, CURRENT : 0}
        levels[currentLevel][TOTAL] += 1
        neighbors = G.neighbors(node)
        for neighbor in neighbors:
            if not neighbor == parent:
                levels =  make_levels(levels, neighbor, currentLevel + 1, node)
        return levels

    def make_pos(pos, node=root, currentLevel=0, parent=None, vert_loc=0):
        dx = 1/levels[currentLevel][TOTAL]
        left = dx/2
        pos[node] = ((left + dx*levels[currentLevel][CURRENT])*width, vert_loc)
        levels[currentLevel][CURRENT] += 1
        neighbors = G.neighbors(node)
        for neighbor in neighbors:
            if not neighbor == parent:
                pos = make_pos(pos, neighbor, currentLevel + 1, node, vert_loc-vert_gap)
        return pos
    
    if levels is None:
        levels = make_levels({})
    else:
        levels = {l:{TOTAL: levels[l], CURRENT:0} for l in levels}
    
    vert_gap = height / (max([l for l in levels])+1)
    return make_pos({})

def process_file(file_path):
    # Load the data from the merged CSV
    Stage_df2 = pd.read_csv(file_path)

    Times = Stage_df2.Time.unique()
    TemporalEventTypes = Stage_df2.TemporalEventType.unique()

    PG = nx.DiGraph()
    PG.add_node('PID')
    root = 'PID'
    for i in Times:
        PG.add_node(i)
        PG.add_edge(root, i)

    L_1 = list(PG.successors(root))

    for i in L_1:
        PG.add_node('Retro' + '-' + str(PG.number_of_nodes()), TE='Retro')
        PG.add_edge(i, 'Retro'  + '-' + str(PG.number_of_nodes() - 1))
        PG.add_node('New Finding'  + '-' + str(PG.number_of_nodes()), TE='New_Finding')
        PG.add_edge(i, 'New Finding'  + '-' + str(PG.number_of_nodes() - 1))
        PG.add_node('RealTime'  + '-' + str(PG.number_of_nodes()), TE='RealTime')
        PG.add_edge(i, 'RealTime'  + '-' + str(PG.number_of_nodes() - 1))

    L2_Retro = [x for x, y in PG.nodes(data=True) if list(y.keys()) == ['TE'] and list(y.values()) == ['Retro']]

    for i in range(len(L2_Retro)):
        PG.add_node('DiseaseDisorderMention' + '-' + str(PG.number_of_nodes()), value='Diabet Mellitus')
        PG.add_edge(L2_Retro[i], 'DiseaseDisorderMention' + '-' + str(PG.number_of_nodes() - 1))
        PG.add_node('Demographic' + '-' + str(PG.number_of_nodes()), value='Femail_40')
        PG.add_edge(L2_Retro[i], 'Demographic' + '-' + str(PG.number_of_nodes() - 1))

    L2_New_Finding = [x for x, y in PG.nodes(data=True) if list(y.keys()) == ['TE'] and list(y.values()) == ['New_Finding']]

    for i in range(len(L2_New_Finding)):
        predecessor = list(PG.predecessors(L2_New_Finding[i]))
        Tmp_df_New_Finding = Stage_df2.loc[
            (Stage_df2['TemporalEventType'] == 'New Finding') & 
            (Stage_df2['Event'] != 'Demographic') & 
            (Stage_df2['Time'] == predecessor[0]), 
            ['Event', 'Value']
        ]
        Ls_Event_New_Finding = Tmp_df_New_Finding.reset_index()[['Event', 'Value']].values.tolist()
        if len(Ls_Event_New_Finding) > 0:
            for j in range(len(Ls_Event_New_Finding)):
                PG.add_node(Ls_Event_New_Finding[j][0] + '-' + str(PG.number_of_nodes()), value=Ls_Event_New_Finding[j][1])
                PG.add_edge(L2_New_Finding[i], Ls_Event_New_Finding[j][0] + '-' + str(PG.number_of_nodes() - 1))

    L2_RealTime = [x for x, y in PG.nodes(data=True) if list(y.keys()) == ['TE'] and list(y.values()) == ['RealTime']]

    for i in range(len(L2_RealTime)):
        predecessor = list(PG.predecessors(L2_RealTime[i]))
        Tmp_df_RealTime = Stage_df2.loc[
            (Stage_df2['TemporalEventType'] == 'RealTime') & 
            (Stage_df2['Time'] == predecessor[0]), 
            ['Event', 'Value']
        ]
        Ls_Event_RealTime = Tmp_df_RealTime.reset_index()[['Event', 'Value']].values.tolist()
        if len(Ls_Event_RealTime) > 0:
            for j in range(len(Ls_Event_RealTime)):
                PG.add_node(Ls_Event_RealTime[j][0] + '-' + str(PG.number_of_nodes()), value=Ls_Event_RealTime[j][1])
                PG.add_edge(L2_RealTime[i], Ls_Event_RealTime[j][0] + '-' + str(PG.number_of_nodes() - 1))

    remove_nodes = []
    for node in PG.nodes:
        if (nx.shortest_path_length(PG, source='PID', target=node) == 2 and PG.out_degree(node) == 0):
            remove_nodes.append(node)
    for i in remove_nodes:
        PG.remove_node(i)

    # Relabeling Level 3
    L3_nodes = []
    for node in PG.nodes:
        if (nx.shortest_path_length(PG, source='PID', target=node) == 2):
            L3_nodes.append(node)

    for i in L3_nodes:
        new_label_1 = ''
        D = dict(nx.bfs_predecessors(PG, i))
        Ls_tmp = [k for k, v in D.items()]
        for j in Ls_tmp:
            new_label_1 = new_label_1 + '_' + j + '_' + PG.nodes[j]['value']

        mapping = {i: new_label_1}
        PG = nx.relabel_nodes(PG, mapping)

    # Relabeling Level 2
    L2_nodes = []
    for node in PG.nodes:
        if (nx.shortest_path_length(PG, source='PID', target=node) == 1):
            L2_nodes.append(node)

    for i in L2_nodes:
        new_label_1 = ''
        D = dict(nx.bfs_predecessors(PG, i))
        Ls_tmp = [k for k, v in D.items()]
        for j in Ls_tmp:
            new_label_1 = new_label_1 + '_' + j

        mapping = {i: new_label_1}
        PG = nx.relabel_nodes(PG, mapping)

    # Relabeling Level 1
    D = dict(nx.bfs_predecessors(PG, 'PID'))
    Ls_tmp = [k for k, v in D.items()]
    new_label_1 = ''
    for j in Ls_tmp:
        new_label_1 = new_label_1 + '_' + j

    mapping = {'PID': new_label_1}
    PG = nx.relabel_nodes(PG, mapping)
    root = new_label_1

    # Create final String
    T = nx.bfs_tree(PG, source=root)
    bfs_string = list(T.nodes())
    s1 = bfs_string[0].replace('__', '_')
    s2 = re.sub(r"(-[1-9][0-9]*)", r"", s1)

    return s2

def process_all_files_in_folder(folder_path):
    # Scan the folder for merged CSV files
    merged_folder_path = os.path.join(folder_path, 'merged')
    for file_name in os.listdir(merged_folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(merged_folder_path, file_name)
            s2 = process_file(file_path)
            txt_file_name = file_name.replace('.csv', '.txt')
            txt_file_path = os.path.join(merged_folder_path, txt_file_name)
            with open(txt_file_path, 'w') as txt_file:
                txt_file.write(s2)
            print(f"Processed and saved: {txt_file_path}")

# Usage
folder_path = targetdir
process_all_files_in_folder(folder_path)
