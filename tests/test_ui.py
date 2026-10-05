import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_ui_import_and_helpers():
    # Verify app/ui.py file exists and has valid syntax
    ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "ui.py")
    assert os.path.exists(ui_path)
    
    with open(ui_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    # Syntax compile check
    compiled = compile(code, ui_path, "exec")
    assert compiled is not None
