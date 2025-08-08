"""
author: Eike E. Köhn
date: Nov 20, 2024
description: Functions to get the model data.
"""

import datetime
import dask
import xarray as xr
import numpy as np
import cftime
from copy import deepcopy
import pandas as pd
import xrmasking_functions_new as MaskGetter
import glob
import re


def get_paths(rparam):
    if rparam.protocol_gen == 'tipesm':
        paths = getTipESMmodfiles(rparam)
    elif rparam.protocol_gen == 'cmip6':
        paths = getCMIP6modfiles(rparam)
    elif rparam.protocol_gen == 'cmip5':
        paths = getCMIP5modfiles(rparam)

    if hasattr(rparam, 'prepend_hist'):
        if rparam.prepend_hist == True:
            rparam_hist = deepcopy(rparam)
            if rparam.experiment == '1pctCO2-cdr':
                rparam_hist.experiment = '1pctCO2'
            else:
                rparam_hist.experiment = 'historical'
            if rparam.protocol_gen == 'cmip6':
                hist_paths = getCMIP6modfiles(rparam_hist)
            elif rparam.protocol_gen == 'cmip5':
                hist_paths = getCMIP5modfiles(rparam_hist)
            paths_all = [*hist_paths,*paths]
        else:
            paths_all = paths
    else:
        paths_all = paths

    rparam.filenames = paths_all

    return rparam

def preprocess_rename_time(ds):
    # Check if 'time_counter' exists and rename it to 'time'
    if 'time_counter' in ds.dims:
        ds = ds.rename({'time_counter': 'time'})
    elif 'time_counter' in ds.coords:
        ds = ds.rename({'time_counter': 'time'})
    
    return ds
    

def preprocess_remove_overlap(ds, start, end):
    """
    Remove a specified overlapping time period from the dataset.
    """
    if 'time' in ds.coords:
        ds = ds.sel(time=~((ds['time'] >= start) & (ds['time'] < end)))
    return ds

# Function to convert a mixed array to cftime.DatetimeGregorian
def convert_to_cftime(mixed_array, calendar="gregorian"):
    cftime_array = []
    for item in mixed_array:
        if isinstance(item, pd.Timestamp):
            # Convert Timestamp to cftime.DatetimeGregorian
            cftime_obj = cftime.DatetimeGregorian(item.year, item.month, item.day,
                                                   item.hour, item.minute, item.second, item.microsecond, has_year_zero=False)
            cftime_array.append(cftime_obj)
        elif isinstance(item,np.datetime64):
            datedum = item.astype('M8[s]').astype(datetime.datetime)
            gregorian_date = cftime.DatetimeGregorian(datedum.year, datedum.month, datedum.day)
            cftime_array.append(gregorian_date)
        elif isinstance(item,cftime.Datetime360Day) or isinstance(item,cftime.DatetimeNoLeap):
            date_360 = datetime.datetime(item.year, item.month, item.day)
            gregorian_date = cftime.DatetimeGregorian(date_360.year, date_360.month, date_360.day)
            cftime_array.append(gregorian_date)
        elif isinstance(item, cftime.DatetimeProlepticGregorian):
            date_prol = datetime.datetime(item.year, item.month, item.day)
            gregorian_date = cftime.DatetimeGregorian(date_prol.year, date_prol.month, date_prol.day)
            cftime_array.append(gregorian_date)
        elif isinstance(item, cftime.DatetimeGregorian):
            cftime_array.append(item) # Keep cftime.DatetimeGregorian as is
        else:
            raise TypeError(f"Unsupported type found: {type(item)}")
    return np.array(cftime_array)
    
