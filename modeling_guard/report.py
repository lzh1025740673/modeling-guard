"""Self-contained HTML reports; no remote scripts, fonts, or telemetry."""

from html import escape


def render(result):
    def e(value):
        return escape(str(value), quote=True)

    passed = result["status"] == "PASS"
    metric = result["metric"]
    rows = "".join(f"<tr><td>{e(name)}</td><td><code>{e(sha)}</code></td></tr>" for name, sha in result["inputs"].items())
    outputs = "".join(f"<li>{e(name)} <code>{e(sha)}</code></li>" for name, sha in result["outputs"].items()) or "<li>No verified outputs</li>"
    tone = "pass" if passed else "review"
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<title>Modeling Guard · {e(result['title'])}</title>
<style>
:root{{color-scheme:light;--ink:#15332e;--muted:#566962;--line:#d9e3dc;--paper:#f4f7f2}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1060px;margin:0 auto;padding:48px 28px}}header{{display:flex;justify-content:space-between;gap:20px;align-items:center;border-bottom:1px solid var(--line);padding-bottom:22px}}
.brand{{font-weight:800;letter-spacing:.12em;font-size:13px}}.meta,small{{color:var(--muted)}}h1{{font-size:clamp(28px,4vw,44px);line-height:1.2;margin:28px 0 12px}}h2{{font-size:19px;margin:0 0 16px}}p{{margin:10px 0}}
.badge{{border-radius:99px;padding:6px 14px;font-weight:750;font-size:13px;white-space:nowrap}}.pass{{background:#d7efda;color:#215b34}}.review{{background:#ffead0;color:#704117}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0}}.card,section{{background:white;border:1px solid var(--line);border-radius:16px;padding:24px}}.number{{font-size:32px;font-weight:750;letter-spacing:-.04em;overflow-wrap:anywhere}}
section{{margin:18px 0}}code,pre{{font:13px/1.6 ui-monospace,monospace}}code{{overflow-wrap:anywhere}}pre{{white-space:pre-wrap;background:#eff4ef;padding:16px;border-radius:8px}}.table{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{text-align:left;border-bottom:1px solid var(--line);padding:10px 12px 10px 0}}td code{{font-size:11px}}ul{{padding-left:20px}}li{{margin-bottom:10px}}footer{{color:var(--muted);font-size:13px;margin-top:30px}}
@media(max-width:700px){{main{{padding:24px 16px}}.grid{{grid-template-columns:1fr}}header{{align-items:flex-start}}.card,section{{padding:18px}}}}
@media print{{body{{background:white}}main{{padding:0}}section,.card{{break-inside:avoid}}}}
</style></head><body><main>
<header><div class="brand">◈ MODELING GUARD<br><small>EXPERIMENT RECEIPT · 实验验收记录</small></div><span class="badge {tone}">{e(result['status'])}</span></header>
<h1>{e(result['title'])}</h1><p class="meta">Stage / 阶段: {e(result['stage'])} · Reviewer / 审核人: {e(result['approved_by'])}</p>
<p>{e(result['reason'])}</p>
<div class="grid"><div class="card"><small>{e(metric['name'])} / measured</small><div class="number">{e(result['value']) if result['value'] is not None else '—'}</div></div>
<div class="card"><small>Baseline threshold / 基准阈值</small><div class="number">{'≤' if metric['direction']=='min' else '≥'} {e(metric['baseline'])}</div></div>
<div class="card"><small>Runtime / 运行时间</small><div class="number">{e(result['elapsed_seconds'])} s</div></div></div>
<section><h2>01 / What ran · 执行记录</h2><pre>{e(__import__('json').dumps(result['command'], ensure_ascii=False))}</pre><p>Command is an argument array, not a shell command. {{python}} is the interpreter running Modeling Guard.</p><p class="meta">Python {e(result['environment']['python'])} · {e(result['environment']['system'])} · Exit {e(result['exit_code'])}</p></section>
<section><h2>02 / Locked inputs · 锁定输入</h2><div class="table"><table><thead><tr><th>File</th><th>SHA-256</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section><h2>03 / Verified outputs · 输出校验</h2><ul>{outputs}</ul></section>
<section><h2>04 / Teacher review · 教师复核</h2><p>PASS means the declared command, file, and metric checks passed. It does not certify the model, data quality, absence of leakage, or the scientific conclusion.</p><p>PASS 只代表预先声明的检查通过，仍须教师判断数据、模型、信息泄漏与结论。日志和输入快照留在本机，分享前请检查隐私。</p><p>Re-run from the original project using <code>python -m modeling_guard run PROJECT</code>, while the approval and run budget remain valid. The work folder preserves the declared files, not a complete dependency environment.</p></section>
<footer>Run {e(result['run_id'])}<br>{e(result['started_at'])}<br>Modeling Guard {e(result['tool_version'])} · Local record; editable, unsigned, and not an identity or security boundary.</footer>
</main></body></html>'''


def write_report(folder, result):
    (folder / "report.html").write_text(render(result), encoding="utf-8")
    lines = ["# Stage report", "", "Status: " + result["status"], "", result["reason"], "",
             "- Stage: " + result["stage"], "- Run: " + result["run_id"],
             "- Metric: " + str(result["value"]), "- Runtime: " + str(result["elapsed_seconds"]) + " s",
             "", "Stop here. A teacher must interpret the results before changing the route or starting another stage.", ""]
    (folder / "STAGE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    if result["status"] != "PASS":
        (folder / "HUMAN_REVIEW.md").write_text("# Human review required\n\n" + result["reason"] +
            "\n\nInspect console.log, contract.json, result.json and work/. Do not automatically change the model, threshold, data, or budget. Review and explicitly reapprove before retrying.\n", encoding="utf-8")
