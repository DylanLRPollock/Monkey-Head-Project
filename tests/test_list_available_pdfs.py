from monkey_head.pdf_utils import list_available_pdfs


def test_list_available_pdfs():
    pdfs = list_available_pdfs("memory/PDF")
    assert "Linux_on_PlayStation_3.pdf" in pdfs
