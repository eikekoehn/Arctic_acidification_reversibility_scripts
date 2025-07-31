"""
author: Eike E. Köhn
date: Jul 30, 2025
description: Collection of functions useful for plotting
"""

import xarray as xr
import numpy as np
import sys
sys.path.append('../00_modules/.')
from get_misc_data import MiscDataGetter
import splining_functions as Spliner

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


class Plotter:

    @staticmethod
    def _get_plot_dir(plotstring):
        if plotstring == 'standard':
            plot_dir = '../04_plots/00_drafting_stage'
        else:
            plot_dir = plotstring
        return plot_dir
    
    @staticmethod
    def plot_global_map(data_to_plot,set_of_loc_reg,vmin,vmax,nlevs,cmap,cticks,extend,clabel,title,agreement=None):

        # initialize figure
        fontsize=16
        plt.rcParams['font.size']=fontsize
        fig = plt.figure(figsize=(10,5.75)); ax = fig.add_subplot(1,1,1,projection=ccrs.Robinson())
        ax.set_global(); ax.gridlines(alpha=0.5)
    
        # prepare data to plot
        da_omask  = MiscDataGetter._get_ocean_mask()
        data_to_plot_masked = xr.where(da_omask,data_to_plot,np.NaN) # data_to_plot*da_omask
        lon_data = data_to_plot.lon; lat_data = data_to_plot.lat
        data_to_plot_cyclic, lon_data_cyclic = add_cyclic_point(data_to_plot_masked, coord=lon_data, axis=-1)
        lon2d, lat2d = np.meshgrid(lon_data_cyclic, lat_data)
    
        # make the plot
        c0 = ax.contourf(lon2d,lat2d,data_to_plot_cyclic,transform=ccrs.PlateCarree(),levels = np.linspace(vmin,vmax,nlevs),cmap = cmap, extend=extend)
        cbar = plt.colorbar(c0,ax=ax,fraction=0.045,label=clabel,orientation='horizontal',pad=0.02)
        cbar.ax.set_xticks(cticks)
        ax.add_feature(cartopy.feature.LAND, zorder=2, edgecolor='black',facecolor='#888888')
        ax.set_title(title,fontsize=fontsize+5)
        if agreement is not None:
            agreement_masked = xr.where(da_omask,agreement,np.NaN) # agreement.where(da_omask,np.NaN)
            agreement_cyclic, lon_data_cyclic = add_cyclic_point(agreement_masked, coord=lon_data, axis=-1)
            c1 = ax.contourf(lon2d, lat2d, agreement_cyclic,colors=[(0.5,0.5,0.5,0),(0.5,0.5,0.5,0)],levels=[-0.5,0.5,1.5],hatches=['///',None],transform=ccrs.PlateCarree()); # 'cmo.phase'
    
        # add markers
        for loc_reg in set_of_loc_reg:
            if loc_reg in ['Global Ocean','central Arctic']:
                continue
            # get the right string
            if isinstance(loc_reg,str):
                region_mask = MiscDataGetter._get_region_mask(loc_reg)
                ax.contour(region_mask.lon,region_mask.lat,region_mask,[0.5],colors='k',transform=ccrs.PlateCarree(),linewidths=4)
                ax.contour(region_mask.lon,region_mask.lat,region_mask,[0.5],colors='w',transform=ccrs.PlateCarree(),linewidths=2) 
            elif isinstance(loc_reg,list):
                loncho = lon_data[loc_reg[1]]
                latcho = lat_data[loc_reg[0]]
                ax.scatter(loncho,latcho,150,'k',marker='x',transform=ccrs.PlateCarree(),linewidth=5,zorder=10,clip_on=False)
                ax.scatter(loncho,latcho,100,'w',marker='x',transform=ccrs.PlateCarree(),linewidth=2,zorder=10,clip_on=False)
        return fig, ax 

    
    @staticmethod
    def plot_arctic_map(data_to_plot,set_of_loc_reg,vmin,vmax,nlevs,cmap,cticks,extend,clabel,title,agreement=None):
    
        # initialize figure
        fontsize=18
        plt.rcParams['font.size']=fontsize
        fig = plt.figure(figsize=(6,6))
        ax = fig.add_subplot(1,1,1,projection=ccrs.NorthPolarStereo())
        ax.set_global()
        ax.gridlines(alpha=0.75)
        ax.set_extent([-180, 180, 55.0, 90], crs=ccrs.PlateCarree())
        Plotter.add_circle_boundary(ax)
    
        # prepare data to plot
        da_omask  = MiscDataGetter._get_ocean_mask()
        data_to_plot_masked = xr.where(da_omask,data_to_plot,np.NaN) # data_to_plot*da_omask
        lon_data = data_to_plot.lon; lat_data = data_to_plot.lat
        data_to_plot_cyclic, lon_data_cyclic = add_cyclic_point(data_to_plot_masked, coord=lon_data, axis=-1)
        lon2d, lat2d = np.meshgrid(lon_data_cyclic, lat_data)
    
        # make the plot
        c0 = ax.pcolormesh(lon2d,lat2d,data_to_plot_cyclic,transform=ccrs.PlateCarree(),vmin=vmin,vmax=vmax,cmap = cmap)
        cbar = plt.colorbar(c0,ax=ax,fraction=0.045,label=clabel,pad=0.02,extend=extend)
        cbar.ax.set_yticks(cticks)
        ax.add_feature(cartopy.feature.LAND, zorder=2, edgecolor='black',facecolor='#888888')
        ax.set_title(title,fontsize=fontsize+5)
        if agreement is not None:
            agreement_masked = xr.where(da_omask,agreement,np.NaN) # agreement.where(da_omask,np.NaN)
            agreement_cyclic, lon_data_cyclic = add_cyclic_point(agreement_masked, coord=lon_data, axis=-1)
            c1 = ax.contourf(lon2d, lat2d, agreement_cyclic,colors=[(0.5,0.5,0.5,0),(0.5,0.5,0.5,0)],levels=[-0.5,0.5,1.5],hatches=['///',None],transform=ccrs.PlateCarree()); # 'cmo.phase'
    
        # add markers
        for loc_reg in set_of_loc_reg:
            if loc_reg == 'central Arctic':
                region_mask = MiscDataGetter._get_region_mask(loc_reg)
                ax.contour(region_mask.lon,region_mask.lat,region_mask,[0.5],colors='k',transform=ccrs.PlateCarree(),linewidths=4)
                ax.contour(region_mask.lon,region_mask.lat,region_mask,[0.5],colors='w',transform=ccrs.PlateCarree(),linewidths=2) 
            #elif isinstance(loc_reg,list):
            #    loncho = lon_data[loc_reg[1]]
            #    latcho = lat_data[loc_reg[0]]
            #    ax.scatter(loncho,latcho,150,'k',marker='x',transform=ccrs.PlateCarree(),linewidth=5,zorder=10,clip_on=False)
            #    ax.scatter(loncho,latcho,100,'w',marker='x',transform=ccrs.PlateCarree(),linewidth=2,zorder=10,clip_on=False)
        return fig, ax 

    
    @staticmethod
    def add_circle_boundary(ax):
        # Compute a circle in axes coordinates, which we can use as a boundary
        # for the map. We can pan/zoom as much as we like - the boundary will be
        # permanently circular.
        import matplotlib.path as mpath
        theta = np.linspace(0, 2*np.pi, 500)
        center, radius = [0.5, 0.5], 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        circle = mpath.Path(verts * radius + center)
        ax.set_boundary(circle, transform=ax.transAxes)

    
    @staticmethod
    def _plot_time_slice_averages(ts_mmm,ts_agreement,time_slice_type='anom_to_preindustrial_initial',vmin=0,vmax=100,cmap=plt.get_cmap('cmo.turbid_r',10),amin=-1,amax=1,amap=plt.get_cmap('cmo.amp_r',10),unit='-',include_region_mask=False):
    
        # get a sorted list of time slice keys
        sorted_time_slice_keys = sorted(ts_mmm.keys())
    
        # initialize an ax and all_cs array
        ax = np.empty((len(sorted_time_slice_keys)),dtype='object')
        all_cs = np.empty((len(sorted_time_slice_keys)),dtype='object')
        
        # set up the figure
        fig = plt.figure(figsize=(15,12))
        for sdx,ts_key in enumerate(sorted_time_slice_keys):
            if sdx == 0:
                xpos = 0.03
            else:
                xpos = 0.1+sdx*0.115
            ax[sdx] = fig.add_axes([xpos,0.4,0.11,0.2],projection=ccrs.NorthPolarStereo())
        
            # chose the data
            da_omask  = MiscDataGetter._get_ocean_mask()
            mmm_to_plot       = xr.where(da_omask,ts_mmm[ts_key],np.NaN)
            agreement_to_plot = xr.where(da_omask,ts_agreement[ts_key],np.NaN)
    
            # Choose the colormap
            if time_slice_type != 'absolute_values' and ts_key != '0_preindustrial':
                vmin_to_plot = amin
                vmax_to_plot = amax
                cmap_to_plot = amap
            else:
                vmin_to_plot = vmin
                vmax_to_plot = vmax
                cmap_to_plot = cmap            
    
            # Plot the data
            all_cs[sdx] = ax[sdx].pcolormesh(mmm_to_plot.lon,mmm_to_plot.lat,mmm_to_plot,vmin=vmin_to_plot,vmax=vmax_to_plot,cmap=cmap_to_plot,transform=ccrs.PlateCarree())
            if time_slice_type != 'absolute_values' and ts_key != '0_preindustrial':
                ax[sdx].contourf(agreement_to_plot.lon,agreement_to_plot.lat,agreement_to_plot,colors=[(0.5,0.5,0.5,0),(0.5,0.5,0.5,0)],levels=[-0.5,0.5,1.5],hatches=['///',None],transform=ccrs.PlateCarree()); # 'cmo.phase'
    
            ax[sdx].add_feature(cartopy.feature.LAND, zorder=2, edgecolor='None',facecolor='#888888')
            ax[sdx].set_global()
            ax[sdx].gridlines(alpha=0.3,linestyle='-',linewidth=0.5)
            ax[sdx].add_feature(cartopy.feature.LAND, zorder=1, edgecolor='black',facecolor='none',linewidth=0.75)
            ax[sdx].set_extent([-180, 180, 55.0, 90], crs=ccrs.PlateCarree())
            Plotter.add_circle_boundary(ax[sdx])
        cbax0 = fig.add_axes([0.15,0.44,0.02,0.12])
        cbar0 = plt.colorbar(all_cs[0],cax=cbax0,extend='both')
        cbax1 = fig.add_axes([0.91,0.44,0.02,0.12])
        cbar1 = plt.colorbar(all_cs[1],cax=cbax1,label=unit,extend='both')

        if include_region_mask is not False:
            if isinstance(include_region_mask,str):
                regions = [include_region_mask]
            elif isinstance(include_region_mask,list):
                regions = include_region_mask
            elif include_region_mask == True:
                regions = ['central Arctic'] # the default option
            # add mask
            for loc_reg in regions:
                region_mask = MiscDataGetter._get_region_mask(loc_reg)
                ax[0].contour(region_mask.lon,region_mask.lat,region_mask,[0.5],colors='k',transform=ccrs.PlateCarree(),linewidths=4)
                ax[0].contour(region_mask.lon,region_mask.lat,region_mask,[0.5],colors='w',transform=ccrs.PlateCarree(),linewidths=2) 
            
        plt.tight_layout()
        plt.subplots_adjust(right=0.9)
        plt.show()
        return fig, ax

    @staticmethod
    def _plot_variable_for_individual_models(run_params,variable_dict,da_name=None,vmin=0,vmax=100,cmap=plt.get_cmap('cmo.amp',10),unit='-'):
    
        # get number of models
        nkeys = len(variable_dict.keys())
        
        # Create figure and subplots with 1 x nkeys layout
        fig, ax = plt.subplots(1, nkeys, figsize=(3*nkeys, 5), subplot_kw={'projection': ccrs.NorthPolarStereo()})
    
        # loop over different runs
        for kdx,key in enumerate(variable_dict.keys()):
            da_omask  = MiscDataGetter._get_ocean_mask()
            data_to_plot = variable_dict[key][da_name] #* da_omask
            data_to_plot_masked = xr.where(da_omask,data_to_plot,np.NaN)
            c0 = ax[kdx].pcolormesh(data_to_plot.lon,data_to_plot.lat,data_to_plot_masked,transform=ccrs.PlateCarree(),vmin=vmin,vmax=vmax,cmap=cmap)
            ax[kdx].coastlines()
            ax[kdx].gridlines(alpha=0.75)
            ax[kdx].set_extent([-180, 180, 55.0, 90], ccrs.PlateCarree()) # # Focus on Arctic region
            ax[kdx].add_feature(cartopy.feature.LAND, zorder=2, edgecolor='black',facecolor='#888888')
            Plotter.add_circle_boundary(ax[kdx])
            ax[kdx].set_title(run_params[key].model)
        cbax = fig.add_axes([0.92,0.25,0.02,0.5])
        cbar = plt.colorbar(c0,cax=cbax,fraction=0.04,pad=0.01,extend='neither')
        cbar.ax.set_title(label=unit)
        plt.tight_layout()
        plt.subplots_adjust(right=0.91)  # Leave space for the suptitle
        #plt.savefig('plots_for_egu2025/map_hyst_area_norm_omegaa1_mocsy_indiv_models.png',dpi=300,transparent=True)
        plt.show()
        return fig, ax

    @staticmethod
    def _plot_regional_time_series_fancy(run_params,time_series_dict,region_of_choice,variable_to_analyze,unit_label,include_atmCO2=True):
    
        fontsize=15
        plt.rcParams['font.size']=fontsize
        fig = plt.figure(figsize=(11,2.2))
        ax = fig.add_axes([0.06, 0.01, 0.84, 0.72])  # left, bottom, width, height
        #if variable_to_analyze == 'dissic1' or variable_to_analyze == 'talk1': # convert from mol m-3 to mumol kg-1
        #    ax = fig.add_axes([0.1, 0.01, 0.84, 0.72])  # left, bottom, width, height
    
        all_timeseries = []
        for key in run_params.keys():
            timeseries = time_series_dict[region_of_choice][key]
            ax.plot(timeseries,color=run_params[key].runcol,zorder=3,linewidth=1,alpha=0.3)
            ax.plot(Spliner.fspline1D(timeseries,0.16),color=run_params[key].runcol,label=run_params[key].model,zorder=3,linewidth=2)
            all_timeseries.append(timeseries)
        ax.axvline(140,color='k',alpha=1,linewidth=0.0625)
        ax.axvline(280,color='k',alpha=1,linewidth=0.0625)        
        all_ts_da = xr.concat(all_timeseries,dim='keys')
        mmm = all_ts_da.mean(dim='keys')
        mmmin = all_ts_da.min(dim='keys')
        mmmax = all_ts_da.max(dim='keys')
        ax.plot(Spliner.fspline1D(mmm,0.16),color='k',zorder=4,linewidth=5,label='MMM')
        ax.fill_between(np.arange(np.size(mmmax)),Spliner.fspline1D(mmmax,0.16),Spliner.fspline1D(mmmin,0.16),color='#888888',zorder=0,alpha=0.15)#,linewidth=5,label='MMM')
        ax.set_xlabel('Year',labelpad=10,fontweight='bold')
        miny,maxy = ax.get_ylim()
        ax.set_ylim([miny,maxy])
        ax.set_xlim([0,340])
        ax.grid(linestyle='--',linewidth=0.25,axis='y')
        ax.fill_between([0,20],[miny]*2,[maxy]*2,alpha=0.081,color='C0')
        ax.fill_between([60,80],[miny]*2,[maxy]*2,alpha=0.081,color='C1')
        ax.fill_between([120,140],[miny]*2,[maxy]*2,alpha=0.081,color='C2')
        ax.fill_between([200,220],[miny]*2,[maxy]*2,alpha=0.081,color='C1')
        ax.fill_between([260,280],[miny]*2,[maxy]*2,alpha=0.081,color='C0')
        ax.fill_between([320,340],[miny]*2,[maxy]*2,alpha=0.081,color='C3')
        ax.set_xticks([0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340])
        ax.set_xticklabels([0,'','','','','','',140,'','','','','','',280,'','',340],fontweight='bold')
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top') 
        ax.tick_params(axis='x',labelsize=fontsize-2)
        if variable_to_analyze == 'tos':
            ax.legend(loc='lower left',fontsize=fontsize-3.5,framealpha=0,bbox_to_anchor=(-0.01,0.25),ncols=2,columnspacing=.75,handlelength=1.25,labelspacing=0.3,handletextpad=0.4)  
        ax.set_ylabel(f'{unit_label}')
    
        if include_atmCO2 == True:
            ds_atmCO2 = MiscDataGetter._get_atmospheric_CO2(run_params)
            dummy_key = list(run_params.keys())[0]
            ax2 = ax.twinx()
            ax2.plot(ds_atmCO2[dummy_key],linewidth=2,color='#555555',linestyle='--')#.plot()
            ax2.set_ylim([240,1200])#.plot()
            ax2.set_yticks([500,1000])#.plot()
            ax2.set_ylabel('atm. CO$_2$\n(ppm)',fontsize=fontsize-2)#,color='w')
            ax2.tick_params(axis='both',labelsize=fontsize-2)#,color='w')
            ax2.set_xticks([0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340])
            ax2.set_xticklabels([0,'','','','','','',140,'','','','','','',280,'','',340],fontweight='bold')
            ax2.xaxis.set_ticks_position('top') # the rest is the same
            ax2.xaxis.set_label_position('top') 
            ax2.spines[['bottom']].set_visible(False)
            
        #plt.savefig(f'plots_for_egu2025/{varia}_annual_Central_Arctic_timeseries_new.png',dpi=250,transparent=True)
        if include_atmCO2 == True:
            return fig,ax,ax2
        else:
            return fig,ax
