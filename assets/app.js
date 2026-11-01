
/* ============ v3.0：异常可见化（绝不再静默失败） ============ */
window.addEventListener('error', function(ev){
  const b = document.getElementById('errTop');
  if(b && ev && ev.message){ b.textContent = '⚠️ 页面出现异常：' + ev.message; b.classList.add('show'); }
});
window.addEventListener('unhandledrejection', function(ev){
  const b = document.getElementById('errTop');
  if(b){ b.textContent = '⚠️ 操作没有完成：' + ((ev.reason && ev.reason.message) || '未知错误'); b.classList.add('show'); }
});

/* ============ 分类图标 ============ */
const CAT = {
  bag:{e:'🎒',c:'#62269c',l:'箱包'}, card:{e:'🪪',c:'#7a35b8',l:'证件卡'}, watch:{e:'⌚',c:'#3a86a8',l:'手表'},
  electronics:{e:'🎧',c:'#c0392b',l:'电子'}, umbrella:{e:'☂️',c:'#2f6f8f',l:'雨具'}, key:{e:'🔑',c:'#b8860b',l:'钥匙'},
  book:{e:'📚',c:'#8a52c7',l:'书籍'}, sports:{e:'🏀',c:'#e08a2b',l:'运动'}, cup:{e:'🥤',c:'#2f9e8f',l:'杯具'},
  charger:{e:'🔋',c:'#4e9a4e',l:'充电'}, repair:{e:'🛠️',c:'#62269c',l:'维修'}, life:{e:'🏠',c:'#2f6f8f',l:'生活'},
  office:{e:'🖨️',c:'#7a35b8',l:'办公'}, outdoor:{e:'⛺',c:'#3a86a8',l:'户外'},
  cloth:{e:'🧥',c:'#8a52c7',l:'衣物'}, other:{e:'📦',c:'#6b6480',l:'其他'},
  help_borrow:{e:'🛠️',c:'#62269c',l:'借用'}, help_errand:{e:'🏃',c:'#e08a2b',l:'代办'},
  help_donate:{e:'🎁',c:'#2f9e8f',l:'捐赠'}, help_volunteer:{e:'🤝',c:'#2f6f8f',l:'志愿'}
};
function catInfo(k){ return CAT[k] || {e:'📦',c:'#62269c',l:'其他'}; }
function thumbHTML(k){ const m=catInfo(k); return '<div class="thumb" style="background:linear-gradient(135deg,'+m.c+','+shade(m.c)+')">'+m.e+'</div>'; }
function shade(hex){ const n=parseInt(hex.slice(1),16); let r=(n>>16)&255,g=(n>>8)&255,b=n&255; r=Math.min(255,r+40);g=Math.min(255,g+40);b=Math.min(255,b+40); return 'rgb('+r+','+g+','+b+')'; }

/* ============ 数据（套用 demo-v3 内容） ============ */
const LOST = [
  {id:'l1',cat:'bag',title:'黑色双肩书包（含课本）',desc:'在六教课间丢失，内有《高等数学》等课本，急寻。',loc:'第六教学楼 3 区',status:'进行中',act:'认领'},
  {id:'l2',cat:'card',title:'校园卡一张',desc:'紫荆公寓附近捡到，姓名已遮挡，请失主认领。',loc:'紫荆公寓 15 号楼',status:'认领中',act:'认领'},
  {id:'l3',cat:'watch',title:'银色手表',desc:'操场跑步后遗落，卡西欧款式。',loc:'东大操场',status:'进行中',act:'认领'},
  {id:'l4',cat:'electronics',title:'AirPods 耳机',desc:'图书馆二层自习室遗失，白色。',loc:'图书馆 2 层',status:'已闭环归还',act:'已归还'},
  {id:'l5',cat:'umbrella',title:'蓝色雨伞',desc:'食堂门口遗留，长柄。',loc:'观畴园食堂',status:'进行中',act:'认领'},
  {id:'l6',cat:'key',title:'钥匙串（含门禁卡）',desc:'教学楼楼梯间捡到。',loc:'第四教学楼',status:'已找回',act:'已找回'}
];
const FOUND = [
  {id:'f1',cat:'card',title:'求找：黑色钱包',desc:'昨晚在食堂丢失，内有身份证和少量现金。',loc:'桃李园食堂',status:'进行中',act:'帮扩散'},
  {id:'f2',cat:'electronics',title:'求找：机械键盘',desc:'机房使用后未带走，茶轴。',loc:'东主楼机房',status:'进行中',act:'提供线索'},
  {id:'f3',cat:'sports',title:'求找：篮球',desc:'篮球场上遗落，斯伯丁。',loc:'北区篮球场',status:'认领中',act:'帮扩散'},
  {id:'f4',cat:'book',title:'求找：课本《线性代数》',desc:'图书馆借的书丢了。',loc:'图书馆',status:'进行中',act:'提供线索'},
  {id:'f5',cat:'cup',title:'求找：保温杯',desc:'体育馆更衣室遗留。',loc:'综合体育馆',status:'已找回',act:'已找回'},
  {id:'f6',cat:'charger',title:'求找：充电宝',desc:'教室插座上忘拿。',loc:'第五教学楼',status:'进行中',act:'帮扩散'}
];
const LEND = [
  {id:'t1',cat:'repair',title:'螺丝刀套装',desc:'常用家用，用后请归还。',loc:'紫荆公寓',status:'出借中',act:'借出'},
  {id:'t2',cat:'life',title:'打气筒',desc:'自行车打气。',loc:'学生区',status:'出借中',act:'借出'},
  {id:'t3',cat:'office',title:'打印机',desc:'支持双面打印，请爱护。',loc:'宿舍区',status:'出借中',act:'借出'},
  {id:'t4',cat:'repair',title:'万用表',desc:'电子实验借用。',loc:'实验室',status:'出借中',act:'借出'}
];
const SERVICES = [
  {id:'s1',cat:'electronics',title:'更换纽扣电池',desc:'手表 / 体温计 / 车钥匙等小型电池更换。',loc:'可约 3 人',status:'可约',act:'预约'},
  {id:'s2',cat:'card',title:'配置卡通门禁卡',desc:'复制 / 写入校园卡通门禁卡，需本人授权。',loc:'可约 2 人',status:'可约',act:'预约'},
  {id:'s3',cat:'life',title:'修拉链 / 缝扣子',desc:'衣物小修小补，工具自备。',loc:'可约 5 人',status:'可约',act:'预约'}
];
const BORROW = [
  {id:'t5',cat:'office',title:'求借：订书机',desc:'装订作业用半天。',loc:'文科图书馆',status:'求借中',act:'我提供'},
  {id:'t6',cat:'outdoor',title:'求借：帐篷',desc:'周末露营活动。',loc:'操场',status:'求借中',act:'我提供'}
];
const NEED_SERVICES = [
  {id:'n1',cat:'watch',title:'求换手表电池',desc:'紫荆 12 号楼，今晚前，提供电池。',loc:'紫荆 12 号楼',status:'求服务',act:'我接单'},
  {id:'n2',cat:'card',title:'求配一张门禁卡',desc:'老馆自习室，周末，需现场。',loc:'老馆自习室',status:'求服务',act:'我接单'},
  {id:'n3',cat:'bag',title:'求修书包拉链',desc:'明早课前，提供针线。',loc:'明早课前',status:'求服务',act:'我接单'}
];

/* ============ 本地存储（阶段一：为将来接后端留的口子） ============ */
const memStore = {};
let storageWarned = false;
function warnStorage(){
  if(storageWarned) return;
  storageWarned = true;
  const b = document.getElementById('errTop');
  if(b){
    b.textContent = '⚠️ 这个浏览器没法保存数据（可能是无痕模式、存储已满或被拦截）。你发布的内容只在当前页面有效，刷新会消失；换成普通窗口打开就能保存。';
    b.classList.add('show');
  }
}
const LS = {
  get(k){ try{ const v = localStorage.getItem(k); return v == null ? null : v; }catch(e){ return memStore[k] || null; } },
  set(k,v){
    try{ localStorage.setItem(k,v); return true; }
    catch(e){ memStore[k] = String(v); warnStorage(); return true; }
  },
  remove(k){ try{ localStorage.removeItem(k); }catch(e){} delete memStore[k]; }
};
const STORE_KEY = 'sg:items:v2';
/* 用 http(s) 打开时（= 走共享服务器）才连后端；file:// 直接打开就是纯本机 */
const API_BASE = (location.protocol === 'http:' || location.protocol === 'https:') ? '/api' : '';
const USER_KEY  = 'sg:user:v1';

function esc(s){
  return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
const ACC_KEY = 'sg:account:v1';
const ACC_PHONE_KEY = 'sg:accountPhone:v1';
function deviceId(){
  let id = LS.get(USER_KEY);
  if(!id){ id = 'u_' + Math.random().toString(36).slice(2,9); LS.set(USER_KEY, id); }
  return id;
}
function myId(){
  return LS.get(ACC_KEY) || deviceId();
}
function statusText(s){
  return ({pending:'审核中',approved:'已上架',rejected:'已驳回',closed:'已闭环',claimed:'已认领',removed:'已下架'})[s] || s || '';
}
function statusChip(s){
  if(!s || s==='approved' || statusText(s)===s) return '';
  return '<span class="st st-'+esc(s)+'">'+esc(statusText(s))+'</span>';
}
function updateBadge(){
  const n = Store.list({status:'pending'}).length;
  const b = document.getElementById('loginBtn');
  if(b) b.classList.toggle('has-dot', n > 0);
}
function fmtTime(ts){
  const d = new Date(ts||Date.now());
  const p = n => ('0'+n).slice(-2);
  return (d.getMonth()+1)+'-'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes());
}
function fmtWhen(v){
  if(!v) return '';
  const m = String(v).match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  return m ? (m[2]+'-'+m[3]+' '+m[4]+':'+m[5]) : String(v);
}
function maskPhone(p){
  return String(p||'').replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
}
function catKey(name){
  return ({'证件':'card','电子设备':'electronics','衣物':'cloth','水杯':'cup','书包':'bag','其他':'other'})[name] || 'other';
}

/* 首次打开时把原来的静态演示数据灌进存储，之后一切以存储为准 */
function seedItems(){
  const mk = type => it => ({
    id: it.id, type: type, cat: it.cat, title: it.title, desc: it.desc,
    place: it.loc, eventTime: '', secret: '', photo: null,
    status: /^已/.test(it.status) ? 'closed' : 'approved',
    rejectReason: '', contact: {}, ownerId: 'seed',
    createdAt: Date.now() - 86400000*3, updatedAt: Date.now(),
    reviewedBy: 'seed', reviewedAt: 0
  });
  return LOST.map(mk('found')).concat(FOUND.map(mk('lost')));
}

const Store = {
  all(){
    const raw = LS.get(STORE_KEY);
    let list = null;
    if(raw){ try{ list = JSON.parse(raw); }catch(e){ list = null; } }
    if(!Array.isArray(list)){ list = seedItems(); LS.set(STORE_KEY, JSON.stringify(list)); }
    return list;
  },
  _write(list){
    if(LS.set(STORE_KEY, JSON.stringify(list))) return true;
    toast('本地存储空间不足：请删掉一些旧发布或换一张更小的图片');
    return false;
  },
  list(f){
    f = f || {};
    let l = this.all().slice();
    if(f.type)   l = l.filter(x => x.type === f.type);
    if(f.status) l = l.filter(x => x.status === f.status);
    if(f.statuses) l = l.filter(x => f.statuses.indexOf(x.status) >= 0);
    if(f.owner)  l = l.filter(x => x.ownerId === f.owner);
    if(f.q){
      const q = String(f.q).toLowerCase();
      l = l.filter(x => ((x.title||'')+(x.desc||'')+(x.place||'')+catInfo(x.cat).l).toLowerCase().indexOf(q) >= 0);
    }
    return l.sort((a,b) => (b.createdAt||0) - (a.createdAt||0));
  },
  get(id){ return this.all().find(x => x.id === id) || null; },
  add(it){
    const l = this.all(); l.push(it);
    if(JSON.stringify(l).length > 4200000 && it.photo){
      it.photo = null;
      toast('图片太大没能保存，已保留文字内容');
    }
    return this._write(l) ? it : null;
  },
  update(id, patch){
    const l = this.all();
    const i = l.findIndex(x => x.id === id);
    if(i < 0) return null;
    l[i] = Object.assign({}, l[i], patch, {updatedAt: Date.now()});
    return this._write(l) ? l[i] : null;
  },
  remove(id){
    return this._write(this.all().filter(x => x.id !== id));
  }
};


/* ============ 服务器（公开内容 + 我自己的发布） ============ */
const Net = {
  async call(path, opts){
    const headers = {'Content-Type':'application/json', 'X-Owner': myId()};
    const r = await fetch(API_BASE + path, Object.assign({headers: headers}, opts || {}));
    if(!r.ok){
      let msg = 'HTTP ' + r.status;
      try{
        const j = JSON.parse(await r.text());
        if(j && j.error) msg = j.error;
      }catch(e){}
      throw new Error(msg);
    }
    const txt = await r.text();
    return txt ? JSON.parse(txt) : null;
  },
  reviewStatus(id){ return this.call('/items/' + encodeURIComponent(id) + '/status'); },
  list(){ return this.call('/items'); },
  mine(){ return this.call('/mine'); },
  sync(){ return this.call('/sync'); },
  precheck(it){ return this.call('/precheck', {method:'POST', body: JSON.stringify(it)}); },
  create(it){ return this.call('/items', {method:'POST', body: JSON.stringify(it)}); },
  update(id, patch){ return this.call('/items/' + encodeURIComponent(id), {method:'PATCH', body: JSON.stringify(patch)}); },
  remove(id){ return this.call('/items/' + encodeURIComponent(id), {method:'DELETE'}); },
  report(id){ return this.call('/items/' + encodeURIComponent(id) + '/report', {method:'POST'}); },
  claim(id, body){ return this.call('/items/' + encodeURIComponent(id) + '/claims', {method:'POST', body: JSON.stringify(body || {})}); },
  claims(){ return this.call('/claims'); },
  claimAction(id, body){ return this.call('/claims/' + encodeURIComponent(id), {method:'PATCH', body: JSON.stringify(body)}); },
  complete(id, code){ return this.call('/claims/' + encodeURIComponent(id) + '/complete', {method:'POST', body: JSON.stringify({code: code || ''})}); },
  supplement(id, body){ return this.call('/claims/' + encodeURIComponent(id) + '/supplement', {method:'POST', body: JSON.stringify(body)}); },
  vision(image, mime){ return this.call('/vision/analyze', {method:'POST', body: JSON.stringify({image: image, mime: mime || 'image/jpeg'})}); },
  format(body){ return this.call('/format', {method:'POST', body: JSON.stringify(body)}); },
  notices(){ return this.call('/notices'); },
  recover(body){ return this.call('/recover', {method:'POST', body: JSON.stringify(body)}); },
  accountLogin(body){ return this.call('/account/login', {method:'POST', body: JSON.stringify(body)}); },
  readNotices(){ return this.call('/notices/read', {method:'POST'}); }
};
let netOnline = false;
let netBusy = false;
let netFails = 0;

