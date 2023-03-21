import logging
from collections import defaultdict

import pycountry
import six
from flask import Blueprint, jsonify, request

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
    type_name = request.args.get('type_name')
    search_data_dict = {"rows": 0, "facet.field": ["geo-location"]}
    if type_name:
        search_data_dict['q'] = f"type_name:\"{type_name}\""
    dataset_search = toolkit.get_action("package_search")({}, search_data_dict)
    location_facet = dataset_search['facets']['geo-location']
    values = defaultdict(dataset_count)
    for geo_location, count in six.iteritems(location_facet):
        if geo_location:
            country_code = _country_code_from_location_name(geo_location)
            values[country_code]["count"] = count
            values[country_code]["link"] = f'/dataset?geo-location={geo_location}'
            if type_name:
                values[country_code]["link"] += f"&type_name={type_name}"
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


