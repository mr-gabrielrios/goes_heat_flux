'''
Package:            GOES-16 Sensible Heat Flux Numerical Model
Script name:        Downscaling
Package file path:  ~/grid/downscaling.py
Objective:          Implement downscaling algorithm to increase spatial resolution of GOES-16 Land Surface Temperature data
Author:             Gabriel Rios
Notes:              Working file
'''

import rasterio
import numpy as np
import matplotlib.pyplot as plt


### Landsat data retrieval - to be used for validating downscaling algorithm
# Create reference to Landsat .tif file and for a target CSV file
data_path = 'aux/LC08_L2SP_013032_20200512_20200820_02_T1_ST_B10.TIF'
target = data_path.split('.')[0] + '.csv'
# Import tif file and save it to a variable
landsat_data = rasterio.open(data_path)
# np.savetxt(target, landsat_data.read(1), delimiter=',')