def open_ds(rparam):
    print(rparam.filenames)
    
    if len(rparam.filenames)==1:
        
        ds = xr.open_dataset(rparam.filenames[0],use_cftime=True,decode_times=False)
        if 'time_counter' in ds.dims:
            ds = ds.rename({'time_counter':'time'})
        ds['time'] = cftime.num2date(ds['time'].values, units=ds['time'].units, calendar=ds['time'].calendar)
        ds = ds.chunk({'time': 12})  # Chunk in steps of 12
        
    elif len(rparam.filenames)==2:

        # STEP 1: Identify time range for each file
        
        fyears = dict()
        # get the years for each filename and adjust them in case of overlaps
        for rdx,rfilen in enumerate(rparam.filenames):
            fyears[rdx] = dict()
            fyears[rdx]['subslice'] = False
            match = re.search(r"_(\d{4})\d{2}-(\d{4})\d{2}\.nc", rfilen)
            if match:
                fyears[rdx]['start_year'] = int(match.group(1))  # First 4-digit year (start)
                fyears[rdx]['end_year'] = int(match.group(2))    # Second 4-digit year (end)
                print(f"Start Year: {fyears[rdx]['start_year']}, End Year: {fyears[rdx]['end_year']}")
            else:
                print("No matching years found in the filename.")
            match = 0

        print("Overview over years in files:")
        for key in fyears.keys():
            print(f"File {key} === Start Year: {fyears[key]['start_year']}, End Year: {fyears[key]['end_year']}")            
        
        # STEP 2: Check if all files are consecutive (i.e. without overlap), or if they start with the same years
        consecutive_files = []
        for rdx,rfilen in enumerate(rparam.filenames):
            if rdx > 0:
                if fyears[rdx]['start_year'] - fyears[int(rdx-1)]['end_year'] > 0:
                    consecutive_files.append(True)
                else:
                    consecutive_files.append(False)

        print(consecutive_files)
        print(np.all(consecutive_files))
        
        same_starting_year = []
        for rdx,rfilen in enumerate(rparam.filenames):
            if rdx > 0:
                if fyears[rdx]['start_year'] == fyears[int(rdx-1)]['start_year']:
                    same_starting_year.append(True)   
                else:
                    same_starting_year.append(False)   

        print(same_starting_year)
        print(np.all(same_starting_year))
        
        #####################################################################################################
        # STEP 3.a: If they are, try opening it just like this.
        if np.all(consecutive_files) == True:
            print('I have consecutive files.')
            try:
                print('use first option')
                ds = xr.open_mfdataset(rparam.filenames,preprocess=preprocess_rename_time,chunks={'time': 12, 'lat':-1, 'lon':-1})
            except:
                raise Exception('Something went wrong.')

        #####################################################################################################
        # STEP 3.b: If the files have the same starting point, we have to append the second to the first year
        elif np.all(same_starting_year) == True:
            print('I have files with the same starting years.')
            print('I do something.')
            
            # open files
            all_files = []
            for rdx,rfilen in enumerate(rparam.filenames):
                if rdx == 0 and fyears[rdx]['start_year']==1 and fyears[rdx]['end_year'] > 140:
                    print('take only 140 first years of first file')
                    ds_dum = xr.open_dataset(rfilen)
                    timeslice_start = f"{fyears[rdx]['start_year']:04d}-01-01"
                    timeslice_end = f"0140-12-17"
                    filedum = ds_dum.sel(time=slice(timeslice_start,timeslice_end))
                    fyears[rdx]['end_year'] = 140
                elif fyears[rdx]['subslice'] == False and rdx != len(rparam.filenames)-1:
                    print('take whole file')
                    filedum = xr.open_dataset(rfilen)
                else:
                    print('choose only subslice')
                    #timeslice_start = f"{fyears[rdx]['start_year']:04d}-01-01"
                    #timeslice_end   = f"{fyears[rdx]['end_year']:04d}-12-17"
                    ds_dum = xr.open_dataset(rfilen) #.sel(time=slice(timeslice_start,timeslice_end))

                    # adjust time in filedum
                    timeslice_start = f"{fyears[rdx]['start_year']:04d}-01-01"

                    if fyears[rdx]['end_year'] < (fyears[0]['start_year']+350) :
                        timeslice_end   = f"{fyears[rdx]['end_year']:04d}-12-17"
                    else:
                        timeslice_end   = f"{(fyears[0]['start_year']+350):04d}-12-17"
                            
                    if rdx > 0:
                        years_to_add = 0
                        for cdx in range(0,rdx):
                            years_to_add += fyears[cdx]['end_year']
                        print('Years to add:')
                        print(years_to_add)

                    print(timeslice_start)
                    print(timeslice_end)
                    
                    filedum = ds_dum.sel(time=slice(timeslice_start,timeslice_end))

                    filedum['time'] = [t.replace(year=t.year + years_to_add) for t in filedum.time.data]

                all_files.append(filedum)            
            
            print(all_files)
            # Concatenate the preprocessed datasets
            combined = xr.concat(all_files, dim='time')
            ds = combined.chunk({'time':12,'lat':-1,'lon':-1})

        #####################################################################################################################################
        # STEP 3.c: Since they are not consecutive, and they do not have the same starting year, i.e. there is some overlap, do the following
        else:
            print('There seems to be an overlap.')
            for rdx,rfilen in enumerate(rparam.filenames):
                if rdx > 0:
                    if fyears[rdx]['start_year'] < fyears[int(rdx-1)]['end_year']: # if there is an overlap
                        fyears[int(rdx-1)]['end_year'] = fyears[rdx]['start_year']-1 # end the first part at the start of the second 
                        fyears[int(rdx-1)]['subslice'] = True
                    
                if fyears[len(rparam.filenames)-1]['end_year'] > fyears[0]['start_year']+350:
                    fyears[len(rparam.filenames)-1]['end_year'] = fyears[0]['start_year']+350
    
            print("Overview over years in files:")
            for key,kdx in enumerate(fyears.keys()):
                print(f"File {rparam.filenames[kdx]} === Start Year: {fyears[kdx]['start_year']}, End Year: {fyears[kdx]['end_year']}")
            
            # open files
            all_files = []
            for rdx,rfilen in enumerate(rparam.filenames):
                if fyears[rdx]['subslice'] == False and rdx != len(rparam.filenames)-1:
                    print('take whole file')
                    filedum = xr.open_dataset(rfilen)
                else:
                    print('choose only subslice')
                    timeslice_start = f"{fyears[rdx]['start_year']:04d}-01-01"
                    timeslice_end   = f"{fyears[rdx]['end_year']:04d}-12-17"
                    print('Selecting:')
                    print(timeslice_start)
                    print(timeslice_end)
                    filedum = xr.open_dataset(rfilen).sel(time=slice(timeslice_start,timeslice_end))
                all_files.append(filedum)
        
            # Concatenate the preprocessed datasets
            combined = xr.concat(all_files, dim='time')
            ds = combined.chunk({'time':12,'lat':-1,'lon':-1})
            print(ds)
                    #ds = xr.open_mfdataset(rparam.filenames,use_cftime=True,preprocess=preprocess_rename_time,chunks={'time': -1})        
                
            # Merge datasets with preprocessing and deduplication
            #ds_merged = xr.open_mfdataset(rparam.filenames,combine="by_coords",parallel=True,chunks={'time': 12,'lat':-1,'lon':-1})
            ## Remove duplicates across all files (merged dataset)
            #_, index = np.unique(ds_merged['time'], return_index=True)
            #ds_deduplicated = ds_merged.isel(time=index)
    else:
        raise Exception('No or too many filenames found for this set of params.')

    ds['time'] = convert_to_cftime(ds.time.data, calendar="gregorian")

    if ds.time.data[0].year < 1850 or ds.time.data[0].year > 1861:
        years_to_add = 1850-ds.time.data[0].year
        ds['time'] = [t.replace(year=t.year + years_to_add) for t in ds.time.data]
        
    return ds    


