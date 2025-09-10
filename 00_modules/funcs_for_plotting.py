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
from funcs_for_multimodel_analysis import MMFuncs

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
        fig.subplots_adjust(right=0.85)  # Leave space on the right for colorbar
    
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
            if time_slice_type == 'absolute_value' or ts_key == '0_preindustrial' or ts_key == '0_signed_hysteresis_area':
                vmin_to_plot = vmin
                vmax_to_plot = vmax
                cmap_to_plot = cmap      
            else:
                vmin_to_plot = amin
                vmax_to_plot = amax
                cmap_to_plot = amap
          
            # Plot the data
            all_cs[sdx] = ax[sdx].pcolormesh(mmm_to_plot.lon,mmm_to_plot.lat,mmm_to_plot,vmin=vmin_to_plot,vmax=vmax_to_plot,cmap=cmap_to_plot,transform=ccrs.PlateCarree())
            if time_slice_type != 'absolute_value' and ts_key != '0_preindustrial':
                ax[sdx].contourf(agreement_to_plot.lon,agreement_to_plot.lat,agreement_to_plot,colors=[(0.5,0.5,0.5,0),(0.5,0.5,0.5,0)],levels=[-0.5,0.5,1.5],hatches=['///',None],transform=ccrs.PlateCarree()); # 'cmo.phase'
    
            ax[sdx].add_feature(cartopy.feature.LAND, zorder=2, edgecolor='None',facecolor='#888888')
            ax[sdx].set_global()
            ax[sdx].gridlines(alpha=0.3,linestyle='-',linewidth=0.5)
            ax[sdx].add_feature(cartopy.feature.LAND, zorder=1, edgecolor='black',facecolor='none',linewidth=0.75)
            ax[sdx].set_extent([-180, 180, 55.0, 90], crs=ccrs.PlateCarree())
            Plotter.add_circle_boundary(ax[sdx])
        cbax0 = fig.add_axes([0.144,0.44,0.02,0.12])
        cbar0 = plt.colorbar(all_cs[0],cax=cbax0,extend='both')
        cbax1 = fig.add_axes([0.904,0.44,0.02,0.12])
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
            
        #plt.tight_layout()
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
            if nkeys == 1:
                axi = ax
            else:
                axi = ax[kdx]
            c0 = axi.pcolormesh(data_to_plot.lon,data_to_plot.lat,data_to_plot_masked,transform=ccrs.PlateCarree(),vmin=vmin,vmax=vmax,cmap=cmap)
            axi.coastlines()
            axi.gridlines(alpha=0.75)
            axi.set_extent([-180, 180, 55.0, 90], ccrs.PlateCarree()) # # Focus on Arctic region
            axi.add_feature(cartopy.feature.LAND, zorder=2, edgecolor='black',facecolor='#888888')
            Plotter.add_circle_boundary(axi)
            axi.set_title(run_params[key].model)
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

        import splining_functions as Spliner

        fontsize=15
        plt.rcParams['font.size']=fontsize
        fig = plt.figure(figsize=(11,2.2))
        if include_atmCO2 == True:
            ax = fig.add_axes([0.06, 0.01, 0.84, 0.72])  # left, bottom, width, height
        else:
            ax = fig.add_axes([0.12, 0.01, 0.84, 0.72])  # left, bottom, width, height

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
        ax.axvline(140,color='k',alpha=1,linewidth=0.0625)
        ax.axvline(280,color='k',alpha=1,linewidth=0.0625)
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

    @staticmethod
    def _plot_regional_time_series_without_smoothing(run_params,time_series_dict,region_of_choice,unit_label,ylims=[0,100],panellabel='a)'):

        # Get the dataset for the region of choice
        if region_of_choice != '_no_region_':
            ts_ds = time_series_dict[region_of_choice]
        else:
            ts_ds = time_series_dict
            
        # figure setup
        fontsize=15
        plt.rcParams['font.size']=15

        # produce the figure
        fig = plt.figure(figsize=(9,4))
        ax = fig.add_axes([0.11,0.15,0.85,0.7])
        for key in run_params.keys(): 
            data_to_plot = ts_ds[key] # get the data 
            ax.plot(data_to_plot,color=run_params[key].runcol,label=run_params[key].model,linewidth=2,alpha=0.75)
        ts_mmm, _ = MMFuncs._calc_multimodel_mean_and_agreement(ts_ds)
        data_to_plot_mmm = ts_mmm # get the multi-model mean 
        ax.plot(data_to_plot_mmm,label='MMM',linewidth=5,color='k')
        ax.axvline(140,linestyle='-',color='#555555')
        ax.axvline(280,linestyle='-',color='#555555')
        ax.set_ylabel(unit_label)
        ax.set_xlabel('Year')
        ax.set_xlim([0,340])
        ax.legend(loc='lower left',bbox_to_anchor=(-.02,.99),ncols=5,columnspacing=1.1,handletextpad=0.2,handlelength=1,edgecolor='None',fontsize=fontsize-2,facecolor=None)
        ax.set_xticks([0,70,140,210,280,340])
        ax.set_ylim(ylims)
        #ax.set_yticks([0,50,100,150,200,250])
        #ax.set_yticklabels([0,50,100,150,200,''])
        ax.grid(alpha=0.25)
        ax.text(0.02,0.1,panellabel,ha='left',va='top',transform=ax.transAxes)
        miny,maxy = ax.get_ylim()
        ax.set_ylim([miny,maxy])
        ax.fill_between([0,20],[miny]*2,[maxy]*2,alpha=0.15,color='C0') # alpha=0.081
        ax.fill_between([60,80],[miny]*2,[maxy]*2,alpha=0.15,color='C1')
        ax.fill_between([200,220],[miny]*2,[maxy]*2,alpha=0.15,color='C1')
        ax.fill_between([260,280],[miny]*2,[maxy]*2,alpha=0.15,color='C0')
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        #ax.fill_between([120,140],[miny]*2,[maxy]*2,alpha=0.081,color='C2')
        #ax.fill_between([320,340],[miny]*2,[maxy]*2,alpha=0.081,color='C3')
        #plt.savefig(f'plots_for_egu2025/post_EGU/time_series_sCT_{reg}_vs_time.png',dpi=300,transparent=True)
        ax.plot()
        return fig, ax
        
        
    @staticmethod
    def _plot_regional_time_series_rel_to_start(run_params,time_series_dict,region_of_choice,unit_label,ylims=[0,100]):
    
        # Get the dataset for the region of choice
        ts_ds = time_series_dict[region_of_choice]
    
        # figure setup
        fontsize=15
        plt.rcParams['font.size']=15

        # produce the figure
        fig = plt.figure(figsize=(9,4))
        ax = fig.add_axes([0.11,0.15,0.85,0.7])
        for key in run_params.keys(): 
            data_to_plot = ts_ds[key] - ts_ds[key].isel(year=0) # plot the data relative to the start (t=0)
            ax.plot(data_to_plot,color=run_params[key].runcol,label=run_params[key].model,linewidth=2,alpha=0.75)
        ts_mmm, _ = MMFuncs._calc_multimodel_mean_and_agreement(ts_ds)
        data_to_plot_mmm = ts_mmm - ts_mmm.isel(year=0) # plot the data relative to the start (t=0)
        ax.plot(data_to_plot_mmm,label='MMM',linewidth=5,color='k')
        ax.axvline(140,linestyle='-',color='#555555')
        ax.axvline(280,linestyle='-',color='#555555')
        ax.set_ylabel(unit_label)
        ax.set_xlabel('Year')
        ax.set_xlim([0,340])
        ax.legend(loc='lower left',bbox_to_anchor=(-.02,.99),ncols=5,columnspacing=1.1,handletextpad=0.2,handlelength=1,edgecolor='None',fontsize=fontsize-2,facecolor=None)
        ax.set_xticks([0,70,140,210,280,340])
        ax.set_ylim(ylims)
        ax.set_yticks([0,50,100,150,200,250])
        ax.set_yticklabels([0,50,100,150,200,''])
        ax.grid(alpha=0.25)
        ax.text(0.02,0.1,'a)',ha='left',va='top',transform=ax.transAxes)
        miny,maxy = ax.get_ylim()
        ax.set_ylim([miny,maxy])
        ax.fill_between([0,20],[miny]*2,[maxy]*2,alpha=0.15,color='C0') # alpha=0.081
        ax.fill_between([60,80],[miny]*2,[maxy]*2,alpha=0.15,color='C1')
        ax.fill_between([200,220],[miny]*2,[maxy]*2,alpha=0.15,color='C1')
        ax.fill_between([260,280],[miny]*2,[maxy]*2,alpha=0.15,color='C0')
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        #ax.fill_between([120,140],[miny]*2,[maxy]*2,alpha=0.081,color='C2')
        #ax.fill_between([320,340],[miny]*2,[maxy]*2,alpha=0.081,color='C3')
        #plt.savefig(f'plots_for_egu2025/post_EGU/time_series_sCT_{reg}_vs_time.png',dpi=300,transparent=True)
        ax.plot()
        return fig, ax

    
    @staticmethod
    def _plot_regional_time_series_rel_to_start_vs_atmCO2(run_params,time_series_dict,region_of_choice,unit_label,ylims=[0,100]):

        import splining_functions as Spliner
        
        # Get atmospheric CO2 levels
        ds_atmCO2 = MiscDataGetter._get_atmospheric_CO2(run_params)
        
        # Get the dataset for the region of choice
        ts_ds = time_series_dict[region_of_choice]
    
        # figure setup
        fontsize=15
        plt.rcParams['font.size']=15

        # produce the figure
        fig = plt.figure(figsize=(4,4))
        ax = fig.add_axes([0.225,0.15,0.7,0.7])
        for key in run_params.keys(): 
            co2_to_plot = ds_atmCO2[key]
            data_to_plot = ts_ds[key] - ts_ds[key].isel(year=0) # plot the data relative to the start (t=0)
            data_to_plot_smooth = Spliner.fspline1D(data_to_plot,0.06)
            ax.plot(co2_to_plot.isel(year=slice(0,140)),data_to_plot_smooth[:140],color=run_params[key].runcol,label=run_params[key].model,linewidth=2,alpha=0.75)
            ax.plot(co2_to_plot.isel(year=slice(140,280)),data_to_plot_smooth[140:280],color=run_params[key].runcol,label=run_params[key].model,linewidth=2,alpha=0.75,linestyle='--')

        ts_mmm, _ = MMFuncs._calc_multimodel_mean_and_agreement(ts_ds)
        data_to_plot_mmm = ts_mmm - ts_mmm.isel(year=0) # plot the data relative to the start (t=0)
        data_to_plot_mmm_smooth = Spliner.fspline1D(data_to_plot_mmm,0.06)
        ax.plot(co2_to_plot.isel(year=slice(0,140)),data_to_plot_mmm_smooth[:140],label='MMM',linewidth=5,color='k')
        ax.plot(co2_to_plot.isel(year=slice(140,280)),data_to_plot_mmm_smooth[140:280],label='MMM',linewidth=5,color='k',linestyle='--')
        ax.set_ylabel(unit_label)
        ax.set_xlabel('atm. CO$_2$ (ppm)')
        ax.set_xlim([270,1200])
        #ax.legend(loc='lower left',bbox_to_anchor=(-.02,.99),ncols=5,columnspacing=1.1,handletextpad=0.2,handlelength=1,edgecolor='None',fontsize=fontsize-2,facecolor=None)
        ax.set_xticks([500,750,1000])
        ax.set_ylim(ylims)
        ax.set_yticks([0,50,100,150,200,250])
        ax.set_yticklabels([0,50,100,150,200,250])
        ax.grid(alpha=0.25)
        ax.text(0.05,0.95,'b)',ha='left',va='top',transform=ax.transAxes)
        miny,maxy = ax.get_ylim()
        ax.set_ylim([miny,maxy])
        ax.fill_between([co2_to_plot.isel(year=0),co2_to_plot.isel(year=20)],[miny]*2,[maxy]*2,alpha=0.15,color='C0') # alpha=0.081
        ax.fill_between([co2_to_plot.isel(year=60),co2_to_plot.isel(year=80)],[miny]*2,[maxy]*2,alpha=0.15,color='C1')
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        #plt.savefig(f'plots_for_egu2025/post_EGU/time_series_sCT_{reg}_vs_time.png',dpi=300,transparent=True)
        ax.plot()
        
        return fig, ax 

    

    def _plot_time_series_of_regional_hysteresis_decomposition(run_params, variable_to_analyze, loc_reg, model_ds, taylor_ds):
        
        # plot setup
        conts_for_plotting = ['t','s','alk','alk_dilution','alk_bgc','dic','dic_dilution','dic_bgc','alk_dic','dilution_terms','bgc_terms','taylor_sum']
        line_labels = ['T','S','A$_T$','A$_{T,fw}$','A$_{T,bgc}$','C$_T$','C$_{T,fw}$','C$_{T,bgc}$','A$_T$ + C$_T$','A$_{T,fw}$ + C$_{T,fw}$','A$_{T,bgc}$ + C$_{T,bgc}$',r'$\Sigma_\text{Taylor}$']
        tcs =  plt.cm.tab20c( (4./3*np.arange(20*3/4)).astype(int) )
        line_colors = [tcs[3],tcs[0],tcs[6],tcs[6],tcs[6],tcs[9],tcs[9],tcs[9],tcs[13],tcs[13],tcs[13],'k']
        linestyles = ['-','-','-',':','--','-',':','--','-',':','--','-']
        if variable_to_analyze == 'hplus':
            varia2 = r'[$H^+$]'
            unit = r'nmol kg$^{-1}$'
            #ylims = [-9,9]
            #hlines = [-7.5,-5,-2.5,2.5,5,7.5]
        elif variable_to_analyze == 'omegaa':
            varia2 = r'$\Omega_\text{Arag.}$'
            unit = '-'
            #ylims = [-.3,.3]
            #hlines = [-.2,-.1,.1,.2]
        
        fontsize = 14
        plt.rcParams['font.size']=fontsize
        fig,ax = plt.subplots(figsize=(12,4))
        # plot the contributions
        for i, cont in enumerate(conts_for_plotting):
            meanval,_ = MMFuncs._calc_multimodel_mean_and_agreement(taylor_ds[cont][loc_reg])
            ax.plot(meanval,color=line_colors[i],linewidth=4,label=line_labels[i],linestyle=linestyles[i])
        # plot the direct model output
        meanmodel,_ = MMFuncs._calc_multimodel_mean_and_agreement(model_ds[loc_reg])
        meanmodel_delta = meanmodel - meanmodel.isel(year=0)
        ax.plot(meanmodel_delta,color='r',label=f'model {varia2}',zorder=10)
    
        ax.set_xlim([0,340])
        ax.axvline([139.5],linestyle='-',color='#555555',alpha=1,zorder=0,linewidth=1)
        ax.axvline([279.5],linestyle='-',color='#555555',alpha=1,zorder=0,linewidth=1)
        ax.axhline(0,color='k',linestyle=':')
        ax.spines[['right', 'top']].set_visible(False)
        ax.set_title(f'a) {loc_reg} {varia2} decomposition',loc='left')
        ax.set_xlabel('Year')
        ax.set_ylabel(f'Cumulative changes in {unit}')
        if variable_to_analyze == 'hplus':
            csp = 0.5
        elif variable_to_analyze == 'omegaa':
            csp = 24
        #ax.legend(loc='lower left',ncols=2,fontsize=10,framealpha=0,columnspacing=csp)
        ax.legend(loc='lower left',bbox_to_anchor=(1.01,-0.09),ncols=1,fontsize=10,framealpha=0,columnspacing=csp,handlelength=4)
        ax.set_xlim([0,340])
        ax.grid(linestyle='--',linewidth=0.25,axis='y')
        ylims = ax.get_ylim()
        miny = ylims[0]
        maxy = ylims[1]
        ax.fill_between(np.array([0,20])-0.5,[miny]*2,[maxy]*2,alpha=0.081,color='C0')
        ax.fill_between(np.array([60,80])-0.5,[miny]*2,[maxy]*2,alpha=0.081,color='C1')
        ax.fill_between(np.array([120,140])-0.5,[miny]*2,[maxy]*2,alpha=0.081,color='C2')
        ax.fill_between(np.array([200,220])-0.5,[miny]*2,[maxy]*2,alpha=0.081,color='C1')
        ax.fill_between(np.array([260,280])-0.5,[miny]*2,[maxy]*2,alpha=0.081,color='C0')
        ax.fill_between(np.array([320,340])-0.5,[miny]*2,[maxy]*2,alpha=0.081,color='C3')
        ax.set_xticks(np.array([0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340])-0.5)
        ax.set_xticklabels([0,'','',60,'','','',140,'','','',220,'','',280,'','',340])#,fontweight='bold')
        ax.set_ylim(ylims)
        plt.tight_layout()
        plt.subplots_adjust(left=0.15)
        plt.show()
        return fig, ax 

    def _plot_bars_of_regional_hysteresis_decomposition(run_params, variable_to_analyze, loc_reg, hyst_model, hyst_taylor_contributions):
    
        # === Setup ===
        conts = ['taylor_sum', 't', 's', 'alk', 'alk_dilution', 'alk_bgc', 'dic', 'dic_dilution', 'dic_bgc', 'alk_dic', 'dilution_terms', 'bgc_terms']
        labels = [r'$\Sigma_\text{Taylor}$', 'T', 'S', 'A$_T$', 'A$_{T,fw}$', 'A$_{T,bgc}$', 'C$_T$', 'C$_{T,fw}$', 'C$_{T,bgc}$',
                  'A$_T$ + C$_T$', 'A$_{T,fw}$ + C$_{T,fw}$', 'A$_{T,bgc}$ + C$_{T,bgc}$']
        heights = [0.5, 0.5, 0.5, 0.5, 0.4, 0.4, 0.5, 0.4, 0.4, 0.5, 0.4, 0.4]
        ypos = -1 * np.array([ -1, 0, 1, 2, 2.5, 3, 4, 4.5, 5, 6, 6.5, 7 ])
        tcs =  plt.cm.tab20c( (4./3*np.arange(20*3/4)).astype(int) )
        colors = ['k',tcs[3],tcs[0],tcs[6],tcs[7],tcs[8],tcs[9],tcs[10],tcs[11],tcs[12],tcs[13],tcs[14]]# ['k'] + list(plt.cm.tab20c((4./3*np.arange(15)).astype(int))[:11])
    
        var_map = {
            'hplus': (r'[$H^+$]', r'nmol kg$^{-1}$', [-25, 25], [-7.5, -5, -2.5, 2.5, 5, 7.5]),
            'omegaa': (r'$\Omega_\text{Arag.}$', '-', [-.5, .5], [-.2, -.1, .1, .2])
        }
        varia2, unit, xlims, hlines = var_map[variable_to_analyze]
        hyst_metric = 'signed_hysteresis_area'
    
        # === Plot ===
        fig, ax = plt.subplots(1, 3, figsize=(12, 6), sharey=True, width_ratios=[1, 5, 1])
    
        for i, cont in enumerate(conts):
            meanval = hyst_taylor_contributions[cont][loc_reg].sel(h_definition=hyst_metric).mean(dim='run_keys')
            ax[1].barh(ypos[i], meanval, height=heights[i], color=colors[i], edgecolor='None', zorder=1)
            for axi in ax:
                for key, param in run_params.items():
                    val = hyst_taylor_contributions[cont][loc_reg].sel(h_definition=hyst_metric, run_keys=key)
                    axi.scatter(val, ypos[i], 50, color=param.runcol, clip_on=True)
    
        # === Model hysteresis ===
        model_y = 2
        modelvals = hyst_model[loc_reg].sel(h_definition=hyst_metric)
        modelmean = modelvals.mean(dim='run_keys')
        ax[1].barh(model_y, modelmean, height=0.5, color='None', edgecolor='r', linewidth=1, zorder=1)
        for axi in ax:
            for key, param in run_params.items():
                axi.scatter(modelvals.sel(run_keys=key), model_y, 50, color=param.runcol, clip_on=True, label=param.model)
    
        # === Beautify ===
        for axi in ax:
            axi.axvline(0, color='k')
            axi.set_yticks([model_y] + list(ypos))
            axi.set_yticklabels([f'model {varia2}'] + labels)
            axi.set_xlabel(f'$H_s$ ({unit})')
            axi.set_xlim(xlims)
            axi.grid(alpha=0.5, zorder=0, linewidth=0.5)
            axi.spines[['right', 'top']].set_visible(False)
    
        ax[0].set_title(f'b) {loc_reg} $H_s$ decomposition for {varia2}', loc='left')
        ax[1].tick_params(left=False, labelleft=False)
        ax[-1].tick_params(left=False, labelleft=False)
        ax[0].set_xlabel('')
        ax[-1].set_xlabel('')
        ax[0].set_title('')
        ax[-1].set_title('')
        ax[1].set_ylim([-7.5, 2.375])
    
        # Custom axis limits for ph1 or omegaa
        if variable_to_analyze == 'hplus':
            xticks = [[-24, -18, -12], [-6, 0, 6], [12, 18, 24]]
            xlims = [[-25.5, -12], [-12, 12], [12, 25.5]]
        else:
            xticks = [[-.5,-.4], [-.3,-.2,-.1, 0,.1,.2, .3], [.4,.5]]
            xlims = [[-0.52, -0.3], [-0.3, 0.3], [0.3, 0.52]]
    
        for i in range(3):
            ax[i].set_xticks(xticks[i])
            ax[i].set_xlim(xlims[i])
    
        # === Legend ===
        legend_ncols = 1 if variable_to_analyze == 'omegaa' else 2
        ax[-1].legend(ncols=legend_ncols, loc='lower left', bbox_to_anchor=(-6, 0), fontsize=12, handletextpad=0.2, columnspacing=0.2, framealpha=1)
    
        plt.tight_layout()
        plt.subplots_adjust(wspace=0, top=0.92, left=0.15, right=0.9)
        return fig, ax

