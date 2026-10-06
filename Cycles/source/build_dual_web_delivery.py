"""Publish the original Eevee edition at / and Cycles at /Cycles/ on main.

Reuses immutable published assets; rebuilds both self-contained HTML files.
Run with ordinary Python from the local Blender project (no Blender render needed).
"""
from pathlib import Path, PurePosixPath
import base64, hashlib, io, json, re, shutil, subprocess, tarfile, zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'publish_repository'
WEB = ROOT / 'web_publish_dual'
TOOLS = ROOT / 'web_tools'
BASES = TOOLS / 'edition_bases'
GIT = shutil.which('git') or 'git'
URL = 'https://wangxp7.github.io/StarParkLuxuryBusRV-6AxH/'
COMMITS = {'eevee': '406c540c933a12d63b4c25ceebb55f8d0f1f9bc4',
           'cycles': '6ed5b994ac2164525affbde42f158a78296437f0'}

def restore_base(key):
    base = BASES / key
    base.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run([GIT, '-C', str(REPO), 'archive', COMMITS[key]],
                             check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as stream:
        for member in stream.getmembers():
            parts = PurePosixPath(member.name)
            if parts.is_absolute() or '..' in parts.parts:
                raise ValueError('Invalid archive path: ' + member.name)
            target = base.joinpath(*parts.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(stream.extractfile(member).read())
            else:
                raise ValueError('Unsupported archive member: ' + member.name)
    return base

COMPARISONS = [
    ('成图方式', 'Blender Eevee 实时引擎，保留原版成图。',
     'Blender Cycles 路径追踪，重新计算反射、透射与间接光。'),
    ('玻璃与反射', '原版近似透明与反射方案，保留更直接的展示效果。',
     '折射玻璃材质；前风挡增加厚度，反射与透射层次更自然。'),
    ('室内光色', '保留原版暖光、皮革和木饰面的色彩表现。',
     '校正偏橙暖光，降低灯带亮度，增强皮革、木饰面与石材的区分。'),
    ('窗外环境', '保留原版程序化树景与环境。',
     '室内窗外改用连续程序化天空，减少不自然的树影干扰。'),
    ('原始图片', '主图 2560×1600；其他 8 张 2000×1250，8 位 PNG。',
     '全部 9 张 2560×1600，16 位 PNG；自适应采样与降噪。'),
    ('离线渲染成本', '渲染速度更快，适合快速预览和迭代。',
     '渲染耗时与计算需求更高，用于更细致的最终成图。'),
]
CSS = '''
/* Edition navigation and comparison are visible on desktop and mobile. */
.edition-banner{max-width:1303px;margin:24px auto 0;padding:22px 26px;border:1px solid var(--line);border-radius:14px;background:#eeeee4;display:flex;align-items:center;justify-content:space-between;gap:24px}
.edition-banner .eyebrow{margin-bottom:7px;font-size:9px}.edition-banner h2{font-family:inherit;font-size:21px;font-weight:500;letter-spacing:.5px}.edition-banner p:not(.eyebrow){font-size:11px;color:var(--muted);margin-top:8px;line-height:1.8}
.edition-navigation{display:flex;flex-direction:column;gap:12px;align-items:flex-end;flex-shrink:0}.edition-tabs{display:flex;gap:8px;flex-wrap:wrap}.edition-tabs a{padding:11px 17px;border:1px solid #bdc3b2;border-radius:24px;font-size:12px;white-space:nowrap}.edition-tabs a[aria-current=page]{background:var(--ink);border-color:var(--ink);color:#f6f5e9}.edition-tabs a:not([aria-current]):hover{background:#dedfcf}.edition-differences-link{font-size:11px;color:var(--muted);border-bottom:1px solid #b5beaa;padding-bottom:3px}
.edition-comparison .section-head{align-items:flex-start}.edition-comparison .section-head>p{max-width:405px}.comparison-table-wrap{border:1px solid var(--line);border-radius:12px;overflow:hidden}.comparison-table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:12px;line-height:1.85;background:#fafaf4}.comparison-table th,.comparison-table td{padding:17px 22px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);overflow-wrap:anywhere}.comparison-table th:first-child{width:19%;font-weight:500;color:var(--muted)}.comparison-table thead{background:#e8e9dc}.comparison-table thead th{font-weight:600;color:var(--ink)}.comparison-table [data-current=true]{background:#f0efdf}.comparison-table tbody tr:last-child>*{border-bottom:0}.comparison-note{font-size:11px;color:var(--muted);line-height:1.9;margin-top:18px;max-width:1000px}
@media(max-width:1420px){.edition-banner{margin:24px 6% 0}}
@media(max-width:650px){.edition-banner{margin:18px 5% 0;padding:18px;display:block}.edition-banner h2{font-size:19px}.edition-navigation{align-items:flex-start;margin-top:16px;gap:13px}.edition-tabs{gap:7px}.edition-tabs a{font-size:11px;padding:9px 12px}.edition-banner p:not(.eyebrow){font-size:10px}.edition-comparison .section-head{display:block}.edition-comparison .section-head>p{max-width:none;margin-top:12px;font-size:11px}.comparison-table{font-size:10px;line-height:1.85}.comparison-table th,.comparison-table td{padding:12px 9px}.comparison-table th:first-child{width:21%}.comparison-note{font-size:10px}}
'''

def comparison_html(key):
    current_ee = 'true' if key == 'eevee' else 'false'
    current_cy = 'true' if key == 'cycles' else 'false'
    rows = ''.join(f'<tr><th scope="row">{title}</th><td data-current="{current_ee}">{ee}</td><td data-current="{current_cy}">{cy}</td></tr>' for title, ee, cy in COMPARISONS)
    return f'''<section class="edition-comparison section" id="version-differences" aria-labelledby="differences-heading">
      <div class="section-head"><div><p class="eyebrow">TWO RENDERS, ONE DESIGN</p><h2 id="differences-heading">两个版本，核心差异。</h2></div><p>选择原版光照，或更细致的光线追踪成图。<br>版本差异体现在图片画廊中。</p></div>
      <div class="comparison-table-wrap"><table class="comparison-table" aria-label="Eevee与Cycles版本核心差异"><thead><tr><th scope="col">对比项</th><th scope="col" data-current="{current_ee}">Eevee · 原版</th><th scope="col" data-current="{current_cy}">Cycles · 光线追踪版</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p class="comparison-note">共同部分：两版沿用 V15 房车几何，包含完整外观、驾驶舱、客厅、厨房、卫浴、卧室、底盘、车顶和车库；网页使用同一份三维模型与浏览器 PBR 材质，均支持旋转、内部剖视与空间定位。切换版本改变图片画廊，不会切换浏览器的实时渲染引擎。表中尺寸和位深指本地原始 PNG，网页均使用 WebP 发布副本。Cycles 玻璃对摄影、反射与透射光线使用折射材质，直射阴影使用透明近似。</p>
    </section>'''

def update_page(folder, key):
    is_cycles = key == 'cycles'
    name = 'Cycles 光线追踪版' if is_cycles else 'Eevee 原版'
    edition = 'cycles-01' if is_cycles else 'eevee-v15'
    engine = 'CYCLES' if is_cycles else 'BLENDER_EEVEE'
    cache = edition + '-dual-01'
    ee_link, cy_link = ('../', './') if is_cycles else ('./', 'Cycles/')
    ee_current = '' if is_cycles else ' aria-current="page"'
    cy_current = ' aria-current="page"' if is_cycles else ''
    text = '重新渲染的玻璃、间接光与室内材质层次。' if is_cycles else '保留原版实时引擎成图、暖光与程序化环境。'
    banner = f'''<section class="edition-banner" aria-label="当前渲染版本与版本切换">
      <div><p class="eyebrow">CURRENT RENDER EDITION · 当前渲染版本</p><h2>{name}</h2><p>{text}</p></div>
      <div class="edition-navigation"><nav class="edition-tabs" aria-label="切换渲染版本"><a href="{ee_link}" data-edition-link="eevee"{ee_current}>Eevee · 原版</a><a href="{cy_link}" data-edition-link="cycles"{cy_current}>Cycles · 光线追踪版</a></nav><a class="edition-differences-link" href="#version-differences">查看核心差异 ↓</a></div>
    </section>'''
    html = (folder / 'index.html').read_text(encoding='utf8')
    html = re.sub(r'<title>.*?</title>', f'<title>STAR PARK 星泊 · {name}</title>', html)
    html = re.sub(r'<body[^>]*>', f'<body data-render-edition="{edition}" data-site-layout="dual-01">', html, count=1)
    html = html.replace('  <main>', banner + '\n  <main>', 1)
    html = html.replace('    <section class="living section"', comparison_html(key) + '\n    <section class="living section"', 1)
    html = re.sub(r'<span class="edition">.*?</span>', f'<span class="edition">{engine.replace("BLENDER_", "")} RENDER EDITION<br>DESIGN EDITION · V15</span>', html)
    html = html.replace('外观、室内与结构的彩色渲染。', '外观、室内与结构的 Eevee 彩色渲染。')
    html = html.replace('© 2026 STAR PARK · DESIGN EDITION V15', f'© 2026 STAR PARK · {name} · V15')
    html = html.replace('download="星泊房车_独立版.html"', f'download="星泊房车_{"Cycles" if is_cycles else "Eevee"}_独立版.html"')
    html = re.sub(r'src="assets/([^"?\s]+\.webp)(?:\?[^"\s]*)?"', lambda m: f'src="assets/{m.group(1)}?v={cache}"', html)
    html = re.sub(r'src="viewer\.js(?:\?[^"\s]*)?"', f'src="viewer.js?v={cache}"', html)
    html = html.replace('href="style.css"', f'href="style.css?v={cache}"')
    (folder / 'index.html').write_text(html, encoding='utf8')
    (folder / 'style.css').write_text((folder / 'style.css').read_text(encoding='utf8') + CSS, encoding='utf8')
    viewer = (BASES / 'cycles' / 'viewer.js').read_text(encoding='utf8')
    viewer = viewer.replace("document.body.dataset.renderEdition||'eevee-v15'", "(document.body.dataset.renderEdition||'eevee-v15')+'-dual-01'")
    (folder / 'viewer.js').write_text(viewer, encoding='utf8')
    info = {'engine': engine, 'edition': name, 'source_iteration': 15, 'views': 9,
            'blender': '5.2.2 LTS', 'site_layout': 'dual-01', 'source_commit': COMMITS[key]}
    (folder / 'assets' / 'render-info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf8')
    return html

def standalone(folder, key, html):
    bundle_file = TOOLS / (key + '.dual.bundle.js')
    subprocess.run([str(TOOLS / 'esbuild.exe'), str(folder / 'viewer.js'), '--bundle',
                    '--format=iife', '--minify', '--legal-comments=inline',
                    '--alias:three=' + str(folder / 'vendor' / 'three.module.min.js'),
                    '--outfile=' + str(bundle_file)], check=True)
    b64 = lambda p: base64.b64encode(p.read_bytes()).decode('ascii')
    data = {'model': b64(folder / 'assets' / 'starpark.glb'),
            'decoder': {n: b64(folder / 'vendor' / 'draco' / n) for n in ('draco_wasm_wrapper.js', 'draco_decoder.wasm')},
            'images': {p.name: 'data:image/webp;base64,' + b64(p) for p in (folder / 'assets').glob('*.webp')}}
    html = re.sub(r'<link rel="stylesheet" href="style\.css(?:\?[^"\s]*)?">', lambda m: '<style>' + (folder / 'style.css').read_text(encoding='utf8') + '</style>', html)
    html = re.sub(r'\s*<script type="importmap">.*?</script>', '', html)
    html = re.sub(r'src="assets/([^"?\s]+\.webp)(?:\?[^"\s]*)?"', lambda m: 'src="' + data['images'][m.group(1)] + '"', html)
    for target, link in [('eevee', URL), ('cycles', URL + 'Cycles/')]:
        html = re.sub(r'href="[^"]*"( data-edition-link="' + target + r'")', lambda m: 'href="' + link + '"' + m.group(1), html)
    payload = json.dumps(data, separators=(',', ':'))
    bundle = bundle_file.read_text(encoding='utf8').replace('</script', '<\\/script')
    html = re.sub(r'<script type="module" src="viewer\.js(?:\?[^"\s]*)?"></script>', lambda m: '<script>window.STARPARK_EMBEDDED=' + payload + ';</script><script>' + bundle + '</script>', html)
    license_text = '\n\n'.join((folder / 'licenses' / n).read_text(encoding='utf8') for n in ('THREE-LICENSE.txt', 'DRACO-LICENSE.txt'))
    html = html.replace('</body>', '<script type="text/plain" id="third-party-licenses">' + license_text.replace('</script', '<\\/script') + '</script></body>')
    (folder / 'standalone.html').write_text(html, encoding='utf8')
    local = ROOT / ('星泊房车_' + ('Cycles' if key == 'cycles' else 'Eevee') + '_独立版.html')
    shutil.copy2(folder / 'standalone.html', local)
    if key == 'cycles':
        shutil.copy2(local, ROOT / '星泊房车_独立版.html')

eevee_base, cycles_base = restore_base('eevee'), restore_base('cycles')
assert (eevee_base / 'assets' / 'starpark.glb').read_bytes() == (cycles_base / 'assets' / 'starpark.glb').read_bytes(), 'Both editions must retain the same complete web model'
WEB.mkdir(exist_ok=True)
shutil.copytree(eevee_base, WEB, dirs_exist_ok=True)
shutil.copytree(cycles_base, WEB / 'Cycles', dirs_exist_ok=True)
for key, folder in [('eevee', WEB), ('cycles', WEB / 'Cycles')]:
    html = update_page(folder, key)
    standalone(folder, key, html)
    shutil.copy2(Path(__file__), folder / 'source' / Path(__file__).name)
    readme = (folder / 'README.md').read_text(encoding='utf8')
    preview = (folder / '预览网页.cmd').read_text(encoding='utf8')
    if key == 'cycles':
        readme = readme.replace(URL, URL + 'Cycles/')
        readme = readme.replace('python -m http.server 8863', 'python -m http.server 8863 --directory ..')
        readme = readme.replace('随后打开 http://localhost:8863/ 。上传整个目录即可发布，保持相对路径。', '随后打开 http://localhost:8863/Cycles/ 。发布时保留 main 根目录与 Cycles 子目录的完整结构。')
        preview = preview.replace('cd /d "%~dp0"', 'cd /d "%~dp0.."').replace('http://localhost:8863/', 'http://localhost:8863/Cycles/')
    preview = preview.replace('可打开项目目录中的“星泊房车_独立版.html”', '可双击本目录中的 standalone.html')
    (folder / '预览网页.cmd').write_text(preview, encoding='utf8')
    prefix = f'''## 两个版本（同属 main 分支）

- Eevee 原版：根目录，{URL}
- Cycles 光线追踪版：Cycles/ 目录，{URL}Cycles/
- 当前目录版本：{'Eevee 原版' if key == 'eevee' else 'Cycles 光线追踪版'}。
- 每版网页和独立 HTML 均注明版本、提供互跳链接和完整差异表。
- 同一 V15 三维模型与浏览器 PBR；图片画廊分别保留原 Eevee 和新 Cycles 渲染。
- Cycles 改善折射玻璃、间接光与室内光色，所有原图为 2560×1600、16 位 PNG；Eevee 主图同尺寸，其他 8 张为 2000×1250、8 位 PNG。
- 从 Blender 项目的 scripts/build_dual_web_delivery.py 可重复构建此次双版本发布；输入为原始提交 406c540 与 6ed5b99 的静态资源。

'''
    (folder / 'README.md').write_text('# STAR PARK 星泊豪华大巴房车\n\n' + prefix + readme.split('\n', 1)[1], encoding='utf8')

manifest = {'branch': 'main', 'layout': 'dual-01', 'editions': {key: {
    'path': '/' if key == 'eevee' else '/Cycles/', 'source_commit': COMMITS[key],
    'image_sha256': {p.stem: hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASES / key / 'assets').glob('*.webp')}
} for key in COMMITS}}
(ROOT / 'logs' / 'dual_web_build.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
with zipfile.ZipFile(ROOT / 'StarPark_网页发布包.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for file in WEB.rglob('*'):
        if file.is_file():
            z.write(file, file.relative_to(WEB).as_posix())
(ROOT / '网页发布说明.txt').write_text(f'''星泊房车双版本网页发布 · main 分支

Eevee 原版：main 根目录，{URL}
Cycles 光线追踪版：main/Cycles/，{URL}Cycles/
两版页面均有版本标识、互跳链接和核心差异表。
web_publish_dual 为此次完整发布目录，StarPark_网页发布包.zip 内文件位于根目录。
星泊房车_Eevee_独立版.html 与 星泊房车_Cycles_独立版.html 可双击打开。
星泊房车_独立版.html 保留为新版 Cycles 独立版别名。
独立版的版本切换链接打开相应在线站点，其模型与图片本身无需联网。
两版使用同一三维模型与浏览器 PBR，Cycles/Eevee 的差异应用于图片画廊。
所有本地 .blend、PNG 和建模源码保持不变。
''', encoding='utf8')
config = json.loads((ROOT / 'project_config.json').read_text(encoding='utf8'))
config.update({'web_publish_directory': 'web_publish_dual', 'web_editions': {'eevee': '.', 'cycles': 'Cycles'}, 'web_branch': 'main'})
(ROOT / 'project_config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps({'status': 'BUILT', 'root_edition': 'Eevee', 'Cycles_edition': 'Cycles', 'files': sum(1 for p in WEB.rglob('*') if p.is_file()), 'bytes': sum(p.stat().st_size for p in WEB.rglob('*') if p.is_file())}, indent=2), flush=True)
