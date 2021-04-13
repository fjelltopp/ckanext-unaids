# ckanext-unaids
CKAN Extension for UNADS Styling and custom features

# Translations

## Docs
- https://docs.ckan.org/en/2.9/extensions/translating-extensions.html

In brief:
0. SSH into the ckan container
    ```
    adx bash ckan
    source ../../bin/activate
    cd /usr/lib/adx/ckanext-extension-name/
    ```

1. Generate the `.pot` file to extract the strings from your extension
    ```
    $ adx bash ckan
    $ cd /usr/lib/ckan/venv/
    $ source bin/activate
    $ cd /usr/lib/adx/ckanext-unaids
    ```

2. Generate the `.pot` file to extract the strings from your extension
    ```
    $ python setup.py extract_messages
    ```

3. If there is no `.po` already set up, init it:
    ```
    $ python setup.py init_catalog --locale fr
    ```

4. If there is a `.po`, update it:
    ```
    $ python setup.py update_catalog --locale fr
    ```

5. Give yourself edit-access to the `.po/.mo` files:
    ```
    $ chmod -R 777 /usr/lib/adx/ckanext-unaids/ckanext/unaids/i18n/
    ```

6. Make updates to the `.po` file

7. Compile the `.po` file into the `.mo` file
    ```
    $ python setup.py compile_catalog --locale fr 
    ```

8. Restart the ckan container to see the changes

# Developing react components

## Setup

- Have npm and nvm installed
- run `$npm install --global yarn` to install yarn

## Running

- cd into the the react directory
- run `yarn` to set up your local environment
- run `yarn start` to start the live builder
- run `yarn build` to run the builder once

## Testing

- cd into the the react directory
- run `yarn test` to run tests once
- run `yarn test:watch` to run the test watcher
