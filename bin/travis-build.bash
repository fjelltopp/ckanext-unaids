#!/bin/bash
set -e

echo "This is travis-build.bash..."

echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq
sudo apt-get install solr-jetty

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
cd ckan
if [ $CKANVERSION == 'master' ]
then
    echo "CKAN version: master"
else
    CKAN_TAG=$(git tag | grep ^ckan-$CKANVERSION | sort --version-sort | tail -n 1)
    git checkout $CKAN_TAG
    echo "CKAN version: ${CKAN_TAG#ckan-}"
fi

# install the recommended version of setuptools
if [ -f requirement-setuptools.txt ]
then
    echo "Sudo Updating setuptools..."
    pip install --user -r requirement-setuptools.txt
fi

if [ $CKANVERSION == '2.7' ]
then
    echo "Installing setuptools"
    pip install --user setuptools==39.0.1
fi

sudo python setup.py develop
pip install --user -r requirements.txt
pip install --user -r dev-requirements.txt
pip install --user flake8
cd -

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

echo "Setting up Solr..."
# Solr is multicore for tests on ckan master, but it's easier to run tests on
# Travis single-core. See https://github.com/ckan/ckan/issues/2972
sed -i -e 's/solr_url.*/solr_url = http:\/\/127.0.0.1:8983\/solr/' ckan/test-core.ini
printf "NO_START=0\nJETTY_HOST=127.0.0.1\nJETTY_PORT=8983\nJAVA_HOME=$JAVA_HOME" | sudo tee /etc/default/jetty
sudo cp ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml
sudo service jetty restart

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
cd -

echo "Installing other extenions that unaids depends upon."
pip install --user -e "git+https://github.com/fjelltopp/ckanext-scheming@development#egg=ckanext-scheming"
pip install --user -r src/ckanext-scheming/requirements.txt
pip install --user -e "git+https://github.com/fjelltopp/ckanext-validation@development#egg=ckanext-validation"
pip install --user -r src/ckanext-validation/requirements.txt
paster --plugin=ckanext-validation validation init-db -c ckan/test-core.ini

echo "Installing ckanext-unaids and its requirements..."
sudo python setup.py develop
pip install --user -r requirements.txt

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "travis-build.bash is done."