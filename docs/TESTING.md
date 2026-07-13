# Testing ProjectBlur

## Environment

Create and activate a virtual environment, then install the current dependency
set:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Set `PYTHONPATH` to `src` for the commands below because packaging metadata has
not yet been added.

## Unit Tests

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests/detection -p "test_*.py" -v
```

POSIX shells:

```bash
PYTHONPATH=src python -m unittest discover -s tests/detection -p 'test_*.py' -v
```

The detection directory currently contains the full test suite, so the same
command is both the relevant and full suite command.

## Syntax Validation

```bash
python -m compileall src examples tests
```

## Linting and Formatting

No linter, formatter, or type checker is configured in this repository. Do not
add one solely for validation.

## Model Test Rules

- No network access or model downloads in unit tests.
- No GPU requirement.
- Mock external inference.
- Use synthetic arrays or authorized sample assets.
- Keep slow integration tests separate and explicitly marked.

## Manual Test

After installing dependencies, supply an authorized image:

```powershell
$env:PYTHONPATH = "src"
python examples/retinaface_example.py path/to/image.jpg
```

RetinaFace may download model weights during the first real inference. Do not
use the manual command in offline unit-test automation.
