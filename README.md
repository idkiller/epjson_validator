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
epjson-validator validate model.epJSON --schema-path /path/to/Energy+.schema.epJSON --expand-parametric
epjson-validator validate model.epJSON --schema-path /path/to/Energy+.schema.epJSON --expand-parametric --parametric-run 2
epjson-validator inspect model.epJSON
epjson-validator stats model.epJSON
epjson-validator hvac-graph model.epJSON --graph all
epjson-validator hvac-graph model.epJSON --graph all --format html --output hvac.html
```

## Parametrics

When an epJSON file contains `Parametric:Logic`, `Parametric:RunControl`, and
`Parametric:SetValueForRun`, use `--expand-parametric` to expand placeholders
such as `=$width` before validation. If `--parametric-run` is omitted, the
validator uses the first enabled run from `Parametric:RunControl`.

## Validation Stages

- `schema`: validate epJSON against the raw EnergyPlus schema
- `reference`: validate object-name references using namespaces extracted from the raw schema
- `geometry`: validate polygon geometry extracted from objects with `vertices`

## HVAC Graphs

Use `hvac-graph` to inspect system connectivity without a schema file.

- `--graph air`: air loop branch and component chains
- `--graph plant`: plant loop supply/demand branch and component chains
- `--graph zone`: zone equipment chains
- `--graph all`: emit all three families
- `--format text`: print a readable text graph to stdout
- `--format html`: render an HTML page with text summary and HTML-based diagram

## Library Usage

```python
from epjson_validator import validate_file

report = validate_file(
    "model.epJSON",
    schema_path="/path/to/Energy+.schema.epJSON",
    expand_parametric=True,
    parametric_run=1,
)

print(report.ok)
print(report.summary)
```
