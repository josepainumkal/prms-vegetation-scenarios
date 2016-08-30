"""
PRMS Vegetation Change Modeling API

Date: Feb 25 2016
"""
import datetime
import json
import math
import netCDF4
import os
import urllib2
import csv
import StringIO
import numpy as np

from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
from werkzeug import secure_filename
from flask import jsonify, request, Response, make_response, stream_with_context, render_template
from flask import current_app as app
from urllib import urlretrieve
from uuid import uuid4

from . import api
from ..models import Scenario, Hydrograph, Inputs, Outputs
from flask import session
from util import get_veg_map_by_hru, model_run_name, download_prms_inputs, find_user_folder, use_default_model_run, add_values_into_json, add_values_into_netcdf, get_nc_variable_name, get_chosen_param_data, gen_nc_frame_by_frame, get_nc_meta_data, download_prms_outputs, get_stat_var_name_list, get_stat_param_data
from PRMSCoverageTool import ScenarioRun


# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

# from flask_security.core import current_user
from flask.ext.security import current_user
import gc

class HruCells(object):
    def __init__(self,row,col):
        self.row=row
        self.col = col

    def dump(self):
        return [self.row,self.col]


@api.route('/api/get-chosen-parameter-details', methods=['GET'])
def getChosenParamDetails():
    if request.method == 'GET':
        chosenParam = request.args.get("chosenParam")
        resp = {}
        """generate json file from netcdf file"""

        BASE_PARAMETER_NC = find_user_folder() + app.config['TEMP_PARAM']
        handle = netCDF4.Dataset(BASE_PARAMETER_NC,'r')

        resp['chosenParam_name'] = chosenParam
        resp['chosenParam_maxVal'] = np.amax(handle[chosenParam][:].tolist())
        resp['chosenParam_minVal'] = np.amin(handle[chosenParam][:].tolist())

        if 'layer_desc' in handle[chosenParam].ncattrs():
            resp['layer_desc'] = handle[chosenParam].layer_desc

        return json.dumps(resp)



@api.route('/api/get-parameter-list', methods=['GET'])
def getParamList():
    if request.method == 'GET':
        """generate json file from netcdf file"""

        BASE_PARAMETER_NC = find_user_folder() + app.config['TEMP_PARAM']
        varList = []
        handle = netCDF4.Dataset(BASE_PARAMETER_NC,'r')
        for var in handle.variables:
            if handle.variables[var].size == 4704:
                varList.append(var) 
        varList.sort()
        handle.close()

        resp={}
        resp['param_list'] = varList
        return json.dumps(resp)


@api.route('/api/scenarios/metadata/<scenario_id>')
def metadata_scenario_by_id(scenario_id):
    '''
    only get meta data
    '''
    scenario = Scenario.objects(id=scenario_id).first()

    if scenario:
        return jsonify(scenario=scenario.to_json_simple())

    else:
        return Response(
            json.dumps(
                {'message': 'no scenario id found! ' +
                            'currently the scenario id must be 1 or 0!'}
            ), 400, mimetype='application/json'
        )


@api.route('/api/scenarios/<scenario_id>', methods=['GET', 'DELETE'])
def scenario_by_id(scenario_id):
    """
    Look up or delete a scenario by its id
    """
    if request.method == 'GET':

        scenario = Scenario.objects(id=scenario_id).first()

        if scenario:
            return jsonify(scenario=scenario.to_json())

        else:
            return Response(
                json.dumps(
                    {'message': 'no scenario id found! ' +
                                'currently the scenario id must be 1 or 0!'}
                ), 400, mimetype='application/json'
            )

    if request.method == 'DELETE':

        scenario = Scenario.objects(id=scenario_id).first()

        if scenario:

            try:
                scenario.delete()
                return jsonify(
                    message='scenario with id ' + scenario_id + ' removed!'
                )

            except:
                return Response(
                    json.dumps(
                        {'message': 'error deleting scenario ' + scenario_id}

                    ), 400, mimetype='application/json'
                )

        else:

            return Response(
                json.dumps(
                    {'message': 'scenario_id' + scenario_id + 'not found'}
                ), 400, mimetype='application/json'
            )


