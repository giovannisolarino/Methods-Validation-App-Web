'''
Guards the two things that made MVA unsafe for concurrent users on a server.

Run with:  python test_isolation.py
'''

import ast
import pathlib
import pandas as pd
from io import BytesIO

PAGES = pathlib.Path(__file__).parent / 'pages'


def test_no_globals_in_pages():
    #Per-user state in a module-level global is shared by every client of the process: a second
    #user opening a page rebinds the first user's dataframe and UI elements. Page state must
    #live in the page function, where each client gets its own.
    offenders = []
    for path in PAGES.glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                offenders.append(f'{path.name}:{node.lineno} global {", ".join(node.names)}')
    assert not offenders, 'per-user state leaked into module globals:\n  ' + '\n  '.join(offenders)


def test_downloads_are_bytes_not_shared_paths():
    #Templates and result tables used to be written to fixed paths under .nicegui/, so two users
    #generating them at once overwrote each other and could download the wrong file. They are
    #built in memory now.
    from utilities.pd_utilities import template_xlsx, tables_xlsx

    template = template_xlsx(levels=3, replicates=2, columns=('Matrix', 'No-Matrix'))
    assert isinstance(template, bytes)
    frame = pd.read_excel(BytesIO(template))
    assert list(frame.columns) == ['Levels', 'Matrix', 'No-Matrix']
    assert frame['Levels'].tolist() == ['low', 'low', 'medium', 'medium', 'high', 'high']

    book = tables_xlsx({'One': pd.DataFrame({'a': [1]}), 'Two': pd.DataFrame({'b': [2]})})
    assert isinstance(book, bytes)
    assert list(pd.read_excel(BytesIO(book), sheet_name=None)) == ['One', 'Two']


if __name__ == '__main__':
    test_no_globals_in_pages()
    test_downloads_are_bytes_not_shared_paths()
    print('ok')
