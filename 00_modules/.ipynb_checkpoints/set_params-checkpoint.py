"""
author: Eike E. Köhn
date: July 28, 2025
description: basic class to store information about the model runs
"""

class Params:
    def __init__(self, **attributes):
        """
        Initialize a new instance of the VarSimuObject class.
        :param attributes: Dictionary of attributes to set on the instance.
        """
        for key, value in attributes.items():
            setattr(self, key, value)

    @staticmethod
    def set_color_cycle():
        # define the color cycle in accordance with color blindness, see https://github.com/matplotlib/matplotlib/issues/9460
        color_cycle = ["None","k","#3f90da", "#ffa90e", "#bd1f01", "#94a4a2", "#832db6", "#a96b59", "#e76300", "#b9ac70", "#717581", "#92dadd"] 
        return color_cycle
    
    @classmethod
    def standard_set_1pctCO2cdr(cls):
        """
        Returns a dictionary of standard VarSimuObject instances with predefined attributes for the 1pctCO2cdr experiment
        """

        # set the color cycle
        color_cycle = cls.set_color_cycle()

        # define the different models used and their associated colors
        set_dict = dict()
        set_dict['2'] = cls(project='CMIP6', activity='CDRMIP', model='UKESM1-0-LL',   institution='MOHC',         experiment='1pctCO2-cdr', member='r1i1p1f2', preprend='1pctCO2', nyears=200, runcol=color_cycle[2]) # nyears = 'all'
        set_dict['3'] = cls(project='CMIP6', activity='CDRMIP', model='NorESM2-LM',    institution='NCC',          experiment='1pctCO2-cdr', member='r1i1p1f1', preprend='1pctCO2', nyears=200, runcol=color_cycle[3]) # nyears = 'all'
        set_dict['4'] = cls(project='CMIP6', activity='CDRMIP', model='MIROC-ES2L',    institution='MIROC',        experiment='1pctCO2-cdr', member='r1i1p1f2', preprend='1pctCO2', nyears=200, runcol=color_cycle[4]) # nyears = 'all'
        set_dict['5'] = cls(project='CMIP6', activity='CDRMIP', model='CNRM-ESM2-1',   institution='CNRM-CERFACS', experiment='1pctCO2-cdr', member='r1i1p1f2', preprend='1pctCO2', nyears=200, runcol=color_cycle[5]) # nyears = 'all'
        set_dict['6'] = cls(project='CMIP6', activity='CDRMIP', model='ACCESS-ESM1-5', institution='CSIRO',        experiment='1pctCO2-cdr', member='r1i1p1f1', preprend='1pctCO2', nyears=200, runcol=color_cycle[6]) # nyears = 'all'
        set_dict['7'] = cls(project='CMIP6', activity='CDRMIP', model='CESM2',         institution='NCAR',         experiment='1pctCO2-cdr', member='r1i1p1f1', preprend='1pctCO2', nyears=200, runcol=color_cycle[7]) # nyears = 'all'
        set_dict['8'] = cls(project='CMIP6', activity='CDRMIP', model='CanESM5',       institution='CCCma',        experiment='1pctCO2-cdr', member='r1i1p2f1', preprend='1pctCO2', nyears=200, runcol=color_cycle[8]) # nyears = 'all'
        set_dict['9'] = cls(project='CMIP6', activity='CDRMIP', model='GFDL-ESM4',     institution='NOAA-GFDL',    experiment='1pctCO2-cdr', member='r1i1p1f1', preprend='1pctCO2', nyears=200, runcol=color_cycle[9]) # nyears = 'all'       
        
        return set_dict


    @classmethod
    def test_set_1pctCO2cdr(cls):
        """
        Returns a dictionary of standard VarSimuObject instances with predefined attributes for the 1pctCO2cdr experiment
        """

        # set the color cycle
        color_cycle = cls.set_color_cycle()

        # define the different models used and their associated colors
        set_dict = dict()
        set_dict['2'] = cls(project='CMIP6', activity='CDRMIP', model='UKESM1-0-LL',   institution='MOHC',         experiment='1pctCO2-cdr', member='r1i1p1f2', preprend='1pctCO2', nyears=200, runcol=color_cycle[2]) # nyears = 'all'     
        return set_dict

    
    @classmethod
    def standard_set_piControl(cls):
        """
        Returns a dictionary of standard VarSimuObject instances with predefined attributes for the preindustrial control simulations
        """

        # set the color cycle
        color_cycle = cls.set_color_cycle()

        # define the different models used and their associated colors
        set_dict = dict()
        set_dict['2'] = cls(project='CMIP6', activity='CMIP', model='UKESM1-0-LL',   institution='MOHC',         experiment='piControl', member='r1i1p1f2', preprend=None, nyears=200, runcol=color_cycle[2]) # nyears = 'all'
        set_dict['3'] = cls(project='CMIP6', activity='CMIP', model='NorESM2-LM',    institution='NCC',          experiment='piControl', member='r1i1p1f1', preprend=None, nyears=200, runcol=color_cycle[3]) # nyears = 'all'
        set_dict['4'] = cls(project='CMIP6', activity='CMIP', model='MIROC-ES2L',    institution='MIROC',        experiment='piControl', member='r1i1p1f2', preprend=None, nyears=200, runcol=color_cycle[4]) # nyears = 'all'
        set_dict['5'] = cls(project='CMIP6', activity='CMIP', model='CNRM-ESM2-1',   institution='CNRM-CERFACS', experiment='piControl', member='r1i1p1f2', preprend=None, nyears=200, runcol=color_cycle[5]) # nyears = 'all'
        set_dict['6'] = cls(project='CMIP6', activity='CMIP', model='ACCESS-ESM1-5', institution='CSIRO',        experiment='piControl', member='r1i1p1f1', preprend=None, nyears=200, runcol=color_cycle[6]) # nyears = 'all'
        set_dict['7'] = cls(project='CMIP6', activity='CMIP', model='CESM2',         institution='NCAR',         experiment='piControl', member='r1i1p1f1', preprend=None, nyears=200, runcol=color_cycle[7]) # nyears = 'all'
        set_dict['8'] = cls(project='CMIP6', activity='CMIP', model='CanESM5',       institution='CCCma',        experiment='piControl', member='r1i1p2f1', preprend=None, nyears=200, runcol=color_cycle[8]) # nyears = 'all'
        set_dict['9'] = cls(project='CMIP6', activity='CMIP', model='GFDL-ESM4',     institution='NOAA-GFDL',    experiment='piControl', member='r1i1p1f1', preprend=None, nyears=200, runcol=color_cycle[9]) # nyears = 'all'       
        
        return set_dict

