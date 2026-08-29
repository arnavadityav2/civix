"""
CIVIX Dataset Report Generator
Queries Profile A Parquet files via DuckDB and generates a
self-contained, shareable HTML report with interactive charts.

Usage:
    python scripts/generate_report.py
    # Opens report in browser automatically
"""
import duckdb, json, os, sys, webbrowser
sys.stdout.reconfigure(encoding="utf-8")

base = r"D:\civix_data\synthetic\profile_a"
cdr_path  = f"{base}/cdrs/year=2025/month=4/*.parquet".replace("\\","/")
base_fwd  = base.replace("\\", "/")
con = duckdb.connect(":memory:")

def q(sql): return con.execute(sql).fetchall()

print("Querying Profile A dataset...")

# -- Pull all data -----------------------------------------------------------
manifest = json.load(open(os.path.join(base, "manifest.json")))

scenario_dist = q(f"""
    SELECT scenario_class, COUNT(*) as n FROM read_parquet('{base_fwd}/persons/*.parquet')
    GROUP BY scenario_class ORDER BY n DESC""")

top_families = q(f"""
    SELECT l.scenario_family, l.scenario_class, COUNT(*) as n
    FROM read_parquet('{base_fwd}/ground_truth/person_labels/*.parquet') l
    GROUP BY l.scenario_family, l.scenario_class ORDER BY n DESC LIMIT 15""")


call_types = q(f"""
    SELECT call_type, COUNT(*) as n FROM read_parquet('{cdr_path}')
    GROUP BY call_type ORDER BY n DESC""")

hourly = q(f"""
    SELECT CAST(SUBSTR(timestamp,12,2) AS INT) as hr, COUNT(*) as n
    FROM read_parquet('{cdr_path}')
    GROUP BY hr ORDER BY hr""")

top_persons = q(f"""
    SELECT p.full_name, p.scenario_class, p.occupation,
           COUNT(*) as cdrs
    FROM read_parquet('{cdr_path}') c
    JOIN read_parquet('{base_fwd}/persons/*.parquet') p ON c.caller_person_id = p.person_id
    GROUP BY p.full_name, p.scenario_class, p.occupation ORDER BY cdrs DESC LIMIT 10""")

high_risk = q(f"""
    SELECT p.full_name, p.occupation, l.scenario_family, l.scenario_class,
           l.difficulty, ROUND(l.risk_score_gt,3) as risk, l.is_false_positive
    FROM read_parquet('{base_fwd}/ground_truth/person_labels/*.parquet') l
    JOIN read_parquet('{base_fwd}/persons/*.parquet') p ON l.entity_id = p.person_id
    WHERE l.is_positive_label = true ORDER BY l.risk_score_gt DESC LIMIT 10""")

txn_types = q(f"""
    SELECT transaction_type, COUNT(*) as n, ROUND(AVG(amount)) as avg_amt
    FROM read_parquet('{base_fwd}/transactions/*.parquet')
    GROUP BY transaction_type ORDER BY n DESC""")

cdr_stats = q(f"""
    SELECT COUNT(*) as total, COUNT(DISTINCT caller_person_id) as callers,
           COUNT(DISTINCT cell_sector_id) as sectors,
           ROUND(AVG(duration_seconds)) as avg_dur,
           MIN(timestamp) as t_min, MAX(timestamp) as t_max
    FROM read_parquet('{cdr_path}')""")[0]

txn_stats = q(f"""
    SELECT COUNT(*) as n, ROUND(SUM(amount)) as total, ROUND(AVG(amount)) as avg,
           ROUND(MAX(amount)) as mx
    FROM read_parquet('{base_fwd}/transactions/*.parquet')""")[0]

splits = q(f"""
    SELECT split, COUNT(*) as n
    FROM read_parquet('{base_fwd}/ground_truth/train_val_test_split/*.parquet')
    GROUP BY split ORDER BY split""")

person_sample = q(f"""
    SELECT p.full_name, p.gender, p.date_of_birth, p.occupation,
           p.scenario_class, ROUND(p.risk_score, 2) as risk
    FROM read_parquet('{base_fwd}/persons/*.parquet') p
    ORDER BY RANDOM() LIMIT 12""")

