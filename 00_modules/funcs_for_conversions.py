"""
author: Eike E. Köhn
date: July 31, 2025
description: Functions to convert between units.
"""

import sys
sys.path.append('../00_modules/.')
from get_model_datasets import ModelDataGetter

import xarray as xr

class Converter:
    def __convert_by_multiplication(a,conv_factor):
        a_converted = a*conv_factor
        return a_converted

    def __conversion_factors(conversion_type,sw_density=None):
        if conversion_type == 'from_1_to_micro':
            conversion_factor = 1000 * 1000
        elif conversion_type == 'from_per_kg_to_per_m3':
            assert sw_density is not None
            conversion_factor = sw_density
        elif conversion_type == 'from_per_m3_to_per_kg':
            assert sw_density is not None
            conversion_factor = 1/sw_density
        elif conversion_type == 'from_kg_to_g':
            conversion_factor = 1000
        elif conversion_type == 'from_per_second_to_per_year':
            conversion_factor = 60*60*24*365.25
        elif conversion_type == 'from_kg_to_Tg':
            conversion_factor = 1/(1000*1000*1000)
        elif conversion_type == 'from_1_to_nano':
            conversion_factor = 1000*1000*1000
        return conversion_factor

    def _convert_from_mol_per_m3_to_mumol_per_kg(run_params,run_paths,temporal_resolution,depth_to_analyze):
        """
        A function to convert from "mol per m3" to "mumol per kg".
        Density is required to do this.
        """

        # first get the density data
        dens_paths = ModelDataGetter._identify_path_strings(run_params,'denis',depth_to_analyze)
        #ds_dens_dict   = ModelDataGetter._open_datasets(dens_paths)

        # now, go through each model and multiply with a conversion factor
        ds_conv_dict = dict()
        for key in run_params.keys():
            if isinstance(run_paths[key],str):
                with xr.open_dataset(run_paths[key]) as ds_data:
                    datum = ds_data[temporal_resolution]
                    with xr.open_dataset(dens_paths[key]) as ds_dens:
                        dens = ds_dens[temporal_resolution]
                        conv_factor = Converter.__conversion_factors('from_per_m3_to_per_kg',dens) * Converter.__conversion_factors('from_1_to_micro')
                    converted_datum = Converter.__convert_by_multiplication(datum,conv_factor)
            elif isinstance(run_paths[key],xr.Dataset):
                datum = run_paths[key][temporal_resolution]
                with xr.open_dataset(dens_paths[key]) as ds_dens:
                    dens = ds_dens[temporal_resolution]
                    conv_factor = Converter.__conversion_factors('from_per_m3_to_per_kg',dens) * Converter.__conversion_factors('from_1_to_micro')
                converted_datum = Converter.__convert_by_multiplication(datum,conv_factor)
            converted_datum.attrs["units"] = "mumol per kg"
            converted_ds = xr.Dataset()
            converted_ds[temporal_resolution] = converted_datum
            ds_conv_dict[key] = converted_ds

        return ds_conv_dict

    
    def _normalize_with_salinity(run_params,run_paths,temporal_resolution,depth_to_analyze,var_to_analyze,standard_salinity=35):
        """
        A function to normalize a concentration with salinity (in psu). Standardized to a standard_salinity of 35 psu (default).
        """

        # first get the salinity data
        salt_paths = ModelDataGetter._identify_path_strings(run_params,'so',depth_to_analyze)
        #print(salt_paths)            
        #ds_salt_dict   = ModelDataGetter._open_datasets(salt_paths)
        #print(ds_salt_dict)
        
        # now, go through each model and multiply with a conversion factor
        ds_snorm_dict = dict()
        for key in run_params.keys():
            if isinstance(run_paths[key],str):
                with xr.open_dataset(run_paths[key]) as ds_data:
                    datum = ds_data[temporal_resolution]
                    with xr.open_dataset(salt_paths[key]) as ds_salt:
                        salt = ds_salt[temporal_resolution]
                        conv_factor = 1/salt * standard_salinity # 
                    converted_datum = Converter.__convert_by_multiplication(datum,conv_factor)
            elif isinstance(run_paths[key],xr.Dataset):
                datum = run_paths[key][temporal_resolution]
                with xr.open_dataset(salt_paths[key]) as ds_salt:
                    salt = ds_salt[temporal_resolution]
                    conv_factor = 1/salt * standard_salinity # 
                converted_datum = Converter.__convert_by_multiplication(datum,conv_factor)
            converted_ds = xr.Dataset()
            converted_ds[temporal_resolution] = converted_datum
            ds_snorm_dict[key] = converted_ds
        var_to_analyze_normalized = var_to_analyze + '_salinity_normalized'

        return ds_snorm_dict, var_to_analyze_normalized