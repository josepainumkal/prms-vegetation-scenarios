"""
Configuration for Flask Application 'NKN Metadata Editor'
"""
import os
from redis import Redis
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    PRODUCTION = False

    @staticmethod
    def init_app(app):
        pass

    # APP_USERNAME = os.getenv('APP_USERNAME', '')
    # APP_PASSWORD = os.getenv('APP_PASSWORD', '')

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


    #JWT

    JWT_SECRET_KEY = os.environ.get('PRMS_APP_JWT_SECRET_KEY', 'virtualwatershed')
    JWT_EXPIRATION_DELTA = timedelta(days=int(os.environ.get(
        'PRMS_APP_JWT_EXPIRATION_DELTA', '30')))
    JWT_AUTH_HEADER_PREFIX = os.environ.get(
        'PRMS_APP_JWT_AUTH_HEADER_PREFIX', 'JWT')
    # JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM','HS256')
    # JWT_REQUIRED_CLAIMS = os.environ.get('JWT_REQUIRED_CLAIMS',['exp', 'iat', 'nbf'])
    # http://vw-dev:5000/api
    # auth-test.virtualwatershed.org/api
    MODEL_HOST =\
        os.getenv('MODEL_HOST', 'https://192.168.99.100:5000/api')

    AUTH_HOST =\
        os.getenv('AUTH_HOST', 'https://192.168.99.100:5005/api')

    VWWEBAPP_HOST = os.environ.get('VWWEBAPP_HOST', 'http://vw-dev:5030')
    VWCONVERTER_HOST = os.environ.get('VWCONVERTER_HOST', 'http://vw-dev:5020')
    
    AJAX_TIMEOUT = os.getenv('AJAX_TIMEOUT', '10000')

    BASE_PARAMETER_NC = 'app/static/data/LC.param.nc'
    
    TEMP_DATA = '/temp_data.nc'
    TEMP_CONTROL = '/temp_control.control'
    TEMP_PARAM = '/temp_param.nc'
    TEMP_VIS = '/vis.nc'
    TEMP_STAT = '/stat.nc'

    DEFAULT_DATA = '/LC.data.nc'
    DEFAULT_CONTROL = '/LC.anim.control'
    DEFAULT_PARAM = '/LC.param.nc'


class DevelopmentConfig(Config):

    DEBUG = True

    MONGODB_SETTINGS = {'db': 'scenarios','host':'mongo'}




    # MODEL_HOST =\
    #     os.getenv('MODEL_HOST', default='http://192.168.99.100:5000/api')

    # AUTH_HOST =\
    #     os.getenv('AUTH_HOST', default='http://192.168.99.100:5005/api')




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