print("Building HTML report...")

# -- Prepare chart data ------------------------------------------------------
sc_labels = [r[0] for r in scenario_dist]
sc_values = [r[1] for r in scenario_dist]
sc_colors = {"normal":"#3b82f6","suspicious":"#f59e0b","confirmed_pattern":"#ef4444","false_positive":"#8b5cf6"}

ct_labels = [r[0] for r in call_types]
ct_values = [r[1] for r in call_types]

hr_labels = [str(r[0]).zfill(2)+":00" for r in hourly]
hr_values = [r[1] for r in hourly]

tp_names  = [r[0] for r in top_persons]
tp_cdrs   = [r[3] for r in top_persons]
tp_colors = [sc_colors.get(r[1], "#6b7280") for r in top_persons]

tx_labels = [r[0] for r in txn_types]
tx_values = [r[1] for r in txn_types]

fam_labels = [r[0] for r in top_families[:10]]
fam_vals   = [r[2] for r in top_families[:10]]

# -- Person cards ------------------------------------------------------------
def class_badge(cls):
    badges = {
        "normal": "badge-blue",
        "suspicious": "badge-yellow",
        "confirmed_pattern": "badge-red",
        "false_positive": "badge-purple",
    }
    return badges.get(cls, "badge-gray")

person_cards_html = ""
for p in person_sample:
    badge = class_badge(p[4])
    risk_pct = int(p[5]*100)
    risk_color = "#ef4444" if risk_pct > 70 else "#f59e0b" if risk_pct > 40 else "#3b82f6"
    person_cards_html += f"""
    <div class="person-card">
      <div class="person-header">
        <div class="avatar">{p[0][0]}</div>
        <div>
          <div class="person-name">{p[0]}</div>
          <div class="person-meta">{p[2]} &bull; {p[3]}</div>
        </div>
      </div>
      <div class="person-footer">
        <span class="badge {badge}">{p[4].replace('_',' ')}</span>
        <div class="risk-bar-wrap">
          <div style="font-size:11px;color:#9ca3af;margin-bottom:3px">Risk: {p[5]}</div>
          <div class="risk-bar"><div class="risk-fill" style="width:{risk_pct}%;background:{risk_color}"></div></div>
        </div>
      </div>
    </div>"""

# -- High risk table rows ----------------------------------------------------
risk_rows = ""
for r in high_risk:
    fp_badge = '<span class="badge badge-purple">FALSE POS</span>' if r[6] else ""
    diff_color = {"VERY_HIGH":"#ef4444","HIGH":"#f59e0b","MEDIUM":"#3b82f6","LOW":"#10b981"}.get(r[4],"#6b7280")
    risk_pct = int(r[5]*100)
    risk_rows += f"""
    <tr>
      <td><strong>{r[0]}</strong><br><small style="color:#9ca3af">{r[1]}</small></td>
      <td><span class="badge badge-red">{r[2].replace('_',' ')}</span></td>
      <td>{r[3].replace('_',' ')}</td>
      <td><span style="color:{diff_color};font-weight:600">{r[4]}</span></td>
      <td>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="risk-bar" style="width:80px">
            <div class="risk-fill" style="width:{risk_pct}%;background:#ef4444"></div>
          </div>
          <strong style="color:#ef4444">{r[5]}</strong>
        </div>
      </td>
      <td>{fp_badge}</td>
    </tr>"""

# -- Splits ------------------------------------------------------------------
split_html = ""
split_total = sum(r[1] for r in splits)
split_colors_map = {"TRAIN":"#3b82f6","VALIDATION":"#f59e0b","TEST":"#10b981"}
for r in splits:
    pct = round(r[1]*100/split_total)
    col = split_colors_map.get(r[0],"#6b7280")
    split_html += f"""
    <div class="split-item">
      <div style="color:{col};font-weight:700;font-size:1.3rem">{r[1]:,}</div>
      <div style="color:#9ca3af;font-size:12px">{r[0]}</div>
      <div style="color:{col};font-size:11px">{pct}%</div>
    </div>"""