@api.route('/api/scenarios/finished_modelruns')
def display_modelruns():
    temp_list = model_run_name(
        auth_host=app.config['AUTH_HOST'],
        model_host=app.config['MODEL_HOST']
    )
    return temp_list

# this part handles the chosen three prms inputs
# post is for send the file meta data such as url
# get is for return the file info
# the url_info used this format: control_url---data_url---param_url


@api.route('/api/scenarios/download_input_files/<url_info>')
def download_model_inputs(url_info):
    url_list = url_info.split('---')
    control_url = url_list[0].replace('+++', '/')
    # app.logger.debug(control_url)
    data_url = url_list[1].replace('+++', '/')
    # app.logger.debug(data_url)
    param_url = url_list[2].replace('+++', '/')
    #app.logger.debug(param_url)
    #app.logger.debug('test here')
    # use the following function to download the three input files
    download_prms_inputs(control_url, data_url, param_url)
    return 'success'


@api.route('/api/defaul_model_run')
def prepare_default_model_run():
    use_default_model_run()
    return 'success'


@api.route('/api/return_hydro_info/<scenario_id>')
def return_hydro_info(scenario_id):
    '''
    This function is used to return all the hydro information
    '''
    # TODO extract hydro data based on id
    # the id is an list separate by ---
    final_csv_raw_data = []

    id_list = scenario_id.split('---')
    for temp_id in id_list:
        scenarios = Scenario.objects(id=temp_id).first()
        hydro_data_list = scenarios.hydrograph.streamflow_array
        hydro_time_list = scenarios.hydrograph.time_array

        final_csv_raw_data.append([temp_id, hydro_time_list, hydro_data_list])

    if len(hydro_time_list) != len(hydro_data_list):
        return 'time and data arrays are not the same length'
    else:
        # idea is from
        # http://stackoverflow.com/questions/28011341/create-and-download-a-csv-file
        def generate():
            data = StringIO.StringIO()
            w = csv.writer(data)

            # write header
            w.writerow(('timestamp', 'HydroValue'))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

            # write each log item
            # TODO this part final_csv_raw_data[0], coz create a csv file only based on
            # the first scenario
            for count in range(len(final_csv_raw_data[0][1])):
                w.writerow((
                    # format datetime as string
                    final_csv_raw_data[0][1][count].isoformat(),
                    final_csv_raw_data[0][2][count]
                ))
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)

        # add a filename
        headers = Headers()
        headers.set('Content-Disposition', 'attachment', filename='hydro.csv')

        # stream the response as the data is generated
        return Response(
            stream_with_context(generate()),
            mimetype='text/csv', headers=headers
        )


@api.route('/api/scenarios/metadata')
def metadata_all_scenarios():
    '''
    get the meta data only
    '''
    scenarios = Scenario.objects(user_id=current_user.id)

    final_list = []
    final_dict = {}

    for temp_item in scenarios:
        # temp_item is class Scenario
        final_list.append({'name': temp_item['name'], '_id': {'$oid': str(
            temp_item['id'])}, 'time_finished': str(temp_item['time_finished'])})

    final_dict = {'scenarios': final_list}
    return json.dumps(final_dict)


