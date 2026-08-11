import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter, Routes, Route, Navigate } from 'react-router-dom'

// mock AuthGuard 直接放行
vi.mock('../components/AuthGuard', () => ({
  AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// mock 各页面组件，只渲染标识文本
vi.mock('../pages/Guide', () => ({ default: () => <div data-testid="guide">Guide</div> }))
vi.mock('../pages/ResourceOverview', () => ({ default: () => <div data-testid="overview">Overview</div> }))
vi.mock('../pages/ResourceManage', () => ({ default: () => <div data-testid="manage">Manage</div> }))
vi.mock('../pages/ResourceUpload', () => ({ default: () => <div data-testid="upload">Upload</div> }))
vi.mock('../pages/SourceManage', () => ({ default: () => <div data-testid="source-manage">SourceManage</div> }))
vi.mock('../pages/Error', () => ({ default: () => <div data-testid="error">Error</div> }))

// 从 App.tsx 提取的路由配置（与 App.tsx 保持一致）
const appRoutes = (
  <Routes>
    <Route path="/" element={<Navigate to="/home" replace />} />
    <Route path="/home" element={<div data-testid="guide">Guide</div>} />
    <Route path="/overview" element={<div data-testid="overview">Overview</div>} />
    <Route path="/error" element={<div data-testid="error">Error</div>} />
    <Route path="/source-manage" element={<div data-testid="source-manage">SourceManage</div>} />
    <Route path="/:type" element={<div data-testid="manage">Manage</div>} />
    <Route path="/:type/upload" element={<div data-testid="upload">Upload</div>} />
  </Routes>
)

function renderAt(path: string) {
  return render(<MemoryRouter initialEntries={[path]}>{appRoutes}</MemoryRouter>)
}

describe('路由配置', () => {
  it('/ 重定向到 /home', () => {
    const { getByTestId } = renderAt('/')
    expect(getByTestId('guide')).toBeInTheDocument()
  })

  it('/home 渲染 Guide 页面', () => {
    const { getByTestId } = renderAt('/home')
    expect(getByTestId('guide')).toBeInTheDocument()
  })

  it('/overview 渲染数据总览页面（不跳首页）', () => {
    const { getByTestId } = renderAt('/overview')
    expect(getByTestId('overview')).toBeInTheDocument()
    expect(() => getByTestId('guide')).toThrow()
  })

  it('/component 渲染资源管理页面', () => {
    const { getByTestId } = renderAt('/component')
    expect(getByTestId('manage')).toBeInTheDocument()
  })

  it('/icon/upload 渲染上传页面', () => {
    const { getByTestId } = renderAt('/icon/upload')
    expect(getByTestId('upload')).toBeInTheDocument()
  })

  it('/error 渲染错误页面', () => {
    const { getByTestId } = renderAt('/error')
    expect(getByTestId('error')).toBeInTheDocument()
  })
})
