import pathlib
import shutil

import pytest

import beamer2pptx


def test_extract_aspect_ratio(pdf_inputs, aspect_ratio):
    assert all(aspect_ratio == beamer2pptx.extract_aspect_ratio(_)
               for _ in pdf_inputs)


def test_extract_metadata(pdf_inputs, title, author):
    for pdf in pdf_inputs:
        pdf_title, _, _, pdf_author = beamer2pptx.extract_metadata(pdf)
        assert pdf_title == title
        assert pdf_author == author


def test_extract_notes(pdf_inputs, note_texts):
    result = beamer2pptx.extract_notes(pdf_inputs[1])
    assert len(result) == 2
    assert result[0].rstrip() == ". ".join(note_texts)
    assert result[1].rstrip() == "\n".join([fr"• {_}" for _ in note_texts])


def test_extract_slides(pdf_inputs, tmp_path):
    result = beamer2pptx.extract_slides(pdf_inputs[0], tmp_path)
    try:
        assert len(result) == 3
    except AssertionError:
        raise
    finally:
        for _ in result:
            pathlib.Path(_).unlink()
