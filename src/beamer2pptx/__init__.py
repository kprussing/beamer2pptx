"""
beamer2pptx
^^^^^^^^^^^

Utilities for converting a beamer presentation into PowerPoint.
"""

import logging
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import zipfile

from importlib import resources
from typing import (
    List,
    Optional,
    Tuple,
    Union,
)
from os import PathLike

import lxml.etree

logging.getLogger(__name__).addHandler(logging.NullHandler())


ASPECT_RATIOS = {
    "4:3": 4 / 3,
    "16:9": 16 / 9,
}
"""The known valid aspect ratios."""


def extract_aspect_ratio(path: Union[PathLike, str],
                         timeout: Optional[float] = None,
                         ) -> str:
    """Extract the aspect ratio from the PDF.

    Parameters
    ----------

    path: path-like
        The path to the slides PDF.
    timeout: float, optional
        The timeout to pass to :func:`subprocess.run`.

    Returns
    -------

    str:
        The aspect ratio of the presentation in the format 'w:h'.

    Raises
    ------

    subprocess.TimeoutError:
        If the call to :manpage:`pdfinfo` times out.
    subprocess.CalledProcessError:
        If the call to :manpage:`pdfinfo` raises an error.
    RuntimeError:
        If the aspect ratio cannot be deduced.

    Notes
    -----

    This calls :manpage:`pdfinfo` to get the page size and compute the
    aspect ratio.  It checks against the known possibilities rounded to
    five significant figures and returns the most appropriate one.

    """
    proc = subprocess.run(["pdfinfo", str(path)],
                          capture_output=True,
                          timeout=timeout,
                          text=True,
                          )

    logger = logging.getLogger(__name__ + ".extract_aspect_ratio")
    try:
        proc.check_returncode()
    except Exception:
        logger.error(f"Error message: '{proc.stderr}'")
        raise

    if proc.stdout == "":
        raise RuntimeError(f"'{logger.name}' no output from pdfinfo")

    match = re.search(r"Page\s*size:\s*([\d.]+)\s*.\s*([\d.]+)",
                      proc.stdout,
                      re.MULTILINE
                      )
    if not match:
        raise RuntimeError(
            f"'{logger.name}' could not locate page size"
        )

    ratio = float(match.group(1)) / float(match.group(2))
    for key, value in ASPECT_RATIOS.items():
        if round(value, ndigits=4) == round(ratio, ndigits=4):
            return key

    raise RuntimeError(
        f"'{logger.name}' could not deduce aspect ratio for {ratio}"
    )


def extract_metadata(path: Union[PathLike, str],
                     timeout: Optional[float] = None,
                     ) -> Tuple[str, str, str, str]:
    """Extract the metadata from the PDF.

    Parameters
    ----------

    path: path-like
        The path to the slides PDF.
    timeout: float, optional
        The timeout to pass to :func:`subprocess.run`.

    Returns
    -------

    str:
        The title of the presentation.
    str:
        The subject of the presentation.
    str:
        The keywords in the presentation.
    str:
        The author of the presentation.

    Raises
    ------

    subprocess.TimeoutError:
        If the call to :manpage:`pdfinfo` times out.
    subprocess.CalledProcessError:
        If the call to :manpage:`pdfinfo` raises an error.

    Notes
    -----

    This calls :manpage:`pdfinfo` to extract the metadata.

    """
    proc = subprocess.run(["pdfinfo", str(path)],
                          capture_output=True,
                          timeout=timeout,
                          text=True,
                          )

    logger = logging.getLogger(__name__ + ".extract_metadata")
    try:
        proc.check_returncode()
    except Exception:
        logger.error(f"Error message: '{proc.stderr}'")
        raise

    title = ""
    subject = ""
    keywords = ""
    author = ""
    for line in proc.stdout.splitlines():
        match = re.match(r"Title:\s*(.*)", line, re.IGNORECASE)
        if match:
            title = match.group(1)
            continue

        match = re.match(r"Subject:\s*(.*)", line, re.IGNORECASE)
        if match:
            subject = match.group(1)
            continue

        match = re.match(r"Keywords:\s*(.*)", line, re.IGNORECASE)
        if match:
            keywords = match.group(1)
            continue

        match = re.match(r"Author:\s*(.*)", line, re.IGNORECASE)
        if match:
            author = match.group(1)
            continue

    return title, subject, keywords, author


