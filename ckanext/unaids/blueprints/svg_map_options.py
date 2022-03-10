import logging

import flask
from flask import Blueprint, jsonify

log = logging.getLogger(__name__)

svg_map_options = Blueprint(
    u'svg_map_options',
    __name__,
    url_prefix=u'/map-options/'
)


def map_options():
    return jsonify({
        "data": {
            "gdp": {
                "name": 'GDP per capita',
                "format": '{0} USD',
                "thousandSeparator": ',',
                "thresholdMax": 50000,
                "thresholdMin": 1000
            },
            "change": {
                "name": 'Change to year before',
                "format": '{0} %'
            }
        },
        "applyData": 'gdp',
        "values": {
            "AF": {"gdp": 587, "change": 4.73},
            "AL": {"gdp": 4583, "change": 11.09},
            "DZ": {"gdp": 4293, "change": 10.01}
        }
    })


svg_map_options.add_url_rule('/', view_func=map_options)
