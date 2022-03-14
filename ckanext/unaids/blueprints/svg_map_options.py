import logging
from collections import defaultdict

import pycountry
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
        "link": '',
        "count": 0
    }


def map_options():
    dataset_search = toolkit.get_action("package_search")({}, {"rows": 0, "facet.field": ["geo-location"]})
    location_facet = dataset_search['facets']['geo-location']
    values = defaultdict(dataset_count)
    for geo_location, count in location_facet.iteritems():
        if geo_location:
            country_code = _country_code_from_location_name(geo_location)
            values[country_code]["count"] = count
            values[country_code]["link"] = u'/dataset/?geo-location={}'.format(geo_location)

    return jsonify({
        "data": {
            "count": {
                "name": 'Datasets Count: ',
                "format": '{0}',
                "thousandSeparator": ','
            }
        },
        "applyData": 'count',
        "values": values,
        "touchLink": True
    })


def _country_code_from_location_name(geo_location):
    return pycountry.countries.get(name=geo_location).alpha_2


svg_map_options.add_url_rule('/', view_func=map_options)
