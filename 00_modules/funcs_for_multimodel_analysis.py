"""
author: Eike E. Köhn
date: July 30, 2025
description: Contains a class with functions handy for multimodel analysis.
"""

import xarray as xr
from get_misc_data import MiscDataGetter

class MMFuncs:

    def _calc_multimodel_mean_and_agreement(data_dict, da_name=None, agreement_type = 'sign', agreement_thresh='at_least_80percent_agree'):

        # Get all the different runs and put them into a list
        data_list = []
        for key in data_dict.keys():

            # Get the respective da from the data_dict
            if isinstance(data_dict[key], xr.Dataset) and da_name != None:
                da = data_dict[key][da_name]
            elif isinstance(data_dict[key], xr.DataArray):
                da = data_dict[key]
            else:
                raise Exception('Not yet implemented for anything else.')

            # Put da into list
            data_list.append(da)

        # Concatenate the list into a new xr.DataArray
        data_da = xr.concat(data_list,dim='keys')

        # Compute the mean over concatenated dimension
        mmm = data_da.mean(dim='keys')

        nkeys = len(data_da.keys)
        # Now compute the model agreement
        if agreement_type == 'mean_bigger_than_std':
            mmstd = data_da.std(dim='keys')
            agreement = mmm>mmstd
        elif agreement_type == 'sign':
            if agreement_thresh=='at_least_70percent_agree':
                athresh = .7*nkeys # 6/8
            elif agreement_thresh=='at_least_80percent_agree':
                athresh = .8*nkeys # 7/8
            elif agreement_thresh=='at_least_100percent_agree':
                athresh = 1*nkeys # 8/8
            else:
                raise Exception("Other agreement threshold for agreement_type == 'sign' is not yet implemented.")
            # count the positives and negatives
            positives = (data_da>0).sum(dim='keys')
            negatives = (data_da<0).sum(dim='keys')
            # check if either the positives or the negatives exceed the threshold
            agreement = (positives >= athresh) + (negatives >= athresh)
        else:
            agreement = None
                        
        return mmm, agreement
    
    def _calc_spatial_average(data,region):#,data,omask,areaweights):
        region_mask = MiscDataGetter._get_region_mask(region)
        da_omask    = MiscDataGetter._get_ocean_mask()
        da_area     = MiscDataGetter._get_grid_cell_areas()
        romask = da_omask * region_mask * 1.
        roweights = da_area*romask
        spatial_mean = data.weighted(roweights).mean(["lat", "lon"])
        return spatial_mean

    def _calc_regional_means(run_params,set_of_loc_reg,ds_data,name_of_dataarray):
    
        regional_time_series = dict()
        # Loop over regions
        for loc_or_reg in set_of_loc_reg:

            # get the right string
            if isinstance(loc_or_reg,str):
                loc_or_reg_string = loc_or_reg
            elif isinstance(loc_or_reg,list):
                loc_or_reg_string = f'point_{loc_or_reg[0]}_{loc_or_reg[1]}'
            else:
                raise Exception('Not yet implemented')
                
            # initiate a dataset for this region
            regional_time_series[loc_or_reg_string] = xr.Dataset()
            
            # Loop over runs
            for key in run_params.keys():
                # choose the data
                data_choice = ds_data[key][name_of_dataarray]
                # Compute the spatial average time series or extract the point location time series
                if isinstance(loc_or_reg,str):
                    regional_time_series[loc_or_reg_string][key] = MMFuncs._calc_spatial_average(data_choice,loc_or_reg)
                elif isinstance(loc_or_reg,list):
                    regional_time_series[loc_or_reg_string][key] = data_choice.isel(lat=loc_or_reg[0],lon=loc_or_reg[1])
                else:
                    raise Exception('Not yet implemented')
                
        return regional_time_series
    
    
    def _calc_time_slice_averages(ds_data,pic_data,temporal_resolution,time_slices='standard',time_slice_type='anom_to_preindustrial_initial'): # time_slice_type = 'absolute values', 'anom_to_preindustrial_concurrent'
    
        #initialize a dictionary containing the multimodel mean time slice averages and a dictionary containing the agreement
        time_slice_averages_mmm       = dict()
        time_slice_averages_agreement = dict()
    
        # Define the time slices of interest
        if time_slices == 'standard':
            time_slices = dict()
            time_slices['0_preindustrial'] = slice(None,20)
            time_slices['1_rampup_start']  = slice(None,20)
            time_slices['2_rampup_mid']    = slice(60,80)
            time_slices['3_rampup_end']    = slice(120,140)
            time_slices['4_rampdown_mid']  = slice(200,220)
            time_slices['5_rampdown_end']  = slice(260,280)
            time_slices['6_stabilization'] = slice(320,340)
        else:
            raise Exception('Not yet implemented for other time slices.')
    
        # get a list of time slice keys
        sorted_time_slice_keys = sorted(time_slices.keys()) # making use of the 0,1,2,3,4... numbering to sort the keys chronologically
    
        # loop over time slices
        for ts_key in sorted_time_slice_keys:
            if ts_key == '0_preindustrial':
                data_dict_to_treat = pic_data
            else:
                data_dict_to_treat = ds_data
                
            # loop over all runs for each time slice
            time_slice_dict = dict()
            for key in data_dict_to_treat.keys():
                time_slice_dum =  data_dict_to_treat[key][temporal_resolution].isel(year=time_slices[ts_key]).mean(dim='year')
                if time_slice_type == 'absolute_value' or ts_key == '0_preindustrial':
                    time_slice_dum = time_slice_dum # Don't do anything
                elif time_slice_type == 'anom_to_preindustrial_initial':
                    pic_slice_key = '0_preindustrial' # always choose the initial time slice
                    time_slice_pic = pic_data[key][temporal_resolution].isel(year=time_slices[pic_slice_key]).mean(dim='year')
                    time_slice_dum = time_slice_dum - time_slice_pic
                elif time_slice_type == 'anom_to_preindustrial_concurrent':
                    pic_slice_key = ts_key # always choose the concurrent time slice
                    time_slice_pic = pic_data[key][temporal_resolution].isel(year=time_slices[pic_slice_key]).mean(dim='year')
                    time_slice_dum = time_slice_dum - time_slice_pic            
    
                time_slice_dict[key] = time_slice_dum
    
            # compute the multimodel mean and agreement for this time slice
            time_slice_mmm, time_slice_agreement = MMFuncs._calc_multimodel_mean_and_agreement(time_slice_dict)
    
            # Mask out marginal seas and put into dictionaries
            da_omask  = MiscDataGetter._get_ocean_mask()
            time_slice_averages_mmm[ts_key] = time_slice_mmm.compute() * da_omask
            time_slice_averages_agreement[ts_key] = time_slice_agreement.compute() * da_omask
    
        return time_slice_averages_mmm, time_slice_averages_agreement




