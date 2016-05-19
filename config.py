"""
Configuration for Flask Application 'NKN Metadata Editor'
"""
import os
from redis import Redis

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    PRODUCTION = False

    @staticmethod
    def init_app(app):
        pass

    APP_USERNAME = os.getenv('APP_USERNAME', '')
    APP_PASSWORD = os.getenv('APP_PASSWORD', '')

    # session
    SECRET_KEY = os.environ.get('VW_SECRET_KEY','hard to guess string')

    SESSION_COOKIE_NAME = os.getenv(
        'PRMS_SESSION_COOKIE_NAME', 'vwsession')
    SESSION_COOKIE_DOMAIN = os.getenv(
        'PRMS_SESSION_COOKIE_DOMAIN', None)
    SESSION_TYPE = os.getenv('PRMS_SESSION_TYPE', None)
    PRMS_SESSION_REDIS_HOST = os.getenv(
        'PRMS_SESSION_REDIS_HOST', None)
    PRMS_SESSION_REDIS_PORT = os.getenv(
        'PRMS_SESSION_REDIS_PORT', 6379)
    PRMS_SESSION_REDIS_DB = os.getenv('PRMS_SESSION_REDIS_DB',0)
    if PRMS_SESSION_REDIS_HOST:
        SESSION_REDIS = Redis(host=PRMS_SESSION_REDIS_HOST,
                              port=PRMS_SESSION_REDIS_PORT, db=PRMS_SESSION_REDIS_DB)

    # sqlalchemy
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite'))


class DevelopmentConfig(Config):

    DEBUG = True

    MONGODB_SETTINGS = {'db': 'scenarios','host':'mongo'}

    BASE_PARAMETER_NC = 'app/static/data/LC.param.nc'
    
    TEMP_DATA = '/temp_data.nc'
    TEMP_CONTROL = '/temp_control.control'
    TEMP_PARAM = '/temp_param.nc'

    DEFAULT_DATA = '/LC.data.nc'
    DEFAULT_CONTROL = '/LC.control'
    DEFAULT_PARAM = '/LC.param.nc'


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