def open_ds_yearly(rparam):
    print(rparam.filenames)
    
    if len(rparam.filenames)==1:
        
        ds = xr.open_dataset(rparam.filenames[0],use_cftime=True,decode_times=False)
        if 'time_counter' in ds.dims:
            ds = ds.rename({'time_counter':'time'})
        ds['time'] = cftime.num2date(ds['time'].values, units=ds['time'].units, calendar=ds['time'].calendar)
        ds = ds.chunk({'time': 12})  # Chunk in steps of 12
        
    elif len(rparam.filenames)==2:

        # STEP 1: Identify time range for each file
        
        fyears = dict()
        # get the years for each filename and adjust them in case of overlaps
        for rdx,rfilen in enumerate(rparam.filenames):
            fyears[rdx] = dict()
            fyears[rdx]['subslice'] = False
            match = re.search(r"_(\d{4})-(\d{4})\.nc", rfilen)
            if match:
                fyears[rdx]['start_year'] = int(match.group(1))  # First 4-digit year (start)
                fyears[rdx]['end_year'] = int(match.group(2))    # Second 4-digit year (end)
                print(f"Start Year: {fyears[rdx]['start_year']}, End Year: {fyears[rdx]['end_year']}")
            else:
                print("No matching years found in the filename.")
            match = 0

        print("Overview over years in files:")
        for key in fyears.keys():
            print(f"File {key} === Start Year: {fyears[key]['start_year']}, End Year: {fyears[key]['end_year']}")            
        
        # STEP 2: Check if all files are consecutive (i.e. without overlap), or if they start with the same years
        consecutive_files = []
        for rdx,rfilen in enumerate(rparam.filenames):
            if rdx > 0:
                if fyears[rdx]['start_year'] - fyears[int(rdx-1)]['end_year'] > 0:
                    consecutive_files.append(True)
                else:
                    consecutive_files.append(False)

        print(consecutive_files)
        print(np.all(consecutive_files))
        
        same_starting_year = []
        for rdx,rfilen in enumerate(rparam.filenames):
            if rdx > 0:
                if fyears[rdx]['start_year'] == fyears[int(rdx-1)]['start_year']:
                    same_starting_year.append(True)   
                else:
                    same_starting_year.append(False)   

        print(same_starting_year)
        print(np.all(same_starting_year))
        
        #####################################################################################################
        # STEP 3.a: If they are, try opening it just like this.
        if np.all(consecutive_files) == True:
            print('I have consecutive files.')
            try:
                print('use first option')
                ds = xr.open_mfdataset(rparam.filenames,preprocess=preprocess_rename_time,chunks={'time': 12, 'lat':-1, 'lon':-1})
            except:
                raise Exception('Something went wrong.')

        #####################################################################################################
        # STEP 3.b: If the files have the same starting point, we have to append the second to the first year
        elif np.all(same_starting_year) == True:
            print('I have files with the same starting years.')
            print('I do something.')
            
            # open files
            all_files = []
            for rdx,rfilen in enumerate(rparam.filenames):
                if rdx == 0 and fyears[rdx]['start_year']==1 and fyears[rdx]['end_year'] > 140:
                    print('take only 140 first years of first file')
                    ds_dum = xr.open_dataset(rfilen)
                    timeslice_start = f"{fyears[rdx]['start_year']:04d}-01-01"
                    timeslice_end = f"0140-12-17"
                    filedum = ds_dum.sel(time=slice(timeslice_start,timeslice_end))
                    fyears[rdx]['end_year'] = 140
                elif fyears[rdx]['subslice'] == False and rdx != len(rparam.filenames)-1:
                    print('take whole file')
                    filedum = xr.open_dataset(rfilen)
                else:
                    print('choose only subslice')
                    #timeslice_start = f"{fyears[rdx]['start_year']:04d}-01-01"
                    #timeslice_end   = f"{fyears[rdx]['end_year']:04d}-12-17"
                    ds_dum = xr.open_dataset(rfilen) #.sel(time=slice(timeslice_start,timeslice_end))

                    # adjust time in filedum
                    timeslice_start = f"{fyears[rdx]['start_year']:04d}-01-01"

                    if fyears[rdx]['end_year'] < (fyears[0]['start_year']+350) :
                        timeslice_end   = f"{fyears[rdx]['end_year']:04d}-12-17"
                    else:
                        timeslice_end   = f"{(fyears[0]['start_year']+350):04d}-12-17"
                            
                    if rdx > 0:
                        years_to_add = 0
                        for cdx in range(0,rdx):
                            years_to_add += fyears[cdx]['end_year']
                        print('Years to add:')
                        print(years_to_add)

                    print(timeslice_start)
                    print(timeslice_end)
                    
                    filedum = ds_dum.sel(time=slice(timeslice_start,timeslice_end))

                    filedum['time'] = [t.replace(year=t.year + years_to_add) for t in filedum.time.data]

                all_files.append(filedum)            
            
            print(all_files)
            # Concatenate the preprocessed datasets
            combined = xr.concat(all_files, dim='time')
            ds = combined.chunk({'time':12,'lat':-1,'lon':-1})

        #####################################################################################################################################
        # STEP 3.c: Since they are not consecutive, and they do not have the same starting year, i.e. there is some overlap, do the following
        else:
            print('There seems to be an overlap.')
            for rdx,rfilen in enumerate(rparam.filenames):
                if rdx > 0:
                    if fyears[rdx]['start_year'] < fyears[int(rdx-1)]['end_year']: # if there is an overlap
                        fyears[int(rdx-1)]['end_year'] = fyears[rdx]['start_year']-1 # end the first part at the start of the second 
                        fyears[int(rdx-1)]['subslice'] = True
                    
                if fyears[len(rparam.filenames)-1]['end_year'] > fyears[0]['start_year']+350:
                    fyears[len(rparam.filenames)-1]['end_year'] = fyears[0]['start_year']+350
    
            print("Overview over years in files:")
            for key,kdx in enumerate(fyears.keys()):
                print(f"File {rparam.filenames[kdx]} === Start Year: {fyears[kdx]['start_year']}, End Year: {fyears[kdx]['end_year']}")
            
            # open files
            all_files = []
            for rdx,rfilen in enumerate(rparam.filenames):
                if fyears[rdx]['subslice'] == False and rdx != len(rparam.filenames)-1:
                    print('take whole file')
                    filedum = xr.open_dataset(rfilen)
                else:
                    print('choose only subslice')
                    timeslice_start = f"{fyears[rdx]['start_year']:04d}-01-01"
                    timeslice_end   = f"{fyears[rdx]['end_year']:04d}-12-17"
                    print('Selecting:')
                    print(timeslice_start)
                    print(timeslice_end)
                    filedum = xr.open_dataset(rfilen).sel(time=slice(timeslice_start,timeslice_end))
                all_files.append(filedum)
        
            # Concatenate the preprocessed datasets
            combined = xr.concat(all_files, dim='time')
            ds = combined.chunk({'time':12,'lat':-1,'lon':-1})
            print(ds)
                    #ds = xr.open_mfdataset(rparam.filenames,use_cftime=True,preprocess=preprocess_rename_time,chunks={'time': -1})        
                
            # Merge datasets with preprocessing and deduplication
            #ds_merged = xr.open_mfdataset(rparam.filenames,combine="by_coords",parallel=True,chunks={'time': 12,'lat':-1,'lon':-1})
            ## Remove duplicates across all files (merged dataset)
            #_, index = np.unique(ds_merged['time'], return_index=True)
            #ds_deduplicated = ds_merged.isel(time=index)
    else:
        raise Exception('No or too many filenames found for this set of params.')

    ds['time'] = convert_to_cftime(ds.time.data, calendar="gregorian")

    if ds.time.data[0].year < 1850 or ds.time.data[0].year > 1861:
        years_to_add = 1850-ds.time.data[0].year
        ds['time'] = [t.replace(year=t.year + years_to_add) for t in ds.time.data]
        
    return ds    


