# GOES Heat Flux Package
The objective of this package is to calculate sensible and latent heat fluxes (Q<sub>H</sub> and Q<sub>L</sub>, respectively) using data from the NASA/NOAA GOES-16 satellite. 

# Known Issues
* Occasional incompatibility between LST and air temperature data, where LST data exists for a given coordinate but air temperature does not appear

## Dependencies
This package is dependent on the following libraries:
* 'cartopy'
* 'csv'
* 'datetime'
* 'elevation'
* 'glob'
* 'google.cloud'
* 'math'
* 'matplotlib'
* 'netCDF4'
* 'numpy'
* 'os'
* 'pandas'
* 'pyproj'
* 'pytz'
* 're'
* 'scipy'
* 'shutil'
* 'time'
* 'timezonefinder'
* 'urllib.request'