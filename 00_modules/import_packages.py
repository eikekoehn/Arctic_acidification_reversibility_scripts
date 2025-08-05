"""
author: Eike E. Köhn
date: July 29, 2025
description: functions to load in a set of packages required
"""

class PackageGetter:
        
    @staticmethod
    def import_standard_packages_for_analysis_and_plotting():
    
        # import system packages
        import sys
        import os    
        from copy import deepcopy
        import importlib
        from importlib import reload
        import glob
        
        # import netcdf packages
        import netCDF4
        import xarray as xr
        import dask
    
        # import time packages
        import time
        import cftime
        import datetime
        #import time as tim
    
        # import analysis packages
        import numpy as np
        import numpy.ma as ma
        import pandas as pd
        from scipy import interpolate
        from scipy import stats as spstats
    
        # import plotting packages
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        import matplotlib.ticker as plticker
        from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
        import cmocean as cmo
        #%matplotlib inline
        import matplotlib.colors as mcolors
        import matplotlib.patches as mpatches
    
        # import mapping packages
        import cartopy.crs as ccrs
        import cartopy
        from cartopy.util import add_cyclic_point
    
        # suppress deprecation warnings
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)

        # Local dictionary for return
        return locals()

    
    @staticmethod
    def import_custom_packages():
        import sys
        sys.path.append('../00_modules/')

        # import the parameters
        from set_params import Params

        # import the classes for getting model data
        from get_model_datasets import ModelDataGetter

        # import the class for getting miscellaneous data
        from get_misc_data import MiscDataGetter

        # import hysteresis functions from the python package (available on github)
        from funcs_for_hysteresis import HystFuncs

        # import functions for the multimodel analysis
        from funcs_for_multimodel_analysis import MMFuncs

        # import plotting functions
        from funcs_for_plotting import Plotter

        # import splining functions
        import splining_functions as Spliner

        # import conversion functions
        from funcs_for_conversions import Converter

        # import functions for Taylor decomposition
        from funcs_for_taylor_decomposition import TaylorFuncs
        
        #import get_modeldata_functions_new as ModelGetter
        #import xrmasking_functions_new as MaskGetter
        #import xrsplining_functions as Spliner
        #import plotting_functions as Plotter
        #import tipping_functions as Tipper
        ####### import custom interpolation packages
        #######import fastspline
        
        # Local dictionary for return
        return locals()



    