@api.route('/api/scenarios', methods=['GET', 'POST'])
def scenarios():
    """
    Handle get and push requests for list of all finished scenarios and submit
    a new scenario, respectively.
    """
    input_file_folder = find_user_folder()
    BASE_PARAMETER_NC = input_file_folder + app.config['TEMP_PARAM']
    if request.method == 'GET':

        scenarios = Scenario.objects(user_id=current_user.id)

        return jsonify(scenarios=scenarios)

    else:
        # assemble parts of a new scenario record
        vegmap_json = request.json['veg_map_by_hru']

        name = request.json['name']
        has_anim = False
        has_stat = False
        animation_url = ''
        stats_url = ''
        if 'animation_url' in request.json.keys():
            animation_url = request.json['animation_url']
            has_anim = True

        if 'stats_url' in request.json.keys():
            stats_url = request.json['stats_url']
            has_stat = True

        app.logger.debug('This is stats url:' + stats_url)
        # app.logger.debug('has_stat:' + str(has_stat))

        time_received = datetime.datetime.now()

        # XXX FIXME XXX
        # this gets confusing, but the scenario_run is for configuring and
        # running the model and the new_scenario is the Mongo record.
        # Issue #35
        # https://github.com/VirtualWatershed/prms-vegetation-scenarios/issues/35
        scenario_run = ScenarioRun(BASE_PARAMETER_NC)

        scenario_run.initialize(name)
        # should change here to transpose it back
        scenario_run.update_cov_type(vegmap_json['bare_ground'], 0)
        scenario_run.update_cov_type(vegmap_json['grasses'], 1)
        scenario_run.update_cov_type(vegmap_json['shrubs'], 2)
        scenario_run.update_cov_type(vegmap_json['trees'], 3)
        scenario_run.update_cov_type(vegmap_json['conifers'], 4)

        # close open netCDF
        scenario_run.finalize_run()

        new_scenario = Scenario(
            user_id=current_user.id,
            name=name,
            time_received=time_received,
            veg_map_by_hru=get_veg_map_by_hru(scenario_run.scenario_file)
        )

        new_scenario.save()

        modelserver_run = scenario_run.run(
            auth_host=app.config['AUTH_HOST'],
            model_host=app.config['MODEL_HOST']
        )

        # TODO placeholder
        time_finished = datetime.datetime.now()
        new_scenario.time_finished = time_finished

        resources = modelserver_run.resources

        control =\
            filter(lambda x: 'control' == x.resource_type, resources
                   ).pop().resource_url
        parameter =\
            filter(lambda x: 'param' == x.resource_type, resources
                   ).pop().resource_url
        data =\
            filter(lambda x: 'data' == x.resource_type, resources
                   ).pop().resource_url

        inputs = Inputs(control=control, parameter=parameter, data=data)
        new_scenario.inputs = inputs

        statsvar =\
            filter(lambda x: 'statsvar' == x.resource_type, resources
                   ).pop().resource_url

        outputs = Outputs(statsvar=statsvar)
        new_scenario.outputs = outputs

        if not os.path.isdir('.tmp'):
            os.mkdir('.tmp')

        tmp_statsvar = os.path.join('.tmp', 'statsvar-' + str(uuid4()))
        urlretrieve(statsvar, tmp_statsvar)

        d = netCDF4.Dataset(tmp_statsvar, 'r')
        # justin nc file has different name
        #cfs = d['sub_cfs_1'][:]
        cfs = d['basin_cfs_1'][:]

        t = d.variables['time']

        # need to subtract 1...bug in generation of statsvar b/c t starts at 1
        dates = netCDF4.num2date(t[:] - 1, t.units)

        hydrograph = Hydrograph(time_array=dates, streamflow_array=cfs)
        new_scenario.hydrograph = hydrograph

        new_scenario.save()

        # app.logger.debug('start download animation here')
        # download animation file here
        # TODO should download these two files separately
        if has_anim and has_stat:
            download_prms_outputs(animation_url, stats_url, new_scenario.get_id())

        # clean up temporary statsvar netCDF
        d.close()
        os.remove(tmp_statsvar)

        return jsonify(scenario=new_scenario.to_json())


@api.route('/api/access_token')
def get_user_access_token():
    '''
    This api get current user acccess token
    '''
    return session['api_token']


@api.route('/api/get_temperature')
def get_temperature():
    '''
    This api get current user model run temperature as a json file
    '''
    app_root = find_user_folder()
    data_file = app_root + app.config['TEMP_DATA']
    return add_values_into_json(data_file)


@api.route('/api/get_default_temperature')
def get_default_temperature():
    '''
    This api get current user default model run temperature as a json file
    '''
    app_root = find_user_folder()

    if not os.path.exists(app_root):
        os.mkdir(app_root)

    default_data_folder = app_root + '/../../data/'
    # app.logger.debug(default_data_folder)
    data_file = default_data_folder + app.config['DEFAULT_DATA']
    # app.logger.debug(data_file)

    return add_values_into_json(data_file)


