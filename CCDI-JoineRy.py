#!/usr/bin/env python3

#CCDI-JoineRy.py

##############
#
# Env. Setup
#
##############

#List of needed packages
import pandas as pd
import argparse
import argcomplete
import os
import sys
from datetime import date
import warnings
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows


parser = argparse.ArgumentParser(
                    prog='CCDI-JoineRy.py',
                    description='Takes a set of TSV outputs from the CCDI Explorer, concatenates and restores ids to match the given CCDI template.',
                    )

required_arg = parser.add_argument_group("required arguments")
optional_arg = parser.add_argument_group("optional arguments")

required_arg.add_argument(
    '-d',
    '--directory', 
    type=str,
    help='directory of tsv/csv node files', 
    required=True)

required_arg.add_argument(
    '-t',
    '--template', 
    type=str,
    help='dataset template file, CCDI_submission_metadata_template.xlsx', 
    required=True)

argcomplete.autocomplete(parser)

args = parser.parse_args()

#pull in args as variables
directory_path=args.directory
template_path=args.template

print('\nThe CCDI submission template is created from the node tsv/csv files.\n\n')


##############
#
# Pull Dictionary Page to create node pulls
#
##############

def read_xlsx(file_path: str, sheet: str):
    #Read in excel file
    warnings.simplefilter(action='ignore', category=UserWarning)
    return pd.read_excel(file_path, sheet, dtype=str)

#create workbook
xlsx_model=pd.ExcelFile(template_path)

#create dictionary for dfs
model_dfs= {}

#check to make sure Dictionary and Terms and Value Sets are in the template
if not "Dictionary" in xlsx_model.sheet_names or not "Terms and Value Sets" in xlsx_model.sheet_names:
    print("ERROR: The template file needs to contain both a 'Dictionary' and 'Terms and Value Sets' tab.")
    sys.exit(1)

#read in dfs and apply to dictionary
for sheet_name in xlsx_model.sheet_names:
    model_dfs[sheet_name]= read_xlsx(xlsx_model, sheet_name)


##############
#
# Find files and read them in
#
##############

directory_file_list=os.listdir(directory_path)

# Separate CSV and TSV files
csv_files = [file for file in directory_file_list if file.lower().endswith('.csv')]
tsv_files = [file for file in directory_file_list if file.lower().endswith('.tsv')]


dfl_dfs={}

for tsv_file in tsv_files:
    df=pd.read_csv(directory_path+'/'+tsv_file, sep="\t")
    df_type=df['type'].unique().tolist()[0]
    dfl_dfs[df_type]=df

for csv_file in csv_files:
    df=pd.read_csv(directory_path+'/'+csv_file)
    df_type=df['type'].unique().tolist()[0]
    dfl_dfs[df_type]=df


##############
#
# File name rework
#
##############

#Find study_id and use that for output file:
study_id=dfl_dfs['study']['study_id'].unique().tolist()[0]

#Find version of template being used
template_ver=model_dfs['README and INSTRUCTIONS'].columns.tolist()[2]

#Determine abs path
file_dir_path=os.path.split(os.path.abspath(directory_path))[0]

if file_dir_path=='':
    file_dir_path="."

#obtain the date
def refresh_date():
    today=date.today()
    today=today.strftime("%Y%m%d")
    return today

todays_date=refresh_date()

#Output file name based on input file name and date/time stamped.
output_file=(study_id+
            "_CCDI_"+
            template_ver+
            "_JoineRy"+
            todays_date)


##############
#
# Fix the linking columns in each df
#
##############

# Since we remove the linking nodes for the data model [node].[node]_id for the more simplistic linking of [node].id, we have to reapply the linking setup.
# For more information on this, please go to CCDIDC-549:
# "Delete the [node].[node]_id column, as the loader cannot differentiate which column the connection should be made to."

for node in dfl_dfs.items():
    node_df=node[1]
    if 'type' in node_df.columns:
        type=node[0]
        if any('.id' in col for col in node_df.columns):
            id_cols=['.id' in col for col in node_df.columns]
            id_cols=node_df.columns[id_cols].tolist()
            for new_id in id_cols:
                parent_node=new_id.split('.')[0]
                new_col=parent_node+"."+parent_node+"_id"
                node_df[new_col]=node_df[new_id]
                if not node_df[new_id].isna().all():
                    node_df[new_col]=node_df[new_col].str.split("::").str[1]

        #for columns in the model
        for column in model_dfs[type].columns.tolist():
            #if the column is in the data
            if column in node_df.columns.tolist():
                #pass
                pass
            #otherwise
            else:
                #add a blank column for that property
                node_df[column]=""

        #for columns in the data
        for column in node_df.columns.tolist():
            #if the column is in the model
            if column in model_dfs[type].columns.tolist():
                #pass
                pass
            #otherwise
            else:
                #remove the extra column
                node_df=node_df.drop(column, axis=1)

        #Then reorder the columns 
        node_df=node_df[model_dfs[type].columns]

        #clean up
        node_df=node_df.fillna("")

        #And apply it back to the list of data frames
        dfl_dfs[type]=node_df



##############
#
# Write out
#
##############

print("\nWriting out the CCDI Submission file.\n")

template_workbook = openpyxl.load_workbook(template_path)

#for each sheet df
for sheet_name, df in dfl_dfs.items():
    #select workbook tab
    ws=template_workbook[sheet_name]
    #remove any data that might be in the template
    ws.delete_rows(2, ws.max_row)

    #write the data
    for row in dataframe_to_rows(df, index=False, header=False):
        ws.append(row)

#save out template
template_workbook.save(f'{file_dir_path}/{output_file}.xlsx')

print(f"\n\nProcess Complete.\n\nThe output file can be found here: {file_dir_path}/{output_file}\n\n")
