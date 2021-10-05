import os
import pathlib
import re
import shutil

import keyring
import nox
import setuptools

config = setuptools.config.read_configuration(
    pathlib.Path(__file__).parent / "setup.cfg"
)

# Set the default sessions to run
pythons = [v.split(":")[-1].strip()
           for v in config["metadata"]["classifiers"]
           if re.search(r"Python\s*::\s*\d+[.]\d+\s*$", v)]
nox.options.sessions = [
    "flake8",
    "mypy",
    *["test-" + x for x in pythons],
    "docs"
]


@nox.session
def flake8(session):
    """Run the flake8"""
    session.install("flake8")
    session.run("flake8", "src", "noxfile.py")


@nox.session
def mypy(session):
    """Run mypy"""
    session.install("mypy")
    session.run("mypy", "src", "noxfile.py")


@nox.session
def lint(session):
    """Run the linters"""
    flake8(session)
    mypy(session)


@nox.session(python=pythons,
             venv_backend="conda")
def test(session):
    """Run the regression tests

    Alternate flags can be passed to ``pytest`` using the positional
    arguments.
    """
    deps = config["options"]["install_requires"]
    deps.extend(config["options"]["extras_require"].get("tests", []))
    if deps != []:
        session.install(*deps)

    session.install(".")
    if session.posargs:
        tests = session.posargs
    else:
        tests = ["tests"]

    session.run("pytest", *tests)


@nox.session
def docs(session):
    """Build the documentation"""
    deps = config["options"]["install_requires"]
    deps.extend(config["options"]["extras_require"].get("docs", []))
    if deps != []:
        session.install(*deps)

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
