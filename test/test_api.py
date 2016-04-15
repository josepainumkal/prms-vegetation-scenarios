"""
Unit tests for server functions contained in app/api/views.py

Author: Matthew A. Turner
Date: 2016-03-10
"""
import glob
import json
import os
import unittest

from datetime import datetime

os.environ['FLASKCONFIG'] = 'testing'

from manage import app
from app.models import Scenario


class TestAPI(unittest.TestCase):
    """

    """
    def setUp(self):

        try:
            Scenario.drop_collection()
        except:
            pass

        self.client = app.test_client()

        # send requests to server that will edit test/data/parameter.nc
        raw_data = '''
            {
                "name": "test-scenario-1",
                "veg_map_by_hru": {
                    "bare_ground": [0, 1, 2, 3, 5, 10, 11],
                    "grasses": [4, 6, 7, 17, 18, 19],
                    "shrubs": [9, 12, 13],
                    "trees": [8, 14, 15, 16],
                    "conifers": []
                }
            }
        '''

        raw_data2 = '''
            {
                "name": "test-scenario-2",
                "veg_map_by_hru": {
                    "bare_ground": [0, 10, 11],
                    "grasses": [2, 3, 5, 7, 17, 18, 19],
                    "shrubs": [9, 12, 13],
                    "trees": [8, 14, 15, 16],
                    "conifers": [4, 6, 1]
                }
            }
        '''

        self.res1 = self.client.post('/api/scenarios', data=raw_data,
                                     headers={
                                        'Content-Type': 'application/json',
                                        'Origin': '*'}
                                     )

        self.res2 = self.client.post('/api/scenarios', data=raw_data2,
                                     headers={
                                         'Content-Type': 'application/json',
                                         'Origin': '*'}
                                     )

        self.r1_scenario = json.loads(json.loads(self.res1.data)['scenario'])
        self.r2_scenario = json.loads(json.loads(self.res2.data)['scenario'])

        self.id1 = self.r1_scenario['id']
        self.id2 = self.r2_scenario['id']

    def tearDown(self):

        for g in glob.glob('test-*'):
            os.remove(g)
        try:
            Scenario.drop_collection()
        except:
            pass

    def test_scenario_creation(self):
        """
        create and query generation of a scenario: (POST/GET scenarios/ GET sccenarios/{scenarioId})
        """
        # check the results from posts above; maps should be updated as follows

        scenario_is_correct(self.r1_scenario, 'test-scenario-1')
        scenario_is_correct(self.r2_scenario, 'test-scenario-2')

        # check pulling all scenarios contains the two we've created
        all_scenarios_res = self.client.get('/api/scenarios')

        scenarios_list = json.loads(all_scenarios_res.data)['scenarios']
        assert len(scenarios_list) == 2

        # check pulling single scenarios
        single_scenario_1 = json.loads(json.loads(self.client.get(
                '/api/scenarios/' + self.id1,
                headers={
                   'Content-Type': 'application/json',
                   'Origin': '*'
                }
        ).data)['scenario'])

        single_scenario_2 = json.loads(json.loads(self.client.get(
                '/api/scenarios/' + self.id2,
                headers={
                   'Content-Type': 'application/json',
                   'Origin': '*'
                }
        ).data)['scenario'])

        scenario_is_correct(single_scenario_1, 'test-scenario-1')
        scenario_is_correct(single_scenario_2, 'test-scenario-2')

    def test_scenario_delete(self):
        """
        delete an existing scenario by ID
        """
        delete_1 = json.loads(self.client.delete(
            '/api/scenarios/' + self.id1
            ).data
        )

        delete_2 = json.loads(self.client.delete(
            '/api/scenarios/' + self.id2
            ).data
        )

        assert delete_1['message'] == \
            'scenario with id ' + self.id1 + ' removed!'

        assert delete_2['message'] == \
            'scenario with id ' + self.id2 + ' removed!'