function setNetBadge(){
  const el = document.getElementById('netBadge');
  if(!el) return;
  if(!API_BASE){
    el.className = 'netbadge';
    el.textContent = '📴 本机模式：数据只保存在这台设备，认领 / 匹配需要用公网地址打开';
    return;
  }
  el.className = 'netbadge ' + (netOnline ? 'on' : 'off');
  el.textContent = netOnline
    ? '🌐 已连接服务器：' + location.origin + '（其他同学也能看到）'
    : '⚠️ 暂时连不上服务器，正在用本机数据';
}
function showStale(){
  const b = document.getElementById('errTop');
  if(!b) return;
  b.textContent = '⚠️ 连不上服务器：这个链接可能已经过期（每次重启地址会变）。请用最新的公网地址重新打开；点这里可以重试。';
  b.classList.add('show');
  b.onclick = function(){ netFails = 0; b.classList.remove('show'); netSync(); };
}
async function netSync(){
  if(!API_BASE || netBusy) return;
  netBusy = true;
  try{
    let pub = null, mine = [];
    try{
      const s = await Net.sync();
      pub = s.items; mine = s.mine || [];
      if(typeof s.unread === 'number') updateBell(s.unread);
    }catch(e0){
      const res = await Promise.all([Net.list(), Net.mine().catch(function(){ return []; })]);
      pub = res[0]; mine = res[1];
    }
    if(Array.isArray(pub)){
      const byId = {};
      pub.forEach(function(x){ byId[x.id] = x; });
      (mine || []).forEach(function(x){ byId[x.id] = x; });   /* 自己的覆盖公开版，带核验特征和完整电话 */
      LS.set(STORE_KEY, JSON.stringify(Object.keys(byId).map(function(k){ return byId[k]; })));
      netOnline = true;
      netFails = 0;
      renderLost(); renderFound(); renderMine();
    }
  }catch(e){
    netOnline = false;
    netFails++;
    if(netFails >= 3) showStale();
  }
  netBusy = false;
  setNetBadge();
}
function applyRemove(id){
  if(API_BASE){
    Net.remove(id).then(netSync).catch(function(){ toast('没连上共享服务器，删除没有生效'); });
  } else {
    Store.remove(id); renderMine(); setNetBadge();
  }
}

/* ============ 中央宣传窗（清华写实 + 企业示意） ============ */
const MEMORIAL = [
  {key:'thu', star:'🎓', name:'清华要闻', sub:'建校115周年 · 党组织百年',
   blocks:[
     {h:'🎉 建校 115 周年校庆', p:['2026年4月26日，清华大学迎来建校115周年，校友返校日温馨启幕；今年亦逢清华党组织建立100周年。','校庆期间举办综合、学术、展览、体育、开放等各类活动，第44届“挑战杯”学生课外学术科技作品展如火如荼，北院修缮后作为学生活动中心开放。']},
     {h:'🔬 科研捷报频传', p:['人形机器人反应式踢球技能、固态电池电解质新进展、磁斯格明子量子比特信息方案、兆瓦级高空风力发电系统试飞成功。','碳中和成果获教育部自然科学一等奖；在量子计算、人工智能、能源材料等领域持续产出标志性成果。']},
     {h:'🌱 红色育人 · 全面发展', p:['坚持“红色育人底色”，书院制培养、人工智能赋能教学、440余门AI赋能课程。','体育、美育、劳动教育成果丰硕，毕业生赴重点单位就业比例连续16年超80%，到祖国最需要的地方建功立业。']}
   ]},
  {key:'gc', star:'🏔️', name:'国城控股集团', sub:'红色引领 · 绿色发展',
   blocks:[
     {h:'🚀 红色引领，绿色发展', p:['在吴城董事长带领下，以“红色引领、绿色发展”为理念，带领集团从智慧矿山拓展至化工、贸易、能源。','以科技创新驱动传统产业升级，绿色低碳、安全智能，市值再创新高。']},
     {h:'⛏️ 智慧矿山 · 化工能源', p:['深耕智慧矿山建设，推动开采智能化、管理数字化。','延伸至化工、能源领域，服务国家战略与实体经济高质量发展。']},
     {h:'🤝 热心公益', p:['积极支持校园公益平台建设，以实干担当回馈社会。']}
   ]},
  {key:'zj', star:'🌾', name:'中基控股集团', sub:'智慧文旅 · 乡村振兴',
   blocks:[
     {h:'🌟 长期价值，多元责任', p:['葛坚董事长以“长期价值投资”与“多元责任担当”为理念，坚持企业发展与社会贡献并重。','长期投身公益慈善与家乡振兴事业。']},
     {h:'🏞️ 智慧文旅 · 乡村振兴', p:['深耕智慧文旅，以数字化手段活化文旅资源、提升体验。','赋能乡村振兴，带动家乡产业与就业，微光汇聚，责任如山。']}
   ]}
];

/* ============ 清华园指路 FAQ ============ */
const FAQ = [
 {cat:'入校与校门', items:[
   {q:'校外访客怎么进校？', a:'校外访客可凭身份证在指定校门登记入校，或提前通过“清华访客”线上预约。推荐从西门或东南门入校。', img:'校门位置示意图'},
   {q:'哪个校门离地铁最近？', a:'东南门距离地铁圆明园站约 600 米，是离地铁最近的校门；西门离地铁 4 号线圆明园站也较近，步行约 8 分钟。', img:'校门—地铁标注图'},
 ]},
 {cat:'食堂与餐饮', items:[
   {q:'游客能在哪个食堂吃饭？', a:'观畴园（万人食堂）、听涛园等开放窗口支持校园卡或扫码支付，部分楼层对游客开放，建议避开午高峰。', img:'食堂实景图'},
   {q:'吃饭怎么支付？', a:'支持微信 / 支付宝扫码，以及校园卡；游客直接使用移动支付即可，无需办卡。', img:''},
 ]},
 {cat:'图书馆', items:[
   {q:'能进图书馆参观吗？', a:'老图书馆、北馆（李文正馆）对师生开放，访客可在开放区域安静参观，阅览区需校园卡进入。', img:'图书馆平面示意图'},
 ]},
 {cat:'生活服务', items:[
   {q:'校医院在哪、能看病吗？', a:'校医院位于近春园一带，师生及访客急症可挂门诊；常用药品可在此开具，位置见图。', img:'校医院位置图'},
   {q:'快递在哪取？', a:'校内快递服务中心集中在紫荆公寓区附近，凭取件码在自助柜取件，营业时间一般为 9:00–21:00。', img:'快递点位置图'},
 ]},
 {cat:'拍照打卡', items:[
   {q:'二校门 / 清华学堂哪里拍好看？', a:'二校门、清华学堂、近春园荷塘是经典打卡点；清晨与傍晚光线最佳，注意避开人流高峰更出片。', img:'打卡点实景图'},
 ]},
];
const LANDMARKS = [
 {name:'西门（主校门）', icon:'🌟', x:9,  y:34, desc:'清华最具代表性的校门，题字“清华大学”于此，访客主要入校口之一，紧邻圆明园。'},
 {name:'观畴园（食堂）', icon:'🍚', x:34, y:22, desc:'万人食堂，位于校园中北部，游客可扫码就餐，菜品丰富、性价比高。'},
 {name:'紫操',           icon:'🏃', x:72, y:14, desc:'紫荆操场，校园东北部，夜跑与社团活动常用场地。'},
 {name:'综合体育馆',     icon:'🏟️', x:86, y:20, desc:'东北部大型场馆，开学典礼、毕业典礼与大型演出常在此举办。'},
 {name:'图书馆（北馆）', icon:'📚', x:70, y:30, desc:'李文正馆，早期建筑区东北侧，馆内安静、适合自习与参观。'},
 {name:'老图书馆',       icon:'📚', x:60, y:36, desc:'清华早期四大建筑之一，红砖坡顶，杨绛先生笔下“最爱的图书馆”。'},
 {name:'大礼堂',         icon:'🎭', x:46, y:42, desc:'古罗马穹顶风格，与大草坪、日晷构成校园中轴经典景观。'},
 {name:'清华学堂',       icon:'🏛️', x:56, y:44, desc:'1911 年建校起点，德国古典风格，培养人才的摇篮。'},
 {name:'校史馆',         icon:'📜', x:38, y:50, desc:'展示清华建校与发展历程，位于大礼堂西侧，预约可参观。'},
 {name:'二校门',         icon:'🏛️', x:48, y:58, desc:'清华标志性白色牌坊，最早的主校门，最热门的拍照打卡点。'},
 {name:'近春园（荷塘）', icon:'🌊', x:28, y:68, desc:'朱自清《荷塘月色》笔下的荷塘，荒岛、亭廊与垂柳环绕，散步佳处。'},
 {name:'校医院',         icon:'🏥', x:18, y:62, desc:'校园西南部，急症门诊与常用药开具，急诊 24 小时（010-62782185）。'},
 {name:'清芬园（食堂）', icon:'🍜', x:56, y:64, desc:'中部主要食堂，风味档口多，支持移动支付，建议避开午高峰。'},
 {name:'艺术博物馆',     icon:'🖼️', x:78, y:84, desc:'校园东南角，常设校藏与专题大展，建筑本身也是打卡点。'},
 {name:'东门',           icon:'🚪', x:90, y:46, desc:'东侧校门，临近东区教学科研楼群与主楼一带。'}
];

/* 实景图：均取自清华大学官网（www.tsinghua.edu.cn）公开组图，热链仅供预览 */
const LANDMARK_PHOTOS = {
  '二校门':        'https://www.tsinghua.edu.cn/__local/1/63/BE/E6DAC008600170338C51AF67AA2_A30DA786_A857B.jpg',
  '清华学堂':      'https://www.tsinghua.edu.cn/__local/E/CB/AB/4013FF557763C9195DBEE3C9E23_4AEC7F2F_B0999.jpg',
  '大礼堂':        'https://www.tsinghua.edu.cn/__local/4/08/64/830C8E47DF858F512AC2BF7A400_F226E486_A08D2.jpg',
  '老图书馆':      'https://www.tsinghua.edu.cn/__local/3/E7/C3/20330133B5ADFF11BED6AC2A2A6_91145F8C_9B199.jpg',
  '近春园（荷塘）':'https://www.tsinghua.edu.cn/__local/0/DB/2D/DBA5A25DA78C44ED8C2DE6C1A10_2423BADD_1C3823.jpg',
  '艺术博物馆':    'https://www.tsinghua.edu.cn/__local/0/E9/B5/123588172AED93BD0193C0D83FA_DED4F3EB_901C6.jpg',
  '综合体育馆':    'https://www.tsinghua.edu.cn/__local/F/F9/68/A5A677B7D9B84F28D44A2452AFF_D369F59E_17F17B.jpg'
};

/* 常见电话：整理自清华大学官方网站与官方发布渠道 */
const PHONES = [
 {g:'医疗急救', items:[
   {n:'校医院急诊（24 小时）', t:'010-62782185'},
   {n:'24 小时心理服务热线', t:'010-62785252'}
 ]},
 {g:'安全保卫', items:[
   {n:'保卫部 24 小时报警求助', t:'010-62782001'},
   {n:'保卫部值班（备用）', t:'010-62783779'}
 ]},
 {g:'后勤服务', items:[
   {n:'后勤综合服务热线 / 校内查号台', t:'010-62793001'},
   {n:'学生公寓 24 小时服务热线', t:'010-62793003'}
 ]},
 {g:'招生咨询', items:[
   {n:'本科生招生办公室', t:'010-62770334'},
   {n:'研究生招生办公室', t:'010-62781380'}
 ]}
]

/* ============ 导航 ============ */
const stack = [];
function burstConfetti(){
  const host = document.getElementById('screen-success');
  if(!host) return;
  const colors = ['#8a5fd0', '#f0a6ca', '#ffd166', '#7bdff2', '#b8f2a8', '#f4978e'];
  for(let i = 0; i < 26; i++){
    const el = document.createElement('i');
    el.className = 'confetti';
    el.style.left = (6 + Math.random() * 88) + '%';
    el.style.background = colors[i % colors.length];
    el.style.animationDelay = (Math.random() * 0.3) + 's';
    host.appendChild(el);
    (function(node){ setTimeout(function(){ node.remove(); }, 2400); })(el);
  }
}
/* ===== 失物热力 ===== */
const HEAT_ZONES = [
  {name:'图书馆', x:44, y:47, kw:['图书馆','李文正','北馆','老馆']},
  {name:'食堂', x:39, y:38, kw:['食堂','餐厅','桃李','听涛','清芬','观畴','万人','紫荆园']},
  {name:'教学楼', x:46, y:62, kw:['教学楼','六教','三教','四教','五教','一教','二教','新水','旧水','建筑馆','学堂']},
  {name:'宿舍', x:25, y:78, kw:['宿舍','公寓','南区','北区']},
  {name:'运动场', x:68, y:33, kw:['操场','体育','篮球','网球','游泳','综体','西体','东操','紫操']},
  {name:'校门 / 路上', x:17, y:41, kw:['校门','门口','路上','路边']}
];

function renderHeat(){
  const host = document.getElementById('heatPanel');
  if(!host) return;
  const items = Store.list({statuses:['approved','claimed','closed']});
  const zones = HEAT_ZONES.map(function(z){ return {name:z.name, x:z.x, y:z.y, n:0}; });
  const other = {name:'其他 / 未填写', x:50, y:50, n:0};
  items.forEach(function(it){
    const text = (it.place || '') + ' ' + (it.title || '');
    let hit = null;
    for(let i = 0; i < HEAT_ZONES.length && !hit; i++){
      for(let j = 0; j < HEAT_ZONES[i].kw.length; j++){
        if(text.indexOf(HEAT_ZONES[i].kw[j]) >= 0){ hit = zones[i]; break; }
      }
    }
    (hit || other).n++;
  });
  const all = zones.concat([other]).sort(function(a,b){ return b.n - a.n; });
  const total = all.reduce(function(s,z){ return s + z.n; }, 0);
  const max = Math.max.apply(null, [1].concat(all.map(function(z){ return z.n; })));
  const done = items.filter(function(x){ return x.status === 'closed' || x.status === 'claimed'; }).length;
  const rate = total ? Math.round(done / total * 100) : 0;
  const top = all.filter(function(z){ return z.name !== '其他 / 未填写'; }).slice(0, 2)
    .map(function(z){ return z.name; }).join('和');
  host.innerHTML = '<div class="heat-panel">' +
    '<div class="heat-head">🔥 失物热力<span>共 ' + total + ' 条发布</span></div>' +
    '<div class="heat-sub">' + (top || '图书馆') + '最容易丢东西；已闭环 ' + done + ' 条，闭环率 ' + rate + '%。</div>' +
    all.map(function(z){
      return '<div class="heat-row"><span class="heat-name">' + esc(z.name) + '</span>' +
        '<span class="heat-bar"><i style="width:' + Math.round(z.n / max * 100) + '%"></i></span>' +
        '<span class="heat-n">' + z.n + '</span></div>';
    }).join('') + '</div>';

  const wrap = document.getElementById('mapWrap');
  if(wrap){
    let layer = document.getElementById('heatDots');
    if(!layer){
      layer = document.createElement('div');
      layer.id = 'heatDots';
      layer.className = 'heat-dots';
      wrap.appendChild(layer);
    }
    layer.innerHTML = zones.filter(function(z){ return z.n > 0; }).map(function(z){
      const size = 20 + Math.min(24, z.n * 2.5);
      return '<div class="heat-dot" style="left:' + z.x + '%;top:' + z.y + '%;width:' + size +
        'px;height:' + size + 'px" title="' + esc(z.name) + ' ' + z.n + ' 条">' + z.n + '</div>';
    }).join('');
  }
}

let activeLayer = null;
const layerObserver = new MutationObserver(function(){
  const open = document.querySelector('.sheet.show');
  if(open){
    activeLayer = function(){ open.classList.remove('show'); };
  }else{
    const v = document.getElementById('imgViewer');
    if(!v || !v.classList.contains('show')) activeLayer = null;
  }
});
document.querySelectorAll('.sheet').forEach(function(s){
  layerObserver.observe(s, {attributes:true, attributeFilter:['class']});
});

function activate(name){
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  const el=document.getElementById('screen-'+name);
  if(!el) return;
  el.classList.add('active');
  const sc=el.querySelector('.scroll'); if(sc) sc.scrollTop=0;
  if(name==='map') renderHeat();
}
function show(name){
  const cur=document.querySelector('.screen.active');
  if(cur && cur.id==='screen-'+name) return;
  activate(name);
  if(stack[stack.length-1]!==name) stack.push(name);
  try{ history.pushState({screen:name}, '', '#'+name); }catch(e){}
}
function back(){
  history.back();
}
window.addEventListener('popstate', function(){
  if(activeLayer){
    const fn = activeLayer;
    activeLayer = null;
    try{ fn(); }catch(e){}
    const cur = document.querySelector('.screen.active');
    const hash = cur ? '#' + cur.id.replace('screen-','') : (location.hash || '#home');
    try{ history.pushState({screen:(cur||{}).id}, '', hash); }catch(e){}
    return;
  }
  const name=(location.hash || '#home').replace('#','') || 'home';
  stack.length = 0;
  stack.push(name);
  activate(name);
});
function toast(msg){const n=document.getElementById('note');n.textContent=msg;n.classList.add('show');setTimeout(()=>n.classList.remove('show'),1400);}
function aiBusy(on, text){
  const el = document.getElementById('aiBusy');
  if(!el) return;
  if(text){ const t = document.getElementById('aiBusyText'); if(t) t.textContent = text; }
  el.classList.toggle('show', !!on);
}

