from unittest import result
import pandas as pd
import numpy as np
from collections import defaultdict
from message_ix_models.util import broadcast, same_node
import message_ix

from message_ix.utils import make_df
import ixmp
import message_data
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


def gen_trade_data (file, sheet_main, scenario):

    #Read the data for given material - Hist referers to historical capacity
    data = pd.read_excel(file, sheet_main)
    
    #Removed the following two lines because now this file is used by global model.
    #More regions to work with
    #region = data['Region'].unique()
    
    data = data.drop(['Region'], axis = 1)
    results = defaultdict(list)
    
    technologies = data['technology'].unique()

## This is hardcoded for now, change it! ###TODO 
# 
    region = ['R12_GLB']
    #First year of calibration of the model. 
    
    
    for t in technologies:

        av = data.loc[(data["technology"] == t),
                                'availability'].values[0]
        years_df = scenario.vintage_and_active_years()
        years_df = years_df.loc[years_df["year_vtg"]>= av]
            # Empty data_frame 
        years_df_final = pd.DataFrame(columns=["year_vtg","year_act"])
        # For each vintage adjsut the active years according to technical 
        # lifetime
        
        for vtg in years_df["year_vtg"].unique():
            years_df_temp = years_df.loc[years_df["year_vtg"]== vtg]
            years_df_temp = years_df_temp.loc[years_df["year_act"]
                                                < vtg + av]
            years_df_final = pd.concat([years_df_temp, years_df_final],
                                        ignore_index=True)
        vintage_years, act_years = years_df_final['year_vtg'].unique(), \
        years_df_final['year_act'].unique()
    

        params = data.loc[(data["technology"] == t),\
                                    "parameter"].values.tolist()
        # Iterate over parameters 
        for par in params:
            split = par.split("|")
            param_name = par.split("|")[0]
            
            val = data.loc[((data["technology"] == t) & 
                                        (data["parameter"] == par)),\
                                'value'].values[0]

            # Common parameters for all input and output tables 
            # node_dest and node_origin are the same as node_loc
            
            common = dict(
            year_vtg= vintage_years,
            year_act= vintage_years,
            mode="M1",
            time="year",
            time_origin="year",
            time_dest="year",)     
            
            if len(split)> 1: 

                if (param_name == "input")|(param_name == "output"):
                
                    com = split[1]
                    lev = split[2]
                    
                    #print(param_name)
                    #print(t)
                    #print(com)
                    #print(val)
                    #print(common)
                    #print(len(common))
                    df = (make_df(param_name, technology=t, commodity=com, 
                                    level=lev, value=val, unit='Mt', **common)
                    .pipe(broadcast, node_loc=region).pipe(same_node))
                    #print(results[param_name])
                    #results[param_name] = pd.concat([results[param_name], df])
                    
                    results[param_name].append(df)
                    
            #else:  
            #    df = (make_df(param_name, technology=t, value=val, node_loc = region, unit='t', 
            #                    **common).pipe(broadcast, node_loc=region))
                #results[param_name] = pd.concat([results[param_name], df])  
            #    results[param_name].append(df)
    results = {par_name: pd.concat(dfs) for par_name, dfs in results.items()}

    scenario.check_out()
    for k, v in results.items():
        scenario.add_par(k,v)


    return results, scenario

