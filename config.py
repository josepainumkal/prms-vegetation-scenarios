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


class DevelopmentConfig(Config):

    DEBUG = True

    MONGODB_SETTINGS = {'db': 'scenarios'}

    BASE_PARAMETER_NC = 'app/static/data/LC.param.nc'

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
