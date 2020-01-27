# encoding: utf-8
import logging
import cStringIO
import json
import os
from flask import Blueprint, Response, abort, request, jsonify
import ckan.plugins.toolkit as t
from ckanext.validation.jobs import _load_dataframe
from ckanext.validation.helpers import validation_load_schemed_table

log = logging.getLogger(__name__)

unaids_blueprint = Blueprint(
    u'unaids_blueprint',
    __name__,
    url_prefix=u'/validation'
)


def download_table_template(validation_schema):
    """
    Downloads a CSV template file for the specified validation schema.
    """
    try:
        format = request.args.get('format', 'csv')
        logging.warning(format)

        log.info('Fetching creating schema: ' + validation_schema)
        schema_directory = t.config['ckanext.validation.schema_directory']
        file_path = schema_directory + '/' + validation_schema + '.json'
        schemed_table = validation_load_schemed_table(file_path)
        template = schemed_table.create_template()

        if format == 'csv':
            csv_content = template.to_csv(
                header=False,
                index=False,
                encoding='utf-8'
            )
            return Response(
                csv_content,
                mimetype="text/csv",
                headers={"Content-disposition":
                         "attachment; filename=" + str(validation_schema) + ".csv"}
            )

        elif format == 'xls':
            template = template.iloc[1:]  # Remove headers
            out = cStringIO.StringIO()
            template.to_excel(out, columns=None, index=None)
            out.seek(0)
            return Response(
                out,
                mimetype="application/xls",
                headers={"Content-disposition":
                         "attachment; filename=" + str(validation_schema) + ".xls"}
            )

    except AttributeError as e:
        log.exception(e)
        abort(404, "404 Not Found Error: No schema exists for " + validation_schema)

    except Exception as e:
        log.exception(e)
        abort(
            500,
            "500 Internal server error: Something went wrong whilst "
            "generating your template " + validation_schema
        )


def download_naomi_geodata(package_id):
    package = t.get_action('package_show')({}, {'id': package_id})
    found_location_hierarchy = False
    found_area_geojson = False
    found_area_metadata = False
    for resource in package.get('resources', []):
        if resource['name'] == u'Location Hierarchy':
            found_location_hierarchy = True
            resource_format = resource.get('format', 'csv').lower()
            resource_path = __get_resource_path(resource)
            location_hierarchy_df = _load_dataframe(resource_path, resource_format)
            location_hierarchy_df['area_sort_order'] = location_hierarchy_df['area_sort_order'].fillna('')
        elif resource['name'] == u'Regional Geometry':
            found_area_geojson = True
            resource_path = __get_resource_path(resource)
            with open(resource_path, 'r') as json_file:
                area_gejson = json.load(json_file)
        elif resource['name'] == u'Areas Metadata':
            found_area_metadata = True
            resource_format = resource.get('format', 'csv').lower()
            resource_path = __get_resource_path(resource)
            area_metadata_df = _load_dataframe(resource_path, resource_format).set_index('area_level')
    if found_area_geojson and found_location_hierarchy:
        for feature in area_gejson['features']:
            prop = feature['properties']
            area_id = prop['area_id']
            area_level = str(int(prop['area_level']))
            area_data = location_hierarchy_df.loc[area_id]
            # Naomi expects parent area id of root node to be null
            if area_data['area_id'] == area_data['parent_area_id']:
                prop['parent_area_id'] = None
            else:
                prop['parent_area_id'] = area_data['parent_area_id']
            prop['area_sort_order'] = _safe_cast(area_data['area_sort_order'], int, 0)
            if found_area_metadata:
                area_metadata = area_metadata_df.loc[area_level]
                for key in ['display', 'spectrum_level',
                            'epp_level', 'naomi_level', 'pepfar_psnu_level']:
                    prop[key] = _convert_string_bool(area_metadata[key])
                for key in ['area_level_label']:
                    prop[key] = area_metadata[key]
    else:
        raise RuntimeError("Failed to fetch proper geographic package resources")

    output = cStringIO.StringIO()
    output.write(json.dumps(area_gejson))
    output.seek(0)
    return Response(
                output,
                mimetype="application/json",
                headers={"Content-disposition":
                         "attachment; filename={!s}_naomi_format.geojson".format(package['name'])}
            )


def _convert_string_bool(input):
    if not input or input in ['False', 'FALSE', 'false', 'f', 'F']:
        return False
    else:
        return True


def _safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default


def __get_resource_path(resource):
    resource_id = resource['id']
    resource_path = os.path.join(
        t.config.get('ckan.storage_path', '/var/lib/ckan'),
        'resources',
        resource_id[0:3],
        resource_id[3:6],
        resource_id[6:]
    )
    return resource_path


unaids_blueprint.add_url_rule(
    u'/geodata/<package_id>',
    view_func=download_naomi_geodata
)
unaids_blueprint.add_url_rule(
    u'/template/<validation_schema>',
    view_func=download_table_template
)