@api.route('/api/apply_modified_json_temperature', methods=['POST'])
def apply_modified_temperature():
    '''
    This api change data.nc based on the json file
    no matter users use the default data.nc or data.nc from
    model run server, it is the same, coz util.use_default_model_run
    copy the default data.nc into the user's data folder
    '''
    # app_root = find_user_folder()

    # if not os.path.exists(app_root):
    #     os.mkdir(app_root)

    # default_data_folder = app_root + '/../../data/'
    # #app.logger.debug(default_data_folder)
    # data_file = default_data_folder + app.config['DEFAULT_DATA']
    # #app.logger.debug(data_file)
    if request.method == 'POST':
        app.logger.debug(type(request.json['temperature_values']))

        app_root = find_user_folder()
        data_file = app_root + app.config['TEMP_DATA']
        # let's see if update file can be overwritten
        add_values_into_netcdf(data_file, request, data_file)

        return 'success'


@api.route('/api/base-veg-map', methods=['GET'])
def hru_veg_json():
    if request.method == 'GET':
        """generate json file from netcdf file"""

        BASE_PARAMETER_NC = find_user_folder() + app.config['TEMP_PARAM']

        return jsonify(
            **json.loads(get_veg_map_by_hru(BASE_PARAMETER_NC).to_json())
        )


def _init_dev_db(BASE_PARAMETER_NC, scenario_num=0):
    """

    """
    name = 'Demo development scenario ' + str(scenario_num)
    time_received = datetime.datetime.now()

    updated_veg_map_by_hru = get_veg_map_by_hru(BASE_PARAMETER_NC)

    time_finished = datetime.datetime.now()

    inputs = Inputs()

    outputs = Outputs()

    # create two water years of fake data starting from 1 Oct 2010
    begin_date = datetime.datetime(2010, 10, 1, 0)
    time_array = [begin_date + datetime.timedelta(days=x) for x in
                  range(365 * 2)]

    # use simple exponentials as the prototype data
    x = range(365)
    streamflow_array = [
        pow(math.e, -pow(((i - 200.0 + 50 * scenario_num) / 100.0), 2))
        for i in x
    ]

    hydrograph = Hydrograph(
        time_array=time_array,
        streamflow_array=streamflow_array + streamflow_array
    )

    new_scenario = Scenario(
        name=name,
        user_id=current_user.id,
        time_received=time_received,
        time_finished=time_finished,
        veg_map_by_hru=updated_veg_map_by_hru,
        inputs=inputs,
        outputs=outputs,
        hydrograph=hydrograph
    )

    new_scenario.save()




@api.route('/api/netCDF/upload', methods=['POST'])
def upload():
    '''
    the function is basically from http://code.runnable.com/UiPcaBXaxGNYAAAL/how-to-upload-a-file-to-the-server-in-flask-for-python
    Route that will process the file upload
    # TODO upload file chunk by chunk, using this http://blog.pelicandd.com/article/80/streaming-input-and-output-in-flask
    '''
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is nc
    if file and (file.filename.split('.')[-1] == 'nc'):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        # Move the file form the temporal folder to
        # the upload folder we setup
        app_root = find_user_folder()
        if not os.path.exists(app_root):
            os.mkdir(app_root)
        file_location = app_root + app.config['TEMP_VIS']
        file.save(file_location)
        #app.logger.debug(get_nc_variable_name(file_location))
        param_list = get_nc_variable_name(file_location)
        return render_template('vis_netcdf.html', param_list=param_list)

@api.route('/api/netCDF_url/<animation_id>')
def download_nc(animation_id=''):
    '''
    the function is used to get the nc file based on url and return
    param list in the nc file
    TODO I should pass some useful information from post request and then
    dynamically get files in this step
    '''
    app_root = find_user_folder()
    if not os.path.exists(app_root):
        os.mkdir(app_root)
    file_location = app_root + app.config['TEMP_VIS'] + animation_id
    # file.save(file_location)
    #app.logger.debug(get_nc_variable_name(file_location))
    param_list = get_nc_variable_name(file_location)
    return render_template('vis_netcdf.html', param_list=param_list, scenario_id=animation_id)