/* ============ 渲染：列表 ============ */
function itemHTML(it, srcLabel){
  const place = it.place || it.loc || '';
  const act   = it.act || (it.type === 'lost' ? '提供线索' : '认领');
  const mine  = !!it.isMine || (it.ownerId && it.ownerId === myId());
  const tag   = mine
    ? '<span class="src-tag" style="background:#2f7d46">我的</span>'
    : '<span class="src-tag">'+esc(srcLabel)+'</span>';
  const thumb = it.photo
    ? '<div class="thumb" style="padding:0;overflow:hidden;background:#eee"><img src="'+esc(it.photo)+'" alt="" style="width:100%;height:100%;object-fit:cover;display:block"></div>'
    : thumbHTML(it.cat);
  let btnHTML;
  if(mine){ btnHTML = '<button class="btn ghost">查看</button>'; }
  else if(it.myClaim === 'pending'){ btnHTML = '<button class="btn ghost">已申请</button>'; }
  else if(it.myClaim === 'accepted' || it.myClaim === 'completed'){ btnHTML = '<button class="btn ghost">已通过</button>'; }
  else if(it.myClaim === 'need_more'){ btnHTML = '<button class="btn" data-act="补充信息">补充信息</button>'; }
  else { btnHTML = '<button class="btn" data-act="'+esc(act)+'">'+esc(act)+'</button>'; }
  const chips = (it.fields ? Object.keys(it.fields).map(function(k){ return it.fields[k]; }).filter(Boolean).slice(0, 3) : [])
    .map(function(v){ return '<span class="chip">' + esc(v) + '</span>'; }).join('');
  const meta = '📍 ' + esc(place) + (it.createdAt ? (' · ' + fmtTime(it.createdAt)) : '');
  return '<div class="item" data-item="'+esc(it.id)+'">'+
    thumb+
    '<div class="body"><div class="tt">'+tag+esc(it.title)+statusChip(it.status)+'</div>'+
    (it.summary ? '<div class="sum">'+esc(it.summary)+'</div>' : '')+
    '<div class="dd">'+esc(it.desc)+'</div>'+
    (chips ? '<div class="chips">' + chips + '</div>' : '')+
    '<div class="row"><span class="meta">'+meta+'</span>'+ btnHTML +
    '</div></div></div>';
}
function renderList(wrap, arr, srcLabel){
  if(!wrap) return;
  wrap.innerHTML = arr.map(it=>itemHTML(it,srcLabel)).join('') ||
    '<div class="empty">暂无内容</div>';
}
function renderLost(){ renderList(document.getElementById('lostWrap'), Store.list({type:'found', statuses:['approved','claimed','closed']}), '招领'); }
function renderFound(){ renderList(document.getElementById('foundWrap'), Store.list({type:'lost', statuses:['approved','claimed','closed']}), '寻物'); }

/* ============ 渲染：我的发布 ============ */
function renderMine(){
  const w = document.getElementById('mineWrap');
  const list = Store.list({owner: myId()});
  updateBadge();
  document.getElementById('mineHint').textContent = list.length
    ? '共 '+list.length+' 条发布，只有「已上架」的才会出现在公共列表里。'
    : '你还没有发布过内容。提交后会先进入审核，通过后才上架。';
  if(!list.length){
    w.innerHTML = '<div class="empty">还没有发布记录<br><br>'+
      '<button class="btn" data-publish="lost">发布寻物</button> '+
      '<button class="btn ghost" data-publish="found">发布招领</button></div>';
    return;
  }
  w.innerHTML = list.map(it=>{
    const m = catInfo(it.cat);
    const typeName = it.type === 'lost' ? '寻物启事' : '招领启事';
    return '<div class="mini">'+
      '<div class="mh">'+m.e+' '+esc(it.title)+'<span class="st st-'+esc(it.status)+'">'+esc(statusText(it.status))+'</span></div>'+
      '<div class="mmeta">'+typeName+' · '+esc(it.place||'')+' · '+fmtTime(it.createdAt)+'</div>'+
      (it.status==='rejected' && it.rejectReason ? '<div class="reason">驳回理由：'+esc(it.rejectReason)+'</div>' : '')+
      (it.status==='pending' ? '<div class="mmeta">审核通过后才会被其他人看到</div>' : '')+
      '<div class="mact">'+
        '<button class="btn ghost" data-item="'+esc(it.id)+'">查看</button>'+
        (it.status==='rejected' ? '<button class="btn" data-edit="'+esc(it.id)+'">✏️ 修改并重新提交</button>' : '')+
        '<button class="btn danger" data-mine-del="'+esc(it.id)+'">撤回删除</button>'+
      '</div></div>';
  }).join('');
}

function renderLend(tab){
  const w=document.getElementById('lendWrap');
  if(tab==='svc') renderList(w, SERVICES, '服务'); else renderList(w, LEND, '出借');
}
function renderBorrow(tab){
  const w=document.getElementById('borrowWrap');
  if(tab==='nsvc') renderList(w, NEED_SERVICES, '求服务'); else renderList(w, BORROW, '求借');
}

/* ============ 渲染：中央宣传窗 ============ */
let MEMORIAL_DATA = MEMORIAL.slice();

async function loadAnnouncements(){
  if(!API_BASE) return;
  try{
    const arr = await fetch(API_BASE + '/announcements').then(function(r){ return r.json(); });
    if(Array.isArray(arr) && arr.length){
      const annSlides = arr.slice(0, 2).map(function(a){
        return {
          key: 'ann_' + a.id,
          star: a.pinned ? '📌' : '📢',
          name: a.title,
          sub: '校园公告 · ' + fmtTime(a.publishedAt),
          blocks: [{h: a.title, p: [a.body]}]
        };
      });
      // 公告排在最前，原来的内容保留在后面
      MEMORIAL_DATA = annSlides.concat(MEMORIAL);
      renderMemorial();
    }
  }catch(e){}
}

function renderMemorial(){
  const track=document.getElementById('memTrack');
  track.innerHTML = MEMORIAL_DATA.map((m,i)=>
    '<div class="mem-slide" data-mem="'+i+'">'+
    '<div class="mem-star">'+m.star+'</div>'+
    '<div><div class="mn">'+m.name+'</div><div class="ms">'+m.sub+'</div></div></div>'
  ).join('');
  const dots=document.getElementById('memDots');
  if(dots){
    dots.innerHTML = MEMORIAL_DATA.map(function(_,i){ return '<i class="'+(i===0?'on':'')+'"></i>'; }).join('');
  }
  track.onscroll=()=>{
    const idx=Math.round(track.scrollLeft/track.clientWidth);
    document.querySelectorAll('#memDots i').forEach((d,i)=>d.classList.toggle('on',i===idx));
  };
  startMemorialAuto();
}
let memTimer = null;
function startMemorialAuto(){
  if(memTimer) clearInterval(memTimer);
  memTimer = setInterval(function(){
    const track = document.getElementById('memTrack');
    const home = document.getElementById('screen-home');
    if(!track || !home || !home.classList.contains('active')) return;
    if(!track.clientWidth || MEMORIAL_DATA.length < 2) return;
    const idx = Math.round(track.scrollLeft / track.clientWidth);
    const next = (idx + 1) % MEMORIAL_DATA.length;
    track.scrollTo({left: next * track.clientWidth, behavior: 'smooth'});
  }, 4800);
}
function renderMemorialDetail(idx){
  const m=MEMORIAL_DATA[idx];
  if(!m) return;
  const w=document.getElementById('memorialWrap');
  w.innerHTML = '<div class="sectitle">'+m.name+' · '+m.sub+'</div>'+
    m.blocks.map(b=>'<div class="blk"><h3>'+b.h+'</h3>'+b.p.map(p=>'<p>'+p+'</p>').join('')+'</div>').join('');
  document.querySelector('#screen-memorial .t').textContent = m.name;
}

/* ============ 渲染：地图 ============ */
(function renderMap(){
  const w=document.getElementById('mapWrap');
  w.insertAdjacentHTML('beforeend','<div class="map-title">清华大学全景文旅图</div>');
  w.insertAdjacentHTML('beforeend','<div class="compass"><b>N</b></div>');
  /* 模糊校园边界：不规则多边形，拟合清华主校区轮廓（西南内凹、东北外凸） */
  w.insertAdjacentHTML('beforeend','<svg class="boundary-svg" viewBox="0 0 100 100" preserveAspectRatio="none">'+
    '<polygon points="7,24 20,12 40,7 60,6 74,6 94,10 96,30 94,44 96,60 88,78 80,90 60,88 44,92 30,86 16,80 10,62 6,44" '+
    'fill="rgba(98,38,156,.07)" stroke="rgba(98,38,156,.5)" stroke-width="0.6" stroke-dasharray="2.4 1.6"/></svg>');
  w.insertAdjacentHTML('beforeend','<div class="park" style="left:6%;top:16%;width:34%;height:28%"></div>');
  w.insertAdjacentHTML('beforeend','<div class="park" style="left:50%;top:28%;width:32%;height:26%"></div>');
  w.insertAdjacentHTML('beforeend','<div class="park" style="left:16%;top:58%;width:28%;height:22%"></div>');
  w.insertAdjacentHTML('beforeend','<div class="water" style="left:22%;top:60%;width:14%;height:11%"></div>');
  w.insertAdjacentHTML('beforeend','<div class="water" style="left:30%;top:40%;width:10%;height:8%"></div>');
  w.insertAdjacentHTML('beforeend','<div class="road" style="left:0;top:40%;width:100%"></div>');
  w.insertAdjacentHTML('beforeend','<div class="road" style="left:44%;top:0;width:7px;height:100%"></div>');
  w.insertAdjacentHTML('beforeend','<div class="road" style="left:0;top:62%;width:100%"></div>');
  w.insertAdjacentHTML('beforeend','<div class="route" style="left:14%;top:36%;width:46%;transform:rotate(26deg)"></div>');
  w.insertAdjacentHTML('beforeend','<div class="legend"><b>图例</b><br>🏛️ 校门/礼堂 · 📚 图书馆<br>🍚 食堂 · 🏥 医疗 · 🏟️ 场馆<br>🌊 水系 · 🌳 绿地</div>');
  LANDMARKS.forEach((l,i)=>{
    const p=document.createElement('div');
    const up = l.y < 20 ? false : (l.y > 78 ? true : (i % 2 === 1));
    p.className='spot'+(up?' up':'');p.style.left=l.x+'%';p.style.top=l.y+'%';
    p.innerHTML='<div class="badge">'+(l.icon||'📍')+'</div><div class="sl">'+l.name.replace(/（.*?）/,'')+'</div>';
    p.onclick=()=>openLandmark(i);
    w.appendChild(p);
  });
})();
function openLandmark(i){
  const l=LANDMARKS[i];
  const url=LANDMARK_PHOTOS[l.name]||'';
  const th=document.getElementById('isThumb');
  th.style.background='linear-gradient(135deg,#c9a24a,#e3c98a)';
  if(url){
    th.innerHTML='<img src="'+url+'" alt="'+l.name+'" style="width:100%;height:100%;object-fit:cover;border-radius:12px" onerror="this.parentNode.textContent=\'📍 图片未能加载\';">';
  }else{
    th.textContent='📍';
  }
  document.getElementById('isTitle').textContent=l.name;
  document.getElementById('isDesc').textContent=l.desc;
  document.getElementById('isMeta').textContent=url?'📷 实景图来源：清华大学官网公开组图':'📷 校园实景图（待补充，敬请期待）';
  const btn=document.getElementById('isAction'); btn.style.display='none';
  document.getElementById('itemSheet').classList.add('show');
}

/* ============ 渲染：FAQ ============ */
(function renderFaq(){
  const w=document.getElementById('faqListWrap');
  /* 常见电话入口（下钻页） */
  const pe=document.createElement('div');
  pe.className='q';pe.id='phoneEntry';
  pe.style.background='linear-gradient(135deg,#f7f1fc,#fdf6e9)';pe.style.borderColor='var(--purple-ll)';
  pe.innerHTML='<div class="qt"><b>📞 常见电话</b><br><span style="font-size:12px;color:var(--sub)">急救 · 安保 · 后勤 · 招生，一键拨打</span></div><div class="qa">›</div>';
  pe.onclick=()=>{ renderPhones(); show('phones'); };
  w.appendChild(pe);
  FAQ.forEach((c,ci)=>{
    w.insertAdjacentHTML('beforeend','<div class="cat">'+c.cat+'</div>');
    c.items.forEach((it,qi)=>{
      const d=document.createElement('div');
      d.className='q';d.innerHTML='<div class="qt">'+it.q+'</div><div class="qa">›</div>';
      d.onclick=()=>openFaq(ci,qi);
      w.appendChild(d);
    });
  });
  w.insertAdjacentHTML('beforeend','<div class="faq-note">🗺️ 地图与实景图说明：地标位置参考清华园实际布局与公开地图修订（示意，非导航底图）；实景图取自清华大学官网公开组图，若未能加载请检查网络。</div>');
})();
function renderPhones(){
  const w=document.getElementById('phonesWrap');
  let h='<div class="hintline">以下电话均整理自清华大学官方网站与官方发布渠道，点按号码可直接拨号。</div>';
  PHONES.forEach(g=>{
    h+='<div class="cat">'+g.g+'</div>';
    g.items.forEach(it=>{
      h+='<a class="ph-row" href="tel:'+it.t.replace(/-/g,'')+'"><span class="ph-n">'+it.n+'</span><span class="ph-t">'+it.t+'</span><span class="qa">›</span></a>';
    });
  });
  h+='<div class="faq-note">📞 号码来源：清华大学保卫部、校医院、总务部门及本科 / 研究生招生网的公开信息；如与最新官方公布不符，以学校官方渠道为准。校外紧急电话：报警 110 · 火警 119 · 急救 120 / 999。</div>';
  w.innerHTML=h;
}
function openFaq(ci,qi){
  const it=FAQ[ci].items[qi];
  show('faqDetail');
  document.getElementById('faqDetailWrap').innerHTML =
    '<div class="tag">'+FAQ[ci].cat+'</div>'+
    '<div class="fdq">'+it.q+'</div>'+
    '<div class="fda">'+it.a+'</div>'+
    (it.img?'<div class="imgph">🖼️ '+it.img+'<br><span style="font-size:11px;opacity:.7">（文字 + 示意图 / 校园实景图 / 位置截图）</span></div>':'');
}

