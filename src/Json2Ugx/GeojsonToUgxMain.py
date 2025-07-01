#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 23:13:39 2024

@author: zhongqiuyan

"""

import argparse
import os
import geojson


import GeojsonToUgx


def main():
    
   cwd = os.getcwd()
   
   parser = argparse.ArgumentParser(description="Process GeoJSON file with specified parameters.")
   parser.add_argument('-i', '--input', help="Input: .geojson")  # User can give file(name or path/name) with .geojson or not
   parser.add_argument('-o', '--output', required=True, help='Output: .ugx')  # User can give file(name, path/name) with .ugx or not
   parser.add_argument('-TYPE', default='wgs', help='TYPE: convert to (wgs or utm)')

   args = parser.parse_args()

   output_name = args.output
   input_name = args.input
   
   TYPE = args.TYPE.lower()

   if args.input:
       #print("Pargs.input:", args.input)    
       
       #check if input contains->>> path & .geojson
       if os.path.dirname(args.input):
           if args.input.endswith('.geojson'):
               filepath = os.path.abspath(args.input)
           else:
               filepath = os.path.abspath(args.input + '.geojson')
       else:
           if args.input.endswith('.geojson'):
               filepath = os.path.join(cwd, args.input)
               #if not os.path.isdir(cwd):
                   #print('Current working directory is not valid.')               
           else:
               filepath = os.path.join(cwd, args.input + '.geojson')
               
                   
       if os.path.exists(filepath):
           print(f"File {input_name}' exists in the current directory.")
           #check if output contains->>> path & .ugx
           if args.output:  
               if os.path.dirname(output_name):
                   if output_name.endswith('.ugx'):
                       output_filepath = os.path.abspath(output_name)
                   else:
                       output_filepath = os.path.abspath(output_name + '.ugx')
               
               else:
                   if output_name.endswith('.ugx'):
                       output_filepath = os.path.join(cwd, output_name)
                   else:
                       output_filepath = os.path.join(cwd, output_name + '.ugx')
               OutPutName = os.path.basename(output_name)
           
           
           #input data
           with open(filepath) as f:
               data = geojson.load(f)
               
               #need to normalize input data
               subna = GeojsonToUgx.InputName(data)
               #check input data type wgs or utm
               data_type_str, data = GeojsonToUgx.CheckDataType(data)

               if data_type_str is not None:
                   if 'Point' in data_type_str:
                       print(f"Processing file: {filepath} with filepath='{filepath}', subna='{subna}' ")
                       GeojsonToUgx.PointWriteUgx(data,TYPE, OutPutName)
                   else:
                       delimiter = GeojsonToUgx.InputDelimiter(delimiter=None)
                       print(f"Processing file: {filepath} with filepath='{filepath}', subna='{subna}', and delimiter='{delimiter}'")
                       GeojsonToUgx.PolygonLineWriteUgx(data, TYPE, OutPutName,subna,delimiter,data_type_str)
               else:
                   print("Unknown data type")
                 
       else:
           print(f"File '{input_name}' does not exist in the current directory.")
                    
   else:
       print('Please provide the right filepath and filename')

  


if __name__ == "__main__":
    
    main()
    
 