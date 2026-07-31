import { useState, useEffect } from 'react'
import {
  BlockOutlined, FunctionOutlined, StarOutlined, PictureOutlined, FileOutlined,
} from '@ant-design/icons'
import { Table, Tag, Switch, Button, Space, Input, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { ReloadOutlined } from '@ant-design/icons'
import { api } from '../api'

const STATS = [
  { key: 'component', label: '组件',  icon: <BlockOutlined />,    color: '#6366f1', bg: '#eef2ff' },
  { key: 'icon',      label: '图标',  icon: <FunctionOutlined />, color: '#0891b2', bg: '#ecfeff' },
  { key: 'illus',     label: '插画',  icon: <StarOutlined />,     color: '#d97706', bg: '#fffbeb' },
  { key: 'image',     label: '图片',  icon: <PictureOutlined />,  color: '#059669', bg: '#ecfdf5' },
  { key: 'file',      label: '文件',  icon: <FileOutlined />,     color: '#f59e0b', bg: '#fffbeb' },
]

function StatCard({
  label, icon, color, bg, count,
}: {
  label: string; icon: React.ReactNode; color: string; bg: string; count: number | null
}) {
  const [hov, setHov] = useState(false)
  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? bg : '#fff',
        borderRadius: 14,
        border: `1.5px solid ${hov ? color : '#e2e8f0'}`,
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        flex: 1,
        cursor: 'default',
        transition: 'all 0.18s ease',
        boxShadow: hov ? `0 4px 20px ${color}22` : '0 1px 3px rgba(0,0,0,0.04)',
        transform: hov ? 'translateY(-2px)' : 'none',
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: 13,
          background: hov ? color : bg,
          color: hov ? '#fff' : color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 22,
          flexShrink: 0,
          transition: 'all 0.18s',
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 28, fontWeight: 800, color: hov ? color : '#0f172a', lineHeight: 1.1, transition: 'color 0.18s' }}>
          {count ?? '—'}
        </div>
        <div style={{ fontSize: 14, color: hov ? color : '#64748b', marginTop: 4, fontWeight: hov ? 600 : 400, whiteSpace: 'nowrap' }}>
          {label}
        </div>
      </div>
    </div>
  )
}