def get_da_from_ds(rparam,ds):
    """
    extract dataarray from dataset
    """
    if rparam.protocol == 'TipESM':
        _, var_inside_file = getTipESMvarspecs(rparam.var)
    elif rparam.protocol in ['ScenarioMIP','CMIP']:
        _, var_inside_file = getCMIPvarspecs(rparam.var)
    else:
        raise Exception('This protocol type is not yet implemented.')
    da = ds[var_inside_file]

    if rparam.var == 'pCO2' and rparam.protocol == 'ScenarioMIP':
        da = da*9.8692326671601 # convert from Pascal to muatm
        da.attrs['units'] = 'uatm'
    elif rparam.var == 'siconc' and rparam.protocol == 'ScenarioMIP':
        da = da/100. # convert from percent to 0-1 fraction
        da.attrs['units'] = '-'
    elif rparam.var == 'siconc' and rparam.protocol == 'TipESM':
        da.attrs['units'] = '-'
    return da

def get_coordinates(rds,rparam):
    """
    This function is to extract the coordinates from all datasets.
    If they are all the same return one general version.
    Otherwise throw error.
    """

    rparam.lat = rds['lat']
    rparam.lon = rds['lon']

    return rparam




################################################
################################################
################################################
# Here go the specific functions for TipESM data
################################################
################################################
################################################



def getTipESMmodfiles(rparam): #var, experiment, model, keep_models='all', frequency='monthly', endyear=2100):
    """
    Get list of TipESM filenames and corresponding list of models for the given attributes of rparam
    """

    # define some settings
    var_in_filename, _ = getTipESMvarspecs(rparam.var)
    exid = 'OptimESM'
    ensemble_run = 'r0p1i1f1'
    if rparam.frequency == 'monthly':
        freqval = '1M'
    else:
        raise Exception('Case for other frequencies not yet implemented.')

    # construct filename and directory
    if rparam.var in ['CO2','t2m']:
        prefix = '/thredds/tgcc/store/torreso/FICHIER_SIMU_OptimESM/'
        filenames = glob.glob(f'{prefix}{exid}.{rparam.experiment}.{ensemble_run}_*_{freqval}_{var_in_filename}.nc')
    else:
        prefix = '/data/ekoehn/projects/TipESM/'
        if rparam.frequency == 'monthly':
            prefix += 'Omon/'
        else:
            raise Exception('Case for other frequencies not yet implemented.')
        grid = 'r360x180'
        filenames = glob.glob(f'{prefix}{rparam.model}/{grid}/{exid}.{rparam.experiment}.{ensemble_run}_*_{freqval}_{var_in_filename}.nc')

    return filenames


