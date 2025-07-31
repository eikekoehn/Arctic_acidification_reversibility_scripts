"""
author: Eike E. Köhn
date: July 30, 2025
description: Class for the calculation of hysteresis areas.
"""

import sys
# import hysteresis functions from the python package (available on github)
sys.path.insert(0,'/home/ekoehn/software/')
#import hysteresis # import the package
from hysteresis import hyst_areas as ha # import the submodule hyst_areas
from hysteresis import loop_metrics as lm # import the submodule loop_metrics


class HystFuncs:
    """
    description: Collection of a number of functions to handle hysteresis calculations.
    """

    def _calc_hysteresis_areas_3D_multimodel(rparams,ds_data,temporal_resolution,ds_atmCO2,normalizer='min_max_diff_full_cycle',nsteps=200, return_interpolated_vectors=False):
        """
        This function calculates hysteresis areas over all models.
        """
    
        # choose the number of years to be included in the calculation of the hysteresis
        num_years_to_analyze = 280
    
        # initialize a dictionary to store the hysteresis areas
        ha_dict = dict()
        
        # Loop over the models and calculate the hysteresis areas
        for key in rparams.keys():
            print(f'Calculating hysteresis area for model {rparams[key].model} (key {key})....')
            # choose the variable data for the respective model
            if temporal_resolution == 'annual_means':
                data_dum = ds_data[key].annual_means
            elif temporal_resolution == 'son_means':
                data_dum = ds_data[key].seasonal_means.isel(season='SON')
            # Select only the first num_years_to_analyze (to discard final stabilization period)
            data     = data_dum.isel(year=slice(None,num_years_to_analyze))
            # get the atmospheric CO2 mixing ratio as reference axis
            ref_axis = ds_atmCO2[key].isel(year=slice(None,num_years_to_analyze)) 
    
            # Perform the calculation and put the result into the dictionary
            ha_dict[key] = ha.calc_hysteresis_area_3D(ref_axis, 
                                                      data, 
                                                      nsteps=nsteps,
                                                      normalizer=normalizer,
                                                      return_interpolated_vectors=return_interpolated_vectors)
        return ha_dict
