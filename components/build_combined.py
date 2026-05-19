#!/usr/bin/env python3
"""
build_combined.py — Emirates NBD All Components Showcase
Combines all component index.html files into one scrollable page.
Fixes: onclick global scope, asset paths, ID collisions, variable conflicts.
"""

import os, re

COMP_DIR    = "/Users/ram/Documents/MyProject/v3/components"
OUTPUT      = "/Users/ram/Documents/MyProject/v3/components/all-components.html"
ASSETS_ROOT = "../assets"   # relative from components/ to v3/assets/

# ── Low-level helpers ─────────────────────────────────────────────────────────

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def slug(name):
    """'Hero-Image-Left' → 'hero_image_left'"""
    return name.lower().replace("-", "_")

# ── Extraction helpers ────────────────────────────────────────────────────────

def extract_head_style(html):
    """Return the content of the first <style> block in <head>."""
    m = re.search(r'<head[^>]*>(.*?)</head>', html, re.DOTALL | re.I)
    if not m:
        return ""
    styles = re.findall(r'<style[^>]*>(.*?)</style>', m.group(1), re.DOTALL | re.I)
    return "\n".join(styles)

def extract_body(html):
    """Return raw content between <body ...> and </body>."""
    m = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.I)
    return m.group(1) if m else html

def remove_fixed_nav(body):
    """Remove the Back Nav comment + its fixed-position div."""
    body = re.sub(r'<!--\s*Back Nav\s*-->', '', body)
    # Find the fixed top-0 opener and depth-count to its closing </div>
    pat = re.compile(r'<div[^>]*class="[^"]*fixed top-0[^"]*"[^>]*>', re.I)
    m = pat.search(body)
    if not m:
        return body
    pos = m.end()
    depth = 1
    while depth and pos < len(body):
        nxt_open  = re.search(r'<div[\s>]', body[pos:], re.I)
        nxt_close = re.search(r'</div\s*>',  body[pos:], re.I)
        if not nxt_close:
            break
        o = nxt_open.start()  if nxt_open  else len(body)
        c = nxt_close.start() if nxt_close else len(body)
        if o < c:
            depth += 1; pos += o + 1
        else:
            depth -= 1
            if depth == 0:
                return body[:m.start()] + body[pos + nxt_close.end():]
            pos += c + 1
    return body

def remove_padding_divs(body):
    """Remove the ↑ / ↓ page content spacer divs."""
    return re.sub(
        r'<div[^>]*class="[^"]*py-12 px-8 text-center text-sm[^"]*"[^>]*>.*?</div>',
        '', body, flags=re.DOTALL | re.I
    )

def remove_script_tag(html, pattern):
    """Remove a <script> or <link> tag matching pattern."""
    return re.sub(pattern, '', html, flags=re.I | re.DOTALL)

def strip_shared_tags(html):
    """Remove tags that are in the combined <head> (tailwind, fonts, gsap, copy-bridge)."""
    html = remove_script_tag(html, r'<script[^>]*tailwind\.cdn\.js[^>]*>\s*</script>')
    html = remove_script_tag(html, r'<link[^>]*(fonts|tajawal)\.css[^>]*/?\s*>')
    html = remove_script_tag(html, r'<script[^>]*cdnjs\.cloudflare\.com[^>]*>\s*</script>')
    html = remove_script_tag(html, r'<script[^>]*assets/js/gsap\.min\.js[^>]*>\s*</script>')
    html = remove_script_tag(html, r'<script[^>]*assets/js/ScrollTrigger\.min\.js[^>]*>\s*</script>')
    html = remove_script_tag(html, r'<script[^>]*copy-bridge\.js[^>]*>\s*</script>')
    return html

