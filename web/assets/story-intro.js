(function () {
  'use strict'
  var root = document.getElementById('story')
  if (!root) return
  var force = new URLSearchParams(location.search).get('intro') === '1'
  var admin = location.pathname.replace(/\/+$/, '') === '/admin'
  var seen = false
  try { seen = localStorage.getItem('sg:story:v1') === '1' } catch (e) {}
  if (admin) { root.parentNode.removeChild(root); return }
  var returning = seen && !force

  var scenes = Array.prototype.slice.call(root.querySelectorAll('.story-scene'))
  var dots = Array.prototype.slice.call(root.querySelectorAll('#story-dots i'))
  var progress = document.getElementById('story-progress')
  var nextBtn = document.getElementById('story-next')
  var toast = document.getElementById('story-toast')
  var durations = [4300, 4500, 4500, 4500, 6500]
  var step = 0
  var timer = null
  var closed = false
  var appReady = false
  var started = false

  function clearTimer() { if (timer) clearTimeout(timer); timer = null }
  function close() {
    if (closed) return
    closed = true
    clearTimer()
    try { localStorage.setItem('sg:story:v1', '1') } catch (e) {}
    document.body.style.overflow = ''
    root.classList.add('leaving')
    setTimeout(function () { if (root.parentNode) root.parentNode.removeChild(root) }, 600)
  }
  function toastOn(text) {
    if (!toast || closed) return
    toast.textContent = text
    root.classList.add('toast-on')
  }
  function toastOff() { root.classList.remove('toast-on') }
  function show(n) {
    step = Math.max(0, Math.min(scenes.length - 1, n))
    clearTimer()
    scenes.forEach(function (s, i) { s.classList.toggle('on', i === step) })
    dots.forEach(function (d, i) { d.classList.toggle('on', i === step) })
    root.setAttribute('data-act', String(step + 1))
    progress.style.width = ((step + 1) / scenes.length * 100) + '%'
    nextBtn.textContent = step === scenes.length - 1 ? '进入拾光里' : '下一步'
    toastOff()
    timer = setTimeout(function () {
      if (closed) return
      if (step === scenes.length - 1) {
        if (appReady) close()
        else { toastOn('暂时还没加载成功，请稍等一下…'); show(0) }
      } else {
        show(step + 1)
      }
    }, durations[step])
  }
  function next() {
    if (closed) return
    if (step === scenes.length - 1) { close(); return }
    show(step + 1)
  }
  function onReady() {
    appReady = true
    // 回访用户如果开场尚未开始，直接进入首页，不播放。
    if (returning && !started) { close(); return }
  }
  function startDeck() {
    if (started || closed) return
    started = true
    document.body.style.overflow = 'hidden'
    show(0)
  }

  document.getElementById('story-skip').addEventListener('click', close)
  document.getElementById('story-enter').addEventListener('click', close)
  nextBtn.addEventListener('click', next)
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close()
    if (e.key === 'ArrowRight') next()
  })
  window.addEventListener('sg:app-ready', onReady, { once: true })

  document.body.style.overflow = 'hidden'
  setTimeout(function () {
    if (returning) {
      if (appReady) { close(); return }
      // 回访用户先给首页 1 秒；如果还是没加载好，再用分镜挡住。
      setTimeout(function () { if (!appReady) startDeck() }, 1000)
    } else {
      startDeck()
    }
  }, 300)
})()
