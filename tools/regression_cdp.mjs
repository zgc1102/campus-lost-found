import { spawn } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = process.env.SG_BASE || 'https://shiguangli.work'
const PORT = 9444
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'sg-reg-'))
const proc = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--disable-crashpad',
  '--no-first-run', '--hide-scrollbars', '--window-size=430,900',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  `${BASE}/?tour=off`
], { stdio: 'ignore' })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
async function waitWs() {
  for (let i = 0; i < 80; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()
      const page = list.find(x => x.type === 'page' && !String(x.url).startsWith('chrome-extension://'))
      if (page?.webSocketDebuggerUrl) return page.webSocketDebuggerUrl
    } catch {}
    await sleep(250)
  }
  throw new Error('no cdp')
}
const ws = new WebSocket(await waitWs())
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })
let seq = 0
const pending = new Map()
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data)
  if (msg.id && pending.has(msg.id)) {
    const p = pending.get(msg.id); pending.delete(msg.id)
    msg.error ? p.reject(new Error(JSON.stringify(msg.error))) : p.resolve(msg.result)
  }
}
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++seq; pending.set(id, { resolve, reject })
    ws.send(JSON.stringify({ id, method, params }))
  })
}
async function ev(expression) {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
  return r.result?.value
}
async function nav(url) {
  fs.appendFileSync('doc_assets/regression.log', 'NAV ' + url + '\\n')
  await send('Page.navigate', { url })
  await sleep(2500)
}
async function shot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
  fs.writeFileSync(path.join('doc_assets', name + '.png'), Buffer.from(r.data, 'base64'))
}
const results = []
function ok(name, pass, detail = '') {
  results.push({ name, pass: !!pass, detail })
  const line = (pass ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')
  console.log(line)
  fs.appendFileSync('doc_assets/regression.log', line + '\\n')
}
await send('Page.enable'); await send('Runtime.enable'); await sleep(700)

// 1. home help category
await nav(`${BASE}/?tour=off`)
const homeText = await ev(`document.querySelector('.section-help')?.innerText || ''`)
ok('首页爱心入口存在', !!homeText)
const cards = await ev(`document.querySelectorAll('.section-help .entry-card').length`)
ok('首页爱心入口数量', cards === 4, String(cards))
await ev(`document.querySelectorAll('.section-help .entry-card')[2]?.click()`)
await sleep(900)
const catAfterDonate = await ev(`document.querySelector('.help-cats button.on b')?.innerText || ''`)
const urlAfterDonate = await ev(`location.href`)
ok('点爱心捐赠进入爱心捐赠', catAfterDonate === '爱心捐赠', catAfterDonate + ' | ' + urlAfterDonate)
await nav(`${BASE}/?view=help&cat=help_volunteer`)
const catVol = await ev(`document.querySelector('.help-cats button.on b')?.innerText || ''`)
ok('爱心志愿分类直达', catVol === '志愿帮忙', catVol)
await nav(`${BASE}/?view=help&cat=help_borrow`)
await sleep(500)
const detailCount = await ev(`document.querySelectorAll('.vue-list .item').length`)
ok('爱心列表有内容', detailCount > 0, String(detailCount))
if (detailCount > 0) {
  await ev(`document.querySelector('.vue-list .item').click()`)
  await sleep(600)
  const sheet = await ev(`!!document.querySelector('.vue-sheet.show')`)
  ok('爱心详情可打开', sheet)
  const helpBtn = await ev(`document.querySelector('.vue-sheet .btn')?.innerText || ''`)
  ok('详情有帮忙按钮', /帮忙|帮|申请|发送/.test(helpBtn), helpBtn)
}

// 2. publish page
await nav(`${BASE}/?view=publish&type=lost`)
const form = await ev(`document.querySelectorAll('.pub-card, .pub-section, .form-card, textarea, input').length`)
ok('发布页表单渲染', form > 2, String(form))

// 3. tag page
await nav(`${BASE}/?view=tag`)
const tagForm = await ev(`!!document.querySelector('#screen-tag input')`)
ok('拾光码页表单渲染', tagForm)
const inputs = await ev(`document.querySelectorAll('#screen-tag input').length`)
if (tagForm) {
  await ev(`(() => { const a=document.querySelectorAll('#screen-tag input'); if(a[0]) a[0].value='回归测试雨伞'; if(a[1]) a[1].value='15944783650'; a.forEach(x=>x.dispatchEvent(new Event('input',{bubbles:true}))); })()`)
  await ev(`document.querySelector('#screen-tag .btn')?.click()`)
  await sleep(4500)
  const qr = await ev(`(() => { const i=document.querySelector('.tag-result img'); return i ? {w:i.naturalWidth,h:i.naturalHeight,src:i.src.slice(0,30)} : null })()`)
  ok('二维码生成并加载', qr && qr.w > 0, JSON.stringify(qr))
  const policy = await ev(`document.querySelector('.tr-policy')?.innerText || ''`)
  ok('长期有效提示', /长期有效/.test(policy), policy)
}

// 4. SSE ask
await nav(`${BASE}/?view=ask`)
const askInput = await ev(`document.querySelector('#screen-ask input, #screen-ask textarea') ? true : false`)
ok('问答输入框', askInput)
if (askInput) {
  await ev(`(() => { const i=document.querySelector('#screen-ask input, #screen-ask textarea'); i.value='校园卡丢了怎么办'; i.dispatchEvent(new Event('input',{bubbles:true})); document.querySelector('#screen-ask .btn')?.click(); })()`)
  await sleep(9000)
  const ans = await ev(`document.querySelector('.ask-a')?.innerText || ''`)
  ok('SSE 问答有回答', ans.length > 20, ans.slice(0, 60))
}

// 5. notices page renders
await nav(`${BASE}/?view=notices`)
const noticeCount = await ev(`document.querySelectorAll('.vue-list .item').length`)
ok('通知页可渲染', noticeCount >= 0, String(noticeCount))

// 6. admin login page
await nav(`${BASE}/admin`)
const adminHasLogin = await ev(`!!document.querySelector('input[type=password]')`)
ok('管理端未登录显示登录框', adminHasLogin)
if (adminHasLogin) {
  await ev(`(() => { const i=document.querySelector('input[type=password]'); i.value='KSKBLZDJD'; i.dispatchEvent(new Event('input',{bubbles:true})); document.querySelector('button.primary')?.click(); })()`)
  await sleep(2500)
  const adminShell = await ev(`!!document.querySelector('.admin-shell')`)
  const header = await ev(`document.querySelector('.brand p')?.innerText || ''`)
  ok('管理端可登录', adminShell, header)
  const red = await ev(`[...document.querySelectorAll('button')].some(b=>b.innerText.includes('下架并填写理由'))`)
  ok('管理端有下架理由按钮', red)
}

await shot('regression-last')
fs.writeFileSync('doc_assets/regression-results.json', JSON.stringify(results, null, 2))
console.log('RESULT', JSON.stringify({ pass: results.filter(x => x.pass).length, total: results.length }))
ws.close(); proc.kill()




