param(
    [Parameter(Mandatory = $true)]
    [string]$SchemaPath,

    [string]$DatasetPath = ".\dataset",

    [string]$ValidatorCommand = "epjson-validator",

    [string[]]$ValidatorArgs = @(),

    [ValidateSet("schema", "reference", "geometry")]
    [string]$Stage = "geometry",

    [switch]$JsonOutput
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SchemaPath -PathType Leaf)) {
    throw "Schema file not found: $SchemaPath"
}

if (-not (Test-Path -LiteralPath $DatasetPath -PathType Container)) {
    throw "Dataset directory not found: $DatasetPath"
}

$schemaFullPath = (Resolve-Path -LiteralPath $SchemaPath).Path
$datasetFullPath = (Resolve-Path -LiteralPath $DatasetPath).Path
$files = Get-ChildItem -LiteralPath $datasetFullPath -Filter *.epJSON -File | Sort-Object Name

if ($files.Count -eq 0) {
    Write-Host "No .epJSON files found under $datasetFullPath"
    exit 0
}

$failures = New-Object System.Collections.Generic.List[object]

Write-Host "Validator: $ValidatorCommand"
if ($ValidatorArgs.Count -gt 0) {
    Write-Host "ValidatorArgs: $($ValidatorArgs -join ' ')"
}
Write-Host "Schema:    $schemaFullPath"
Write-Host "Dataset:   $datasetFullPath"
Write-Host "Stage:     $Stage"
Write-Host ""

foreach ($file in $files) {
    Write-Host "=== $($file.Name) ==="

    $arguments = @(
        $ValidatorArgs
        "validate"
        $file.FullName
        "--schema-path"
        $schemaFullPath
        "--stage"
        $Stage
    )

    if ($JsonOutput) {
        $arguments += "--json"
    }

    $output = & $ValidatorCommand @arguments 2>&1
    $exitCode = $LASTEXITCODE

    if ($output) {
        $output | ForEach-Object { Write-Host $_ }
    }

    if ($exitCode -eq 0) {
        Write-Host "RESULT: PASS"
    }
    else {
        Write-Host "RESULT: FAIL (exit code $exitCode)"
        $failures.Add([pscustomobject]@{
            File = $file.Name
            ExitCode = $exitCode
        })
    }

    Write-Host ""
}

Write-Host "=== Summary ==="
Write-Host "Total files: $($files.Count)"
Write-Host "Passed:      $($files.Count - $failures.Count)"
Write-Host "Failed:      $($failures.Count)"

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed files:"
    foreach ($failure in $failures) {
        Write-Host "- $($failure.File) (exit code $($failure.ExitCode))"
    }
    exit 1
}

exit 0
