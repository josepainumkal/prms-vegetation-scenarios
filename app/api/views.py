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

from flask import jsonify, request, Response
from flask import current_app as app
from urllib import urlretrieve
from uuid import uuid4

from . import api
from ..models import Scenario, Hydrograph, Inputs, Outputs
from util import get_veg_map_by_hru, model_run_name, download_prms_inputs, find_user_folder
from PRMSCoverageTool import ScenarioRun


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
            model_host=app.config['MODEL_HOST'],
            app_username=app.config['APP_USERNAME'],
            app_password=app.config['APP_PASSWORD']
        )
    return temp_list

# this part handles the chosen three prms inputs
# post is for send the file meta data such as url
# get is for return the file info
# the url_info used this format: control_url---data_url---param_url
@api.route('/api/scenarios/download_input_files/<url_info>')
def download_model_inputs(url_info):
    url_list = url_info.split('---')
    control_url = url_list[0].replace('+++','/')
    #app.logger.debug(control_url)
    data_url = url_list[1].replace('+++','/')
    #app.logger.debug(data_url)
    param_url = url_list[2].replace('+++','/')
    #app.logger.debug(param_url)
    # use the following function to download the three input files
    download_prms_inputs(control_url, data_url, param_url)
    return 'success'
    

@api.route('/api/scenarios', methods=['GET', 'POST'])
def scenarios():
    """
    Handle get and push requests for list of all finished scenarios and submit
    a new scenario, respectively.
    """
    input_file_folder = find_user_folder()
    BASE_PARAMETER_NC = input_file_folder + '/temp_param.nc'
    if request.method == 'GET':

        scenarios = Scenario.objects

        # this is for the first three scenarios only
        if app.config['DEBUG'] and len(scenarios) < 3:
            for loop_counter in range(3):
                _init_dev_db(BASE_PARAMETER_NC, loop_counter)

                scenarios = Scenario.objects

        return jsonify(scenarios=scenarios)

    else:
        #app.logger.debug('Post request recevied')
        
        #app.logger.debug(BASE_PARAMETER_NC)

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
            model_host=app.config['MODEL_HOST'],
            app_username=app.config['APP_USERNAME'],
            app_password=app.config['APP_PASSWORD']
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

# this part is only for initial model run input
# test only
@api.route('/api/scenarios/test', methods=['GET', 'POST'])
def scenarios_test():
    """
    Handle get and push requests for list of all finished scenarios and submit
    a new scenario, respectively.
    """
    if request.method == 'GET':

        scenarios = Scenario.objects

        # this is for the first three scenarios only
        if app.config['DEBUG'] and len(scenarios) < 3:
            for loop_counter in range(3):
                _init_dev_db(app.config['BASE_PARAMETER_NC'], loop_counter)

                scenarios = Scenario.objects

        return jsonify(scenarios=scenarios)

    else:
        BASE_PARAMETER_NC = app.config['BASE_PARAMETER_NC']

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
            model_host=app.config['MODEL_HOST'],
            app_username=app.config['APP_USERNAME'],
            app_password=app.config['APP_PASSWORD']
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
    # prepare the post request
    auth_host = app.config['AUTH_HOST'] + '/v1/auth'
    req = urllib2.Request(auth_host)
    req.add_header('Content-Type', 'application/json')

    data = {"username":app.config['APP_USERNAME'],"password":app.config['APP_PASSWORD']} 
    response = urllib2.urlopen(req, json.dumps(data))

    msg = response.read()
    json_msg = json.loads(msg)

    return json_msg['access_token']

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
                  range(365*2)]

    # use simple exponentials as the prototype data
    x = range(365)
    streamflow_array = [
        pow(math.e, -pow(((i - 200.0 + 50*scenario_num)/100.0), 2))
        for i in x
    ]

    hydrograph = Hydrograph(
        time_array=time_array,
        streamflow_array=streamflow_array+streamflow_array
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
