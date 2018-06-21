
import pytest

from config import CONFIG
# Make all shared fixtures available in Directory tests. `NOQA` ignores
# warnings about `import *`.
from appliance_cli.shared_fixtures import *  # NOQA.


@pytest.fixture(autouse=True)
def mock_directory_record(monkeypatch, tmpdir):
    mock_record = tmpdir.mkdir("directory").join('record').strpath
    monkeypatch.setattr(CONFIG, 'DIRECTORY_RECORD', mock_record)
