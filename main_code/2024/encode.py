import os

files_pyc = ["__init__.py", "const.py", "api.py"]

# Biên dịch file .py thành .pyc và xóa file gốc
for file in files_pyc:
    if os.path.exists(file):
        import py_compile
        py_compile.compile(file, cfile=file + "c")
        os.remove(file)

