import json

from . import db


class Hydrograph(db.EmbeddedDocument):
    """
    Hydrograph output data
    """
    time_array = db.ListField(db.DateTimeField())
    streamflow_array = db.ListField(db.FloatField())


class VegetationMapByHRU(db.EmbeddedDocument):
    """
    Vegetation map by HRU, modified as requested by the user
    """
    bare_ground = db.ListField(db.IntField())
    elevation = db.ListField(db.FloatField())
    grasses = db.ListField(db.IntField())
    shrubs = db.ListField(db.IntField())
    trees = db.ListField(db.IntField())
    conifers = db.ListField(db.IntField())
    projection_information = db.EmbeddedDocumentField('ProjectionInformation')


class ProjectionInformation(db.EmbeddedDocument):
    """
    Information used to display gridded data on a map
    """
    ncol = db.IntField()
    nrow = db.IntField()
    xllcorner = db.FloatField()
    yllcorner = db.FloatField()
    xurcorner = db.FloatField()
    yurcorner = db.FloatField()
    cellsize = db.FloatField()


class Inputs(db.EmbeddedDocument):
    """
    download links to control, data, and parameter files for a given scenario
    """
    control = db.URLField(default='http://example.com/control.dat')
    parameter = db.URLField(default='http://example.com/parameter.nc')
    data = db.URLField(default='http://example.com/data.nc')


class Outputs(db.EmbeddedDocument):
    """
    download links to PRMS outputs from scenario
    """
    statsvar = db.URLField(default='http://example.com/statvar.nc')


class Scenario(db.Document):
    """
    Scenario data and metadata
    """
    name = db.StringField(required=True)
    user = db.StringField(default='anonymous')

    time_received = db.DateTimeField(required=True)
    time_finished = db.DateTimeField()

    veg_map_by_hru = db.EmbeddedDocumentField('VegetationMapByHRU')

    inputs = db.EmbeddedDocumentField('Inputs')
    outputs = db.EmbeddedDocumentField('Outputs')

    hydrograph = db.EmbeddedDocumentField('Hydrograph')

    def to_json(self):
        """
        Override db.Document's to_json for custom date fomratting
        """
        base_json = db.Document.to_json(self)

        js_dict = json.loads(base_json)

        js_dict['hydrograph']['time_array'] = [
            d.isoformat() for d in self.hydrograph.time_array
        ]

        js_dict['time_received'] = self.time_received.isoformat()
        js_dict['time_finished'] = self.time_finished.isoformat()

        js_dict['id'] = str(self.pk)

        return json.dumps(js_dict)

    def __str__(self):

        return \
            '\n'.join(["{}: {}".format(k, self[k])
                       for k in self._fields_ordered])
