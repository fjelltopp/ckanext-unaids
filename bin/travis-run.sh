#!/bin/bash
set -e

pytest --ckan-ini=subdir/test.ini --cov=ckanext.unaids ckanext/unaids/tests
