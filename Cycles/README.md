# STAR PARK 星泊豪华大巴房车

## 两个版本（同属 main 分支）

- Eevee 原版：根目录，https://wangxp7.github.io/StarParkLuxuryBusRV-6AxH/
- Cycles 光线追踪版：Cycles/ 目录，https://wangxp7.github.io/StarParkLuxuryBusRV-6AxH/Cycles/
- 当前目录版本：Cycles 光线追踪版。
- 每版网页和独立 HTML 均注明版本、提供互跳链接和完整差异表。
- 同一 V15 三维模型与浏览器 PBR；图片画廊分别保留原 Eevee 和新 Cycles 渲染。
- Cycles 改善折射玻璃、间接光与室内光色，所有原图为 2560×1600、16 位 PNG；Eevee 主图同尺寸，其他 8 张为 2000×1250、8 位 PNG。
- 从 Blender 项目的 scripts/build_dual_web_delivery.py 可重复构建此次双版本发布；输入为原始提交 406c540 与 6ed5b99 的静态资源。


交互式三维展示与 9 张内外 Cycles 光线追踪彩色渲染图。基于 Blender 5.2.2 的 V15 完整模型导出。

## 在线浏览

https://wangxp7.github.io/StarParkLuxuryBusRV-6AxH/Cycles/

GitHub Pages 设置：Deploy from a branch → main → / (root)。
本仓库是纯静态网页，无需构建，无 CDN、外部字体或在线素材依赖。

## 房车外部与内部

- 整车外观：曲面车身、全景风挡、车灯、三轴车轮与车门。
- 内部剖视：驾驶舱、客厅、厨房、卫浴、后部卧室，可分别定位查看。
- 底盘动力：车架、发动机、制动、水电与储能系统。
- 车顶设备：无人机升降平台、空调和后部造型道具。
- 后部车库：低位车库、红色跑车与可开合的车库门。
- 影像画廊：9 个 Cycles 彩色渲染视角，支持筛选、大图与保存。

鼠标拖动旋转，滚轮缩放，右键平移；触屏单指旋转、双指缩放/平移。
三维面板进入可视范围时加载；模型不自动旋转，页面静止时不连续渲染。

## 本地预览与发布

双击 `预览网页.cmd`；或使用 Python：

```sh
python -m http.server 8863 --directory ..
```

随后打开 http://localhost:8863/Cycles/ 。发布时保留 main 根目录与 Cycles 子目录的完整结构。
普通目录版 index.html 通过 HTTP/HTTPS 运行；交付目录另外提供可双击打开、完全内嵌资源的独立 HTML。

## 模型与材质

`assets/starpark.glb` 为包含 16 个语义分组的完整房车模型（约 4.6 MB），使用 Draco 压缩。
合并静态网格，保留内部与外部几何，车库门枢轴独立；未修改原始 .blend。
浏览器使用 PBR 材质近似 Blender 程序化材质。任意程序化节点无法直接传入 glTF，
因此木纹、玻璃反射与照明不会和原始 Cycles 渲染完全相同；画廊保留原渲染视觉。
网页图片是渲染图的高质量 WebP 发布副本，原始 PNG 保留在本地项目 cycles_v01/renders 目录。
Blender 建模仍为 bpy 程序化几何与程序化节点，无导入模型、外部纹理或 HDR。

## 文件

- `index.html`、`style.css`、`viewer.js`：网页与交互。
- `assets/`：完整 GLB、9 张渲染图及缩略图、导出报告。
- `vendor/`：本地 Three.js r180、加载器、控制器与 Draco 解码器。
- `licenses/`：Three.js MIT 与 Draco Apache 2.0 许可。
- `source/`：可重复执行的导出和网页打包脚本。

页面展示概念设计，后部车顶造型为无功能的视觉道具。
第三方代码许可见 licenses；房车设计与渲染素材未额外授予开源许可。

Cycles 01：2560×1600、256/384 采样上限、自适应采样与 OpenImageDenoise；折射玻璃与程序化材质。
