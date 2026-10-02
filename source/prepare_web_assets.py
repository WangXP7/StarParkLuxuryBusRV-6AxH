from pathlib import Path
import urllib.request, shutil, json
from PIL import Image
root=Path(__file__).resolve().parents[1]
web=root/'web_publish';vendor=web/'vendor';(vendor/'draco').mkdir(parents=True,exist_ok=True)
base='https://raw.githubusercontent.com/mrdoob/three.js/r180/'
files={'OrbitControls.js':'examples/jsm/controls/OrbitControls.js','GLTFLoader.js':'examples/jsm/loaders/GLTFLoader.js','DRACOLoader.js':'examples/jsm/loaders/DRACOLoader.js','BufferGeometryUtils.js':'examples/jsm/utils/BufferGeometryUtils.js','RoomEnvironment.js':'examples/jsm/environments/RoomEnvironment.js','draco/draco_decoder.js':'examples/jsm/libs/draco/gltf/draco_decoder.js','draco/draco_wasm_wrapper.js':'examples/jsm/libs/draco/gltf/draco_wasm_wrapper.js','draco/draco_decoder.wasm':'examples/jsm/libs/draco/gltf/draco_decoder.wasm','THREE-LICENSE.txt':'LICENSE'}
for name,src in files.items():
    path=vendor/name
    if not path.exists():
        with urllib.request.urlopen(base+src,timeout=60) as response:path.write_bytes(response.read())
    if path.suffix=='.js' and name=='GLTFLoader.js':
        path.write_text(path.read_text(encoding='utf8').replace('../utils/BufferGeometryUtils.js','./BufferGeometryUtils.js'),encoding='utf8')
for name in ('three.module.min.js','three.core.min.js'):
    shutil.copy2(Path('PRIVACY-REDACTED/PRIVACY-REDACTED/Buckshot-Roulette/vendor')/name,vendor/name)
entries=[('Exterior','exterior','三分之四外观','珍珠白车身、石墨色下裙与香槟金腰线。','exterior'),('reference','reference','前侧外观','全景前风挡与三轴车身比例。','exterior'),('entrance','entrance','乘客侧与入口','前部车门、车窗与服务舱细节。','exterior'),('cutaway','cutaway','内部全景剖视','驾驶舱、客厅、厨房、卫浴与后部卧室。','interior'),('lounge','lounge','客厅与驾驶舱','弧形座椅、皮革沙发、暖光与木饰面。','interior'),('kitchen','kitchen','厨房与卫浴','胡桃木柜体、石材台面与独立卫浴。','interior'),('garage','garage','后部下层车库','卧室下方的低位车库与红色跑车。','structure'),('chassis','chassis','底盘与动力系统','车架、制动、发动机与水电系统。','structure'),('roof','roof','车顶与设备','前部升降平台、空调与车顶造型。','structure')]
gallery=[]
for source,key,title,description,category in entries:
    src=root/'renders'/('StarPark_52_'+source+'.png')
    target=web/'assets'/(key+'.webp')
    im=Image.open(src).convert('RGB');im.thumbnail((2200,1400));im.save(target,'WEBP',quality=88,method=6)
    thumb=im.copy();thumb.thumbnail((720,460));thumb.save(web/'assets'/(key+'-thumb.webp'),'WEBP',quality=82,method=6)
    gallery.append(dict(id=key,title=title,description=description,category=category,src='assets/'+key+'.webp',thumb='assets/'+key+'-thumb.webp',width=im.width,height=im.height))
(web/'assets'/'gallery.json').write_text(json.dumps(gallery,ensure_ascii=False,indent=2),encoding='utf8')
print('WEB_ASSETS',len(gallery),'views; vendor',len(files),'files',flush=True)
