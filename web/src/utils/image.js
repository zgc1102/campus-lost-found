export async function compressImage(file, maxSide = 1400, quality = 0.78) {
  if (!file || !/^image\//.test(file.type)) throw new Error('请选择图片文件')
  if (file.size > 15 * 1024 * 1024) throw new Error('图片太大，请选择 15MB 以内的照片')
  let bitmap = null
  try {
    if (typeof createImageBitmap === 'function') {
      bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
    }
  } catch (_) {}
  if (!bitmap) {
    bitmap = await new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = () => reject(new Error('图片读取失败'))
      img.src = URL.createObjectURL(file)
    })
  }
  const w = bitmap.width || bitmap.naturalWidth
  const h = bitmap.height || bitmap.naturalHeight
  const scale = Math.min(1, maxSide / Math.max(w, h))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(w * scale))
  canvas.height = Math.max(1, Math.round(h * scale))
  const ctx = canvas.getContext('2d')
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  const out = canvas.toDataURL('image/jpeg', quality)
  if (out.length > 1_800_000) {
    return canvas.toDataURL('image/jpeg', 0.6)
  }
  return out
}
