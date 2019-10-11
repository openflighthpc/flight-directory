#==============================================================================
# Copyright (C) 2019-present Alces Flight Ltd.
#
# This file is part of Flight Directory.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License 2.0 which is available at
# <https://www.eclipse.org/legal/epl-2.0>, or alternative license
# terms made available by Alces Flight Ltd - please direct inquiries
# about licensing to licensing@alces-flight.com.
#
# Flight Directory is distributed in the hope that it will be useful, but
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
# IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
# OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
# PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
# details.
#
# You should have received a copy of the Eclipse Public License 2.0
# along with Flight Directory. If not, see:
#
#  https://opensource.org/licenses/EPL-2.0
#
# For more information on Flight Directory, please visit:
# https://github.com/openflighthpc/flight-directory
#==============================================================================

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
