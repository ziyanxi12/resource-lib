import { useState, useEffect, useCallback } from 'react'
import {
  BlockOutlined, FunctionOutlined, StarOutlined, PictureOutlined, FileOutlined,
} from '@ant-design/icons'
import { Table, Radio, DatePicker, Space, message, Spin } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Pie, Column } from '@ant-design/charts'
import dayjs, { type Dayjs } from 'dayjs'
import { api } from '../api'

const STATS = [
  { key: 'component', label: '组件',  icon: <BlockOutlined />,    color: '#6366f1', bg: '#eef2ff' },
  { key: 'icon',      label: '图标',  icon: <FunctionOutlined />, color: '#0891b2', bg: '#ecfeff' },
  { key: 'illus',     label: '插画',  icon: <StarOutlined />,     color: '#d97706', bg: '#fffbeb' },
  { key: 'image',     label: '图片',  icon: <PictureOutlined />,  color: '#059669', bg: '#ecfdf5' },
  { key: 'file',      label: '文件',  icon: <FileOutlined />,     color: '#f59e0b', bg: '#fffbeb' },
]

const RESOURCE_TYPE_LABELS: Record<string, string> = {
  component: '组件',
  icon: '图标',
  illus: '插画',
  image: '图片',
  file: '文件',
  unknown: '未知',
}

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

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 28 }}>
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

      <SearchStatsSection />
    </div>
  )
}

type MetricType = 'api_call_count' | 'resource_return_count'

const METRIC_LABELS: Record<MetricType, string> = {
  api_call_count: '接口调用次数',
  resource_return_count: '资源返回数',
}

interface AppRow {
  app_id: string | null
  app_name: string
  resource_type: string
  api_call_count: number
  resource_return_count: number
}

