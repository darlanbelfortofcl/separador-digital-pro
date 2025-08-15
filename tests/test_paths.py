from pathlib import Path
from file_utils import is_safe_output_path
from config import OUTPUT_FOLDER

def test_is_safe_output_path_inside(tmp_path):
    inside = OUTPUT_FOLDER / "file.txt"
    assert is_safe_output_path(inside) is True

def test_is_safe_output_path_outside(tmp_path):
    outside = Path("/tmp/file.txt")
    # Garante que não está dentro do OUTPUT_FOLDER
    assert is_safe_output_path(outside) is False