def extract_notes(path: Union[PathLike, str],
                  timeout: Optional[float] = None,
                  ) -> List[str]:
    """Extract the notes from the PDF.

    Parameters
    ----------

    path: path-like
        The path to the notes PDF.
    timeout: float, optional
        The timeout to pass to :func:`subprocess.run`.

    Returns
    -------

    list of str:
        The text of each note page.

    Raises
    ------

    subprocess.TimeoutError:
        If the call to :manpage:`pdftotext` times out.
    subprocess.CalledProcessError:
        If the call to :manpage:`pdftotext` raises an error.

    Notes
    -----

    This calls :manpage:`pdftotext` to do the work and splits the result
    at the formfeeds.

    """
    proc = subprocess.run(["pdftotext", str(path), "-"],
                          capture_output=True,
                          timeout=timeout,
                          text=True,
                          )
    try:
        proc.check_returncode()
    except Exception:
        logger = logging.getLogger(__name__ + ".extract_notes")
        logger.error(f"Error message: '{proc.stderr}'")
        raise

    return proc.stdout.split("\f")


def extract_slides(path: Union[PathLike, str],
                   directory: str = os.curdir,
                   timeout: Optional[float] = None,
                   ) -> List[str]:
    """Extract the slides from the PDF.

    Parameters
    ----------

    path: path-like
        The path to the slides PDF.
    directory: str
        The path to the output directory in which to write the images.
    timeout: float, optional
        The timeout to pass to :func:`subprocess.run`.

    Returns
    -------

    list of str:
        The path to each created slide file.

    Raises
    ------

    subprocess.TimeoutError:
        If the call to :manpage:`pdftocairo` times out.
    subprocess.CalledProcessError:
        If the call to :manpage:`pdftocairo` raises an error.

    Notes
    -----

    This calls :manpage:`pdftocairo` to do the work converting each
    slide page to an image.

    """
    output = pathlib.Path(directory).joinpath(pathlib.Path(path).stem)
    proc = subprocess.run(["pdftocairo", "-png", "-r", "600", "-transp",
                           str(path), str(output)
                           ],
                          capture_output=True,
                          timeout=timeout,
                          text=True,
                          )

    logger = logging.getLogger(__name__ + ".extract_slides")
    try:
        proc.check_returncode()
    except Exception:
        logger.error(f"Error message: '{proc.stderr}'")
        raise

    if proc.stdout != "":
        logger.info(proc.stdout)

    return [str(_) for _ in output.parent.glob(output.stem + "*.png")]