export default function ResourceOverview() {
  const [counts, setCounts] = useState<Record<string, number>>({})

  useEffect(() => {
    Promise.all(
      STATS.map(s =>
        api.listResources({ type: s.key, limit: 1 })
          .then(d => ({ key: s.key, total: d.total as number }))
          .catch(() => ({ key: s.key, total: 0 }))
      )
    ).then(results => {
      const m: Record<string, number> = {}
      results.forEach(r => { m[r.key] = r.total })
      setCounts(m)
    })
  }, [])

  return (
    <div style={{ flex: 1, overflowY: 'auto', minHeight: 0, minWidth: 0, paddingTop: 4, paddingBottom: 8 }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>数据总览</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>五类设计资源的当前数量</p>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {STATS.map(s => (
          <StatCard
            key={s.key}
            label={s.label}
            icon={s.icon}
            color={s.color}
            bg={s.bg}
            count={counts[s.key] ?? null}
          />
        ))}
      </div>

      <SearchLogSection />
    </div>
  )
}

function jsonPreview(val: unknown): string {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

const SEARCH_LOG_COLUMNS: ColumnsType<Record<string, unknown>> = [
  { title: 'ID', dataIndex: 'id', width: 60, fixed: 'left' },
  {
    title: '创建时间', dataIndex: 'created_at', width: 180, fixed: 'left',
    render: (v: string) => v ?? '—',
  },
  {
    title: '状态', dataIndex: 'status', width: 90,
    render: (v: string) => v === 'success'
      ? <Tag color="green">success</Tag>
      : <Tag color="red">{v ?? '—'}</Tag>,
  },
  { title: '资源类型', dataIndex: 'resource_type', width: 120, render: (v) => v ?? '—' },
  { title: '搜索模式', dataIndex: 'search_mode', width: 110, render: (v) => v ?? '—' },
  { title: '响应模式', dataIndex: 'response_mode', width: 120, render: (v) => v ?? '—' },
  { title: '返回数量', dataIndex: 'top_k', width: 90, render: (v) => v ?? '—' },
  { title: '混合权重', dataIndex: 'hybrid_weight', width: 100, render: (v) => v ?? '—' },
  { title: '查询词数', dataIndex: 'query_count', width: 90, render: (v) => v ?? '—' },
  { title: '查询词', dataIndex: 'queries', width: 220, render: jsonPreview },
  { title: '过滤条件', dataIndex: 'filters', width: 220, render: jsonPreview },
  { title: '命中数量', dataIndex: 'result_count', width: 90, render: (v) => v ?? '—' },
  { title: '命中ID', dataIndex: 'result_ids', width: 220, render: jsonPreview },
  { title: '最高分', dataIndex: 'top_score', width: 90, render: (v) => v ?? '—' },
  { title: '结果集', dataIndex: 'results', width: 260, render: jsonPreview },
  { title: 'HTTP状态码', dataIndex: 'http_status', width: 110, render: (v) => v ?? '—' },
  { title: '错误信息', dataIndex: 'error_message', width: 200, render: (v) => v ?? '—' },
  { title: '耗时(ms)', dataIndex: 'duration_ms', width: 90, render: (v) => v ?? '—' },
  { title: '客户端IP', dataIndex: 'client_ip', width: 130, render: (v) => v ?? '—' },
  { title: '应用ID', dataIndex: 'app_id', width: 130, render: (v) => v ?? '—' },
  { title: '用户代理', dataIndex: 'user_agent', width: 220, render: (v) => v ?? '—' },
  { title: '来源页', dataIndex: 'referer', width: 220, render: (v) => v ?? '—' },
  { title: '请求ID', dataIndex: 'request_id', width: 280, render: (v) => v ?? '—' },
  { title: '接口路径', dataIndex: 'api_path', width: 160, render: (v) => v ?? '—' },
]

function SearchLogSection() {
  const [items, setItems] = useState<Record<string, unknown>[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [includeResults, setIncludeResults] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  const fetchLogs = (p = page, incRes = includeResults, st = statusFilter, rt = typeFilter) => {
    setLoading(true)
    api.getSearchLogs({
      page: p,
      limit: 20,
      include_results: incRes,
      ...(st ? { status: st } : {}),
      ...(rt ? { resource_type: rt } : {}),
    }).then(data => {
      setItems(data.items)
      setTotal(data.total)
      setPage(data.page)
    }).catch(err => {
      message.error(err.message || '加载搜索日志失败')
    }).finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchLogs(1)
  }, [])

  return (
    <div style={{ marginTop: 32 }}>
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#0f172a' }}>
          搜索日志采集预览
          <span style={{ fontSize: 13, color: '#94a3b8', fontWeight: 400, marginLeft: 8 }}>
            vector_search_logs 表 · 共 {total} 条
          </span>
        </h2>
        <Space wrap>
          <Input
            placeholder="状态 (success/error)"
            allowClear
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            style={{ width: 180 }}
            onPressEnter={() => fetchLogs(1)}
          />
          <Input
            placeholder="资源类型"
            allowClear
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            style={{ width: 150 }}
            onPressEnter={() => fetchLogs(1)}
          />
          <Space>
            <span style={{ fontSize: 13, color: '#64748b' }}>包含完整 results</span>
            <Switch
              checked={includeResults}
              onChange={(checked) => {
                setIncludeResults(checked)
                fetchLogs(page, checked)
              }}
            />
          </Space>
          <Button icon={<ReloadOutlined />} onClick={() => fetchLogs(page)}>刷新</Button>
        </Space>
      </div>

      <Table<Record<string, unknown>>
        rowKey="id"
        size="small"
        loading={loading}
        columns={SEARCH_LOG_COLUMNS}
        dataSource={items}
        scroll={{ x: 'max-content', y: 600 }}
        pagination={{
          current: page,
          pageSize: 20,
          total,
          showSizeChanger: false,
          onChange: (p) => fetchLogs(p),
        }}
        bordered
      />
    </div>
  )
}
