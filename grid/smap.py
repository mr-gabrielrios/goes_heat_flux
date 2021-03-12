'''
Package:            GOES-16 Heat Flux Numerical Model
Script name:        Soil Moisture Active Passive (SMAP) Data Processing
Package file path:  ~/grid/smap.py
Objective:          Read soil moisture data from the SMAP data repository
Author:             Gabriel Rios
Note:               See the 'User Guide' tab for SMAP file information: 
                    https://nsidc.org/data/SPL2SMAP_S/versions/3
'''

# NOTE: THIS FILE IS CURRENTLY USED FOR INTIAL PHASES OF THE LATENT HEAT FLUX ALGORITHM PROCESS
#       CUSTOM COORDINATES ADDED FOR US-ARM AMERIFLUX STATION IN OKLAHOMA
#       https://ameriflux.lbl.gov/sites/siteinfo/US-ARM       

##############################################################################################
# BEGIN IMPORTS
##############################################################################################

import cartopy, cartopy.crs as ccrs, datetime, matplotlib.pyplot as plt, numpy as np, os, pandas as pd, re, scipy, xarray as xr, netCDF4
from scipy import spatial

##############################################################################################
# END IMPORTS
##############################################################################################

def reader(var, crd, res, date_range):
    ''' Grab SMAP dataset corresponding to a given location and time. '''
    
    # Create path pointing to subfolder with SMAP satellite-derived data products
    file_dir = os.path.join(os.path.dirname(__file__), 'smap')
    # Generate list of files in SMAP subfolder, sorted alphabetically      
    file_list = sorted(os.listdir(file_dir)) 
    
    # Define regular expression corresponding to file name coordinates
    crd_re = '\d{3}[A-Z]\d{2}[A-Z]'
    # Overwrite date range
    date_range = pd.date_range(start=datetime.datetime(year=2020, month=1, day=1),
                               end=datetime.datetime(year=2020, month=12, day=31),
                               freq='D')
    # Initialize list of dates with SMAP data
    dates = []
    # Initialized empty list to store all SMAP data from loop
    data = []
    # Create bound box for window within each data to create a consistent array size
    bound_box = [crd[0]-res, crd[1]-res, crd[0]+res, crd[1]+res]
    # Counter for number of files found meeting criteria
    i = 0
    # If a file is found within the allotted temporal tolerance, read its data into an xarray
    for date in date_range:
        for file in file_list:
            # Downselect HDF5 files
            if file.endswith('.h5'):
                # Read the date of the data from the file name
                file_date = datetime.datetime.strptime(file.split('_')[5].replace('T', ''), '%Y%m%d%H%M%S')
                # Read the latitude and longitude of the SMAP pass form the file name
                file_crd = [float(re.findall(crd_re, file)[0][-3:-1]), float(re.findall(crd_re, file)[0][0:3])]
                # Filter by date (Julian days must be equal) and for specific location
                if file_date.timetuple().tm_yday == date.timetuple().tm_yday and file_crd == [36, 97]:
                    print(file_date)
                    # Read file data into netCDF variable
                    dataset = netCDF4.Dataset(os.path.join(file_dir, file), mode='r')
                    # Pull relevant data from the HDF5 file
                    temp = np.array(dataset.groups['Soil_Moisture_Retrieval_Data_1km'].variables[var])
                    # Define coordinate grids
                    lat = np.array(dataset.groups['Soil_Moisture_Retrieval_Data_1km'].variables['latitude_1km'])
                    lon = np.array(dataset.groups['Soil_Moisture_Retrieval_Data_1km'].variables['longitude_1km'])
                    # Filter out data beyond the bounding box
                    # The point of this is to create consistent dataset sizes despite distinct SMAP data sizes
                    temp_ = np.where((lat >= bound_box[0]) & (lat <= bound_box[2]) & (lon >= bound_box[1]) & (lon <= bound_box[3]), temp, np.nan)
                    lat_ = np.where((lat >= bound_box[0]) & (lat <= bound_box[2]) & (lon >= bound_box[1]) & (lon <= bound_box[3]), lat, np.nan)
                    lon_ = np.where((lat >= bound_box[0]) & (lat <= bound_box[2]) & (lon >= bound_box[1]) & (lon <= bound_box[3]), lon, np.nan)
                    # Remove all rows and columns that only have nans - this is where data beyond the bounding box should exist
                    temp_ = temp_[~np.all(np.isnan(temp_), axis=1)][:, ~np.all(np.isnan(temp_), axis=0)]
                    lat_ = lat_[~np.all(np.isnan(lat_), axis=1)][:, ~np.all(np.isnan(lat_), axis=0)]
                    lon_ = lon_[~np.all(np.isnan(lon_), axis=1)][:, ~np.all(np.isnan(lon_), axis=0)]                    
                    # Reshape data into a 3D array for insertion to xArray format
                    temp_ = temp_.reshape(np.shape(temp_)[0], np.shape(temp_)[1], 1)    
                    
                    # Initialize data with first array read in. For other iterations, append to data.
                    if i == 0:
                        data = temp_
                    else:
                        data = np.append(data, temp_, axis=2)
                    
                    dates.append(date)
                        
                    i += 1
    
    # Create xarray data structure with longitude and latitude dimensions
    arr = xr.Dataset(
        {var: (['x', 'y', 'time'], data)},
        coords={
            "lon": (["x", "y"], lon_),
            "lat": (["x", "y"], lat_),
            "time": dates,
        })
    # Filter data that is null (== -9999)
    arr[var] = arr[var].where(arr[var] >= 0)
    
    return arr

