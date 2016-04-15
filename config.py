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


class DevelopmentConfig(Config):

    DEBUG = True

    MONGODB_SETTINGS = {'db': 'scenarios'}

    BASE_PARAMETER_NC = 'app/static/data/parameter.nc'

    VWMODELS_HOST =\
        os.getenv('MODEL_HOST', default='http://192.168.99.100:5000')

    AUTH_HOST =\
        os.getenv('AUTH_HOST', default='http://192.168.99.100:5005')


class TestingConfig(Config):
    TESTING = True

    MONGODB_SETTINGS = {'db': 'scenarios_test'}

    BASE_PARAMETER_NC = 'test/data/parameter.nc'


class ProductionConfig(Config):
    PRODUCTION = True

    VWMODELS_HOST = os.getenv(
        'MODEL_HOST', default='https://modelserver.virtualwatershed.org'
    )

    VWMODELS_AUTH_HOST = os.getenv(
        'AUTH_HOST', default='https://auth.virtualwatershed.org'
    )


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
