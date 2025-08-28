#!/usr/bin/env python3
import os
import re
import csv
import sys
import json
import shlex
import math
import html
import tempfile
import subprocess
from urllib.parse import quote_plus

# Config
OUT_DIR = os.path.join('.', 'review_out')
RAW_TEXT_DIR = os.path.join(OUT_DIR, 'raw_text')
PAGE_IMG_DIR = os.path.join(OUT_DIR, 'page_images')
EVIDENCE_DIR = os.path.join(OUT_DIR, 'evidence')

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RAW_TEXT_DIR, exist_ok=True)
os.makedirs(PAGE_IMG_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)


def run(cmd, input_bytes=None, check=False, capture=True, text=False):
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
    try:
        res = subprocess.run(cmd, input=input_bytes, check=check,
                             stdout=(subprocess.PIPE if capture else None),
                             stderr=(subprocess.PIPE if capture else None),
                             shell=shell, text=text)
        return res
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, 127, b'', b'command not found')


def which(prog):
    res = run(['bash', '-lc', f'which {shlex.quote(prog)}'])
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return None


def have_tool(name):
    return which(name) is not None


TESS = which('tesseract')
PDFTOTEXT = which('pdftotext')
PDFTOPPM = which('pdftoppm')
PDFINFO = which('pdfinfo') or which('mdls')  # fallback mdls on macOS
CONVERT = which('convert') or which('magick')  # ImageMagick
SIPS = which('sips')  # macOS image tool


def safe_basename(path):
    base = os.path.basename(path)
    # Normalize spaces and parentheses for filenames used in outputs
    base = base.replace(' ', '_').replace('(', '').replace(')', '')
    return base


def pdf_num_pages(pdf_path):
    if which('pdfinfo'):
        res = run(['pdfinfo', pdf_path], capture=True, text=True)
        if res.returncode == 0:
            m = re.search(r'^Pages:\s*(\d+)', res.stdout, re.M)
            if m:
                return int(m.group(1))
    # Fallback: try mdls (macOS) to get page count
    if which('mdls'):
        res = run(['mdls', '-name', 'kMDItemNumberOfPages', pdf_path], capture=True, text=True)
        if res.returncode == 0:
            m = re.search(r'kMDItemNumberOfPages\s*=\s*(\d+)', res.stdout)
            if m:
                return int(m.group(1))
    # Last resort: try pdftoppm to render page 1 until it fails
    if PDFTOPPM:
        # Try rendering page 1; if that works, assume at least 1 page
        return 1
    return 0


def pdftotext_page(pdf_path, page_num):
    if not PDFTOTEXT:
        return ''
    # Extract single page to stdout
    res = run(['pdftotext', '-layout', '-nopgbrk', '-f', str(page_num), '-l', str(page_num), pdf_path, '-'], capture=True)
    if res.returncode == 0:
        return res.stdout.decode('utf-8', errors='ignore')
    return ''


def render_pdf_page_to_png(pdf_path, page_num, out_png_path):
    if not PDFTOPPM:
        return False
    out_prefix = os.path.splitext(out_png_path)[0]
    # pdftoppm numbers pages starting at 1; use -singlefile to prevent suffixes
    res = run(['pdftoppm', '-f', str(page_num), '-l', str(page_num), '-png', '-singlefile', pdf_path, out_prefix])
    return res.returncode == 0 and os.path.exists(out_png_path)


def tesseract_ocr(image_path, out_base_noext):
    tex_out = out_base_noext + '.txt'
    hocr_out = out_base_noext + '.hocr'
    tsv_out = out_base_noext + '.tsv'
    # Text
    run([TESS, image_path, out_base_noext, '-l', 'eng', '--psm', '6', '--oem', '1'])
    # hOCR
    run([TESS, image_path, out_base_noext, '-l', 'eng', '--psm', '6', '--oem', '1', 'hocr'])
    # TSV
    run([TESS, image_path, out_base_noext, '-l', 'eng', '--psm', '6', '--oem', '1', 'tsv'])
    return tex_out, hocr_out, tsv_out


def tesseract_osd(image_path):
    # Orientation/Script detection
    res = run([TESS, image_path, 'stdout', '--psm', '0', 'osd'], capture=True, text=True)
    if res.returncode == 0:
        return res.stdout
    return ''


