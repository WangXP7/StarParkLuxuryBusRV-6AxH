import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { GLTFLoader } from './vendor/GLTFLoader.js';
import { DRACOLoader } from './vendor/DRACOLoader.js';
import { RoomEnvironment } from './vendor/RoomEnvironment.js';

const $ = (id) => document.getElementById(id);
const embedded = window.STARPARK_EMBEDDED;
if(embedded)$('download-offline').hidden=true;
const gallery = JSON.parse($('gallery-data').textContent);
const media = (name) => embedded?.images[name] || `assets/${name}`;
let galleryFilter='all', imageIndex=0;
const dialog=$('lightbox');
gallery.forEach((item,i)=>{
  const button=document.createElement('button');button.className='gallery-card';button.dataset.category=item.category;
  button.innerHTML=`<div class="image-wrap"><img src="${media(item.id+'-thumb.webp')}" loading="lazy" width="720" height="450" alt="${item.title}"><span>↗</span></div><div class="card-label">${item.title}<small>${String(i+1).padStart(2,'0')}</small></div><p>${item.description}</p>`;
  button.addEventListener('click',()=>openImage(i));$('gallery-grid').append(button);
});
function openImage(i){imageIndex=i;const item=gallery[i];$('lightbox-image').src=media(item.id+'.webp');$('lightbox-image').alt=item.title;$('lightbox-title').textContent=item.title;$('lightbox-description').textContent=item.description;$('download-image').href=media(item.id+'.webp');$('download-image').download=`StarPark_${item.id}.webp`;$('lightbox-counter').textContent=`${String(i+1).padStart(2,'0')} / 09`;if(!dialog.open)dialog.showModal();}
function moveImage(delta){const visible=gallery.map((x,i)=>({x,i})).filter(({x})=>galleryFilter==='all'||x.category===galleryFilter).map(({i})=>i);openImage(visible[(visible.indexOf(imageIndex)+delta+visible.length)%visible.length]);}
$('close-lightbox').onclick=()=>dialog.close();$('previous-image').onclick=()=>moveImage(-1);$('next-image').onclick=()=>moveImage(1);
dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});
dialog.addEventListener('keydown',e=>{if(e.key==='ArrowRight')moveImage(1);if(e.key==='ArrowLeft')moveImage(-1);});
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{galleryFilter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});document.querySelectorAll('.gallery-card').forEach(x=>x.hidden=galleryFilter!=='all'&&x.dataset.category!==galleryFilter);});

