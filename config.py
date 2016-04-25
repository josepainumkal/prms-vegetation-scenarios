"""
Configuration for Flask Application 'NKN Metadata Editor'
"""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    PRODUCTION = False

    @staticmethod
    def init_app(app):
        pass

    APP_USERNAME = os.getenv('APP_USERNAME', '')
    APP_PASSWORD = os.getenv('APP_PASSWORD', '')
    # MONGODB_HOST = os.getenv('MONGODB_HOST', 'mongo')
    # MONGODB_DB = os.getenv('MONGODB_DB', 'scenarios')
    # MONGODB_PORT = os.getenv('MONGODB_PORT', 27017)

    # these three files names are for data and control files
    # these three files are in static/user_data/USERFOLDER

    # TEMP_DATA = os.getenv('TEMP_DATA', '/temp_data.nc')
    # TEMP_CONTROL = os.getenv('TEMP_CONTROL', '/temp_control.control')
    # TEMP_PARAM = os.getenv('TEMP_PARAM', '/temp_param.nc')


class DevelopmentConfig(Config):

    DEBUG = True

    MONGODB_SETTINGS = {'db': 'scenarios','host':'mongo'}

    BASE_PARAMETER_NC = 'app/static/data/LC.param.nc'
    
    TEMP_DATA = '/temp_data.nc'
    TEMP_CONTROL = '/temp_control.control'
    TEMP_PARAM = '/temp_param.nc'

    MODEL_HOST =\
        os.getenv('MODEL_HOST', default='http://192.168.99.100:5000/api')

    AUTH_HOST =\
        os.getenv('AUTH_HOST', default='http://192.168.99.100:5005/api')




class TestingConfig(Config):
    TESTING = True

    MONGODB_SETTINGS = {'db': 'scenarios_test'}

    BASE_PARAMETER_NC = 'test/data/parameter.nc'


class ProductionConfig(Config):
    PRODUCTION = True

    MODEL_HOST = os.getenv(
        'MODEL_HOST', default='https://modelserver.virtualwatershed.org'
    )

    AUTH_HOST = os.getenv(
        'AUTH_HOST', default='https://auth.virtualwatershed.org'
    )


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
