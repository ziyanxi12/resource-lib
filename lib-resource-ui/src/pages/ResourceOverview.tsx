import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  BlockOutlined, FunctionOutlined, StarOutlined, PictureOutlined, FileOutlined,
} from '@ant-design/icons'
import { Table, Radio, DatePicker, Space, message, Spin } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Pie, Column } from '@ant-design/charts'
import dayjs, { type Dayjs } from 'dayjs'
import { api } from '../api'

const STATS = [
  { key: 'component', label: '组件',  icon: <BlockOutlined />,    bg: '#f2effe', color: '#715AFB' },
  { key: 'icon',      label: '图标',  icon: <FunctionOutlined />, bg: '#e8f1fe', color: '#2070F3' },
  { key: 'illus',     label: '插画',  icon: <StarOutlined />,     bg: '#fff5ea', color: '#F69E39' },
  { key: 'image',     label: '图片',  icon: <PictureOutlined />,  bg: '#eef8e4', color: '#62B42E' },
  { key: 'file',      label: '文件',  icon: <FileOutlined />,     bg: '#e6f7f8', color: '#2CBBC9' },
]

const RESOURCE_TYPE_LABELS: Record<string, string> = {
  component: '组件',
  icon: '图标',
  illus: '插画',
  image: '图片',
  file: '文件',
  unknown: '未知',
}

const EXTRA_COLOR_PALETTE = ['#94a3b8', '#a78bfa', '#22d3ee', '#fb923c', '#a3e635', '#f472b6', '#64748b', '#f43f5e']

function buildColorScale(types: string[]): { domain: string[]; range: string[] } {
  const present = new Set(types)
  const colorMap: Record<string, string> = {}
  STATS.forEach(s => { colorMap[RESOURCE_TYPE_LABELS[s.key]] = s.color })

  const domain: string[] = []
  const range: string[] = []

  for (const s of STATS) {
    const label = RESOURCE_TYPE_LABELS[s.key]
    if (present.has(label)) {
      domain.push(label)
      range.push(s.color)
    }
  }

  let paletteIdx = 0
  for (const t of present) {
    if (!colorMap[t]) {
      const c = EXTRA_COLOR_PALETTE[paletteIdx++ % EXTRA_COLOR_PALETTE.length]
      colorMap[t] = c
      domain.push(t)
      range.push(c)
    }
  }

  return { domain, range }
}

