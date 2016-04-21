import json
import netCDF4
import shutil


from numpy import where

from ..models import VegetationMapByHRU, ProjectionInformation

from client.model_client.client import ModelApiClient
from client.swagger_client.apis.default_api import DefaultApi

LEHMAN_CREEK_CELLSIZE = 100  # in meters; should be in netCDF, but it's not


def propagate_all_vegetation_changes(original_prms_params, veg_map_by_hru):
    """
    Given a vegetation_updates object and an original_parameters netcdf,
    propagate the updates through the original prms params netcdf and return
    an updated copy of the PRMS parameter netCDF

    Arguments:
        original_prms_params (netCDF4.Dataset): Base PRMS parameters for the
            watershed under investigation
        veg_map_by_hru (dict): Dictionary with structure
            {
                'bare_ground': [ (HRUs with bare_ground) ],
                'grasses': [ (HRUs with grasses) ],
                #  ... and so on with fields as given in app/models.py
            }

    Returns:
        (netCDF4.Dataset) netCDF Dataset with parameters updated according to
            the veg_map_by_hru
    """
    ret = original_prms_params
    return ret


def get_veg_map_by_hru(prms_params_file):
    """
    Create the vegetation map by HRU, which will also include the elevations
    in an array indexed by HRU.

    Arguments:
        prms_params (netCDF4.Dataset): PRMS parameters netCDF
    Returns:
        (VegetationMapByHRU): JSON representation of the vegetation and
            elevation by HRU
    """
    prms_params = netCDF4.Dataset(prms_params_file, 'r')
    # latitudes read from top to bottom
    upper_right_lat = prms_params.variables['lat'][:][0]
    lower_left_lat = prms_params.variables['lat'][:][-1]

    # longitudes get increasingly negative from right to left
    lower_left_lon = prms_params.variables['lon'][:][0]
    upper_right_lon = prms_params.variables['lon'][:][-1]

    ctv = prms_params.variables['cov_type'][:].flatten()

    projection_information = ProjectionInformation(
        ncol=prms_params.number_of_columns,
        nrow=prms_params.number_of_rows,
        xllcorner=lower_left_lon,
        yllcorner=lower_left_lat,
        xurcorner=upper_right_lon,
        yurcorner=upper_right_lat,
        cellsize=LEHMAN_CREEK_CELLSIZE
    )

    vegmap = VegetationMapByHRU(
        bare_ground=where(ctv == 0)[0].tolist(),
        grasses=where(ctv == 1)[0].tolist(),
        shrubs=where(ctv == 2)[0].tolist(),
        trees=where(ctv == 3)[0].tolist(),
        conifers=where(ctv == 4)[0].tolist(),

        projection_information=projection_information
    )

    # ret = json.loads(vegmap.to_json())
    # ret['elevation'] = prms_params.variables['hru_elev'][:].flatten().tolist()
    vegmap.elevation = prms_params.variables['hru_elev'][:].flatten().tolist()

    return vegmap

def model_run_name(auth_host=None, model_host=None,
        app_username=None, app_password=None):
    """
    the function is used to collect model run names
    """ 

    cl = ModelApiClient(auth_host=auth_host, model_host=model_host)
    cl.authenticate_jwt(username=app_username, password=app_password)

    api = DefaultApi(api_client=cl)

    # record all the model runs 
    model_run = api.search_modelruns().objects

    temp_list = [0] * len(model_run)

    for loop_count in range(len(temp_list)):
        temp_item = model_run[loop_count]
        # for current version, we only display finished model run
        if temp_item['progress_state'] =='FINISHED':
            temp_list[loop_count] = {'id':temp_item['id']}

    return json.dumps(temp_list)
