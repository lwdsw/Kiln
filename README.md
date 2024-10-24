<p align="center">
    <picture>
        <img width="300" alt="Kiln AI Logo" src="https://github.com/user-attachments/assets/5fbcbdf7-1feb-45c9-bd73-99a46dd0a47f">
    </picture>
</p>


|         |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CI      | [![Build and Test](https://github.com/Kiln-AI/kiln/actions/workflows/build_and_test.yml/badge.svg)](https://github.com/Kiln-AI/kiln/actions/workflows/build_and_test.yml) [![Format and Lint](https://github.com/Kiln-AI/kiln/actions/workflows/format_and_lint.yml/badge.svg)](https://github.com/Kiln-AI/kiln/actions/workflows/format_and_lint.yml) [![Desktop Apps Build](https://github.com/Kiln-AI/kiln/actions/workflows/build_desktop.yml/badge.svg)](https://github.com/Kiln-AI/kiln/actions/workflows/build_desktop.yml) [![Web UI Build](https://github.com/Kiln-AI/kiln/actions/workflows/web_format_lint_build.yml/badge.svg)](https://github.com/Kiln-AI/kiln/actions/workflows/web_format_lint_build.yml) [![Test Count Badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/scosman/57742c1b1b60d597a6aba5d5148d728e/raw/test_count_kiln.json)](https://github.com/Kiln-AI/kiln/actions/workflows/test_count.yml) [![Test Coverage Badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/scosman/57742c1b1b60d597a6aba5d5148d728e/raw/library_coverage_kiln.json)](https://github.com/Kiln-AI/kiln/actions/workflows/test_count.yml) |
| Package | [![PyPI - Version](https://img.shields.io/pypi/v/kiln-ai.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/kiln-ai/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kiln-ai.svg?logo=python&label=Python&logoColor=gold)](https://pypi.org/project/kiln-ai/)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Meta    | [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/) [![types - Mypy](https://img.shields.io/badge/types-pyright-blue.svg)](https://github.com/microsoft/pyright)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |

# Kiln AI

> Iterative Data-based ML Product Platform

Kiln includes:

- A data platform for teams to collaborate on tasks, goals, evaluations, training data, and more. Designed for Git, providing familiar and rich tooling.
- Easy-to-use desktop apps, enabling everyone to continuously contribute to quality (QA, PM, labelers, subject matter experts, etc.). No GPU or command line required.
- No-code data-science tools to quickly try a variety of approaches in a few clicks. Currently, we support about a dozen models and a variety of prompting solutions (few-shot, multi-shot, chain of thought), with plans for more (fine-tuning, RAG).
- An open-source Python library and REST API for data scientists and engineers to deeply integrate where needed.
- Completely private: Kiln runs locally, and we never have access to your dataset. Bring your own keys, or run locally with Ollama.

<kbd>
<img width="185" alt="Run Screen" src="https://github.com/user-attachments/assets/158efb43-4991-4c19-9e3a-28f61c919892">
</kbd>
<kbd>
<img width="185" alt="Connect Providers Screen" src="https://github.com/user-attachments/assets/b7b5a3b6-0142-4db2-af2d-3310fc583ea9">
</kbd><kbd>
<img width="185" alt="Dataset Screen" src="https://github.com/user-attachments/assets/c5f15c88-9a27-4d7b-81e6-b6350b3cb92c">
</kbd><kbd>
<img width="185" alt="Prompts screen" src="https://github.com/user-attachments/assets/70544362-8420-4a49-9e9f-34a046c837dd">
</kbd>

## Download Now

#### MacOS and Windows

You can download our latest desktop app build [here](https://github.com/Kiln-AI/kiln/actions/workflows/build_desktop.yml). Click a recent run, and download the appropriate build from the “Artifacts” section.

Note: These alpha releases are not signed, and you may need to [allow unidentified apps](https://www.macworld.com/article/672947/how-to-open-a-mac-app-from-an-unidentified-developer.html) to run them. Our official releases will be signed once we enter beta.

## Install Python Library

[![PyPI - Version](https://img.shields.io/pypi/v/kiln-ai.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/kiln-ai/)

`pip install kiln-ai`

## What is this for?

Kiln AI is based on a simple idea: building ML products is like any other product. That means:

- Unexpected bugs emerge from users.
- New/unexpected use cases will emerge.
- Product goals will change over time.
- Underlying tech will get better, and you’ll need to be able to adopt it to keep up.

Classic data science doesn’t quite align with ML product development. You can have the best evaluations ever, but if the dataset doesn’t match the product goals, it doesn’t matter. Kiln aims to fix that.

> Kiln helps your whole team continuously improve your dataset.

Our apps make it easy to continuously iterate and improve your dataset. When using the app, it automatically captures all the inputs/outputs/model parameters and everything else you need to reproduce an issue, repair the result, and capture high-quality data for multi-shot prompting or fine-tuning. QA and PM can easily identify issues sooner and help generate the dataset needed to fix the issue.

Our apps are extremely user-friendly and designed for non-technical users. This includes one-click to launch, no command line required, no GPU required, and a consumer-grade UI.

> Kiln makes it easier to try new models and techniques.

For experimentation, Kiln includes no-code data-science tools to quickly try a variety of approaches and models in a few clicks.

These tools leverage your dataset, and the quality gets better the more you use Kiln. For example, multi-shot prompting finds the highest-rated results to use as examples.

Currently, we support about a dozen models and a variety of prompting solutions (few-shot, multi-shot, chain of thought), with plans for more models and complex techniques (fine-tuning, RAG).

> Deep integrations with our library and REST APIs.

If you have a data science team and want to go deeper, our Python library has everything you need. Ingest the Kiln data format into your pipeline. Create custom evaluations. Use Kiln data in notebooks. Build fine-tunes. Extend or replace any part of the pipeline.

We also offer a REST API for integrating Kiln into your own tools and workflows.

## Status

Kiln is currently in alpha with plans to enter beta soon.

## License

We’re working out our license and will have it sorted soon. The plan is that the core library and REST API will be open source, so there’s zero lock-in. The desktop app will be source-available and free (as in beer).

## Development Commands

Running the desktop app without building an executable:

- First, build the web UI: `npm run build`
- Then run the desktop app: `python -m app.desktop.desktop`

Run the API server and web UI with auto-reload for development:

- Python server: `AUTO_RELOAD=true python -m libs.studio.kiln_studio.server`
- Web UI: `npm run dev --`
