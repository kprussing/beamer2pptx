import os
import pathlib
import re
import shutil

import keyring
import nox
import toml

config = toml.load(pathlib.Path(__file__).parent / "pyproject.toml")

# Set the default sessions to run
pythons = [v.split(":")[-1].strip()
           for v in config["project"]["classifiers"]
           if re.search(r"Python\s*::\s*\d+[.]\d+\s*$", v)]
nox.options.sessions = [
    "lint",
    *["test-" + x for x in pythons],
    "docs"
]
nox.options.reuse_existing_virtualenvs = True


@nox.session
def lint(session):
    """Run the linters"""
    session.install(*config["project"]["optional-dependencies"]["lint"])
    session.run("flake8", "src", "tests", "noxfile.py")
    session.run("mypy", "src", "tests", "noxfile.py")


@nox.session(python=pythons,
             venv_backend="conda")
def test(session):
    """Run the regression tests

    Alternate flags can be passed to ``pytest`` using the positional
    arguments.
    """
    session.install(*config["project"]["dependencies"],
                    *config["project"]["optional-dependencies"]["test"])

    session.install(".")
    if session.posargs:
        tests = session.posargs
    else:
        tests = ["tests"]

    session.run("pytest", *tests)


@nox.session
def docs(session):
    """Build the documentation"""
    session.install(*config["project"]["dependencies"],
                    *config["project"]["optional-dependencies"]["docs"])

    session.install(".")
    root = pathlib.Path(__file__).parent
    srcdir = root / "doc"
    html = root / "docs"
    static = srcdir / "_static"
    if not static.is_dir():
        static.mkdir()

    session.run("sphinx-build",
                "-b", "html",
                "-W",  # Warnings as errors
                str(srcdir.resolve()),
                str(html.resolve())
                )


@nox.session
def dist(session):
    """Push to PyPI"""
    session.install("build", "twine")
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    session.run("python", "-m", "build")
    session.run(
        "python", "-m", "twine", "check", os.path.join("dist", "*")
    )
    session.run(
        "python", "-m", "twine", "upload", "--user", "__token__",
        "--password", keyring.get_password("beamer2pptx", "kprussing"),
        os.path.join("dist", "*")
    )
