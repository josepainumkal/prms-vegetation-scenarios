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

from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
from flask import jsonify, request, Response, make_response, stream_with_context
from flask import current_app as app
from urllib import urlretrieve
from uuid import uuid4

from . import api
from ..models import Scenario, Hydrograph, Inputs, Outputs
from flask import session
from util import get_veg_map_by_hru, model_run_name, download_prms_inputs, find_user_folder, use_default_model_run, add_values_into_json, add_values_into_netcdf
from PRMSCoverageTool import ScenarioRun

# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

# from flask_security.core import current_user
from flask.ext.security import current_user

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
    app.logger.debug(param_url)
    app.logger.debug('test here')
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
        # idea is from http://stackoverflow.com/questions/28011341/create-and-download-a-csv-file
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
                    final_csv_raw_data[0][1][count].isoformat(), # format datetime as string
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
        


@api.route('/api/scenarios', methods=['GET', 'POST'])
def scenarios():
    """
    Handle get and push requests for list of all finished scenarios and submit
    a new scenario, respectively.
    """
    input_file_folder = find_user_folder()
    BASE_PARAMETER_NC = input_file_folder + app.config['TEMP_PARAM']
    if request.method == 'GET':

        scenarios = Scenario.objects

        # this is for the first three scenarios only
        if app.config['DEBUG'] and len(scenarios) < 3:
            for loop_counter in range(3):
                _init_dev_db(BASE_PARAMETER_NC, loop_counter)

                scenarios = Scenario.objects

        return jsonify(scenarios=scenarios)

    else:
        # assemble parts of a new scenario record
        vegmap_json = request.json['veg_map_by_hru']

        name = request.json['name']

        time_received = datetime.datetime.now()

        # XXX FIXME XXX
        # this gets confusing, but the scenario_run is for configuring and
        # running the model and the new_scenario is the Mongo record.
        # Issue #35
        # https://github.com/VirtualWatershed/prms-vegetation-scenarios/issues/35
        scenario_run = ScenarioRun(BASE_PARAMETER_NC)

        scenario_run.initialize(name)

        scenario_run.update_cov_type(vegmap_json['bare_ground'], 0)
        scenario_run.update_cov_type(vegmap_json['grasses'], 1)
        scenario_run.update_cov_type(vegmap_json['shrubs'], 2)
        scenario_run.update_cov_type(vegmap_json['trees'], 3)
        scenario_run.update_cov_type(vegmap_json['conifers'], 4)

        # close open netCDF
        scenario_run.finalize_run()

        new_scenario = Scenario(
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
        cfs = d['basin_cfs_1'][:]

        t = d.variables['time']

        # need to subtract 1...bug in generation of statsvar b/c t starts at 1
        dates = netCDF4.num2date(t[:] - 1, t.units)

        hydrograph = Hydrograph(time_array=dates, streamflow_array=cfs)
        new_scenario.hydrograph = hydrograph

        new_scenario.save()

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
    #app.logger.debug(default_data_folder)
    data_file = default_data_folder + app.config['DEFAULT_DATA']
    #app.logger.debug(data_file)

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

        BASE_PARAMETER_NC = find_user_folder() + '/temp_param.nc'

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
        time_received=time_received,
        time_finished=time_finished,
        veg_map_by_hru=updated_veg_map_by_hru,
        inputs=inputs,
        outputs=outputs,
        hydrograph=hydrograph
    )

    new_scenario.save()

# this part is used to test the session working or not
@api.route('/api/test/user')
def test_user():
    print current_user.is_authenticated()
    print current_user.name
    return str(current_user.is_authenticated()) + current_user.email