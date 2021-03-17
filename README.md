# ckanext-unaids
CKAN Extension for UNADS Styling

## Translations

Read the docs:
- https://docs.ckan.org/en/2.9/extensions/translating-extensions.html

In brief:
1. Generate the `.pot` file to extract the strings from your extension
    ```
    python setup.py extract_messages
    ```

2. If there is no `.po` already set up, init it:
    ```
    python setup.py init_catalog --locale fr
    ```

3. If there is a `.po`, update it:
    ```
    python setup.py update_catalog --locale fr
    ```

4. Make updates to the `.po` file

5. Compile the `.po` file into the `.mo` file
    ```
    python setup.py compile_catalog --locale fr 
    ```

6. Restart the ckan container to see the changes

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
