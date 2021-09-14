import pathlib
import shutil
import subprocess

import pytest


@pytest.fixture(scope="session")
def title():
    return "An Example Presentation"


@pytest.fixture(scope="session")
def author():
    return "A. Nonymous"


@pytest.fixture(scope="session")
def note_texts():
    return ["The first item", "The second item", "The third item"]


@pytest.fixture(scope="session", params=["4:3", "16:9"])
def aspect_ratio(request):
    return request.param


@pytest.fixture(scope="session")
def pdf_dir(tmp_path_factory):
    pdf_dir = tmp_path_factory.mktemp("pdf_dir")
    yield pdf_dir
    shutil.rmtree(pdf_dir)


@pytest.fixture(scope="session")
def tex_inputs(pdf_dir, aspect_ratio):
    ar = "".join(aspect_ratio.split(":"))
    presentation_tex = pdf_dir.joinpath(f"presentation-{aspect_ratio}.tex")
    presentation_tex.write_text(fr"""
    \documentclass[aspectratio={ar}]{{beamer}}
    \input{{body}}
    """)

    notes_tex = pdf_dir.joinpath(f"notes-{aspect_ratio}.tex")
    notes_tex.write_text(fr"""
    \documentclass[aspectratio={ar}]{{beamer}}
    \setbeameroption{{show only notes}}
    \setbeamertemplate{{note page}}[plain]
    \input{{body}}
    """)
    yield presentation_tex, notes_tex


@pytest.fixture(scope="session")
def pdf_inputs(pdf_dir, author, title, note_texts, tex_inputs):
    sconstruct = pdf_dir.parent.joinpath(
        f"SConstruct-{tex_inputs[0].stem}"
    )
    sconstruct.write_text(
        "\n".join([f"PDF('{_.name}')" for _ in tex_inputs])
    )
    body_tex = pdf_dir.joinpath("body.tex")
    body_tex.write_text(r"""
        \usepackage{{mwe}}
        \title{{{title}}}
        \author{{{author}}}
        \begin{{document}}
        \begin{{frame}}
        \titlepage
        \end{{frame}}

        \begin{{frame}}
        \frametitle{{An Example of Only an Image}}
        \begin{{center}}
        \includegraphics[width=\textwidth]{{example-image}}
        \end{{center}}
        \end{{frame}}
        \note{{
        {running}
        }}

        \begin{{frame}}
        \frametitle{{An Example of Only a List}}
        \begin{{itemize}}
        {listed}
        \end{{itemize}}
        \end{{frame}}
        \note[itemize]{{
        {listed}
        }}
        \end{{document}}
        """.format(author=author, title=title,
                   running=". ".join(note_texts),
                   listed="\n".join([fr"\item {_}" for _ in note_texts])
                   )
        )
    subprocess.run(["scons", f"--file={sconstruct}"],
                   check=True,
                   cwd=pdf_dir
                   )
    yield [_.with_suffix(".pdf") for _ in tex_inputs]
