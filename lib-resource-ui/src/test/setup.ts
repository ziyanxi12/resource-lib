import '@testing-library/jest-dom/vitest'
import { beforeEach } from 'vitest'

// jsdom 不原生支持 matchMedia，antd 需要
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })
}

// jsdom 不原生支持 IntersectionObserver
if (!window.IntersectionObserver) {
  window.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() { return [] }
  } as any
}

// jsdom 不原生支持 scrollIntoView
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}

// 每个测试前清理 localStorage
beforeEach(() => {
  localStorage.clear()
})
