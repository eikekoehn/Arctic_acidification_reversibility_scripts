"""
author: Eike E. Köhn
date: July 30, 2025
description: Contains a class with functions handy for multimodel analysis.
"""

import xarray as xr
from get_misc_data import MiscDataGetter

class MMFuncs:

    def _calc_model_agreement(data_da,agreement_type='sign',agreement_thresh='at_least_80percent_agree'):
        
        nkeys = len(data_da.run_keys)

        if agreement_type == 'mean_bigger_than_std':
            mmstd = data_da.std(dim='run_keys')
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
            positives = (data_da>0).sum(dim='run_keys')
            negatives = (data_da<0).sum(dim='run_keys')
            # check if either the positives or the negatives exceed the threshold
            agreement = (positives >= athresh) + (negatives >= athresh)
        else:
            agreement = None
        return agreement
        
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

            if 'depth' in da.coords:
                da = da.reset_coords('depth', drop=True)
                
            # Put da into list
            data_list.append(da)

        # Concatenate the list into a new xr.DataArray
        data_da = xr.concat(data_list,dim='run_keys')

        # Compute the mean over concatenated dimension
        mmm = data_da.mean(dim='run_keys')

        # Now compute the model agreement
        agreement = MMFuncs._calc_model_agreement(data_da,agreement_type='sign',agreement_thresh='at_least_80percent_agree')
                        
        return mmm, agreement
    
    def _calc_spatial_average(data,region):#,data,omask,areaweights):
        region_mask = MiscDataGetter._get_region_mask(region)
        da_omask    = MiscDataGetter._get_ocean_mask()
        da_area     = MiscDataGetter._get_grid_cell_areas()
        romask = da_omask * region_mask * 1.
        roweights = da_area*romask
        #print(roweights)
        #print(data)
        spatial_mean = data.weighted(roweights).mean(["lat", "lon"])
        return spatial_mean

    def _calc_regional_means(run_params,set_of_loc_reg,run_paths,name_of_dataarray):

        if name_of_dataarray == 'son_means':
            name_of_dataarray_adjusted = 'seasonal_means'
            chosen_season = 'SON'
            
        regional_data = dict()
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
            regional_data[loc_or_reg_string] = xr.Dataset()

            # if the run keys are a dimension in an xarray dataarray
            if isinstance(run_paths,xr.DataArray):
                #print(run_paths)
                data_choice = run_paths#.squeeze()#.fillna(0)
                #print(data_choice)
                if isinstance(loc_or_reg,str):
                    regional_data[loc_or_reg_string] = MMFuncs._calc_spatial_average(data_choice,loc_or_reg)
                elif isinstance(loc_or_reg,list):
                    regional_data[loc_or_reg_string] = data_choice.isel(lat=loc_or_reg[0],lon=loc_or_reg[1])
                else:
                    raise Exception('Not yet implemented')                                
            else:
                # Loop over runs
                for key in run_params.keys():
                    # choose the data
                    # if paths were provided instead of already opened xarrays
                    if isinstance(run_paths[key],str):
                        with xr.open_dataset(run_paths[key]) as ds:
                            if name_of_dataarray in ['son_means','djf_means','mam_means','jja_means']:
                                data_choice = ds[name_of_dataarray_adjusted].sel(season=chosen_season)
                            else:
                                data_choice = ds[name_of_dataarray]
                            # Compute the spatial average time series or extract the point location time series
                            if isinstance(loc_or_reg,str):
                                regional_data[loc_or_reg_string][key] = MMFuncs._calc_spatial_average(data_choice,loc_or_reg)
                            elif isinstance(loc_or_reg,list):
                                regional_data[loc_or_reg_string][key] = data_choice.isel(lat=loc_or_reg[0],lon=loc_or_reg[1])
                            else:
                                raise Exception('Not yet implemented')
                    # if already opened xarray datasets were provided in a dictionary
                    elif isinstance(run_paths[key],xr.Dataset):
                        if name_of_dataarray in ['son_means','djf_means','mam_means','jja_means']:
                            data_choice = run_paths[key][name_of_dataarray_adjusted].sel(season=chosen_season)
                        else:
                            data_choice = run_paths[key][name_of_dataarray]
                        # Compute the spatial average time series or extract the point location time series
                        if isinstance(loc_or_reg,str):
                            regional_data[loc_or_reg_string][key] = MMFuncs._calc_spatial_average(data_choice,loc_or_reg)
                        elif isinstance(loc_or_reg,list):
                            regional_data[loc_or_reg_string][key] = data_choice.isel(lat=loc_or_reg[0],lon=loc_or_reg[1])
                        else:
                            raise Exception('Not yet implemented')
                    # if already opened xarray dataarrays were provided in a dictionary
                    elif isinstance(run_paths[key],xr.DataArray):
                        data_choice = run_paths[key]
                        # Compute the spatial average time series or extract the point location time series
                        if isinstance(loc_or_reg,str):
                            regional_data[loc_or_reg_string][key] = MMFuncs._calc_spatial_average(data_choice,loc_or_reg)
                        elif isinstance(loc_or_reg,list):
                            regional_data[loc_or_reg_string][key] = data_choice.isel(lat=loc_or_reg[0],lon=loc_or_reg[1])
                        else:
                            raise Exception('Not yet implemented')                
        return regional_data
    
    
    def _calc_time_slice_averages(ds_paths,pic_paths,temporal_resolution,time_slices='standard',time_slice_type='anom_to_preindustrial_initial'): # time_slice_type = 'absolute values', 'anom_to_preindustrial_concurrent'

        if temporal_resolution == 'son_means':
            temporal_resolution_adjusted = 'seasonal_means'
            chosen_season = 'SON'
            
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
        elif time_slices == 'hysteresis_areas':
            time_slices = dict()
            time_slices['0_signed_hysteresis_area'] = None
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
                data_dict_to_treat = pic_paths
            elif ts_key == '0_signed_hysteresis_area':
                data_dict_to_treat = pic_paths
            else:
                data_dict_to_treat = ds_paths

            if ts_key != '0_signed_hysteresis_area':
                # loop over all runs for each time slice
                time_slice_dict = dict()
                for key in data_dict_to_treat.keys():
                    # if paths were provided instead of already opened xarrays
                    if isinstance(data_dict_to_treat[key],str):
                        with xr.open_dataset(data_dict_to_treat[key]) as ds:
                            if temporal_resolution in ['son_means','djf_means','mam_means','jja_means']:
                                time_slice_dum =  ds[temporal_resolution_adjusted].sel(season=chosen_season).isel(year=time_slices[ts_key]).mean(dim='year')
                            else:
                                time_slice_dum =  ds[temporal_resolution].isel(year=time_slices[ts_key]).mean(dim='year')
                            if time_slice_type == 'absolute_value' or ts_key == '0_preindustrial':
                                time_slice_dum = time_slice_dum # Don't do anything
                            elif time_slice_type == 'anom_to_preindustrial_initial':
                                pic_slice_key = '0_preindustrial' # always choose the initial time slice
                                with xr.open_dataset(pic_paths[key]) as ds_pic:
                                    if temporal_resolution in ['son_means','djf_means','mam_means','jja_means']:
                                        time_slice_pic = ds_pic[temporal_resolution_adjusted].sel(season=chosen_season).isel(year=time_slices[pic_slice_key]).mean(dim='year')
                                    else:
                                        time_slice_pic = ds_pic[temporal_resolution].isel(year=time_slices[pic_slice_key]).mean(dim='year')
                                    time_slice_dum = time_slice_dum - time_slice_pic
                            elif time_slice_type == 'anom_to_preindustrial_concurrent':
                                pic_slice_key = ts_key # always choose the concurrent time slice
                                with xr.open_dataset(pic_paths[key]) as ds_pic:
                                    if temporal_resolution in ['son_means','djf_means','mam_means','jja_means']:
                                        time_slice_pic = ds_pic[temporal_resolution_adjusted].sel(season=chosen_season).isel(year=time_slices[pic_slice_key]).mean(dim='year')
                                    else:
                                        time_slice_pic = ds_pic[temporal_resolution].isel(year=time_slices[pic_slice_key]).mean(dim='year')
                                    time_slice_dum = time_slice_dum - time_slice_pic  
                                    
                    # if already opened xarray datasets were provided in a dictionary
                    elif isinstance(data_dict_to_treat[key],xr.Dataset):
                        ds = data_dict_to_treat[key]
                        if temporal_resolution in ['son_means','djf_means','mam_means','jja_means']:
                            time_slice_dum =  ds[temporal_resolution_adjusted].sel(season=chosen_season).isel(year=time_slices[ts_key]).mean(dim='year')
                        else:
                            time_slice_dum =  ds[temporal_resolution].isel(year=time_slices[ts_key]).mean(dim='year')
                        if time_slice_type == 'absolute_value' or ts_key == '0_preindustrial':
                            time_slice_dum = time_slice_dum # Don't do anything
                        elif time_slice_type == 'anom_to_preindustrial_initial':
                            pic_slice_key = '0_preindustrial' # always choose the initial time slice
                            ds_pic = pic_paths[key]
                            if temporal_resolution in ['son_means','djf_means','mam_means','jja_means']:
                                time_slice_pic = ds_pic[temporal_resolution_adjusted].sel(season=chosen_season).isel(year=time_slices[pic_slice_key]).mean(dim='year')
                            else:
                                time_slice_pic = ds_pic[temporal_resolution].isel(year=time_slices[pic_slice_key]).mean(dim='year')
                            time_slice_dum = time_slice_dum - time_slice_pic
                        elif time_slice_type == 'anom_to_preindustrial_concurrent':
                            pic_slice_key = ts_key # always choose the concurrent time slice
                            ds_pic = pic_paths[key]
                            if temporal_resolution in ['son_means','djf_means','mam_means','jja_means']:
                                time_slice_pic = ds_pic[temporal_resolution_adjusted].sel(season=chosen_season).isel(year=time_slices[pic_slice_key]).mean(dim='year')
                            else:
                                time_slice_pic = ds_pic[temporal_resolution].isel(year=time_slices[pic_slice_key]).mean(dim='year')
                            time_slice_dum = time_slice_dum - time_slice_pic 
                    # if already opened xarray dataarrays were provided in a dictionary
                    elif isinstance(data_dict_to_treat[key],xr.DataArray):
                        da = data_dict_to_treat[key]
                        time_slice_dum =  da.isel(year=time_slices[ts_key]).mean(dim='year')
                        if time_slice_type == 'absolute_value' or ts_key == '0_preindustrial':
                            time_slice_dum = time_slice_dum # Don't do anything
                        elif time_slice_type == 'anom_to_preindustrial_initial':
                            pic_slice_key = '0_preindustrial' # always choose the initial time slice
                            da_pic = pic_paths[key]
                            time_slice_pic = da_pic.isel(year=time_slices[pic_slice_key]).mean(dim='year')
                            time_slice_dum = time_slice_dum - time_slice_pic
                        elif time_slice_type == 'anom_to_preindustrial_concurrent':
                            pic_slice_key = ts_key # always choose the concurrent time slice
                            da_pic = pic_paths[key]
                            time_slice_pic = da_pic.isel(year=time_slices[pic_slice_key]).mean(dim='year')
                            time_slice_dum = time_slice_dum - time_slice_pic 

                    time_slice_dict[key] = time_slice_dum.load()
        
                # compute the multimodel mean and agreement for this time slice
                time_slice_mmm, time_slice_agreement = MMFuncs._calc_multimodel_mean_and_agreement(time_slice_dict)
            
            else:
                time_slice_mmm = data_dict_to_treat.mean(dim='run_keys')
                time_slice_agreement = MMFuncs._calc_model_agreement(data_dict_to_treat,agreement_type='sign',agreement_thresh='at_least_80percent_agree')

            # Mask out marginal seas and put into dictionaries
            da_omask  = MiscDataGetter._get_ocean_mask()
            time_slice_averages_mmm[ts_key] = time_slice_mmm.compute() * da_omask
            time_slice_averages_agreement[ts_key] = time_slice_agreement.compute() * da_omask
    
        return time_slice_averages_mmm, time_slice_averages_agreement


