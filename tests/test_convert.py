import pytest

import beamer2pptx

def test_convert_no_notes(pdf_inputs, aspect_ratio):
    """Check the conversion without notes"""
    slides, _ = pdf_inputs
    pres = beamer2pptx.convert(slides)
    assert len(pres.slides) == 3
    width, height = beamer2pptx.ASPECT_RATIOS[aspect_ratio]
    assert width == pres.slide_width
    assert height == pres.slide_height
    assert all(_.notes_slide.notes_text_frame.text == ""
               for _ in pres.slides)


def test_convert_notes(pdf_inputs, aspect_ratio):
    """Check the conversion with notes"""
    slides, notes = pdf_inputs
    pres = beamer2pptx.convert(slides, notes)
    notes_text = beamer2pptx.extract_notes(notes)
    assert len(pres.slides) == 3
    assert all(slide.notes_slide.notes_text_frame.text == text
               for slide, text in zip(pres.slides, notes_text + [""]))

    pres = beamer2pptx.convert(slides, notes, notes_map=[1, 2])
    assert all(slide.notes_slide.notes_text_frame.text == text
               for slide, text in zip(pres.slides, [""] + notes_text))

    pres = beamer2pptx.convert(slides, notes, notes_map=[2, 1])
    assert all(slide.notes_slide.notes_text_frame.text == text
               for slide, text in zip(pres.slides, [""] + notes_text[::-1])
               )

    with pytest.raises(ValueError):
        beamer2pptx.convert(slides, notes, notes_map=[1])
