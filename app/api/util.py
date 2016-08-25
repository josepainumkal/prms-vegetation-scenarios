import json
import netCDF4
import shutil
import urllib
import os
import datetime
import os.path

from dateutil.rrule import rrule, DAILY
from numpy import where
import numpy

from ..models import VegetationMapByHRU, ProjectionInformation

from flask import current_app as app
from flask import session
from flask.ext.security import current_user

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


#model_run = 0
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

    # temp_veg = numpy.transpose(prms_params.variables['cov_type'][:])
    temp_veg = prms_params.variables['cov_type'][:]
    ctv = temp_veg.flatten()

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


def model_run_name(auth_host=None, model_host=None):
    """
    the function is used to collect model run names
    """

    cl = ModelApiClient(api_key=session['api_token'],auth_host=auth_host, model_host=model_host)

    api = DefaultApi(api_client=cl)

    # record all the model runs
    model_run = api.search_modelruns().objects

    temp_list = [0] * len(model_run)

    for loop_count in range(len(temp_list)):
        temp_item = model_run[loop_count]
        # for current version, we only display finished model run
        if temp_item['progress_state'] == 'FINISHED':
            temp_list[loop_count] = {'id': temp_item['id']}

    return json.dumps(temp_list)


def find_user_folder():
    username = current_user.email
    # get the first part of username as part of the final file name
    username_part = username.split('.')[0]
    app_root = os.path.dirname(os.path.abspath(__file__))
    app_root = app_root + '/../static/user_data/' + username_part
    return app_root


def use_default_model_run():
    app_root = find_user_folder()

    if not os.path.exists(app_root):
        os.mkdir(app_root)

    default_data_folder = app_root + '/../../data/'

    data_file = app_root + app.config['TEMP_DATA']
    control_file = app_root + app.config['TEMP_CONTROL']
    param_file = app_root + app.config['TEMP_PARAM']
    # copy the default file
    shutil.copyfile(default_data_folder +
                    app.config['DEFAULT_CONTROL'], control_file)
    shutil.copyfile(default_data_folder +
                    app.config['DEFAULT_DATA'], data_file)
    shutil.copyfile(default_data_folder +
                    app.config['DEFAULT_PARAM'], param_file)

    # change permission
    #os.chmod(param_file, 0666)


def download_prms_inputs(control_url, data_url, param_url):
    app_root = find_user_folder()

    if not os.path.exists(app_root):
        os.mkdir(app_root)

    # TODO clean the previous download input files
    data_file = app_root + app.config['TEMP_DATA']
    control_file = app_root + app.config['TEMP_CONTROL']
    param_file = app_root + app.config['TEMP_PARAM']

    # clean up previous download file
    if os.path.isfile(data_file):
        os.remove(data_file)

    if os.path.isfile(control_file):
        os.remove(control_file)
        
    if os.path.isfile(param_file):
        os.remove(param_file)

    # download three inputs file based on the urls
    urllib.urlretrieve(control_url, control_file)
    urllib.urlretrieve(data_url, data_file)
    urllib.urlretrieve(param_url, param_file)

    # change permisson
    #os.chmod(param_file, 0666)


    app.logger.debug(
        'User: ' + current_user.email + ' finished downloading three input files')

def download_prms_outputs(animation_url, stats_url, scenario_id):
    '''
    current version only download animation file
    '''
    app_root = find_user_folder()

    if not os.path.exists(app_root):
        os.mkdir(app_root)

    animation_file = app_root + app.config['TEMP_VIS'] + scenario_id
    stats_file = app_root + app.config['TEMP_STAT'] + scenario_id

    # clean up previous download file
    if os.path.isfile(animation_file):
        os.remove(animation_file)

    if os.path.isfile(stats_file):
        os.remove(stats_file)

    # retrieve url
    animation_url = animation_url.replace('+++', '/')
    stats_url = stats_url.replace('+++', '/')

    # download three inputs file based on the urls
    urllib.urlretrieve(animation_url, animation_file)
    urllib.urlretrieve(stats_url, stats_file)

    app.logger.debug(
        'User: ' + current_user.email + ' finished downloading animation and stats files')


# lisa's function, grab temperature from data.nc
# Rui modified it a little bit to fit current version program
def add_values_into_json(input_data_nc):

    variableList = []

    fileHandle = netCDF4.Dataset(input_data_nc, 'r')
    
    # Extract number of time steps
    dimensions = [dimension for dimension in fileHandle.dimensions] 
    if 'time' in dimensions:
        numberOfTimeSteps = len(fileHandle.dimensions['time'])

    # extract tmax and tmin variables and append to a list
    variables = [variable for variable in fileHandle.variables]
    
    if 'tmin' in variables:
        variableList.append('tmin')
    if 'tmax' in variables:
        variableList.append('tmax')
        
    for index in range(len(variables)):
        if '_' in variables[index]:
            position = variables[index].find('_')
            if 'tmax' in variables[index][0:position] or 'tmin' in variables[index][0:position]:
                variableList.append(variables[index])

    valueList = []
    for index in range(len(variableList)):
        valueList.append([])

    for index in range(len(variableList)):
        valueList[index] = fileHandle.variables[variableList[index]][:].flatten().tolist()
    
    varValues = {}

    for index in range(len(variableList)):
        varValues[variableList[index]] = valueList[index]

    # Find time step values

    timeStepValues = []

    for variable in fileHandle.variables:
        if variable == 'time':
    
            units = str(fileHandle.variables[variable].units)
            startDate = units.rsplit(' ')[2]
            startYear = int(startDate.rsplit('-')[0].strip())
            startMonth = int(startDate.rsplit('-')[1].strip())
            startDay = int(startDate.rsplit('-')[2].strip())
            shape = str(fileHandle.variables[variable].shape)
            numberOfValues = int(shape.rsplit(',')[0].strip('('))
            endDate = str(datetime.date (startYear, startMonth, startDay) + datetime.timedelta (days = numberOfValues-1))
            endYear = int(endDate.rsplit('-')[0].strip())
            endMonth = int(endDate.rsplit('-')[1].strip())
            endDay = int(endDate.rsplit('-')[2].strip())

    startDate = datetime.date(startYear, startMonth, startDay)
    endDate = datetime.date(endYear, endMonth, endDay)

    for dt in rrule(DAILY, dtstart=startDate, until=endDate):
        #timeStepValues.append(dt.strftime("%Y %m %d 0 0 0"))
        timeStepValues.append(dt.strftime("%Y-%m-%dT00:00:00"))
    
    data = { 
              'temperature_values': varValues, \
              'timestep_values': timeStepValues \
           }
    
    fileHandle.close()

    return json.dumps(data)

