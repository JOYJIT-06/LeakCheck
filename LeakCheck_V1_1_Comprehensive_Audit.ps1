[CmdletBinding()]
param(
    [string]$Python = "D:\anaconda\envs\leakcheck\python.exe",
    [string]$Repo = "D:\my lab\LeakCheck_remote",
    [string]$AuditRoot = "D:\my lab\LeakCheck_remote\docs\AUDIT\FINAL_ADVERSARIAL_AUDIT"
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path $Repo)) { throw "Repository not found: $Repo" }
if (-not (Test-Path $Python)) { throw "Python interpreter not found: $Python" }

Set-Location $Repo

$runName = "RUN_COMPREHENSIVE_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$AuditDir = Join-Path $AuditRoot $runName
New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null

$Transcript = Join-Path $AuditDir "01_COMPREHENSIVE_AUDIT_TRANSCRIPT.txt"
$Summary = Join-Path $AuditDir "00_AUDIT_SUMMARY.md"

Start-Transcript -Path $Transcript -Force | Out-Null

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "LEAKCHECK V1.1 COMPREHENSIVE READ-ONLY AUDIT" -ForegroundColor Cyan
Write-Host "Repository: $Repo"
Write-Host "Python: $Python"
Write-Host "Audit output: $AuditDir"
Write-Host "============================================================" -ForegroundColor Cyan

function Section($name) {
    Write-Host "`n`n========== $name ==========" -ForegroundColor Cyan
}

function Run-Git($argsList) {
    Write-Host "`n> git $($argsList -join ' ')"
    git @argsList 2>&1
    Write-Host "GIT_EXIT_CODE=$LASTEXITCODE"
}

Section "1. REPOSITORY AND GIT PROVENANCE"
Run-Git @("rev-parse", "--show-toplevel")
Run-Git @("branch", "--show-current")
Run-Git @("rev-parse", "HEAD")
Run-Git @("log", "-1", "--format=%H%n%h%n%ad%n%s", "--date=iso-strict")
Run-Git @("status", "--short", "--branch")
Run-Git @("remote", "-v")
Run-Git @("tag", "--list", "--format=%(refname:short) %(objectname:short)")
Run-Git @("branch", "-vv")
Run-Git @("diff", "--stat")
Run-Git @("diff", "--cached", "--stat")

Section "2. PYTHON ENVIRONMENT, PACKAGE PROVENANCE, AND SOURCE SYNTAX"
$pythonAudit = @'
import sys, json, ast, hashlib
from pathlib import Path
from importlib.metadata import version, distribution, PackageNotFoundError
import importlib.util

print("PYTHON:", sys.version)
print("EXECUTABLE:", sys.executable)
for name in ["emi", "mne", "numpy", "scipy", "scikit-learn",
             "pandas", "matplotlib", "joblib", "pytest"]:
    try:
        print(f"PACKAGE {name}: {version(name)}")
    except PackageNotFoundError:
        print(f"PACKAGE {name}: NOT INSTALLED")

try:
    d = distribution("emi")
    print("EMI_DIST_ROOT:", d.locate_file(""))
    du = d.read_text("direct_url.json")
    print("EMI_DIRECT_URL:", du if du else "NOT RECORDED")
except PackageNotFoundError:
    print("EMI_DISTRIBUTION: NOT INSTALLED")

spec = importlib.util.find_spec("emi")
print("EMI_IMPORT_ORIGIN:", spec.origin if spec else "NOT FOUND")
print("EMI_PACKAGE_PATHS:", list(spec.submodule_search_locations or []) if spec else [])

root = Path.cwd()
source = root / "src" / "emi"
files = sorted(source.rglob("*.py")) if source.exists() else []
errors = []
for path in files:
    try:
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except Exception as e:
        errors.append((str(path.relative_to(root)), repr(e)))
print("SOURCE_PY_FILES:", len(files))
print("SOURCE_AST_PARSE_ERRORS:", len(errors))
for item in errors:
    print("AST_ERROR:", item)

print("SOURCE_FILE_SHA256:")
for path in files:
    print(hashlib.sha256(path.read_bytes()).hexdigest(), path.relative_to(root))
'@
$pythonAudit | & $Python - 2>&1

Section "3. RELEASE ARTIFACTS AND METADATA"
$artifactAudit = @'
import zipfile, tarfile, hashlib
from pathlib import Path
from email.parser import Parser

