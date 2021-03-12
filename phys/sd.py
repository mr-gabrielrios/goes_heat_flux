'''
Package:            GOES-16 Sensible Heat Flux Numerical Model
Script name:        Downward Shortwave Radiation
Package file path:  ~/phys/sd.py
Objective:          Read S_d from GOES-16 Level 2 product for each spatial pixel.
Author:             Gabriel Rios
'''

##############################################################################################
# BEGIN IMPORTS
##############################################################################################

# External imports
from netCDF4 import Dataset
from scipy import spatial
import datetime, numpy as np, os, pandas, pytz, sys, time, timezonefinder
import cartopy.crs as ccrs, matplotlib.pyplot as plt

##############################################################################################
# END IMPORTS
##############################################################################################

##############################################################################################
# Method name:      data_download
# Method objective: Download GOES-16 data from Google Cloud for selected time.
# Input(s):         domain center [list], date [datetime], bucket [Google Client object]
# Outputs(s):       goes_products [netCDF file object], goes_varnames [list]
##############################################################################################

def data_download(domain_center, date, bucket=None):
    # Create directory where temporary GOES netCDF file will be stored
    dir_name = 'goes_data'
    # If directory doesn't exist, make it
    if not os.path.isdir(os.path.join(os.path.dirname(__file__), dir_name)):
        os.mkdir(os.path.join(os.path.dirname(__file__), dir_name))
    goes_dir = os.path.join(os.path.dirname(__file__), dir_name)
    
    prod = 'DSR' # Level L-2 Product identifier
    product_ID = 'ABI-L2-' + prod + 'C/' # ABI, L2 product, CONUS
    
    goes_16_date_vec, goes_16_file_vec = [], []
    
    while goes_16_file_vec == []:
        yr = '{:0004d}'.format(date.year) 
        yday = '{:003d}'.format(date.timetuple().tm_yday)
        thour = '{:02d}'.format(date.hour)
        
        if bucket:        
            # this is the relative folder where the GOES-16 data will be
            prefix_16 = product_ID + yr + '/' + yday + '/' + thour 
            blobs_16 = bucket.list_blobs(prefix=prefix_16) # get all files in prefix
        
            for kk_16, blob_16 in enumerate(blobs_16): # loop through files
        
                if len(blob_16.name.split('_')) <= 5:
                    end_time_16 = blob_16.name.split('_')[4][1:-3]
                    end_datetime_16 = datetime.datetime.strptime(end_time_16,'%Y%j%H%M%S%f')
                else:
                    end_time_16 = blob_16.name.split('_')[4][1:]
                    end_datetime_16 = datetime.datetime.strptime(end_time_16,'%Y%j%H%M%S%f')
        
                goes_16_date_vec.append(end_datetime_16)
                goes_16_file_vec.append(blob_16)
            
                curr_filename = (goes_16_file_vec[0].name).split('/')[-1] # the the last file in search
                if os.path.isfile(goes_16_file_vec[0].name+curr_filename):
                    pass
                else:
                    # download the file to the local GOES-16 repository
                    (goes_16_file_vec[0]).download_to_filename(goes_dir+curr_filename)
                
                try:
                    # Load LST data
                    goes_product = Dataset(goes_dir+curr_filename) 
                    # Remove LST data from local directory
                    os.remove(goes_dir+curr_filename)
                except:
                    # If there was an error, remove the faulty file and re-download
                    os.remove(goes_dir+curr_filename) 
                    (goes_16_file_vec[0]).download_to_filename(goes_dir+curr_filename)
                    # Load LST data
                    goes_product = Dataset(goes_dir+curr_filename)
                    # Remove LST data from local directory
                    os.remove(goes_dir+curr_filename)
                
                goes_varnames = []
                for i in goes_product.variables:
                    # Get all variable names in GOES-16 file
                    goes_varnames.append(i)
            
        else:
            fdir = os.path.join(os.path.dirname(__file__), 'goes_data', 's_d')
            for file in os.listdir(fdir):
                if file.endswith(".nc"):
                    if len(file.split('_')) <= 5:
                        end_time_16 = file.split('_')[4][1:-3]
                        end_datetime_16 = datetime.datetime.strptime(end_time_16,'%Y%j%H%M%S%f')
                    else:
                        end_time_16 = file.split('_')[4][1:]
                        end_datetime_16 = datetime.datetime.strptime(end_time_16,'%Y%j%H%M%S%f')
                    goes_16_date_vec.append(end_datetime_16)
                    goes_16_file_vec.append(file)
            
            temp = []
            # Grab hourly DSR data only. To be updated if frequency is changed.
            for file in goes_16_file_vec:
                if date.strftime('%Y%j%H') == file.split('_e')[1][0:9]:
                    temp.append(os.path.join(fdir, file))
            
            # Try to grab the file associated with the current date
            # If an exception occurs, return None and let main() handle it
            try:
                # Load LST data
                goes_product = Dataset(temp[0]) 
                goes_varnames = []
                for i in goes_product.variables:
                    # Get all variable names in GOES-16 file
                    goes_varnames.append(i)        
                if goes_16_file_vec == []:
                    date = date - datetime.timedelta(hours=1) # if there are no files at that time, look an hour behind   
                return goes_product, goes_varnames
            
            except:
                goes_product, goes_varnames = None, None
                return goes_product, goes_varnames         

