import pytest
from database.seed import seed


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.sqlite3"
    seed(path)
    return path
