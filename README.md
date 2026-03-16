# epjson_validator

`epjson_validator` is a Python 3.11+ CLI tool and reusable library for validating
EnergyPlus epJSON files. It validates structure, references, geometry, and
visualization readiness. It is not a simulator.

## Features

- Version-aware validation for EnergyPlus `24.2.0`
- Structured diagnostics with machine-readable issue metadata
- Clean validation pipeline split into schema, reference, geometry, and visualization stages
- Extensible schema provider architecture for future EnergyPlus versions
- Minimal dependency footprint with Typer for CLI and pytest for tests

## Installation

```bash
python3 -m pip install .
```

For development:

```bash
python3 -m pip install -e .[dev]
```

## CLI

```bash
epjson-validator validate model.epJSON
epjson-validator validate model.epJSON --json
epjson-validator validate model.epJSON --stage geometry
epjson-validator validate model.epJSON --profile svg-plan
epjson-validator validate model.epJSON --ep-version 24.2.0
epjson-validator inspect model.epJSON
epjson-validator stats model.epJSON
epjson-validator convert-schema Energy+.schema.epJSON
epjson-validator convert-schema Energy+.schema.epJSON -o converted_schema.json
```

## Supported EnergyPlus Objects (MVP)

- `Version`
- `GlobalGeometryRules`
- `Zone`
- `BuildingSurface:Detailed`
- `FenestrationSurface:Detailed`
- `Shading:Zone:Detailed`
- `Shading:Building:Detailed`
- `Shading:Site:Detailed`
- `Construction`
- `Material`

## Raw schema converter (Energy+.schema.epJSON)

The package includes a converter scaffold that can transform an EnergyPlus
`Energy+.schema.epJSON` JSON payload into the internal `VersionSchema` model.

Current converter behavior:
- Reads object categories from top-level `properties`
- Resolves per-object field definitions from `patternProperties` / `additionalProperties`
- Maps primitive field types (`string`, `number`, `integer`, `boolean`, `array`, `object`)
- Treats `vertices` specially as validator geometry field type
- Resolves references via `object_list` + `object_lists` mapping

See `epjson_validator.schema.converter.convert.convert_raw_schema`.

You can run conversion directly with CLI `convert-schema` and print JSON to stdout
or write the converted payload to a file with `--output`.