def extract_inline_scripts(html):
    """
    Pull out all non-src non-module inline <script> blocks.
    Returns (list_of_script_contents, html_with_scripts_removed).
    """
    scripts = []
    def replacer(m):
        attrs, content = m.group(1), m.group(2)
        if 'src=' in attrs or 'type="module"' in attrs or "type='module'" in attrs:
            return m.group(0)   # keep external/module scripts in place
        scripts.append(content)
        return ''               # remove inline script from html
    html = re.sub(r'<script([^>]*)>(.*?)</script>', replacer, html, flags=re.DOTALL | re.I)
    return scripts, html

# ── Asset path fixer ─────────────────────────────────────────────────────────

def fix_asset_paths(html, folder_name):
    """
    Fix relative asset references inside a component's HTML.
    - ../../assets/... → ../assets/...   (shared v3 assets)
    - ./assets/...     → FolderName/assets/...  (component-local assets)
    - assets/...       → FolderName/assets/...
    - ./dotted-map.svg → FolderName/dotted-map.svg
    """
    # Shared assets (one level up from components/)
    html = html.replace('../../assets/', f'{ASSETS_ROOT}/')

    # Component-local relative paths: ./something or assets/something
    # Handle src, href, url() patterns
    def prefix_local(m):
        attr, quote, path = m.group(1), m.group(2), m.group(3)
        # Skip already-fixed paths, data URIs, external URLs
        if path.startswith(('../', 'http', 'data:', '//')):
            return m.group(0)
        # Strip leading ./
        clean = path[2:] if path.startswith('./') else path
        return f'{attr}={quote}{folder_name}/{clean}{quote}'

    # src="./..." href="./..." src="assets/..." etc.
    html = re.sub(
        r'(src|href)=(["\'])((?:\./|assets/)[^"\']+)\2',
        prefix_local, html
    )
    # url('./...') or url('assets/...')
    def prefix_url(m):
        quote, path = m.group(1), m.group(2)
        if path.startswith(('../', 'http', 'data:', '//')):
            return m.group(0)
        clean = path[2:] if path.startswith('./') else path
        return f"url({quote}{folder_name}/{clean}{quote})"
    html = re.sub(r"url\((['\"]?)((?:\./|assets/)[^)\"']+)\1\)", prefix_url, html)

    # Fix cobe.js import path (module scripts keep ../../ which was already fixed above)
    html = html.replace("'../../assets/js/cobe.js'", f"'{ASSETS_ROOT}/js/cobe.js'")
    html = html.replace('"../../assets/js/cobe.js"', f'"{ASSETS_ROOT}/js/cobe.js"')

    return html

# ── ID prefixer ───────────────────────────────────────────────────────────────

def prefix_ids(html, comp_slug):
    """
    Prefix all id="..." values with comp_slug to avoid cross-component DOM collisions.
    Also updates getElementById / querySelector('#...') / href="#..." references.
    """
    ids = sorted(set(re.findall(r'\bid=["\']([^"\']+)["\']', html, re.I)), key=len, reverse=True)
    for id_val in ids:
        new_id = f"{comp_slug}_{id_val}"
        html = re.sub(rf'\bid=(["\']){re.escape(id_val)}\1', f'id=\\1{new_id}\\1', html)
        html = re.sub(rf'\bgetElementById\((["\']){re.escape(id_val)}\1\)',
                      f'getElementById(\\1{new_id}\\1)', html)
        html = re.sub(rf"\bquerySelectorAll?\(([\"'])#{re.escape(id_val)}\1\)",
                      lambda m, n=new_id: m.group(0).replace(f'#{id_val}', f'#{n}'), html)
        html = re.sub(rf'\bhref=(["\'])#{re.escape(id_val)}\1', f'href=\\1#{new_id}\\1', html)
    return html

def prefix_ids_in_css(css, ids, comp_slug):
    """Update #foo → #comp_slug_foo in a CSS string."""
    for id_val in sorted(ids, key=len, reverse=True):
        css = re.sub(rf'#{re.escape(id_val)}\b', f'#{comp_slug}_{id_val}', css)
    return css

# ── Script wrapper with global onclick exposure ───────────────────────────────