class Presentation:
    """A class to manage the presentation while adding slides.

    This class provides an interface that will prepare the presentation
    by creating the boiler plate files in a temporary directory while
    slides are added to the presentation.  On entry, it creates a
    directory named after the output path with '.dir' tacked on the end
    and adds the boiler plate code.  On exit, it zips ups the directory
    and removes the created directory.

    Parameters
    ----------

    path: :class:`pathlib.Path`
        The path to the PowerPoint presentation.
    workdir: :class:`pathlib.Path`
        The path under which the temporary files directory will be
        created.

    """

    class _XMLFile:
        """A helper class to manage the XML files we need to modify.

        Attributes
        ----------

        path: :class:`pathlib.Path`
            The path to the XML file to modify.
        etree: :class:`lxml.etree.ElementTree`
            The element tree of the file.
        template: :class:`lxml.etree.Element`
            The template for the element to be created for a slide.

        """

        def __init__(self,
                     path: Union[os.PathLike, str],
                     ):
            self.path = pathlib.Path(path)
            self.etree: lxml.etree._ElementTree
            self._template: lxml.etree._Element

        @property
        def template(self) -> lxml.etree._Element:
            """Return a duplicate of the template for editing"""
            return lxml.etree.Element(
                self._template.tag,
                {str(k): str(v) for k, v in self._template.attrib.items()}
            )

        def load(self):
            """Load the tree and remove the file"""
            self.etree = lxml.etree.parse(str(self.path))
            self.path.unlink()

        def write(self):
            """Write the XML back to the path"""
            self.etree.write(str(self.path),
                             xml_declaration=True,
                             encoding="utf-8",
                             method="xml",
                             standalone=True,
                             )
            # The following just changes the single quotes in the
            # generated XML to double quotes in the PowerPoint
            # templates.  This shouldn't matter, but we *never* want
            # PowerPoint to complain about it.
            text = open(self.path, "r").readlines()
            open(self.path, "w").write(
                "\n".join([re.sub("'", '"', text[0][:-1]), *text[1:]])
            )

    def __init__(self,
                 path: Union[os.PathLike, str],
                 workdir: Union[os.PathLike, str] = os.curdir,
                 ):
        self._path = pathlib.Path(path)
        self._files_dir = pathlib.Path(workdir).joinpath(
            self._path.with_suffix(".pptx.dir").name
        )

        self._content_types = self._XMLFile(
            self.files_dir / "[Content_Types].xml"
        )
        self._presentation_xml = self._XMLFile(
            self.files_dir / "ppt" / "presentation.xml"
        )
        self._presentation_xml_rels = self._XMLFile(
            self.files_dir / "ppt" / "_rels" / "presentation.xml.rels"
        )
        self._slide_template: str = ""
        self._slide_rels_template: str = ""

    def __enter__(self):
        self.prepare()
        return self

    def __exit__(self, type, value, traceback):
        self.finalize()

    @property
    def path(self) -> pathlib.Path:
        """The path to the PowerPoint presentation."""
        return self._path

    @property
    def workdir(self) -> pathlib.Path:
        """The path under which the temporary files directory was created.
        """
        return self.files_dir.parent

    @property
    def files_dir(self) -> pathlib.Path:
        """The path to the temporary files directory."""
        return self._files_dir

    @property
    def media_dir(self) -> pathlib.Path:
        """The path to the media directory in the temporary directory.
        """
        return self._files_dir / "ppt" / "media"

    @property
    def slides_dir(self) -> pathlib.Path:
        """The path to the slides directory in the temporary directory.
        """
        return self._files_dir / "ppt" / "slides"

    def prepare(self) -> None:
        """Prepare the directory for adding slides."""
        if self.files_dir.exists():
            shutil.rmtree(self.files_dir)

        # Unpack the template
        with resources.path(__name__, "template.pptx") as template:
            zipfile.ZipFile(template).extractall(self.files_dir)

        # Pull the relevant details and remove the place holder items.
        self._content_types.load()
        root = self._content_types.etree.getroot()
        self._content_types._template = next(
            _ for _ in root if "slide1.xml" in _.attrib.get("PartName", "")
        )
        root.remove(self._content_types._template)

        self._presentation_xml.load()
        root = self._presentation_xml.etree.getroot()
        # The silencing of mypy is due to the invariance of the keys.
        # https://github.com/lxml/lxml-stubs/issues/31#issuecomment-899083523
        self._presentation_xml._template = lxml.etree.Element(
            f"{{{root.nsmap['p']}}}sldId",  # type: ignore
            {"id": "",
             f"{{{root.nsmap['r']}}}id": "",  # type: ignore
             }
        )

        self._presentation_xml_rels.load()
        root = self._presentation_xml_rels.etree.getroot()
        self._presentation_xml_rels._template = next(
            _ for _ in root if "slide1.xml" in _.attrib.get("Target", "")
        )
        root.remove(self._presentation_xml_rels._template)

        _ = self.files_dir / "ppt" / "slides" / "slide1.xml"
        self._slide_template = _.read_text()
        _.unlink()

        _ = _.parent / "_rels" / "slide1.xml.rels"
        self._slide_rels_template = _.read_text()
        _.unlink()

    def finalize(self) -> None:
        """Write the files and zip up the tree."""
        self._content_types.write()
        self._presentation_xml.write()
        self._presentation_xml_rels.write()

        if self.path.exists():
            self.path.unlink()

        with zipfile.ZipFile(self.path, "w") as out:
            for _ in self.files_dir.rglob("*"):
                out.write(_, str(_)[len(str(self.files_dir)):])

        shutil.rmtree(self.files_dir)

    def add_slide(self, slide: Union[PathLike, str]) -> None:
        r"""Add a slide to the presentation.

        This adds the slide to the media directory, if not already
        there, and generates the XML details to place the slide in the
        presentation.

        Parameters
        ----------

        slide: path like
            The path to the image to add as a slide.

        Raises
        ------

        RuntimeError:
            If the files directory has not been created by calling
            :meth:`prepare` or the slide number cannot be deduced from
            the given slide's name.

        Note
        ----

        The slide *must* be named in the format '(P<stem>.*)-(\d+).png'
        as is created by the call to :func:`extract_slides`.  The slide
        number is deduced from the number before the extension.

        """
        if not self.files_dir.exists():
            raise RuntimeError(
                f"'{type(self).__name__}.add_slide' "
                f"called before '{type(self).__name__}.prepare'"
            )

        if not self.media_dir.exists():
            self.media_dir.mkdir()

        if self.media_dir != pathlib.Path(slide).parent:
            shutil.copy(slide, self.media_dir)

        image_name = pathlib.Path(slide).name
        match = re.match(r"(?P<stem>.*-)(?P<slide>\d+)(?P<ext>[.]\w+)$",
                         image_name)
        if not match:
            raise RuntimeError(
                f"'{type(self).__name__}.add_slide' "
                f"could not determine slide number from '{image_name}'"
            )

        slide_name = f"slide-{match.group('slide')}.xml"
        slide_xml = self.slides_dir.joinpath(slide_name)
        slide_xml.write_text(self._slide_template)
        rels_xml = slide_xml.parent / "_rels" / f"{slide_name}.rels"
        rels_xml.write_text(
            re.sub("image1[.]JPG", image_name, self._slide_rels_template)
        )

        # First, set the relationship
        relationship = self._presentation_xml_rels.template
        rId = int(match.group("slide")) + 8
        relationship.attrib["Id"] = f"rId{rId}"
        relationship.attrib["Target"] = f"slides/{slide_name}"
        self._presentation_xml_rels.etree.getroot().append(relationship)

        # Next, the content type
        override = self._content_types.template
        override.attrib["PartName"] = \
            f"/ppt/{relationship.attrib['Target']}"  # type:ignore
        self._content_types.etree.getroot().append(override)

        # And finally, link them in the presentation
        sldId = self._presentation_xml.template
        sId = int(match.group("slide")) + 256
        root = self._presentation_xml.etree.getroot()
        sldId.attrib["id"] = f"{sId}"
        sldId.attrib[f"{{{root.nsmap['r']}}}id"] = f"rId{rId}"  # type: ignore
        root.find(f"{{{root.nsmap['p']}}}sldIdLst"  # type: ignore
                  ).append(sldId)

    def add_notes(self, text: str, slide: int) -> None:
        """Add the given text as notes to the specified slide.

        Parameters
        ----------

        text: str
            The text of the notes.
        slide: int
            The one based slide to which to add the notes.

        """
        raise NotImplementedError

    def adjust_aspect_ratio(self, aspect: str) -> None:
        """Adjust the aspect ratio of the presentation.

        Parameters
        ----------

        aspect: str
            The aspect ratio key in :data:`ASPECT_RATIOS` to use.

        Raises
        ------

        ValueError:
            If aspect is not in :data:`ASPECT_RATIOS`.
        NotImplementedError:
            To protect against version skew.
        AssertionError:
            If the slide size entry cannot be found.

        """
        if aspect not in ASPECT_RATIOS:
            raise ValueError(
                f"'{type(self).__name__}.adjust_aspect_ratio' "
                f"invalid aspect {aspect}"
            )

        root = self._presentation_xml.etree.getroot()
        elem = root.find(f"{{{root.nsmap['p']}}}sldSz")  # type: ignore
        assert elem is not None
        if aspect == "4:3":
            pass
        elif aspect == "16:9":
            elem.attrib["cx"] = "12192000"
            elem.attrib["cy"] = "6858000"
            elem.attrib.pop("type")  # type: ignore
        else:
            raise NotImplementedError(
                f"'{type(self).__name__}.adjust_aspect_ratio' "
                f"unknown aspect ratio {aspect}"
            )


def convert(slides: Union[PathLike, str],
            output: Union[PathLike, str],
            notes: Optional[Union[PathLike, str]] = None,
            timeout: Optional[float] = None,
            ) -> None:
    """Convert the presentation to PowerPoint.

    Parameters
    ----------

    slides: path-like
        The path to the slides PDF.
    output: path-like
        The path to the generated PowerPoint.
    notes: path-like, optional
        The path to the notes PDF.
    timeout: float, optional
        The timeout to pass to subroutines.

    Raises
    ------

    subprocess.TimeoutError:
        If a call to one of the subroutines times out.
    subprocess.CalledProcessError:
        If a call to one of the subroutines errors.

    """
    logger = logging.getLogger(f"{__name__}.convert")
    with tempfile.TemporaryDirectory() as temp:
        with Presentation(output, temp) as pres:

            logger.info("Generate the slide images")
            pres.media_dir.mkdir()
            images = extract_slides(slides, pres.media_dir, timeout)

            logger.info("Generate the XML for each slide")
            for image in images:
                pres.add_slide(image)

            logger.info("Add the notes to the proper slides")

            logger.info("Adjust the aspect ratio")
            pres.adjust_aspect_ratio(extract_aspect_ratio(slides))