def save_text(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def load_text(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ''


def avg_conf_from_tsv(tsv_path):
    try:
        with open(tsv_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return None
    confs = []
    if not lines:
        return None
    header = lines[0].split('\t')
    try:
        idx_conf = header.index('conf')
    except ValueError:
        return None
    for ln in lines[1:]:
        parts = ln.split('\t')
        if len(parts) <= idx_conf:
            continue
        try:
            c = int(parts[idx_conf])
        except ValueError:
            continue
        if c >= 0:
            confs.append(c)
    if not confs:
        return None
    return sum(confs)/len(confs)


def parse_hocr_boxes(hocr_path):
    # Return list of (text, (x0,y0,x1,y1)) word boxes
    try:
        with open(hocr_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
    except FileNotFoundError:
        return []
    # Find spans with title="bbox x0 y0 x1 y1"
    boxes = []
    for m in re.finditer(r'<span[^>]*class="ocrx_word"[^>]*title="[^"]*bbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)[^"]*"[^>]*>(.*?)</span>', data, re.S|re.I):
        x0, y0, x1, y1 = map(int, m.group(1,2,3,4))
        txt = re.sub('<[^<]+?>', '', m.group(5))
        txt = html.unescape(txt)
        txt = txt.strip()
        if txt:
            boxes.append((txt, (x0,y0,x1,y1)))
    return boxes


def find_text_bbox(target_text, boxes):
    # Very simple matching: split target into words and try to find sequence in boxes
    words = [w for w in re.split(r'\s+', target_text.strip()) if w]
    if not words:
        return None
    # Normalize
    wnorm = [re.sub(r'[^0-9A-Za-z%°₹$.,/\\-]+', '', w).lower() for w in words]
    box_words = [re.sub(r'[^0-9A-Za-z%°₹$.,/\\-]+', '', t).lower() for (t,_) in boxes]
    n = len(wnorm)
    for i in range(0, max(0, len(box_words)-n)+1):
        if box_words[i:i+n] == wnorm:
            # Union bbox
            xs = []
            ys = []
            for j in range(n):
                x0,y0,x1,y1 = boxes[i+j][1]
                xs += [x0,x1]
                ys += [y0,y1]
            return (min(xs), min(ys), max(xs), max(ys))
    return None


def crop_evidence(image_path, bbox, out_path, pad=10):
    x0,y0,x1,y1 = bbox
    w = max(1, x1 - x0 + 2*pad)
    h = max(1, y1 - y0 + 2*pad)
    x = max(0, x0 - pad)
    y = max(0, y0 - pad)
    if CONVERT:
        # Use ImageMagick convert
        cmd = [CONVERT, image_path, '-crop', f'{w}x{h}+{x}+{y}', '+repage', out_path]
        res = run(cmd)
        return res.returncode == 0 and os.path.exists(out_path)
    elif SIPS:
        # sips requires cropping in place; copy first
        import shutil
        shutil.copyfile(image_path, out_path)
        # sips -c height width --cropOffset x y out_path
        res = run([SIPS, '-c', str(h), str(w), '--cropOffset', str(x), str(y), out_path])
        return res.returncode == 0 and os.path.exists(out_path)
    else:
        return False


# Simple numeric expression evaluator (safe)
import ast
import operator as op

OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.Mod: op.mod,
}


def eval_num_expr(expr):
    expr = expr.strip()
    expr = expr.replace('π', str(math.pi))
    expr = expr.replace('–', '-')  # en dash
    expr = expr.replace('−', '-')  # minus
    expr = expr.replace('×', '*')
    expr = expr.replace('÷', '/')
    # Remove units and stray characters
    expr = re.sub(r'(?<=\d)\s*(cm|m|km|mm|kg|g|mg|l|L|°|%)\b', '', expr)
    try:
        node = ast.parse(expr, mode='eval').body
    except Exception:
        return None
    def _eval(n):
        if isinstance(n, ast.Num):
            return n.n
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            a = _eval(n.left)
            b = _eval(n.right)
            if a is None or b is None:
                return None
            try:
                return OPS[type(n.op)](a, b)
            except Exception:
                return None
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            v = _eval(n.operand)
            if v is None:
                return None
            try:
                return OPS[type(n.op)](v)
            except Exception:
                return None
        return None
    return _eval(node)


PROB_PATTERNS = [
    re.compile(r'^(?:Question|Qn|Que|Q|Problem|Exercise|Ex)\s*[:.]?\s*([0-9]+[a-zA-Z]?)', re.I),
    re.compile(r'^\(?\s*([0-9]{1,3})\s*\)?\s*[).:-]\s+'),
    re.compile(r'^\s*([ivxlcdm]+)\)\s+', re.I),
]


def split_problems(text):
    lines = text.splitlines()
    idxs = []
    labels = []
    for i, ln in enumerate(lines):
        for pat in PROB_PATTERNS:
            m = pat.match(ln.strip())
            if m:
                idxs.append(i)
                labels.append(m.group(1) if m.groups() else str(len(idxs)))
                break
    if not idxs:
        # treat as single problem
        return [{'problem_id': '1', 'text': text}]
    idxs.append(len(lines))
    problems = []
    for k in range(len(idxs)-1):
        start = idxs[k]
        end = idxs[k+1]
        chunk = '\n'.join(lines[start:end]).strip()
        pid = labels[k] if k < len(labels) else str(k+1)
        problems.append({'problem_id': pid, 'text': chunk})
    return problems


UNIT_TOKENS = ['cm','mm','m','km','kg','g','mg','L','l','ml','₹','Rs','%','degree','degrees','°']


def detect_final_answer(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    final = ''
    for ln in reversed(lines):
        if re.search(r'^(Ans|Answer)\s*[:\-]', ln, re.I):
            final = ln
            break
        if re.search(r'^(Thus|Therefore|Hence)[,:\-\s]', ln, re.I):
            final = ln
            break
        if re.search(r'=\s*[^=]+$', ln):
            final = ln
            break
    return final or (lines[-1] if lines else '')


def check_equations(lines):
    issues = []
    for i, ln in enumerate(lines):
        # Split potential multi equations
        parts = re.split(r'(?<![<>])\s=\s', ln)
        if len(parts) >= 2:
            left = parts[0]
            right = ' = '.join(parts[1:])
            lv = eval_num_expr(left)
            rv = eval_num_expr(right)
            if lv is not None and rv is not None:
                if not math.isfinite(lv) or not math.isfinite(rv):
                    continue
                if abs(lv - rv) > 1e-6 * (1 + abs(rv)):
                    issues.append({
                        'issue_type': 'Arithmetic error',
                        'detail': f"Line {i+1}: {left.strip()} = {right.strip()} (computed {lv} ≠ {rv})",
                        'confidence': 0.9,
                    })
    return issues


def check_units(problem_text, final_answer):
    issues = []
    mentions = [u for u in UNIT_TOKENS if re.search(rf'\b{re.escape(u)}\b', problem_text)]
    if mentions and not any(re.search(rf'\b{re.escape(u)}\b', final_answer) for u in mentions):
        issues.append({
            'issue_type': 'Missing units',
            'detail': f"Problem mentions units {', '.join(sorted(set(mentions)))} but final answer lacks units.",
            'confidence': 0.7,
        })
    return issues


def check_rounding(final_answer):
    issues = []
    m = re.search(r'(\d+\.\d+)', final_answer)
    if m and re.search(r'rounded|approx|correct\s*to', final_answer, re.I) is None:
        # If there is a decimal number but no rounding context and problem likely integer
        issues.append({
            'issue_type': 'Rounding/precision',
            'detail': 'Decimal answer without stated rounding; verify required precision.',
            'confidence': 0.5,
        })
    return issues


def check_undefined_symbols(text):
    issues = []
    # Flag standalone symbols that often need definition (k, n, x in sequences)
    if re.search(r'\b(k|n)\b\s*(?:=|\bin\b)', text) is None and re.search(r'\b(k|n)\b', text):
        issues.append({
            'issue_type': 'Undefined symbol',
            'detail': 'Symbol like k/n appears without definition.',
            'confidence': 0.4,
        })
    return issues


def duckduckgo_search(query, max_results=3):
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        res = run(['bash', '-lc', f"curl -A 'Mozilla/5.0' -s --max-time 10 {shlex.quote(url)}"], capture=True, text=True)
        if res.returncode != 0:
            return []
        html_text = res.stdout
        # Extract result links
        links = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"', html_text)
        # Clean DDG redir if present
        cleaned = []
        for l in links:
            l = html.unescape(l)
            cleaned.append(l)
        # Dedup preserving order
        dedup = []
        seen = set()
        for l in cleaned:
            if l not in seen:
                seen.add(l)
                dedup.append(l)
        return dedup[:max_results]
    except Exception:
        return []


def cross_check_web(problem_text):
    # Use first sentence or first ~12 words
    words = re.findall(r'\w+[\w\-]*|[∠°%]', problem_text)
    snippet = ' '.join(words[:12])
    queries = [
        f'Selina Concise Mathematics {snippet}',
        f'Selena Kansai {snippet}',
    ]
    refs = []
    for q in queries:
        refs.extend(duckduckgo_search(q, max_results=2))
    # Dedup
    uniq = []
    seen = set()
    for r in refs:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq[:3]


def analyze_page(file_path, page_num, image_path, hocr_path, tsv_path, text):
    # Split into problems within this page
    problems = split_problems(text)
    findings = []
    issues_rows = []
    evidence_items = []
    avg_conf = avg_conf_from_tsv(tsv_path) if tsv_path else None
    # OSD orientation
    osd = tesseract_osd(image_path) if image_path and TESS else ''
    skew_issue = None
    if osd:
        m = re.search(r'Rotate:\s*(\d+)', osd)
        if m:
            rot = int(m.group(1))
            if rot % 180 != 0:
                skew_issue = {
                    'issue_type': 'Image quality: skew',
                    'detail': f'Orientation suggests rotation {rot}°; consider rescanning/uprighting.',
                    'confidence': 0.6,
                }
    # Edge cutoff detection using hocr boxes
    cutoff_issue = None
    boxes = parse_hocr_boxes(hocr_path) if hocr_path else []
    near_edge = 0
    total = len(boxes)
    if total:
        # Need image size; try identify
        w = h = None
        if CONVERT:
            res = run([CONVERT, image_path, '-format', '%w %h', 'info:'], capture=True, text=True)
            if res.returncode == 0:
                try:
                    w, h = map(int, res.stdout.strip().split())
                except Exception:
                    w = h = None
        elif SIPS:
            # sips -g pixelWidth -g pixelHeight
            res = run([SIPS, '-g', 'pixelWidth', '-g', 'pixelHeight', image_path], capture=True, text=True)
            if res.returncode == 0:
                mw = re.search(r'pixelWidth:\s*(\d+)', res.stdout)
                mh = re.search(r'pixelHeight:\s*(\d+)', res.stdout)
                if mw and mh:
                    w = int(mw.group(1)); h = int(mh.group(1))
        for _, (x0,y0,x1,y1) in boxes:
            if w is not None:
                if x0 < 5 or x1 > w-5:
                    near_edge += 1
        if total > 0 and near_edge/total > 0.15:
            cutoff_issue = {
                'issue_type': 'Image quality: cut-off margins',
                'detail': f'{near_edge}/{total} words touch page edges; margins may be cropped.',
                'confidence': 0.5,
            }

    # Low confidence implies blur/contrast
    blur_issue = None
    if avg_conf is not None and avg_conf < 70:
        blur_issue = {
            'issue_type': 'Image quality: blur/low contrast',
            'detail': f'Average OCR confidence {avg_conf:.1f} < 70.',
            'confidence': 0.6,
        }

    # Per problem analysis
    for idx, prob in enumerate(problems, start=1):
        pid = prob['problem_id'] or str(idx)
        ptext = prob['text']
        final_ans = detect_final_answer(ptext)
        lines = [ln for ln in ptext.splitlines() if ln.strip()]
        prob_issues = []
        prob_issues += check_equations(lines)
        prob_issues += check_units(ptext, final_ans)
        prob_issues += check_rounding(final_ans)
        prob_issues += check_undefined_symbols(ptext)
        web_refs = cross_check_web(ptext) if ptext.strip() else []

        # Evidence: try crop final answer
        ev_path = None
        if final_ans and boxes:
            bbox = find_text_bbox(final_ans, boxes)
            if bbox:
                ev_name = f"{safe_basename(file_path)}_p{page_num}_prob{pid}_final.png"
                ev_path = os.path.join(EVIDENCE_DIR, ev_name)
                ok = crop_evidence(image_path, bbox, ev_path)
                if not ok:
                    ev_path = None
        # Fallback: crop bottom quarter of the page
        if not ev_path:
            # Determine image size
            w = h = None
            if CONVERT:
                res = run([CONVERT, image_path, '-format', '%w %h', 'info:'], capture=True, text=True)
                if res.returncode == 0:
                    try:
                        w, h = map(int, res.stdout.strip().split())
                    except Exception:
                        w = h = None
            elif SIPS:
                res = run([SIPS, '-g', 'pixelWidth', '-g', 'pixelHeight', image_path], capture=True, text=True)
                if res.returncode == 0:
                    mw = re.search(r'pixelWidth:\s*(\d+)', res.stdout)
                    mh = re.search(r'pixelHeight:\s*(\d+)', res.stdout)
                    if mw and mh:
                        w = int(mw.group(1)); h = int(mh.group(1))
            if w and h:
                x0, y0, x1, y1 = 0, int(h*0.75), w, h
                bbox = (x0, y0, x1, y1)
                ev_name = f"{safe_basename(file_path)}_p{page_num}_prob{pid}_bottom.png"
                ev_path2 = os.path.join(EVIDENCE_DIR, ev_name)
                ok = crop_evidence(image_path, bbox, ev_path2, pad=0)
                if ok:
                    ev_path = ev_path2

        # Add generic image issues once per page to the first problem
        page_issues = []
        if idx == 1:
            if blur_issue:
                page_issues.append(blur_issue)
            if skew_issue:
                page_issues.append(skew_issue)
            if cutoff_issue:
                page_issues.append(cutoff_issue)

        all_issues = page_issues + prob_issues
        for it in all_issues:
            issues_rows.append({
                'file': os.path.basename(file_path),
                'page': page_num,
                'problem_id': pid,
                'issue_type': it['issue_type'],
                'detail': it['detail'],
                'suggestion': suggestion_for_issue(it['issue_type']),
                'confidence': f"{it['confidence']:.2f}",
                'web_refs': ';'.join(web_refs) if web_refs else '',
                'evidence': ev_path or '',
            })

        findings.append({
            'file': os.path.basename(file_path),
            'page': page_num,
            'problem_id': pid,
            'problem_text': ptext[:800],
            'final_answer': final_ans,
            'web_refs': web_refs,
            'issues': all_issues,
            'evidence': ev_path,
        })

    return findings, issues_rows


def suggestion_for_issue(issue_type):
    suggestions = {
        'Arithmetic error': 'Recompute both sides; correct the mistaken step.',
        'Missing units': 'Append correct units to the final answer.',
        'Rounding/precision': 'State required precision and round accordingly.',
        'Undefined symbol': 'Define symbols (e.g., k, n) before use.',
        'Image quality: blur/low contrast': 'Retake photo with better focus/lighting or scan.',
        'Image quality: skew': 'Rotate or rescan to upright orientation.',
        'Image quality: cut-off margins': 'Rescan ensuring full margins are visible.',
    }
    return suggestions.get(issue_type, 'Clarify and justify this step in writing.')


def process_pdf(pdf_path):
    base = safe_basename(pdf_path)
    pages = pdf_num_pages(pdf_path)
    all_findings = []
    all_issues = []
    if pages <= 0:
        return all_findings, all_issues
    for p in range(1, pages+1):
        text = pdftotext_page(pdf_path, p)
        raw_text_path = os.path.join(RAW_TEXT_DIR, f"{base}_p{p}.txt")
        save_text(raw_text_path, text)
        # Render page to image
        img_path = os.path.join(PAGE_IMG_DIR, f"{base}_p{p}.png")
        if not os.path.exists(img_path):
            render_pdf_page_to_png(pdf_path, p, img_path)
        # OCR on image for hOCR/TSV even if text exists
        ocr_base = os.path.join(PAGE_IMG_DIR, f"{base}_p{p}")
        _, hocr_path, tsv_path = tesseract_ocr(img_path, ocr_base)

        findings, issues_rows = analyze_page(pdf_path, p, img_path, hocr_path, tsv_path, text)
        all_findings.extend(findings)
        all_issues.extend(issues_rows)
    return all_findings, all_issues


def process_image(img_path):
    base = safe_basename(img_path)
    # Convert/copy to PNG for consistency
    png_path = os.path.join(PAGE_IMG_DIR, f"{base}_p1.png")
    if CONVERT:
        run([CONVERT, img_path, png_path])
    elif SIPS:
        run([SIPS, img_path, '--setProperty', 'format', 'png', '--out', png_path])
    else:
        # fallback: copy
        import shutil
        shutil.copyfile(img_path, png_path)
    ocr_base = os.path.join(PAGE_IMG_DIR, f"{base}_p1")
    txt_path, hocr_path, tsv_path = tesseract_ocr(png_path, ocr_base)
    text = load_text(txt_path)
    raw_text_path = os.path.join(RAW_TEXT_DIR, f"{base}_p1.txt")
    save_text(raw_text_path, text)
    findings, issues_rows = analyze_page(img_path, 1, png_path, hocr_path, tsv_path, text)
    return findings, issues_rows


def write_reports(all_findings, all_issues):
    # CSV
    csv_path = os.path.join(OUT_DIR, 'review_report.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['file','page','problem_id','issue_type','detail','suggestion','confidence','web_refs','evidence'])
        writer.writeheader()
        for row in all_issues:
            writer.writerow(row)

    # Markdown report
    md_path = os.path.join(OUT_DIR, 'review_report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('# Review Report\n\n')
        if not all_findings:
            f.write('No problems detected or no files processed.\n')
        current_file = None
        current_page = None
        for item in all_findings:
            if (item['file'], item['page']) != (current_file, current_page):
                current_file, current_page = item['file'], item['page']
                f.write(f"\n## {current_file} — Page {current_page}\n\n")
            f.write(f"### Problem {item['problem_id']}\n")
            f.write('Problem text (excerpt):\n\n')
            f.write('> ' + item['problem_text'].replace('\n', '\n> ') + '\n\n')
            f.write(f"Final answer (heuristic): {item['final_answer']}\n\n")
            if item['web_refs']:
                f.write('Web refs:\n')
                for r in item['web_refs']:
                    f.write(f'- {r}\n')
                f.write('\n')
            if item['issues']:
                f.write('Issues:\n')
                for it in item['issues']:
                    f.write(f"- {it['issue_type']}: {it['detail']} (conf {it['confidence']:.2f})\n")
                f.write('\n')
            else:
                f.write('No issues detected.\n\n')

    # Fix plan
    fix_path = os.path.join(OUT_DIR, 'fix_plan.md')
    with open(fix_path, 'w', encoding='utf-8') as f:
        f.write('# Fix Plan\n\n')
        grouped = {}
        for it in all_issues:
            key = (it['file'], it['page'], it['problem_id'])
            grouped.setdefault(key, []).append(it)
        for (file, page, pid), issues in grouped.items():
            f.write(f"## {file} — Page {page} — Problem {pid}\n\n")
            for it in issues:
                f.write(f"- {it['issue_type']}: {it['detail']}\n  - Suggestion: {it['suggestion']}\n  - Evidence: {it.get('evidence','')}\n")
            f.write('\n')


def main():
    # Discover files
    files = []
    for ext in ('*.pdf','*.PDF','*.png','*.PNG','*.jpg','*.JPG','*.jpeg','*.JPEG'):
        for name in sorted([p for p in os.listdir('.') if re.fullmatch(ext.replace('*','.*'), p)]):
            files.append(name)
    # More robust glob
    import glob
    files = sorted(set(glob.glob('*.pdf') + glob.glob('*.PDF') + glob.glob('*.png') + glob.glob('*.PNG') + glob.glob('*.jpg') + glob.glob('*.JPG') + glob.glob('*.jpeg') + glob.glob('*.JPEG')))

    if not files:
        print('No target files found (PDFs or images) in current directory.', file=sys.stderr)
        sys.exit(1)

    all_findings = []
    all_issues = []
    for fp in files:
        try:
            if fp.lower().endswith('.pdf'):
                fnd, iss = process_pdf(fp)
            else:
                fnd, iss = process_image(fp)
            all_findings.extend(fnd)
            all_issues.extend(iss)
        except Exception as e:
            print(f"Error processing {fp}: {e}", file=sys.stderr)

    write_reports(all_findings, all_issues)

    # Print top 10 issues summary to stdout for CLI
    ranked = sorted(all_issues, key=lambda r: float(r.get('confidence','0')), reverse=True)
    print('\nTop issues:')
    for i, it in enumerate(ranked[:10], start=1):
        print(f"{i}. [{it['issue_type']}] {it['file']} p{it['page']} prob {it['problem_id']}: {it['detail']} (conf {it['confidence']})")


if __name__ == '__main__':
    main()
