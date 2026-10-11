from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from tests.conformance.tf_harness import build_tiny_corpus, load_api

BHSA_ENV = "TF_JEV_BHSA_DIR"
BHSA_VERSION = "2021"


@pytest.fixture(scope="session")
def tiny_api(tmp_path_factory: pytest.TempPathFactory) -> Any:
    directory = tmp_path_factory.mktemp("tiny-tf")
    build_tiny_corpus(directory)
    return load_api(directory)


@pytest.fixture(scope="session")
def bhsa_api() -> Any:
    """Real BHSA corpus, opt-in.

    Set ``TF_JEV_BHSA_DIR`` to a local BHSA ``tf/2021`` directory, e.g.
    ``~/text-fabric-data/github/ETCBC/bhsa/tf/2021``. Skipped otherwise, so
    CI never downloads the corpus.
    """
    location = os.environ.get(BHSA_ENV)
    if not location:
        pytest.skip(f"set {BHSA_ENV} to a BHSA tf/{BHSA_VERSION} directory to run")
    directory = Path(location).expanduser()
    if directory.name != BHSA_VERSION or not (directory / "otype.tf").exists():
        pytest.fail(f"{BHSA_ENV} must point at a BHSA tf/{BHSA_VERSION} directory: {directory}")
    return load_api(directory, features="sp gn nu lex prs function typ verse book qere dist mother")


@pytest.fixture(scope="session")
def bhsa_dir(bhsa_api: Any) -> Path:
    """The BHSA 2021 directory (same opt-in as ``bhsa_api``)."""
    return Path(os.environ[BHSA_ENV]).expanduser()