function SearchStatsSection() {
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('year'),
    dayjs(),
  ])
  const [metric, setMetric] = useState<MetricType>('api_call_count')
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState({ api_call_count: 0, resource_return_count: 0 })
  const [pieData, setPieData] = useState<Array<{ type: string; value: number }>>([])
  const [barData, setBarData] = useState<Array<{ resource_type: string; month: string; value: number }>>([])
  const [apps, setApps] = useState<AppRow[]>([])

  const fetchData = useCallback((range?: [Dayjs, Dayjs]) => {
    const [start, end] = range ?? dateRange
    setLoading(true)
    api.getSearchStats({
      start_date: start.format('YYYY-MM-DD'),
      end_date: end.format('YYYY-MM-DD'),
    }).then(data => {
      setSummary(data.summary)
      setPieData(
        data.pie.map(d => ({
          type: RESOURCE_TYPE_LABELS[d.resource_type] ?? d.resource_type,
          value: d[metric],
        }))
      )
      setBarData(
        data.bar.map(d => ({
          resource_type: RESOURCE_TYPE_LABELS[d.resource_type] ?? d.resource_type,
          month: d.month,
          value: d[metric],
        }))
      )
      setApps(data.apps)
    }).catch(err => {
      message.error(err.message || '加载统计数据失败')
    }).finally(() => setLoading(false))
  }, [dateRange, metric])

  useEffect(() => {
    fetchData()
  }, [])

  const handleMetricChange = (m: MetricType) => {
    setMetric(m)
    const [start, end] = dateRange
    setLoading(true)
    api.getSearchStats({
      start_date: start.format('YYYY-MM-DD'),
      end_date: end.format('YYYY-MM-DD'),
    }).then(data => {
      setPieData(
        data.pie.map(d => ({
          type: RESOURCE_TYPE_LABELS[d.resource_type] ?? d.resource_type,
          value: d[m],
        }))
      )
      setBarData(
        data.bar.map(d => ({
          resource_type: RESOURCE_TYPE_LABELS[d.resource_type] ?? d.resource_type,
          month: d.month,
          value: d[m],
        }))
      )
    }).catch(err => {
      message.error(err.message || '加载统计数据失败')
    }).finally(() => setLoading(false))
  }

  const appColumns: ColumnsType<AppRow> = [
    {
      title: 'AppID', dataIndex: 'app_id', width: 200,
      render: (v: string | null) => v ?? <span style={{ color: '#94a3b8' }}>—</span>,
    },
    { title: '应用名称', dataIndex: 'app_name', width: 140 },
    {
      title: '调用类型', dataIndex: 'resource_type', width: 100,
      render: (v: string) => RESOURCE_TYPE_LABELS[v] ?? v,
    },
    {
      title: '接口调用次数', dataIndex: 'api_call_count', width: 120,
      sorter: (a, b) => a.api_call_count - b.api_call_count,
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: '资源返回数', dataIndex: 'resource_return_count', width: 120,
      sorter: (a, b) => a.resource_return_count - b.resource_return_count,
      render: (v: number) => v.toLocaleString(),
    },
  ]

  const pieConfig = {
    data: pieData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.9,
    label: {
      text: 'type',
      position: 'outside' as const,
      connector: true,
    },
    legend: {
      color: {
        position: 'right' as const,
      },
    },
    tooltip: (d: { type: string; value: number }) => ({
      title: d.type,
      items: [{ value: d.value, name: '数量' }],
    }),
    height: 300,
  }

  const columnConfig = {
    data: barData,
    xField: 'month',
    yField: 'value',
    colorField: 'resource_type',
    stack: true,
    maxWidth: 40,
    legend: {
      color: {
        position: 'right' as const,
      },
    },
    tooltip: (d: { resource_type: string; month: string; value: number }) => ({
      title: d.month,
      items: [{ name: d.resource_type, value: d.value }],
    }),
    axis: {
      y: {
        title: METRIC_LABELS[metric],
        labelFormatter: (v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v),
      },
    },
    height: 300,
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#0f172a' }}>调用统计</h2>
        <Space wrap>
          <DatePicker.RangePicker
            value={dateRange}
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                const range: [Dayjs, Dayjs] = [dates[0], dates[1]]
                setDateRange(range)
                fetchData(range)
              }
            }}
          />
          <Radio.Group
            value={metric}
            onChange={e => handleMetricChange(e.target.value)}
            optionType="button"
            buttonStyle="solid"
          >
            <Radio.Button value="api_call_count">接口调用次数</Radio.Button>
            <Radio.Button value="resource_return_count">资源返回数</Radio.Button>
          </Radio.Group>
        </Space>
      </div>

      <Spin spinning={loading}>
        <div style={{ display: 'flex', gap: 32, marginBottom: 24 }}>
          <div style={{
            background: '#fff', borderRadius: 12, padding: '20px 28px',
            border: '1px solid #e2e8f0', flex: 1, textAlign: 'center',
          }}>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>接口调用次数</div>
            <div style={{ fontSize: 32, fontWeight: 800, color: '#6366f1' }}>
              {summary.api_call_count.toLocaleString()}
            </div>
          </div>
          <div style={{
            background: '#fff', borderRadius: 12, padding: '20px 28px',
            border: '1px solid #e2e8f0', flex: 1, textAlign: 'center',
          }}>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>资源返回数</div>
            <div style={{ fontSize: 32, fontWeight: 800, color: '#0891b2' }}>
              {summary.resource_return_count.toLocaleString()}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          <div style={{
            background: '#fff', borderRadius: 12, padding: 16,
            border: '1px solid #e2e8f0', flex: 1, minWidth: 0,
          }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: '#475569' }}>
              各类资源占比
            </h3>
            <Pie {...pieConfig} />
          </div>
          <div style={{
            background: '#fff', borderRadius: 12, padding: 16,
            border: '1px solid #e2e8f0', flex: 1.5, minWidth: 0,
          }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: '#475569' }}>
              各类资源按月分布
            </h3>
            <Column {...columnConfig} />
          </div>
        </div>

        <div style={{
          background: '#fff', borderRadius: 12, padding: 16,
          border: '1px solid #e2e8f0',
        }}>
          <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: '#475569' }}>
            三方调用详情
          </h3>
          <Table<AppRow>
            rowKey={(r) => `${r.app_id ?? 'anonymous'}-${r.resource_type}`}
            size="small"
            columns={appColumns}
            dataSource={apps}
            pagination={false}
            scroll={{ x: 'max-content' }}
          />
        </div>
      </Spin>
    </div>
  )
}