def getTipESMvarspecs(var):
    if var in ['Alkalini','Alk','Alkalinity']:
        var_in_filename = 'Alkalini'
        var_inside_file = 'Alkalini'
    elif var in ['BetaD','betaD','revelle_factor']:
        var_in_filename = 'BetaD'
        var_inside_file = 'BetaD'
    elif var in ['co2_flux','cflx','Cflx','CFLX']:
        var_in_filename = 'Cflx'
        var_inside_file = 'Cflx'
    elif var in ['DIC','dic','TCO2','tco2']:
        var_in_filename = 'DIC'
        var_inside_file = 'DIC'
    elif var in ['intpp','INTPP','IntPP','Intpp','integrated_pp','int_primary_productivity']:
        var_in_filename = 'INTPP'
        var_inside_file = 'INTPP'
    elif var in ['OmegaA','omegaa','omega_aragonite','Omega_Aragonite']:
        var_in_filename = 'OmegaA'
        var_inside_file = 'OmegaA'
    elif var in ['OmegaC','omegac','omega_calcite','Omega_Calcite']:
        var_in_filename = 'OmegaC'
        var_inside_file = 'OmegaC'
    elif var in ['pco2','PCO2','PCo2','Pco2','pCO2','pCo2']:
        var_in_filename = 'pco2'
        var_inside_file = 'pCO2'
    elif var in ['ph','PH','Ph','pH']:
        var_in_filename = 'ph'
        var_inside_file = 'pH'
    elif var in ['po4','PO4','Po4','phosphate']:
        var_in_filename = 'PO4'
        var_inside_file = 'PO4'
    elif var in ['sio3','SiO3','Sio3','SIO3','silicate']:
        var_in_filename = 'Si'
        var_inside_file = 'Si'
    elif var in ['sos','SOS','Sos','sss','SSS','Sis','S','s','salinity']:
        var_in_filename = 'sos'
        var_inside_file = 'sos'     
    elif var in ['tos','TOS','Tos','sst','SST','Tis','T','t','temperature']:
        var_in_filename = 'tos'
        var_inside_file = 'tos' 
    elif var in ['siconc','SICONC','seaice','seaice_conc','seaice_concentration']:
        var_in_filename = 'siconc'
        var_inside_file = 'siconc'
    elif var in ['air_co2','atmco2','co2','CO2','Co2']:
        var_in_filename = 'CO2'
        var_inside_file = 'CO2'  
    elif var in ['t2m','T2M','temp_2m','2mT','2mt','temp2meter','2metertemp']:
        var_in_filename = 't2m'
        var_inside_file = 't2m'  
    else:
        raise Exception('Not yet implemented for this variable.')
    return var_in_filename, var_inside_file




################################################
################################################
################################################
# Here go the specific functions for CMIP6 data#
################################################
################################################
################################################


def getCMIP6modfiles(rparam): 
 
    """
    Get list of CMIP filenames and corresponding list of models for the 'var' variable in CMIP5/6
    These files are all in a single directory 
    """

    # define some settings
    var_in_filename, _ = getCMIPvarspecs(rparam.var)
    if var_in_filename in ['CO2','tas','t2m','tauu','ps','psl']:
        domain_letter = 'A'
        domain_word = 'atmos'
    elif var_in_filename in ['siconc']:
        domain_letter = 'SI'
        domain_word = 'seaice'
    else:
        domain_letter = 'O'
        domain_word = 'ocnBgchem'
        
    # get the frequency
    if rparam.frequency == 'monthly':
        freqval = 'mon'
    elif rparam.frequency == 'annual':
        freqval = 'yr'
    else:
        raise Exception('Case for other frequencies not yet implemented.')
    
    # grid
    grid = 'gr'

    # variant
    variant = 'r1i1p1f1'

    # START BUILDING THE DIRECTORY AND FILENAME
    cmip_cycle_experiments = ['1pctCO2','1pctCO2-cdr','historical','piControl','ssp126','ssp245','ssp370','ssp534-over','ssp585']
    if rparam.var in ['mlotst','zos','thetao300','tauu','so300','sos','ps','psl','dpco2','tas','o2300','epc100','talk1','dissic1','pco2','siconc','ph1','tos','intdissic','mino2','po41','si1','no31','thetao1','so1']:
        prefix = '/data/ekoehn/CMIP6_derived/'
    elif rparam.var in ['fgco2'] and rparam.protocol == 'CMIP':
        prefix = '/data/ekoehn/CMIP6_derived/'
    else:
        prefix = '/modfs/project/OCMIP6/CMIP6_derived/'
    # make sure cmip_cycle and experiment are consistent
    assert rparam.experiment in cmip_cycle_experiments

    #
    if rparam.var in ['CO2','t2m']:
        raise Exception('Not implemented for atmospheric variables.')
    elif rparam.model in ['CESM2','ACCESS-ESM1-5'] and rparam.var in ['dissic1'] and rparam.experiment in ['1pctCO2','1pctCO2-cdr']:
        freqval2 = 'yr'
        direc = f'{prefix}{var_in_filename}/{rparam.experiment}/{domain_letter}{freqval2}/'
        filenames = glob.glob(f'{direc}{var_in_filename}_{domain_letter}{freqval2}_{rparam.model}_{rparam.experiment}_*.nc')
    else:
        direc = f'{prefix}{var_in_filename}/{rparam.experiment}/{domain_letter}{freqval}/'
        filenames = glob.glob(f'{direc}{var_in_filename}_{domain_letter}{freqval}_{rparam.model}_{rparam.experiment}_*.nc')
        #print(filenames)

    if len(filenames)==0:
        print('Attention: No files found for these model specs.')

    # the following if statement was only included, since there is spurious data in the folder "/modfs/project/OCMIP6/CMIP6_derived/intpp/1pctCO2-cdr/Omon". UKESM and MIROC model appear twice.
    print(filenames)
    if (rparam.var == 'intpp' and rparam.model == 'UKESM1-0-LL') or (rparam.var == 'intpp' and rparam.model=='MIROC-ES2L'):
        filenames = [filenames[-1]]
    print(filenames)

    # choose the long version (until 2300) if existing, variant if existing, otherwise take any other
    filenames_short = []


    if len(filenames)>=1:
        variant_checks = np.array([variant in filename for filename in filenames]) 
        if hasattr(rparam, 'endyear'):
            year_checks = np.array([str(rparam.endyear) in filename for filename in filenames])
        else:
            year_checks = np.zeros_like(variant_checks,dtype='bool')
        combined_checks = year_checks*variant_checks

        if np.sum(combined_checks)>=1:
            filenames_short = [filenames[int(np.argwhere(combined_checks==1))]]
        elif np.sum(year_checks)>=1:
            #print(year_checks)
            #print(np.argwhere(year_checks==1))
            selector = np.argwhere(year_checks==1).flatten()
            dummy_selected_files = sorted([filenames[select] for select in selector])
            filenames_short = [dummy_selected_files[0]]
        elif np.sum(variant_checks)>=1:
            filenames_short = [filenames[int(np.argwhere(variant_checks==1))]]
        else:
            filenames_short = [sorted(filenames)[0]]
    else:
        filenames_short = []

    return filenames_short