dist = Path("dist")
print("DIST_EXISTS:", dist.exists())
if not dist.exists():
    raise SystemExit(0)

for path in sorted(dist.iterdir()):
    if path.is_file():
        print("ARTIFACT:", path.name, "SIZE:", path.stat().st_size,
              "SHA256:", hashlib.sha256(path.read_bytes()).hexdigest())

wheels = list(dist.glob("*.whl"))
sdists = list(dist.glob("*.tar.gz"))

for wheel in wheels:
    print("\nWHEEL:", wheel.name)
    with zipfile.ZipFile(wheel) as z:
        names = z.namelist()
        metadata_path = next((n for n in names if n.endswith(".dist-info/METADATA")), None)
        if metadata_path:
            msg = Parser().parsestr(z.read(metadata_path).decode("utf-8", "replace"))
            for key in ["Metadata-Version", "Name", "Version", "License-Expression",
                        "License-File", "Requires-Python"]:
                print(f"{key}:", msg.get_all(key))
            print("Requires-Dist:", msg.get_all("Requires-Dist"))
        pyfiles = [n for n in names if n.startswith("emi/") and n.endswith(".py")]
        print("PACKAGE_PY_FILES:", len(pyfiles))
        print("V2_OR_OPENBMI_PATH_HITS:",
              [n for n in names if "openbmi" in n.lower() or "/v2/" in n.lower()][:30])

for sdist in sdists:
    print("\nSDIST:", sdist.name)
    with tarfile.open(sdist, "r:gz") as t:
        names = t.getnames()
        pkg = next((n for n in names if n.endswith("/PKG-INFO")), None)
        if pkg:
            msg = Parser().parsestr(t.extractfile(pkg).read().decode("utf-8", "replace"))
            for key in ["Metadata-Version", "Name", "Version", "License-Expression",
                        "License-File", "Requires-Python"]:
                print(f"{key}:", msg.get_all(key))
            print("Requires-Dist:", msg.get_all("Requires-Dist"))
        print("V2_OR_OPENBMI_PATH_HITS:",
              [n for n in names if "openbmi" in n.lower() or "/v2/" in n.lower()][:30])

license_path = Path("LICENSE")
if license_path.exists():
    root_hash = hashlib.sha256(license_path.read_bytes()).hexdigest()
    print("\nROOT_LICENSE_SHA256:", root_hash)
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as z:
            hits = [n for n in z.namelist() if n.lower().endswith("/licenses/license")]
            for n in hits:
                print("WHEEL_LICENSE_IDENTICAL:", z.read(n) == license_path.read_bytes(), n)
    for sdist in sdists:
        with tarfile.open(sdist, "r:gz") as t:
            hits = [n for n in t.getnames() if n.endswith("/LICENSE")]
            for n in hits:
                print("SDIST_LICENSE_IDENTICAL:", t.extractfile(n).read() == license_path.read_bytes(), n)
'@
$artifactAudit | & $Python - 2>&1

Section "4. TEST DISCOVERY AND FULL TEST SUITE"
Write-Host "Test files:"
Get-ChildItem tests -File -ErrorAction SilentlyContinue |
    Select-Object Name, Length

$env:PYTHONDONTWRITEBYTECODE = "1"
$baseTemp = Join-Path $AuditDir "pytest_tmp"
New-Item -ItemType Directory -Path $baseTemp -Force | Out-Null

Write-Host "`n--- Pytest collection ---"
& $Python -B -m pytest --collect-only -q -p no:cacheprovider
$collectExit = $LASTEXITCODE
Write-Host "PYTEST_COLLECTION_EXIT_CODE=$collectExit"

Write-Host "`n--- Full pytest suite ---"
Write-Host "Tests may execute temporary-file operations; pytest temporary files are directed into the audit folder."
& $Python -B -m pytest -q -p no:cacheprovider --basetemp $baseTemp
$testExit = $LASTEXITCODE
Write-Host "PYTEST_FULL_SUITE_EXIT_CODE=$testExit"

Remove-Item Env:\PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue
Remove-Item Env:\PYTEST_DISABLE_PLUGIN_AUTOLOAD -ErrorAction SilentlyContinue

