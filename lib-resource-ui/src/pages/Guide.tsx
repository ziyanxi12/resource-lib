import { useEffect, useState, useRef } from 'react'
import { Spin } from 'antd'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
})

export function slugify(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[—–\-]/g, ' ')
    .replace(/[^\w\s\u4e00-\u9fff]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

export function addHeadingIds(html: string): string {
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const headings = doc.querySelectorAll('h1, h2, h3, h4, h5, h6')
  const slugMap = new Map<string, string>()

  headings.forEach(h => {
    const id = slugify(h.textContent || '')
    h.id = id
    slugMap.set(h.textContent?.trim() || '', id)
  })

  doc.querySelectorAll('a[href^="#"]').forEach(a => {
    const href = a.getAttribute('href') || ''
    if (href.length <= 1) return
    const rawId = decodeURIComponent(href.slice(1))

    if (doc.getElementById(rawId)) return

    const normalized = rawId.replace(/-+/g, '-')
    if (doc.getElementById(normalized)) {
      a.setAttribute('href', '#' + normalized)
      return
    }

    const linkText = (a.textContent || '').trim()
    for (const [hText, id] of slugMap) {
      if (hText.includes(linkText) || linkText.includes(hText)) {
        a.setAttribute('href', '#' + id)
        return
      }
    }
  })

  return doc.body.innerHTML
}

const css = `
.guide-body {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 40px 80px;
  font-size: 14px;
  line-height: 1.8;
  color: #1e293b;
}
.guide-body h1 {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
  padding-bottom: 16px;
  border-bottom: 2px solid #6366f1;
  color: #0f172a;
}
.guide-body h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 40px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
  color: #1e293b;
}
.guide-body h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 28px 0 12px;
  color: #334155;
}
.guide-body h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 20px 0 8px;
  color: #475569;
}
.guide-body p { margin: 8px 0; }
.guide-body ul, .guide-body ol {
  padding-left: 24px;
  margin: 8px 0;
}
.guide-body li { margin: 4px 0; }
.guide-body a {
  color: #6366f1;
  text-decoration: none;
}
.guide-body a:hover { text-decoration: underline; }
.guide-body blockquote {
  margin: 12px 0;
  padding: 10px 16px;
  border-left: 4px solid #6366f1;
  background: #f8fafc;
  color: #475569;
  border-radius: 0 6px 6px 0;
}
.guide-body code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  color: #db2777;
}
.guide-body pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px 20px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.6;
}
.guide-body pre code {
  background: none;
  color: inherit;
  padding: 0;
}
.guide-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}
.guide-body th {
  background: #f8fafc;
  font-weight: 600;
  text-align: left;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
}
.guide-body td {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  vertical-align: top;
}
.guide-body tr:nth-child(even) td {
  background: #fafbfc;
}
.guide-body hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 32px 0;
}
.guide-body strong { font-weight: 600; color: #0f172a; }
`

export default function Guide() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [html, setHtml] = useState('')

  useEffect(() => {
    let cancelled = false
    fetch(`${import.meta.env.BASE_URL}USER_GUIDE.md`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.text()
      })
      .then(text => {
        if (cancelled) return
        setHtml(addHeadingIds(marked.parse(text) as string))
      })
      .catch(() => {
        if (cancelled) return
        setHtml('<p style="color:#94a3b8;padding:32px">加载指南内容失败</p>')
      })
    return () => { cancelled = true }
  }, [])

  const handleClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement
    const anchor = target.closest('a')
    if (!anchor) return
    const href = anchor.getAttribute('href')
    if (!href || !href.startsWith('#')) return
    e.preventDefault()
    const id = decodeURIComponent(href.slice(1))
    if (!id) return
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div ref={containerRef} style={{ height: '100%', overflowY: 'auto', background: '#fff' }}>
      <style>{css}</style>
      {html ? (
        <div className="guide-body" dangerouslySetInnerHTML={{ __html: html }} onClick={handleClick} />
      ) : (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
          <Spin tip="加载中..." />
        </div>
      )}
    </div>
  )
}