/* ============ 物品详情 ============ */
function openItem(id){
  let it = Store.get(id);
  if(!it){
    it = [].concat(LEND, SERVICES, BORROW, NEED_SERVICES).find(x=>x.id===id) || null;
  }
  if(!it) return;
  const m = catInfo(it.cat);
  const place = it.place || it.loc || '';
  const act = it.act || (it.type === 'lost' ? '提供线索' : '认领');
  const th = document.getElementById('isThumb');
  th.style.background = 'linear-gradient(135deg,'+m.c+','+shade(m.c)+')';
  th.innerHTML = it.photo
    ? '<img src="'+esc(it.photo)+'" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:12px">'
    : m.e;
  document.getElementById('isTitle').textContent = it.title;
  document.getElementById('isDesc').textContent = it.desc;
  document.getElementById('isMeta').textContent = '📍 '+place+
    (it.status ? ('　|　'+statusText(it.status)) : '')+
    (it.contact && it.contact.phone ? ('　|　📞 '+maskPhone(it.contact.phone)) : '');
  const btn = document.getElementById('isAction');
  const box = document.getElementById('claimBox');
  const mine = !!it.isMine || (it.ownerId && it.ownerId === myId());
  const isLostPost = it.type === 'lost';           /* 寻物帖：来的人可能是捡到的人 */
  const canClaim = API_BASE && !mine && it.status === 'approved';
  const myClaim = it.myClaim || '';
  const myClaimId = it.myClaimId || '';
  currentSheetId = it.id;
  currentClaimKind = isLostPost ? 'found' : 'claim';
  currentClaimMode = 'new';
  currentClaimId = '';
  document.getElementById('claimMsg').value = '';
  document.getElementById('claimPhone').value = '';
  btn.disabled = false;
  if(box) box.style.display = 'none';
  if(mine){
    btn.style.display = 'block';
    btn.disabled = false;
    btn.textContent = '去「我的发布」管理';
    btn.onclick = function(){
      document.getElementById('itemSheet').classList.remove('show');
      renderMine(); renderClaims(); renderAccBox(); show('mine');
    };
  } else if(myClaim === 'pending'){
    btn.style.display = 'block';
    btn.disabled = true;
    btn.textContent = '已申请，等待对方确认';
  } else if(myClaim === 'accepted' || myClaim === 'completed'){
    btn.style.display = 'block';
    btn.disabled = true;
    btn.textContent = '已通过，联系方式见「我的发布」';
  } else if(myClaim === 'need_more' || myClaim === 'rejected'){
    currentClaimMode = 'supplement';
    currentClaimId = myClaimId;
    btn.style.display = 'block';
    btn.disabled = false;
    btn.textContent = myClaim === 'need_more' ? '对方要你补充信息' : '重新申请（上次被拒）';
    document.getElementById('claimTip').textContent = myClaim === 'need_more'
      ? '补充更具体的细节，让对方更容易核对'
      : '上次被拒了：重新填写更完整、更具体的特征，再提交一次';
    document.getElementById('claimMsg').placeholder = myClaim === 'need_more'
      ? '例如：卡背面除了保护膜，右下角还有一道折痕'
      : '写清颜色、标记、划痕、贴纸位置等只有失主知道的细节';
    document.getElementById('claimSend').textContent = myClaim === 'need_more' ? '提交补充' : '重新提交申请';
    btn.onclick = function(){ toggleClaimBox(btn, box); };
  } else if(it.status === 'claimed'){
    btn.style.display = 'block';
    btn.disabled = true;
    btn.textContent = '已被认领';
  } else if(canClaim){
    btn.style.display = 'block';
    btn.textContent = isLostPost ? '我捡到了，联系失主' : '申请认领';
    document.getElementById('claimTip').textContent = isLostPost
      ? '写清你是在哪捡到的、大概什么时候，失主会核对'
      : '写下只有失主知道的细节，对方核对后才会通过';
    document.getElementById('claimMsg').placeholder = isLostPost
      ? '例如：昨天下午在图书馆一楼自助机旁捡到，卡套是蓝色的'
      : '例如：伞骨内侧缠过胶带，伞柄上有一张卡通贴纸';
    document.getElementById('claimSend').textContent = isLostPost ? '发送给失主' : '发送认领申请';
    btn.onclick = function(){ toggleClaimBox(btn, box); };
  } else {
    btn.style.display = 'none';
  }
  const rep = document.getElementById('isReport');
  const repHint = document.getElementById('reportHint');
  if(rep){
    const canReport = API_BASE && !mine && it.status && ['approved','claimed'].indexOf(it.status) >= 0;
    rep.style.display = canReport ? 'block' : 'none';
    if(repHint) repHint.style.display = canReport ? 'block' : 'none';
    rep.onclick = function(){
      this.style.display = 'none';
      if(repHint) repHint.style.display = 'none';
      Net.report(it.id).then(function(r){
        toast('已收到举报（' + (r && r.reports || 1) + ' 人），达到 3 人会重新审核；如遇诈骗请拨打 110');
      }).catch(function(){ toast('举报失败，请稍后重试'); });
    };
  }
  document.getElementById('itemSheet').classList.add('show');
}

let currentSheetId = null;
let currentClaimKind = 'claim';
let currentClaimMode = 'new';
let currentClaimId = '';
let retypeOldId = null;
let claimsMap = {};

function toggleClaimBox(btn, box){
  if(!box) return;
  const opening = (box.style.display === 'none' || !box.style.display);
  box.style.display = opening ? 'block' : 'none';
  if(btn) btn.style.display = opening ? 'none' : 'block';
  if(opening){ try{ box.scrollIntoView({block:'nearest'}); }catch(e){} }
}

/* ============ 认领申请 / 通知 ============ */
function claimCard(c, side){
  const st = {pending:'等待确认', accepted:'已通过', rejected:'不是这个物品', completed:'已完成', need_more:'等你补充'}[c.status] || c.status;
  const cls = c.status === 'accepted' ? 'st-approved' : (c.status === 'rejected' ? 'st-rejected' : 'st-pending');
  let acts = '';
  if(side === 'received' && c.status === 'pending'){
    acts = '<button class="btn" data-claim-view="'+esc(c.id)+'">查看并核对</button>' +
           '<button class="btn danger" data-claim-reject="'+esc(c.id)+'">不是这个</button>';
  }
  if(c.status === 'accepted'){
    if(c.returnCode){
      acts += '<div class="return-code"><span>取件码</span><b>' + esc(c.returnCode) + '</b>' +
        '<div class="tip-small">把码给对方，对方确认后完成归还</div></div>';
    }
    if(c.canConfirm){
      acts += '<div class="claimbox" style="display:block;margin-top:8px">' +
        '<input id="rc_' + esc(c.id) + '" maxlength="6" inputmode="numeric" placeholder="输入对方的 6 位取件码">' +
        '<button class="btn ok" data-claim-return="' + esc(c.id) + '" style="width:100%">确认归还</button></div>';
    } else if(c.kind === 'help' && side === 'received'){
      acts += '<button class="btn" data-claim-done="' + esc(c.id) + '">已完成帮忙</button>';
    }
  }
  if(side === 'sent' && (c.status === 'need_more' || c.status === 'rejected')){
    acts = '<button class="btn" data-claim-supplement="'+esc(c.id)+'">补充信息</button>';
  }
  const supBox = (side === 'sent' && (c.status === 'need_more' || c.status === 'rejected'))
    ? '<div class="claimbox" id="sup_'+esc(c.id)+'" style="display:none">' +
      '<textarea id="supt_'+esc(c.id)+'" placeholder="补充说明，例如颜色、划痕位置、贴纸"></textarea>' +
      '<button class="btn" data-claim-supplement-ok="'+esc(c.id)+'" style="width:100%">提交补充</button></div>'
    : '';
  let contact = '';
  if(side === 'received' && c.claimContact){
    const done = (c.status === 'accepted' || c.status === 'completed');
    contact = '<div class="claimcontact">对方联系方式：' + esc(c.claimContact) +
      (done ? '' : '（通过后才显示完整号码）') + '</div>';
  }
  if(side === 'sent' && c.ownerContact){
    contact = '<div class="claimcontact">发布者联系方式：' + esc(c.ownerContact) + '</div>';
  }
  return '<div class="claim"><div class="ch">' +
    (side === 'received'
      ? (c.kind === 'help' ? '🙋 有人愿意帮忙'
         : (c.kind === 'found' ? '📥 有人捡到了你的东西' : '📥 有人申请认领'))
      : '📤 我发出的申请') +
    ' · ' + esc(c.itemTitle || '') + ' <span class="st ' + cls + '">' + st + '</span></div>' +
    '<div class="cm">' + esc(c.message || '') + '</div>' + contact +
    '<div class="ca">' + acts + '</div>' + supBox + '</div>';
}

async function renderClaims(){
  if(!API_BASE) return;
  try{
    const r = await Net.claims();
    const wrap = document.getElementById('claimsWrap');
    if(!wrap) return;
    claimsMap = {};
    (r.received || []).forEach(function(c){ claimsMap[c.id] = c; });
    (r.sent || []).forEach(function(c){ claimsMap[c.id] = c; });
    const parts = [];
    (r.received || []).forEach(function(c){ parts.push(claimCard(c, 'received')); });
    (r.sent || []).forEach(function(c){ parts.push(claimCard(c, 'sent')); });
    wrap.innerHTML = parts.length ? ('<div class="sectitle">认领申请</div>' + parts.join('')) : '';
  }catch(e){}
}

async function renderAccBox(){
  const box = document.getElementById('accBox');
  if(!box) return;
  const acc = LS.get(ACC_KEY);
  if(acc){
    const phone = LS.get(ACC_PHONE_KEY) || '';
    box.innerHTML = '<div class="acc-line">✅ 已登录：' + esc(maskPhone(phone)) +
      '　换设备/换网址时，用同一手机号登录就能看到你的发布。 ' +
      '<a href="javascript:void(0)" id="accLogout">退出</a></div>';
    const lo = document.getElementById('accLogout');
    if(lo) lo.onclick = function(){
      LS.remove(ACC_KEY); LS.remove(ACC_PHONE_KEY);
      renderAccBox(); netSync(); renderMine();
      toast('已退出，现在按本机身份使用');
    };
    return;
  }
  box.innerHTML =
    '<div class="acc-title">登录后，换设备或换网址也能看到「我的发布」<br>第一次输入手机号 + 密码就是注册</div>' +
    '<div class="acc-row">' +
    '<input id="accPhone" inputmode="numeric" maxlength="20" placeholder="手机号">' +
    '<input id="accPwd" type="password" maxlength="30" placeholder="密码（至少 4 位）"></div>' +
    '<button class="btn" id="accLogin" style="width:100%;margin-top:8px">登录 / 注册</button>';
  document.getElementById('accLogin').onclick = async function(){
    const p = (document.getElementById('accPhone').value || '').trim();
    const w = (document.getElementById('accPwd').value || '').trim();
    if(p.length < 5){ toast('请输入手机号'); return; }
    const pchk = phoneCheckLocal(p);
    if(pchk.status === 'red' || pchk.type !== 'mobile'){ toast(pchk.reason || '请用 11 位手机号注册/登录'); return; }
    if(w.length < 4){ toast('密码至少 4 位'); return; }
    this.disabled = true; this.textContent = '处理中…';
    try{
      const r = await Net.accountLogin({phone: p, password: w});
      LS.set(ACC_KEY, r.accountId);
      LS.set(ACC_PHONE_KEY, r.phone);
      renderAccBox();
      await netSync();
      renderMine(); renderClaims();
      toast(r.created ? '账号已创建，以后换设备登录同一手机号即可' : '登录成功');
    }catch(e){
      toast((e && e.message) || '登录失败，请稍后再试');
    }finally{
      this.disabled = false; this.textContent = '登录 / 注册';
    }
  };
}

async function openClaimById(cid){
  if(!claimsMap[cid]){
    try{
      const r = await Net.claims();
      claimsMap = {};
      (r.received || []).forEach(function(c){ claimsMap[c.id] = c; });
      (r.sent || []).forEach(function(c){ claimsMap[c.id] = c; });
    }catch(e){}
  }
  if(claimsMap[cid]){ openClaimReview(cid); }
  else { toast('这条申请已经处理过或已失效'); }
}

function openClaimReview(id){
  const c = claimsMap[id];
  if(!c) return;
  const isFinder = c.kind === 'found';
  const isHelp = c.kind === 'help';
  document.getElementById('csItem').innerHTML =
    '<span class="k">标题</span>' + esc(c.itemTitle || '') +
    '<div style="margin-top:6px"><span class="k">你填写的描述</span>' + esc(c.itemDesc || '（无）') + '</div>' +
    (c.itemPlace ? '<div style="margin-top:6px"><span class="k">地点</span>' + esc(c.itemPlace) + '</div>' : '') +
    (!isHelp && (c.itemSecret
      ? '<div style="margin-top:6px"><span class="k">你填写的独有特征（对方看不到）</span><span class="cs-secret">' + esc(c.itemSecret) + '</span></div>'
      : '<div style="margin-top:6px" class="cs-tip">你当时没填独有特征，这次只能靠描述核对。</div>'));
  document.getElementById('csClaimTitle').textContent = isHelp ? '对方的留言' : (isFinder ? '对方说在哪捡到的' : '对方提供的物品特征');
  document.getElementById('csTip').textContent = isHelp
    ? '确认对方能帮上忙后点「通过」，双方就能看到联系方式。'
    : (isFinder
      ? '核对地点、时间是否合理，确认是你丢的东西再点通过；通过后双方才会看到联系方式。'
      : '只有对方说的特征真的对得上，才点「通过」。通过后双方才会看到联系方式。');
  document.getElementById('csClaim').innerHTML =
    '<span class="k">' + (isFinder ? '对方说' : '对方说的特征') + '</span>' + esc(c.message || '（没有填写）') +
    (c.claimContact ? '<div style="margin-top:6px"><span class="k">对方联系方式</span>' + esc(c.claimContact) +
      (c.status === 'pending' ? '（通过后显示完整号码）' : '') + '</div>' : '') +
    '<div style="margin-top:6px"><span class="k">申请时间</span>' + fmtTime(c.createdAt) + '</div>';

  const sheet = document.getElementById('claimSheet');
  sheet.classList.add('show');

  // AI 核验（只对「我收到的、待处理」的申请开放）
  const agentBtn = document.getElementById('csAgentBtn');
  const agentBox = document.getElementById('csAgentBox');
  const agentSteps = document.getElementById('csAgentSteps');
  const agentVerdict = document.getElementById('csAgentVerdict');
  const canAgent = (c.kind !== 'help') && (c.itemSecret !== undefined) && c.status === 'pending';
  agentBox.style.display = 'none';
  agentSteps.innerHTML = '';
  agentVerdict.innerHTML = '';
  agentBtn.style.display = canAgent ? 'block' : 'none';
  agentBtn.disabled = false;
  agentBtn.textContent = '🔍 让 AI 帮我核验一下';
  agentBtn.onclick = async function(){
    this.disabled = true;
    this.textContent = 'AI 正在核验…';
    agentBox.style.display = 'block';
    agentSteps.innerHTML = '<div class="agent-step"><span class="dot">…</span><span>正在读取物品与申请</span></div>';
    agentVerdict.innerHTML = '';
    try{
      await runAgentReview(c.itemId, c.id, agentSteps, agentVerdict);
      this.textContent = '重新核验';
    }catch(e){
      agentSteps.innerHTML = '<div class="agent-step">核验失败：' + esc((e && e.message) || '网络问题') + '</div>';
      this.textContent = '重试';
    }finally{
      this.disabled = false;
    }
  };

  document.getElementById('csAccept').onclick = function(){
    Net.claimAction(id, {status:'accepted'}).then(function(){
      sheet.classList.remove('show');
      renderClaims(); netSync();
      toast('已通过，双方现在可以看到联系方式');
    }).catch(function(){ toast('操作失败，稍后再试'); });
  };
  document.getElementById('csNeedMore').onclick = function(){
    Net.claimAction(id, {status:'need_more'}).then(function(){
      sheet.classList.remove('show');
      renderClaims();
      toast('已通知对方补充信息');
    }).catch(function(){ toast('操作失败，稍后再试'); });
  };
  document.getElementById('csReject').onclick = function(){
    Net.claimAction(id, {status:'rejected'}).then(function(){
      sheet.classList.remove('show');
      renderClaims();
      toast('已标记「不是这个物品」，对方可以补充后再申请');
    }).catch(function(){ toast('操作失败，稍后再试'); });
  };
  document.getElementById('csClose').onclick = function(){ sheet.classList.remove('show'); };
}

const AGENT_LABELS = {
  get_item: '读取物品与独有特征',
  get_claim: '读取申请内容与补充记录',
  check_reports: '查询举报记录',
  policy_check: '检查平台规则',
  search_similar: '检索库内相似物品'
};