def add_values_into_netcdf(original_nc, post_data, update_file):
    '''
    this function is bascially from Lisa, Rui changed it to fit the post request from
    the client side
    '''
    temperature = post_data.json['temperature_values']


    fileHandle = netCDF4.Dataset(original_nc, mode='a')

    for index in range(len(temperature.keys())):
        fileHandle.variables[temperature.keys()[index]][:] = \
        temperature[temperature.keys()[index]]

    shutil.move(original_nc, update_file)

    
    fileHandle.close()

# this function is used to get all the variable named
# and the variable should have as many elements as the hru num
def get_nc_variable_name(filename):
    var_name_list = []
    netcdf_aim_file = netCDF4.Dataset(filename,'r')
    # TODO find a better way to get row and col
    lat_num = netcdf_aim_file['lat'].shape[0]
    lon_num = netcdf_aim_file['lon'].shape[0]
    for temp_var in netcdf_aim_file.variables.values():
        # check if the variable is the same size with hru map
        if hasattr(temp_var,'shape'):
            total_len = 1
            for i in temp_var.shape:
                total_len = total_len * i
            # using this method to check if the size is the same with hru map 
            if total_len%(lat_num*lon_num)==0:
                var_name_list.append(temp_var.name)
    netcdf_aim_file.close()
    return var_name_list


def get_chosen_param_data(filename,param_name,start_frame,end_frame):
    '''
    # this function is used to get the data
    # start frame starts from 0
    # end frame ends len-1
    '''
    netcdf_aim_file = netCDF4.Dataset(filename,'r')
    chosen_data_list = netcdf_aim_file[param_name]
    if int(start_frame) < 0:
        raise Exception("start frame number is less than 0")
        return
    elif int(end_frame)>=len(chosen_data_list):
        raise Exception("end frame number is more than maximum")
        return
    elif int(end_frame)<int(start_frame):
        raise Exception("end frame number is smaller than start frame number")
        return
    # TODO make it general use
    # for current version the format of each chosen param is
    # [framenum][lat][lon]
    temp_list = chosen_data_list[int(start_frame):(int(end_frame)+1)].tolist()
    
    upload_data = { 
              'param_data':temp_list \
           }

    netcdf_aim_file.close()

    return json.dumps(upload_data)


def gen_nc_frame_by_frame(filename,param_name):
    '''
    this function generates data frame by frame
    '''
    netcdf_aim_file = netCDF4.Dataset(filename,'r')
    chosen_data_list = netcdf_aim_file[param_name]

    for i in chosen_data_list[:]:
        upload_data = { 
              'param_data': i.tolist() \
           }
        yield json.dumps(upload_data)
    # TODO if i close the file here, then it will have some errors
    # need to study where to close the file
    # netcdf_aim_file.close()

def get_nc_meta_data(filename,param_name):
    '''
    return chosen param meta data
    '''
    netcdf_aim_file = netCDF4.Dataset(filename,'r')
    chosen_data_list = netcdf_aim_file[param_name]
    param_max = numpy.amax(chosen_data_list[:])
    param_min = numpy.amin(chosen_data_list[:])
    lat_num = netcdf_aim_file['lat'].shape[0]
    lon_num = netcdf_aim_file['lon'].shape[0]
    total_num = len(chosen_data_list)
    upload_data = { 
          'row_num': lat_num, \
          'col_num': lon_num, \
          'total_num': total_num, \
          'param_max': param_max, \
          'param_min': param_min \
       }
    netcdf_aim_file.close()
    return json.dumps(upload_data)

def get_stat_var_name_list(filename):
    '''
    This function gets the var name list
    all the var should be the same size with time
    '''
    netcdf_aim_file = netCDF4.Dataset(filename,'r')
    time_shape = netcdf_aim_file['time'].shape[0]

    var_name_list = []

    for temp_var in netcdf_aim_file.variables.values():
        # check if the variable is the same size with time
        if hasattr(temp_var,'shape'):
            if temp_var.shape[0] == time_shape:
                var_name_list.append(temp_var.name)

    # netcdf_aim_file.variables.values()[0].shape[0]

    upload_data = { 
              'time': netcdf_aim_file['time'][:].tolist(), \
              'param_data':var_name_list \
           }

    netcdf_aim_file.close()

    return json.dumps(upload_data)

def get_stat_param_data(filename,param_name):
    '''
    This function is used to get param values
    '''
    netcdf_aim_file = netCDF4.Dataset(filename,'r')

    upload_data = {               
              'param_data':netcdf_aim_file[param_name][:].tolist() \
           }

    netcdf_aim_file.close()

    return json.dumps(upload_data)