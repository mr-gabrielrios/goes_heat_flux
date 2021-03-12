'''
Package:            GOES-16 Sensible Heat Flux Numerical Model
Script name:        Meshgrid Plotter - Subplots
Package file path:  ~/plot/meshgrid_subplots.py
Objective:          Plot gridded data onto corresponding 2D map with subplot functionality
                    enabled for different timeframes to be shown on one figure.
Author:             Gabriel Rios
'''

##############################################################################################
# BEGIN IMPORTS
##############################################################################################

import cartopy.crs as ccrs, cartopy.io.img_tiles as cimgt, datetime, numpy as np, matplotlib, matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker

##############################################################################################
# END IMPORTS
##############################################################################################

##############################################################################################
# Method name:      base
# Method objective: Provide general formatting and projection settings to the 2D plots.
# Input(s):         domain [list], domain_center [list], zoom [float]
# Outputs(s):       matplotlib objects [fig, ax, projection]
##############################################################################################

def base(domain, domain_center, zoom, font_size):
    
    # Define projections for the base map
    proj_pc = ccrs.PlateCarree()
    proj_ortho = ccrs.Orthographic(central_latitude=domain_center[0], central_longitude=domain_center[1])
    fig, ax = plt.subplots(nrows=2, ncols=2, subplot_kw={'projection': proj_ortho}, dpi=300)
    # Limit the extent of the map to a small longitude/latitude range
    for i, axs in enumerate(ax.flatten()):
        axs.set_extent([domain[2] - zoom, domain[3] + zoom, domain[0] - zoom, domain[1] + zoom])
        axs.coastlines()
    
    # Add the satellite background data at zoom level 12.
    # sat_img = cimgt.GoogleTiles(style='satellite')
    # ax.add_image(sat_img, 12)

        # Draw and format gridlines
        gl = axs.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.1, linestyle='--')
        gl.xlabel_style, gl.ylabel_style = {'fontsize': font_size['plot_ticks']}, {'fontsize': font_size['plot_ticks']}
        if i == 0:
            gl.top_labels, gl.left_labels, gl.bottom_labels, gl.right_labels = False, True, False, False
        if i == 1:
            gl.top_labels, gl.left_labels, gl.bottom_labels, gl.right_labels = False, False, False, False
        if i == 2:       
            gl.top_labels, gl.left_labels, gl.bottom_labels, gl.right_labels = False, True, True, False
        if i == 3:
            gl.top_labels, gl.left_labels, gl.bottom_labels, gl.right_labels = False, False, True, False
        gl.xpadding = 20
        gl.ypadding = 20
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER        
        gl.xlocator = mticker.FixedLocator([-74.2, -73.8])
        gl.ylocator = mticker.FixedLocator([40.5, 40.7, 40.9])

    fig.tight_layout()

    return fig, ax, proj_pc

##############################################################################################
# Method name:      gridded_data
# Method objective: Define data to be plotted along with corresponding formatting.
# Input(s):         domain [list], domain_center [list], date [datetime or list], 
#                   lats [2D NumPy array], lons [2D NumPy array], data [2D or 3D array], 
#                   var [str], animated [bool]
# Outputs(s):       plot or .gif file
##############################################################################################

def gridded_data(domain, domain_center, date, lats, lons, data, data_limits, var, zoom=0.1, animated=False, savefig=False):
    
    matplotlib.rcParams['font.family'] = 'FreeSans'
    font_size = {'title': 13,
                 'subtitle': 10,
                 'plot_ticks': 10,
                 'axes_label': 10}
    
    # Define padding around data for map
    fig, ax, proj_pc = base(domain, domain_center, zoom, font_size)
    
    # Colormap definition
    # Logic: Color negative fluxes blue (to represent cooling), positive fluxes red (heating), net zero white
    if data_limits[0] < 0 and data_limits[1] > 0:
        norm = matplotlib.colors.TwoSlopeNorm(vmin=data_limits[0], vcenter=0, vmax=data_limits[1])
        cmap = plt.cm.get_cmap('RdBu_r')
    elif data_limits[0] < 0 and data_limits[1] < 0:
        norm = matplotlib.colors.Normalize(vmin=data_limits[0], vmax=0)
        cmap = plt.cm.get_cmap('Blues_r')
    else:
        norm = matplotlib.colors.Normalize(vmin=0, vmax=data_limits[1])
        cmap = plt.cm.get_cmap('Reds_r')
    
    # Plot the data
    # Note that pcolormesh data dimensions must 1 smaller along each axis than the X and Y arrays.
    for i, ax_ in enumerate(fig.axes):
        im = ax_.pcolormesh(lons, lats, data[i][:-1, :-1], cmap=cmap, norm=norm, transform=proj_pc)
        subtitle_str = '{0} UTC'.format(date[i].strftime('%H:%M'))
        ax_title = ax_.set_title(subtitle_str, fontsize=font_size['subtitle'])
     
    fig.subplots_adjust(right=0.8)
    cax = fig.add_axes([0.7, 0.035, 0.025, 0.93])  
    colorbar = fig.colorbar(im, pad=0.01, cax=cax)
    colorbar.set_label('${0}$ [${1}$]'.format(var['name'], var['units']))    
    colorbar.set_label('${0}$ [${1}$]'.format(var['name'], var['units']), fontsize=font_size['axes_label']+2, rotation=270, labelpad=15)
    colorbar.ax.tick_params(labelsize=font_size['axes_label']) 
    
    # Figure title formatting
    title_str = '{0}'.format(var['full_name'])
    # Note: value used for x-position centers the figure title relative to the subplot
        
    fig.subplots_adjust(hspace=0.175, wspace=-0.5)
    
    return fig, ax

##############################################################################################
# Method name:      main
# Method objective: Control sequencing and relaying of plot data.
# Input(s):         domain [list], domain_center [list], date_range [datetime or list], 
#                   lats [2D NumPy array], lons [2D NumPy array], var [str], metadata [dict], 
#                   zoom [float], animated [bool]
# Outputs(s):       plot or .gif file
##############################################################################################

def main(domain, domain_center, date_range, lats, lons, var, metadata, zoom=0.0, animated=False, savefig=False):
    # Grab variable of interest from global variables collection.
    grid_data = var
    # Define absolute data limits over timeseries for coloring purposes
    data_limits = [np.nanmin(grid_data), np.nanmax(grid_data)]
    # Define depth of the gridded data matrix
    z = grid_data.shape[2]
    # If animation chosen, plot using this function. Else, use iterative prodecure below.
    data = [grid_data[:, :, 9], 
            grid_data[:, :, 12], 
            grid_data[:, :, 15],
            grid_data[:, :, 18]]
    dates = [date_range[9],
             date_range[12],
             date_range[15],
             date_range[18]]
    datamap = gridded_data(domain, domain_center, dates, lats, lons, data, data_limits, metadata, zoom=0.00)