@api.route('/api/netCDF_stat_url/<scenario_id>')
def download_stat_nc(scenario_id=''):
    '''
    '''
    # I am really confused why scenario_id is '' for the front end
    # return render_template('vis_stat.html', scenario_id=scenario_id)
    return render_template('vis_stat.html')

@api.route('/api/netCDF_stat_basic_data/<scenario_id>')
def get_stat_basic_data(scenario_id=''):
    '''
    This function return basic info of the stat nc file
    '''
    app_root = find_user_folder()
    if not os.path.exists(app_root):
        os.mkdir(app_root)
    file_location = app_root + app.config['TEMP_STAT'] + scenario_id
    param_list = get_stat_var_name_list(file_location)
    return param_list

@api.route('/api/netCDF_stat_data/<scenario_id>/<param_name>')
def obtain_stat_param_data(scenario_id='',param_name=''):
    '''
    This function return basic info of the stat nc file
    '''
    app_root = find_user_folder()
    if not os.path.exists(app_root):
        os.mkdir(app_root)
    file_location = app_root + app.config['TEMP_STAT'] + scenario_id
    param_val = get_stat_param_data(file_location,param_name)
    return param_val

@api.route('/api/get_chosen_data_by_frame/<param_name>/<start_frame>/<end_frame>/<scenario_id>')
def get_param_data_by_frame_num(param_name='',start_frame='',end_frame='',scenario_id=''):
    '''
    this part is used to get
    '''
    app_root = find_user_folder()
    file_location = app_root + app.config['TEMP_VIS'] + scenario_id
    return get_chosen_param_data(file_location,param_name,start_frame,end_frame)

@api.route('/api/get_chosen_data_stream/<param_name>/<scenario_id>')
def stream_param_data(param_name='',scenario_id=''):
    '''
    TODO
    This part does not work for now
    next() does not return next frame
    '''
    app_root = find_user_folder()
    file_location = app_root + app.config['TEMP_VIS'] + scenario_id
    return gen_nc_frame_by_frame(file_location,param_name).next()

@api.route('/api/get_chosen_metadata/<param_name>/<scenario_id>')
def get_param_metadat(param_name='',scenario_id=''):
    '''
    this function returns the metadata
    '''
    app_root = find_user_folder()
    file_location = app_root + app.config['TEMP_VIS'] + scenario_id
    return get_nc_meta_data(file_location,param_name)


@api.route('/api/test/user')
def test_user():
    '''
    this part is used to test the session working or not
    '''
    print current_user.is_authenticated()
    print current_user.name
    return str(current_user.is_authenticated()) + current_user.email


