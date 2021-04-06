# ckanext-unaids
CKAN Extension for UNADS Styling

## Translations

Read the docs:
- https://docs.ckan.org/en/2.9/extensions/translating-extensions.html

In brief:
0. SSH into the ckan container
    ```
    adx bash ckan
    source ../../bin/activate
    cd /usr/lib/adx/ckanext-unaids/
    ```

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
