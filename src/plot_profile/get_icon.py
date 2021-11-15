"""Purpose: Get data from icon simulation.

Author: Stephanie Westerhuis

Date: 11/11/2021
"""

# Standard library
import subprocess  # use: run command line commands from python
from io import StringIO
from pathlib import Path

# Third-party
# import ipdb
import numpy as np
import pandas as pd
import xarray as xr
from click.decorators import option


def lfff_name(lt):
    """Create mch-filename for icon ctrl run for given leadtime.

    Args:
        lt (int): leadtime

    Returns:
        str: filename of icon output simulation in netcdf, following mch-convention

    """
    hour = int(lt) % 24
    day = (int(lt) - hour) // 24
    remaining_s = round((lt - int(lt)) * 3600)
    sec = int(remaining_s % 60)
    mm = int((remaining_s - sec) / 60)

    return f"lfff{day:02}{hour:02}{mm:02}{sec:02}.nc"


def ind_from_latlon(lats, lons, lat, lon, verbose=False):
    """Find the nearest neighbouring index to given location.

    Args:
        lats (2d array):            Latitude grid
        lons (2d array):            Longitude grid
        lat (float):                Latitude of location
        lon (float):                Longitude of location
        verbose (bool, optional):   Print information. Defaults to False.

    Returns:
        int     Index of nearest grid point.

    """
    dist = [
        np.sqrt((lats[i] - lat) ** 2 + (lons[i] - lon) ** 2) for i in range(len(lats))
    ]
    ind = np.where(dist == np.min(dist))[0][0]

    if verbose:
        print(f"Closest ind: {ind}")
        print(f" Given lat: {lat:.3f} vs found lat: {lats[ind]:.3f}")
        print(f" Given lat: {lon:.3f} vs found lon: {lons[ind]:.3f}")

    return ind


def get_icon(folder, leadtime, lat, lon, ind, grid, var, alt_bot, alt_top):
    """Retrieve vertical profile of variable from icon simulation.

    Args:
        folder (str):           here are the icon simulation output files
        leadtime (list of int): simulation leadtime(s)
        lat (float):            latitude of location
        lon (float):            longitude of location
        ind (int):              index of location
        grid (str):             icon grid file containing HEIGHT field
        var (str):              variable name in icon file
        alt_bot (int):          lower boundary of plot
        alt_top (int):          upper boundary of plot

    Returns:
        pandas dataframe:       icon simulation values

    """
    df = pd.DataFrame()
    print(folder)

    # list icon files
    files = [Path(folder, lfff_name(lt)) for lt in leadtime]

    # load as xarray dataset
    ds = xr.open_mfdataset(files).squeeze()

    # extract latitude and longitude
    lats = ds.clat_1.values
    lons = ds.clon_1.values

    # convert from radians to degrees if given in radians
    if lats.max() < 2.0 and lons.max() < 2.0:
        print("assuming that lats and lons are given in radians")
        lats = np.rad2deg(lats)
        lons = np.rad2deg(lons)

    # find index closest to specified lat, lon
    ind = ind_from_latlon(lats, lons, lat, lon, True)

    # load constants file
    if Path(grid).is_file():
        ds_const = xr.open_dataset(grid).squeeze()
    else:
        print("grid file does not exist!")

    # load latitude and longitude grid of constants file
    lats_const = ds_const.clat.values
    lons_const = ds_const.clon.values

    # convert from radians to degrees if given in radians
    if lats_const.max() < 2.0 and lons_const.max() < 2.0:
        print("assuming that lats and lons are given in radians")
        lats_const = np.rad2deg(lats_const)
        lons_const = np.rad2deg(lons_const)

    if ds.cells_1.size != ds_const.cell.size:
        print("Attention: Size of output and grid file does not match!")

    print("Latitude and logitude of selected index in grid file:")
    print(f"{lats_const[ind]:.2f}, {lons_const[ind]:.2f}")

    # ipdb.set_trace()
    # subselect column
    # dss = ds.isel(cells_1=ind)

    return df
