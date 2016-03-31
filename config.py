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


class TestingConfig(Config):
    TESTING = True

    MONGODB_SETTINGS = {'db': 'scenarios_test'}

    BASE_PARAMETER_NC = 'test/data/parameter.nc'


class ProductionConfig(Config):
    PRODUCTION = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