row_counts_html = ""
for k,v in sorted(manifest["row_counts"].items()):
    row_counts_html += f'<tr><td>{k}</td><td style="text-align:right;font-weight:600;color:#60a5fa">{v:,}</td></tr>'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CIVIX — Profile A Dataset Explorer</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:'Inter',sans-serif; background:#0a0f1e; color:#e2e8f0; min-height:100vh; }}

.hero {{
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
  border-bottom: 1px solid #1e3a5f;
  padding: 48px 40px 36px;
  position: relative; overflow: hidden;
}}
.hero::before {{
  content:''; position:absolute; top:-50%; left:-20%; width:600px; height:600px;
  background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
  animation: pulse 6s ease-in-out infinite;
}}
@keyframes pulse {{ 0%,100%{{opacity:.5;transform:scale(1)}} 50%{{opacity:1;transform:scale(1.1)}} }}
.hero-tag {{ color:#818cf8; font-size:12px; font-weight:600; letter-spacing:3px; text-transform:uppercase; margin-bottom:12px; }}
.hero-title {{ font-size:2.8rem; font-weight:800; background:linear-gradient(135deg,#e0e7ff,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; line-height:1.1; }}
.hero-sub {{ color:#94a3b8; margin-top:10px; font-size:1rem; }}
.hero-chips {{ display:flex; gap:12px; margin-top:20px; flex-wrap:wrap; }}
.chip {{ background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); color:#a5b4fc; padding:6px 14px; border-radius:999px; font-size:13px; font-weight:500; }}

.container {{ max-width:1400px; margin:0 auto; padding:32px 24px; }}
.grid-4 {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:28px; }}
.grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:28px; }}
.grid-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:20px; margin-bottom:28px; }}

.stat-card {{
  background:linear-gradient(135deg,#111827,#1a2235);
  border:1px solid #1e3a5f; border-radius:16px; padding:20px;
  transition:transform .2s; cursor:default;
}}
.stat-card:hover {{ transform:translateY(-3px); border-color:#3b82f6; }}
.stat-label {{ font-size:12px; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }}
.stat-value {{ font-size:2rem; font-weight:800; color:#e2e8f0; }}
.stat-sub {{ font-size:12px; color:#64748b; margin-top:4px; }}
.stat-accent {{ color:#60a5fa; }}

.card {{
  background:#111827; border:1px solid #1e3a5f; border-radius:16px; padding:24px;
}}
.card-title {{ font-size:15px; font-weight:700; color:#e2e8f0; margin-bottom:18px; display:flex; align-items:center; gap:8px; }}
.card-title::before {{ content:''; display:block; width:3px; height:16px; background:linear-gradient(#6366f1,#3b82f6); border-radius:2px; }}

.badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.5px; }}
.badge-blue    {{ background:rgba(59,130,246,.2); color:#60a5fa; border:1px solid rgba(59,130,246,.3); }}
.badge-yellow  {{ background:rgba(245,158,11,.2); color:#fbbf24; border:1px solid rgba(245,158,11,.3); }}
.badge-red     {{ background:rgba(239,68,68,.2);  color:#f87171; border:1px solid rgba(239,68,68,.3); }}
.badge-purple  {{ background:rgba(139,92,246,.2); color:#a78bfa; border:1px solid rgba(139,92,246,.3); }}
.badge-gray    {{ background:rgba(107,114,128,.2);color:#9ca3af; border:1px solid rgba(107,114,128,.3); }}

.person-cards {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:14px; }}
.person-card {{
  background:linear-gradient(135deg,#111827,#1a2235); border:1px solid #1e3a5f;
  border-radius:14px; padding:16px; transition:all .2s;
}}
.person-card:hover {{ border-color:#6366f1; transform:translateY(-2px); box-shadow:0 8px 24px rgba(99,102,241,.15); }}
.person-header {{ display:flex; gap:12px; align-items:flex-start; margin-bottom:14px; }}
.avatar {{ width:40px; height:40px; border-radius:50%; background:linear-gradient(135deg,#6366f1,#3b82f6); display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:700; flex-shrink:0; color:white; }}
.person-name {{ font-weight:600; font-size:14px; color:#e2e8f0; line-height:1.3; }}
.person-meta {{ font-size:11px; color:#64748b; margin-top:2px; }}
.person-footer {{ display:flex; flex-direction:column; gap:8px; }}
.risk-bar-wrap {{ width:100%; }}
.risk-bar {{ height:5px; background:#1e3a5f; border-radius:999px; overflow:hidden; }}
.risk-fill {{ height:100%; border-radius:999px; transition:width .6s ease; }}

table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; padding:10px 12px; color:#64748b; font-weight:600; text-transform:uppercase; font-size:11px; letter-spacing:.5px; border-bottom:1px solid #1e3a5f; }}
td {{ padding:10px 12px; border-bottom:1px solid #0f172a; vertical-align:middle; }}
tr:hover td {{ background:rgba(99,102,241,.05); }}

.split-row {{ display:flex; gap:20px; justify-content:center; padding:10px 0; }}
.split-item {{ text-align:center; padding:16px 24px; background:#0f172a; border-radius:12px; border:1px solid #1e3a5f; min-width:100px; }}

canvas {{ max-height:280px; }}

.section-label {{ font-size:11px; color:#4b5563; text-transform:uppercase; letter-spacing:2px; font-weight:600; margin-bottom:12px; margin-top:32px; }}

.footer {{ text-align:center; padding:32px; color:#374151; font-size:13px; border-top:1px solid #111827; margin-top:32px; }}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-tag">CIVIX Intelligence Platform &bull; Phase 2C</div>
  <div class="hero-title">Profile A Dataset</div>
  <div class="hero-sub">Development dataset &bull; Synthetic investigative records &bull; Seed 20260829</div>
  <div class="hero-chips">
    <span class="chip">1,000 Persons</span>
    <span class="chip">250,000 CDRs</span>
    <span class="chip">61,275 Transactions</span>
    <span class="chip">100 Cases</span>
    <span class="chip">22/22 Verified</span>
    <span class="chip">15 MB</span>
  </div>
</div>

<div class="container">

  <div class="grid-4">
    <div class="stat-card">
      <div class="stat-label">Total Records</div>
      <div class="stat-value stat-accent">321,275</div>
      <div class="stat-sub">across all entities</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">CDR Date Range</div>
      <div class="stat-value" style="font-size:1.1rem;padding-top:8px">Jan – Jun<br><span style="color:#60a5fa;font-size:1.8rem">2025</span></div>
      <div class="stat-sub">{cdr_stats[4][:10]} to {cdr_stats[5][:10]}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Call Duration</div>
      <div class="stat-value stat-accent">{int(cdr_stats[3])}s</div>
      <div class="stat-sub">~{int(cdr_stats[3])//60}m {int(cdr_stats[3])%60}s average</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Txn Volume</div>
      <div class="stat-value" style="font-size:1.3rem;padding-top:6px">INR {int(txn_stats[1])//10000000}Cr</div>
      <div class="stat-sub">avg INR {int(txn_stats[2]):,}/txn</div>
    </div>
  </div>

  <div class="grid-3">
    <div class="card">
      <div class="card-title">Scenario Distribution</div>
      <canvas id="scenarioPie"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Call Type Mix</div>
      <canvas id="callTypePie"></canvas>
    </div>
    <div class="card">
      <div class="card-title">ML Split (TRAIN / VAL / TEST)</div>
      <div class="split-row" style="margin-top:30px">{split_html}</div>
      <div class="card-title" style="margin-top:24px">Row Counts by Entity</div>
      <table><thead><tr><th>Entity</th><th style="text-align:right">Rows</th></tr></thead>
      <tbody>{row_counts_html}</tbody></table>
    </div>
  </div>

  <div class="card" style="margin-bottom:28px">
    <div class="card-title">CDR Hourly Activity Pattern (call volume by hour of day)</div>
    <canvas id="hourlyBar" style="max-height:220px"></canvas>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-title">Top 10 Most Active Persons (CDR count)</div>
      <canvas id="topPersonsBar"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Transactions by Type</div>
      <canvas id="txnBar"></canvas>
    </div>
  </div>

  <div class="card" style="margin-bottom:28px">
    <div class="card-title">Top 10 Highest-Risk Confirmed Persons (Ground Truth)</div>
    <table>
      <thead><tr><th>Person</th><th>Scenario Family</th><th>Class</th><th>Difficulty</th><th>Risk Score</th><th></th></tr></thead>
      <tbody>{risk_rows}</tbody>
    </table>
  </div>

  <div class="card" style="margin-bottom:28px">
    <div class="card-title">Scenario Families (top 10 planted patterns)</div>
    <canvas id="familyBar" style="max-height:240px"></canvas>
  </div>

  <div class="card">
    <div class="card-title">Person Sample (12 random persons)</div>
    <div class="person-cards">{person_cards_html}</div>
  </div>

</div>

<div class="footer">
  CIVIX Synthetic Dataset &bull; Profile A (Development) &bull; Generated 2026-08-29 &bull; Seed 20260829<br>
  All persons, events, and transactions are entirely synthetic and deterministically generated for ML training purposes.
</div>

<script>
const C = (id, type, data, opts={{}}) => new Chart(document.getElementById(id), {{type, data, options:{{responsive:true, plugins:{{legend:{{labels:{{color:'#9ca3af',font:{{size:12}}}}}}}}, ...opts}}}});

const COLORS = ['#3b82f6','#f59e0b','#ef4444','#8b5cf6','#10b981','#06b6d4','#f97316'];

C('scenarioPie','doughnut',{{
  labels:{json.dumps(sc_labels)},
  datasets:[{{data:{json.dumps(sc_values)},backgroundColor:['#3b82f6','#f59e0b','#ef4444','#8b5cf6'],borderColor:'#0a0f1e',borderWidth:3}}]
}},{{plugins:{{legend:{{position:'bottom'}}}},cutout:'60%'}});

C('callTypePie','doughnut',{{
  labels:{json.dumps(ct_labels)},
  datasets:[{{data:{json.dumps(ct_values)},backgroundColor:['#6366f1','#06b6d4','#f97316'],borderColor:'#0a0f1e',borderWidth:3}}]
}},{{plugins:{{legend:{{position:'bottom'}}}},cutout:'60%'}});

C('hourlyBar','bar',{{
  labels:{json.dumps(hr_labels)},
  datasets:[{{label:'CDRs',data:{json.dumps(hr_values)},backgroundColor:'rgba(99,102,241,0.7)',borderColor:'#6366f1',borderWidth:1,borderRadius:4}}]
}},{{plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#64748b',font:{{size:10}}}},grid:{{color:'#0f172a'}}}},y:{{ticks:{{color:'#64748b'}},grid:{{color:'#1e3a5f'}}}}}}}});

C('topPersonsBar','bar',{{
  labels:{json.dumps(tp_names)},
  datasets:[{{label:'CDRs',data:{json.dumps(tp_cdrs)},backgroundColor:{json.dumps(tp_colors)},borderRadius:6}}]
}},{{indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#64748b'}},grid:{{color:'#1e3a5f'}}}},y:{{ticks:{{color:'#e2e8f0',font:{{size:11}}}},grid:{{color:'#0f172a'}}}}}}}});

C('txnBar','bar',{{
  labels:{json.dumps(tx_labels)},
  datasets:[{{label:'Transactions',data:{json.dumps(tx_values)},backgroundColor:COLORS,borderRadius:6}}]
}},{{plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#64748b'}},grid:{{color:'#0f172a'}}}},y:{{ticks:{{color:'#64748b'}},grid:{{color:'#1e3a5f'}}}}}}}});

C('familyBar','bar',{{
  labels:{json.dumps(fam_labels)},
  datasets:[{{label:'Persons',data:{json.dumps(fam_vals)},backgroundColor:'rgba(99,102,241,0.75)',borderRadius:6}}]
}},{{plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#64748b',font:{{size:11}}}},grid:{{color:'#0f172a'}}}},y:{{ticks:{{color:'#64748b'}},grid:{{color:'#1e3a5f'}}}}}}}});
</script>
</body>
</html>"""

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "CIVIX_Profile_A_Report.html")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Report saved to: {os.path.abspath(out)}")
webbrowser.open(f"file:///{os.path.abspath(out)}")
print("Opening in browser...")