Section "5. DATA, EXPERIMENT, FIGURE, AND MANUSCRIPT EVIDENCE INVENTORY"
$roots = @(
    "data", "benchmark_results", "figures", "analysis",
    "registry", "paper_evidence", "LeakCheck_paper_evidence",
    "docs", "manuscript", "scripts", "archive"
)

$extensions = @(
    ".edf", ".fif", ".bdf", ".gdf", ".mat", ".npy", ".npz",
    ".csv", ".tsv", ".json", ".jsonl", ".parquet",
    ".png", ".jpg", ".jpeg", ".svg", ".pdf",
    ".md", ".bib", ".txt", ".yaml", ".yml"
)

$inventoryPath = Join-Path $AuditDir "02_EVIDENCE_FILE_INVENTORY.csv"
$inventory = foreach ($rootName in $roots) {
    $full = Join-Path $Repo $rootName
    if (Test-Path $full) {
        Get-ChildItem $full -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $extensions -contains $_.Extension.ToLowerInvariant() } |
            ForEach-Object {
                [PSCustomObject]@{
                    Root = $rootName
                    RelativePath = $_.FullName.Substring($Repo.Length + 1)
                    Extension = $_.Extension
                    SizeBytes = $_.Length
                    LastWriteTime = $_.LastWriteTime.ToString("s")
                }
            }
    }
}
$inventory | Export-Csv -NoTypeInformation -Encoding UTF8 $inventoryPath
Write-Host "Inventory saved: $inventoryPath"
Write-Host "Evidence files inventoried: $($inventory.Count)"
$inventory | Group-Object Extension | Sort-Object Count -Descending |
    Select-Object Count, Name | Format-Table -AutoSize

Section "6. CONFIGURATION AND CLAIM-RELATED FILE PRESENCE"
$important = @(
    "pyproject.toml", "MANIFEST.in", "README.md", "LICENSE",
    "docs/MANUSCRIPT.md", "docs/PREREGISTRATION.md",
    "docs/real_eeg_checks", "tests"
)
foreach ($item in $important) {
    $p = Join-Path $Repo $item
    if (Test-Path $p) {
        Write-Host "PRESENT: $item"
    } else {
        Write-Host "MISSING: $item"
    }
}

Section "7. AUDIT OUTPUT AND PRELIMINARY STATUS"
Write-Host "Repository source and release checks were inspected."
Write-Host "PYTEST_COLLECTION_EXIT_CODE=$collectExit"
Write-Host "PYTEST_FULL_SUITE_EXIT_CODE=$testExit"
Write-Host "Evidence inventory count=$($inventory.Count)"
Write-Host "No source, configuration, dataset, manuscript, release artifact, Git ref, or lockfile was intentionally modified."
Write-Host "Audit output is confined to: $AuditDir"

@"
# LeakCheck V1.1 Comprehensive Audit — Run Summary

- Run folder: ``$runName``
- Repository: ``$Repo``
- Interpreter: ``$Python``
- Branch/commit and working-tree state: see ``01_COMPREHENSIVE_AUDIT_TRANSCRIPT.txt``
- Release metadata and artifact checks: see transcript.
- Source AST parsing and package provenance: see transcript.
- Pytest collection exit code: **$collectExit**
- Pytest full-suite exit code: **$testExit**
- Evidence inventory: ``02_EVIDENCE_FILE_INVENTORY.csv`` ($($inventory.Count) files)

## Interpretation

- Exit code 0 means the corresponding pytest command completed successfully; inspect the transcript for exact counts and warnings.
- Non-zero exit codes require investigation; they are not silently treated as passes.
- File inventory is not proof that an experiment was executed or that a result is valid.
- This automated run does not independently validate participant-level statistics, EEG preprocessing correctness, leakage mechanisms, figure values, citation support, or manuscript claims.
- Missing evidence must remain UNVERIFIED/BLOCKED until primary evidence is examined.

## Read-only boundary

The script writes only its own audit output folder. Pytest temporary files are directed into that folder. Tests can still have their own side effects; inspect the test code and repository status after execution.
"@ | Set-Content -Path $Summary -Encoding UTF8

Stop-Transcript | Out-Null

Write-Host "`nAUDIT RUN FINISHED."
Write-Host "Summary: $Summary"
Write-Host "Transcript: $Transcript"
Write-Host "Inventory: $inventoryPath"
Write-Host "`nIMPORTANT: Review git status after execution to detect any test-created repository changes."
