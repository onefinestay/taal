import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--neo4j_uri", action="store",
        default="temp://",
        help=("URI for establishing a connection to neo4j."
        "See the docs for valid URIs"))


@pytest.fixture
def storage(request):
    from kaiso.persistence import Storage

    neo4j_uri = request.config.getoption('neo4j_uri')
    storage = Storage(neo4j_uri)
    storage.delete_all_data()
    storage.initialize()
    return storage