async function runAgentReview(itemId, claimId, stepsEl, verdictEl){
  const resp = await fetch(API_BASE + '/agent/review', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Owner': myId()},
    body: JSON.stringify({itemId: itemId, claimId: claimId})
  });
  let obj = null;
  try{ obj = await resp.json(); }catch(e){ obj = null; }
  if(!resp.ok || !obj || obj.error){
    throw new Error((obj && obj.error) || '核验失败');
  }
  stepsEl.innerHTML = '';
  const steps = obj.steps || [];
  for(let i = 0; i < steps.length; i++){
    const st = steps[i];
    const div = document.createElement('div');
    div.className = 'agent-step';
    div.innerHTML = '<span class="dot">✓</span><span>' + esc(AGENT_LABELS[st.tool] || st.tool) + '</span>';
    stepsEl.appendChild(div);
    await new Promise(function(res){ setTimeout(res, 180); });
  }
  const map = {
    accept: ['v-ok', '建议通过'],
    need_more: ['v-more', '建议请对方补充'],
    reject: ['v-no', '建议拒绝']
  };
  const m = map[obj.decision] || ['', '建议人工判断'];
  let html = '<span class="' + m[0] + '">' + m[1] + '</span>' +
    '（置信度 ' + Math.round((obj.confidence || 0) * 100) + '%）<br>' + esc(obj.reason || '');
  if(obj.missing && obj.missing.length){
    html += '<br><span style="color:var(--sub)">还需要：' + obj.missing.map(esc).join('、') + '</span>';
  }
  verdictEl.innerHTML = html;
}

function updateBell(n){
  const dot = document.getElementById('bellDot');
  if(!dot) return;
  if(n > 0){ dot.style.display = 'block'; dot.textContent = n > 9 ? '9+' : String(n); }
  else { dot.style.display = 'none'; }
}

async function renderNotices(){
  if(!API_BASE) return;
  try{
    const r = await Net.notices();
    updateBell(r.unread || 0);
    const wrap = document.getElementById('noticesWrap');
    if(!r.items.length){ wrap.innerHTML = '<div class="empty">还没有通知</div>'; return; }
    wrap.innerHTML = r.items.map(function(n){
      const t = {match:'🔍 相似物品提醒', claim:'📥 收到认领申请', accepted:'✅ 申请已通过',
                 rejected:'❌ 申请被拒', done:'🎉 已完成归还'}[n.type] || '通知';
      return '<div class="mini" data-notice-item="' + esc(n.itemId || '') + '"' +
        ' data-notice-claim="' + esc(n.claimId || '') + '"' +
        ' data-notice-type="' + esc(n.type || '') + '">' +
        '<div class="mh">' + t + '</div>' +
        '<div class="mmeta">' + esc(n.text || '') + '</div>' +
        (n.type === 'claim' && n.claimId ? '<div class="mmeta" style="color:var(--purple)">点这里查看对方填了什么，与自己那条对比 →</div>' : '') +
        '<div class="mmeta">' + fmtTime(n.at) + '</div></div>';
    }).join('');
  }catch(e){}
}

/* ============ 搜索 ============ */
function allItems(){
  return Store.list({statuses:['approved','claimed','closed']});
}
function doSearch(q){
  q = (q||'').trim();
  const r = Store.list({q: q, statuses:['approved','claimed','closed']});
  showResults(r, q ? ('“'+q+'”的搜索结果') : '全部物品');
}
function showResults(arr, title){
  document.getElementById('searchResultTitle').style.display = 'block';
  document.getElementById('searchResultTitle').textContent = title+'（'+arr.length+'）';
  const w = document.getElementById('searchResult');
  w.innerHTML = arr.map(it=>itemHTML(it, it.type==='lost' ? '寻物' : (it.type==='found' ? '招领' : '物品'))).join('') ||
    '<div class="empty">没有匹配的物品</div>';
}
function renderImgSearch(){
  const g=document.getElementById('imgSearchGrid');
  const keys=Object.keys(CAT);
  g.innerHTML = keys.map(k=>{
    const m=CAT[k];
    return '<div class="ic" data-cat="'+k+'"><div class="em">'+m.e+'</div><div class="lb">'+m.l+'</div></div>';
  }).join('');
}

/* ============ 事件绑定 ============ */
document.addEventListener('click', e=>{
  const b=e.target.closest('[data-back]'); if(b){ back(); return; }
  const nav=e.target.closest('[data-nav]');
  const hcat=e.target.closest('[data-help-cat]');
  if(hcat){ openHelp(hcat.getAttribute('data-help-cat')); return; }
  if(nav){ const t=nav.getAttribute('data-nav');
    if(t==='lost'){renderLost();show('lost');return;}
    if(t==='found'){renderFound();show('found');return;}
    if(t==='lend'){document.querySelectorAll('#lendTabs span').forEach(s=>s.classList.toggle('on',s.dataset.tab==='lend'));renderLend('lend');show('lend');return;}
    if(t==='borrow'){document.querySelectorAll('#borrowTabs span').forEach(s=>s.classList.toggle('on',s.dataset.tab==='borrow'));renderBorrow('borrow');show('borrow');return;}
    if(t==='map'){show('map');return;}
    if(t==='faqList'){show('faqList');return;}
    if(t==='about'){show('about');return;}
    if(t==='contact'){show('contact');return;}
    if(t==='legal'){show('legal');return;}
    if(t==='privacy'){show('privacy');return;}
    if(t==='mine'){renderMine();show('mine');return;}
    show(t); return;
  }
  const mem=e.target.closest('[data-mem]');
  if(mem){ renderMemorialDetail(parseInt(mem.getAttribute('data-mem'),10)); show('memorial'); return; }
  const item=e.target.closest('[data-item]');
  if(item && !e.target.closest('[data-act]')){ openItem(item.getAttribute('data-item')); return; }
  const act=e.target.closest('[data-act]');
  if(act){
    e.stopPropagation();
    const card = act.closest('[data-item]');
    if(!card){ toast('请先打开这条详情'); return; }
    openItem(card.getAttribute('data-item'));
    const realBtn = document.getElementById('isAction');
    if(realBtn && !realBtn.disabled && realBtn.style.display !== 'none') realBtn.click();
    return;
  }
  const pub=e.target.closest('[data-publish]'); if(pub){ openPublish(pub.getAttribute('data-publish')); return; }
  const demo=e.target.closest('[data-demo]');
  if(demo){ toast('演示版：发布功能需在完整后台版本使用'); return; }
  const tab=e.target.closest('.tabs span');
  if(tab){ const tb=tab.parentElement; tb.querySelectorAll('span').forEach(s=>s.classList.remove('on')); tab.classList.add('on');
    if(tb.id==='lendTabs') renderLend(tab.dataset.tab); if(tb.id==='borrowTabs') renderBorrow(tab.dataset.tab); return; }
  const ed = e.target.closest('[data-edit]');
  if(ed){ openEdit(ed.getAttribute('data-edit')); return; }
  const md = e.target.closest('[data-mine-del]');
  if(md){
    if(md.getAttribute('data-confirm') === '1'){
      applyRemove(md.getAttribute('data-mine-del'));
      toast('已撤回并删除');
    } else {
      md.setAttribute('data-confirm','1');
      md.textContent = '确定删除？再点一次';
    }
    return;
  }
  if(e.target.closest('#searchEntry')){ show('search'); return; }
  if(e.target.closest('#bellBtn')){ renderNotices(); show('notices'); return; }
  if(e.target.closest('#readAll')){ Net.readNotices().then(function(){ updateBell(0); renderNotices(); }); return; }
  const nitem = e.target.closest('[data-notice-item]');
  if(nitem){
    const iid = nitem.getAttribute('data-notice-item');
    const cid = nitem.getAttribute('data-notice-claim');
    const ntype = nitem.getAttribute('data-notice-type');
    if(ntype === 'claim' && cid){ openClaimById(cid); return; }
    if(iid){ document.getElementById('itemSheet').classList.remove('show'); openItem(iid); }
    return;
  }
  const cv = e.target.closest('[data-claim-view]');
  if(cv){ openClaimReview(cv.getAttribute('data-claim-view')); return; }
  const sc = e.target.closest('[data-claim-supplement]');
  if(sc){
    const box = document.getElementById('sup_' + sc.getAttribute('data-claim-supplement'));
    if(box) box.style.display = (box.style.display === 'none' || !box.style.display) ? 'block' : 'none';
    return;
  }
  const sco = e.target.closest('[data-claim-supplement-ok]');
  if(sco){
    const cid = sco.getAttribute('data-claim-supplement-ok');
    const ta = document.getElementById('supt_' + cid);
    const msg = (ta && ta.value || '').trim();
    if(msg.length < 2){ toast('写点补充内容，比如颜色、划痕位置'); return; }
    sco.disabled = true;
    Net.supplement(cid, {message: msg}).then(function(){
      renderClaims();
      toast('已补充，对方会再核对一次');
    }).catch(function(){ toast('提交失败，稍后再试'); });
    return;
  }
  const ca = e.target.closest('[data-claim-accept]');
  if(ca){
    Net.claimAction(ca.getAttribute('data-claim-accept'), {status:'accepted'}).then(function(){
      renderClaims(); netSync(); toast('已通过，对方能看到你的联系方式');
    }).catch(function(){ toast('操作失败，稍后再试'); });
    return;
  }
  const cr = e.target.closest('[data-claim-reject]');
  if(cr){
    Net.claimAction(cr.getAttribute('data-claim-reject'), {status:'rejected'}).then(function(){
      renderClaims(); toast('已拒绝');
    }).catch(function(){ toast('操作失败，稍后再试'); });
    return;
  }
  const cd = e.target.closest('[data-claim-done]');
  if(cd){
    Net.complete(cd.getAttribute('data-claim-done')).then(function(){
      renderClaims(); netSync(); toast('已标记完成归还');
    }).catch(function(){ toast('操作失败，稍后再试'); });
    return;
  }
  const retBtn = e.target.closest('[data-claim-return]');
  if(retBtn){
    const id = retBtn.getAttribute('data-claim-return');
    const inp = document.getElementById('rc_' + id);
    const code = inp ? inp.value.trim() : '';
    if(!/^\d{6}$/.test(code)){ toast('请输入 6 位取件码'); return; }
    retBtn.disabled = true;
    Net.complete(id, code).then(function(){
      const c = claimsMap[id] || {};
      renderClaims(); netSync();
      showCertificate({title: c.itemTitle, code: code, createdAt: c.createdAt, completedAt: Date.now()});
    }).catch(function(err){
      retBtn.disabled = false;
      toast((err && err.message) || '取件码不对，让对方再看一眼');
    });
    return;
  }
  if(e.target.closest('#loginBtn')){ renderMine(); show('mine'); return; }
  if(e.target.closest('#searchBtn')){ doSearch(document.getElementById('searchInput').value); return; }
  if(e.target.closest('#imgSearchBtn')){ const g=document.getElementById('imgSearchGrid'); const h=document.getElementById('imgHint');
    g.style.display = g.style.display==='none'?'grid':'none'; h.style.display=g.style.display==='grid'?'block':'none'; return; }
  const ic=e.target.closest('.imgsearch-grid .ic');
  if(ic){ const k=ic.getAttribute('data-cat'); const r=allItems().filter(it=>it.cat===k);
    showResults(r, '以图搜图 · 「'+catInfo(k).l+'」相似匹配（'+r.length+'）'); return; }
  if(e.target.hasAttribute('data-close-sheet')||e.target.closest('[data-close-sheet]')){ document.getElementById('itemSheet').classList.remove('show'); return; }
});
document.getElementById('searchInput').addEventListener('input', e=>doSearch(e.target.value));
document.getElementById('claimCancel').onclick = function(){
  const box = document.getElementById('claimBox');
  if(box) box.style.display = 'none';
  const b = document.getElementById('isAction');
  if(b){ b.style.display = 'block'; b.disabled = false; }
};
document.getElementById('recoverLink').onclick = function(){
  recoverStage = 'input';
  recoverPhoneCache = '';
  document.getElementById('recoverGo').textContent = '查找';
  document.getElementById('recoverDialog').classList.add('show');
  document.getElementById('recoverResult').style.display = 'none';
  document.getElementById('recoverPhone').value = '';
};
document.getElementById('recoverCancel').onclick = function(){
  document.getElementById('recoverDialog').classList.remove('show');
};
let recoverStage = 'input';
let recoverPhoneCache = '';
document.getElementById('recoverGo').onclick = async function(){
  const phone = document.getElementById('recoverPhone').value.trim();
  const out = document.getElementById('recoverResult');
  const btn = this;
  if(phone.length < 5){ out.style.display = 'block'; out.textContent = '请输入完整的手机号'; return; }
  btn.disabled = true; btn.textContent = '处理中…';
  try{
    if(recoverStage === 'input'){
      const r = await Net.recover({phone: phone});
      if(!r.count){
        out.style.display = 'block';
        out.textContent = '没找到用这个手机号发布的记录，确认一下号码是否一致。';
        return;
      }
      recoverPhoneCache = phone;
      recoverStage = 'confirm';
      out.style.display = 'block';
      out.innerHTML = '找到 <b>' + r.count + '</b> 条：' + esc((r.titles || []).join('、')) +
        '<br><br>确认要归到这台设备吗？';
      btn.textContent = '确认找回这 ' + r.count + ' 条';
    } else {
      const r2 = await Net.recover({phone: recoverPhoneCache, confirm: true});
      out.style.display = 'block';
      out.textContent = '已找回 ' + r2.count + ' 条，正在刷新…';
      await netSync(); renderMine(); renderClaims();
      setTimeout(function(){
        document.getElementById('recoverDialog').classList.remove('show');
        toast('已找回 ' + r2.count + ' 条发布');
      }, 900);
      recoverStage = 'input';
      btn.textContent = '查找';
    }
  }catch(e){
    out.style.display = 'block';
    out.textContent = (e && e.message) || '查找失败，请稍后再试';
  }finally{
    btn.disabled = false;
    if(recoverStage === 'input'){ btn.textContent = '查找'; }
  }
};
document.getElementById('claimSend').onclick = function(){
  const msg = document.getElementById('claimMsg').value.trim();
  const phone = document.getElementById('claimPhone').value.trim();
  if(msg.length < 2){ toast('写点细节，方便对方核对'); return; }
  if(phone){
    const pchk = phoneCheckLocal(phone);
    if(pchk.status === 'red'){ toast('电话号码不正确：' + pchk.reason); return; }
  }
  if(!currentSheetId) return;
  const btn = this;
  btn.disabled = true; btn.textContent = '发送中…';
  const isSupplement = (currentClaimMode === 'supplement' && currentClaimId);
  const req = isSupplement
    ? Net.supplement(currentClaimId, {message: msg})
    : Net.claim(currentSheetId, {message: msg, contact: phone});
  req.then(function(){
    toast(isSupplement ? '已补充，对方会再核对一次' : (currentClaimKind === 'found' ? '已发送给失主，等待确认' : '已发送申请，对方确认后会通知你'));
    document.getElementById('claimBox').style.display = 'none';
    document.getElementById('itemSheet').classList.remove('show');
    renderClaims();
    netSync();
  }).catch(function(e){
    toast((e && e.message) || '发送失败，请稍后重试');
  }).finally(function(){
    btn.disabled = false;
    btn.textContent = isSupplement ? '提交补充' : (currentClaimKind === 'found' ? '发送给失主' : '发送认领申请');
  });
};
document.querySelector('[data-close-sheet]').onclick=()=>document.getElementById('itemSheet').classList.remove('show');

/* ============ 发布启事（v3.0） ============ */
let pendingPhoto = null;
let pendingFields = null;
let phoneManualRequest = false;
let pendingSummary = '';
let photoBusy = false;
let photoSeq = 0;

const CAT2NAME = {card:'证件', electronics:'电子设备', cloth:'衣物', cup:'水杯', bag:'书包', other:'其他'};
let editingItem = null;