def wrap_script(script_content, body_html, comp_slug):
    """
    Wraps a component's inline JS in an IIFE.
    Also:
      • Collects ALL functions defined in the script
      • Also scans the script itself for onclick="..." patterns (JS-generated HTML)
      • Exposes every defined function as window['slug__func'] inside the IIFE
      • Updates body_html's onclick handlers to call the window-namespaced versions
    Returns (wrapped_script, updated_body_html).
    """
    # ── 1. Collect ALL function names defined in this script ──────────
    defined_funcs = set()
    # function foo(
    for m in re.finditer(r'\bfunction\s+(\w+)\s*\(', script_content):
        defined_funcs.add(m.group(1))
    # const/let/var foo = function | foo = (
    for m in re.finditer(r'\b(?:const|let|var)\s+(\w+)\s*=\s*(?:function\b|\([^)]*\)\s*=>)', script_content):
        defined_funcs.add(m.group(1))
    # window.foo = function | window.foo = (
    for m in re.finditer(r'\bwindow\.(\w+)\s*=\s*(?:function\b|\()', script_content):
        defined_funcs.add(m.group(1))

    if not defined_funcs:
        # No functions to expose; just wrap
        wrapped = f"<script>\n(function() {{\n{script_content}\n}})();\n</script>"
        return wrapped, body_html

    # ── 2. Build window exposure lines ────────────────────────────────
    expose_lines = []
    name_map = {}   # func → win_key
    for func in sorted(defined_funcs):
        win_key = f"{comp_slug}__{func}"
        name_map[func] = win_key
        expose_lines.append(
            f"  try {{ window['{win_key}'] = {func}; }} catch(e) {{}}"
        )

    # ── 3. Update onclick handlers in static HTML body ────────────────
    updated_body = body_html
    # Sort by length descending to avoid partial replacements (e.g. "go" before "goTo")
    for func in sorted(name_map.keys(), key=len, reverse=True):
        win_key = name_map[func]
        # Replace any `funcname(` inside an on* attribute value string
        # Uses a callback to only replace within the attribute value
        def replace_in_attr(m, fn=func, wk=win_key):
            full  = m.group(0)     # entire on*="..." attribute
            value = m.group(2)     # the attribute value text
            # Replace bare function call: funcname( → window['wk'](
            new_value = re.sub(rf'\b{re.escape(fn)}\s*\(', f"window['{wk}'](", value)
            return m.group(1) + new_value + m.group(3)
        updated_body = re.sub(
            rf'(on\w+=["\'])([^"\']*\b{re.escape(func)}\b[^"\']*)(["\'])',
            replace_in_attr,
            updated_body
        )

    # ── 4. Update function calls in script content ────────────────────
    # Replace bare function calls (not definitions) in the script:
    #   • "funcname(" anywhere NOT preceded by "function " or "."
    #   • Covers onclick inside JS template strings AND recursive calls
    updated_script = script_content
    for func in sorted(name_map.keys(), key=len, reverse=True):
        win_key = name_map[func]
        # Negative lookbehind: skip "function foo(" definitions and "obj.foo(" method calls
        updated_script = re.sub(
            rf'(?<!function )(?<!\.)(?<!\w)\b{re.escape(func)}\s*\(',
            f"window['{win_key}'](",
            updated_script
        )

    expose_block = "\n".join(expose_lines)
    wrapped = (
        f"<script>\n"
        f"(function() {{\n"
        f"{updated_script}\n"
        f"{expose_block}\n"
        f"}})();\n"
        f"</script>"
    )
    return wrapped, updated_body

# ── Per-component processor ───────────────────────────────────────────────────

