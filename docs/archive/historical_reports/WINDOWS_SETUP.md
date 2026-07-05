# Windows setup

Use Python 3.12 for this project. Do not create the virtual environment with
the bare `python` command on Windows, because it may resolve to the Microsoft
Store alias or to an unsupported interpreter.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
```

The project is pinned to Python 3.12.11 in `.python-version`, `render.yaml`,
and the Docker base image used by Render.
