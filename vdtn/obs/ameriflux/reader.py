'''
Package:            GOES-16 Heat Flux Numerical Model
Script name:        Ameriflux Data Processing
Package file path:  ~/vdtn/obs/ameriflux/reader.py
Objective:          Read relevant data from selected Ameriflux stations
Author:             Gabriel Rios
'''

##############################################################################################
# BEGIN IMPORTS
##############################################################################################

import datetime, glob, matplotlib.pyplot as plt, numpy as np, os, pandas as pd, sys, time

##############################################################################################
# END IMPORTS
##############################################################################################

##############################################################################################
# Method name:      CtoK
# Method objective: Convert degrees Celsius to degrees Kelvin.
# Input(s):         T [float]
# Outputs(s):       T + 273.15 [float]
##############################################################################################

def CtoK(T):
    ''' Convert degrees Celsius to degrees Kelvin. '''
    return T + 273.15

##############################################################################################
# Method name:      distance
# Method objective: Calculate great circle distance between a point and an Ameriflux station.
# Input(s):         lat_crd [float], lon_crd [float], lat_asos [float], lon_asos [float]
##############################################################################################
    
def distance(lat_crd, lon_crd, lat_stat, lon_stat):
    ''' Calculate great circle distance between a point and an Ameriflux station. '''
    # GRS80 semi-major axis of Earth, per GOES-16 PUG-L2, Volume 5, Table 4.2.8
    R = 6378137 
    p = np.pi/180
    a = 0.5 - np.cos((lat_stat-lat_crd)*p)/2 + np.cos(lat_crd*p) * np.cos(lat_stat*p) * (1-np.cos((lon_stat-lon_crd)*p))/2
    return 2*R*np.arcsin(np.sqrt(a))

##############################################################################################
# Method name:      site_finder
# Method objective: Find closest Ameriflux station to a given coordinate.
# Input(s):         lat_crd [float], lon_crd [float]
# Outputs(s):       station [str]
##############################################################################################

def site_finder(lat_crd, lon_crd):
    ''' Find closest Ameriflux station to a given coordinate. '''
    
    # Text file listing all ASOS stations with metadata.
    ameriflux_log = os.path.join(os.path.dirname(__file__), 'log.csv')
    # GRS80 semi-major axis of Earth, per GOES-16 PUG-L2, Volume 5, Table 4.2.8
    R = 6378137
    # Define relevant columns for station location
    cols = ['Site', 'Latitude', 'Longitude']
    # Read data into ASOS DataFrame (adf)
    sites = pd.read_csv(ameriflux_log, usecols=cols)
    # Get relevant data in list format for distance calculation
    stations, lat_asos, lon_asos = [sites['Site'], sites['Latitude'], sites['Longitude']]   
    # Define arbitrarily large number as an initial condition (rouglhy equal to circumference of Earth)
    dists = 2*np.pi*R 
    # Initialize empty string for population
    station = '' 
    # Iterate over list of statons to find closest station
    for i in range(1, len(lat_asos)):
        dist = distance(lat_crd, lon_crd, lat_asos[i], lon_asos[i])
        if dist < dists:
            dists = dist
            station = stations[i]

    print("Closest station: %s, %.2f m away" % (station, dists))

    return station

##############################################################################################
# Method name:  CSV Reader
# Objective:    Read data from the Ameriflux station closest to the given coordinate.
# Input(s):     Site name (str), start date (datetime), end date (datetime)   
# Output(s):    DataFrame
###################################################################################################

def csv_reader(crd, start_date, end_date):
    ''' Read data from the Ameriflux station closest to the given coordinate. '''
    # Find closest Ameriflux station to given coordinates
    station = site_finder(crd[0], crd[1])
    # Find directory and file corresponding to selected site. 
    # Assuming only one .csv file per station directory.   
    # End program if local data isn't found.
    try:
        fdir = glob.glob(os.path.join(os.path.dirname(__file__), '*' + station + '*'))[0]
        file = glob.glob(os.path.join(fdir, '*.csv'))[0]
    except:
        print('Data corresponding to closest Ameriflux station has not been downloaded locally. Exiting...')
        sys.exit()
    
    ### DataFrame generation, data filtering, and type conversions
    
    # List of parameters of interest. See Ameriflux README for more information (linked below).
    # https://ftp.fluxdata.org/.ameriflux_downloads/BASE/README_AmeriFlux_BASE.txt
    # Timestamp, sensible heat flux, atmospheric pressure, relative humidity, air temperature, friction velocity, wind speed
    # Use the try/except based on the site-to-site variation in column names for air temperature and wind speed
    try:
        col_list = ['TIMESTAMP_START', 'H_1_1_1', 'LE_1_1_1', 'PA_1_1_1', 'RH_1_1_1', 'TA_1_1_1', 'USTAR_1_1_1', 'WS_1_1_1']
        data = pd.read_csv(file, header=2, usecols=col_list)
        data = data.rename(columns = {'TIMESTAMP_START': 'datetime', 
                                      'TA_1_1_1': 'T_air', 
                                      'H_1_1_1': 'Q_H', 
                                      'LE_1_1_1': 'Q_E', 
                                      'PA_1_1_1': 'PA_1_1_1', 
                                      'USTAR_1_1_1': 'u_star',
                                      'WS_1_1_1': 'u_r'}) 
    except:
        col_list = ['TIMESTAMP_START', 'H', 'PA', 'RH', 'TA', 'USTAR', 'WS']
        data = pd.read_csv(file, header=2, usecols=col_list)
        data = data.rename(columns = {'TIMESTAMP_START': 'datetime', 
                                      'TA': 'T_air', 
                                      'H': 'Q_H', 
                                      'L': 'Q_E', 
                                      'USTAR': 'u_star',
                                      'WS': 'u_r'}) 
    
    # Remove null sensible heat flux data
    data = data[data > -9999] 
    # Cast times to datetime format
    data['datetime'] = pd.to_datetime(data['datetime'], format='%Y%m%d%H%M') 
    
    # Convert air temperature to Kelvin
    data['T_air'] = CtoK(data['T_air'])
    
    # Date filtering
    # End date hour adjustment to account for hour reduction in main script
    end_date = end_date + datetime.timedelta(hours=1)
    data = data[(data['datetime'] >= start_date) & (data['datetime'] <= end_date)]

    date_df = pd.DataFrame()
    date_range = pd.date_range(start_date, end_date, (end_date-start_date).total_seconds()/3600+1)
    
    date_df = date_df.reindex(date_range, fill_value=np.nan)
    date_df = date_df.reset_index().rename(columns={'index': 'datetime'})
    
    data = pd.merge(data, date_df, how='right', on=['datetime'])   
    data = data.sort_values(by=['datetime'])
    data = data.reset_index(drop=True)
    data = data[:-1] # Drop nan row at end due to reindexing
    
    # Plotting for troubleshooting
    # nanmask = np.isfinite(data['Q_E']) # Masking to plot over nans
    # plt.plot(data['datetime'][nanmask], data['Q_E'][nanmask])
    # plt.plot(data['datetime'][nanmask], data['Q_H'][nanmask])
    
    return data
    
if __name__ == "__main__":
    # Pull name of Ameriflux station US-xUK (outside of Portland, OR) for trial version
    # Note: data available for 06-2019 to 12-2020
    data = csv_reader([36.6058, -97.4888], datetime.datetime(year=2017, month=10, day=8, hour=0), datetime.datetime(year=2017, month=10, day=9, hour=0))
    print(data)