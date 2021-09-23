Convert a Beamer Presentation to PowerPoint
===========================================

This project is yet another attempt at getting a presentation generated
using beamer to be presentable using PowerPoint or Keynote to gain
access to the additional presentation features of those programs.
Notable tools for accomplishing this task include pdf2pptx_ and
pdf2keynote_.  However, these programs are either platform specific in
the case of pdf2keynote or do not transfer all of the details I desire
such as the presenter notes or are not in a library like format in the
case of pdf2pptx.  This package aims to improve upon the current state
of the art by refactoring the base logic into a usable library with a
command line interface.  In fact, the base logic for the substitutions
to insert the slides was derived from pdf2pptx’s implementation.

The major differences in this project are:

-   It is written as a Python package with the bulk of the logic
    available to other programs and provides a centralized command line
    interface once installed.
-   It uses the PDF inspection tools :manpage:`pdftocairo` to extra the
    slides as images, :manpage:`pdfinfo` to get the metadata and the
    aspect ratio, and :manpage:`pdftotext` to extract the notes pages.
    These tools are described by XpdfReader_ but are also available
    through Poppler_.
-   It places the presenter notes in the file for use during the
    presentation.
-   It directly manipulates the PowerPoint presentation using
    python-pptx_ to avoid `parsing XML with regular expressions`_.

.. note:: This project is currently in a proof of concept stage.  Not
   all of the above features have been implemented at this time.

.. _pdf2pptx: https://github.com/ashafaei/pdf2pptx
.. _pdf2keynote: https://www.cs.hmc.edu/~oneill/freesoftware/pdftokeynote.html
.. _XpdfReader: https://www.xpdfreader.com/download.html
.. _Poppler: https://poppler.freedesktop.org/releases.html
.. _python-pptx: https://python-pptx.readthedocs.io/en/latest/index.html
.. _parsing XML with regular expressions: https://stackoverflow.com/a/1732454/4249913

Installation
------------

To install, run

.. code-block:: bash

    python -m pip install https://github.com/kprussing/beamer2pptx.git

Usage
-----

The basic usage to convert a beamer to a presentation is 

.. code-block:: bash

    beamer2pptx presentation.pdf

This will create the file ``presentation.pptx`` in the same directory as
the original file.  To specify a different output file, you can use the
``--output`` option

.. code-block:: bash

    beamer2pptx --output output.pptx presentation.pdf

To add notes, recompile the presentation in with the following in the
preamble

.. code-block:: latex

    \setbeameroption{show only notes}
    \setbeamertheme{note page}[plain]

Then create a text file that lists the frames to which to assign the
notes (one per line) and run the command

.. code-block:: bash

    beamer2pptx --map mapping.txt --notes notes.pdf presentation.pdf

Licensing
---------

This project is licensed under the open source MIT license.  See
LICENSE.rst for full details.
