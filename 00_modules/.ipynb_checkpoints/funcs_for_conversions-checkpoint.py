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
        return conversion_factor

    def _convert_from_mol_per_m3_to_mumol_per_kg(run_params,ds_data_dict,temporal_resolution,depth_to_analyze):
        """
        A function to convert from "mol per m3" to "mumol per kg".
        Density is required to do this.
        """

        # first get the density data
        dens_paths = ModelDataGetter._identify_path_strings(run_params,'denis',depth_to_analyze)
        print(dens_paths)
        ds_dens_dict   = ModelDataGetter._open_datasets(dens_paths)

        # now, go through each model and multiply with a conversion factor
        ds_conv_dict = dict()
        for key in run_params.keys():
            datum = ds_data_dict[key][temporal_resolution]
            dens = ds_dens_dict[key][temporal_resolution]
            conv_factor = Converter.__conversion_factors('from_per_m3_to_per_kg',dens) * Converter.__conversion_factors('from_1_to_micro')
            converted_datum = Converter.__convert_by_multiplication(datum,conv_factor)
            converted_datum.attrs["units"] = "mumol per kg"
            converted_ds = xr.Dataset()
            converted_ds[temporal_resolution] = converted_datum
            converted_ds
            ds_conv_dict[key] = converted_ds

        return ds_conv_dict