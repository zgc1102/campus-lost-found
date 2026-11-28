(function () {
  'use strict'
  var root = document.getElementById('intro-tour')
  if (!root) return
  var force = new URLSearchParams(location.search).get('intro') === '1'
  var admin = location.pathname.replace(/\/+$/, '') === '/admin'
  var seen = false
  try { seen = localStorage.getItem('sg:tour:v1') === '1' } catch (e) {}
  if (admin || (!force && seen)) {
    root.parentNode.removeChild(root)
    return
  }

  var steps = [
    {
      screen: 'problem',
      target: '[data-target="problem"]',
      title: '东西丢了，先别急',
      text: '拾光里会把寻物和招领放在同一个地方，让捡到的人更容易找到失主。',
      tip: '跟着光标看：先认识问题，再看怎么发布。',
      wait: 4400
    },
    {
      screen: 'home',
      target: '[data-target="publish"]',
      title: '第一步：发布一条',
      text: '点这里发布。丢失的东西选“寻物启事”，捡到的东西选“失物招领”。',
      tip: '标题、地点、时间写清楚，别人才能判断是不是自己的。',
      wait: 5000
    },
    {
      screen: 'publish',
      target: '[data-target="feature"]',
      title: '第二步：留一个“只有失主知道”的特征',
      text: '颜色、划痕、贴纸、里面放了什么，这些细节比“我的东西”更有用。',
      tip: '不要把所有特征都写出来，留一点给认领时核对。',
      wait: 5200
    },
    {
      screen: 'ai',
      target: '[data-target="ai"]',
      title: 'AI 先帮你看一遍',
      text: '发布后，AI 会检查内容是否属于校园失物招领，识别广告、诈骗和隐私风险。',
      tip: 'AI 只做辅助；有疑问的内容会进入人工复核。',
      wait: 5200
    },
    {
      screen: 'match',
      target: '[data-target="match"]',
      title: 'AI 匹配：把两条信息放到一起',
      text: '系统会把相似的寻物和招领放在一起，告诉你哪些特征对上了。',
      tip: '匹配只是线索，最终仍然要核对实物和独有特征。',
      wait: 5600
    },
    {
      screen: 'claim',
      target: '[data-target="privacy"]',
      title: '认领前，先核对',
      text: '不是谁先点认领就归谁。答对独有特征，才进入下一步。',
      tip: '手机号默认打码，核对通过后才交换，避免被骚扰。',
      wait: 5400
    },
    {
      screen: 'final',
      target: '[data-target="final"]',
      title: '让每件失物，都有回家的路',
      text: '拾光里是校园公益项目，不交易、不收费。感谢国城控股集团与中基控股集团的支持。',
      tip: '现在可以进入拾光里，自己试一次。',
      wait: 7500
    }
  ]

  var step = 0
  var timer = null
  var closed = false
  var screens = Array.prototype.slice.call(root.querySelectorAll('.tour-screen'))
  var ring = document.getElementById('tour-ring')
  var cursor = document.getElementById('tour-cursor')
  var callout = document.getElementById('tour-callout')
  var stepNo = document.getElementById('tour-stepno')
  var title = document.getElementById('tour-title')
  var text = document.getElementById('tour-text')
  var tip = document.getElementById('tour-tip')
  var progress = document.getElementById('tour-progress')
  var count = document.getElementById('tour-count')
  var nextBtn = document.getElementById('tour-next')
  var prevBtn = document.getElementById('tour-prev')
  var device = root.querySelector('.tour-device')

  function clearTimer() {
    if (timer) clearTimeout(timer)
    timer = null
  }

  function close() {
    if (closed) return
    closed = true
    clearTimer()
    try { localStorage.setItem('sg:tour:v1', '1') } catch (e) {}
    document.body.style.overflow = ''
    root.classList.add('leaving')
    setTimeout(function () { if (root.parentNode) root.parentNode.removeChild(root) }, 600)
  }

  function setCallout(on) {
    callout.classList.toggle('on', on)
  }

  function position() {
    var target = root.querySelector(steps[step].target)
    if (!target || !device) return
    var d = device.getBoundingClientRect()
    var r = target.getBoundingClientRect()
    if (r.width < 2 || r.height < 2) return
    var pad = 5
    ring.style.left = (r.left - d.left - pad) + 'px'
    ring.style.top = (r.top - d.top - pad) + 'px'
    ring.style.width = (r.width + pad * 2) + 'px'
    ring.style.height = (r.height + pad * 2) + 'px'
    ring.style.opacity = '1'
    var cx = r.left - d.left + Math.min(r.width - 6, Math.max(10, r.width * .74))
    var cy = r.top - d.top + Math.min(r.height - 4, r.height * .68)
    cursor.style.transform = 'translate(' + cx + 'px,' + cy + 'px)'
    cursor.style.opacity = '1'
  }

  function show(n, manual) {
    step = Math.max(0, Math.min(steps.length - 1, n))
    var s = steps[step]
    clearTimer()
    screens.forEach(function (screen) {
      screen.classList.toggle('on', screen.getAttribute('data-screen') === s.screen)
    })
    root.setAttribute('data-step', String(step))
    stepNo.textContent = String(step + 1).padStart(2, '0') + ' / ' + String(steps.length).padStart(2, '0')
    title.textContent = s.title
    text.textContent = s.text
    tip.textContent = s.tip
    progress.style.width = ((step + 1) / steps.length * 100) + '%'
    count.textContent = (step + 1) + ' / ' + steps.length
    prevBtn.disabled = step === 0
    nextBtn.textContent = step === steps.length - 1 ? '进入拾光里' : '下一步'
    setCallout(false)
    ring.style.opacity = '0'
    cursor.style.opacity = '0'
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        position()
        setCallout(true)
      })
    })
    timer = setTimeout(function () {
      if (step < steps.length - 1) show(step + 1, false)
      else close()
    }, s.wait || 5000)
  }

  function next() { if (step < steps.length - 1) show(step + 1, true); else close() }
  function prev() { if (step > 0) show(step - 1, true) }

  document.getElementById('tour-skip').addEventListener('click', close)
  nextBtn.addEventListener('click', next)
  prevBtn.addEventListener('click', prev)
  document.getElementById('tour-enter').addEventListener('click', close)
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close()
    if (e.key === 'ArrowRight') next()
    if (e.key === 'ArrowLeft') prev()
  })
  window.addEventListener('resize', function () { requestAnimationFrame(position) })

  document.body.style.overflow = 'hidden'
  setTimeout(function () { if (!closed) show(0, false) }, 350)
})()