def getCMIPvarspecs(var):
    if var in ['Alkalini','Alk','Alkalinity']:
        var_in_filename = 'Alkalini'
        var_inside_file = 'Alkalini'
    elif var in ['BetaD','betaD','revelle_factor']:
        var_in_filename = 'BetaD'
        var_inside_file = 'BetaD'
    elif var in ['co2_flux','cflx','Cflx','CFLX']:
        var_in_filename = 'Cflx'
        var_inside_file = 'Cflx'
    elif var in ['DIC','dic','TCO2','tco2']:
        var_in_filename = 'DIC'
        var_inside_file = 'DIC'
    elif var in ['intpp','INTPP','IntPP','Intpp','integrated_pp','int_primary_productivity']:
        var_in_filename = 'intpp'
        var_inside_file = 'intpp'
    elif var in ['OmegaA','omegaa','omega_aragonite','Omega_Aragonite']:
        var_in_filename = 'OmegaA'
        var_inside_file = 'OmegaA'
    elif var in ['OmegaC','omegac','omega_calcite','Omega_Calcite']:
        var_in_filename = 'OmegaC'
        var_inside_file = 'OmegaC'
    elif var in ['pco2','PCO2','PCo2','Pco2','pCO2','pCo2']:
        var_in_filename = 'spco2'
        var_inside_file = 'spco2'
    elif var in ['ph','PH','Ph','pH']:
        var_in_filename = 'ph'
        var_inside_file = 'pH'
    elif var in ['po4','PO4','Po4','phosphate']:
        var_in_filename = 'PO4'
        var_inside_file = 'PO4'
    elif var in ['sio3','SiO3','Sio3','SIO3','silicate']:
        var_in_filename = 'Si'
        var_inside_file = 'Si'
    elif var in ['sos','SOS','Sos','sss','SSS','Sis','S','s','salinity']:
        var_in_filename = 'sos'
        var_inside_file = 'sos'     
    elif var in ['tos','TOS','Tos','sst','SST','Tis','T','t','temperature']:
        var_in_filename = 'tos'
        var_inside_file = 'tos' 
    elif var in ['siconc','SICONC','seaice','seaice_conc','seaice_concentration']:
        var_in_filename = 'siconc'
        var_inside_file = 'siconc'
    elif var in ['air_co2','atmco2','co2','CO2','Co2']:
        var_in_filename = 'CO2'
        var_inside_file = 'CO2'  
    elif var in ['t2m','T2M','temp_2m','2mT','2mt','temp2meter','2metertemp']:
        var_in_filename = 't2m'
        var_inside_file = 't2m'  
    elif var in ['tas']:
        var_in_filename = 'tas'
        var_inside_file = 'tas'
    elif var in ['mlotst']:
        var_in_filename = 'mlotst'
        var_inside_file = 'mlotst'  
    elif var in ['fgco2']:
        var_in_filename = 'fgco2'
        var_inside_file = 'fgco2'  
    elif var in ['dpco2']:
        var_in_filename = 'dpco2'
        var_inside_file = 'dpco2'  
    elif var in ['zos']:
        var_in_filename = 'zos'
        var_inside_file = 'zos'  
    elif var in ['thetao300']:
        var_in_filename = 'thetao300'
        var_inside_file = 'thetao'       
    elif var in ['so300']:
        var_in_filename = 'so300'
        var_inside_file = 'so'   
    elif var in ['tauu']:
        var_in_filename = 'tauu'
        var_inside_file = 'tauu'      
    elif var in ['ps']:
        var_in_filename = 'ps'
        var_inside_file = 'ps'   
    elif var in ['psl']:
        var_in_filename = 'psl'
        var_inside_file = 'psl'       
    elif var in ['tas']:
        var_in_filename = 'tas'
        var_inside_file = 'tas'    
    elif var in ['o2300']:
        var_in_filename = 'o2300'
        var_inside_file = 'o2'  
    elif var in ['epc100']:
        var_in_filename = 'epc100'
        var_inside_file = 'epc100'          
    elif var in ['talk1']:
        var_in_filename = 'talk1'
        var_inside_file = 'talk'  
    elif var in ['dissic1']:
        var_in_filename = 'dissic1'
        var_inside_file = 'dissic'  
    elif var in ['intdissic']:
        var_in_filename = 'intdissic'
        var_inside_file = 'dissic'  
    elif var in ['ph1']:
        var_in_filename = 'ph1'
        var_inside_file = 'ph'  
    elif var in ['mino2']:
        var_in_filename = 'mino2'
        var_inside_file = 'o2'  
        var_inside_file = 'ph'  
    elif var in ['po41']:
        var_in_filename = 'po41'
        var_inside_file = 'po4' 
    elif var in ['no31']:
        var_in_filename = 'no31'
        var_inside_file = 'no3' 
    elif var in ['si1']:
        var_in_filename = 'si1'
        var_inside_file = 'si' 
    elif var in ['thetao1']:
        var_in_filename = 'thetao1'
        var_inside_file = 'thetao' 
    elif var in ['so1']:
        var_in_filename = 'so1'
        var_inside_file = 'so' 
    else:
        raise Exception('Not yet implemented for this variable.')
    return var_in_filename, var_inside_file



