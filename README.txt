## Author: Eike E. Köhn
## date: Jul 28, 2025

Repository containing the analysis scripts and results for the manuscript on Arctic acdification reversibility.

Things to do:

Minor plot adjustments:
- hysteresis: ramp-up and ramp-down instead of rampup and rampdown

Analysis plots:
- fgco2,anth
- hysteresis analysis for h+

Preprocessing:
- processing of raw model datasets to combined 1pctCO2-1pctCO2cdr runs (double checking year alignment for each model) (pCO2_seasonality/process_all_variables_to_optain_annual_means.ipynb)
- mocsy calculations of omega/h+ from model output and for sensitivities (run_mocsy_1pctCO2-cdr_annual_for_sensitivities.ipynb,
run_mocsy_1pctCO2-cdr_annual.ipynb, run_mocsy_piControl_annual.ipynb)
- make sure to use the Waters et al. (2014) constants for the carbonate chemistry (MOCSY and pyco2sys for sCT_equil)
- make sure that sea ice concentrations are treated equally between 1pctco-cdr and picontrol (as of now 0-1 and 0-100% and manually adjusted in sea ice analysis)

General:
- check atmospheric xCO2 axis (correct and same positioning for all models?)
- check for atmospheric pressure and humidity data to properly convert xCO2 to pCO2

