from file_utils import allowed_file

def test_allowed_file_ok():
    assert allowed_file("doc.pdf")
    assert allowed_file("doc.DOCX")

def test_allowed_file_fail():
    assert not allowed_file("script.sh")
    assert not allowed_file("noext")
