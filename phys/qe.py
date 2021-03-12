
'''
Package:            GOES-16 Latent Heat Flux Numerical Model
Script name:        Latent Heat Flux Calculation
Package file path:  ~/phys/qe.py
Objective:          Calculate latent heat flux at a given coordinate and time
Author:             Gabriel Rios
'''

##############################################################################################
# BEGIN IMPORTS
##############################################################################################

import math, numpy as np, sys, time

##############################################################################################
# END IMPORTS
##############################################################################################

# Psychrometric constant (hPa K^-1)
gamma = 0.670 
# Gas constant (J K^-1 kg^-1)
R = 287.05   
# Specific heat capacity of air at constant pressure
c_p = 1006  
# Latent heat of vaporization (J kg^-1)
L_v = 2.5e6
# Gas constant for water vapor (J K^-1 kg^-1)
R_v = 461
# Reference vapor pressure (hPa)
e_0 = 6.113

##############################################################################################
# Method name:      rho
# Method objective: Calculate air density at a given temperature.
# Input(s):         T_air [float], p_air [float]
# Outputs(s):       rho [float]
##############################################################################################    

def rho(T_air, p_air):
    ''' Calculate air density at a given temperature. '''
    return p_air*100/(R*T_air)

##############################################################################################
# Method name:      theta
# Method objective: Calculate potential and virtual potential temperatures.
# Input(s):         T_air [float], T_dew [float], p_air [float]
# Outputs(s):       theta [float], theta_v [float]
# Reference:        https://glossary.ametsoc.org/wiki/Virtual_potential_temperature
##############################################################################################    

def theta(T_air, T_dew, p_air):
    ''' Calculate potential and virtual potential temperatures. '''
    # Convert from Kelvin to Celsius
    T_dew = T_dew - 273.15
    # Calculate potential temperature
    theta_0 = T_air * math.pow(1000/p_air, R/c_p)
    # Calculate virtual potential temperature
    theta_v = T_air/(1-0.379*6.11*math.pow(10, 7.5*T_dew/(237.7+T_dew))/p_air)
    return theta_0

##############################################################################################
# Method name:      vp
# Method objective: Calculate atmospheric and saturation vapor pressure for a given temperature.
# Input(s):         T_air [float, degK]
# Outputs(s):       e [float, hPa], e_s [float, hPa]
# Reference:        "The computation of equivalent potential temperature" (Bolton, 1980).
##############################################################################################    

def q(T_air, T_dew, p_air):
    ''' Calculate atmospheric specific, saturated specific, and relative humidity for a given temperature. '''
    # Convert from Kelvin to Celsius
    T_air, T_dew = [T_air-273.15, T_dew-273.15]
    # Calculate atmospheric vapor pressure
    e = e_0*np.exp((17.67*T_dew)/(T_dew + 243.5))
    # Calculate saturated vapor pressure
    e_s = e_0*np.exp((17.67*T_air)/(T_air + 243.5))
    # Calculate atmospheric specific humidity (kg/kg)
    q_a = 0.622*e/(p_air - 0.378*e)
    # Calculate saturated specific humidity (kg/kg)
    q_s = 0.622*e_s/(p_air - 0.378*e_s) 
    # Calculate relative humidity
    rh = 100*q_a/q_s
    return q_a, q_s

##############################################################################################
# Method name:      lhf
# Method objective: Calculate latent heat flux using an iterative algorithm.
# Input(s):         
# Outputs(s):       
# Reference:        Trial 1: Wang, 2012
##############################################################################################

def lhf(T_lst, T_air, T_dew, p_air, r_av, sm, S_d, LAI):
    ''' Calculate latent heat flux using an iterative algorithm. '''
    
    # print('T_s: {0:.2f} K | T_a: {1:.2f} K | T_dew: {2:.2f} K | p: {3:.2f} kPa | r_av: {4:.2f} | sm: {5:.2f} m3/m3 | sd: {6:.2f} W/m2 | lai: {7:.2f}'.format(T_lst, T_air, T_dew, p_air, r_av, sm, S_d, LAI))
    
    q_a, q_sat_l = q(T_air, T_dew, p_air)
    _, q_sat_g = q(T_lst, T_dew, p_air)
    # print('Saturated specific humidity: {0:.4f} | Specific surface temperature humidity: {1:.4f} | Specific humidity: {2:.4f}'.format(q_sat_l, q_sat_g, q_a))
    
    # Assumed values for r_st
    r_st_min = 1e2
    r_st_max = 1e4    
    c_sd = 25
    
    sm_max = np.nanmax(sm)
    c_sw = sm/sm_max
    
    r_st = r_st_min/c_sw + ((r_st_max-r_st_min)/c_sw)*(1-np.tanh(S_d/c_sd))
    r_c = r_st/LAI
    
    # Assumed coefficient values for r_soil
    a = 3.5
    b = 2.3
    c = 433.5   
    r_soil = a*(sm_max/sm)**b+c
    
    # print('Aerodynamic resistance: {0:.2f} | Canopy resistance: {1:.2f} | Soil resistance: {2:.2f}'.format(r_av, r_c, r_soil))
    
    T = rho(T_air, p_air)*(q_sat_l - q_a)/(r_av + r_c)
    E = rho(T_air, p_air)*(q_sat_g - q_a)/(r_av + r_soil)
    qe = (T + E)*L_v
    
    # print('Latent heat flux: {0:.3f} W/m2'.format(qe))
    
    return qe

if __name__ == '__main__':
    ii, jj = [1, 1]
    qe_ = []
    for i in range(0, 23):
        qe = lhf(T_s[:, :, i][ii, jj], T_a[:, :, i][ii, jj], T_dew[i], p_air[i], r_av[:, :, i][ii, jj], sm[:, :, i][ii, jj], sd[:, :, i][ii, jj], lai[:, :, i][ii, jj])
        qe_.append(qe)
        print('---------------------------------------------------------------')