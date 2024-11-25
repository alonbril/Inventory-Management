import PyInstaller.__main__

PyInstaller.__main__.run([
    'run.py',
    '--name=Inventory_Management',
    '--onefile',
    '--windowed',
    '--add-data=templates;templates',
    '--add-data=static;static',
    '--hidden-import=flask',
    '--hidden-import=cryptography',
    '--hidden-import=_cffi_backend',
    '--hidden-import=engineio.async_drivers.threading',
    '--hidden-import=jinja2.ext',
    '--hidden-import=sqlite3',
    '--hidden-import=openpyxl',
])