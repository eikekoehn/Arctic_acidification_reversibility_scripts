"""
author: Eike E. Köhn
date: July 28, 2025
description: Collection of functions to get miscellaneous data.
"""

import xarray as xr
import numpy as np

class MiscDataGetter():
    """
    A class to load in miscellaneous data.
    """
    
    @staticmethod
    def _get_atmospheric_CO2(rparams):
        """
        Get the atmospheric CO2 concentration as defined by the 1pctCO2-cdr experiment.
        """
        da_atmCO2 = dict()
        for key in rparams.keys():
            if rparams[key].experiment != '1pctCO2-cdr':
                raise Exception('Not yet implemented for anything else than the 1pctCO2-cdr experiment.')
            else:
                # Set the preindustrial level of 
                pi_value = 284.7  #ppm 
                idealized_atmco2_rampup = pi_value*((1.01)**np.arange(0,140,1))
                idealized_atmco2_rampdown = idealized_atmco2_rampup[-1]*((0.99)**np.arange(0,139,1))
                idealized_atmco2_stabil = np.ones(61)*pi_value     
                idealized_atmco2 = np.concatenate((idealized_atmco2_rampup,idealized_atmco2_rampdown,idealized_atmco2_stabil))
                co2_year = 1850+np.arange(len(idealized_atmco2))
                da = xr.DataArray(data=idealized_atmco2,coords={"year": co2_year},dims=["year"],name='atmospheric_co2')
                da = da.assign_attrs({'unit':'ppm'})
                da_atmCO2[key] = da
        return da_atmCO2

    @staticmethod
    def _get_ocean_mask():
        mask_path = '../00_support_data/ocean_land_mask.nc'
        omask_ds = xr.open_dataset(mask_path)
        omask_ds = omask_ds.rename({'combined_mask':'ocean_mask'})
        omask_da = omask_ds.ocean_mask
        # Mask out different additional marginal seas
        latis = [(115,135),(121,128), (142,156),(143,146),(142,160),(159,165)] # Med Sea 1, Med Sea 2, Baltic 1, Baltic 2, Baffin Bay, Canadian Archipelago
        lonis = [(None,40),(357,None),(15,24),  (11,15),  (260,288),(237,270)] # Med Sea 1, Med Sea 2, Baltic 1, Baltic 2, Baffin Bay, Canadian Archipelago
        for lati, loni in zip(latis,lonis):
            lati0,lati1 = lati
            loni0,loni1 = loni
            # select the respective subset and set to 0, i.e. land
            subset = omask_da.isel(lat=slice(lati0,lati1), lon=slice(loni0,loni1)).copy()
            subset[:] = 0  # update the subset
            # Assign back to the original copy
            omask_da_mod = omask_da.copy()
            omask_da_mod.loc[dict(lat=omask_da.lat[lati0:lati1], lon=omask_da.lon[loni0:loni1])] = subset
            omask_da = omask_da_mod
        return omask_da

    @staticmethod
    def _get_grid_cell_areas():
        gridfile="/modfs/project/OCMIP5/DATA/GRID/WOA2001_grid.nc"
        gridds = xr.open_dataset(gridfile)
        gridds = gridds.rename({'AREA':'area'})
        grid_cell_areas = gridds.area#.values
        grid_cell_areas['longitude'] = grid_cell_areas['longitude']-0.5
        grid_cell_areas = grid_cell_areas.rename({'longitude':'lon','latitude':'lat'})
        return grid_cell_areas

    @staticmethod
    def _get_ocean_regions(return_lookup_dict=True):
        """
        Function to load in the ocean regions defined by the RECCAP2 project.
        """
        
        reg_ds = xr.open_dataset('../00_support_data/RECCAP2_region_masks_all_v20221025.nc')
        region_dict = dict()
        for oce in ['arctic','atlantic','pacific','indian','southern']:#,'open_ocean','coast']:
            dummy_mask = reg_ds[oce]
            for idx in range(1,np.max(dummy_mask.values)+1):
                dummy_mask2 = xr.where(dummy_mask==idx,1,0)
                # now shift by half a degree to make it align with other data to be analysed
                dummy_mask2 = dummy_mask2.assign_coords(lon=((dummy_mask2.lon - 0.5) % 360))  # Wraps around at 360°
                #
                new_lon = np.arange(0, 360, 1.0) % 360  # Ensures wrapping
                # regrid the mask accordingly 
                dummy_mask2_interpolated = dummy_mask2.interp(lon=new_lon, method="nearest")  # "nearest" preserves mask values (0/1)

                # now combine the mask with the global ocean mask
                omask_da = MiscDataGetter._get_ocean_mask()
                dummy_mask2_combined = dummy_mask2_interpolated * omask_da
                
                # put result into the region_dict
                region_dict[f'{oce}{int(idx)}'] = dummy_mask2_combined

        # add a pan Arctic mask
        region_dict['arctic_full'] = region_dict['arctic1']+region_dict['arctic2']+region_dict['arctic3']+\
                            region_dict['arctic4']+region_dict['arctic5']+region_dict['arctic6']+\
                            region_dict['arctic7']+region_dict['arctic8']+region_dict['arctic9']+region_dict['arctic10']
        # add a pan Atlantic mask
        region_dict['atlantic_full'] = region_dict['atlantic1']+region_dict['atlantic2']+region_dict['atlantic3']+\
                            region_dict['atlantic4']+region_dict['atlantic5']+region_dict['atlantic6']
        # add a pan Pacific mask
        region_dict['pacific_full'] = region_dict['pacific1']+region_dict['pacific2']+region_dict['pacific3']+\
                            region_dict['pacific4']+region_dict['pacific5']+region_dict['pacific6']
        # add a pan Indian mask
        region_dict['indian_full'] = region_dict['indian1']+region_dict['indian2']+region_dict['indian3']+\
                            region_dict['indian4']
        # add a pan Southern Ocean mask
        region_dict['southern_full'] = region_dict['southern1']+region_dict['southern2']+region_dict['southern3']
        # add a global ocean mask
        region_dict['global_ocean'] = region_dict['arctic_full'] + region_dict['atlantic_full'] + region_dict['pacific_full'] + region_dict['indian_full'] + region_dict['southern_full']

        # convert region_dict into a xarray dataset
        region_ds = xr.Dataset(region_dict)
        
        # Create a region lookup dict
        region_lookup_dict = dict()
        region_lookup_dict['arctic_full']   = 'Arctic Ocean'
        region_lookup_dict['atlantic_full'] = 'Atlantic Ocean'
        region_lookup_dict['pacific_full']  = 'Pacific Ocean'
        region_lookup_dict['indian_full']   = 'Indian Ocean'
        region_lookup_dict['southern_full'] = 'Southern Ocean'
        region_lookup_dict['global_ocean']  = 'Global Ocean'
        region_lookup_dict['arctic1']     = 'central Arctic'
        region_lookup_dict['arctic2']     = 'East Greenland'
        region_lookup_dict['arctic3']     = 'Baffin Bay'
        region_lookup_dict['arctic4']     = 'Canadian Archipelago'
        region_lookup_dict['arctic5']     = 'Canadian North Coast'
        region_lookup_dict['arctic6']     = 'Chukchi Sea'
        region_lookup_dict['arctic7']     = 'East Siberian Sea'
        region_lookup_dict['arctic8']     = 'Laptev Sea'
        region_lookup_dict['arctic9']     = 'Kara Sea'
        region_lookup_dict['arctic10']    = 'Barents Sea'
        region_lookup_dict['atlantic1']   = 'subpolar North Atlantic'
        region_lookup_dict['atlantic2']   = 'intergyre North Atlantic'
        region_lookup_dict['atlantic3']   = 'subtropical North Atlantic'
        region_lookup_dict['atlantic4']   = 'tropical Atlantic'
        region_lookup_dict['atlantic5']   = 'subtropical South Atlantic'
        region_lookup_dict['atlantic6']   = 'Mediterranean Sea'
        region_lookup_dict['pacific1']    = 'subpolar North Pacific'
        region_lookup_dict['pacific2']    = 'intergyre North Pacific'
        region_lookup_dict['pacific3']    = 'subtropical North Pacific'
        region_lookup_dict['pacific4']    = 'western tropical Pacific'
        region_lookup_dict['pacific5']    = 'eastern tropical Pacific'
        region_lookup_dict['pacific6']    = 'subtropical South Pacific'
        region_lookup_dict['indian1']     = 'Arabian Sea'
        region_lookup_dict['indian2']     = 'Bay of Bengal'
        region_lookup_dict['indian3']     = 'tropical Indian Ocean'
        region_lookup_dict['indian4']     = 'subtropical South Indian Ocean'
        region_lookup_dict['southern1']   = 'Subantarctic Zone'
        region_lookup_dict['southern2']   = 'Polar Front Zone'
        region_lookup_dict['southern3']   = 'Antarctic Zone'

        if return_lookup_dict == False:
            return region_ds        
        else:
            return region_ds, region_lookup_dict        

    def _get_region_mask(region):
        ds_oregs, reg_lookup_dict  = MiscDataGetter._get_ocean_regions()
        inverted_lookup_dict = {v: k for k, v in reg_lookup_dict.items()}
        reg_id = inverted_lookup_dict[region]
        region_mask = ds_oregs[reg_id]
        return region_mask

    def _standard_set_of_regions_locations():
        set_of_loc_reg = []
        set_of_loc_reg.append('Global Ocean')
        set_of_loc_reg.append([88,260]) # 'eastern tropical Pacific') #
        set_of_loc_reg.append([60,90]) # 'subtropical South Indian Ocean') #
        set_of_loc_reg.append('central Arctic')
        return set_of_loc_reg
    
    #def _pick_standard_set_of_example_locations():
    #    chosen_loc_or_reg = dict()
    #    chosen_loc_or_reg['Global Ocean'] = 'Global Ocean'
    #    chosen_loc_or_reg['East. Trop. Pac.'] = 'eastern tropical Pacific'#[88,260]
    #    chosen_loc_or_reg['Subtr. Indian Oce.'] = 'subtropical South Indian Ocean'#[60,90]
    #    chosen_loc_or_reg['Central Arctic'] = 'central Arctic'
    #    return chosen_loc_or_reg
        