const descriptions={full:['01','完整外观','珍珠白曲面车身、全景风挡、香槟金饰件与三轴底盘。'],cutaway:['02','完整内部空间','移开车身与遮挡，探索驾驶舱、客厅、厨房、卫浴和后部卧室。'],chassis:['03','底盘与动力系统','三轴车架、制动组件、发动机、储能与水电系统。'],roof:['04','车顶设备','前部无人机升降平台、空调设备与后部造型道具。'],garage:['05','后部下层车库','打开低位车库门，查看卧室下方的车库和红色跑车。']};
const presets={full:[[-13,15,16],[0,2.3,0]],cutaway:[[-8,13,21],[0,1.8,0]],chassis:[[-9,9,19],[0,.7,0]],roof:[[-9,13,11],[0,2.5,0]],garage:[[13,4.8,7],[4.3,1.6,0]],cockpit:[[-7,5.8,5.3],[-5,2.05,0]],lounge:[[-4.5,6.8,6.5],[-3.2,2.05,0]],kitchen:[[-1.7,6,5.2],[-.5,2.1,0]],bathroom:[[2,6,4.8],[1.4,2.1,0]],bedroom:[[6,7,5.5],[4.6,3,0]]};
const tourLabels={cockpit:['驾驶舱',[-5,2.25,0]],lounge:['客厅',[-3.2,2.2,0]],kitchen:['厨房',[-.5,2.2,0]],bathroom:['卫浴',[1.4,2.25,0]],bedroom:['卧室',[4.6,3.1,0]]};
let scene,camera,renderer,controls,model,hatch,framePending=false,mode='full',tour='all',loadingPromise,ready=false,hatchOpen=false,frameCount=0;
const layerNodes=new Map(),cutawayCovers=[];const labelButtons=[];
function requestRender(){if(!renderer||framePending||document.hidden)return;framePending=true;requestAnimationFrame(()=>{framePending=false;renderer.render(scene,camera);frameCount++;positionLabels();});}
function resize(){if(!renderer)return;const r=$('viewer-stage').getBoundingClientRect();renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();requestRender();}
function setCamera(key){if(!controls)return;const [position,target]=presets[key]||presets.full;camera.position.fromArray(position);controls.target.fromArray(target);if(camera.aspect<1&&key in tourLabels)camera.position.sub(controls.target).multiplyScalar(1.35).add(controls.target);camera.near=.025;camera.far=200;camera.updateProjectionMatrix();controls.update();if(ready&&!(key in tourLabels))fitOverview();requestRender();}
function fitOverview(){
  model.updateMatrixWorld(true);const points=[];
  // Sample actual surfaces instead of the empty corners of a long coach's bounding box.
  model.traverseVisible(node=>{if(node.isMesh){const pos=node.geometry.attributes.position;const stride=Math.max(1,Math.ceil(pos.count/256));for(let i=0;i<pos.count;i+=stride)points.push(new THREE.Vector3().fromBufferAttribute(pos,i).applyMatrix4(node.matrixWorld));}});
  const q=new THREE.Vector3();
  for(let i=0;i<7;i++){camera.updateMatrixWorld();let factor=0;for(const p of points){q.copy(p).project(camera);factor=Math.max(factor,Math.abs(q.x)/.82,Math.abs(q.y)/.73);}if(Math.abs(factor-1)<.015)break;camera.position.sub(controls.target).multiplyScalar(THREE.MathUtils.clamp(factor,.7,1.5)).add(controls.target);controls.update();}
}
function updateActive(selector,value,attribute){document.querySelectorAll(selector).forEach(b=>{const active=b.dataset[attribute]===value;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});}
function setMode(next){mode=next;tour='all';updateActive('[data-mode]',next,'mode');updateActive('[data-tour]','all','tour');const [number,title,description]=descriptions[next];$('mode-index').textContent=number;$('mode-heading').textContent=title;$('view-title').textContent=title;$('mode-description').textContent=description;$('tour-bar').hidden=next!=='cutaway';$('hatch-toggle').hidden=!['full','garage'].includes(next);
  if(!ready)return;
  for(const [key,node] of layerNodes){node.visible=next==='chassis'?['frame','engine','wheels'].includes(key):next==='cutaway'?!['body','trim','roof','drone','roofprop'].includes(key):true;}
  cutawayCovers.forEach(n=>n.visible=next!=='cutaway');
  if(next==='garage')setHatch(true);else setHatch(false);
  setCamera(next);positionLabels();requestRender();
}
function setTour(next){tour=next;updateActive('[data-tour]',next,'tour');setCamera(next==='all'?'cutaway':next);$('view-title').textContent=next==='all'?'完整内部空间':tourLabels[next][0];positionLabels();}
function setHatch(open){hatchOpen=open;if(hatch){hatch.quaternion.copy(hatch.userData.closedQuaternion);if(open)hatch.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,-1),THREE.MathUtils.degToRad(118)));}$('hatch-toggle').textContent=open?'关闭车库门 ↙':'打开车库门 ↗';$('hatch-toggle').setAttribute('aria-pressed',String(open));requestRender();}
function positionLabels(){if(!camera)return;camera.updateMatrixWorld();labelButtons.forEach(({id,button,point})=>{button.hidden=mode!=='cutaway'||tour!=='all';if(button.hidden)return;const p=point.clone().project(camera);button.hidden=p.z>1||p.z< -1;button.style.left=`${(p.x*.5+.5)*100}%`;button.style.top=`${(-p.y*.5+.5)*100}%`;});}
function base64Buffer(base64){const bytes=Uint8Array.from(atob(base64),x=>x.charCodeAt(0));return bytes.buffer;}
function initializeScene(){
  renderer=new THREE.WebGLRenderer({canvas:$('model-canvas'),alpha:true,antialias:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;renderer.shadowMap.enabled=false;
  scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(40,1,.025,200);
  const pmrem=new THREE.PMREMGenerator(renderer);const environment=new RoomEnvironment();scene.environment=pmrem.fromScene(environment,.04).texture;environment.dispose();pmrem.dispose();scene.environmentIntensity=.8;
  scene.add(new THREE.HemisphereLight(0xffffff,0xb1ab92,.8));
  const key=new THREE.DirectionalLight(0xfff5df,2);key.position.set(-6,10,8);scene.add(key);
  const fill=new THREE.DirectionalLight(0xe0ebff,1.1);fill.position.set(2,6,-8);scene.add(fill);
  const rim=new THREE.DirectionalLight(0xffffff,1.2);rim.position.set(7,7,2);scene.add(rim);
  // A small generated contact plane grounds the model, without shadow passes or images.
  const contact=new THREE.Mesh(new THREE.PlaneGeometry(14.4,3.7),new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{color:{value:new THREE.Color('#43513a')}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'uniform vec3 color;varying vec2 vUv;void main(){vec2 p=(vUv-.5)*2.;float a=exp(-3.*pow(length(p),3.));gl_FragColor=vec4(color,a*.16);}'}));contact.rotation.x=-Math.PI/2;contact.position.y=.015;scene.add(contact);
  controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;controls.minDistance=1.3;controls.maxDistance=55;controls.maxPolarAngle=Math.PI*.94;controls.addEventListener('change',requestRender);
  new ResizeObserver(resize).observe($('viewer-stage'));resize();
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)requestRender();});
  $('model-canvas').addEventListener('webglcontextlost',e=>{e.preventDefault();$('loading').hidden=false;$('loading-title').textContent='三维显示已暂停';$('loading-copy').textContent='显卡资源被系统回收，请刷新页面重新载入。渲染图仍可浏览。';$('load-model').hidden=true;});
}
async function loadModel(){
  if(loadingPromise)return loadingPromise;
  $('loading').classList.add('busy');$('load-model').hidden=true;$('loading-track').hidden=false;$('loading-title').textContent='正在打开完整房车';$('loading-copy').textContent='加载车身、完整内饰、车库、底盘与车顶…';
  loadingPromise=(async()=>{
    try{
      initializeScene();
      const draco=new DRACOLoader();draco.setDecoderPath('vendor/draco/');draco.setWorkerLimit(2);
      if(embedded){draco._loadLibrary=(url,type)=>Promise.resolve(type==='arraybuffer'?base64Buffer(embedded.decoder[url]):atob(embedded.decoder[url]));}
      const loader=new GLTFLoader();loader.setDRACOLoader(draco);
      let gltf;
      if(embedded){$('loading-progress').style.width='70%';gltf=await loader.parseAsync(base64Buffer(embedded.model),'');}
      else{gltf=await loader.loadAsync('assets/starpark.glb',p=>{if(p.total)$('loading-progress').style.width=`${Math.round(p.loaded/p.total*85)}%`;});}
      model=gltf.scene;scene.add(model);
      const adjusted=new Set();
      model.traverse(node=>{if(node.userData.layer)layerNodes.set(node.userData.layer,node);if(node.userData.cutawayHide)cutawayCovers.push(node);if(node.userData.isHatch){hatch=node;hatch.userData.closedQuaternion=node.quaternion.clone();}if(node.isMesh){node.frustumCulled=true;const materials=Array.isArray(node.material)?node.material:[node.material];materials.forEach(m=>{if(m.transparent)m.depthWrite=false;if(!adjusted.has(m)){adjusted.add(m);if(m.name.startsWith('09 |'))m.color.setRGB(.12,.043,.016);}});}});
      for(const [id,[text,point]] of Object.entries(tourLabels)){const button=document.createElement('button');button.className='model-label';button.textContent=text;button.hidden=true;button.onclick=()=>setTour(id);$('model-labels').append(button);labelButtons.push({id,button,point:new THREE.Vector3(...point)});}
      ready=true;setMode(mode);$('loading-progress').style.width='100%';$('loading').hidden=true;draco.dispose();
      if(embedded)$('download-model').href=URL.createObjectURL(new Blob([base64Buffer(embedded.model)],{type:'model/gltf-binary'}));
      window.starParkViewer={get state(){return{ready,mode,tour,hatchOpen,frameCount,layers:Array.from(layerNodes,([id,n])=>({id,visible:n.visible})),drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,camera:camera.position.toArray()};},setMode,setTour,setHatch};
    }catch(error){console.error('StarPark viewer:',error);$('loading').classList.remove('busy');$('loading-title').textContent='三维模型暂未打开';$('loading-copy').textContent=location.protocol==='file:'?'请使用“星泊房车_独立版.html”直接打开，或通过网页服务器预览此发布目录。':'请确认浏览器支持 WebGL 2，或刷新后重试。下方的内外彩色渲染图仍可查看。';$('loading-track').hidden=true;}
  })();return loadingPromise;
}
document.querySelectorAll('[data-mode]').forEach(button=>button.onclick=()=>{setMode(button.dataset.mode);loadModel();});
document.querySelectorAll('[data-tour]').forEach(button=>button.onclick=()=>setTour(button.dataset.tour));
$('load-model').onclick=loadModel;$('hatch-toggle').onclick=()=>{if(!ready){mode='garage';loadModel();}else setHatch(!hatchOpen);};$('reset-view').onclick=()=>{if(ready)setCamera(mode==='cutaway'&&tour!=='all'?tour:mode);};
$('fullscreen').onclick=async()=>{const card=document.querySelector('.viewer-card');try{if(document.fullscreenElement)await document.exitFullscreen();else await card.requestFullscreen();}catch{ /* The embedded host may not permit fullscreen. */ }};
$('jump-interior').onclick=()=>{setMode('cutaway');loadModel();};
// Load only when the 3D panel comes into view; no permanent animation loop.
if(location.protocol!=='file:'||embedded){const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){observer.disconnect();loadModel();}},{rootMargin:'0px',threshold:.15});observer.observe($('viewer-stage'));}
