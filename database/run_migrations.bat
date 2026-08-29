@echo off
:: =============================================================================
:: CIVIX Phase 2A — Run All Migrations
:: Authority: docs/phase2/PHASE2A_ARCHITECTURE_READINESS_CHECK.md
:: =============================================================================
:: USAGE: run_migrations.bat [connection_string]
:: Example: run_migrations.bat "postgresql://civix_admin:pass@localhost:5432/civix"
:: =============================================================================

SET CONN=%1
IF "%CONN%"=="" SET CONN=postgresql://civix_admin:@localhost:5432/civix

echo CIVIX Phase 2A — Applying all migrations
echo Connection: %CONN%
echo.

echo [000] Installing extensions and creating civix schema...
psql %CONN% -f migrations\000_extensions.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [001] Creating ENUM types...
psql %CONN% -f migrations\001_enums.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [002] Creating users and synthetic data tables...
psql %CONN% -f migrations\002_users_and_synthetic.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [003] Creating source and evidence tables...
psql %CONN% -f migrations\003_source_and_evidence.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [004] Creating core entity model...
psql %CONN% -f migrations\004_core_entities.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [005] Creating identity resolution tables...
psql %CONN% -f migrations\005_identity_resolution.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [006] Creating telecom and financial tables...
psql %CONN% -f migrations\006_telecom_and_financial.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [007] Creating cases and access control...
psql %CONN% -f migrations\007_cases_and_access.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [008] Creating epistemic pipeline...
psql %CONN% -f migrations\008_epistemic_pipeline.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [009] Creating workflow and legal tables...
psql %CONN% -f migrations\009_workflow_and_legal.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [010] Creating provenance and data quality tables...
psql %CONN% -f migrations\010_provenance_and_quality.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [011] Installing triggers...
psql %CONN% -f migrations\011_triggers.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [012] Creating indexes...
psql %CONN% -f migrations\012_indexes.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo [013] Enabling Row-Level Security...
psql %CONN% -f migrations\013_rls.sql
IF %ERRORLEVEL% NEQ 0 GOTO error

echo.
echo All migrations applied successfully.
echo.
echo Running schema validation...
psql %CONN% -f migrations\014_validation.sql
echo.
echo Phase 2A migration complete. Review validation output above.
GOTO end

:error
echo.
echo ERROR: Migration failed at step above. Review error output.
echo The database may be in a partially applied state.
echo Restore from backup or DROP SCHEMA civix CASCADE and retry.
exit /b 1

:end
