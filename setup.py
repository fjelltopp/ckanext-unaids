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
    [babel.extractors]
    ckan = ckan.lib.extract:extract_ckan
    """,
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ]}
)
