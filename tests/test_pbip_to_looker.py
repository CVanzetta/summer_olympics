import tempfile
from pathlib import Path
from scripts.pbip_to_looker import generate_looker_view


def test_generate_looker_view_minimal():
    cols = []
    # simple column structure
    class C:
        pass

    # create minimal Column-like objects
    C.name = 'id'
    C.column_type = 'int64'
    cols = [C]

    view = generate_looker_view('TestTable', cols, [])
    assert 'view:' in view
    assert 'sql_table_name' in view
