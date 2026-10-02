"""Build both a self-contained HTML and a GitHub Pages-ready static directory."""
from pathlib import Path
import base64,json,re,urllib.request,tarfile,io,subprocess,zipfile,shutil
root=Path(__file__).resolve().parents[1];web=root/'web_publish';tools=root/'web_tools';tools.mkdir(exist_ok=True)
bundler=tools/'esbuild.exe'
if not bundler.exists():
    with urllib.request.urlopen('https://registry.npmjs.org/@esbuild/win32-x64/-/win32-x64-0.25.10.tgz',timeout=60) as r:data=r.read()
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
        member=next(m for m in t.getmembers() if m.name.endswith('/esbuild.exe'))
        bundler.write_bytes(t.extractfile(member).read())
subprocess.run([str(bundler),str(web/'viewer.js'),'--bundle','--format=iife','--minify','--legal-comments=inline','--alias:three='+str(web/'vendor'/'three.module.min.js'),'--outfile='+str(tools/'viewer.bundle.js')],check=True)
b64=lambda p:base64.b64encode(p.read_bytes()).decode('ascii')
embedded={'model':b64(web/'assets'/'starpark.glb'),'decoder':{name:b64(web/'vendor'/'draco'/name) for name in ('draco_wasm_wrapper.js','draco_decoder.wasm')},'images':{p.name:'data:image/webp;base64,'+b64(p) for p in (web/'assets').glob('*.webp')}}
html=(web/'index.html').read_text(encoding='utf8')
html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+ (web/'style.css').read_text(encoding='utf8')+'</style>')
html=re.sub(r'\s*<script type="importmap">.*?</script>','',html)
html=re.sub(r'src="assets/([^"\s]+\.webp)"',lambda m:'src="'+embedded['images'][m.group(1)]+'"',html)
payload=json.dumps(embedded,ensure_ascii=False,separators=(',',':'))
bundle=(tools/'viewer.bundle.js').read_text(encoding='utf8').replace('</script','<\\/script')
html=html.replace('<script type="module" src="viewer.js"></script>','<script>window.STARPARK_EMBEDDED='+payload+';</script><script>'+bundle+'</script>')
single=root/'星泊房车_独立版.html'
licenses=web/'licenses';licenses.mkdir(exist_ok=True)
shutil.copy2(web/'vendor'/'THREE-LICENSE.txt',licenses/'THREE-LICENSE.txt')
draco_license=licenses/'DRACO-LICENSE.txt'
if not draco_license.exists():
    with urllib.request.urlopen('https://raw.githubusercontent.com/google/draco/1.5.7/LICENSE',timeout=60) as r:draco_license.write_bytes(r.read())
license_text=(licenses/'THREE-LICENSE.txt').read_text(encoding='utf8')+'\n\nDRACO\n'+draco_license.read_text(encoding='utf8')
html=html.replace('</body>','<script type="text/plain" id="third-party-licenses">'+license_text.replace('</script','<\\/script')+'</script></body>')
single.write_text(html,encoding='utf8')
shutil.copy2(single,web/'standalone.html')
(web/'.nojekyll').write_text('',encoding='utf8')
(web/'.gitignore').write_text('.DS_Store\nThumbs.db\n*.log\n',encoding='utf8')
readme='''# STAR PARK 星泊豪华大巴房车

交互式三维展示与 9 张内外彩色渲染图。基于 Blender 5.2.2 的 V15 完整模型导出。

## 在线浏览

https://wangxp7.github.io/StarParkLuxuryBusRV-6AxH/

GitHub Pages 设置：Deploy from a branch → main → / (root)。
本仓库是纯静态网页，无需构建，无 CDN、外部字体或在线素材依赖。

## 房车外部与内部

- 整车外观：曲面车身、全景风挡、车灯、三轴车轮与车门。
- 内部剖视：驾驶舱、客厅、厨房、卫浴、后部卧室，可分别定位查看。
- 底盘动力：车架、发动机、制动、水电与储能系统。
- 车顶设备：无人机升降平台、空调和后部造型道具。
- 后部车库：低位车库、红色跑车与可开合的车库门。
- 影像画廊：9 个 Eevee 彩色渲染视角，支持筛选、大图与保存。

鼠标拖动旋转，滚轮缩放，右键平移；触屏单指旋转、双指缩放/平移。
三维面板进入可视范围时加载；模型不自动旋转，页面静止时不连续渲染。

## 本地预览与发布

双击 `预览网页.cmd`；或使用 Python：

```sh
python -m http.server 8863
```

随后打开 http://localhost:8863/ 。上传整个目录即可发布，保持相对路径。
普通目录版 index.html 通过 HTTP/HTTPS 运行；交付目录另外提供可双击打开、完全内嵌资源的独立 HTML。

## 模型与材质

`assets/starpark.glb` 为包含 16 个语义分组的完整房车模型（约 4.6 MB），使用 Draco 压缩。
合并静态网格，保留内部与外部几何，车库门枢轴独立；未修改原始 .blend。
浏览器使用 PBR 材质近似 Blender 程序化材质。任意程序化节点无法直接传入 glTF，
因此木纹、玻璃反射与照明不会和原始 Eevee 渲染完全相同；画廊保留原渲染视觉。
网页图片是渲染图的高质量 WebP 发布副本，原始 PNG 保留在本地项目 renders 目录。
Blender 建模仍为 bpy 程序化几何与程序化节点，无导入模型、外部纹理或 HDR。

## 文件

- `index.html`、`style.css`、`viewer.js`：网页与交互。
- `assets/`：完整 GLB、9 张渲染图及缩略图、导出报告。
- `vendor/`：本地 Three.js r180、加载器、控制器与 Draco 解码器。
- `licenses/`：Three.js MIT 与 Draco Apache 2.0 许可。
- `source/`：可重复执行的导出和网页打包脚本。

页面展示概念设计，后部车顶造型为无功能的视觉道具。
第三方代码许可见 licenses；房车设计与渲染素材未额外授予开源许可。
'''
(web/'README.md').write_text(readme,encoding='utf8')
(root/'网页发布说明.txt').write_text('星泊房车网页交付\n\n1. 星泊房车_独立版.html：完整三维模型与9张内外渲染图全部内嵌，可双击打开，也可直接上传网站。\n2. web_publish：GitHub Pages发布目录。index.html为入口，上传整个目录，不能只上传index.html。\n3. StarPark_网页发布包.zip：上述完整发布目录的ZIP，文件位于包内根目录。\n4. assets/starpark.glb：包含全部车身、内部、底盘、车顶和车库。\n\n三维采用浏览器PBR材质，程序化木纹和复杂反射与Eevee略有差异。画廊保留Eevee渲染效果。\n页面静止时暂停渲染，操作时按需刷新，像素倍率不超过1.5。\nGitHub Pages地址：https://wangxp7.github.io/StarParkLuxuryBusRV-6AxH/\n',encoding='utf8')
source=web/'source';source.mkdir(exist_ok=True)
for name in ('export_web.py','prepare_web_assets.py','build_web_delivery.py'):shutil.copy2(root/'scripts'/name,source/name)
with zipfile.ZipFile(root/'StarPark_网页发布包.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in web.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(web).as_posix())
print(json.dumps({'standalone_bytes':single.stat().st_size,'static_bytes':sum(p.stat().st_size for p in web.rglob('*') if p.is_file()),'zip_bytes':(root/'StarPark_网页发布包.zip').stat().st_size},indent=2),flush=True)