def process(folder_name):
    """Returns (section_html, style_content)."""
    comp_slug = slug(folder_name)
    path = os.path.join(COMP_DIR, folder_name, "index.html")
    raw  = read(path)

    # ── 1. Extract head style ──────────────────────────────────────────
    head_style = extract_head_style(raw)

    # ── 2. Extract body ────────────────────────────────────────────────
    body = extract_body(raw)

    # ── 3. Strip shared/unwanted tags ─────────────────────────────────
    body = strip_shared_tags(body)
    body = remove_fixed_nav(body)
    body = remove_padding_divs(body)

    # ── 4. Fix asset paths ─────────────────────────────────────────────
    body = fix_asset_paths(body, folder_name)

    # ── 5. Collect IDs before ID prefixing (needed for CSS too) ───────
    all_ids = sorted(set(re.findall(r'\bid=["\']([^"\']+)["\']', body, re.I)),
                     key=len, reverse=True)

    # ── 6. Extract inline scripts (before ID prefixing so we can update them too) ─
    scripts, body = extract_inline_scripts(body)

    # ── 7. Prefix IDs in body + collected scripts ──────────────────────
    body = prefix_ids(body, comp_slug)
    scripts = [prefix_ids(s, comp_slug) for s in scripts]

    # ── 8. Fix asset paths in CSS ─────────────────────────────────────
    head_style = fix_asset_paths(head_style, folder_name)
    head_style = prefix_ids_in_css(head_style, all_ids, comp_slug)

    # ── 9. Wrap each inline script + expose onclick functions ──────────
    script_tags = []
    working_body = body
    for sc in scripts:
        wrapped, working_body = wrap_script(sc, working_body, comp_slug)
        script_tags.append(wrapped)
    body = working_body

    # ── 10. Assemble section ───────────────────────────────────────────
    label = folder_name.replace("-", " ")
    section = (
        f'\n\n<!-- ════ {folder_name} ════ -->\n'
        f'<div class="comp-label-bar">{label}</div>\n'
        f'<div class="comp-section" data-comp="{comp_slug}" id="section-{comp_slug}">\n'
        f'{body.strip()}\n'
        f'{"".join(script_tags)}\n'
        f'</div>'
    )
    return section, head_style

# ── Main ──────────────────────────────────────────────────────────────────────

def build():
    folders = sorted([
        d for d in os.listdir(COMP_DIR)
        if os.path.isdir(os.path.join(COMP_DIR, d)) and not d.startswith('.')
    ])
    print(f"Building {len(folders)} components…")

    all_styles  = []
    all_sections = []

    for folder in folders:
        print(f"  {folder}")
        section, style = process(folder)
        all_sections.append(section)
        if style.strip() and style not in all_styles:
            all_styles.append(style)

    combined_style = "\n\n/* ───────────────────────────────────────────── */\n\n".join(all_styles)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>All Components — Emirates NBD Design System</title>

  <!-- Tailwind (local) -->
  <script src="../assets/js/tailwind.cdn.js"></script>

  <!-- Fonts (local) -->
  <link rel="stylesheet" href="../assets/css/fonts.css" />

  <!-- GSAP (needed for Download-App-Cinematic) -->
  <script src="../assets/js/gsap.min.js"></script>
  <script src="../assets/js/ScrollTrigger.min.js"></script>

  <style>
    /* ── Reset & base ──────────────────────────────────────────────── */
    *, body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    body {{ background: #F4F7FB; margin: 0; }}

    /* ── Component label bar ───────────────────────────────────────── */
    .comp-label-bar {{
      position: sticky;
      top: 0;
      z-index: 9999;
      background: #072447;
      color: white;
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      padding: 10px 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}

    /* ── Component section wrapper ─────────────────────────────────── */
    .comp-section {{
      background: white;
      border-bottom: 4px solid #F4F7FB;
    }}

    /* ── Component-specific styles ─────────────────────────────────── */
{combined_style}
  </style>
</head>
<body>
{''.join(all_sections)}
</body>
</html>"""

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(page)

    size = os.path.getsize(OUTPUT) / 1024
    print(f"\n✓  Written: {OUTPUT}")
    print(f"   Size:    {size:.0f} KB")
    print(f"   Count:   {len(folders)} components")

if __name__ == "__main__":
    build()
