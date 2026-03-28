# Deploy Checklist

Run when user says "final checks", "deploy", "pre-deploy", or "run all tests".

## Command
```bash
python agent/scripts/checklist.py .
python agent/scripts/checklist.py . --url <URL>  # with live URL
```

## Execution Order
1. Security (`security_scan.py`, `dependency_analyzer.py`)
2. Lint (`lint_runner.py`)
3. Schema (`schema_validator.py`)
4. Tests (`test_runner.py`)
5. UX (`ux_audit.py`, `accessibility_checker.py`)
6. SEO (`seo_checker.py`)
7. Performance (`bundle_analyzer.py`, `lighthouse_audit.py`)
8. E2E (`playwright_runner.py`)

Fix Critical (Security/Lint) blockers before marking task complete.
