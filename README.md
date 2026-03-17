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

### How each graph family is extracted

`hvac-graph` follows explicit epJSON object references (not simulation flow solving)
to build path-style connectivity diagrams.

#### Air Loop (`--graph air`)

1. Start from each `AirLoopHVAC` object.
2. Read its `branch_list_name`.
3. Resolve that `BranchList` and iterate `branches[].branch_name`.
4. For each `Branch`, append each `components[]` item as a node in order.
5. If a component is `AirLoopHVAC:OutdoorAirSystem`, expand its nested
   `AirLoopHVAC:OutdoorAirSystem:EquipmentList` (`component_1..component_32`)
   inline in the same path.

Result: `AirLoopHVAC -> Branch -> Component -> ...`

#### Plant Loop (`--graph plant`)

1. Start from each `PlantLoop` object.
2. Read both side branch-list fields:
   - `plant_side_branch_list_name` (supply)
   - `demand_side_branch_list_name` (demand)
3. For each side, resolve the `BranchList` and iterate its branches.
4. For each branch, append branch `components[]` in listed order.

Result: `PlantLoop -> Side(Supply/Demand) -> Branch -> Component -> ...`

#### Zone Equipment (`--graph zone`)

1. Start from each `ZoneHVAC:EquipmentConnections` object.
2. Use `zone_name` as the diagram root.
3. Follow `zone_conditioning_equipment_list_name` to
   `ZoneHVAC:EquipmentList`.
4. For each `equipment[]` entry, append the referenced equipment node.
5. If equipment is `ZoneHVAC:AirDistributionUnit`, additionally expand:
   - referenced air terminal (`air_terminal_object_type` / `air_terminal_name`)
   - optional reheat coil reference on the terminal.

Result: `Zone -> EquipmentList -> Equipment -> (Terminal -> Reheat Coil)`

#### Notes and limitations

- The extractor is reference-based and intentionally lightweight.
- It does not perform hydraulic/airflow solving or cycle detection.
- Missing or malformed references are skipped when building paths.

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
