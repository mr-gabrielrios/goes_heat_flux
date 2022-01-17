# GOES Heat Flux Package
The objective of this package is to calculate sensible and latent heat fluxes (Q<sub>H</sub> and Q<sub>L</sub>, respectively) using data from the NASA/NOAA GOES-16 satellite. The code has been developed with a focus on urban areas, so there are likely to be additional factors in the algorithm(s) that may not be applicable to rural areas or other areas with heterogeneous land cover.

The geographical domain of this package is the continental United States. The temporal domain of this package is dependent on the availability of [GOES-16 ABI Level 2+ Land Surface Temperature](https://console.cloud.google.com/storage/browser/gcp-public-data-goes-16/ABI-L2-LSTC). Dates prior to 2018 are unlikely to have data. Also note that the land cover data used from the [2016 National Land Cover Database](https://www.mrlc.gov/data/nlcd-2016-land-cover-conus) is most accurate to model runs in the 2010s, especially in urban areas (due to urbanization and corresponding land cover changes).

**Update:** the paper cataloguing the model and its validation has been peer-reviewed and published in [Remote Sensing of Environment](https://doi.org/10.1016/j.rse.2021.112880).

## How do I use this?
This is more of a note for my future self than anyone else, because I can't imagine why someone else would use this.

0. Make sure you have Python (ideally version 3.0+) and all dependencies below installed
1. Clone the repo to your favorite local directory
2. Find `main.py` and customize the booleans in the post-processing section. This enables/disables animation and plot saving
3. Run `main.py` in your favorite console - I advise a console over your Terminal or Command Prompt to better accommodate user input functionality
4. Follow the commands in the console and get fluxed
5. Rinse, lather, repeat

## Technical description
This package uses Monin Obukhov similarity theory (abbreviated as MOST) (Monin and Obukhov, 1954) to provide a turbulence parameterization through which surface fluxes can be estimated. The intended scope of the package is limited to turbulent surface fluxes and associated parameters [e.g. atmospheric stability (&zeta;), friction velocity (`u*`)].

## Program flow
The program flow for this package is roughly described in the flowchart seen below. 

![GOES Heat Flux Package Flowchart](https://github.com/mr-gabrielrios/goes_heat_flux/blob/main/aux/goes_heat_flux_product_flowchart.png)

**Notes:** the `aux` folder is reserved for files used in the `README` file, so if you do use this repo, feel free to delete that.

## Sample outputs

![GOES Heat Flux Heatmap](https://github.com/mr-gabrielrios/goes_heat_flux/blob/main/aux/41.1_-74.35_40.3_-73.55_s2019-07-28%2005:00:00_e2019-07-29%2004:00:00.gif)
**Figure 1:** Sensible heat flux (Q<sub>H</sub>) in the New York City metropolitan area on 28 July 2019. Notice the stronger heat flux signals come through in the borough of Brooklyn and Queens and the urban agglomeration north of Newark (Paterson, Passaic, Clifton).

![GOES Heat Flux Timeseries](https://github.com/mr-gabrielrios/goes_heat_flux/blob/main/aux/timeseries_example.png)
**Figure 2:** Sensible heat flux (Q<sub>H</sub>) [subplot 1] and land surface and air temperatures [subplot 2] timeseries in Flatbush, Brooklyn from 26 to 28 July 2019.

## Known issues
* Underprediction of Q<sub>H</sub> during nocturnal hours. Likely a function of storage heat not being accounted for, investigation underway as of 2020/02/04.
* Occasional incompatibility between LST and air temperature data, where LST data exists for a given coordinate but air temperature does not appear

## Dependencies
This package is dependent on the following libraries:
* `cartopy`
* `csv`
* `datetime`
* `elevation`
* `glob`
* `google.cloud`
* `math`
* `matplotlib`
* `netCDF4`
* `numpy`
* `os`
* `pandas`
* `pyproj`
* `pytz`
* `re`
* `scipy`
* `shutil`
* `time`
* `timezonefinder`
* `urllib.request`
