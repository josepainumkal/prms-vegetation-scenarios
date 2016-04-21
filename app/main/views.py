"""Metadata server help page views"""
from flask import render_template

from . import main



@main.route('/')
def index():
    """Help page"""

    return render_template('index.html')

@main.route('/modelruns_table')
def show_all_modelruns():
	return render_template('modelruns_table.html')

@main.route('/hydrograph_vis/<scenario_id>')
def hydrograph_visualization(scenario_id = ''):
    """
    This function is for hydrograph visualization
    """

    return render_template('hydrograph_vis.html', scenario_id = scenario_id)


