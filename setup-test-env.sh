#!/bin/bash
set -e

echo "=== Setting up test environment in Docker ==="

# Start services
echo "Starting services..."
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Install Node dependencies and build React app
echo "Building React app..."
docker-compose -f docker-compose.test.yml exec -T ckan-dev bash -c "
    cd /srv/app/src/ckanext-unaids/ckanext/unaids/react
    apt-get update && apt-get install -y nodejs npm
    npm install -g yarn
    yarn install
    yarn build
"

# Install Python dependencies
echo "Installing Python dependencies..."
docker-compose -f docker-compose.test.yml exec -T ckan-dev bash -c "
    cd /srv/app/src/ckanext-unaids
    pip install -r requirements.txt
    pip install -r dev-requirements.txt
    pip install -e 'git+https://github.com/fjelltopp/ckanext-scheming@fix/ckan-2.11-python-3.10-compatibility#egg=ckanext-scheming'
    pip install -e 'git+https://github.com/fjelltopp/ckanext-validation@toavina/update-python#egg=ckanext-validation'
    pip install -e 'git+https://github.com/fjelltopp/ckanext-ytp-request@toavina/update-python#egg=ckanext-ytp-request'
    pip install -e 'git+https://github.com/datopian/ckanext-authz-service@d179b19469faff7e461191db53e31c60d19003bc#egg=ckanext-authz-service'
    # Python 3.10 compatibility patch for ckanext-authz-service
    sed -i 's/from collections import Iterable, defaultdict/from collections.abc import Iterable\nfrom collections import defaultdict/' /srv/app/src/ckanext-authz-service/ckanext/authz_service/authzzie.py
    pip install -e 'git+https://github.com/ckan/ckanext-pages.git@6c8d5939b01964c30a0394f10fef6e8f5a210ada#egg=ckanext-pages'
    pip install -e 'git+https://github.com/fjelltopp/ckanext-blob-storage@toavina/update-python#egg=ckanext-blob-storage'
    pip install -e 'git+https://github.com/fjelltopp/ckanext-versions@toavina/update-python#egg=ckanext-versions'
    pip install -e 'git+https://github.com/fjelltopp/ckanext-restricted@toavina/update-python#egg=ckanext-restricted'
    pip install -e .
    # Replace default path to CKAN core config file with the one on the container
    sed -i -e 's/use = config:.*/use = config:\/srv\/app\/src\/ckan\/test-core.ini/' test.ini
"

# Initialize git repository (required by some CKAN extensions)
echo "Initializing git repository..."
docker-compose -f docker-compose.test.yml exec -T ckan-dev bash -c "
    cd /srv/app/src/ckanext-unaids
    # Remove any existing .git file or directory (handles submodule references)
    rm -rf .git
    # Configure git to trust this directory
    git config --global --add safe.directory /srv/app/src/ckanext-unaids
    git config --global init.defaultBranch main
    git init
    git config user.email 'test@example.com'
    git config user.name 'Test User'
    git add .
    git commit -m 'Initial commit'
"

# Initialize CKAN database
echo "Initializing CKAN database..."
docker-compose -f docker-compose.test.yml exec -T ckan-dev bash -c "
    cd /srv/app/src/ckanext-unaids
    ckan -c test.ini db init
"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To run tests, use:"
echo "  ./run-docker-tests.sh"
echo ""
echo "To enter the container:"
echo "  docker-compose -f docker-compose.test.yml exec ckan-dev bash"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.test.yml down"