function setPubType(type){
  const lost = type !== 'found';
  document.getElementById('pubTabLost').classList.toggle('active', lost);
  document.getElementById('pubTabFind').classList.toggle('active', !lost);
  document.getElementById('placeLabel').textContent = lost ? '丢失地点' : '捡到地点';
  document.getElementById('timeLabel').textContent  = lost ? '丢失时间' : '捡到时间';
}
function resetPublishForm(){
  const f = document.getElementById('publishForm');
  if(f) f.reset();
  pendingPhoto = null;
  photoSeq++;
  photoBusy = false;
  document.getElementById('photoPreview').innerHTML = '';
  document.getElementById('descCount').textContent = '0';
  document.getElementById('editNote').style.display = 'none';
}
function openPublish(type){
  editingItem = null;
  retypeOldId = null;
  resetPublishForm();
  setPubType(type);
  clearFormErrors();
  if(stack[stack.length-1] === 'success') stack.pop();
  show('publish');
}
function openEdit(id){
  const it = Store.get(id);
  if(!it) return;
  editingItem = it;
  setPubType(it.type);
  const f = document.getElementById('publishForm');
  f.elements['goodsName'].value = it.title || '';
  f.elements['category'].value = CAT2NAME[it.cat] || '其他';
  f.elements['place'].value = (it.place === '未填写地点' ? '' : (it.place || ''));
  f.elements['eventTime'].value = it.eventTime || '';
  f.elements['desc'].value = it.desc || '';
  f.elements['secret'].value = it.secret || '';
  f.elements['phone'].value = (it.contact && it.contact.phone) || '';
  pendingPhoto = it.photo || null;
  photoSeq++;
  photoBusy = false;
  document.getElementById('photoInput').value = '';
  document.getElementById('photoPreview').innerHTML = pendingPhoto
    ? '<img src="'+esc(pendingPhoto)+'" alt="预览" style="width:100%;max-height:170px;object-fit:cover;border-radius:10px;margin-top:8px">'
    : '';
  document.getElementById('descCount').textContent = String((it.desc || '').length);
  document.getElementById('editNote').style.display = 'block';
  clearFormErrors();
  show('publish');
}
function setErr(field, msg){
  const box = document.querySelector('#publishForm .form-item[data-field="'+field+'"]');
  if(!box) return;
  box.classList.add('err');
  const e = box.querySelector('.errmsg');
  if(e) e.textContent = msg;
}
function clearFormErrors(){
  document.querySelectorAll('#publishForm .form-item.err').forEach(function(el){
    el.classList.remove('err');
    const e = el.querySelector('.errmsg');
    if(e) e.textContent = '';
  });
}
function focusFirstErr(){
  const box = document.querySelector('#publishForm .form-item.err');
  if(!box) return;
  const ctl = box.querySelector('input,select,textarea');
  if(ctl){ try{ ctl.focus({preventScroll:true}); }catch(e){ try{ ctl.focus(); }catch(e2){} } }
  try{ box.scrollIntoView({block:'center', behavior:'smooth'}); }catch(e){}
}

function compressImage(file){
  return new Promise(function(resolve, reject){
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = function(){
      try{
        const max = 640;
        let w = img.width, h = img.height;
        if(w > max || h > max){ const r = Math.min(max/w, max/h); w = Math.round(w*r); h = Math.round(h*r); }
        const cv = document.createElement('canvas');
        cv.width = w; cv.height = h;
        cv.getContext('2d').drawImage(img, 0, 0, w, h);
        const data = cv.toDataURL('image/jpeg', 0.62);
        URL.revokeObjectURL(url);
        resolve(data);
      }catch(err){ URL.revokeObjectURL(url); reject(err); }
    };
    img.onerror = function(){ URL.revokeObjectURL(url); reject(new Error('image load failed')); };
    img.src = url;
  });
}
function guessCategory(text){
  const t = String(text || '');
  if(/包|书包|背包|箱/.test(t)) return '书包';
  if(/卡|证|身份证|学生证/.test(t)) return '证件';
  if(/耳机|手机|电脑|电子|充电|相机|键盘|鼠标/.test(t)) return '电子设备';
  if(/衣|外套|帽子|围巾|手套|鞋/.test(t)) return '衣物';
  if(/杯|水壶|保温/.test(t)) return '水杯';
  return '其他';
}

document.getElementById('photoInput').onchange = function(){
  const f = this.files && this.files[0];
  const box = document.getElementById('photoPreview');
  pendingPhoto = null; box.innerHTML = '';
  if(!f) return;
  const seq = ++photoSeq;
  photoBusy = true;
  box.innerHTML = '<div class="tip-small">图片处理中…</div>';
  compressImage(f).then(function(d){
    if(seq !== photoSeq) return;
    photoBusy = false;
    pendingPhoto = d;
    box.innerHTML = '<img src="'+d+'" alt="预览" style="width:100%;max-height:170px;object-fit:cover;border-radius:10px;margin-top:8px">';
    if(API_BASE){
      const hint = document.createElement('div');
      hint.className = 'tip-small';
      hint.id = 'visionHint';
      hint.textContent = 'AI 正在识别图片…';
      box.appendChild(hint);
      const raw = String(d).split(',')[1] || '';
      aiBusy(true, 'AI 正在识别图片，请稍候…');
      Net.vision(raw, 'image/jpeg').then(function(r){
        aiBusy(false);
        if(seq !== photoSeq) return;
        const h = document.getElementById('visionHint');
        if(!r || !r.ok){
          if(h) h.textContent = (r && r.reason) ? ('AI 识别暂不可用：' + r.reason) : 'AI 识别暂不可用，可手动填写分类和描述';
          return;
        }
        const cat = guessCategory((r.category || '') + ' ' + (r.desc || ''));
        const sel = document.querySelector('#publishForm select[name="category"]');
        if(sel && !sel.value) sel.value = cat;
        const ta = document.querySelector('#publishForm textarea[name="desc"]');
        if(ta && ta.value.trim().length < 5 && r.desc){
          const base = String(r.desc).replace(/[。.!！]+$/, '');
          const color = (r.color && base.indexOf(r.color) < 0) ? ('，' + r.color) : '';
          ta.value = base + color;
          ta.dispatchEvent(new Event('input'));
        }
        if(h){
          h.textContent = 'AI 识别：' + [r.color, r.category, r.features].filter(Boolean).join(' · ') + '（可修改）';
        }
      }).catch(function(){
        aiBusy(false);
        const h = document.getElementById('visionHint');
        if(h) h.textContent = 'AI 识别失败，可手动填写分类和描述';
      });
    }
  }).catch(function(){
    if(seq !== photoSeq) return;
    photoBusy = false;
    box.innerHTML = '';
    toast('图片读取失败，可以不带图继续发布');
  });
};
document.getElementById('pubTabLost').onclick = function(){ setPubType('lost'); };
document.getElementById('pubTabFind').onclick = function(){ setPubType('found'); };

document.querySelector('#publishForm textarea[name="desc"]').addEventListener('input', function(e){
  const n = this.value.length;
  document.getElementById('descCount').textContent = n;
  const warn = document.getElementById('descWarn');
  if(warn) warn.style.display = n > 150 ? 'block' : 'none';
  if(e && e.isTrusted){
    pendingFields = null;
    pendingSummary = '';
  }
});

/* ===== 图片放大查看 ===== */
function openImageViewer(src){
  const v = document.getElementById('imgViewer');
  const img = document.getElementById('imgViewerImg');
  if(!v || !img || !src) return;
  img.src = src;
  v.classList.add('show');
  activeLayer = closeImageViewer;
}
function closeImageViewer(){
  const v = document.getElementById('imgViewer');
  if(v) v.classList.remove('show');
  if(activeLayer === closeImageViewer) activeLayer = null;
}
document.addEventListener('click', function(e){
  const img = e.target.closest('#isThumb img, .item .thumb img, #photoPreview img');
  if(img && img.src){
    e.preventDefault();
    e.stopPropagation();
    openImageViewer(img.src);
  }
}, true);
document.addEventListener('DOMContentLoaded', function(){
  const v = document.getElementById('imgViewer');
  if(v) v.addEventListener('click', closeImageViewer);
});
document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeImageViewer(); });

/* ===== AI 信息整理 ===== */
async function runAiFormat(){
  const f = document.getElementById('publishForm');
  const title = (f.elements['goodsName'].value || '').trim();
  const desc = (f.elements['desc'].value || '').trim();
  const panel = document.getElementById('aiFormatPanel');
  if(desc.length < 5){ toast('先写一点描述，AI 才好整理'); return; }
  panel.style.display = 'block';
  document.getElementById('afSummary').textContent = '正在整理…';
  document.getElementById('afDesc').textContent = '';
  document.getElementById('afLen').textContent = '';
  document.getElementById('afTags').innerHTML = '';
  try{
    const r = await Net.format({title: title, desc: desc, category: f.elements['category'].value || ''});
    pendingFields = r.fields || {};
    pendingSummary = r.summary || '';
    document.getElementById('afLen').textContent =
      '（' + (r.originalLen || desc.length) + ' 字 → ' + String(r.desc || '').length + ' 字）';
    document.getElementById('afSummary').textContent = r.summary || '';
    document.getElementById('afDesc').textContent = r.desc || '';
    const tags = Object.keys(r.fields || {}).map(function(k){ return r.fields[k]; }).filter(Boolean).slice(0, 4);
    document.getElementById('afTags').innerHTML = tags.map(function(t){
      return '<span class="af-tag">' + esc(t) + '</span>';
    }).join('');
  }catch(e){
    panel.style.display = 'none';
    toast((e && e.message) || 'AI 整理失败，可以直接提交');
  }
}

document.getElementById('aiFormatBtn').onclick = runAiFormat;
document.getElementById('afAgain').onclick = runAiFormat;
document.getElementById('afClose').onclick = function(){
  document.getElementById('aiFormatPanel').style.display = 'none';
};
document.getElementById('afUse').onclick = function(){
  const desc = (document.getElementById('afDesc').textContent || '').trim();
  if(desc){
    const ta = document.querySelector('#publishForm textarea[name="desc"]');
    ta.value = desc;
    document.getElementById('descCount').textContent = desc.length;
  }
  document.getElementById('aiFormatPanel').style.display = 'none';
  toast('已使用 AI 整理版本');
};
document.querySelector('#publishForm textarea[name="desc"]').addEventListener('blur', function(){
  const panel = document.getElementById('aiFormatPanel');
  if(this.value.trim().length > 60 && panel && panel.style.display === 'none'){
    runAiFormat();
  }
});

/* ===== 拍照即发布 ===== */
function resetPublishForm(){
  const f = document.getElementById('publishForm');
  if(!f) return;
  f.reset();
  pendingPhoto = null; pendingFields = null; pendingSummary = '';
  phoneManualRequest = false;
  const pp = document.getElementById('photoPreview'); if(pp) pp.innerHTML = '';
  const pi = document.getElementById('photoInput'); if(pi) pi.value = '';
  const dc = document.getElementById('descCount'); if(dc) dc.textContent = '0';
  const ap = document.getElementById('aiFormatPanel'); if(ap) ap.style.display = 'none';
  const ph = document.getElementById('phoneHint'); if(ph) ph.textContent = '';
  const cw = document.getElementById('phoneConfirmWrap'); if(cw) cw.style.display = 'none';
  photoSeq++; photoBusy = false;
  clearFormErrors();
}

document.getElementById('quickPhotoBtn').onclick = function(){
  document.getElementById('quickPhotoInput').click();
};

document.getElementById('quickPhotoInput').onchange = async function(){
  const file = this.files && this.files[0];
  this.value = '';
  if(!file) return;
  resetPublishForm();
  show('publish');
  document.getElementById('pubTabFind').click();
  toast('照片处理中…');
  let data = null;
  try{ data = await compressImage(file); }catch(e){ data = null; }
  if(!data){ toast('图片读取失败，可以手动填写'); return; }
  pendingPhoto = data;
  document.getElementById('photoPreview').innerHTML =
    '<img src="' + data + '" alt="预览" style="width:100%;max-height:170px;object-fit:cover;border-radius:10px;margin-top:8px">';
  aiBusy(true, 'AI 正在识别图片，请稍候…');
  try{
    const raw = String(data).split(',')[1] || '';
    const r = await Net.vision(raw, 'image/jpeg');
    const f = document.getElementById('publishForm');
    if(r && r.ok){
      const color = r.color || '';
      const catName = r.category || '';
      const title = (color + catName).slice(0, 30);
      if(title) f.elements['goodsName'].value = title;
      let desc = String(r.desc || '').replace(/[。.!！]+$/, '');
      if(color && desc.indexOf(color) < 0) desc = color + '，' + desc;
      if(desc) f.elements['desc'].value = desc;
      f.elements['category'].value = guessCategory(catName + ' ' + (r.desc || ''));
      document.getElementById('descCount').textContent = f.elements['desc'].value.length;
      toast('已根据照片填好，补个地点就能发');
    } else {
      toast('AI 没看清，照片已带上，手动补个名称');
    }
  }catch(e){
    toast('AI 识别失败，照片已带上，手动补个名称');
  }finally{
    aiBusy(false);
  }
};

document.getElementById('fillDemo').onclick = function(){
  const f = document.getElementById('publishForm');
  f.elements['goodsName'].value = '示例：黑色钥匙扣';
  f.elements['category'].value = '其他';
  f.elements['place'].value = '六教门口';
  f.elements['desc'].value = '黑色钥匙扣，挂着一个校徽挂件，落在六教门口，着急找回来。';
  f.elements['secret'].value = '钥匙上刻了名字缩写';
  f.elements['phone'].value = '13800001234';
  pendingPhoto = null;
  document.getElementById('photoPreview').innerHTML = '';
  document.getElementById('photoInput').value = '';
  photoSeq++;
  photoBusy = false;
  document.getElementById('descCount').textContent = f.elements['desc'].value.length;
  clearFormErrors();
  toast('示例已填好，直接点下面的提交按钮');
};

document.getElementById('okMine').onclick = function(){
  renderMine();
  if(stack[stack.length-1] === 'success') stack.pop();
  show('mine');
};

function wait(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }

async function showQueued(ticket){
  document.getElementById('okTitle').textContent = '已收下，正在排队审核';
  const note = document.getElementById('okNote');
  if(note) note.textContent = '现在同时发布的人有点多，系统按顺序审核。你可以留在这里，审完会自动更新。';
  const meta = document.getElementById('okMeta');
  const setMeta = function(pos, eta){
    meta.textContent = '前面还有 ' + (pos > 0 ? pos : 0) + ' 人 · 预计 ' + (eta || pos * 2 || 2) + ' 秒';
  };
  setMeta(ticket.position || 1, ticket.eta);
  const hint2 = document.getElementById('okTypeHint');
  if(hint2){ hint2.style.display = 'none'; hint2.innerHTML = ''; }
  if(stack[stack.length-1] === 'publish') stack.pop();
  show('success');
  const deadline = Date.now() + 45000;
  while(Date.now() < deadline){
    await wait(1500);
    try{
      const st = await Net.reviewStatus(ticket.id);
      if(st.queue === 'queued' || st.queue === 'reviewing') setMeta(st.position || 0, (st.position || 0) * 2);
      if(st.status && st.status !== 'pending' && st.item){ showSuccess(st.item); return; }
    }catch(e){}
  }
  meta.textContent = '审核还在进行，完成后会在「我的发布」里显示';
}

function showSuccess(item, isEdit){
  const approved = item && item.status === 'approved';
  const rejected = item && item.status === 'rejected';
  let title;
  if(rejected){ title = isEdit ? '已重新提交，但被自动拦截' : '已提交，但被自动拦截'; }
  else if(approved){ title = isEdit ? '已重新发布成功' : '已发布成功'; }
  else { title = isEdit ? '已重新提交，等待审核' : '已提交，等待审核'; }
  document.getElementById('okTitle').textContent = title;
  const note = document.getElementById('okNote');
  if(note){
    if(item && item.typeAutoFixed && approved){
      note.textContent = 'AI 发现你写的内容更像「' + (item.type === 'lost' ? '寻物启事' : '招领启事') +
        '」，已经自动归到正确分类，其他同学现在就能看到。';
    }else{
      note.textContent = rejected
        ? '内容命中了违规检测，没有公开展示。可以在「我的发布」里看到原因，修改后重新提交。'
        : (approved
          ? '已经出现在「失物招领 / 寻物启事」列表里，其他同学现在就能看到。'
          : '审核通过后，其他同学才能在「失物招领 / 寻物启事」里看到这条信息。');
    }
  }
  document.getElementById('okMeta').textContent =
    (item.type === 'lost' ? '寻物启事' : '招领启事') + ' · 编号 ' + item.id + ' · ' + fmtTime(item.createdAt);
  const hint2 = document.getElementById('okTypeHint');
  if(hint2){ hint2.style.display = 'none'; hint2.innerHTML = ''; }
  if(stack[stack.length-1] === 'publish') stack.pop();
  show('success');
  burstConfetti();
  renderMine();
}

