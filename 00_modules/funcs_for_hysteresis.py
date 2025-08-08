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

import xarray as xr

class HystFuncs:
    """
    description: Collection of a number of functions to handle hysteresis calculations.
    """

    def _calc_hysteresis_areas_1D_multimodel(
        rparams,
        rpaths,
        temporal_resolution,
        ds_atmCO2,
        normalizer='min_max_diff_full_cycle',
        nsteps=200,
        return_interpolated_vectors=False
    ):
        """
        Calculate hysteresis areas for all models over a 1D dataset, using a reference
        CO2 vector and selected normalization. Datasets can be paths or already-loaded.
    
        Parameters:
            rparams (dict): Run parameters for each model.
            rpaths (dict): File paths or datasets for each model.
            temporal_resolution (str): 'annual_means' or 'son_means'.
            ds_atmCO2 (dict): Dictionary of CO2 reference vectors per model.
            normalizer (str): Method to normalize hysteresis area.
            nsteps (int): Interpolation steps for the reference axis.
            return_interpolated_vectors (bool): If True, also return interpolated vectors.
    
        Returns:
            dict: Hysteresis area (and optionally interpolation vectors) for each model.
        """
        
        num_years_to_analyze = 280
        ha_dict = {}
    
        for key, run_param in rparams.items():
            print(f'Calculating hysteresis area for model {run_param.model} (key {key})...')
    
            # Helper: Load dataset and extract relevant time series
            def extract_data(ds):
                if temporal_resolution == 'annual_means':
                    raw_data = ds['annual_means']
                elif temporal_resolution == 'son_means':
                    raw_data = ds['seasonal_means'].sel(season='SON')
                else:
                    raise ValueError(f"Unknown temporal resolution: {temporal_resolution}")
                return raw_data.isel(year=slice(None, num_years_to_analyze))
    
            # Load from file or use already-loaded dataset
            if isinstance(rpaths[key], str):
                with xr.open_dataset(rpaths[key]) as ds_data:
                    clipped_data = extract_data(ds_data)
                    clipped_data.load()  # Load into memory before file closes
            elif isinstance(rpaths[key],xr.DataArray):
                clipped_data = rpaths[key].isel(year=slice(None, num_years_to_analyze))
            else:
                clipped_data = extract_data(rpaths[key])
    
            # Get matching CO2 reference vector
            ref_axis = ds_atmCO2[key].isel(year=slice(None, num_years_to_analyze))

            # Calculate hysteresis area
            ha_dict[key] = ha.calc_hysteresis_area_1D(
                ref_axis,
                clipped_data,
                nsteps=nsteps,
                normalizer=normalizer,
                return_interpolated_vectors=return_interpolated_vectors
            )
    
        return ha_dict

    
    def _calc_hysteresis_areas_3D_multimodel(
        rparams,
        rpaths,
        temporal_resolution,
        ds_atmCO2,
        normalizer='min_max_diff_full_cycle',
        nsteps=200,
        return_interpolated_vectors=False
    ):
        """
        Calculate hysteresis areas for all models over a 3D dataset, using a reference
        CO2 vector and selected normalization. Datasets can be paths or already-loaded.
    
        Parameters:
            rparams (dict): Run parameters for each model.
            rpaths (dict): File paths or datasets for each model.
            temporal_resolution (str): 'annual_means' or 'son_means'.
            ds_atmCO2 (dict): Dictionary of CO2 reference vectors per model.
            normalizer (str): Method to normalize hysteresis area.
            nsteps (int): Interpolation steps for the reference axis.
            return_interpolated_vectors (bool): If True, also return interpolated vectors.
    
        Returns:
            dict: Hysteresis area (and optionally interpolation vectors) for each model.
        """
        
        num_years_to_analyze = 280
        ha_dict = {}
    
        for key, run_param in rparams.items():
            print(f'Calculating hysteresis area for model {run_param.model} (key {key})...')
    
            # Helper: Load dataset and extract relevant time series
            def extract_data(ds):
                if temporal_resolution == 'annual_means':
                    raw_data = ds['annual_means']
                elif temporal_resolution == 'son_means':
                    raw_data = ds['seasonal_means'].sel(season='SON')
                else:
                    raise ValueError(f"Unknown temporal resolution: {temporal_resolution}")
                return raw_data.isel(year=slice(None, num_years_to_analyze))
    
            # Load from file or use already-loaded dataset
            if isinstance(rpaths[key], str):
                with xr.open_dataset(rpaths[key]) as ds_data:
                    clipped_data = extract_data(ds_data)
                    clipped_data.load()  # Load into memory before file closes
            elif isinstance(rpaths[key],xr.DataArray):
                clipped_data = rpaths[key].isel(year=slice(None, num_years_to_analyze))
            else:
                clipped_data = extract_data(rpaths[key])
    
            # Get matching CO2 reference vector
            ref_axis = ds_atmCO2[key].isel(year=slice(None, num_years_to_analyze))
    
            # Calculate hysteresis area
            ha_dict[key] = ha.calc_hysteresis_area_3D(
                ref_axis,
                clipped_data,
                nsteps=nsteps,
                normalizer=normalizer,
                return_interpolated_vectors=return_interpolated_vectors
            )
    
        return ha_dict


    def _reorganize_hysteresis_dict(run_params, hyst_dict_taylor):
        """
        Reorganizes hysteresis data into an xarray.Dataset where each contribution 
        is a separate DataArray with dimensions (h_definition, keys).
        
        Args:
            run_params (dict): Dictionary of model run identifiers.
            hyst_dict_taylor (dict): Nested dict: [contribution][model_key] -> object with hysteresis metrics.
            
        Returns:
            xarray.Dataset: Dataset with one DataArray per contribution.
        """
        contributions = [
            't', 's', 'alk', 'dic', 'alk_bgc', 'dic_bgc',
            'alk_dilution', 'dic_dilution', 'dilution_terms',
            'bgc_terms', 'alk_dic', 'taylor_sum', 'fwtaylor_sum'
        ]
    
        hysteresis_metrics = [
            'normalized_hysteresis_area',
            'signed_hysteresis_area',
            'hysteresis_area',
            'normalizer_value'
        ]
    
        dataset_dict = {}
    
        for cont in contributions:
            metric_arrays = {metric: [] for metric in hysteresis_metrics}
            model_keys = []
    
            for key in run_params.keys():
                data = hyst_dict_taylor[cont][key]
                for metric in hysteresis_metrics:
                    # Use getattr in case data is an object with attributes
                    metric_arrays[metric].append(getattr(data, metric))
                model_keys.append(key)
    
            # Concatenate each metric over the model keys dimension
            concatenated_metrics = [
                xr.concat(metric_arrays[metric], dim=xr.DataArray(model_keys, dims="run_keys"))
                for metric in hysteresis_metrics
            ]
    
            # Stack the metrics into one DataArray for this contribution
            contribution_array = xr.concat(
                concatenated_metrics,
                dim=xr.DataArray(hysteresis_metrics, dims="h_definition")
            )
    
            # Store in dataset dict
            dataset_dict[cont] = contribution_array
    
        # Return dataset
        return xr.Dataset(dataset_dict)

    
    def _reorganize_hysteresis_dict_model_direct(run_params, hyst_dict_model):
        """
        Reorganizes hysteresis data into an xarray.Dataset where each contribution 
        is a separate DataArray with dimensions (h_definition, keys).
        
        Args:
            run_params (dict): Dictionary of model run identifiers.
            hyst_dict_taylor (dict): Nested dict: [contribution][model_key] -> object with hysteresis metrics.
            
        Returns:
            xarray.Dataset: Dataset with one DataArray per contribution.
        """
    
        hysteresis_metrics = [
            'normalized_hysteresis_area',
            'signed_hysteresis_area',
            'hysteresis_area',
            'normalizer_value'
        ]
    
        dataset_dict = {}
        cont = 'model'
    
        metric_arrays = {metric: [] for metric in hysteresis_metrics}
        model_keys = []

        for key in run_params.keys():
            data = hyst_dict_model[key]
            for metric in hysteresis_metrics:
                # Use getattr in case data is an object with attributes
                metric_arrays[metric].append(getattr(data, metric))
            model_keys.append(key)

        # Concatenate each metric over the model keys dimension
        concatenated_metrics = [
            xr.concat(metric_arrays[metric], dim=xr.DataArray(model_keys, dims="run_keys"))
            for metric in hysteresis_metrics
        ]

        # Stack the metrics into one DataArray for this contribution
        contribution_array = xr.concat(
            concatenated_metrics,
            dim=xr.DataArray(hysteresis_metrics, dims="h_definition")
        )

        # Store in dataset dict
        dataset_dict[cont] = contribution_array
    
        # Return dataset
        return xr.Dataset(dataset_dict)