###########################################################
###########################################################
### Get the atmospheric fields ############################
###########################################################
###########################################################


def get_global_average_atmospheric_data(rparam,atm_var):
    if rparam.protocol_gen == 'tipesm':
        atm_ds = getTipESMatmosphere(rparam,atm_var)
    elif rparam.protocol_gen == 'cmip6':
        atm_ds = getCMIP6atmosphere(rparam,atm_var)
    elif rparam.protocol_gen == 'cmip5':
        raise Exception('Not yet implemented.')
        #atm_ds = getCMIP5atmosphere(rparam)
    return atm_ds


def getCMIP6atmosphere(rparam,atm_var):
    atm_ds = xr.Dataset()
    _, var_inside_file = getCMIPvarspecs(atm_var)
    
    if atm_var == 'CO2':
        da = get_CMIP6atmco2(rparam,atm_var)
    elif atm_var == 't2m':
        da = get_CMIP6atmt2m(rparam,atm_var)
        
    if hasattr(rparam, 'prepend_hist'):
        if rparam.prepend_hist == True and rparam.experiment != '1pctCO2-cdr':
            print('need to prepend the historical data')
            rparam_hist = deepcopy(rparam)
            rparam_hist.experiment = 'historical'
            if atm_var == 'CO2':
                hist_da = get_CMIP6atmco2(rparam_hist,atm_var)
            elif atm_var == 't2m':
                hist_da = get_CMIP6atmt2m(rparam_hist,atm_var)
            #print('concatenate')
            all_da = xr.concat((hist_da,da),dim='time')
        else:
            print('not prepending historical run')
            all_da = da
    else:
        print('not prepending historical run')
        all_da = da

    #print(all_da)
    atm_ds[atm_var] = all_da

    atm_ds[atm_var+'_annual_mean'] = atm_ds[atm_var].resample(time='1YE').mean().rename({'time': 'year'})

    return atm_ds
    

def get_CMIP6atmco2(rparam,atm_var):
    dir_atmco2 = '/home/jomce/Projects/ipcc/ar6/parts/'
    if rparam.experiment == 'historical':
        file_atmco2 = dir_atmco2 + 'atmCO2_CMIP6_' + 'historical' + '.csv'
    elif rparam.experiment == '1pctCO2-cdr':
        file_atmco2 = 'no file present'
    else:
        file_atmco2 = dir_atmco2 + 'atmCO2_CMIP6_' + rparam.experiment + '.csv'

    if rparam.experiment == '1pctCO2-cdr':
        
        ## 1% increase for 140 yr then opposite trend over next 140 yr; after hold at 284.7 ppm 
        #yearco2=np.arange(141) #edges of years (Jan 1) - goes to Jan 1 of year 141
        ## 284.7 ppm is the atmospheric CO2 of piControl (1850 value in historical)
        ## first 140 years 1% increase per year
        #atmco2 = 284.7 * 1.01**yearco2
        ## second 140 years (mirror image, decline), makes len(atmco2) = 281
        #atmco2 = np.concatenate((atmco2, atmco2[::-1][1:]))
        ## Extend 60 years with atm CO2 = 284.7 ppm (preindustrial value), makes len(atmco2) = 341
        #atmco2_extend = 284.7 * np.ones((60))
        #atmco2 = np.concatenate((atmco2, atmco2_extend))
        #yearco2 = 1850+np.arange(np.size(atmco2))#
        #
        ## newly added line to make it consistent with J. Orr's treatment (Feb 26, 2025)
        #atmco2 = np.interp(yearco2+0.5, yearco2, atmco2)      #Interpolate with year and yearco2 all at mid-year
        
        #pi_value = 284.7
        #rampup_years = np.arange(0,140,1/365)
        #rampup_co2 = pi_value*(1.01**rampup_years)
        #rampdown_years = np.arange(140,280,1/365)
        #rampdown_co2 = rampup_co2[-1]*(0.99**(rampdown_years-140))
        #stabilization_years = np.arange(280,340,1/365)
        #stabilization_co2 = np.ones_like(stabilization_years)*pi_value
        #atmosphere_co2_daily = np.concatenate((rampup_co2,rampdown_co2,stabilization_co2))
        #atmco2 = np.array([np.mean(atmosphere_co2_daily[int(i*365):int((i+1)*365)]) for i in range(int(len(atmosphere_co2_daily)/365))])
        #yearco2 = 1850+np.arange(np.size(atmco2))
        #atmco2_monthly = np.repeat(atmco2,12)
        #yearco2_monthly = [cftime.DatetimeGregorian(year, month, 16) for year in yearco2 for month in range(1,13)]
        #da = xr.DataArray(data=atmco2_monthly,coords={"time": yearco2_monthly},dims=["time"],name=atm_var)

        pi_value = 284.7#28.844391901636502* 1e6/101325 #28.844332#28.8472275#28.80853#28.844332
        idealized_atmco2_rampup = pi_value*((1.01)**np.arange(0,140,1))
        idealized_atmco2_rampdown = idealized_atmco2_rampup[-1]*((0.99)**np.arange(0,139,1))
        idealized_atmco2_stabil = np.ones(62)*pi_value
        idealized_atmco2 = np.concatenate((idealized_atmco2_rampup,idealized_atmco2_rampdown,idealized_atmco2_stabil))
        #idealized_atmco2_yearly = np.array([np.mean(idealized_atmco2[int(i*365):int((i+1)*365)]) for i in range(int(len(idealized_atmco2)/365))])
        idealized_atmco2_yearly = idealized_atmco2
        yearco2 = 1850+np.arange(len(idealized_atmco2_yearly))
        #idealized_atmco2 = np.interp(yearco2+0.5, yearco2, idealized_atmco2)
        atmco2_monthly = np.repeat(idealized_atmco2_yearly,12)
        yearco2_monthly = [cftime.DatetimeGregorian(year, month, 16) for year in yearco2 for month in range(1,13)]
        da = xr.DataArray(data=atmco2_monthly,coords={"time": yearco2_monthly},dims=["time"],name=atm_var)

    else:
        df_atmco2 = pd.read_csv(file_atmco2)
        yearco2_dum     = df_atmco2['year'].values
        atmco2          = df_atmco2['atmCO2'].values
        yearco2_monthly = [cftime.DatetimeGregorian(year, month, 16) for year in yearco2_dum for month in range(1,13)]
        atmco2_monthly = [atmco2val for atmco2val in atmco2 for month in range(1,13)]
        # put monthly data to real data
        yearco2 = yearco2_monthly
        atmco2  =  atmco2_monthly
        #
        da = xr.DataArray(data=atmco2,coords={"time": yearco2},dims=["time"],name=atm_var)
    return da

