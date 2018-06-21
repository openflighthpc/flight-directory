
import pytest
import subprocess


@pytest.fixture(autouse=True)
def subprocess_run_success(monkeypatch):
    _mock_subprocess_run(monkeypatch, exit_code=0)


@pytest.fixture
def subprocess_run_failure(monkeypatch):
    _mock_subprocess_run(monkeypatch, exit_code=1)


def _mock_subprocess_run(monkeypatch, exit_code=None):
    mock_process = subprocess.CompletedProcess(
        [], exit_code, stdout=''
    )
    mock_run = lambda *args, **kwargs: mock_process
    monkeypatch.setattr(subprocess, 'run', mock_run)


@pytest.fixture(params=[subprocess_run_success, subprocess_run_failure])
def subprocess_run_success_and_failure(monkeypatch, request):
    request.param(monkeypatch)
