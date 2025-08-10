import xarray as xr
import matplotlib.pyplot as plt
import sys
sys.path.append('../00_modules/.')
from set_params import Params
from get_model_datasets import ModelDataGetter
from funcs_for_conversions import Converter
from funcs_for_multimodel_analysis import MMFuncs

class TaylorFuncs:

    def _interpolate_to_midpoint_in_time(ds,temporal_resolution):
        int_ds = xr.Dataset()
        for key in ds.keys():
            if isinstance(ds[key],str):           
                with xr.open_dataset(ds[key]) as da:
                    slice0_da = da[temporal_resolution].isel(year=slice(0,-1)).load()
                    slice1_da = da[temporal_resolution].isel(year=slice(1,None)).load()
            else:
                slice0_da = ds[key][temporal_resolution].isel(year=slice(0,-1))
                slice1_da = ds[key][temporal_resolution].isel(year=slice(1,None))                
            slice0 = slice0_da.values
            slice1 = slice1_da.values
            interpolated_slice = (slice0+slice1)/2
            int_ds[key] = xr.DataArray(interpolated_slice,dims=slice1_da.dims,coords=slice1_da.coords)
        return int_ds

    def _multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,sensitivity_dict,driver_deltas_dict,sensitivity_adjustment_factor_dict=None):
        cumsum_mult_sens_delta = xr.Dataset()
        for key in run_params.keys():
            sensitivity = sensitivity_dict[key]
            delta = driver_deltas_dict[key]
            # check if additional term is included in the contribution to adjust the sensitivity term
            if sensitivity_adjustment_factor_dict is not None:
                sensitivity_adjustment_factor = sensitivity_adjustment_factor_dict[key]
                adjusted_sensitivity = sensitivity_adjustment_factor * sensitivity
            else:
                adjusted_sensitivity = sensitivity
            # multiply sensitivity and delta
            mult_sens_delta = adjusted_sensitivity * delta
            # integrate in time
            cumsum_mult_sens_delta[key] = mult_sens_delta.cumsum(dim='year')
        return cumsum_mult_sens_delta
        
    def _perform_taylor_decomposition(run_params,variable_to_analyze,depth_to_analyze,temporal_resolution):
        
        # set the standard salinity s0
        misc_params = Params.additional_misc_params() 
        s0 = misc_params.standard_salinity

        # initialize the final dictionary
        taylor_terms_dict = dict()

        # compute driver deltas for T, S, DIC, Alk
        driver_deltas_dict = dict()
        for driver_var in ['thetao','so','dissic','talk']:
            path_dum = ModelDataGetter._identify_path_strings(run_params,driver_var,depth_to_analyze)
            driver_deltas = xr.Dataset()
            for key in run_params.keys():
                with xr.open_dataset(path_dum[key]) as driver_ds:
                    driver_deltas[key] = driver_ds[temporal_resolution].diff(dim='year').load()
            driver_deltas_dict[driver_var] = driver_deltas

        # compute the salinity normalized DIC and Alk deltas
        for driver_var in ['dissic','talk']:
            path_dum = ModelDataGetter._identify_path_strings(run_params,driver_var,depth_to_analyze)
            # first normalize by salinity
            ds_norm_dict, driver_var_normalized = Converter._normalize_with_salinity(run_params,path_dum,temporal_resolution,depth_to_analyze,driver_var,standard_salinity=s0)
            driver_deltas = xr.Dataset()
            for key in run_params.keys():
                # now calculate the delta for each run
                driver_deltas[key] = ds_norm_dict[key][temporal_resolution].diff(dim='year').load()
            driver_deltas_dict[driver_var_normalized] = driver_deltas        

        # Now load and select the sensitivities, and interpolate them to in-between time steps
        sens_dict = dict()
        for sensvar in ['tem','sal','dic','alk']:
            sens_dict[sensvar] = xr.Dataset()
            if variable_to_analyze == 'hplus':
                sensvar_to_load = f'dh_d{sensvar}'
            else:
                sensvar_to_load = f'd{variable_to_analyze}_d{sensvar}'
            sens_paths = ModelDataGetter._identify_path_strings(run_params,sensvar_to_load,None)
            sens_dict[sensvar] = TaylorFuncs._interpolate_to_midpoint_in_time(sens_paths,temporal_resolution)

        # Now load and interpolate the salinity field as well as the dissic and alk field, divided by salinity (for the freshwater terms)
        interpolated_div_sal_dict = dict()
        for driver_var in ['dissic','talk']:
            path_dum = ModelDataGetter._identify_path_strings(run_params,driver_var,depth_to_analyze)
            # Here, I use the "_normalize_with_salinity" routine, but i put standard salinity to 1, so that effectively, the concentrations are just divided by the salinity (and then multiplied by 1)
            div_sal_orig_time, _ = Converter._normalize_with_salinity(run_params,path_dum,temporal_resolution,depth_to_analyze,driver_var,standard_salinity=1)
            interpolated_div_sal_dict[driver_var] = TaylorFuncs._interpolate_to_midpoint_in_time(div_sal_orig_time,temporal_resolution)
        # now add the interpolated salinity divided by the standard salinity s0
        path_dum = ModelDataGetter._identify_path_strings(run_params,'so',depth_to_analyze)
        interpolated_div_sal_dict['so'] = TaylorFuncs._interpolate_to_midpoint_in_time(path_dum,temporal_resolution)/s0

        # Now put everything together to construct the terms, i.e. compute the contributions
        contribution_terms = dict()
        contribution_terms['t'] = TaylorFuncs._multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,
                                                                                                     sens_dict['tem'],
                                                                                                     driver_deltas_dict['thetao'])
        contribution_terms['s'] = TaylorFuncs._multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,
                                                                                                     sens_dict['sal'],
                                                                                                     driver_deltas_dict['so'])
        contribution_terms['dic'] = TaylorFuncs._multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,
                                                                                                     sens_dict['dic'],
                                                                                                     driver_deltas_dict['dissic'])
        contribution_terms['alk'] = TaylorFuncs._multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,
                                                                                                     sens_dict['alk'],
                                                                                                     driver_deltas_dict['talk'])
        contribution_terms['dic_dilution'] = TaylorFuncs._multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,
                                                                                                     sens_dict['dic'],
                                                                                                     driver_deltas_dict['so'],
                                                                                                     sensitivity_adjustment_factor_dict = interpolated_div_sal_dict['dissic'])
        contribution_terms['alk_dilution'] = TaylorFuncs._multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,
                                                                                                     sens_dict['alk'],
                                                                                                     driver_deltas_dict['so'],
                                                                                                     sensitivity_adjustment_factor_dict = interpolated_div_sal_dict['talk'])        
        contribution_terms['dic_bgc'] = TaylorFuncs._multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,
                                                                                                     sens_dict['dic'],
                                                                                                     driver_deltas_dict['dissic_salinity_normalized'],
                                                                                                     sensitivity_adjustment_factor_dict = interpolated_div_sal_dict['so'])
        contribution_terms['alk_bgc'] = TaylorFuncs._multiply_sensitivity_and_deltas_and_integrate_in_time(run_params,
                                                                                                     sens_dict['alk'],
                                                                                                     driver_deltas_dict['talk_salinity_normalized'],
                                                                                                     sensitivity_adjustment_factor_dict = interpolated_div_sal_dict['so'])     

        contribution_terms['alk_dic'] = contribution_terms['dic'] + contribution_terms['alk']
        contribution_terms['dilution_terms'] = contribution_terms['dic_dilution'] + contribution_terms['alk_dilution']
        contribution_terms['bgc_terms'] = contribution_terms['dic_bgc'] + contribution_terms['alk_bgc']
        contribution_terms['taylor_sum'] = contribution_terms['t'] + contribution_terms['s'] + contribution_terms['dic'] + contribution_terms['alk']
        contribution_terms['fwtaylor_sum'] = contribution_terms['t'] + contribution_terms['s'] + contribution_terms['dic_bgc'] + contribution_terms['alk_bgc'] + contribution_terms['dic_dilution'] + contribution_terms['alk_dilution']
        
        # Expand the contributions to include an initial 0 at year 1850
        for contributor in ['t','s','dic','alk','alk_bgc','dic_bgc','alk_dilution','dic_dilution','bgc_terms','dilution_terms','taylor_sum','fwtaylor_sum']:
            dummy_term = contribution_terms[contributor]
            dummy_data0 = dummy_term.isel(year=0)*0
            dummy_data0['year'] = dummy_data0['year']-1 # year 1850
            contribution_terms[contributor] = xr.concat([dummy_data0,dummy_term],'year')     

        return contribution_terms


    def _plot_regional_timeseries_for_all_contributions(run_params, regional_time_series, region, variable_to_analyze):
        """
        Plots regional time series for all contributions to changes in Ω_Arag over time.
    
        Parameters:
            regional_time_series (dict): Nested dict of time series data per contribution per region.
            region (str): Name of the region to plot.
            run_params (dict): Dictionary with run metadata (e.g. color and model name).
        """
        # Contribution label strings (LaTeX formatted)
        contribution_labels = {
            't': r'T: $\left( \frac{\partial \Omega_\text{Arag.}}{\partial T} \right) \Delta T $',
            's': r'S: $\left( \frac{\partial \Omega_\text{Arag.}}{\partial S} \right) \Delta S $',
            'alk': r'A$_T$: $\left( \frac{\partial \Omega_\text{Arag.}}{\partial A_T} \right) \Delta A_T $',
            'dic': r'C$_T$: $\left( \frac{\partial \Omega_\text{Arag.}}{\partial C_T} \right) \Delta C_T $',
            'alk_bgc': r'A$_{T,\text{bgc}}$: $\left( \frac{S}{S_0} \frac{\partial \Omega_\text{Arag.}}{\partial A_T} \right) \Delta sA_T $',
            'dic_bgc': r'C$_{T,\text{bgc}}$: $\left( \frac{S}{S_0} \frac{\partial \Omega_\text{Arag.}}{\partial C_T} \right) \Delta sC_T $',
            'alk_dilution': r'A$_{T,\text{fw}}$: $\left( \frac{A_T}{S} \frac{\partial \Omega_\text{Arag.}}{\partial A_T} \right) \Delta S $',
            'dic_dilution': r'C$_{T,\text{fw}}$: $\left( \frac{C_T}{S} \frac{\partial \Omega_\text{Arag.}}{\partial C_T} \right) \Delta S $'
        }
    
        panel_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        contributions = list(contribution_labels.keys())
    
        # Plot configuration
        fontsize = 16
        plt.rcParams['font.size'] = fontsize
        fig, ax = plt.subplots(2, 4, figsize=(14, 10), sharex=True, sharey=True)
    
        for idx, contribution in enumerate(contributions):
            row = idx // 4
            col = idx % 4
            axis = ax[row, col]
    
            # Collect all models' time series
            all_series = []
            for key, rp in run_params.items():
                ts = regional_time_series[contribution][region][key]
                all_series.append(ts)
                axis.plot(ts, color=rp.runcol, alpha=0.75,
                          label=rp.model if contribution == 't' else None)
    
            # Plot multi-model mean
            mean_series = xr.concat(all_series, dim='models').mean(dim='models')
            axis.plot(mean_series, color='k', linewidth=5,
                      label='MMM' if contribution == 't' else None)
    
            axis.set_title(contribution_labels[contribution])
    
        # Add common formatting
        for idx, axis in enumerate(ax.flatten()):
            axis.set_xlim([0, 340])
            axis.axvline(140, linestyle='--', color='#777777')
            axis.axvline(280, linestyle='--', color='#777777')
            axis.axhline(0, linestyle='--', color='#777777')
            axis.text(0.02, 0.98, f'{panel_labels[idx]})',
                      ha='left', va='top', transform=axis.transAxes)
    
        # Axis labels
        if variable_to_analyze in ['omegaa','omegaa1']:
            ax[0, 0].set_ylabel(r'$\Delta \Omega_\text{Arag.}$')
            ax[1, 0].set_ylabel(r'$\Delta \Omega_\text{Arag.}$')
        else:
            ax[0,0].set_ylabel(r'$\Delta [H^+]$ in nmol/kg')
            ax[1,0].set_ylabel(r'$\Delta [H^+]$ in nmol/kg')
            
        for axis in ax[1, :]:
            axis.set_xlabel('Experiment year')
        # Legend
        legend = fig.legend(loc='upper left', bbox_to_anchor=(0.09, 0.65),
                            fontsize=fontsize - 3, ncols=3, facecolor='w', columnspacing=1)
        legend.get_frame().set_alpha(1.0)
    
        plt.tight_layout()
        plt.show()
        
        return fig, ax 


    def _plot_comparison_taylor_sum_vs_model_output(run_params,region,variable_regional_time_series,contribution_regional_time_series,variable_to_analyze):
        fontsize=16
        plt.rcParams['font.size']=fontsize
        psts = ['a','b']
        fig, ax = plt.subplots(1,2,figsize=(15,5.4),sharey=True,sharex=True)
        for rdx,reg in enumerate(['Global Ocean',region]):
    
            # loop through the models and plot the taylor sum and fwtaylor sum (for model data plot the change from the first time step)
            for key in run_params.keys():
                # taylor sum
                taylor_sum_to_plot = contribution_regional_time_series['taylor_sum'][reg][key]
                ax[rdx].plot(taylor_sum_to_plot,color=run_params[key].runcol,alpha=0.75,linestyle='--')
                # fw tylor sum
                fwtaylor_sum_to_plot = contribution_regional_time_series['fwtaylor_sum'][reg][key]
                ax[rdx].plot(fwtaylor_sum_to_plot,color=run_params[key].runcol,alpha=0.75,linestyle=':')
                # model data
                model_data_to_plot = variable_regional_time_series[reg][key] - variable_regional_time_series[reg][key].isel(year=0)
                ax[rdx].plot(model_data_to_plot,color=run_params[key].runcol,alpha=0.75,label=run_params[key].model,linestyle='-')
        
            # calculate and plot the multimodel means (for model data plot the change from the first time step)
            # taylor sum
            mmm_taylor, _   = MMFuncs._calc_multimodel_mean_and_agreement(contribution_regional_time_series['taylor_sum'][reg], da_name=None, agreement_type = 'sign', agreement_thresh='at_least_80percent_agree')
            ax[rdx].plot(mmm_taylor,color='k',linewidth=5,label=r'$\Sigma_{Taylor}$',linestyle='--')
            # fw taylor sum
            mmm_fwtaylor, _ = MMFuncs._calc_multimodel_mean_and_agreement(contribution_regional_time_series['fwtaylor_sum'][reg], da_name=None, agreement_type = 'sign', agreement_thresh='at_least_80percent_agree')
            ax[rdx].plot(mmm_fwtaylor,color='k',linewidth=5,label=r'$\Sigma_{fwTaylor}$',linestyle=':')
            # model data
            mmm_model,_ = MMFuncs._calc_multimodel_mean_and_agreement(variable_regional_time_series[reg], da_name=None, agreement_type = 'sign', agreement_thresh='at_least_80percent_agree')
            mmm_model = mmm_model - mmm_model.isel(year=0)
            ax[rdx].plot(mmm_model,color='k',linewidth=5,label=r'Model',linestyle='-')
    
            for adx,axi in enumerate(ax.flatten()):
                axi.set_xlim([0,340])
                axi.axvline([140],linestyle='--',color='#777777')
                axi.axvline([280],linestyle='--',color='#777777')
                axi.axhline(0,linestyle='--',color='#777777')
                axi.text(0.02,0.98,f'{psts[adx]})',ha='left',va='top',transform=axi.transAxes)
    
            if variable_to_analyze == 'omegaa':
                ax[0].set_ylabel(r'$\Delta \Omega_\text{Arag.}$')
            else:
                ax[0].set_ylabel(r'$\Delta [H^+]$ in nmol/kg')
            #ax[1,0].set_ylabel(r'$\Delta [H^+]$ in nmol/L')
            for axi in ax:
                axi.set_xlabel('Experiment year')
            ax[0].legend(fontsize=fontsize-5)#,loc='lower left')#,bbox_to_anchor=(0.1,0.6))
            plt.tight_layout()
            #if varia == 'ph1':
            #    varia2 = 'hplus'
            ax[rdx].set_title(f'{reg}')
        
        return fig, ax 

    
    def _plot_decomposition_error_time_series(run_params,cont_ts,var_ts,loc_reg,variable_to_analyze):
    
        # plot setup
        conts_for_plotting = ['taylor_sum']
        bar_labels = [r'$\Sigma_\text{Taylor}$']
        bar_colors = ['k']
        if variable_to_analyze == 'hplus':
            varia2 = r'[$H^+$]'
            unit = r'nmol kg$^{-1}$'
            ylabel = '$\Delta$ '+f'{varia2} ({unit})'
        elif variable_to_analyze == 'omegaa':
            varia2 = r'$\Omega_\text{Arag.}$'
            unit = '-'
            ylabel = '$\Delta$ '+f'{varia2} ({unit})'
    
        # compute the multimodel mean taylor sum
        taylor_sum = cont_ts['taylor_sum'][loc_reg]
        taylor_sum_mmm, _ = MMFuncs._calc_multimodel_mean_and_agreement(taylor_sum, da_name=None, agreement_type = 'sign', agreement_thresh='at_least_80percent_agree')
    
        # compute the multimodel mean variable
        var_dum = var_ts[loc_reg] - var_ts[loc_reg].isel(year=0)
        var_mmm, _ = MMFuncs._calc_multimodel_mean_and_agreement(var_dum, da_name=None, agreement_type = 'sign', agreement_thresh='at_least_80percent_agree')
    
        figsize=11
        fig,ax = plt.subplots(1,3,figsize=(17,6))
        # plot the contributions
        ax[0].plot(taylor_sum_mmm,'k',linewidth=4,label=r'$\Sigma_\text{Taylor}$')
        ax[0].plot(var_mmm,'r',linewidth=2,label=r'model $\Omega_\text{Arag.}$')
        ax[0].legend(loc=0)
        ax[0].set_ylabel(ylabel)
        ax[0].set_title(f'{loc_reg} {varia2} (MMM)',loc='left')
        ax[0].axhline(0,linestyle='--',alpha=0.5)
        # plot the relative error
        ax[1].plot((taylor_sum_mmm-var_mmm)/var_mmm*100)#[:-1])
        ax[1].axhline(0,linestyle='--',alpha=0.5)
        ax[1].set_ylabel('Error in %')
        ax[1].set_title('relative error')#mmm_reg_mean_direct_model')
        ax[1].text(0.5,0.93,r'$(\Sigma_\text{Taylor} - \text{model})/\text{model} * 100$',transform=ax[1].transAxes,ha='center')
        # plot the absolute error
        ax[2].plot(taylor_sum_mmm-var_mmm)#[:-1])
        ax[2].axhline(0,linestyle='--',alpha=0.5)
        ax[2].set_ylabel('Error in -')
        ax[2].set_title('absolute error')#mmm_reg_mean_direct_model')
        ax[2].text(0.75,0.93,r'$\Sigma_\text{Taylor} - \text{model}$',transform=ax[2].transAxes,ha='center')
    
        
        for axi in ax:
            axi.set_xlim([0,340])
            axi.axvline([140],linestyle='--',color='#CCCCCC',alpha=1,zorder=0,linewidth=1)
            axi.axvline([280],linestyle='--',color='#CCCCCC',alpha=1,zorder=0,linewidth=1)
            axi.spines[['right', 'top']].set_visible(False)
            axi.set_xlabel('Year')
        ax[1].set_ylim([-3,3])
    
        plt.tight_layout()
        plt.show()    
        return fig, ax
    
