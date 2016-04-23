"""Metadata server help page views"""
from flask import render_template

from flask import current_app as app
from . import main



@main.route('/')
def index():
    """Help page"""

    return render_template('index.html')

@main.route('/scenario_table')
def show_all_modelruns():
	return render_template('scenario_table.html')

@main.route('/create_new_scenario')
def create_new_scenario():
	return render_template('create_new_scenario.html',model_run_server = app.config['MODEL_HOST'])

@main.route('/hydrograph_vis/<scenario_id>')
def hydrograph_visualization(scenario_id = ''):
    """
    This function is for hydrograph visualization
    """

    return render_template('hydrograph_vis.html', scenario_id = scenario_id)


