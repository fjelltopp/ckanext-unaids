import logging
from collections import defaultdict

from flask import Blueprint, jsonify

from ckan.plugins import toolkit

log = logging.getLogger(__name__)

svg_map_options = Blueprint(
    u'svg_map_options',
    __name__,
    url_prefix=u'/map-options/'
)

def dataset_count():
    return {
        "url": '',
        "count": 0
    }

def map_options():
    datasets = toolkit.get_action("package_search")({}, {})['results']
    values = defaultdict(dataset_count)
    for dataset in datasets:
        geo_location = dataset.get('geo-location')
        if geo_location:
            country_code = _country_code_from_location_name(geo_location)
            values[country_code]["count"] += 1
            values[country_code]["url"] = u'http://adr.local/dataset/?geo-location={}'.format(geo_location)

    return jsonify({
        "data": {
            "count": {
                "name": 'Dataset Count',
                "format": '{0} datasets',
                "thousandSeparator": ',',
                "thresholdMax": 100,
                "thresholdMin": 0
            },
            "url": {
                "name": 'Browse',
                "format": '{0}'
            }
        },
        "applyData": 'count',
        "values": values
    })

def _country_code_from_location_name(geo_location):
    return 'PL'

svg_map_options.add_url_rule('/', view_func=map_options)
