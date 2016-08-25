"""Metadata server help page views"""
from flask import render_template
from functools import wraps

from flask import current_app as app
from flask.ext.login import user_logged_in
from flask.ext.security import login_required
from flask import session
from flask_jwt import _default_jwt_encode_handler
from flask.ext.security import current_user

from . import main


def set_api_token(func):
    '''
    set up token
    '''
    @wraps(func)
    def decorated(*args, **kwargs):
        if current_user and 'api_token' not in session:
            session['api_token'] = _default_jwt_encode_handler(current_user)
        return func(*args, **kwargs)
    return decorated

@main.route('/')
@login_required
@set_api_token
def show_all_modelruns():
    return render_template('scenario_table.html', timeout = app.config['AJAX_TIMEOUT'])


@main.route('/create_new_scenario')
@login_required
@set_api_token
def create_new_scenario():
    return render_template('create_new_scenario.html', model_run_server=app.config['MODEL_HOST'])


@main.route('/hydrograph_vis/<scenario_id>')
@login_required
@set_api_token
def hydrograph_visualization(scenario_id=''):
    """
    This function is for hydrograph visualization
    """

    return render_template('hydrograph_vis.html', scenario_id=scenario_id)


@main.route('/vis_netcdf')
@login_required
@set_api_token
def netcdf_visualization():
    """
    This function is for hydrograph visualization
    """

    return render_template('vis_upload_netcdf.html')