function retypeItem(it){
  const target = it.typeSuggestion;
  if(!target) return;
  openPublish(target);          /* 重置表单并切到正确类型 */
  const f = document.getElementById('publishForm');
  f.elements['goodsName'].value = it.title || '';
  f.elements['desc'].value = it.desc || '';
  f.elements['place'].value = (it.place === '未填写地点' ? '' : (it.place || ''));
  f.elements['secret'].value = it.secret || '';
  f.elements['phone'].value = (it.contact && it.contact.phone) || '';
  document.getElementById('descCount').textContent = String((it.desc || '').length);
  retypeOldId = it.id;
  toast('已按新类型填好，提交后旧的那条会自动删除');
}

document.getElementById('publishForm').onsubmit = async function(e){
  e.preventDefault();
  clearFormErrors();
  if(photoBusy){ toast('图片还在处理，等一两秒再提交'); return; }
  const fd = new FormData(this);
  const title = String(fd.get('goodsName')||'').trim();
  let desc  = String(fd.get('desc')||'').trim();
  const phone = String(fd.get('phone')||'').trim();
  let bad = 0;

  if(title.length < 2){ setErr('title', '请填写物品名称（2–30 个字）'); bad++; }
  else if(title.length > 30){ setErr('title', '名称不要超过 30 个字'); bad++; }
  if(desc.length < 5){ setErr('desc', '请描述一下物品特征（至少 5 个字），方便别人核对'); bad++; }
  else if(desc.length > 300){ setErr('desc', '描述不要超过 300 个字'); bad++; }
  if(phone && !/^[0-9+\-\s]{5,20}$/.test(phone)){ setErr('phone', '电话只支持数字、+、-，也可以留空'); bad++; }
  if(phone){
    const pchk = phoneCheckLocal(phone);
    if(pchk.status === 'red'){ setErr('phone', '电话号不正确：' + pchk.reason); bad++; }
    else if(pchk.status === 'yellow'){
      const cb = document.getElementById('phoneConfirm');
      if(!cb || !cb.checked){
        if(phoneManualRequest){
          /* 已申请人工确认，允许提交 */
        }else if(confirm('这个号码 ' + phone + ' 有连续重复，确认是你本人的常用号码吗？')){
          if(cb) cb.checked = true;
        } else {
          setErr('phone', '请先确认这个号码是你本人的，或点「申请人工确认」');
          bad++;
        }
      }
    }
  }

  if(bad){
    focusFirstErr();
    toast('还有 ' + bad + ' 项需要改一下');
    return;
  }

  // 强制走一遍模板整理，保证所有人看到的信息结构一致
  if(API_BASE && (!pendingSummary || !pendingFields || desc.length > 60)){
    try{
      const r = await Net.format({title: title, desc: desc, category: fd.get('category') || ''});
      if(r && r.desc){
        desc = r.desc;
        pendingSummary = r.summary || pendingSummary;
        pendingFields = r.fields || pendingFields;
        const ta = document.querySelector('#publishForm textarea[name="desc"]');
        if(ta){ ta.value = desc; document.getElementById('descCount').textContent = String(desc.length); }
      }
    }catch(e){ /* 整理失败就按原文提交，服务端还会补一次规则整理 */ }
  }

  const isLost = !document.getElementById('pubTabFind').classList.contains('active');
  const type = isLost ? 'lost' : 'found';
  const dup = Store.list({owner:myId(), status:'pending'}).some(function(x){
    return x.title === title && x.desc === desc;
  });
  if(dup){ toast('刚提交过一样的内容，已经在审核里了'); return; }

  const item = {
    id: 'p_' + Date.now().toString(36) + Math.random().toString(36).slice(2,6),
    type: type,
    cat: catKey(fd.get('category') || '其他'),
    title: title,
    desc: desc,
    place: String(fd.get('place')||'').trim() || '未填写地点',
    eventTime: fd.get('eventTime') || '',
    secret: String(fd.get('secret')||'').trim(),
    photo: pendingPhoto,
    fields: pendingFields || null,
    summary: pendingSummary || '',
    phoneConfirmed: !!(document.getElementById('phoneConfirm') || {}).checked,
    phoneReviewRequested: !!phoneManualRequest,
    contact: { phone: phone },
    status: API_BASE ? 'pending' : 'approved',
    rejectReason: '',
    ownerId: myId(),
    createdAt: Date.now(),
    updatedAt: Date.now(),
    reviewedBy: '',
    reviewedAt: 0
  };

  const editing = editingItem;

  if(editing){
    const patch = {
      title: item.title, desc: item.desc,
      place: item.place, cat: item.cat, category: item.cat,
      eventTime: item.eventTime, secret: item.secret,
      photo: item.photo, contact: item.contact, phone: item.contact.phone,
      status: API_BASE ? 'pending' : 'approved', rejectReason: ''
    };
    let updated = null;
    if(API_BASE){
      try{
        await Net.update(editing.id, patch);
        await netSync();
        updated = Store.get(editing.id) || Object.assign({}, editing, patch);
      }catch(err){
        toast('没连上共享服务器，修改没有保存');
        return;
      }
    } else {
      updated = Store.update(editing.id, patch);
    }
    editingItem = null;
    this.reset();
    pendingPhoto = null;
    photoSeq++;
    document.getElementById('photoPreview').innerHTML = '';
    document.getElementById('descCount').textContent = '0';
    document.getElementById('editNote').style.display = 'none';
    showSuccess(updated || editing, true);
    return;
  }

  if(API_BASE){
    const btn = document.getElementById('submitBtn');
    if(btn){ btn.disabled = true; btn.textContent = 'AI 审核中，请稍等…'; }
    let pre = null;
    try{
      pre = await Net.precheck(item);
    }catch(err){
      if(btn){ btn.disabled = false; btn.textContent = '提交发布（提交后进入审核）'; }
      toast((err && err.message) || '审核服务暂时不可用，请稍后再试');
      return;
    }
    if(btn){ btn.disabled = false; btn.textContent = '提交发布（提交后进入审核）'; }
    if(pre && pre.suggestion){
      pendingPublish = {item: item, checkId: pre.checkId, form: this};
      showTypeDialog(pre.suggestion, item.type);
      return;
    }
    await finishSubmit(item, pre ? pre.checkId : '', this);
    return;
  }
  await finishSubmit(item, '', this);
};

let pendingPublish = null;

function showTypeDialog(suggestion, currentType){
  const want = suggestion === 'lost' ? '寻物启事' : '招领启事';
  const now = currentType === 'lost' ? '寻物启事' : '招领启事';
  const box = document.getElementById('typeDialog');
  document.getElementById('tdText').innerHTML =
    'AI 已经看完这条内容：你选的是「' + now + '」，但根据文字看，它更像是「' + want + '」。<br>要不要改一下？';
  document.getElementById('tdChange').textContent = '改成「' + want + '」';
  box.classList.add('show');
  document.getElementById('tdChange').onclick = function(){
    box.classList.remove('show');
    if(!pendingPublish) return;
    const it = pendingPublish.item;
    pendingPublish = null;
    openPublish(suggestion);
    const f = document.getElementById('publishForm');
    f.elements['goodsName'].value = it.title || '';
    f.elements['desc'].value = it.desc || '';
    f.elements['place'].value = (it.place === '未填写地点' ? '' : (it.place || ''));
    f.elements['secret'].value = it.secret || '';
    f.elements['phone'].value = (it.contact && it.contact.phone) || '';
    document.getElementById('descCount').textContent = String((it.desc || '').length);
    toast('已切到「' + want + '」，确认后再提交');
  };
  document.getElementById('tdContinue').onclick = function(){
    box.classList.remove('show');
    if(!pendingPublish) return;
    const p = pendingPublish; pendingPublish = null;
    finishSubmit(p.item, p.checkId, p.form);
  };
  document.getElementById('tdBack').onclick = function(){
    box.classList.remove('show');
    pendingPublish = null;
    toast('已返回，可以继续修改');
  };
}

async function finishSubmit(item, checkId, form){
  let saved = Store.add(item);
  if(!saved){ toast('保存失败，请再点一次提交'); return; }
  if(API_BASE){
    const btn = document.getElementById('submitBtn');
    if(btn){ btn.disabled = true; btn.textContent = '发布中…'; }
    try{
      const fromServer = await Net.create(Object.assign({}, item, {checkId: checkId || ''}));
      if(fromServer && fromServer.queued){
        if(btn){ btn.disabled = false; btn.textContent = '提交发布（提交后进入审核）'; }
        if(retypeOldId){ Net.remove(retypeOldId).catch(function(){}); retypeOldId = null; }
        if(form) form.reset();
        pendingPhoto = null;
        document.getElementById('photoPreview').innerHTML = '';
        document.getElementById('descCount').textContent = '0';
        Store.remove(item.id);
        netSync().catch(function(){});
        showQueued(fromServer);
        return;
      }
      if(fromServer && fromServer.id) saved = fromServer;
      await netSync();
    }catch(err){
      if(btn){ btn.disabled = false; btn.textContent = '提交发布（提交后进入审核）'; }
      toast((err && err.message) || '发布失败，请稍后再试');
      return;
    }
    if(btn){ btn.disabled = false; btn.textContent = '提交发布（提交后进入审核）'; }
  }
  if(retypeOldId){ Net.remove(retypeOldId).catch(function(){}); retypeOldId = null; }
  if(form) form.reset();
  pendingPhoto = null;
  document.getElementById('photoPreview').innerHTML = '';
  document.getElementById('descCount').textContent = '0';
  showSuccess(saved);
}

/* ============ 校园问答（RAG） ============ */
const ASK_EXAMPLES = ['校园卡丢了怎么办', '捡到东西应该交到哪里', '怎么认领我丢的东西', '交接时要注意什么'];

function renderAskChips(){
  const box = document.getElementById('askChips');
  if(!box) return;
  box.innerHTML = ASK_EXAMPLES.map(function(q){
    return '<span class="ask-chip" data-ask="' + esc(q) + '">' + esc(q) + '</span>';
  }).join('');
}

function formatAnswer(t){
  return esc(String(t || '')).replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
}

async function askQuestion(q){
  const answer = document.getElementById('askAnswer');
  const sources = document.getElementById('askSources');
  const btn = document.getElementById('askBtn');
  if(!q){ toast('先输入一个问题'); return; }
  if(!API_BASE){ toast('本机模式暂不支持问答'); return; }
  answer.innerHTML = '<div class="ask-card"><div class="ask-a">正在检索校园知识库…</div></div>';
  sources.innerHTML = '';
  if(btn){ btn.disabled = true; btn.textContent = '…'; }
  try{
    const r = await fetch(API_BASE + '/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: q})
    }).then(function(x){ return x.json(); });
    if(!r || !r.ok) throw new Error((r && r.error) || '问答服务暂时不可用');
    answer.innerHTML = '<div class="ask-card">' +
      '<div class="ask-q">你问：' + esc(q) + '</div>' +
      '<div class="ask-a">' + formatAnswer(r.answer) + '</div></div>';
    if(r.sources && r.sources.length){
      sources.innerHTML = '<div class="ask-card"><div class="ask-q">参考来源</div>' +
        r.sources.map(function(s, i){
          return '<div class="ask-src-item">[' + (i + 1) + '] ' + esc(s.title || '') + '：' +
            esc(String(s.text || '').slice(0, 60)) + '…</div>';
        }).join('') + '</div>';
    }
  }catch(e){
    answer.innerHTML = '<div class="ask-card"><div class="ask-a">抱歉，' +
      esc((e && e.message) || '问答服务暂时不可用') + '</div></div>';
  }finally{
    if(btn){ btn.disabled = false; btn.textContent = '问'; }
  }
}

document.getElementById('askBtn').onclick = function(){
  askQuestion(document.getElementById('askInput').value.trim());
};
document.getElementById('askInput').addEventListener('keydown', function(e){
  if(e.key === 'Enter'){ e.preventDefault(); askQuestion(this.value.trim()); }
});
document.getElementById('askChips').addEventListener('click', function(e){
  const c = e.target.closest('[data-ask]');
  if(!c) return;
  const q = c.getAttribute('data-ask');
  document.getElementById('askInput').value = q;
  askQuestion(q);
});

/* ============ 爱心求助 ============ */
const HELP_NAMES = {help_borrow:'借用工具', help_errand:'代办跑腿', help_donate:'爱心捐赠', help_volunteer:'志愿帮忙'};
let currentHelpCat = '';
let helpGoId = '';

function openHelp(cat){
  currentHelpCat = cat || '';
  document.getElementById('helpTitle').textContent = cat ? (HELP_NAMES[cat] || '爱心求助') : '爱心求助';
  renderHelp();
  show('help');
}

function renderHelp(){
  const wrap = document.getElementById('helpList');
  if(!wrap) return;
  let arr = Store.list({statuses:['approved','claimed','closed']}).filter(function(x){ return x.type === 'help'; });
  if(currentHelpCat){
    arr = arr.filter(function(x){ return x.cat === currentHelpCat || x.helpCat === currentHelpCat; });
  }
  arr.sort(function(a,b){ return (b.createdAt||0) - (a.createdAt||0); });
  if(!arr.length){
    wrap.innerHTML = '<div class="empty">这个分类还没有求助，点右上角「发布」发一条吧</div>';
    return;
  }
  wrap.innerHTML = arr.map(function(it){
    const m = catInfo(it.cat);
    return '<div class="item" data-help-item="' + esc(it.id) + '">' +
      '<div class="thumb" style="background:linear-gradient(135deg,' + m.c + ',' + shade(m.c) + ')">' + m.e + '</div>' +
      '<div class="body">' +
      '<div class="tt">' + esc(it.title) + statusChip(it.status) + '</div>' +
      '<div class="dd">' + esc(it.desc || '') + '</div>' +
      '<div class="row"><span class="meta">📍 ' + esc(it.place || '未填写地点') + ' · ' + fmtTime(it.createdAt) + '</span>' +
      '<button class="btn" data-help-go="' + esc(it.id) + '">我来帮忙</button></div>' +
      '</div></div>';
  }).join('');
}

document.getElementById('helpPublishBtn').onclick = function(){
  document.getElementById('helpCatSel').value = currentHelpCat || 'help_borrow';
  document.getElementById('helpSheet').classList.add('show');
};
document.getElementById('helpSheetClose').onclick = function(){
  document.getElementById('helpSheet').classList.remove('show');
};
document.getElementById('helpSubmit').onclick = async function(){
  const title = document.getElementById('helpTitleInput').value.trim();
  const desc = document.getElementById('helpDesc').value.trim();
  const cat = document.getElementById('helpCatSel').value;
  const place = document.getElementById('helpPlace').value.trim();
  const phone = document.getElementById('helpPhone').value.trim();
  if(title.length < 2){ toast('写个标题，比如「想借一把雨伞」'); return; }
  if(desc.length < 5){ toast('说明一下需求、时间和地点'); return; }
  if(phone){
    const pchk = phoneCheckLocal(phone);
    if(pchk.status === 'red'){ toast('电话号码不正确：' + pchk.reason); return; }
  }
  this.disabled = true;
  this.textContent = '发布中…';
  try{
    const payload = {type:'help', cat:cat, helpCat:cat, title:title, desc:desc,
                     place: place || '未填写地点', eventTime:'', secret:'', photo:null,
                     contact:{phone: phone}};
    if(API_BASE){ await Net.create(payload); await netSync(); }
    else {
      Store.add(Object.assign({id:'p_'+Date.now().toString(36), status:'approved', ownerId:myId(),
                               createdAt:Date.now(), updatedAt:Date.now()}, payload));
    }
    document.getElementById('helpSheet').classList.remove('show');
    document.getElementById('helpTitleInput').value = '';
    document.getElementById('helpDesc').value = '';
    document.getElementById('helpPlace').value = '';
    document.getElementById('helpPhone').value = '';
    renderHelp();
    toast('已发布，审核通过后会出现在列表');
  }catch(e){
    toast((e && e.message) || '发布失败');
  }finally{
    this.disabled = false;
    this.textContent = '发布求助';
  }
};