def mapper(arr, var):
    ax = plt.subplot(projection=ccrs.PlateCarree())
    arr[var].isel(time=0).plot.pcolormesh("lon", "lat", ax=ax, cmap='viridis_r')
    ax.gridlines(draw_labels=True)

def main(domain, domain_center, date_range, var):
    # Half the width of the bounding box
    res = 0.25    
    
    # Generate file path
    # Format: VARNAME_lat_lon_sYYYYmmdd_eYYYYmmdd.nc
    fname = var + '_' + str(domain_center[0]) + '_' + str(domain_center[1]) + '_s' + date_range[0].strftime('%Y%m%d') + '_e' + date_range[-1].strftime('%Y%m%d') + '.nc'
    fpath = os.path.join(os.path.dirname(__file__), 'smap', fname)
    
    # Boolean to check if file containing data for selected date range exists already
    file_exists = False
    # Check all files in SMAP folder
    for fname in os.listdir(os.path.join(os.path.dirname(__file__), 'smap')):
        if fname.endswith('.nc'):
            # Get file date range. The [1:] indexing isolates the datetime string.
            fname_ = os.path.splitext(fname)[0]
            fdate = [datetime.datetime.strptime(fname_.split('_')[-2][1:], '%Y%m%d'), 
                     datetime.datetime.strptime(fname_.split('_')[-1][1:], '%Y%m%d')]
            if fdate[0] <= date_range[0] and fdate[-1] >= date_range[-1]:
                file_exists = True
                fpath = os.path.join(os.path.dirname(__file__), 'smap', fname)
                break
    
    # If data exists for given time and coordinate, access it. 
    # Else, generate it.
    if not file_exists:   
        arr = reader(var, domain_center, res, date_range)
        arr.to_netcdf(os.path.join(os.path.dirname(__file__), 'smap', fname))
    else:
        arr = xr.open_dataset(fpath)
    
    # Define data resampling frequency
    freq = 'H'    
    # Get index of starting hour in question
    # Note: this is being done to sample the part of the yearlong dataset for the given date range
    #       this allows for appropriate indexing in main.py
    if freq == 'H':
        hrs = [int((date_range[0] - datetime.datetime(year=2017, month=1, day=1)).total_seconds() // 3600),
               int((date_range[-1] - datetime.datetime(year=2017, month=1, day=1)).total_seconds() // 3600)]
    # Generate resampled and interpolated data over the given date range        
    data = arr.resample(time=freq).interpolate('linear')[var].values[:, :, hrs[0]:hrs[1]+1]
    
    # Get length difference between latitude and longitude
    dim_diff = arr['lat'].values[:, 0].shape[0] - arr['lon'].values[0, :].shape[0]
    
    # Return a sliced set of latitude, longitude, and data arrays such that a square is generated
    if dim_diff > 0:
        return arr['lat'].values[:-dim_diff, 0], arr['lon'].values[0, :], data[:-dim_diff, :, :]
    elif dim_diff < 0:
        return arr['lat'].values[:, 0], arr['lon'].values[0, :-dim_diff], data[:, :-dim_diff, :]
    else:
        return arr['lat'].values[:, 0], arr['lon'].values[0, :], data

if __name__ == '__main__':    
    
    # True if troubleshooting this script alone
    troubleshooting = True
    if troubleshooting:
        # Coordinate of interest
        crd = [36.6058, -97.4888]
        # Half the width of the bound box
        res = 0.25
        # Date range of interest
        date_range = pd.date_range(start=datetime.datetime(year=2017, month=7, day=1),
                                   end=datetime.datetime(year=2017, month=12, day=31))
        # Variable of interest
        var = 'soil_moisture_1km'  
        
        lon, lat, data = main(crd, crd, date_range, var)
        plt.pcolormesh(lon, lat, data[:, :, 2])