##############################################################################################
# Method name:      lst
# Method objective: Get land surface temperature from GOES-16 data for select pixel.
# Input(s):         goes_products [netCDF file object], goes_varnames [list], date [datetime], goes_idx [list]
# Outputs(s):       T_s [float]
##############################################################################################

def s_d(goes_product, goes_varnames, domain_center, domain, date):
    
    # Create 2D arrays with latitudes and longitudes
    lon, lat = np.meshgrid(goes_product['lon'][:].data, goes_product['lat'][:].data)
    # Define data grid
    data = goes_product.variables[goes_varnames[0]]
    
    # Initialize indices list for data grid
    goes_idx = []
    # Create 2 coordinates from the domain limits specified
    crds = [[domain[0], domain[2]], [domain[1], domain[3]]]
    for i, crd in enumerate(crds):
        index = spatial.cKDTree(np.c_[lat.ravel(), lon.ravel()]).query(crd)[1]
        loc = np.where((lat == lat.ravel()[index]) & (lon == lon.ravel()[index]))
        goes_idx.append(loc[0][0])
        goes_idx.append(loc[1][0])
    # Switch the index positions to correct positions
    goes_idx[0], goes_idx[2] = goes_idx[2], goes_idx[0]
    goes_idx[1], goes_idx[2] = goes_idx[2], goes_idx[1]
    
    # Get the actual data
    lat = (lat[goes_idx[0]:goes_idx[1], goes_idx[2]:goes_idx[3]])
    lon = (lon[goes_idx[0]:goes_idx[1], goes_idx[2]:goes_idx[3]])
    data = (data[goes_idx[0]:goes_idx[1], goes_idx[2]:goes_idx[3]]).data
    # Retrieve the data quality flag
    dqf = ((goes_product.variables[goes_varnames[1]])[goes_idx[0]:goes_idx[1], goes_idx[2]:goes_idx[3]]).data
    
    # Identify any water or non-clear/valid pixels and set to nan
    data[dqf != 0] = np.nan
    
    # If the dataset is full of nans, it is nighttime and downward shortwave can be assumed to be zero
    if np.sum(np.isnan(data)) == data.shape[0]*data.shape[1]:
        data = np.zeros(data.shape)
        
    return lat.ravel(), lon.ravel(), data

def main(domain, domain_center, date):
    goes_product, goes_varnames = data_download(domain_center, date, bucket=None)
    
    # If data is not found for this datetime, return none and let main.py handle it
    # Else, go ahead and extract data
    if goes_product is None and goes_varnames is None:
        print('DSRC file not found for {0}!'.format(date))
        lat, lon, data = [None, None, None]
    else:
        lat, lon, data = s_d(goes_product, goes_varnames, domain_center, domain, date)  
        
    return lat, lon, data

def mapper(goes_product, crd):
    fig, ax = plt.subplots(dpi=300, subplot_kw={'projection': ccrs.Orthographic(central_latitude=crd[0], central_longitude=crd[1])})
    
    pcm = ax.pcolormesh(goes_product.variables['lon'], goes_product.variables['lat'], goes_product.variables['DSR'], transform=ccrs.PlateCarree(), edgecolor='k')    
    fig.colorbar(pcm, ax=ax)
    
    ax.scatter(crd[1], crd[0], color='r', transform=ccrs.PlateCarree())
    ax.set_extent([crd[1]-5, crd[1]+5, crd[0]-5, crd[0]+5])
    ax.coastlines()
    ax.set_title(goes_product.time_coverage_end)
    
    gl = ax.gridlines(draw_labels=True)    
    gl.top_labels, gl.right_labels = False, False
    
if __name__ == '__main__':
    # Test to see if LST algorithm is working properly
    def gcp_bucket():
        from google.cloud import storage
        
        # Reference local Google Credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'GOOGLE_AUTH_CREDS.json'))
        # Start the storage client
        client = storage.Client() 
        # Call the GOES-16 storage bucket
        bucket = client.get_bucket('gcp-public-data-goes-16') 
    
        return bucket
    
    bucket = gcp_bucket()
    domain_center = [36.6058, -97.4888]
    domain = [36.1058, 37.1058, -97.9888, -96.9888]
    date_range = [datetime.datetime(year=2017, month=10, day=20, hour=8),
                  datetime.datetime(year=2017, month=10, day=20, hour=12)-datetime.timedelta(hours=1)]    
    date_range = pandas.date_range(start=date_range[0], end=date_range[1], freq='H') 
    for date in date_range:
        print(date)
        goes_product, goes_varnames = data_download(domain_center, date, bucket=None)
        mapper(goes_product, domain_center)
        lat, lon, data = s_d(goes_product, goes_varnames, domain_center, domain, date)