def get_CMIP6atmt2m(rparam,atm_var):
    rparam_t2m = deepcopy(rparam)
    rparam_t2m.var = 'tas'
    paths = getCMIP6modfiles(rparam_t2m)
    _, var_inside_file = getCMIPvarspecs(rparam_t2m.var)
    ds = xr.open_dataset(paths[0],use_cftime=True,decode_times=False) # ,engine='h5netcdf'
    if 'time_counter' in ds.dims:
        ds = ds.rename({'time_counter':'time'})
    #time_dim = 'time'#_counter'
    ds['time'] = cftime.num2date(ds['time'].values, units=ds['time'].units, calendar=ds['time'].calendar)
    ds_chunked = ds.chunk({'time': 12})
    da = ds_chunked[var_inside_file]    
    lon = da.lon
    lat = da.lat
    # get the general area weights
    #print('---Get the general area weights---')
    rparam_t2m = MaskGetter.get_area_weights(rparam_t2m,weight_choice='coslat')  # Jim Orr used WOA2001 grid - should i use the same?
    da_area_averaged = da.weighted(rparam_t2m.area_weights).mean(["lat","lon"])
    #print(da_area_averaged.time)
    #print(da.time)
    da_area_averaged['time'] = da.time
    return da_area_averaged

def getTipESMatmosphere(rparam,atm_var):
    #atm_das = []
    atm_ds = xr.Dataset()
    
    rparam_atm = deepcopy(rparam)
    rparam_atm.var = atm_var
    _, var_inside_file = getTipESMvarspecs(atm_var)
    paths = getTipESMmodfiles(rparam_atm)
    ds = xr.open_dataset(paths[0],use_cftime=True,decode_times=False)
    if 'time_counter' in ds.dims:
        ds = ds.rename({'time_counter':'time'})
    ds_chunked = ds.chunk({'time': 12})
    # get the area weights
    weights_file = '/bdd/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/fx/areacella/gr/latest/areacella_fx_IPSL-CM6A-LR_historical_r1i1p1f1_gr.nc'
    weights_ds = xr.open_dataset(weights_file)
    area_weights_atm = weights_ds.areacella
    da = ds_chunked[var_inside_file]
    da_weighted_average = da.weighted(area_weights_atm).mean(["lat","lon"])
    #da_weighted_average.attrs = da.attrs
    da_weighted_average['time'] = cftime.num2date(ds['time'].values, units=ds['time'].units, calendar=ds['time'].calendar)
    atm_ds[atm_var] = da_weighted_average.squeeze()

    atm_ds[atm_var+'_annual_mean'] = atm_ds[atm_var].resample(time='1YE').mean().rename({'time': 'year'})

    
    return atm_ds


##################################################
##################################################
#### OTHERS ######################################
##################################################
##################################################

def get_unit_dict():
    varia_unit = dict()
    varia_unit['pco2']='uatm'
    varia_unit['siconc'] = 'Ice fraction'
    varia_unit['INTPP']='mol/m2/s'
    varia_unit['tos']='°C'
    varia_unit['sos']='1e-3'
    varia_unit['ph']='-'
    varia_unit['Cflx']='mol/m2/s'
    varia_unit['OmegaA']='-'
    return varia_unit
    
def cftime_to_datetime_safe(cftime_date):
    """Safely converts cftime.DatetimeGregorian to datetime.datetime."""
    return datetime.datetime.strptime(
        cftime_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'
    )