@api.route('/api/prmsparam_submit', methods=['POST'])
def prmsparam_submit():
    
    # code fix to avoid restarting container after every prms input ajax call
    gc.collect()

    paramList = request.json['paramList']
    changeParam = request.json['changeParam']
    changeToVal = float(request.json['changeToVal'])

    BASE_PARAMETER_NC = find_user_folder() + app.config['TEMP_PARAM']
    handle = netCDF4.Dataset(BASE_PARAMETER_NC,'a')
    
    hruList=[]
    temp_hruList =[]

    for i in xrange(49):
        for j in xrange(96):
            obj = HruCells(i,j)
            hruList.append(obj) 


    for bp in paramList:
        temp_hruList = hruList[:]

        arr_temp = handle.variables[bp['paramName']][:]
        low_limit = float(bp['lowLimit'])
        condition = bp['condition']

        if hasattr(bp, 'highLimit'):
            high_limit=float(bp['high_limit'])
        else:
            high_limit = 0
               

        if condition =="between":
            for i in temp_hruList:
                if arr_temp[i.row][i.col] <= low_limit  or arr_temp[i.row][i.col] >= high_limit:
                    hruList.remove(i)

        elif condition =="greater than":
            for i in temp_hruList:
                if arr_temp[i.row][i.col] <= low_limit:
                    hruList.remove(i)
        elif condition =="less than":
            for i in temp_hruList:
                if arr_temp[i.row][i.col] >= low_limit:
                    hruList.remove(i)
        elif condition =="equal to":
            for i in temp_hruList:
                if arr_temp[i.row][i.col] != low_limit:
                    hruList.remove(i)      


        # for i in temp_hruList:
        #     if condition =="between":
        #         if arr_temp[i.row][i.col] <= low_limit  or arr_temp[i.row][i.col] >= high_limit:
        #             hruList.remove(i)
        #     elif condition =="greater than":
        #         if arr_temp[i.row][i.col] <= low_limit:
        #             hruList.remove(i)
        #     elif condition =="less than":
        #         if arr_temp[i.row][i.col] >= low_limit:
        #             hruList.remove(i)
        #     elif condition =="equal to":
        #         if arr_temp[i.row][i.col] != low_limit:
        #             hruList.remove(i)        

    #forming the json string
    data = {}
    data['chosenHRU'] = [o.dump() for o in hruList]


    if len(data["chosenHRU"]) > 0 :
        temp=np.array([[None]*96]*49)
        for i in data["chosenHRU"]:
            temp[i[0]][i[1]] = changeToVal

        for i in xrange(49):
            for j in xrange(96):
                if temp[i][j] == None:
                   temp[i][j] = handle.variables[changeParam][:][i][j]

        handle.variables[changeParam][:] = temp
        # flash(json_data["chosenHRU"])
        # flash(handle.variables[changeParam][:])

    
    param_max = np.amax(handle.variables[changeParam][:].tolist())
    param_min = np.amin(handle.variables[changeParam][:].tolist())
    # total_num = len(handle.variables[changeParam][:])

    #Final repsonse sent on ajax call
    resp = {}
    resp['param_name'] = changeParam
    resp['param_max'] = param_max
    resp['param_min'] = param_min
    resp['modified_handle'] = handle.variables[changeParam][:].tolist()

    handle.close()
    return json.dumps(resp)

def get2DArrayIndex (gridValue):
	col = gridValue % 96
	row = gridValue / 96
	return row,col


@api.route('/api/updateToParamFile', methods=['POST'])
def updateToParamFile():
    gc.collect()
    BASE_PARAMETER_NC = find_user_folder() + app.config['TEMP_PARAM']
    handle = netCDF4.Dataset(BASE_PARAMETER_NC,'a')


    chosenAreaInfo = request.json['chosenAreaInfo']
    # app.logger.debug(chosenAreaInfo)
    # app.logger.debug(len(chosenAreaInfo))

    paramMap = {}
    paramValueMap ={}

    for i in chosenAreaInfo:
        paramName = i['paramName']
        paramVal = i['paramVal']
        gridNos = i['chosenArea']

        if paramName in paramMap:
            paramValueMap = paramMap[paramName]
            if paramVal in paramValueMap:
                paramValueMap[paramVal] = paramValueMap[paramVal] + gridNos
            else:
                paramValueMap[paramVal] = gridNos
        else:
            paramValueMap = {}
            paramValueMap[paramVal] = gridNos
            paramMap[paramName] = paramValueMap

        # app.logger.debug("printing parammaps***********************")
        # app.logger.debug(paramMap)


    #updating in the values of param handle
    for i in paramMap:
    	temp=np.array([[None]*96]*49)

        paramName = i
        valueMap = paramMap[i]
       
        for value in valueMap:
            gridNoList = valueMap[value]
            for g in gridNoList:
                row,col = get2DArrayIndex(g)
                # app.logger.debug("ROW COL")
                # app.logger.debug(row)
                # app.logger.debug(col)

                temp[row][col] = value

        for i in xrange(49):
            for j in xrange(96):
                if temp[i][j] == None:
                   temp[i][j] = handle.variables[paramName][:][i][j]

        handle.variables[paramName][:] = temp
        # app.logger.debug("HERE COMES MY TEMP")
        # app.logger.debug(temp)


    handle.close()

    # app.logger.debug("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFParam map i contructed is below")
    # app.logger.debug(paramMap)
    return "success"