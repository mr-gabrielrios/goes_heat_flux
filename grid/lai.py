'''
Package:            GOES-16 Heat Flux Numerical Model
Script name:        AVHRR Leaf Area Index (LAI) Processing
Package file path:  ~/grid/lai.py
Objective:          Read leaf area index from the AVHRR data repository
Author:             Gabriel Rios
'''

# NOTE: THIS FILE IS CURRENTLY USED FOR INTIAL PHASES OF THE LATENT HEAT FLUX ALGORITHM PROCESS
#       CUSTOM COORDINATES ADDED FOR US-ARM AMERIFLUX STATION IN OKLAHOMA
#       https://ameriflux.lbl.gov/sites/siteinfo/US-ARM       


##############################################################################################
# BEGIN IMPORTS
##############################################################################################

import cartopy.crs as ccrs, datetime, matplotlib.pyplot as plt, gc, netCDF4, numpy as np, os, pandas as pd, requests, scipy, sys, time, urllib, xarray as xr
from bs4 import BeautifulSoup

xr.set_options(file_cache_maxsize=24)

##############################################################################################
# END IMPORTS
##############################################################################################

##############################################################################################
# Method name:      pull_data
# Method objective: Returns URLs for LAI file corresponding to a given date range.
# Input(s):         date_range [Pandas date range]
# Outputs(s):       files [list]
##############################################################################################

def nc_reader(file, domain):
    ''' Returns netCDF4 data for a given a file path and location. '''
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    # Create temp directory to hold files in process
    if not os.path.isdir(temp_dir):
        os.mkdir(temp_dir)
    fname = 'lai' + '_' + file.split('_')[-2] + '.nc'
    fpath = os.path.join(os.path.dirname(__file__), 'lai', fname)
    if os.path.isfile(fpath):
        # Download file
        urllib.request.urlretrieve(file, os.path.join(temp_dir, file.split('/')[-1]))
        # Read to netCDF4 file
        nc = xr.open_dataset(os.path.join(temp_dir, file.split('/')[-1]))
        # Locate corresponding data point
        # nc.sel(latitude=crd[0], longitude=crd[1], method="nearest").to_netcdf(fpath)
        data = nc['LAI'].isel(time=0)
        nc.where((data.latitude >= domain[0]) & (data.latitude <= domain[2]) & (data.longitude >= domain[1]) & (data.longitude <= domain[3]), drop=True).to_netcdf(fpath)
        # Remove file from temp folder
        os.remove(os.path.join(temp_dir, file.split('/')[-1]))
        return nc     
    
def pull_data(domain, date_range):
    ''' Returns URL for LAI file corresponding to a given date range. '''
    
    # URL for directory where LAI and FAPAR data is stored
    # 2017 is year used for current data collection
    url = r'https://www.ncei.noaa.gov/data/avhrr-land-leaf-area-index-and-fapar/access/' + str(date_range[0].year) + '/'
    # Grab HTML data for the specified URL
    page = requests.get(url).text
    # Create parser for HTML data
    soup = BeautifulSoup(page, 'html.parser')
    # Loop to grab data for each day in the date range given. A list is populated with each file.
    files = []
    for day in date_range:
        file = [url + link.get('href') for link in soup.find_all('a') 
              if '_' in link.get('href') and link.get('href').split('_')[-2] == day.strftime('%Y%m%d')]
        # Selects string in list item to prevent 'files' from being a 2D list
        files.append(file[0])
        
    for file in files:
        print(file.split('/')[-1])
        # Create .nc file for given coordinate
        # nc_reader(file, domain)
    
    flist = sorted(os.listdir(os.path.join(os.path.dirname(__file__), 'lai')))
    flist = [os.path.join(os.path.dirname(__file__), 'lai', i) for i in flist]
    ncs = xr.open_mfdataset(flist)
    return ncs

def mapper(data, domain):
    lai = data['LAI'].isel(time=[60, 61, 62, 63])
    plt = lai.plot(x="longitude", y="latitude", col="time", col_wrap = 2, cmap='YlGn')

def main(domain, domain_center, date_range, var):
    
    # Boolean to check if file containing data for selected date range exists already
    file_exists, file = False, ''
    # Check all files in LAI folder
    for file in os.listdir(os.path.join(os.path.dirname(__file__), 'lai')):
        if file.endswith('.nc'):
            # Get file date range. The [1:] indexing isolates the datetime string.
            file_ = os.path.splitext(file)[0]
            fdate = [datetime.datetime.strptime(file_.split('_')[-2][1:], '%Y%m%d'), 
                     datetime.datetime.strptime(file_.split('_')[-1][1:], '%Y%m%d')]
            if fdate[0] <= date_range[0] and fdate[-1] >= date_range[-1]:
                file_exists = True
                fname = file
            break
        
    if not file_exists:        
        fname = 'lai' + '_' + str(domain_center[0]) + '_' + str(domain_center[1]) + '_s' + date_range[0].strftime('%Y%m%d') + '_e' + date_range[-1].strftime('%Y%m%d') + '.nc'
    
    fpath = os.path.join(os.path.dirname(__file__), 'lai', fname)
    
    if not file_exists:
        ncs = pull_data(domain, date_range)
        ncs.to_netcdf(fpath)
    else:
        ncs = xr.open_dataset(fpath)
        
    return ncs.latitude.values, ncs.longitude.values, ncs[var].interpolate_na(dim=('time'), method='linear').values
        
if __name__ == '__main__':
    troubleshooting = True
    if troubleshooting:
        date_range = pd.date_range(datetime.datetime(year=2017, month=10, day=8),
                                   datetime.datetime(year=2017, month=10, day=9),
                                   freq="D")
        crd = [36.6058, -97.4888]
        res = 0.25
        domain = [crd[0]-res, crd[1]-res, crd[0]+res, crd[1]+res]
        var = 'LAI'
        
        fname = 'lai' + '_' + str(crd[0]) + '_' + str(crd[1]) + '_s' + date_range[0].strftime('%Y%m%d') + '_e' + date_range[-1].strftime('%Y%m%d') + '.nc'
        fpath = os.path.join(os.path.dirname(__file__), 'lai', fname)
        
        # Boolean to check if file containing data for selected date range exists already
        file_exists = False
        # Check all files in LAI folder
        for fname in os.listdir(os.path.join(os.path.dirname(__file__), 'lai')):
            if fname.endswith('.nc'):
                # Get file date range. The [1:] indexing isolates the datetime string.
                fname_ = os.path.splitext(fname)[0]
                fdate = [datetime.datetime.strptime(fname_.split('_')[-2][1:], '%Y%m%d'), 
                         datetime.datetime.strptime(fname_.split('_')[-1][1:], '%Y%m%d')]
                if fdate[0] <= date_range[0] and fdate[-1] >= date_range[-1]:
                    file_exists = True
                break
        
        if not file_exists:
            ncs = pull_data(domain, date_range)
            ncs.to_netcdf(os.path.join(os.path.dirname(__file__), 'lai', fname))
        else:
            ncs = xr.open_dataset(fpath)
        
        ncs[var].sel(latitude=crd[0], longitude=crd[1], method='nearest').interpolate_na(dim=('time'), method='linear').plot()
    mapper(ncs, domain)
    
    lons, lats, data = main([36.1058, 37.1058, -97.9888, -96.9888], [36.6058, -97.4888], [datetime.datetime(year=2017, month=10, day=8, hour=5),
                  datetime.datetime(year=2017, month=10, day=8, hour=6)-datetime.timedelta(hours=1)], 'LAI')