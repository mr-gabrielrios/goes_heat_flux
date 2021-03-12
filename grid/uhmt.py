'''
Objective:  Read u-HMT data given by P. Ramamurthy
'''

import cartopy.crs as ccrs, matplotlib.pyplot as plt, numpy as np, os, pandas as pd

def reader():
    # Initialize empty DataFrame to collect data
    data = pd.DataFrame()
    # Get directory name
    fdir = os.path.join(os.path.dirname(__file__), 'smap', 'uhmt')
    # Iterate through all files and open each one, read and append to DataFrame
    for file in os.listdir(fdir):
        if file.endswith('.dat'):
            # Read in data. Preserve name of each column (row 1 becomes header)
            temp = pd.read_csv(os.path.join(fdir, file), skiprows=[0, 2, 3])  
            temp['site'] = file.split('.')[0]
            data = data.append(temp)
    # Assign datatypes to each column
    data = data.astype({'TIMESTAMP': 'datetime64',
                        'RECORD': 'int64',
                        'VWC': 'float64',
                        'T': 'float64',
                        'P': 'float64',
                        'VWC_2': 'float64',
                        'T_2': 'float64',
                        'P_2': 'float64',
                        'VWC_3': 'float64',
                        'T_3': 'float64',
                        'P_3': 'float64',
                        'VWC_4': 'float64',
                        'T_4': 'float64',
                        'P_4': 'float64',
                        'AirTF': 'float64',
                        'RH': 'float64',
                        'Rainfall_Tot': 'float64',
                        'Snowfall_Tot': 'float64',
                        'site': 'string'})
    # Assign coordinates to each site in the complete dataset
    # Note: NYCHA sites used for measurement sites
    coords = {'Site1_Queens_Botanical_Garden_Fifteen': [40.7530379, -73.831358],
              'Site2_Queensborough_Community_College_Fifteen': [40.755387, -73.757445],
              'Site3_Ronald_Edmonds_Learning_Center_Fifteen': [40.689081, -73.971370],
              'Site5_Middletown_Houses_Fifteen': [40.844358, -73.828863],
              'Site6_Dyckman_Houses_Fifteen': [40.860940, -73.923663],
              'Site7_Williamsburg_Houses_Fifteen': [40.710173, -73.941144],
              'Site8_Polo_Ground_Fifteen': [40.830674, -73.937114],
              'Site9_Far_Rockaway_Fifteen': [40.596704, -73.772494],
              'Site10_BayView_Fifteen': [40.633247, -73.885945],
              'Site11_Baisley_Park_Fifteen': [40.684824, -73.782535],
              'Site12_East_River_Fifteen': [40.787633, -73.940002]}
    for file in os.listdir(fdir):
        if file.endswith('.dat'):
            site = file.split('.')[0]
            data.loc[data['site'] == site, 'lat'] = coords[site][0]
            data.loc[data['site'] == site, 'lon'] = coords[site][1]
    # Return opened data 
    return data

def mapper(data):
    
    crd = [40.7128, -73.8560]
    res = 0.25
    
    fig = plt.figure(figsize=(6, 6), dpi=300)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([crd[1] - res, crd[1] + res, crd[0] - res, crd[0] + res])
    ax.coastlines()
    
    # Get coordinates for each location
    locs = data['site'].unique()
    for location in locs:
        lat, lon = [data.loc[data['site'] == location, 'lat'][0], 
                    data.loc[data['site'] == location, 'lon'][0]]
        ax.scatter(lon, lat, zorder=999)
        ax.text(lon, lat, '  ' + location.split('_')[0])

if __name__ == "__main__":
    # Read in data
    data = reader()
    mapper(data)