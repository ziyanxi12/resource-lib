import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

// mock marked 只返回简单 HTML
vi.mock('marked', () => ({
  marked: {
    parse: (src: string) => src,
    setOptions: () => {},
  },
}))

// mock fetch 返回测试用 MD 内容
const MOCK_MD = '# 标题1\n\n## 1. 系统简介\n\n正文内容\n\n## 2. 登录\n\n<a href="#1-系统简介">系统简介</a>'
vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({
  ok: true,
  text: () => Promise.resolve(MOCK_MD),
})))

import { slugify, addHeadingIds } from '../pages/Guide'

describe('slugify', () => {
  it('英文转小写 + 空格转连字符', () => {
    expect(slugify('Hello World')).toBe('hello-world')
  })

  it('保留中文', () => {
    expect(slugify('1. 系统简介')).toBe('1-系统简介')
  })

  it('去除标点符号', () => {
    expect(slugify('附录 A：测试！')).toBe('附录-a测试')
  })

  it('空字符串', () => {
    expect(slugify('')).toBe('')
  })

  it('多余空格合并', () => {
    expect(slugify('a   b')).toBe('a-b')
  })
})

describe('addHeadingIds', () => {
  it('给 h1-h6 添加 id', () => {
    const html = '<h1>标题</h1><h2>子标题</h2><p>正文</p>'
    const result = addHeadingIds(html)
    expect(result).toContain('id="标题"')
    expect(result).toContain('id="子标题"')
  })

  it('中文标题 id 正确', () => {
    const html = '<h2>1. 系统简介</h2>'
    const result = addHeadingIds(html)
    expect(result).toContain('id="1-系统简介"')
  })

  it('没有标题时原样返回', () => {
    const html = '<p>只有段落</p>'
    const result = addHeadingIds(html)
    expect(result).toBe('<p>只有段落</p>')
  })
})

describe('Guide 组件 — 锚点点击', () => {
  it('点击 # 锚点不修改 window.location.hash', async () => {
    const { default: Guide } = await import('../pages/Guide')
    render(<Guide />)

    // 等待异步 fetch 完成后渲染
    const link = await screen.findByText('系统简介')
    fireEvent.click(link)

    // hash 应保持不变（不会被改成 #1-系统简介 破坏路由）
    expect(window.location.hash).not.toContain('系统简介')
  })
})
