# ckanext-unaids
CKAN Extension for UNADS Styling

## Translations
https://docs.ckan.org/en/2.8/extensions/translating-extensions.html
1. Fetch messages from code into pot file
    ```
    python setup.py extract_messages
    ```
2. Update the po file from the pot file
    ```
    python setup.py update_catalog --locale fr
    ```
3. Then you need to add the translation sting.
4. Compile translated po file into mo file
    ```
    python setup.py compile_catalog --locale fr 
    ```
