from setuptools import setup, find_packages

version = '0.0'

setup(
    name='ckanext-unaids',
    version=version,
    description="Styling for UNAIDS",
    long_description="""""",
    classifiers=[],
    keywords='',
    author='Fjelltopp',
    author_email='',
    url='http://ckan.org',
    license='GPL v3.0',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points="""
    [ckan.plugins]
    # Add plugins here, eg
    unaids=ckanext.unaids.plugin:UNAIDSPlugin
    unaids_recline_view=ckanext.unaids.plugin:UNAIDSReclineView
    [babel.extractors]
    ckan = ckan.lib.extract:extract_ckan
    [paste.paster_command]
    initdb = ckanext.unaids.command:InitDBCommand
    """,
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**/node_modules/**.js', 'ignore', None),
            ('**/react/jest/**.js', 'ignore', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ]}
)
