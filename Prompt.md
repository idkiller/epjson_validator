I want to build a Python project named:

epjson_validator

This project is a CLI tool and reusable Python library for validating EnergyPlus epJSON files.

The CLI command must be:

epjson-validator

The validator must perform four validation stages:

1. Schema validation
2. Reference validation
3. Geometry validation
4. Visualization validation

The project must be designed as a clean architecture that supports:

- structured diagnostics
- EnergyPlus version support
- future visualization engines
- schema extensibility

This tool is NOT a simulator.

It validates epJSON structure, references, geometry, and renderability.

# Target EnergyPlus version

The validator must support:

EnergyPlus 24.2.0

Architecture must allow future versions to be added easily.

Version handling requirements:

- detect version from epJSON if possible
- allow CLI override:

--ep-version 24.2.0

- unsupported versions must generate a structured UNSUPPORTED issue

# Technology stack

Use:

Python 3.11+
Typer for CLI
pytest for tests
pyproject.toml packaging

Dependencies must be minimal.

Prefer Python standard library when possible.

# Project architecture

Create this structure:

src/epjson_validator/

    __init__.py
    cli.py
    loader.py
    config.py
    registry.py
    models.py
    diagnostics.py
    types.py

    schema/
        __init__.py
        base.py
        loader.py

        providers/
            __init__.py
            v24_2_0.py

        converter/
            __init__.py
            raw_loader.py
            convert.py
            enrich.py

    reference/
        __init__.py
        validator.py

    geometry/
        __init__.py
        models.py
        normalize.py
        validator.py
        math_utils.py

    visualization/
        __init__.py
        profiles.py
        validator.py

    pipeline/
        __init__.py
        validate.py

tests/

README.md
pyproject.toml

# Validation stages

## Schema validation

Validate structural correctness of epJSON:

- object category exists
- supported category
- required fields
- field types
- enums
- arrays vs objects
- version compatibility

Issue codes:

SCHEMA_ERROR
SCHEMA_WARNING
UNSUPPORTED

Supported MVP categories for EnergyPlus 24.2.0:

Version
GlobalGeometryRules
Zone
BuildingSurface:Detailed
FenestrationSurface:Detailed
Shading:Zone:Detailed
Shading:Building:Detailed
Shading:Site:Detailed
Construction
Material

Design schema providers so additional versions can be added later.

## Reference validation

Validate object relationships:

- zone_name → Zone exists
- construction_name → Construction exists
- material references exist
- parent surface exists
- duplicate object names
- invalid reference targets

Issue codes:

REFERENCE_ERROR
REFERENCE_WARNING

Use an internal registry mapping:

category → object_name → object

## Geometry validation

Validate polygon geometry:

- vertex count >= 3
- vertices distinct
- coordinates finite
- duplicate vertices
- zero-area polygons
- approximate planarity
- simple self-intersection detection
- polygon winding consistency
- fenestration inside parent surface plane

Issue codes:

GEOMETRY_ERROR
GEOMETRY_WARNING

Normalize geometry before validation.

## Visualization validation

Validate renderability for visualization engines.

Checks include:

- stable projection for SVG plan
- triangulation feasibility
- footprint extraction
- centroid calculation
- unsupported objects for visualization

Issue codes:

VIS_ERROR
VIS_WARNING
VIS_INFO
UNSUPPORTED

Render profiles:

svg-plan
svg-elevation
three-basic

Implement svg-plan only for MVP.

# Issue model

Create structured diagnostics.

Example:

class ValidationIssue:
    code: str
    stage: str
    severity: str
    message: str
    path: str | None
    category: str | None
    object_name: str | None
    details: dict | None
    suggestion: str | None
    ep_version: str | None

# Validation report

class ValidationReport:
    ok: bool
    issues: list
    summary: dict
    ep_version: str | None
    schema_version: str | None

Summary must include:

error_count
warning_count
info_count
unsupported_count
counts_by_stage

# Geometry models

Example structures:

class Vec3:
    x: float
    y: float
    z: float

class Polygon3D:
    id: str
    category: str
    object_name: str
    vertices: list
    parent_name: str | None
    zone_name: str | None
    surface_type: str | None

class GeometryModel:
    polygons: list
    bounds: dict | None

# Validation pipeline

Pipeline order:

1 load epJSON
2 detect version
3 load version schema provider
4 schema validation
5 build object registry
6 reference validation
7 geometry normalization
8 geometry validation
9 visualization validation
10 generate report

Collect issues instead of failing early.

# CLI commands

Command name:

epjson-validator

Commands:

validate
inspect
stats

Examples:

epjson-validator validate model.epJSON
epjson-validator validate model.epJSON --json
epjson-validator validate model.epJSON --stage geometry
epjson-validator validate model.epJSON --profile svg-plan
epjson-validator validate model.epJSON --ep-version 24.2.0
epjson-validator inspect model.epJSON
epjson-validator stats model.epJSON

Options:

--json
--stage
--profile
--fail-on-warning
--ep-version

# CLI output

Human readable:

- group issues by stage
- show severity and issue code
- show object name and path
- show EnergyPlus version
- show summary

JSON mode:

Output full ValidationReport JSON.

Exit codes:

0 if no errors
non-zero if errors
if --fail-on-warning then warnings cause failure

# Schema abstraction

Implement a validator-friendly internal schema model.

Example:

class FieldSchema:
    name: str
    field_type: str
    required: bool
    enum_values: list[str] | None
    reference_target: str | None
    semantic_type: str | None

class ObjectSchema:
    name: str
    fields: dict
    geometry_supported: bool
    visualization_supported: bool

class VersionSchema:
    ep_version: str
    objects: dict

# Schema converter

Design the system so a schema converter can transform:

Energy+.schema.epJSON

into the internal Python schema.

For MVP:

- implement the internal schema model
- implement a manually curated provider for EnergyPlus 24.2.0
- scaffold a converter module

Converter pipeline:

raw schema
→ parse
→ enrich with semantic rules
→ internal schema

Enrichment rules may include:

reference mappings
geometry semantics
visualization support

# Testing

Add pytest tests for:

- valid minimal epJSON
- version detection
- unsupported version
- missing required field
- missing zone reference
- missing surface reference
- invalid vertex count
- zero-area polygon
- non-planar polygon warning
- visualization warnings
- CLI JSON output

# Scope constraints

This is an MVP.

Do NOT implement:

- full EnergyPlus schema
- rendering engine
- web UI
- database

Focus on:

- validation engine
- CLI
- version-aware schema architecture
- tests
- documentation

# Implementation order

1 project scaffold
2 diagnostics and types
3 schema abstraction
4 v24_2_0 schema provider
5 loader and version detection
6 schema validator
7 registry
8 reference validator
9 geometry model and validator
10 visualization validator
11 CLI
12 tests
13 README

Prioritize architecture clarity and extensibility.

Please implement the project now.
