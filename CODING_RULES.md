# ProjectBlur Coding Rules

## Python Version

To be confirmed. No `pyproject.toml`, `setup.py`, runtime file, or CI
configuration currently declares the supported Python version. The code uses
modern union annotations and therefore requires a compatible modern Python
runtime, but the support range has not been formalized.

## Style

- Use type hints and public API docstrings.
- Follow existing snake_case module/function and PascalCase class naming.
- Prefer `pathlib.Path` for filesystem paths.
- Avoid global mutable state and hidden side effects.
- Keep functions focused and adapters separate from domain logic.

## Configuration

- Never use machine-specific absolute paths or put secrets in source code.
- Use environment variables or configuration files for variable settings once
  the configuration layer is implemented.
- Validate configuration at application startup.
- `.env.example` documents the detector backend, OpenVINO device, and optional
  model-path variables consumed by the web prototype. The application does not
  load `.env` files automatically.

## Logging

- Use the standard module logger already demonstrated by the detection adapter.
- Do not use `print()` in reusable modules; CLI entry points may print results.
- Do not log face crops, embeddings, names, or whitelist identifiers.
- Include actionable error context without sensitive data.

## Error Handling

- Validate all public inputs and raise clear, specific exceptions.
- Do not swallow exceptions or confuse infrastructure failure with no face
  detected.
- Return empty detections only when no detection is a valid outcome.
- Add fallback behavior only when it is safe and documented.

## Dependencies

- Follow `requirements.txt`, the current dependency manager.
- Prefer published packages and install them only in a project virtual
  environment.
- Pin versions after successful compatibility validation.
- Record upstream repository and license information.
- Do not vendor entire external repositories.

## Tests

- Use the existing standard-library `unittest` framework.
- Mock model inference; unit tests must not access the network, download model
  weights, require a GPU, or depend on private data.
- Prefer synthetic arrays or explicitly authorized assets.
- Keep slow model integration tests separate from unit tests.
