"""
author: Eike E. Köhn
date: July 30, 2025
description: A class to get model data.
"""

import os
import glob
import xarray as xr

class ModelDataGetter:

    @staticmethod
    def _get_variable_string(variable_to_analyze,depth_to_analyze):
        """
        This function converts the variable to analyze into a string that is used in constructing the data path.
        """
        if depth_to_analyze == 'surface' or depth_to_analyze == 1 or depth_to_analyze == '1':
            variable_string = variable_to_analyze+'1'
        elif depth_to_analyze == 'vertical_integral':
            variable_string = 'int'+variable_to_analyze
        elif depth_to_analyze == None:
            variable_string = variable_to_analyze
        else:
            raise Exception('Not yet implemented for other depths.')
        return variable_string

    @staticmethod
    def _get_domain_string(variable_to_analyze):
        """
        This function gets the domain of the respective variable.
        """
        if variable_to_analyze in ['ps','psl']:
            domain_string = 'A'
        elif variable_to_analyze in ['siconc']:
            domain_string = 'SI'
        else:
            domain_string = 'O'
        return domain_string

    @staticmethod
    def _get_temporal_resolution_string(temporal_resolution):
        """
        This function gets the temporal resolution of the respective variable.
        """
        if temporal_resolution in ['monthly']:
            temporal_res_string = 'mon'
        elif temporal_resolution in ['annual']:
            temporal_res_string = 'yr'
        else:
            raise Exception('Not yet implemented for other temporal resolutions.')
        return temporal_res_string

    @staticmethod
    def _get_list_of_mocsy_variables():
        """
        Set a list of variables that i use from the mocsy output.
        """
        list_of_mocsy_core_variables = ['ph','omegaa','pco2','co3','denis']
        list_of_mocsy_sensitivities  = ['dh_dalk',     'dh_ddic',     'dh_dtem',     'dh_dsal',
                                        'domegaa_dalk','domegaa_ddic','domegaa_dtem','domegaa_dsal',
                                        'dpco2_dalk',  'dpco2_ddic',  'dpco2_dtem',  'dpco2_dsal',
                                        'dco3_dalk',   'dco3_ddic',   'dco3_dtem',   'dco3_dsal']
        return list_of_mocsy_core_variables, list_of_mocsy_sensitivities

    @staticmethod
    def _identify_path_strings(run_params,variable_to_analyze,depth_to_analyze,verbose=False):#,temporal_resolution):
        """
        This function identifies the path for the different datasets.
        """        

        base_path = '/data/ekoehn/projects/pco2_seasonality/Data'

        variable_string = ModelDataGetter._get_variable_string(variable_to_analyze,depth_to_analyze)
        mocsy_core_vars, mocsy_sensitivity_vars = ModelDataGetter._get_list_of_mocsy_variables()

        # now construct the path strings
        path_strings = dict()
        for key in run_params.keys():
            model = run_params[key].model
            experiment = run_params[key].experiment
            if experiment == '1pctCO2-cdr':
                experiment_folder = f'processed_{experiment.lower()}_data'
            else:
                experiment_folder = f'processed_{experiment}_data'
            
                
            # construct the path_string depending on whether the variable is a direct model output or output from MOCSY calculations
            if variable_to_analyze in mocsy_core_vars:
                path_string = f'{base_path}/{experiment_folder}/mocsy_output/{variable_string}/{variable_string}_{model}_processed.nc'
            elif variable_to_analyze in mocsy_sensitivity_vars:
                path_string = f'{base_path}/{experiment_folder}/mocsy_sensitivities/{variable_string}/{variable_string}_{model}_processed.nc' 
            else:
                path_string = f'{base_path}/{experiment_folder}/{variable_string}/{variable_string}_{model}_processed.nc'

            # make sure the path string exists
            #path_string_found = glob.glob(path_string) # glob returns a list of paths
            #if len(path_string_found) != 1: # one path contained
            #    raise Exception('Less or more than 1 data path found per model.')
            #else:
            #    identified_path = path_string_found[0]
            #    if len(identified_path)==0:
            #        raise Exception('Identified string is empty, indicating that no model was found.')
            #    # add path string to dictionary of path_strings
            #    path_strings[key] = identified_path

            path_string_found = glob.glob(path_string) # glob returns a list of paths
            if len(path_string_found) > 1: # one path contained
                raise Exception('More than 1 data path found per model.')
            else:
                if len(path_string_found) == 1:
                    identified_path = path_string_found[0]
                    path_strings[key] = identified_path
                elif len(path_string_found)==0:
                    if verbose == True:
                        print(f'WARNING: Identified string is empty, indicating that no model was found for model {run_params[key].model} and variable {variable_string}.')
                    path_strings[key] = ''
                # add path string to dictionary of path_strings
                
        return path_strings

    @staticmethod
    def _open_datasets(run_paths):
        """
        This function serves to open the datasets listed in the run_paths.
        """
        open_ds = dict()
        for key in run_paths.keys():
            open_ds[key] = xr.open_dataset(run_paths[key])
        return open_ds

    @staticmethod
    def _close_datasets(ds_dict):
        """
        This function serves to open the datasets listed in the run_paths.
        """
        for key in ds_dict.keys():
            ds_dict[key].close()

    @staticmethod
    def _get_dataset(path):
        with xr.open_dataset(path) as ds:
            return ds.load()
        
    #(self,variable_to_analyze,depth_to_analyze):
    #domain_string = self._get_domain_string(variable_to_analyze)
    #temporal_res_string = self._get_temporal_resolution_string(temporal_resolution)
    #member = run_params[key].member
    #grid_name = 'gr'
