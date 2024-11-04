# Contributing to Kiln

## Issues and Bug Tracking

We use [GitHub issues](https://github.com/Kiln-AI/Kiln/issues) for tracking issues, bugs, and feature requests.

## Contributing

Contributors must agree to the [contributor license agreement](CLA.md).

## Development Environment Setup

We use [uv](https://github.com/astral-sh/uv) to manage the Python environment and dependencies, and npm to manage the web UI.

```
# First install uv: https://github.com/astral-sh/uv
uv sync
cd app/web_ui
# install Node if you don't have it already
npm install
```

### Running Development Servers

Running the web-UI and Python servers separately is useful for development, as both can hot-reload.

To run the API server, Studio server, and Studio Web UI with auto-reload for development:

1. In your first terminal:

   ```bash
   uv run python -m app.desktop.dev_server
   ```

2. In a second terminal, navigate to the web UI directory and start the dev server:

   ```bash
   cd app/web_ui
   npm run dev --
   ```

3. Open the app: http://localhost:5173/run

### Running the Desktop App

Running the desktop app without building an executable:

- First, build the web UI from the `app/web_ui` directory: `npm run build`
- Then run the desktop app: `uv run python -m app.desktop.desktop`

### Building the Desktop App

Typically building desktop apps are done in a CI/CD pipeline, but if you need to build the desktop app locally, you can do so with:

```bash
cd app/desktop
uv run ./build_desktop_app.sh
```
