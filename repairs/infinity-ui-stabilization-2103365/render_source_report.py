#!/usr/bin/env python3
"""Render approved source proof without claiming repaired UI/device acceptance."""
from pathlib import Path
import argparse, html, json

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--inventory',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
 args=parser.parse_args();data=json.loads(args.inventory.read_text());h=html.escape
 def table(headers,rows):
  head='<tr>'+''.join('<th>'+h(x)+'</th>' for x in headers)+'</tr>'
  body=''.join('<tr>'+''.join('<td>'+h(str(x))+'</td>' for x in row)+'</tr>' for row in rows)
  return '<div class="scroll"><table>'+head+body+'</table></div>'
 owner_table=table(['Defect','Source owner / active file','Repair target','Status'],[
  [o['defect']+' — '+o['screen'],o['source_path']+' / '+o['owner'],o['repair_target'],'Source verified; repair pending'] for o in data['owners']])
 delta_table=table(['.201 → .204 file','Protected parent SHA256','Approved .204 SHA256'],[
  [x['path'],x['parent_sha256'],x['approved_sha256']] for x in data['parent_to_approved_delta']])
 hash_table=table(['Approved active source','SHA256'],[[o['source_path'],o['source_sha256']] for o in data['owners']])
 actions=next(o for o in data['owners'] if o['defect']=='U07')['existing_actions']
 action_table=table(['Control ID','Label','Binding'],[[x['id'],x['label'] or '', '; '.join(x['onclick'])] for x in actions])
 preservation=''.join('<li>'+h(x)+'</li>' for x in data['preservation_requirements'])
 dependencies=''.join('<li>'+h(x)+'</li>' for x in data['integration_requirements'])
 text=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Infinity UI — approved .204 source verification</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;background:#f4f7fa;color:#172b40;margin:0}}main{{max-width:1120px;margin:32px auto;padding:32px;background:#fff;border-radius:16px}}h1{{font-size:30px;margin:0 0 10px}}h2{{font-size:22px;margin-top:34px}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border-bottom:1px solid #dbe4ed;padding:12px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}th{{background:#eff4f9}}code{{font-size:12px;overflow-wrap:anywhere}}aside{{padding:18px;border-left:5px solid #2879b8;background:#eef6ff;margin:22px 0}}li{{margin:10px 0}}.small{{color:#52667a;font-size:14px}}.scroll{{overflow:auto}}a{{color:#0068b5}}@media(max-width:700px){{main{{margin:0;padding:20px;border-radius:0}}table{{min-width:680px}}}}</style><main>
<h1>Infinity UI — approved .204 source verified</h1>
<p class="small">Authorized isolated UI workstream • 11 October 2026 • Baseline correction; no UI patches or candidate promotion yet.</p>
<aside><strong>Implementation baseline: Infinity 1.0.5.204 Closing Status Polish RC1.</strong>
<p>Recovered <code>{h(data['approved_package'])}</code>. Its skin ID, version and description match the user-confirmed installed screenshot. The protected repository's original .204 builder reproduced the complete ZIP byte for byte. Use these exact .204 sources for repairs.</p>
<p>The .201 archive is the protected locked parent. The .206 audit package remains diagnostic guidance only. Neither replaces the working .204 UI.</p></aside>
<h2>Exact source identity</h2>
<p><strong>Skin ID:</strong> <code>{h(data['approved_id'])}</code><br><strong>Version:</strong> {h(data['approved_version'])}<br><strong>Description:</strong> {h(data['approved_description'])}<br><strong>Active profile:</strong> <code>unified</code> — 1080 × 2400, aspect 9:20, default enabled.<br><strong>Approved ZIP SHA256:</strong> <code>{h(data['approved_package_sha256'])}</code><br><strong>Source builder:</strong> <code>{h(data['source_builder'])}</code></p>
<p>The screenshot establishes installed identity and description. An independent export of every byte currently on the Fold has not been captured; final device comparison and acceptance remain pending. This limitation does not substitute .206 for the approved recovered .204 source.</p>
<h2>Preservation proof and requirements</h2>
<p>All {len(data['approved_file_hashes']):,} approved package files have SHA256 records. All {data['approved_xml_parse']['passed']} active XML files parsed successfully. The complete .201 → .204 comparison found exactly two changed files, with all other entries byte identical:</p>
{delta_table}
<p>The Power change adds the existing closing acknowledgment, its property transitions and optional motion while retaining the original actions. Its exact .204 hash is protected. No skin XML has been changed during this preparation, so no approved .204 improvement has been overwritten.</p>
<ul>{preservation}</ul>
<h2>Workstream isolation</h2>
<p><strong>UI branch:</strong> <a href="https://github.com/mahfouzhassine8-ops/project-infinity/tree/{h(data['branch'])}">{h(data['branch'])}</a><br><strong>Protected repository baseline:</strong> <code>{h(data['protected_baseline_commit'])}</code><br><strong>Backend branch observed:</strong> <code>{h(data['backend_branch_observed'])}</code><br><strong>Backend head observed:</strong> <code>{h(data['backend_head_observed'])}</code></p>
<p>Only source inventory/report generators and preparation records changed. Native C++, Android lifecycle, Command Center, Resume Hub, provider internals, Health Center classification and build workflows remain untouched. No engine build, backend-branch update, merge, skin installation or release lock occurred.</p>
<h2>Ownership and repair inventory</h2>{owner_table}
<p>The .204 and .206 packages differ only in addon.xml and the Power dialog. The reported dialog/dashboard/navigation files therefore match at source level, but runtime causes, provider ownership and repair acceptance still require their own evidence.</p>
<h2>Existing Health Center actions</h2>
<p>These bindings were read from the approved active .204 XML. They are preservation requirements, not interaction test results.</p>{action_table}
<h2>Theme, adaptive and backend dependencies</h2>
<p>Keep existing InfinityLegacy surface, field, text, secondary, disabled, accent, border and scrim variables and OLED/light/dark/cinema conditions. The source inventory records shared include consumers. Preserve existing native in-place reflow and visible-partial-row touch repairs.</p>
<p>The shared context menu mixes a percentage background height and a fixed 1100-unit auto-height maximum. This remains a source lead consistent with screenshots; it is not a measurement of live Fold bounds. Measure runtime geometry before claiming the root cause or acceptance.</p>
<ul>{dependencies}</ul>
<p>Existing Health bindings: <code>{h(', '.join(data['approved_health_properties']))}</code>. Use the coordinating backend's verified contract for status classifications, current/saved scan times and baseline times; do not infer those semantics from labels.</p>
<h2>Exact active-source hashes</h2>{hash_table}
<p><strong>Audit SHA256:</strong> <code>{h(data['audit_sha256'])}</code><br><strong>Diagnostic ZIP SHA256:</strong> <code>{h(data['diagnostic_zip_sha256'])}</code></p>
<h2>Rollback and verification limits</h2>
<p>Exact current-source rollback: <code>{h(data['approved_package'])}</code>, SHA256 above. Protected parent: <code>{h(data['protected_parent_package'])}</code>, SHA256 <code>{h(data['protected_parent_sha256'])}</code>. Both original archives are retained. Do not automatically revert, downgrade or reset settings.</p>
<p>{h(data['validation_limits'])} Touch, focus, scrolling, Back, provider actions, all Fold/window profiles, themes and the 60–120 minute mixed session remain untested on the physical device. No speed, memory or native stability improvement is claimed.</p>
</main></html>'''
 args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(text)
 print(json.dumps({'report':str(args.out),'bytes':args.out.stat().st_size,'status':data['gate']}))

if __name__=='__main__': main()