document.getElementById('helpList').addEventListener('click', function(e){
  const b = e.target.closest('[data-help-go]');
  if(!b) return;
  e.stopPropagation();
  helpGoId = b.getAttribute('data-help-go');
  const it = Store.get(helpGoId);
  document.getElementById('helpGoTitle').textContent = it ? ('《' + it.title + '》') : '';
  document.getElementById('helpGoMsg').value = '';
  document.getElementById('helpGoPhone').value = '';
  document.getElementById('helpGoSheet').classList.add('show');
});
document.getElementById('helpGoClose').onclick = function(){
  document.getElementById('helpGoSheet').classList.remove('show');
};
document.getElementById('helpGoSubmit').onclick = async function(){
  const msg = document.getElementById('helpGoMsg').value.trim();
  const phone = document.getElementById('helpGoPhone').value.trim();
  if(msg.length < 2){ toast('说一句你能怎么帮'); return; }
  this.disabled = true;
  this.textContent = '发送中…';
  try{
    await Net.claim(helpGoId, {message: msg, contact: phone});
    document.getElementById('helpGoSheet').classList.remove('show');
    toast('已告诉对方，等 TA 确认');
  }catch(e){
    toast((e && e.message) || '发送失败');
  }finally{
    this.disabled = false;
    this.textContent = '发送';
  }
};

/* ============ 电话号码校验（前端即时提示，服务端再校验） ============ */
function maxRun(d){ let b = 1, c = 1; for(let i = 1; i < d.length; i++){ c = d[i] === d[i-1] ? c + 1 : 1; b = Math.max(b, c); } return b; }
function maxSeq(d){ let u = 1, dn = 1, b = 1; for(let i = 1; i < d.length; i++){ const x = +d[i-1], y = +d[i]; u = y === x + 1 ? u + 1 : 1; dn = y === x - 1 ? dn + 1 : 1; b = Math.max(b, u, dn); } return b; }
function periodic(d){ for(const p of [2,3]){ if(d.length >= p * 4){ let ok = true; for(let i = 0; i < d.length; i++){ if(d[i] !== d[i % p]){ ok = false; break; } } if(ok) return p; } } return 0; }

function phonePattern(d){
  if(new Set(d).size === 1) return {red:'全部数字相同，不是有效号码'};
  const run = maxRun(d), seq = maxSeq(d), per = periodic(d);
  if(run >= 8) return {red:'连续 ' + run + ' 位数字相同，不是有效号码'};
  if(seq >= 8) return {red:'连续 ' + seq + ' 位数字递增/递减，不是有效号码'};
  if((per === 2 && d.length >= 8) || (per === 3 && d.length >= 9)) return {red:'数字循环重复，不是有效号码'};
  if(run >= 6) return {yellow:'连续 ' + run + ' 位数字相同，请确认是本人常用号码'};
  if(seq >= 6) return {yellow:'连续 ' + seq + ' 位数字递增/递减，请确认是本人常用号码'};
  if(per === 2 && d.length >= 6) return {yellow:'数字循环重复，请确认是本人常用号码'};
  if(run >= 4) return {yellow:'连续 ' + run + ' 位相同，确认是本人常用号吗？'};
  if(seq >= 4) return {yellow:'连续 ' + seq + ' 位递增/递减，确认是本人常用号吗？'};
  return {};
}

function phoneCheckLocal(raw){
  let s = String(raw || '').trim();
  s = s.replace(/[０-９]/g, function(ch){ return String.fromCharCode(ch.charCodeAt(0) - 65248); });
  s = s.replace(/幺/g, '1').replace(/[〇零]/g, '0')
       .replace(/一/g, '1').replace(/二/g, '2').replace(/三/g, '3').replace(/四/g, '4')
       .replace(/五/g, '5').replace(/六/g, '6').replace(/七/g, '7').replace(/八/g, '8').replace(/九/g, '9');
  s = s.replace(/[\s()（）.．]/g, '').replace(/[－—]/g, '-');
  if(!s) return {status:'none', type:'none', reason:'', normalized:''};
  if(/[A-Za-z]/.test(s)){
    if(/^[A-Za-z][A-Za-z0-9_-]{5,19}$/.test(s)) return {status:'green', type:'wechat', reason:'', normalized:s};
    return {status:'red', type:'invalid', reason:'包含字母', normalized:''};
  }
  if(/[^\d+\-]/.test(s)) return {status:'red', type:'invalid', reason:'包含无法识别的字符', normalized:''};

  let work = s;
  if(work.indexOf('+86') === 0) work = work.slice(3);
  else if(work.indexOf('0086') === 0) work = work.slice(4);
  const digits = work.replace(/\D/g, '');
  if(!digits) return {status:'red', type:'invalid', reason:'没有数字', normalized:''};
  if(/^(400|800)/.test(digits) || /^(95|96)\d{3,5}$/.test(digits)){
    return {status:'red', type:'service', reason:'企业或服务号码，请留个人号码', normalized:digits};
  }
  if(s.indexOf('+') === 0 && s.indexOf('+86') !== 0 && digits.length >= 8 && digits.length <= 15){
    return {status:'green', type:'international', reason:'', normalized:'+' + digits};
  }

  const lm = work.match(/^(0\d{2,3})-?(\d{7,8})(?:-(\d{1,6}))?$/);
  if(lm){
    const pat = phonePattern(lm[2]);
    if(pat.red) return {status:'red', type:'landline', reason:'座机号码不真实（' + pat.red + '）', normalized:work};
    if(pat.yellow) return {status:'yellow', type:'landline', reason:pat.yellow, normalized:work};
    return {status:'green', type:'landline', reason:'', normalized:work};
  }

  if(digits.length === 11 && digits[0] === '1'){
    const pat = phonePattern(digits);
    if(pat.red) return {status:'red', type:'mobile', reason:pat.red, normalized:''};
    if(['13800138000','12345678901','11111111111'].indexOf(digits) >= 0) return {status:'red', type:'mobile', reason:'这是常见的测试号码', normalized:''};
    if(!/^1[3-9]\d{9}$/.test(digits)) return {status:'red', type:'mobile', reason:'手机号应以 13–19 开头', normalized:''};
    if(pat.yellow) return {status:'yellow', type:'mobile', reason:pat.yellow, normalized:digits};
    if(/^1(70|71|62|65|67)/.test(digits)) return {status:'yellow', type:'mobile', reason:'虚拟号段，建议留常用号码', normalized:digits};
    return {status:'green', type:'mobile', reason:'', normalized:digits};
  }

  if(/^\d{7,8}$/.test(digits)){
    const pat = phonePattern(digits);
    if(pat.red) return {status:'red', type:'landline', reason:pat.red, normalized:''};
    return {status:'yellow', type:'landline', reason:'座机请带区号，例如 010-62785566', normalized:digits};
  }

  return {status:'red', type:'invalid', reason:'号码应为 11 位手机号，或带区号的座机', normalized:''};
}

function bindPhoneHint(input, hint, confirmWrap, confirmBox){
  if(!input || !hint) return;
  let timer = null;
  const apply = function(){
    const r = phoneCheckLocal(input.value.trim());
    input.style.borderColor = '';
    if(r.status === 'none'){
      hint.textContent = '';
    } else if(r.status === 'green'){
      hint.textContent = '✅ ' + (r.type === 'wechat' ? '将作为微信号展示' :
        (r.type === 'landline' ? '座机号码正常' : (r.type === 'international' ? '国际号码正常' : '号码格式正常')));
      hint.style.color = '#2f7d46';
      input.style.borderColor = '#b8e0c2';
    } else if(r.status === 'yellow'){
      hint.textContent = '⚠️ ' + r.reason;
      hint.style.color = '#a15c00';
      input.style.borderColor = '#f0c36d';
    } else {
      hint.textContent = '❌ ' + r.reason + (r.type === 'landline' ? '' : '。如果是座机，请带区号，如 010-62785566');
      hint.style.color = '#a12f2f';
      input.style.borderColor = '#e8a0a0';
    }
    if(confirmWrap) confirmWrap.style.display = (r.status === 'yellow') ? 'block' : 'none';
    const ml = document.getElementById('phoneManualLine');
    if(ml && input === document.querySelector('#publishForm input[name="phone"]')){
      ml.style.display = (r.status === 'yellow') ? 'block' : 'none';
    }
    if(confirmBox && r.status !== 'yellow'){ confirmBox.checked = false; phoneManualRequest = false; }
    return r;
  };
  input.addEventListener('input', function(){
    if(timer) clearTimeout(timer);
    timer = setTimeout(apply, 300);
  });
  input.addEventListener('blur', function(){
    if(timer) clearTimeout(timer);
    apply();
  });
  return apply;
}

bindPhoneHint(document.querySelector('#publishForm input[name="phone"]'), document.getElementById('phoneHint'),
              document.getElementById('phoneConfirmWrap'), document.getElementById('phoneConfirm'));
bindPhoneHint(document.getElementById('claimPhone'), document.getElementById('claimPhoneHint'));
bindPhoneHint(document.getElementById('helpPhone'), document.getElementById('helpPhoneHint'));

document.getElementById('phoneManual').onclick = function(){
  phoneManualRequest = true;
  const cb = document.getElementById('phoneConfirm');
  if(cb) cb.checked = false;
  toast('已申请人工确认，可以直接提交');
};

/* 黄色号码：离开输入框就弹确认，不用等提交 */
(function(){
  const input = document.querySelector('#publishForm input[name="phone"]');
  if(!input) return;
  let asked = '';
  input.addEventListener('blur', function(){
    setTimeout(function(){
      const v = input.value.trim();
      if(!v || v === asked) return;
      const r = phoneCheckLocal(v);
      if(r.status !== 'yellow') return;
      asked = v;
      if(confirm('这个号码 ' + v + ' 有连续重复，确认是你本人的常用号码吗？')){
        const cb = document.getElementById('phoneConfirm');
        if(cb) cb.checked = true;
      }
    }, 350);
  });
})();

/* ===== 归还证书 ===== */
function fmtDuration(ms){
  const m = Math.max(1, Math.round(ms / 60000));
  if(m < 60) return m + ' 分钟';
  const h = Math.floor(m / 60), mm = m % 60;
  if(h < 24) return h + ' 小时' + (mm ? ' ' + mm + ' 分钟' : '');
  return Math.floor(h / 24) + ' 天' + (h % 24 ? ' ' + (h % 24) + ' 小时' : '');
}

function roundRect(g, x, y, w, h, r){
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}

function wrapText(g, text, cx, y, maxW, lh){
  const chars = String(text).split('');
  let line = '', lines = [];
  for(let i = 0; i < chars.length; i++){
    const test = line + chars[i];
    if(g.measureText(test).width > maxW && line){ lines.push(line); line = chars[i]; }
    else line = test;
  }
  if(line) lines.push(line);
  lines.forEach(function(l, i){ g.fillText(l, cx, y + i * lh); });
}

function certDate(ts){
  const d = new Date(ts || Date.now());
  return d.getFullYear() + '.' + (d.getMonth() + 1) + '.' + d.getDate();
}

function showCertificate(info){
  const old = document.getElementById('certMask');
  if(old) old.remove();
  const doneAt = info.completedAt || Date.now();
  const dur = fmtDuration(doneAt - (info.createdAt || doneAt));
  const mask = document.createElement('div');
  mask.className = 'cert-mask';
  mask.id = 'certMask';
  mask.innerHTML = '<div class="cert-card">' +
    '<div class="cert-badge">🎉</div>' +
    '<div class="cert-h">归还成功</div>' +
    '<div class="cert-title">《' + esc(info.title || '物品') + '》</div>' +
    '<div class="cert-sub">从发布到归还，用了 ' + esc(dur) + '</div>' +
    '<div class="cert-code"><span>取件码</span><b>' + esc(info.code || '') + '</b></div>' +
    '<div class="cert-brand">清华校园拾光里 · ' + certDate(doneAt) + '</div>' +
    '<div class="cert-acts"><button class="btn" id="certSave">保存证书</button>' +
    '<button class="btn ghost" id="certClose">关闭</button></div></div>';
  document.body.appendChild(mask);
  const closeCert = function(){ mask.remove(); if(activeLayer === closeCert) activeLayer = null; };
  activeLayer = closeCert;
  document.getElementById('certClose').onclick = closeCert;
  document.getElementById('certSave').onclick = function(){ saveCertificate(info, dur, doneAt); };
}

function saveCertificate(info, dur, doneAt){
  const W = 720, H = 1000;
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const g = cv.getContext('2d');
  const grad = g.createLinearGradient(0, 0, W, H);
  grad.addColorStop(0, '#5b1f92');
  grad.addColorStop(1, '#a06ad6');
  g.fillStyle = grad;
  g.fillRect(0, 0, W, H);
  g.fillStyle = 'rgba(255,255,255,.97)';
  roundRect(g, 40, 120, W - 80, H - 240, 28);
  g.fill();
  g.textAlign = 'center';
  g.fillStyle = '#62269c';
  g.font = 'bold 34px sans-serif';
  g.fillText('归 还 成 功', W / 2, 220);
  g.fillStyle = '#2f2a3a';
  g.font = 'bold 38px sans-serif';
  wrapText(g, '《' + (info.title || '物品') + '》', W / 2, 300, W - 160, 50);
  g.fillStyle = '#6b6480';
  g.font = '26px sans-serif';
  g.fillText('从发布到归还，用了 ' + dur, W / 2, 390);
  g.fillStyle = '#f2eefc';
  roundRect(g, W / 2 - 150, 430, 300, 110, 18);
  g.fill();
  g.fillStyle = '#7a7290';
  g.font = '22px sans-serif';
  g.fillText('取件码', W / 2, 472);
  g.fillStyle = '#62269c';
  g.font = 'bold 46px monospace';
  g.fillText(info.code || '------', W / 2, 522);
  g.fillStyle = '#3a3645';
  g.font = '24px sans-serif';
  wrapText(g, '每一件回到主人手里的东西，都让校园更温暖一点。', W / 2, 630, W - 170, 38);
  g.fillStyle = '#8a8594';
  g.font = '22px sans-serif';
  g.fillText('清华校园拾光里 · ' + certDate(doneAt), W / 2, H - 220);
  g.fillStyle = '#62269c';
  g.font = '20px sans-serif';
  g.fillText('AI 审核 · 智能匹配 · 双向核验', W / 2, H - 180);
  const a = document.createElement('a');
  a.download = '归还证书-' + certDate(doneAt) + '.png';
  a.href = cv.toDataURL('image/png');
  a.click();
}

/* ============ 初始化 ============ */
function checkStorage(){
  try{
    const k = '__sg_test__';
    localStorage.setItem(k, '1');
    localStorage.removeItem(k);
  }catch(e){ warnStorage(); }
}
try{
  checkStorage();
  renderMemorial();
  loadAnnouncements();
  renderImgSearch();
  renderLost(); renderFound(); renderLend('lend'); renderBorrow('borrow');
  renderMine();
  setNetBadge();
  if(API_BASE){
    netSync();
    renderClaims();
    renderAccBox();
    renderAskChips();
    setInterval(function(){ if(!document.hidden) netSync(); }, 30000);
  } else {
    setTimeout(function(){
      toast('本机模式：数据只在这台电脑；要发帖给同学看，请用公网地址打开');
    }, 900);
  }
  console.log('清华校园拾光里 v3.2 已就绪 · 模式=' + (API_BASE ? '共享' : '本机') + ' · 存储键 ' + STORE_KEY);
}catch(err){
  const b = document.getElementById('errTop');
  if(b){ b.textContent = '⚠️ 页面初始化失败：' + err.message; b.classList.add('show'); }
  if(window.console) console.error(err);
}