function StatCard({
  label, icon, color, bg, count,
}: {
  label: string; icon: React.ReactNode; color: string; bg: string; count: number | null
}) {
  return (
    <div
      style={{
        background: '#fff',
        borderRadius: 14,
        border: '1.5px solid #e2e8f0',
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        flex: 1,
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: 13,
          background: bg,
          color: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 22,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>
          {count ?? '—'}
        </div>
        <div style={{ fontSize: 14, color: '#64748b', marginTop: 4, whiteSpace: 'nowrap' }}>
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

type Granularity = 'day' | 'week' | 'month'

const GRANULARITY_LABELS: Record<Granularity, string> = {
  day: '天',
  week: '周',
  month: '月',
}

interface AppRow {
  app_id: string | null
  app_name: string
  resource_type: string
  api_call_count: number
  resource_return_count: number
  last_call_time?: number | null
}

interface WideAppRow {
  app_id: string | null
  app_name: string
  total_api: number
  total_resource: number
  component_api: number
  component_resource: number
  icon_api: number
  icon_resource: number
  illus_api: number
  illus_resource: number
  image_api: number
  image_resource: number
  file_api: number
  file_resource: number
  last_call_time?: number | null
}

function SearchStatsSection() {
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('year'),
    dayjs(),
  ])
  const [metric, setMetric] = useState<MetricType>('api_call_count')
  const [granularity, setGranularity] = useState<Granularity>('month')
  const [appGranularity, setAppGranularity] = useState<Granularity>('month')
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState({ api_call_count: 0, resource_return_count: 0 })
  const [lastUpdated, setLastUpdated] = useState<number | null>(null)
  const [pieData, setPieData] = useState<Array<{ type: string; value: number }>>([])
  const [barData, setBarData] = useState<Array<{ resource_type: string; period: string; value: number }>>([])
  const [appPieData, setAppPieData] = useState<Array<{ type: string; value: number }>>([])
  const [appBarData, setAppBarData] = useState<Array<{ app_name: string; period: string; value: number }>>([])
  const [apps, setApps] = useState<AppRow[]>([])

  const fetchData = useCallback((range?: [Dayjs, Dayjs], m?: MetricType, g?: Granularity, ag?: Granularity) => {
    const [start, end] = range ?? dateRange
    const metricKey = m ?? metric
    const granularityKey = g ?? granularity
    const appGranularityKey = ag ?? appGranularity
    setLoading(true)
    api.getSearchStats({
      start_date: start.format('YYYY-MM-DD'),
      end_date: end.format('YYYY-MM-DD'),
      granularity: granularityKey,
      app_granularity: appGranularityKey,
    }).then(data => {
      setSummary(data.summary)
      setLastUpdated(typeof data.last_updated === 'number' ? data.last_updated : null)
      setPieData(
        data.pie.map(d => ({
          type: RESOURCE_TYPE_LABELS[d.resource_type] ?? d.resource_type,
          value: d[metricKey],
        }))
      )
      setBarData(
        data.bar.map(d => ({
          resource_type: RESOURCE_TYPE_LABELS[d.resource_type] ?? d.resource_type,
          period: d.period,
          value: d[metricKey],
        }))
      )
      setAppBarData(
        data.app_bar.map(d => ({
          app_name: d.app_name,
          period: d.period,
          value: d[metricKey],
        }))
      )
      setApps(data.apps)
      const byApp = new Map<string, number>()
      for (const r of data.apps) {
        const key = r.app_name
        byApp.set(key, (byApp.get(key) ?? 0) + (r[metricKey] || 0))
      }
      setAppPieData(
        Array.from(byApp.entries()).map(([name, value]) => ({ type: name, value }))
      )
    }).catch(err => {
      message.error(err.message || '加载统计数据失败')
    }).finally(() => setLoading(false))
  }, [dateRange, metric, granularity, appGranularity])

  useEffect(() => {
    fetchData()
  }, [])

  const handleMetricChange = (m: MetricType) => {
    setMetric(m)
    fetchData(undefined, m)
  }

  const handleGranularityChange = (g: Granularity) => {
    setGranularity(g)
    fetchData(undefined, undefined, g)
  }

  const handleAppGranularityChange = (ag: Granularity) => {
    setAppGranularity(ag)
    fetchData(undefined, undefined, undefined, ag)
  }

  const groupedApps = useMemo(() => {
    const byApp = new Map<string, AppRow[]>()
    for (const row of apps) {
      const key = row.app_id ?? ''
      let arr = byApp.get(key)
      if (!arr) {
        arr = []
        byApp.set(key, arr)
      }
      arr.push(row)
    }

    const result: WideAppRow[] = []
    for (const [, rows] of byApp) {
      const base = rows[0]
      const row: WideAppRow = {
        app_id: base.app_id,
        app_name: base.app_name ?? '匿名调用',
        total_api: 0,
        total_resource: 0,
        component_api: 0,
        component_resource: 0,
        icon_api: 0,
        icon_resource: 0,
        illus_api: 0,
        illus_resource: 0,
        image_api: 0,
        image_resource: 0,
        file_api: 0,
        file_resource: 0,
        last_call_time: base.last_call_time,
      }
      for (const r of rows) {
        const api = r.api_call_count || 0
        const res = r.resource_return_count || 0
        row.total_api += api
        row.total_resource += res
        switch (r.resource_type) {
          case 'component': row.component_api += api; row.component_resource += res; break
          case 'icon': row.icon_api += api; row.icon_resource += res; break
          case 'illus': row.illus_api += api; row.illus_resource += res; break
          case 'image': row.image_api += api; row.image_resource += res; break
          case 'file': row.file_api += api; row.file_resource += res; break
        }
      }
      result.push(row)
    }
    result.sort((a, b) => {
      if (!a.app_id) return 1
      if (!b.app_id) return -1
      return b.total_api - a.total_api
    })
    return result
  }, [apps])

  const grayCellStyle = { style: { background: '#f0f0f0' } }

  const appColumns: ColumnsType<WideAppRow> = [
    {
      title: '应用名称',
      dataIndex: 'app_name',
      width: 140,
      fixed: 'left',
      render: (v: string) => v,
    },
    {
      title: '最近调用',
      dataIndex: 'last_call_time',
      width: 150,
      render: (v: number | null) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'),
    },
    {
      title: '总接口数',
      dataIndex: 'total_api',
      width: 90,
      render: (v: number) => v.toLocaleString(),
      onCell: () => grayCellStyle,
    },
    {
      title: '总资源数',
      dataIndex: 'total_resource',
      width: 90,
      render: (v: number) => v.toLocaleString(),
    },
    ...STATS.reduce<ColumnsType<WideAppRow>>((acc, s) => {
      acc.push(
        {
          title: `${s.label}接口数`,
          dataIndex: `${s.key}_api`,
          width: 80,
          render: (v: number) => v.toLocaleString(),
          onCell: () => grayCellStyle,
        },
        {
          title: `${s.label}资源数`,
          dataIndex: `${s.key}_resource`,
          width: 80,
          render: (v: number) => v.toLocaleString(),
        },
      )
      return acc
    }, []),
  ]

  const pieColorScale = buildColorScale(pieData.map(d => d.type))

  const pieConfig = {
    data: pieData,
    angleField: 'value',
    colorField: 'type',
    label: {
      text: (d: { type: string; value: number }, i: number, data: { type: string; value: number }[]) => {
        const total = data.reduce((s, x) => s + x.value, 0)
        return total > 0 ? `${(d.value / total * 100).toFixed(1)}%` : '0%'
      },
      position: 'outside',
      connectorLength: 16,
      connectorLength2: 8,
      connectorDistance: 2,
      transform: [
        { type: 'overlapDodgeY' },
      ],
    },
    tooltip: {
      items: [(d: { type: string; value: number }) => ({ name: d.type, value: d.value.toLocaleString() })],
    },
    legend: {
      color: {
        title: false,
        position: 'right',
        rowPadding: 5,
      },
    },
    scale: {
      color: pieColorScale,
    },
    radius: 0.75,
    height: 300,
  }

  const barColorScale = buildColorScale(barData.map(d => d.resource_type))

  const columnConfig = {
    data: barData,
    xField: 'period',
    yField: 'value',
    colorField: 'resource_type',
    stack: true,
    style: { maxWidth: 20 },
    label: {
      text: (d: { resource_type: string; period: string; value: number }, i: number, data: any[]) => {
        const samePeriod = data.filter((x: any) => x.period === d.period)
        if (d !== samePeriod[samePeriod.length - 1]) return ''
        const total = samePeriod.reduce((s: number, x: any) => s + x.value, 0)
        return total > 0 ? total.toLocaleString() : ''
      },
      position: 'top',
      dy: -16,
    },
    scrollbar: granularity === 'day' ? { x: {} } : undefined,
    legend: {
      color: {
        title: false,
        position: 'right',
      },
    },
    scale: {
      color: barColorScale,
    },
    tooltip: {
      title: (d: { resource_type: string; period: string; value: number }) => d.period,
      items: [(d: { resource_type: string; period: string; value: number }) => ({ name: d.resource_type, value: d.value })],
    },
    axis: {
      x: {
        labelFormatter: (v: string) => v.slice(5),
      },
      y: {
        title: METRIC_LABELS[metric],
        labelFormatter: (v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v),
      },
    },
    height: 300,
  }

  const appPieColorScale = buildColorScale(appPieData.map(d => d.type))

  const appPieConfig = {
    data: appPieData,
    angleField: 'value',
    colorField: 'type',
    label: {
      text: (d: { type: string; value: number }, i: number, data: { type: string; value: number }[]) => {
        const total = data.reduce((s, x) => s + x.value, 0)
        return total > 0 ? `${(d.value / total * 100).toFixed(1)}%` : '0%'
      },
      position: 'outside',
      connectorLength: 16,
      connectorLength2: 8,
      connectorDistance: 2,
      transform: [
        { type: 'overlapDodgeY' },
      ],
    },
    tooltip: {
      items: [(d: { type: string; value: number }) => ({ name: d.type, value: d.value.toLocaleString() })],
    },
    legend: {
      color: {
        title: false,
        position: 'right',
        rowPadding: 5,
      },
    },
    scale: {
      color: appPieColorScale,
    },
    radius: 0.75,
    height: 300,
  }

  const appBarColorScale = buildColorScale(appBarData.map(d => d.app_name))

  const appColumnConfig = {
    data: appBarData,
    xField: 'period',
    yField: 'value',
    colorField: 'app_name',
    stack: true,
    style: { maxWidth: 20 },
    label: {
      text: (d: { app_name: string; period: string; value: number }, i: number, data: any[]) => {
        const samePeriod = data.filter((x: any) => x.period === d.period)
        if (d !== samePeriod[samePeriod.length - 1]) return ''
        const total = samePeriod.reduce((s: number, x: any) => s + x.value, 0)
        return total > 0 ? total.toLocaleString() : ''
      },
      position: 'top',
      dy: -16,
    },
    scrollbar: appGranularity === 'day' ? { x: {} } : undefined,
    legend: {
      color: {
        title: false,
        position: 'right',
      },
    },
    scale: {
      color: appBarColorScale,
    },
    tooltip: {
      title: (d: { app_name: string; period: string; value: number }) => d.period,
      items: [(d: { app_name: string; period: string; value: number }) => ({ name: d.app_name, value: d.value })],
    },
    axis: {
      x: {
        labelFormatter: (v: string) => v.slice(5),
      },
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
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#0f172a' }}>调用统计</h2>
          <span style={{ fontSize: 13, color: '#94a3b8' }}>
              上次更新时间：{lastUpdated ? dayjs(lastUpdated).format('YYYY-MM-DD HH:mm:ss') : '—'}
          </span>
        </div>
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
            <div style={{ fontSize: 28, fontWeight: 800, color: '#0f172a' }}>
              {summary.api_call_count.toLocaleString()}
            </div>
          </div>
          <div style={{
            background: '#fff', borderRadius: 12, padding: '20px 28px',
            border: '1px solid #e2e8f0', flex: 1, textAlign: 'center',
          }}>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>资源返回数</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#0f172a' }}>
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 8, flexWrap: 'wrap' }}>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#475569' }}>
                各类资源按{GRANULARITY_LABELS[granularity]}分布
              </h3>
              <Radio.Group
                size="small"
                value={granularity}
                onChange={e => handleGranularityChange(e.target.value)}
                optionType="button"
                buttonStyle="solid"
              >
                <Radio.Button value="day">按天</Radio.Button>
                <Radio.Button value="week">按周</Radio.Button>
                <Radio.Button value="month">按月</Radio.Button>
              </Radio.Group>
            </div>
            <Column {...columnConfig} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          <div style={{
            background: '#fff', borderRadius: 12, padding: 16,
            border: '1px solid #e2e8f0', flex: 1, minWidth: 0,
          }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: '#475569' }}>
              三方调用占比
            </h3>
            <Pie {...appPieConfig} />
          </div>
          <div style={{
            background: '#fff', borderRadius: 12, padding: 16,
            border: '1px solid #e2e8f0', flex: 1.5, minWidth: 0,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 8, flexWrap: 'wrap' }}>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#475569' }}>
                三方调用按{GRANULARITY_LABELS[appGranularity]}分布
              </h3>
              <Radio.Group
                size="small"
                value={appGranularity}
                onChange={e => handleAppGranularityChange(e.target.value)}
                optionType="button"
                buttonStyle="solid"
              >
                <Radio.Button value="day">按天</Radio.Button>
                <Radio.Button value="week">按周</Radio.Button>
                <Radio.Button value="month">按月</Radio.Button>
              </Radio.Group>
            </div>
            <Column {...appColumnConfig} />
          </div>
        </div>

        <div style={{
          background: '#fff', borderRadius: 12, padding: 16,
          border: '1px solid #e2e8f0', overflow: 'hidden',
        }}>
          <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: '#475569' }}>
            三方调用详情
          </h3>
          <Table<WideAppRow>
            rowKey={(r) => r.app_id ?? 'anonymous'}
            size="small"
            columns={appColumns}
            dataSource={groupedApps}
            pagination={false}
            tableLayout="fixed"
            scroll={{ x: 1200 }}
          />
        </div>
      </Spin>
    </div>
  )
}