def scenario_is_correct(scenario_from_server, expected_name,
                        # for now none of these need to be set
                        expected_time_received=None,
                        expected_time_finished=None,
                        expected_veg_map_by_hru=None, expected_inputs=None,
                        expected_outputs=None,
                        expected_projection_information=None,
                        expected_hydrograph=None):
    """
    Helper function for testing correctness of scenarios from the server.
    """
    assert scenario_from_server['name'] == expected_name

    vegmap1_code0 = scenario_from_server['veg_map_by_hru']['bare_ground']
    vegmap1_code1 = scenario_from_server['veg_map_by_hru']['grasses']
    vegmap1_code2 = scenario_from_server['veg_map_by_hru']['shrubs']
    vegmap1_code3 = scenario_from_server['veg_map_by_hru']['trees']
    vegmap1_code4 = scenario_from_server['veg_map_by_hru']['conifers']

    # TODO this is just what exists currently in test/data/parameter.nc
    # after John Erickson's updates are worked in, update this
    assert vegmap1_code0 == [0, 1, 2, 10]
    assert vegmap1_code1 == [3,  4,  8,  9, 11, 15, 16, 19]
    assert vegmap1_code2 == [5,  6,  7, 17, 18]
    assert vegmap1_code3 == [12, 13, 14]
    assert vegmap1_code4 == []

    inputs = scenario_from_server['inputs']
    expected_inputs = {
        'control': 'http://example.com/control.dat',
        'parameter': 'http://example.com/parameter.nc',
        'data': 'http://example.com/data.nc'
    }
    assert inputs == expected_inputs

    outputs = scenario_from_server['outputs']
    expected_outputs = {
        'statvar': 'http://example.com/statvar.nc'
    }
    assert outputs == expected_outputs

    projection_information = \
        scenario_from_server['veg_map_by_hru']['projection_information']
    # the ur corner has floats that get mangled; check approx equals
    try:
        xurcorner = projection_information['xurcorner']
        yurcorner = projection_information['yurcorner']
    except:
        import ipdb; ipdb.set_trace()
    xllcorner = projection_information['xllcorner']
    yllcorner = projection_information['yllcorner']
    expected_xurcorner = 2.9000001
    expected_yurcorner = -5.0999999
    assert abs(xurcorner - expected_xurcorner) < 1e6
    assert abs(yurcorner - expected_yurcorner) < 1e6
    expected_xllcorner = 2.9000001
    expected_yllcorner = -5.0999999
    assert abs(xllcorner - expected_xllcorner) < 1e6
    assert abs(yllcorner - expected_yllcorner) < 1e6
    del projection_information['xurcorner']
    del projection_information['yurcorner']
    del projection_information['xllcorner']
    del projection_information['yllcorner']
    expected_projection_information = dict(
        ncol=5,
        nrow=4,
        cellsize=100
    )
    assert projection_information == expected_projection_information

    hydrograph = scenario_from_server['hydrograph']
    time_array = hydrograph['time_array']
    streamflow_array = hydrograph['streamflow_array']
    expected_time_array = [
        '2010-10-01T00:00:00', '2010-10-01T01:00:00',
        '2010-10-01T02:00:00', '2010-10-01T03:00:00'
    ]
    expected_streamflow_array = [24.4, 34.6, 10.0, 86.0]
    assert time_array == expected_time_array
    assert streamflow_array == expected_streamflow_array

    then = datetime.now()
    year = then.year
    month = then.month if then.month >= 10 else '0' + str(then.month)
    day = then.day if then.day >= 10 else '0' + str(then.day)

    expected_time_received_date = "{0}-{1}-{2}".format(year, month, day)
    time_received_date = scenario_from_server['time_received'].split('T')[0]
    assert time_received_date == expected_time_received_date

    expected_time_finished_date = "{0}-{1}-{2}".format(year, month, day)
    time_finished_date = scenario_from_server['time_finished'].split('T')[0]
    assert time_finished_date == expected_time_finished_date
