#!/usr/bin/env python3
import re
import shlex
import subprocess
from pathlib import Path
import zipfile

ROOT = Path('.')
OUT = ROOT / 'review_out'
FIXED = OUT / 'fixed'


def run(cmd):
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
    return subprocess.run(cmd, shell=shell, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def pdf_pages(pdf_path: Path) -> int:
    if not pdf_path.exists():
        return 0
    # try pdfinfo
    r = run(['bash','-lc', f"pdfinfo {shlex.quote(str(pdf_path))} 2>/dev/null | sed -n 's/^Pages:\s*//p' | head -n 1"])
    if r.returncode == 0 and r.stdout.strip().isdigit():
        return int(r.stdout.strip())
    # fallback: assume >=1
    return 1


def assess_tex(tex: str) -> dict:
    # Focus analysis on Solution section to avoid preamble noise
    sol_block = tex
    m_sol = re.search(r"\\subsection\*\{Solution\}(.*?)(\\subsection\*\{Reviewer notes\}|\\end\{document\})", tex, re.S)
    if m_sol:
        sol_block = m_sol.group(1)
    # Heuristics for completeness within solution body
    has_todo = 'TODO' in sol_block
    has_numeric = bool(re.search(r'(=|≈)\s*\d', sol_block)) or bool(re.search(r'\b\d+\.?\d*\s*(cm|mm|m|km|L|ml|g|kg|%)\b', sol_block))
    mentions_hence = bool(re.search(r'Hence|Therefore', sol_block))
    only_template = '\\begin{enumerate}' in sol_block and not has_numeric
    return {
        'has_todo': has_todo,
        'has_numeric': has_numeric,
        'mentions_hence': mentions_hence,
        'only_template': only_template,
    }


def main():
    problems = []
    for tex_path in sorted(FIXED.glob('prob_*.tex'), key=lambda p: int(re.search(r'prob_(\d+)\.tex', p.name).group(1))):
        idx = int(re.search(r'prob_(\d+)\.tex', tex_path.name).group(1))
        pdf_path = tex_path.with_suffix('.pdf')
        tex = tex_path.read_text(encoding='utf-8', errors='ignore')
        meta = assess_tex(tex)
        pages = pdf_pages(pdf_path)
        pdf_ok = pages >= 1
        # Determine pass/fail
        reasons = []
        status = 'PASS'
        if meta['has_todo']:
            status = 'FAIL'; reasons.append('open TODO present')
        if meta['only_template']:
            status = 'FAIL'; reasons.append('no concrete computation shown')
        if not pdf_ok:
            status = 'FAIL'; reasons.append('PDF missing or zero pages')
        # Consistency with verified question text — we did not verify online here
        reasons.append('question text not externally verified')
        problems.append({
            'idx': idx,
            'pdf': pdf_path,
            'pages': pages,
            'pdf_ok': pdf_ok,
            'meta': meta,
            'status': status,
            'reason': '; '.join(reasons),
        })

    # Write final report
    lines = ['# Final Review Report', '']
    all_pass = True
    open_todos = 0
    for p in problems:
        all_pass = all_pass and (p['status'] == 'PASS')
        if p['meta']['has_todo']:
            open_todos += 1
        lines.append(f"- Problem {p['idx']}: {p['status']} — {p['reason']}")
    lines.append('')
    # Remaining defects
    defects = []
    templ_count = sum(1 for p in problems if p['meta']['only_template'])
    if templ_count:
        defects.append(f"{templ_count} solutions are generic templates without computed results.")
    missing_pdf = [p['idx'] for p in problems if not p['pdf_ok']]
    if missing_pdf:
        defects.append(f"PDF issues in problems: {', '.join(map(str, missing_pdf))}.")
    if open_todos:
        defects.append(f"{open_todos} problems contain TODOs requiring clearer photos.")
    if not defects:
        defects.append('No defects detected beyond lack of external question verification.')
    lines.append('## Remaining Defects / Open TODOs')
    for d in defects:
        lines.append(f"- {d}")
    lines.append('')
    ready = 'Yes' if all_pass else 'No'
    lines.append('## Ready To Share')
    lines.append(f"- Ready: {ready}")
    lines.append(f"- Combined PDF: {'solutions_compiled.pdf exists' if (OUT/'solutions_compiled.pdf').exists() else 'missing'}")
    (OUT / 'final_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    # Build release if all green
    release_path = OUT / 'release.zip'
    if all_pass:
        with zipfile.ZipFile(release_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for pdf in sorted(FIXED.glob('prob_*.pdf'), key=lambda p: int(re.search(r'prob_(\d+)\.pdf', p.name).group(1))):
                z.write(pdf, arcname=pdf.name)
            z.write(OUT / 'contents.md', arcname='contents.md')
            z.write(OUT / 'final_report.md', arcname='final_report.md')
        print(f"Release created: {release_path}")
    else:
        # Remove any stale release
        if release_path.exists():
            release_path.unlink()
        print("Release not created: not all problems passed.")

    # Executive summary
    total = len(problems)
    passes = sum(1 for p in problems if p['status'] == 'PASS')
    fails = total - passes
    print('Summary:')
    print(f"- Problems reviewed: {total}")
    print(f"- Pass: {passes}")
    print(f"- Fail: {fails}")
    print(f"- Combined PDF: {'present' if (OUT/'solutions_compiled.pdf').exists() else 'missing'}")
    print(f"- Final report: {OUT/'final_report.md'}")


if __name__ == '__main__':
    main()
