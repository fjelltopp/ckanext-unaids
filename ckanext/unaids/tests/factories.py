from ckan.tests import factories

class User(factories.User):
    job_title = "Data Scientist"
    affiliation = "Fjelltopp"
