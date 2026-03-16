# epjson_validator

`epjson_validator` is a Python 3.11+ CLI tool and reusable library for validating
EnergyPlus epJSON files. It validates:

- schema compliance against an external `Energy+.schema.epJSON`
- object-name references
- geometry sanity for polygon-based objects

It is not a simulator.

## Features

- Raw EnergyPlus schema validation via external `Energy+.schema.epJSON`
- Reference validation using namespaces extracted from the raw schema
- Geometry extraction and validation for objects with `vertices`
- Structured diagnostics with machine-readable issue metadata

## Installation

```bash
python3 -m pip install .
```

For development:

```bash
python3 -m pip install -e .[dev]
```

## Schema Path

The validator does not bundle `Energy+.schema.epJSON`.

Provide it either with:

- CLI option `--schema-path`
- environment variable `EPJSON_VALIDATOR_SCHEMA_PATH`

## CLI

```bash
epjson-validator validate model.epJSON --schema-path /path/to/Energy+.schema.epJSON
epjson-validator validate model.epJSON --schema-path /path/to/Energy+.schema.epJSON --json
epjson-validator validate model.epJSON --schema-path /path/to/Energy+.schema.epJSON --stage reference
epjson-validator validate model.epJSON --schema-path /path/to/Energy+.schema.epJSON --stage geometry
epjson-validator inspect model.epJSON
epjson-validator stats model.epJSON
```

## Validation Stages

- `schema`: validate epJSON against the raw EnergyPlus schema
- `reference`: validate object-name references using namespaces extracted from the raw schema
- `geometry`: validate polygon geometry extracted from objects with `vertices`

## Library Usage

```python
from epjson_validator import validate_file

report = validate_file(
    "model.epJSON",
    schema_path="/path/to/Energy+.schema.epJSON",
)

print(report.ok)
print(report.summary)
```
