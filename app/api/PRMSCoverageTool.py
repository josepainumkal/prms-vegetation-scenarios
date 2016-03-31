__author__ = 'jerickson'

import netCDF4
import shutil
import types
import os


class ScenarioRun:
    """
    Scenario Run object representation of the process of creating and running
    a PRMS Scenario
    """

    scenario_file = ""

    def __init__(self, basefile):
        self.basefile = basefile
        self.working_scenario = None

    def initialize(self, scenarioname):
        '''
        Starts a new scenario based on the original file under a new name

        :param scenarioname: Name of scenario to make a new file;
            .nc will be appended
        :return:
        '''
        if self.working_scenario is not None:
            raise Exception("Working Scenario already open")
            return

        if os.path.exists("{0}.nc".format(scenarioname)):
            sequence = 2
            while os.path.exists("{0}-{1}.nc".format(scenarioname, sequence)):
                sequence = sequence + 1
            self.scenario_file = "{0}-{1}.nc".format(scenarioname, sequence)
        else:
            self.scenario_file = "{0}.nc".format(scenarioname)

        shutil.copyfile(self.basefile, self.scenario_file)
        self.working_scenario = netCDF4.Dataset(self.scenario_file, 'r+')

    def end(self):
        '''
        Close the working scenario and free our references to it
        :return:
        '''
        if self.working_scenario is None:
            return
        self.working_scenario.close()
        self.working_scenario = None

    def debug_display_cov_type(self, hru):
        '''
        For debug purposes; given a list of hrus, display the
        coverage type for each coordinate

        :param coords: List of coordinates
        :return:
        '''
        if self.working_scenario is None:
            raise Exception("No working scenario defined")
            return

        print self.working_scenario.variables['cov_type'][hru]

    def update_cov_type(self, hru, val):
        '''
        Update coverage type in a single hru using 2d coordinates
        :param hru (list): list of HRU to set to a new value, val
        :param val: value to set hru to
        :return:
        '''
        if self.working_scenario is None:
            raise Exception("No working scenario defined")
            return

        if hru != []:
            self.working_scenario.variables['cov_type'][hru] = val

    def run(self):
        """
        Where it will run!
        """
        # call Moinul's PRMS web service here!
        pass


if __name__ == "__main__":
    prmsfile = ScenarioRun("parameter.nc")

    coord_list_old = [(0, 0), (0, 1), (0, 2),
                      (1, 0), (1, 1), (1, 2),
                      (2, 0), (2, 1), (2, 2)]

    coord_list = [0,   1,   2,
                  96,  97,  98,
                  192, 193, 194]

    try:
        prmsfile.begin("test")
        prmsfile.debug_display_cov_type(coord_list)
        prmsfile.debug_display_cov_type(coord_list_old)
        prmsfile.block_update_cov_type(coord_list, 2)
        prmsfile.debug_display_cov_type(coord_list)
        prmsfile.debug_display_cov_type(coord_list_old)
        prmsfile.end()

    except Exception as ex:
        print "Test run failed: " + ex.message

    print "Testing exceptions..."
    try:
        prmsfile.debug_display_cov_type(coord_list)
    except Exception as ex:
        print "DebugDisplayCovType properly failed"
    try:
        prmsfile.update_cov_type(coord_list)
    except Exception as ex:
        print "BlockUpdateCovType properly failed"
