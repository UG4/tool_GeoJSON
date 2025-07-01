#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sat Oct 19 20:17:10 2024

@author: zhongqiuyan

convert .geojson to .ugx 

"""


#import geojson
import pandas as pd
import xml.etree.cElementTree as ET
#import numpy as np
import WgsToUtm



def CheckDataType(data):
    """
    have some different data types to check, like 
    Point_geojson, MultiPoint_geojson, Linear_geojson,
    MultiLinear_geojson, Polygon_geojson, MultiPolygon_geojson.

    but here all_type_list = ['Polygon', 'Polygon', 'MultiPolygon', 'MultiPolygon']
    actually they are the same type, so need to normalize the strings by removing 
    'Multi'

    check whether all geometry types in the data are the the same.
        if SAME, then print the type.
        if NOT SAME, then print all_different_type_list.
        
    """

    data_type_str = None
    data_result = None

    try:

        type_n = 0

        all_type_list = []

        for x in data['features']:
            type_n = type_n + 1
            y1 = str(x['geometry']['type'])

       

        if type_n == 1:
            print('The only one type of geometry is:', y1)
            data_type_str = str(y1)

        else:
            for x in data['features']:
                y2 = str(x['geometry']['type'])
                all_type_list.append(y2)
            #print("All Type list is:",all_type_list)

            normalized_list = [element.replace(
                'Multi', '') for element in all_type_list]

            all_strings_same = all(
                element == normalized_list[0] for element in normalized_list)

            if all_strings_same:

                data_type_str = str(normalized_list[0])
                print("All types of geometry in the data are the same:", data_type_str)

            else:
                print("Not all types of geometry in the data are the same.", all_type_list)

        return data_type_str, data

    except ValueError:
        print("Oops! Please try again!")


def ExtractCoordinates(data):
    """
    Most of the Subset have no recursive list, but still the structure of the subset will be different.
    So hier want to unify the structure of subsets.

    * Although in some subsets have recursive list, all data can still be read out.

    Like Polygon1 and Polygon2:

    Polygon2 = [
                [[14,53],[13,53],[11,53],[11,53]]
                ]    

    Polygon2 = [
                [[[14,53],[13,53],[11,53],[11,53]]]
                ]

    Return:

        Polygon = [
                [[14,53],[13,53],[11,53],[11,53]]
                ]          
    """

    coordinates = []

    def RecursiveExtract(coord):
        if isinstance(coord, list):
            if all(isinstance(subcoord, (float, int)) for subcoord in coord):
                coordinates.append(coord)
            else:
                for subcoord in coord:
                    RecursiveExtract(subcoord)
        elif isinstance(coord, (float, int)):
            coordinates.append(coord)

    RecursiveExtract(data)

    return coordinates


def UniRecursiveType(polygon):
    """
    In some Subsets exist recursive list, and the structure of recursive list will be different,
    So hier want to unify the structure of recursive list. 
    Like Polygon1 and Polygon2:

    Polygon1 = [  
                [[[116, 39.], [116, 40],  [11, 39]]],
                [[[113, 36], [113, 36]]]
                ]

    Polygon2 = [
            [[14, 53], [13, 53]],
            [[13, 52]]
            ]

    Return:

    Polygon = [
            [[14, 53], [13, 53]],
            [[13, 52]]
            ]        

    """

    input_sub = []

    for sub in polygon:
        contains_two_coordinates = False

        for mini_sub in sub:
            if isinstance(mini_sub, list) and all(isinstance(coord, (float, int)) for coord in mini_sub) and len(mini_sub) == 2:
                contains_two_coordinates = True
                input_sub.append(sub)
                break  # Exit the inner loop once a valid sublist is found

        if not contains_two_coordinates:
            # Append the first sublist if no valid sublist is found
            input_sub.append(sub[0])

    return input_sub



def InputName(data):
    """
    usually in the 'properties', there are many key-names can be choosed, and will be used in later

    """

    subna = None
    # Check if subna has been set before
    if data.get('subna'):
        print(f"Using the previous value for subna: {data['subna']}\n")
        return data['subna']

    for feature in data.get('features', []):

        properties = feature.get('properties', {})

        if properties:
            print(
                'This is one of the properties, where can choose the subset name.',  '\n')
            print(properties)

            subna = input(
                'please input the key of the subset name (like id or name or anything else!!): ')

            break

        else:
            print("Empty properties")
            subna = 'subset'
            break

    print(subna)
    print('\n')
    return subna


def InputDelimiter(delimiter=None):

    # If delimiter is not provided, ask the user to choose it
    if delimiter is None:

        delimiter = input(
            'Please do not use a delimiter that has been used by subset name,like(-, /, or others):',)

    return delimiter


def BasicDataframe(data):
    """
    Para: 
        all coordinate from geojson

    Return:
        global_vertex_table: all coordinates from all subsets
        global_unique_vertex_table: no repeat coordinates from all subsets
        global_unique_VertexIndex_table: merge global_vertex_table and  global_unique_vertex_table get reindex for all coordinates

    """

    global_vertex_table = pd.DataFrame(columns=['Longitude', 'Latitude'])
    
    for feature in data.get('features', []):
        coords = feature['geometry']['coordinates']
        new_coords = ExtractCoordinates(coords)

        local_vertex_table = pd.DataFrame(
            new_coords, columns=['Longitude', 'Latitude'])
        local_vertex_table['Coordinate'] = list(
            zip(local_vertex_table['Longitude'], local_vertex_table['Latitude']))
        
        print('local_vertex_table',local_vertex_table,'\n'*2)
        #Get all Vertex include repeated
        global_vertex_table = pd.concat([global_vertex_table, local_vertex_table], ignore_index=True)
    print('global_vertex_table',global_vertex_table,'\n'*2)

    #Get all unique Vertex
    global_unique_vertex_table = global_vertex_table.drop_duplicates(
        subset=['Longitude', 'Latitude'], keep='first').reset_index(drop=True)
    
    global_unique_vertex_table.reset_index(drop=True, inplace=True)
    print('global_unique_vertex_table', global_unique_vertex_table, '\n'*2)

      

    #All vertex(include repeat vertex) get the unique indices 
    global_unique_VertexIndex_table = pd.merge(global_vertex_table, global_unique_vertex_table.reset_index(),
         how='left', left_on='Coordinate', right_on='Coordinate', suffixes=('_global_vertex_table', '_global_unique_vertex_table'))
    
    global_unique_VertexIndex_table = global_unique_VertexIndex_table.drop(
        ['Longitude_global_unique_vertex_table', 'Latitude_global_unique_vertex_table'], axis=1)
    
    print('global_unique_VertexIndex_table', global_unique_VertexIndex_table, '\n'*2)

    return global_unique_vertex_table, global_unique_VertexIndex_table


def AllEdgesDataframe(data, subna, delimiter):
    """
    Para:
        global_unique_vertex_table

    Compared to global_unique_vertex_table, each subset get SubsetName and reindex column
    Because 2 points generate 1 edge, so each-subset-dataframe get edge-sets and it's SubsetName column
    combine all pairs and SubsetName. Drop all repeat pairs, get dataframe with no repeat pairs and combine 
    the SubsetName
    merge global_edges_table with global_unique_edges_table get all edge pairs with common SubsetName and it's reindex

    Return: 
        updated_global_edges_table: include all edges common SubsetName und reindex 

    """

    global_unique_vertex_table, global_unique_VertexIndex_table = BasicDataframe(data)

  
    all_coor_df = pd.DataFrame(columns=['Coordinate', 'index', 'Subset_Name'])
    global_edges_table = pd.DataFrame(columns=['Pairs', 'Subset_Name'])

    all_subset_index_list = []
    for feature in data.get('features', []):
        coords = feature['geometry']['coordinates']
        properties = feature.get('properties', {})
        uni_coords = UniRecursiveType(coords)
        new_coords = ExtractCoordinates(coords)
        # print('new_coords',new_coords)

        if subna in properties and properties[subna]:
            subset_name = properties[subna]
        else:
            subset_name = 'subset'

         #Check the subset has recursive list or not
        if len(coords[0]) < len(new_coords):
            #print('Exist Recursive List')
            
            #One local-edges-table include all Parts in recursive list 
            sub_local_edges_table = pd.DataFrame(columns=['Pairs', 'Subset_Name'])
            
            
            #Rename each part in recursive list
            part_i=0
            for part in uni_coords:          
                part_i=part_i+1
                
                
                #Each Part get unique-index and name
                part_unique_local_vertex_table = pd.DataFrame(
                    part, columns=['Longitude', 'Latitude'])
                
                part_unique_local_vertex_table['Coordinate'] = list(
                    zip(part_unique_local_vertex_table['Longitude'], part_unique_local_vertex_table['Latitude']))
                
                part_unique_local_vertex_table = pd.merge(part_unique_local_vertex_table, global_unique_vertex_table.reset_index(), how='left', left_on='Coordinate',
                                                 right_on='Coordinate', suffixes=('_part_unique_local_vertex_table', '_global_unique_vertex_table'))
                
                part_unique_local_vertex_table = part_unique_local_vertex_table.drop(
                    ['Longitude_global_unique_vertex_table', 'Latitude_global_unique_vertex_table'], axis=1)
                
                part_local_unique_VertexIndex_table = part_unique_local_vertex_table.copy()
                
                part_local_unique_VertexIndex_table['Subset_Name'] = subset_name+str(part_i)              
                #print('unique_local_vertex_table', unique_local_vertex_table,'\n'*2)
                #print('part_local_unique_VertexIndex_table',part_local_unique_VertexIndex_table)


                #Combine Edges for each part
                part_subset_reindex = part_local_unique_VertexIndex_table['index'].tolist()
                pairs = [(min(part_subset_reindex[i], part_subset_reindex[i + 1]), max(part_subset_reindex[i],
                                                                                       part_subset_reindex[i + 1])) for i in range(len(part_subset_reindex) - 1)]
                part_local_edges_table = pd.DataFrame(
                    {'Pairs': pairs, 'Subset_Name': subset_name+str(part_i)})
                
                #Summern all parts edges in local_edges_table
                sub_local_edges_table = pd.concat(
                    [sub_local_edges_table, part_local_edges_table], ignore_index=True)

                #print('sub_local_edges_table', sub_local_edges_table)
                
                
                
                all_subset_index_list.append(
                    part_unique_local_vertex_table['index'].tolist())
                
                part_local_unique_VertexIndex_table = part_local_unique_VertexIndex_table[['Coordinate', 'index', 'Subset_Name']]
                all_coor_df = pd.concat([all_coor_df, part_local_unique_VertexIndex_table], ignore_index=True)
                #print('part_local_unique_VertexIndex_table.columns', part_local_unique_VertexIndex_table.columns,all_coor_df )
                

            #Get all edges from all of the subsets
            global_edges_table = pd.concat(
                [global_edges_table, sub_local_edges_table], ignore_index=True)
            
           
        else:

            #print('No Recursive List')

            unique_local_vertex_table = pd.DataFrame(
                new_coords, columns=['Longitude', 'Latitude'])

            unique_local_vertex_table['Coordinate'] = list(
                zip(unique_local_vertex_table['Longitude'], unique_local_vertex_table['Latitude']))

            #All Vertex in each Subset get unique indices from global_unique_vertex_table
            unique_local_vertex_table = pd.merge(unique_local_vertex_table, global_unique_vertex_table.reset_index(
            ), how='left', left_on='Coordinate', right_on='Coordinate', suffixes=('_unique_local_vertex_table', '_global_unique_vertex_table'))

            unique_local_vertex_table = unique_local_vertex_table.drop(
                ['Longitude_global_unique_vertex_table', 'Latitude_global_unique_vertex_table'], axis=1)

            #All Vertex in each Subset get subset-name and unique index
            local_unique_VertexIndex_table = unique_local_vertex_table.copy() 
            local_unique_VertexIndex_table['Subset_Name'] = subset_name

            #print('unique_local_vertex_table', unique_local_vertex_table, '\n'*2)
            print('local_unique_VertexIndex_table', local_unique_VertexIndex_table, '\n' * 2)

            
            all_subset_index_list.append(unique_local_vertex_table['index'].tolist())
            subset_reindex = local_unique_VertexIndex_table['index'].tolist()
            #print('!!!!!!!!!!!!', subset_reindex, len(subset_reindex), '\n' * 2)

            #Each Subset get edges
            pairs = [(min(subset_reindex[i], subset_reindex[i + 1]), max(subset_reindex[i],
                                                                         subset_reindex[i + 1])) for i in range(len(subset_reindex) - 1)]
            local_edges_table = pd.DataFrame(
                {'Pairs': pairs, 'Subset_Name': subset_name})
            print('local_edges_table', local_edges_table, '\n' * 2)

        
            global_edges_table = pd.concat(
                [global_edges_table, local_edges_table], ignore_index=True)
            print('global_edges_table', global_edges_table,'\n' * 2)
            
            
            
            local_unique_VertexIndex_table = local_unique_VertexIndex_table.rename(columns={
    'Longitude_unique_local_vertex_table': 'Longitude',
    'Latitude_unique_local_vertex_table': 'Latitude'
})
            
            
            local_unique_VertexIndex_table = local_unique_VertexIndex_table[['Coordinate', 'index', 'Subset_Name']]
            all_coor_df = pd.concat([all_coor_df, local_unique_VertexIndex_table], ignore_index=True)


    #print('global_edges_table', global_edges_table, '\n' * 2)
    #print('all_coor_df', all_coor_df, '\n' * 2)


    # Extract unique pairs from global_edges_table, set(x)can automatically removes duplicate values.
    global_unique_edges_table = global_edges_table.groupby('Pairs')['Subset_Name'].agg(
        lambda x: str(delimiter).join(set(x))).reset_index()

    print('global_unique_edges_table', global_unique_edges_table, '\n' * 2)
    #print('all_subset_index_list', all_subset_index_list, '\n'*2)


    #Update global edges
    result_edges_df = global_edges_table[['Pairs']].copy()
    #print('result_edges_df', result_edges_df, '\n'*2)
    updated_global_edges_table = pd.DataFrame({'Pairs': global_edges_table['Pairs']})
   
    updated_global_edges_table = pd.merge(
        updated_global_edges_table, global_unique_edges_table, how='left', on='Pairs')
    print('updated_global_edges_table', updated_global_edges_table, '\n'*2)


    updated_global_edges_table['reindex'] = updated_global_edges_table.index
    updated_global_edges_table['reindex'] = updated_global_edges_table.groupby(
        'Pairs').transform('first')['reindex']

    #print('updated_global_edges_table', updated_global_edges_table, '\n'*2)
    
    
    return all_subset_index_list, updated_global_edges_table,all_coor_df



def AllVerticesDataframe(data, subna, delimiter):
    """
    Para:
        global_unique_vertex_table
        global_unique_VertexIndex_table

    Each Subset-Dataframe with coordiantes and SubsetName columns, then combine all these 
    subset dataframes, get one dataframe with all coordinates and SubsetName from all subsets.
    Drop all same coordinates and combine all SubsetName. 

    Return:
        updated_global_vertex_table (all coordinates with reindex and common SubsetName)

   
    """

    all_subset_index_list, updated_global_edges_table,all_coor_df = AllEdgesDataframe(
        data, subna, delimiter)
    
    global_unique_vertex_table, global_unique_VertexIndex_table = BasicDataframe(data)
    

    #Use delimiter to combine all subset-name according to the same vertex-index
    merged_df_with_subna = pd.merge(global_unique_vertex_table, all_coor_df[[
                                    'Coordinate', 'Subset_Name']], on='Coordinate', how='left')

    merged_df_with_subna['Subset_Name'] = merged_df_with_subna.groupby(
        'Coordinate')['Subset_Name'].transform(lambda x:  str(delimiter).join(set(x)))

    merged_df_with_subna = merged_df_with_subna.drop_duplicates(
        subset=['Longitude', 'Latitude', 'Coordinate'])
    #print('merged_df_with_subna', merged_df_with_subna)
    


    #All vertex(with unique index) get combined name
    updated_global_vertex_table = global_unique_VertexIndex_table.merge(
        merged_df_with_subna[['Coordinate', 'Subset_Name']], on='Coordinate', how='left')
    
    updated_global_vertex_table = updated_global_vertex_table.drop(
        ['Longitude_global_vertex_table', 'Latitude_global_vertex_table'], axis=1)
    print('updated_global_vertex_table', updated_global_vertex_table, '\n'*2)
    
    
    return updated_global_vertex_table



def CombinationVerticesEdgesList(data,coor_type,subna,delimiter):
    """
    Para: 
        global_unique_vertex_table
        all_subset_index_list

    get not_repeat coordinates from (global_unique_vertex_table).
    get edge sets list from (all_subset_index_list).

    Return:
        vertices_list
        edges_list

    """


    global_unique_vertex_table, global_unique_VertexIndex_table = BasicDataframe(data)

    all_subset_index_list,updated_global_edges_table,all_coor_df = AllEdgesDataframe(
        data, subna, delimiter)

    # get all unique vertex coordinates 
    coordinates = global_unique_vertex_table['Coordinate'].tolist()
    #coor_type = args.TYPE.lower()
    
    if coor_type=='wgs':
        type_coor = coordinates
    
    else:
        utm_df = pd.DataFrame()
        utm_coordinates = WgsToUtm.get_utm_coordinates(coordinates)
    #print('!!!!coordinates:',coordinates,'\n','1',coordinates[0],'2',coordinates[0][0], '3',coordinates[0][1])
    
        utm_df['WGS Coordinate'] = global_unique_vertex_table['Coordinate']
        utm_df['UTM(x,y)'] = utm_coordinates
        
    #utmm_df = utm_df.drop(columns=['Longitude', 'Latitude'], axis=1)
        print('!!!utm_df',utm_df,'\n'*2)
        type_coor=utm_coordinates
    
    #Turn all unique vertex coordinates into string 'x y 0'
    vertices_array = []
    coord_number = 0
    for coord in type_coor:
        coord_number += 1
        vertices_array.append(coord[0])
        vertices_array.append(coord[1])
        vertices_array.append(0)  
    vertices_list = ''
    for n in vertices_array:
        vertices_list = vertices_list + str(n) + ' '
    #print('vertices_list:', vertices_list, '\n',
          #'coord_number:', coord_number, '\n'*2)


    #Get all successively vertex index and turn into string
    edges_array = []
    for sub in all_subset_index_list:
        for n in range(len(sub)):
            if n >= (len(sub)-1):
                pass
            else:
                edges_array.append(sub[n])
                edges_array.append(sub[n+1])
    #print('edges_array', edges_array, '\n'*2)
    edges_list = ''
    for n in edges_array:
        edges_list = edges_list + str(n) + ' '
    #print('edges_list:', edges_list, '\n'*2)
    return vertices_list, edges_list, coord_number



def PointWriteUgx(data,coor_type,output_name):
    """
    point.json is simpler 

    Para:
        get global_unique_vertex_table, global_unique_VertexIndex_table from BasicDataframe(data)
    """
    
    

    global_unique_vertex_table, global_unique_VertexIndex_table = BasicDataframe(data)
    #subna = InputName(data)
    coords = global_unique_vertex_table['Coordinate'].tolist()

    #print('coords:', coords, len(coords), '\n')
    #
    #/choose coordinates type
    #
    #coor_type = args.TYPE.lower()
    
    if coor_type=='wgs':
        type_coor = coords
    
    else:
        
        utm_df = pd.DataFrame()
        utm_coordinates = WgsToUtm.get_utm_coordinates(coords)
    #print('!!!!coordinates:',coordinates,'\n','1',coordinates[0],'2',coordinates[0][0], '3',coordinates[0][1])
    
        utm_df['WGS Coordinate'] = global_unique_vertex_table['Coordinate']
        utm_df['UTM(x,y)'] = utm_coordinates
        
        #print('!!!utm_df',utm_df,'\n'*2)
        type_coor=utm_coordinates
    

    coords_list = ''
    for n in range(len(type_coor)):
        coords_list = coords_list + str(type_coor[n][0]) + ' '
        coords_list = coords_list + str(type_coor[n][1]) + ' '
        coords_list = coords_list + str(0) + ' '
        # print(coords[n][0])
    #print('coords_list:', coords_list, "\n")

    root = ET.Element('grid', name="defGrid")
    ET.SubElement(root, 'vertices', coords='3').text = str(coords_list)
    subset_handler = ET.SubElement(root, 'subset_handler', name="defSH")

    index = global_unique_VertexIndex_table['index'].tolist()
    #print('index:', index)

    vertices_list = ''
    for i in index:
        vertices_list = vertices_list + str(i) + ' '
    #print('vertices list:', vertices_list)
    
    subset = ET.SubElement(subset_handler, 'subset', name='subset',
                              color="0.588235 0.588235 1 1", state="393216")
    ET.SubElement(subset, 'vertices').text = vertices_list
    ET.SubElement(root, 'selector', name="defSel")
    projection_handler = ET.SubElement(
        root, 'projection_handler', name="defPH", subset_handler="0")
    ET.SubElement(projection_handler, 'default',
                  type="default").text = str(0) + ' ' + str(0)
    tree = ET.ElementTree(root)
    tree.write(output_name, encoding='utf-8', xml_declaration=True)



def PolygonLineWriteUgx(data,coor_type,output_name,subna,delimiter,data_type_str): 
    """
    usually the data structure of polygon is relatively complex.
    even in some subset will appear recursively process nested list, 
    so use extract_coordinates(data) function to solve this problem

    - update vertices dataframe (both_subset_df or all_subset_index_list
    - update edges dataframe 

    return:
    --not repeat vertice coordinates combination list
    --the corresponding index of all points(including all repeated points)
    --edges_subset_list
    --vertices_subset_list
    
    """

   

    vertices_list, edges_list,coord_number = CombinationVerticesEdgesList(data,coor_type,subna,delimiter)

    updated_global_vertex_table = AllVerticesDataframe(data, subna, delimiter)

    all_subset_index_list, updated_global_edges_table,all_coor_df = AllEdgesDataframe(
        data, subna, delimiter)

 
    root = ET.Element('grid', name="defGrid")
    #print("\n")
    ET.SubElement(root, 'vertices', coords='3').text = str(vertices_list)
    #print('\n')

    # get edges list

    ET.SubElement(root, 'edges').text = str(edges_list)
    #print('\n')
    subset_handler = ET.SubElement(root, 'subset_handler', name="defSH")

    ########################################################################

    #print('!!!!!!!!vertices_list', vertices_list, '\n')
    #print('!!!!!!!!edges_list', edges_list, '\n')
    #print('!!!!!!!!updated_global_vertex_table', updated_global_vertex_table, '\n')
    #print('!!!!!!!!!updated_global_edges_table ', updated_global_edges_table, '\n')

    ##########################################################################

    edges_li = updated_global_edges_table['reindex'].tolist() 
    #print('edges_li',edges_li)
    ##########################################################################
    if 'Line' in data_type_str:
        coords_list = ''
        edges_list = ''
        for n in range(coord_number):
            coords_list = coords_list + str(n) + ' '
        for i in edges_li:
            edges_list = edges_list + str(i) + ' '
       
        #print('coords_list:', coords_list, "\n")
        #print('edges_list:', edges_list, "\n")
        subset = ET.SubElement(subset_handler, 'subset', name=subna,color="0.588235 0.588235 1 1", state="393216")
        ET.SubElement(subset, 'vertices').text = coords_list
        ET.SubElement(subset, 'edges').text = edges_list
        
    else:
        
        #Get all Unique Subset_Name values (no duplicates)
        name_categories = updated_global_edges_table['Subset_Name'].tolist()

        unique_subset_names = list(set(name_categories))
        print("\nUnique Subset_Name values (no duplicates):",
          unique_subset_names, len(unique_subset_names), '\n')

        #According to the unique name category, output vertices index and edges index
        for i in range(len(unique_subset_names)):

            aim_name = unique_subset_names[i]

            vertices_array = updated_global_vertex_table[updated_global_vertex_table['Subset_Name']
                                            == aim_name]['index'].tolist()
            edges_array = updated_global_edges_table[updated_global_edges_table['Subset_Name']
                                         == aim_name]['reindex'].tolist()

            print('aim_name', aim_name)
            print('vertices_array', vertices_array)
            print('edges_array', edges_array)

            vertices_list = ''
            edges_list = ''
            for n in range(len(vertices_array)):
                vertices_list = vertices_list + str(vertices_array[n])+' '
            #print('vertices_list', vertices_list)

            for n in range(len(edges_array)):
                edges_list = edges_list + str(edges_array[n])+' '

            #print('edges_list', edges_list)

            subset = ET.SubElement(subset_handler, 'subset', name=aim_name,
                               color="0.588235 0.588235 1 1", state="393216")
            ET.SubElement(subset, 'vertices').text = vertices_list
            ET.SubElement(subset, 'edges').text = edges_list

    ET.SubElement(root, 'selector', name="defSel")
    projection_handler = ET.SubElement(
        root, 'projection_handler', name="defPH", subset_handler="0")
    ET.SubElement(projection_handler, 'default',
                  type="default").text = str(0) + ' ' + str(0)
    tree = ET.ElementTree(root)
    tree.write(output_name, encoding='utf-8', xml_declaration=True)

