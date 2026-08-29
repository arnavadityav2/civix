Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " CIVIX PHASE 5 CHUNK 2: GRAPH PIPELINE " -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# 1. Graph Construction
Write-Host "`n[1/8] Building Graph Edges..." -ForegroundColor Yellow
python -m civix_ml graph build --skip-temporal
if ($LASTEXITCODE -ne 0) { throw "Graph Build failed" }

# 2. Graph Features
Write-Host "`n[2/8] Extracting Topological Features..." -ForegroundColor Yellow
python -m civix_ml graph features
if ($LASTEXITCODE -ne 0) { throw "Graph Features failed" }

# 3. Validation
Write-Host "`n[3/8] Validating Graph Temporal & Label Integrity..." -ForegroundColor Yellow
python -m civix_ml graph validate
if ($LASTEXITCODE -ne 0) { throw "Graph Validation failed" }

# 4. Graph Audit
Write-Host "`n[4/8] Auditing Graph for Synthetic Artifacts..." -ForegroundColor Yellow
python -m civix_ml graph audit
if ($LASTEXITCODE -ne 0) { throw "Graph Audit failed" }

# 5. Graph Baselines
Write-Host "`n[5/8] Training Graph Baselines (Logistic & RF & IF)..." -ForegroundColor Yellow
python -m civix_ml graph baseline --model logistic
python -m civix_ml graph baseline --model random_forest
python -m civix_ml graph baseline --model isolation_forest

# 6. Three-way Comparison
Write-Host "`n[6/8] Comparing Behavior vs Graph vs Combined..." -ForegroundColor Yellow
python -m civix_ml graph compare
if ($LASTEXITCODE -ne 0) { throw "Graph Compare failed" }

# 7. Hard Negatives
Write-Host "`n[7/8] Evaluating Hard Negatives (Adversarial Robustness)..." -ForegroundColor Yellow
python scratch/eval_graph_hard_negatives.py
if ($LASTEXITCODE -ne 0) { throw "Hard Negative Eval failed" }

# 8. GraphSAGE
Write-Host "`n[8/8] Training GraphSAGE GNN (CPU)..." -ForegroundColor Yellow
python -m civix_ml gnn train --device cpu --epochs 30 --batch-size 250000
if ($LASTEXITCODE -ne 0) { throw "GNN Training failed" }

Write-Host "`n==============================================" -ForegroundColor Green
Write-Host " CHUNK 2 EXECUTION COMPLETE " -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host "Please copy the output and paste it back to the agent." -ForegroundColor Cyan
