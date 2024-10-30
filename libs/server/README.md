# Kiln AI Server

[![PyPI - Version](https://img.shields.io/pypi/v/kiln-server.svg)](https://pypi.org/project/kiln-server)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kiln-server.svg)](https://pypi.org/project/kiln-server)

---

## About

The Kiln AI Server is a Python library that provides a REST API server for the Kiln AI datamodel.

See our [website](https://getkiln.ai) for more information.

## Installation

```console
pip install kiln_server
```

## API Docs

Our OpenApi docs: [https://kiln-ai.github.io/Kiln/kiln_server_openapi_docs/index.html](https://kiln-ai.github.io/Kiln/kiln_server_openapi_docs/index.html)

## Running the server

```console
python -m kiln_server.server
```

With auto-reload:

```console
AUTO_RELOAD=true python -m kiln_server.server
```

## Using the server in another FastAPI app

See server.py for examples, but you can connect individual API endpoints to your app like this:

```python
from kiln_server.project_api import connect_project_api

app = FastAPI()
connect_project_api(app)
```
