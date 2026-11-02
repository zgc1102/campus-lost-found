
(function(){
  const BASE = location.protocol === 'file:' ? '' : '';
  let token = sessionStorage.getItem('sg_admin_token') || '';
  let items = [];
  let tab = 'pending';
  let keyword = '';

  const $ = id => document.getElementById(id);

  async function api(path, opts){
    opts = opts || {};
    opts.headers = Object.assign({'Content-Type':'application/json'}, opts.headers || {});
    if(token) opts.headers['X-Admin-Token'] = token;
    const r = await fetch(path, opts);
    if(r.status === 401){ logout(true); throw new Error('登录已过期，请重新登录'); }
    if(!r.ok) throw new Error('请求失败 HTTP ' + r.status);
    const t = await r.text();
    return t ? JSON.parse(t) : null;
  }

  function showLogin(msg){
    $('loginBox').style.display = 'block';
    $('panel').style.display = 'none';
    $('hbar').style.display = 'none';
    $('loginMsg').textContent = msg || '';
  }
  function showPanel(){
    $('loginBox').style.display = 'none';
    $('panel').style.display = 'block';
    $('hbar').style.display = 'flex';
  }
  function logout(silent){
    token = '';
    sessionStorage.removeItem('sg_admin_token');
    showLogin(silent ? '登录已过期，请重新登录' : '');
  }

  async function login(){
    const pwd = $('pwd').value.trim();
    if(!pwd){ $('loginMsg').textContent = '请输入密码'; return; }
    $('loginMsg').textContent = '登录中…';
    try{
      const r = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({password: pwd})});
      if(!r.ok){ $('loginMsg').textContent = '密码不对'; return; }
      const data = await r.json();
      token = data.token;
      sessionStorage.setItem('sg_admin_token', token);
      $('pwd').value = '';
      $('loginMsg').textContent = '';
      showPanel();
      await loadAiConfig();
      await load();
    }catch(e){ $('loginMsg').textContent = '连不上服务器'; }
  }

  async function load(){
    try{
      items = await api('/api/admin/items') || [];
      if(tab === 'users'){ await loadAccounts(); return; }
      if(tab === 'announce'){ await loadAnnouncements(); return; }
      if(tab === 'phone'){ await loadSpecial(); return; }
      if(tab === 'overview'){ await loadStats(); return; }
      render();
    }catch(e){ $('list').innerHTML = '<div class="empty">' + e.message + '</div>'; }
  }

  let accounts = [];
  async function loadAccounts(){
    try{
      accounts = await api('/api/admin/accounts') || [];
      renderUsers();
    }catch(e){
      $('list').innerHTML = '<div class="empty">' + e.message + '</div>';
    }
  }

  let statsData = null;
  async function loadStats(){
    try{
      statsData = await api('/api/admin/stats');
      renderStats();
    }catch(e){
      $('list').innerHTML = '<div class="empty">' + e.message + '</div>';
    }
  }

  function countUp(el, target){
    const dur = 520, t0 = performance.now();
    function tick(t){
      const p = Math.min(1, (t - t0) / dur);
      const ease = 1 - Math.pow(1 - p, 3);
      el.textContent = String(Math.round(target * ease));
      if(p < 1) requestAnimationFrame(tick);
      else el.textContent = String(target);
    }
    requestAnimationFrame(tick);
  }

  function renderStats(){
    const s = statsData || {};
    const bs = s.byStatus || {};
    $('stats').innerHTML =
      '<div class="s"><b>' + (s.items || 0) + '</b><span>总发布</span></div>' +
      '<div class="s"><b>' + (bs.approved || 0) + '</b><span>已上架</span></div>' +
      '<div class="s"><b>' + (bs.pending || 0) + '</b><span>待审核</span></div>' +
      '<div class="s"><b>' + (bs.rejected || 0) + '</b><span>已驳回</span></div>';
    [s.items, bs.approved, bs.pending, bs.rejected].forEach(function(v, i){
      const el = document.querySelectorAll('#stats .s b')[i];
      if(el) countUp(el, v || 0);
    });
    const days = s.days || [];
    const max = Math.max.apply(null, [1].concat(days.map(function(d){ return d.count; })));
    const bars = days.map(function(d){
      const h = Math.round(d.count / max * 88) + 4;
      return '<div style="flex:1;text-align:center;font-size:10px;color:#7a7290">' +
        '<div style="height:92px;display:flex;align-items:flex-end;justify-content:center">' +
        '<div style="width:18px;height:' + h + 'px;background:#8a5fd0;border-radius:4px 4px 0 0" title="' + d.count + '"></div></div>' +
        '<div style="margin-top:4px">' + d.day + '</div></div>';
    }).join('');
    $('list').innerHTML =
      '<div class="item"><div class="tt">最近 7 天发布</div>' +
      '<div style="display:flex;gap:6px;margin-top:12px;align-items:flex-end">' + bars + '</div></div>' +
      '<div class="item"><div class="tt">数据分布</div>' +
      '<div class="meta">寻物 ' + (s.lost || 0) + ' · 招领 ' + (s.found || 0) + ' · 爱心求助 ' + (s.help || 0) + '</div>' +
      '<div class="meta">注册用户 ' + (s.accounts || 0) + '（停用 ' + (s.banned || 0) + '） · 已发布公告 ' + (s.announcements || 0) + '</div>' +
      '<div class="meta">认领申请 ' + (s.claims || 0) + '（完成 ' + ((s.claimsByStatus || {}).completed || 0) + '）</div></div>';
  }

  function renderUsers(){
    $('stats').innerHTML = '<div class="s"><b>' + accounts.length + '</b><span>注册用户</span></div>';
    if(!accounts.length){
      $('list').innerHTML = '<div class="empty">还没有人注册账号</div>';
      return;
    }
    $('list').innerHTML = '<div class="table-wrap"><table class="utable"><thead><tr>' +
      '<th>手机号</th><th>注册时间</th><th>最近登录</th><th>发布</th><th>状态</th><th>操作</th>' +
      '</tr></thead><tbody>' + accounts.map(function(a){
        return '<tr>' +
          '<td class="num">' + esc(a.phone) + '</td>' +
          '<td>' + fmt(a.createdAt) + '</td>' +
          '<td>' + (a.lastLoginAt ? fmt(a.lastLoginAt) : '—') + '</td>' +
          '<td class="num">' + (a.posts || 0) + '</td>' +
          '<td class="' + (a.banned ? 'bad' : 'ok') + '">' + (a.banned ? '已停用' : '正常') + '</td>' +
          '<td><button class="btn ' + (a.banned ? 'ok' : 'danger') +
          '" data-ban="' + a.id + '" data-banned="' + (a.banned ? '1' : '0') + '">' +
          (a.banned ? '恢复' : '停用') + '</button></td>' +
          '</tr>';
      }).join('') + '</tbody></table></div>';
  }

  let announcements = [];
  let editingAnn = null;

  async function loadAnnouncements(){
    try{
      announcements = await api('/api/admin/announcements') || [];
      renderAnnounce();
    }catch(e){ $('list').innerHTML = '<div class="empty">' + e.message + '</div>'; }
  }

  function annForm(a){
    a = a || {title:'', body:'', pinned:false};
    return '<div class="item" style="padding:14px">' +
      '<div class="tt" style="margin-bottom:8px">' + (editingAnn ? '编辑公告' : '新建公告') + '</div>' +
      '<input id="annTitle" placeholder="公告标题（必填，例如：失物招领点调整通知）" value="' + esc(a.title || '') + '" style="width:100%;padding:9px;border:1px solid #ddd;border-radius:8px;margin-bottom:8px;font-family:inherit">' +
      '<textarea id="annBody" placeholder="公告正文（必填）" style="width:100%;height:110px;padding:9px;border:1px solid #ddd;border-radius:8px;margin-bottom:8px;font-family:inherit">' + esc(a.body || '') + '</textarea>' +
      '<label style="font-size:13px;display:block;margin-bottom:10px"><input type="checkbox" id="annPinned" ' + (a.pinned ? 'checked' : '') + '> 置顶</label>' +
      '<div class="acts">' +
      '<button class="btn ok" data-ann-save="1">' + (editingAnn ? '保存修改' : '保存草稿') + '</button>' +
      '<button class="btn" data-ann-pub="1">保存并发布</button>' +
      (editingAnn ? '<button class="btn gray" data-ann-cancel="1">取消编辑</button>' : '') +
      '</div></div>';
  }

  function renderAnnounce(){
    $('stats').innerHTML = '<div class="s"><b>' + announcements.length + '</b><span>公告</span></div>';
    $('list').innerHTML = annForm(editingAnn) + (announcements.length ? announcements.map(function(a){
      return '<div class="item"><div class="row1">' +
        '<span class="tag">' + (a.status === 'published' ? '已发布' : '草稿') + '</span>' +
        (a.pinned ? '<span class="status" style="background:#fff4d6;color:#a97a00">置顶</span>' : '') +
        '<div class="tt">' + esc(a.title) + '</div></div>' +
        '<div class="meta">' + esc((a.body || '').slice(0, 80)) + '</div>' +
        '<div class="meta">更新：' + fmt(a.updatedAt) + '　发布：' + (a.publishedAt ? fmt(a.publishedAt) : '—') + '</div>' +
        '<div class="acts">' +
        '<button class="btn ghost" data-ann-edit="' + a.id + '">编辑</button>' +
        (a.status === 'published'
          ? '<button class="btn gray" data-ann-draft="' + a.id + '">下线</button>'
          : '<button class="btn ok" data-ann-publish="' + a.id + '">发布</button>') +
        '<button class="btn danger" data-ann-del="' + a.id + '">删除</button>' +
        '</div></div>';
    }).join('') : '<div class="empty">还没有公告，上面写一条吧</div>');
  }

  async function saveAnnounce(publish){
    const title = ($('annTitle') || {}).value || '';
    const body = ($('annBody') || {}).value || '';
    const pinned = !!($('annPinned') || {}).checked;
    if(title.trim().length < 2 || body.trim().length < 5){ alert('标题或正文太短'); return; }
    try{
      if(editingAnn){
        await api('/api/admin/announcements/' + encodeURIComponent(editingAnn.id), {
          method: 'PATCH',
          body: JSON.stringify({title: title.trim(), body: body.trim(), pinned: pinned,
                                status: publish ? 'published' : undefined})
        });
      } else {
        await api('/api/admin/announcements', {
          method: 'POST',
          body: JSON.stringify({title: title.trim(), body: body.trim(), pinned: pinned, publish: !!publish})
        });
      }
      editingAnn = null;
      await loadAnnouncements();
    }catch(e){ alert(e.message); }
  }

  let specialNumbers = [];
  async function loadSpecial(){
    try{
      items = await api('/api/admin/items') || [];
      specialNumbers = await api('/api/admin/special-numbers') || [];
      renderSpecial();
    }catch(e){ $('list').innerHTML = '<div class="empty">' + e.message + '</div>'; }
  }

  function renderSpecial(){
    const pending = items.filter(function(x){ return x.phoneReviewRequested; });
    $('stats').innerHTML = '<div class="s"><b>' + specialNumbers.length + '</b><span>白名单号码</span></div>';
    const pendingHtml = pending.length ? ('<div class="sectitle">用户申请</div>' + pending.map(function(it){
      return '<div class="item"><div class="row1"><span class="tag">申请</span><div class="tt">' +
        esc((it.contact || {}).phone || '') + '</div></div>' +
        '<div class="meta">' + esc(it.title || '') + ' · ' + esc(it.place || '') + '</div>' +
        '<div class="acts"><button class="btn ok" data-phone-approve="' + esc(it.id) + '">通过并加入白名单</button></div></div>';
    }).join('')) : '';
    const listHtml = specialNumbers.length ? specialNumbers.map(function(p){
      return '<div class="item"><div class="row1"><div class="tt">' + esc(p) + '</div></div>' +
        '<div class="acts"><button class="btn danger" data-special-del="' + esc(p) + '">移出白名单</button></div></div>';
    }).join('') : '<div class="empty">还没有特殊号码</div>';
    $('list').innerHTML =
      '<div class="item"><div class="tt">添加特殊号码</div>' +
      '<div class="meta">豹子号、连号等真实存在但被规则误判的号码，加入后发布直接通过，不再提示</div>' +
      '<div style="display:flex;gap:8px;margin-top:8px">' +
      '<input id="specialPhone" placeholder="11 位手机号，如 13311111111" style="flex:1;padding:9px;border:1px solid #ddd;border-radius:8px;font-family:inherit">' +
      '<button class="btn ok" id="specialAdd">添加</button></div></div>' +
      pendingHtml +
      '<div class="sectitle">已加入白名单</div>' + listHtml;
    const add = document.getElementById('specialAdd');
    if(add) add.onclick = async function(){
      const v = (document.getElementById('specialPhone').value || '').trim();
      if(!v){ alert('请输入手机号'); return; }
      try{
        await api('/api/admin/special-numbers', {method:'POST', body: JSON.stringify({phone:v})});
        await loadSpecial();
      }catch(e){ alert(e.message); }
    };
  }

  function statusText(s){
    return ({pending:'审核中',approved:'已上架',rejected:'已驳回',closed:'已闭环',claimed:'已认领',removed:'已下架',hidden:'已隐藏'})[s] || s;
  }

  function render(){
    const counts = {pending:0, approved:0, rejected:0, all:items.length};
    items.forEach(x => { if(counts[x.status] !== undefined) counts[x.status]++; });
    $('stats').innerHTML =
      '<div class="s"><b>'+counts.pending+'</b><span>待审核</span></div>'+
      '<div class="s"><b>'+counts.approved+'</b><span>已上架</span></div>'+
      '<div class="s"><b>'+counts.rejected+'</b><span>已驳回</span></div>';

    let list = items.slice();
    if(tab === 'phone'){ list = list.filter(x => x.phoneStatus === 'yellow' && !x.phoneVerified); }
    else if(tab === 'all'){ list = list.filter(x => x.status !== 'removed'); }
    else { list = list.filter(x => x.status === tab); }
    if(keyword){
      const k = keyword.toLowerCase();
      list = list.filter(x => ((x.title||'')+(x.desc||'')+(x.place||'')).toLowerCase().indexOf(k) >= 0);
    }

    if(!list.length){ $('list').innerHTML = '<div class="empty">没有内容</div>'; return; }
    $('list').innerHTML = list.map(card).join('');
  }

  function esc(s){
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function card(it){
    const typeName = it.type === 'lost' ? '寻物' : '招领';
    const phone = (it.contact && it.contact.phone) || '';
    let acts = '';
    if(it.status === 'pending'){
      acts = '<button class="btn ok" data-approve="'+esc(it.id)+'">通过并上架</button>'+
             '<button class="btn danger" data-reject="'+esc(it.id)+'">驳回</button>';
    } else if(it.status === 'approved' || it.status === 'claimed'){
      acts = '<button class="btn ghost" data-approve="'+esc(it.id)+'">保持上架</button>'+
             '<button class="btn danger" data-reject="'+esc(it.id)+'">下架</button>';
    } else if(it.status === 'rejected'){
      acts = '<button class="btn ok" data-approve="'+esc(it.id)+'">改为通过</button>';
    } else if(it.status === 'removed'){
      acts = '<button class="btn ok" data-approve="'+esc(it.id)+'">恢复上架</button>';
    }
    if(it.phoneStatus === 'yellow' && !it.phoneVerified){
      acts = '<button class="btn ok" data-phone-approve="'+esc(it.id)+'">通过号码</button>' + acts;
    }
    return '<div class="item">'+
      '<div class="row1">'+
        '<span class="tag '+(it.type === 'lost' ? '' : 'found')+'">'+typeName+'</span>'+
        '<span class="status st-'+esc(it.status)+'">'+esc(statusText(it.status))+'</span>'+
        (it.autoApproved ? '<span class="status" style="background:#e6f4ea;color:#2f7d46">AI 自动通过</span>' : '')+
        (it.autoRejected ? '<span class="status" style="background:#fdeaea;color:#a12f2f">AI 自动拦截</span>' : '')+
        (it.phoneStatus === 'yellow' && !it.phoneVerified ? '<span class="status" style="background:#fff4d6;color:#a97a00" title="'+esc(it.phoneReason||'')+'">📞 号码待确认</span>' : '')+
        (it.phoneStatus === 'yellow' && it.phoneVerified ? '<span class="status" style="background:#e6f4ea;color:#2f7d46">号码已人工确认</span>' : '')+
        (it.phoneStatus === 'red' ? '<span class="status" style="background:#fdeaea;color:#a12f2f" title="'+esc(it.phoneReason||'')+'">📵 号码无效</span>' : '')+
        '<div class="tt">'+esc(it.title)+'</div>'+
      '</div>'+
      '<div class="meta">'+esc(it.place || '未填写地点')+' · '+fmt(it.createdAt)+'</div>'+
      '<div class="meta">'+esc(it.desc || '')+'</div>'+
      (it.visionDesc ? '<div class="meta" style="color:#7a5aa8">🖼 AI 看图：'+esc(it.visionDesc)+'</div>' : '')+
      (it.photoUrl ? '<img class="admin-photo" src="' + esc(it.photoUrl) + (token ? (it.photoUrl.indexOf('?') >= 0 ? '&' : '?') + 'token=' + encodeURIComponent(token) : '') + '" alt="发布图片">' : '')+
      (it.secret ? '<div class="secret">🔒 核验特征（仅管理员可见）：'+esc(it.secret)+'</div>' : '')+
      (phone ? '<div class="phone">📞 联系电话：'+esc(phone)+'</div>' : '')+
      (it.status === 'rejected' && it.rejectReason ? '<div class="meta">驳回理由：'+esc(it.rejectReason)+'</div>' : '')+
      aiBlock(it)+
      '<div class="acts">'+acts+'</div>'+
      '<div class="reject" id="rj_'+esc(it.id)+'">'+
        '<textarea id="rjt_'+esc(it.id)+'" placeholder="驳回理由（会展示给发布者）"></textarea>'+
        '<div class="acts"><button class="btn danger" data-reject-ok="'+esc(it.id)+'">确认驳回</button>'+
        '<button class="btn gray" data-reject-cancel="'+esc(it.id)+'">取消</button></div>'+
      '</div>'+
    '</div>';
  }

  function fmt(ts){
    const d = new Date(ts || Date.now());
    const p = n => ('0'+n).slice(-2);
    return (d.getMonth()+1)+'-'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes());
  }

  async function setStatus(id, status, reason){
    try{
      await api('/api/admin/items/' + encodeURIComponent(id), {
        method:'PATCH',
        body: JSON.stringify({status: status, rejectReason: reason || ''})
      });
      await load();
    }catch(e){ alert(e.message); }
  }

  function aiLabel(d){ return d === 'approve' ? '建议通过' : (d === 'reject' ? '建议驳回' : '建议人工复核'); }

  function aiBlock(it){
    if(!it.ai){
      return '<div class="acts" style="margin-top:10px"><button class="btn gray" data-ai-run="'+esc(it.id)+'">🤖 AI 审核这条</button></div>';
    }
    const a = it.ai;
    const src = a.source === 'llm' ? ('大模型 · ' + esc(a.model || ''))
              : (a.source === 'rule-fallback' ? '规则引擎（大模型调用失败）' : '本地规则引擎');
    return '<div class="ai ai-'+esc(a.decision)+'">'+
      '<b>🤖 AI '+aiLabel(a.decision)+'</b> · 风险 '+esc(a.score)+'/100'+
      '<div class="aireason">'+esc(a.reason || '')+'</div>'+
      '<div class="aisrc">'+src+'</div>'+
      '<div class="acts">'+
        '<button class="btn ghost" data-ai-apply="'+esc(it.id)+'">采纳建议</button>'+
        '<button class="btn gray" data-ai-run="'+esc(it.id)+'">重新审核</button>'+
      '</div></div>';
  }

  async function loadAiConfig(){
    try{
      const c = await api('/api/admin/ai/config');
      const autoText = c.auto_approve ? ('自动放行 ≤ ' + c.approve_threshold + ' 分') : '自动放行已关闭';
      $('aiStat').innerHTML = (c.enabled && c.has_key)
        ? '🤖 AI 审核：大模型已启用 · ' + esc(c.model || '默认模型') + ' ｜ ' + autoText + '<a href="#" id="aiToggle">修改</a>'
        : '🤖 AI 审核：本地规则引擎运行中（未接大模型）｜ ' + autoText + '<a href="#" id="aiToggle">接入大模型</a>';
      $('aiAuto').checked = !!c.auto_approve;
      $('aiThreshold').value = c.approve_threshold;
      const t = $('aiToggle');
      if(t) t.onclick = ev => {
        ev.preventDefault();
        $('aiConf').style.display = 'block';
        $('aiBase').value = c.base_url || '';
        $('aiModel').value = c.model || '';
        $('aiAuto').checked = !!c.auto_approve;
        $('aiThreshold').value = c.approve_threshold;
      };
    }catch(e){ $('aiStat').textContent = '🤖 AI 审核：不可用'; }
  }

  async function runAi(id){
    const btn = document.querySelector('[data-ai-run="'+id+'"]');
    if(btn){ btn.textContent = '审核中…'; btn.disabled = true; }
    try{ await api('/api/admin/ai/review/' + encodeURIComponent(id), {method:'POST'}); await load(); }
    catch(e){ alert('AI 审核失败：' + e.message); if(btn){ btn.textContent = '重新审核'; btn.disabled = false; } }
  }

  function applyAi(id){
    const it = items.filter(x => x.id === id)[0];
    if(!it || !it.ai) return;
    const d = it.ai.decision;
    if(d === 'approve'){ setStatus(id, 'approved'); }
    else if(d === 'reject'){ setStatus(id, 'rejected', 'AI 预审：' + (it.ai.reason || '')); }
    else { alert('AI 建议人工复核：' + (it.ai.reason || '') + '\n请自己判断后点「通过并上架」或「驳回」。'); }
  }

  // 事件
  $('btnLogin').onclick = login;
  $('pwd').onkeydown = e => { if(e.key === 'Enter') login(); };
  $('btnLogout').onclick = () => { if(confirm('确定退出登录？')) logout(false); };
  $('btnRefresh').onclick = load;
  document.addEventListener('click', function(e){
    const img = e.target.closest('.admin-photo');
    if(img && img.src){
      const v = document.getElementById('adminImgViewer');
      const vi = document.getElementById('adminImgViewerImg');
      if(v && vi){ vi.src = img.src; v.classList.add('show'); }
    }
  });
  document.addEventListener('DOMContentLoaded', function(){
    const v = document.getElementById('adminImgViewer');
    if(v) v.addEventListener('click', function(){ v.classList.remove('show'); });
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape'){
      const v = document.getElementById('adminImgViewer');
      if(v) v.classList.remove('show');
    }
  });
  $('btnDeploy').onclick = async () => {
    if(!confirm('从 GitHub 拉取最新代码并重启服务？约 10 秒生效。')) return;
    const btn = $('btnDeploy');
    btn.disabled = true; btn.textContent = '检查更新…';
    try{
      const r = await api('/api/admin/deploy', {method:'POST'});
      if(r && r.hasUpdate){
        btn.textContent = '更新中…';
        alert(r.msg || '发现新版本，正在更新');
        let n = 12;
        const tip = document.createElement('div');
        tip.id = 'deployTip';
        tip.style.cssText = 'position:fixed;right:18px;bottom:18px;background:#3b1d63;color:#fff;padding:12px 16px;border-radius:12px;font-size:13px;z-index:999;box-shadow:0 8px 24px rgba(0,0,0,.25)';
        document.body.appendChild(tip);
        const timer = setInterval(function(){
          n--;
          tip.textContent = '正在更新，' + n + ' 秒后自动刷新…';
          if(n <= 0){
            clearInterval(timer);
            api('/api/admin/deploy-log').then(function(lg){
              const t = (lg && lg.log) || '';
              if(/fatal|error|could not|failed/i.test(t)){
                tip.style.background = '#a12f2f';
                alert('更新失败，服务器日志：\n\n' + t);
              }else{
                location.reload();
              }
            }).catch(function(){ location.reload(); });
          }
        }, 1000);
        tip.textContent = '正在更新，' + n + ' 秒后自动刷新…';
      }else{
        alert((r && r.msg) || '暂无要更新的代码');
      }
    }catch(e){ alert('更新失败：' + e.message); }
    finally{ btn.disabled = false; btn.textContent = '更新代码'; }
  };
  $('btnAiAll').onclick = async () => {
    if(!confirm('对当前待审核内容跑一遍 AI 预审？')) return;
    try{ await api('/api/admin/ai/review-all', {method:'POST'}); await load(); }
    catch(e){ alert('AI 预审失败：' + e.message); }
  };
  $('aiCancel').onclick = () => { $('aiConf').style.display = 'none'; $('aiTestMsg').className = 'aitest'; };
  $('aiTest').onclick = async () => {
    const base = $('aiBase').value.trim();
    const model = $('aiModel').value.trim();
    const key = $('aiKey').value.trim();
    const msg = $('aiTestMsg');
    if(!base || !key){ msg.className = 'aitest err'; msg.textContent = '先填接口地址和 API Key'; return; }
    msg.className = 'aitest'; msg.textContent = '正在连接…（最多 25 秒）';
    try{
      const r = await api('/api/admin/ai/test', {method:'POST', body: JSON.stringify({base_url:base, model:model, api_key:key})});
      if(r.ok){
        msg.className = 'aitest ok';
        msg.textContent = '✅ 连接成功（' + r.latency + ' 秒）· 模型回复：' + (r.reply || '正常');
      } else {
        msg.className = 'aitest err';
        msg.textContent = '❌ ' + r.error;
      }
    }catch(e){
      msg.className = 'aitest err';
      msg.textContent = '❌ 测试失败：' + e.message;
    }
  };
  $('aiSave').onclick = async () => {
    const base = $('aiBase').value.trim();
    const model = $('aiModel').value.trim();
    const key = $('aiKey').value.trim();
    const auto = $('aiAuto').checked;
    const threshold = Math.max(0, Math.min(100, parseInt($('aiThreshold').value || '20', 10)));
    const msg = $('aiTestMsg');

    let hasKey = !!key;
    if(!hasKey){
      try{ const c = await api('/api/admin/ai/config'); hasKey = !!c.has_key; }catch(e){}
    }

    if(base && hasKey){
      msg.className = 'aitest'; msg.textContent = '保存前先测一下连接…（最多 25 秒）';
      try{
        const r = await api('/api/admin/ai/test', {method:'POST', body: JSON.stringify({base_url:base, model:model, api_key:key})});
        if(!r.ok){ msg.className = 'aitest err'; msg.textContent = '❌ ' + r.error + '（没有保存）'; return; }
      }catch(e){ msg.className = 'aitest err'; msg.textContent = '❌ ' + e.message + '（没有保存）'; return; }
    }

    const body = {
      enabled: !!(base && hasKey),
      base_url: base,
      model: model,
      auto_approve: auto,
      approve_threshold: threshold
    };
    if(key) body.api_key = key;

    try{
      await api('/api/admin/ai/config', {method:'POST', body: JSON.stringify(body)});
      $('aiConf').style.display = 'none';
      $('aiKey').value = '';
      msg.className = 'aitest ok';
      msg.textContent = '✅ 已保存：' + (body.enabled ? '大模型审核已启用' : '规则审核') + ' · 自动放行 ' + (auto ? ('≤ ' + threshold + ' 分') : '关闭');
      await loadAiConfig();
      await load();
    }catch(e){ alert('保存失败：' + e.message); }
  };
  $('btnReset').onclick = async () => {
    if(!confirm('确定恢复初始演示数据？现有发布记录会被清空。')) return;
    try{ await api('/api/admin/reset', {method:'POST'}); await load(); }
    catch(e){ alert(e.message); }
  };
  $('tabs').addEventListener('click', e => {
    const b = e.target.closest('button[data-tab]');
    if(!b) return;
    tab = b.getAttribute('data-tab');
    Array.prototype.forEach.call($('tabs').children, x => x.classList.remove('on'));
    b.classList.add('on');
    if(tab === 'users'){ loadAccounts(); return; }
    if(tab === 'overview'){ loadStats(); return; }
    if(tab === 'announce'){ loadAnnouncements(); return; }
    if(tab === 'phone'){ loadSpecial(); return; }
    render();
  });
  $('search').addEventListener('input', e => { keyword = e.target.value.trim(); render(); });

  $('list').addEventListener('click', e => {
    const pa = e.target.closest('[data-phone-approve]');
    if(pa){
      const id = pa.getAttribute('data-phone-approve');
      if(!confirm('确认这个号码真实存在，并加入白名单？')) return;
      api('/api/admin/items/' + encodeURIComponent(id) + '/phone-approve', {method:'POST'})
        .then(function(){ return tab === 'phone' ? loadSpecial() : load(); })
        .catch(function(err){ alert(err.message); });
      return;
    }
    const sd = e.target.closest('[data-special-del]');
    if(sd){
      const p = sd.getAttribute('data-special-del');
      if(!confirm('把 ' + p + ' 移出白名单？')) return;
      api('/api/admin/special-numbers', {method:'POST', body: JSON.stringify({phone:p, remove:true})})
        .then(loadSpecial).catch(function(err){ alert(err.message); });
      return;
    }
    const banBtn = e.target.closest('[data-ban]');
    if(banBtn){
      const id = banBtn.getAttribute('data-ban');
      const banned = banBtn.getAttribute('data-banned') === '1';
      if(!confirm(banned ? '恢复这个账号？' : '停用这个账号？其发布内容会全部下架')) return;
      api('/api/admin/accounts/' + encodeURIComponent(id) + '/ban', {
        method: 'POST', body: JSON.stringify({banned: !banned})
      }).then(loadAccounts).catch(function(err){ alert(err.message); });
      return;
    }
    const annSave = e.target.closest('[data-ann-save]');
    if(annSave){ saveAnnounce(false); return; }
    const annPub = e.target.closest('[data-ann-pub]');
    if(annPub){ saveAnnounce(true); return; }
    const annCancel = e.target.closest('[data-ann-cancel]');
    if(annCancel){ editingAnn = null; renderAnnounce(); return; }
    const annEdit = e.target.closest('[data-ann-edit]');
    if(annEdit){
      editingAnn = announcements.find(function(x){ return x.id === annEdit.getAttribute('data-ann-edit'); }) || null;
      renderAnnounce();
      return;
    }
    const annPublish = e.target.closest('[data-ann-publish]');
    if(annPublish){
      const id = annPublish.getAttribute('data-ann-publish');
      api('/api/admin/announcements/' + encodeURIComponent(id), {
        method: 'PATCH', body: JSON.stringify({status: 'published'})
      }).then(loadAnnouncements).catch(function(err){ alert(err.message); });
      return;
    }
    const annDraft = e.target.closest('[data-ann-draft]');
    if(annDraft){
      const id = annDraft.getAttribute('data-ann-draft');
      api('/api/admin/announcements/' + encodeURIComponent(id), {
        method: 'PATCH', body: JSON.stringify({status: 'draft'})
      }).then(loadAnnouncements).catch(function(err){ alert(err.message); });
      return;
    }
    const annDel = e.target.closest('[data-ann-del]');
    if(annDel){
      if(!confirm('确定删除这条公告？')) return;
      const id = annDel.getAttribute('data-ann-del');
      api('/api/admin/announcements/' + encodeURIComponent(id), {method: 'DELETE'})
        .then(loadAnnouncements).catch(function(err){ alert(err.message); });
      return;
    }
    const run = e.target.closest('[data-ai-run]');
    if(run){ runAi(run.getAttribute('data-ai-run')); return; }
    const ap = e.target.closest('[data-ai-apply]');
    if(ap){ applyAi(ap.getAttribute('data-ai-apply')); return; }
    const a = e.target.closest('[data-approve]');
    if(a){ setStatus(a.getAttribute('data-approve'), 'approved'); return; }
    const r = e.target.closest('[data-reject]');
    if(r){ const box = $('rj_' + r.getAttribute('data-reject')); if(box) box.classList.add('show'); return; }
    const ok = e.target.closest('[data-reject-ok]');
    if(ok){
      const id = ok.getAttribute('data-reject-ok');
      const ta = $('rjt_' + id);
      const reason = (ta && ta.value || '').trim();
      if(!reason){ alert('请填写驳回理由'); return; }
      setStatus(id, 'rejected', reason);
      return;
    }
    const c = e.target.closest('[data-reject-cancel]');
    if(c){ const box = $('rj_' + c.getAttribute('data-reject-cancel')); if(box) box.classList.remove('show'); return; }
  });

  if(token){ showPanel(); loadAiConfig(); load(); }
  else { showLogin(''); }
})();
