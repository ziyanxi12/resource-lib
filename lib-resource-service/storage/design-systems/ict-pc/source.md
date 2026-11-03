---
format: octo-design-md/1
id: ict-pc
name: "ICT领域PC端设计规范"
author: "黄舒凡"
cover: cover-blue.jpg
usage: 158
order: 4
source_skill: "ICT领域PC端设计规范"
adapter: markdown-tokens
source_files: "31"
source_size: "68 KB"
source_entry: "references/design_system.md"
---

# ICT领域PC端设计规范

> 由 spec-skill-to-design-system 从规范 Skill 转换生成。每个区块的正文是说明和使用规则，`json design` 数据块供管理页渲染；
> 标注「未定义」的区块表示规范里没有提取到这部分内容。

## 概览 {#overview}

用于创建、审查符合 ICT 基础设施通用 UI 规范 3.1.1 一致性的 UI，在保留企业级页面场景适配弹性的同时，提高 Design Token 使用、组件规范、视觉一致性、无障碍和规范完整性的上线要求

## 颜色 {#color}

70 个颜色 token，按用途分组。

### 使用规则

- 所有 UI 颜色必须引用颜色 token 或组件语义 props。
- 背景、文字、图标、边框、状态、图表和数据高亮都不得在消费端硬编码色值。
- 禁止为了局部视觉效果新增一次性色值；确需新增时，先沉淀为 token，再在规范中登记用途。
- 语义状态必须使用 `error`、`success`、`warning`、`critical`、`info` 及其 container/on-container token。
- 文本必须使用与背景匹配的 `on-*` token，避免手动猜测对比度。

```json design
{
 "title": "语义色",
 "themes": [
  "light"
 ],
 "groups": [
  {
   "title": "品牌色",
   "desc": "品牌主色及其容器、固定色",
   "kind": "cards",
   "tokens": [
    {
     "name": "primary",
     "token": "primary",
     "value": "#0067D1"
    },
    {
     "name": "on-primary",
     "token": "on-primary",
     "value": "#FFFFFF"
    },
    {
     "name": "primary-container",
     "token": "primary-container",
     "value": "#E6F2FD"
    },
    {
     "name": "on-primary-container",
     "token": "on-primary-container",
     "value": "#191919"
    },
    {
     "name": "primary-fixed",
     "token": "primary-fixed",
     "value": "#0067D1"
    },
    {
     "name": "primary-fixed-dim",
     "token": "primary-fixed-dim",
     "value": "#004EA8"
    },
    {
     "name": "on-primary-fixed",
     "token": "on-primary-fixed",
     "value": "#FFFFFF"
    },
    {
     "name": "on-primary-fixed-variant",
     "token": "on-primary-fixed-variant",
     "value": "#F3F3F3"
    },
    {
     "name": "inverse-primary",
     "token": "inverse-primary",
     "value": "#0067D1"
    }
   ]
  },
  {
   "title": "表面色",
   "desc": "页面与容器的层级背景及其文字色",
   "kind": "cards",
   "tokens": [
    {
     "name": "surface",
     "token": "surface",
     "value": "#F3F3F3"
    },
    {
     "name": "surface-dim",
     "token": "surface-dim",
     "value": "#DFDFDF"
    },
    {
     "name": "surface-bright",
     "token": "surface-bright",
     "value": "#FFFFFF"
    },
    {
     "name": "on-surface",
     "token": "on-surface",
     "value": "#191919"
    },
    {
     "name": "surface-variant",
     "token": "surface-variant",
     "value": "#F3F3F3"
    },
    {
     "name": "on-surface-variant",
     "token": "on-surface-variant",
     "value": "#777777"
    },
    {
     "name": "surface-container-lowest",
     "token": "surface-container-lowest",
     "value": "#F3F3F3"
    },
    {
     "name": "surface-container-low",
     "token": "surface-container-low",
     "value": "rgba(255,255,255,0.5)"
    },
    {
     "name": "surface-container",
     "token": "surface-container",
     "value": "rgba(255,255,255,0.65)"
    },
    {
     "name": "surface-container-high",
     "token": "surface-container-high",
     "value": "rgba(255,255,255,0.8)"
    },
    {
     "name": "surface-container-highest",
     "token": "surface-container-highest",
     "value": "#FFFFFF"
    },
    {
     "name": "inverse-surface",
     "token": "inverse-surface",
     "value": "#191919"
    },
    {
     "name": "inverse-on-surface",
     "token": "inverse-on-surface",
     "value": "#FFFFFF"
    },
    {
     "name": "inverse-on-surface-variant",
     "token": "inverse-on-surface-variant",
     "value": "#C9C9C9"
    }
   ]
  },
  {
   "title": "语义色",
   "desc": "错误、成功、警告、严重、信息状态",
   "kind": "cards",
   "tokens": [
    {
     "name": "error",
     "token": "error",
     "value": "#E02128"
    },
    {
     "name": "on-error",
     "token": "on-error",
     "value": "#FFFFFF"
    },
    {
     "name": "error-container",
     "token": "error-container",
     "value": "#FEE7E8"
    },
    {
     "name": "on-error-container",
     "token": "on-error-container",
     "value": "#191919"
    },
    {
     "name": "success",
     "token": "success",
     "value": "#09AA71"
    },
    {
     "name": "on-success",
     "token": "on-success",
     "value": "#FFFFFF"
    },
    {
     "name": "success-container",
     "token": "success-container",
     "value": "#E7FBF2"
    },
    {
     "name": "on-success-container",
     "token": "on-success-container",
     "value": "#191919"
    },
    {
     "name": "critical",
     "token": "critical",
     "value": "#F4840C"
    },
    {
     "name": "on-critical",
     "token": "on-critical",
     "value": "#FFFFFF"
    },
    {
     "name": "critical-container",
     "token": "critical-container",
     "value": "#FEF5E8"
    },
    {
     "name": "on-critical-container",
     "token": "on-critical-container",
     "value": "#191919"
    },
    {
     "name": "warning",
     "token": "warning",
     "value": "#FCC800"
    },
    {
     "name": "on-warning",
     "token": "on-warning",
     "value": "#FFFFFF"
    },
    {
     "name": "warning-container",
     "token": "warning-container",
     "value": "#FEFCE0"
    },
    {
     "name": "on-warning-container",
     "token": "on-warning-container",
     "value": "#191919"
    },
    {
     "name": "info",
     "token": "info",
     "value": "#0067D1"
    },
    {
     "name": "on-info",
     "token": "on-info",
     "value": "#FFFFFF"
    },
    {
     "name": "info-container",
     "token": "info-container",
     "value": "#E6F2FD"
    },
    {
     "name": "on-info-container",
     "token": "on-info-container",
     "value": "#191919"
    }
   ]
  },
  {
   "title": "辅助色",
   "desc": "图表与分类用的扩展色",
   "kind": "cards",
   "tokens": [
    {
     "name": "accent-1",
     "token": "accent-1",
     "value": "#8B5CF6"
    },
    {
     "name": "on-accent-1",
     "token": "on-accent-1",
     "value": "#FFFFFF"
    },
    {
     "name": "accent-1-container",
     "token": "accent-1-container",
     "value": "#EDE9FE"
    },
    {
     "name": "on-accent-1-container",
     "token": "on-accent-1-container",
     "value": "#4C1D95"
    },
    {
     "name": "accent-2",
     "token": "accent-2",
     "value": "#F43F5E"
    },
    {
     "name": "on-accent-2",
     "token": "on-accent-2",
     "value": "#FFFFFF"
    },
    {
     "name": "accent-2-container",
     "token": "accent-2-container",
     "value": "#FFE4E6"
    },
    {
     "name": "on-accent-2-container",
     "token": "on-accent-2-container",
     "value": "#9F1239"
    },
    {
     "name": "accent-3",
     "token": "accent-3",
     "value": "#F59E0B"
    },
    {
     "name": "on-accent-3",
     "token": "on-accent-3",
     "value": "#FFFFFF"
    },
    {
     "name": "accent-3-container",
     "token": "accent-3-container",
     "value": "#FEF3C7"
    },
    {
     "name": "on-accent-3-container",
     "token": "on-accent-3-container",
     "value": "#92400E"
    },
    {
     "name": "accent-4",
     "token": "accent-4",
     "value": "#06B6D4"
    },
    {
     "name": "on-accent-4",
     "token": "on-accent-4",
     "value": "#FFFFFF"
    },
    {
     "name": "accent-4-container",
     "token": "accent-4-container",
     "value": "#CFFAFE"
    },
    {
     "name": "on-accent-4-container",
     "token": "on-accent-4-container",
     "value": "#164E63"
    },
    {
     "name": "accent-5",
     "token": "accent-5",
     "value": "#6366F1"
    },
    {
     "name": "on-accent-5",
     "token": "on-accent-5",
     "value": "#FFFFFF"
    },
    {
     "name": "accent-5-container",
     "token": "accent-5-container",
     "value": "#E0E7FF"
    },
    {
     "name": "on-accent-5-container",
     "token": "on-accent-5-container",
     "value": "#3730A3"
    }
   ]
  },
  {
   "title": "其他",
   "desc": "分割线等",
   "kind": "cards",
   "tokens": [
    {
     "name": "divider",
     "token": "divider",
     "value": "#F3F3F3"
    }
   ]
  },
  {
   "title": "描边色",
   "desc": "",
   "kind": "cards",
   "tokens": [
    {
     "name": "border-base",
     "token": "border-base",
     "value": "#C9C9C9"
    },
    {
     "name": "border-divider",
     "token": "border-divider",
     "value": "#F3F3F3"
    },
    {
     "name": "border-selected",
     "token": "border-selected",
     "value": "#0067D1"
    },
    {
     "name": "border-error",
     "token": "border-error",
     "value": "#E02128"
    }
   ]
  },
  {
   "title": "焦点描边",
   "desc": "",
   "kind": "cards",
   "tokens": [
    {
     "name": "outline-brand",
     "token": "outline-brand",
     "value": "#0067D1"
    },
    {
     "name": "outline-error",
     "token": "outline-error",
     "value": "#E02128"
    }
   ]
  }
 ]
}
```

## 字体 {#typography}

12 级字号，字体家族 HarmonyOS Sans SC。

### 使用规则

- `font-size` 和 `line-height` 必须使用 typography token，不得自定义任意字号或行高。
- `font-weight` 必须使用规范角色定义：正文/表格默认 Regular，标题/激活导航/关键指标使用 Medium，避免随意使用 Bold。
- 中文主字体使用 HarmonyOS Sans SC；运行环境未加载时使用系统 fallback。
- 卡片标题必须使用 `text-lg`。表格内容必须使用 `text-md`。
- 页面级标题、模块标题、表格内容、表单标签、Caption、KPI 数字必须按信息层级选择 token，不得用视觉喜好临时放大或缩小。
- 禁止使用 viewport width 缩放字体，字距保持 `0`。

```json design
{
 "title": "字体层级",
 "families": [
  "HarmonyOS Sans SC"
 ],
 "weights": [],
 "scale": [
  {
   "name": "text-sm",
   "token": "text-sm",
   "size": 12,
   "lineHeight": 19,
   "weight": null
  },
  {
   "name": "text-md",
   "token": "text-md",
   "size": 14,
   "lineHeight": 21,
   "weight": null
  },
  {
   "name": "text-lg",
   "token": "text-lg",
   "size": 16,
   "lineHeight": 24,
   "weight": null
  },
  {
   "name": "text-xl",
   "token": "text-xl",
   "size": 18,
   "lineHeight": 27,
   "weight": null
  },
  {
   "name": "text-2xl",
   "token": "text-2xl",
   "size": 20,
   "lineHeight": 28,
   "weight": null
  },
  {
   "name": "text-3xl",
   "token": "text-3xl",
   "size": 24,
   "lineHeight": 34,
   "weight": null
  },
  {
   "name": "text-4xl",
   "token": "text-4xl",
   "size": 28,
   "lineHeight": 39,
   "weight": null
  },
  {
   "name": "text-5xl",
   "token": "text-5xl",
   "size": 36,
   "lineHeight": 50,
   "weight": null
  },
  {
   "name": "text-6xl",
   "token": "text-6xl",
   "size": 48,
   "lineHeight": 62,
   "weight": null
  },
  {
   "name": "text-7xl",
   "token": "text-7xl",
   "size": 60,
   "lineHeight": 78,
   "weight": null
  },
  {
   "name": "text-8xl",
   "token": "text-8xl",
   "size": 72,
   "lineHeight": 86,
   "weight": null
  },
  {
   "name": "text-9xl",
   "token": "text-9xl",
   "size": 96,
   "lineHeight": 115,
   "weight": null
  }
 ]
}
```

## 间距 {#spacing}

6 个 token。

### 使用规则

- `padding`、`margin`、`gap` 必须使用 spacing token，不得自定义任意数值。
- 禁止使用 `p-[...]`、`px-[...]`、`m-[...]`、`mt-[...]`、`gap-[...]` 等任意值。
- 同一页面同类区块的 spacing 层级必须一致，不能随机混用多个相近数值。

```json design
{
 "title": "间距",
 "tokens": [
  {
   "name": "inline",
   "value": 8,
   "raw": "0.5rem",
   "desc": "用于图标与文字、按钮内部元素、小型内联元素之间的间距。"
  },
  {
   "name": "stack",
   "value": 12,
   "raw": "0.75rem",
   "desc": "用于表单字段、标题与说明、列表项内部的垂直间距。"
  },
  {
   "name": "gutter",
   "value": 16,
   "raw": "1rem",
   "desc": "用于表格工具区、筛选项、按钮组、卡片内部较紧凑的横向间距。"
  },
  {
   "name": "inset",
   "value": 24,
   "raw": "1.5rem",
   "desc": "用于 Card、Drawer、Dialog、表单区块等容器内部 padding。"
  },
  {
   "name": "section",
   "value": 16,
   "raw": "1rem",
   "desc": "用于模块、Card、表格、图表和功能区之间的间距。"
  },
  {
   "name": "page",
   "value": 32,
   "raw": "2rem",
   "desc": "用于页面最外层容器 padding。"
  }
 ]
}
```

## 圆角 {#radius}

8 个 token。

### 使用规则

- `border-radius` 必须使用 radius token，不得自定义任意圆角值。
- 小型控件和紧凑元素使用 `rounded-sm` 或 `rounded-md`。
- Button、Input、Search、Select、Checkbox、Tag 等默认操作和表单控件使用组件映射的 action/control 圆角。
- Card、Dialog、Drawer、Popover、Tooltip、Overlay 等容器使用 `rounded-xl`、`rounded-container` 或 `rounded-overlay`。
- Switch、进度条、胶囊型标签等需要完全圆角时使用 `rounded-full`。
- 禁止把所有组件统一改成大圆角；圆角必须匹配组件尺寸、密度和功能。

```json design
{
 "title": "圆角",
 "tokens": [
  {
   "name": "rounded-sm",
   "value": 2,
   "raw": "2px",
   "desc": ""
  },
  {
   "name": "rounded-md",
   "value": 4,
   "raw": "4px",
   "desc": ""
  },
  {
   "name": "rounded-lg",
   "value": 6,
   "raw": "6px",
   "desc": ""
  },
  {
   "name": "rounded-xl",
   "value": 8,
   "raw": "8px",
   "desc": ""
  },
  {
   "name": "rounded-badge",
   "value": 4,
   "raw": "4px",
   "desc": ""
  },
  {
   "name": "rounded-action",
   "value": 4,
   "raw": "4px",
   "desc": ""
  },
  {
   "name": "rounded-container",
   "value": 8,
   "raw": "8px",
   "desc": ""
  },
  {
   "name": "rounded-overlay",
   "value": 8,
   "raw": "8px",
   "desc": ""
  }
 ]
}
```

## 阴影 {#shadow}

7 个 token。

```json design
{
 "title": "阴影",
 "tokens": [
  {
   "name": "shadow-sm",
   "value": "1px 1px 6px 0 rgba(0, 0, 0, 0.08)",
   "raw": "1px 1px 6px 0 rgba(0, 0, 0, 0.08)",
   "desc": ""
  },
  {
   "name": "shadow-md",
   "value": "0 4px 12px 0px rgba(0, 0, 0, 0.16)",
   "raw": "0 4px 12px 0px rgba(0, 0, 0, 0.16)",
   "desc": ""
  },
  {
   "name": "shadow-lg",
   "value": "0 8px 24px 0px rgba(0, 0, 0, 0.16)",
   "raw": "0 8px 24px 0px rgba(0, 0, 0, 0.16)",
   "desc": ""
  },
  {
   "name": "shadow-xl",
   "value": "0 16px 48px 0px rgba(0, 0, 0, 0.16)",
   "raw": "0 16px 48px 0px rgba(0, 0, 0, 0.16)",
   "desc": ""
  },
  {
   "name": "shadow-card",
   "value": "1px 1px 6px 0 rgba(0, 0, 0, 0.08)",
   "raw": "1px 1px 6px 0 rgba(0, 0, 0, 0.08)",
   "desc": "同 shadow-sm"
  },
  {
   "name": "shadow-popover",
   "value": "0 8px 24px 0px rgba(0, 0, 0, 0.16)",
   "raw": "0 8px 24px 0px rgba(0, 0, 0, 0.16)",
   "desc": "同 shadow-lg"
  },
  {
   "name": "shadow-modal",
   "value": "0 16px 48px 0px rgba(0, 0, 0, 0.16)",
   "raw": "0 16px 48px 0px rgba(0, 0, 0, 0.16)",
   "desc": "同 shadow-xl"
  }
 ]
}
```

## 组件 {#components}

23 个组件规范，含用途、属性与使用规则。有源码的直接渲染，无源码的由 AI 按规范生成参考实现。

```json design
{
 "title": "组件",
 "items": [
  {
   "id": "alert",
   "name": "Alert 公告提示",
   "desc": "用于页面级或区域级状态消息，用户看到后仍可继续任务。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/alert.html",
      "lang": "html",
      "code": "<style>\n.al{width:520px;padding:10px 14px;border-radius:var(--r-a);display:flex;gap:10px;align-items:flex-start;font-size:14px;color:var(--t1)}\n.al i{width:16px;height:16px;border-radius:50%;color:#fff;font-size:11px;font-style:normal;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:3px}\n.al .c{margin-left:auto;cursor:pointer;color:#777}.al .c:hover{color:var(--t1)}.al a{color:var(--p);margin-left:8px;cursor:pointer}\n.in{background:#E6F2FD}.in i{background:var(--p)}.ok{background:#E7FBF2}.ok i{background:#09AA71}.wa{background:#FEFCE0}.wa i{background:#FCC800}.er{background:#FEE7E8}.er i{background:var(--err)}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">类型 type · 可关闭</div>\n<div class=\"al in\"><i>i</i>系统将于今晚 22:00 升级，届时服务短暂中断。<a>查看公告</a><span class=\"c\" onclick=\"this.parentNode.remove()\">✕</span></div>\n<div class=\"al ok\"><i>✓</i>配置已下发到 128 台设备。</div>\n<div class=\"al wa\"><i>!</i>3 台设备证书将在 7 天内过期。<a>立即处理</a></div>\n<div class=\"al er\"><i>✕</i>同步失败：网络连接超时。<span class=\"c\" onclick=\"this.parentNode.remove()\">✕</span></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "类型",
    "规则",
    "Don't"
   ],
   "rules": [
    "Critical/Risk",
    "使用语义容器 token。",
    "可带图标、操作链接/按钮、关闭按钮。",
    "页面级 Alert 放在标题或工具区下方，说明全局影响。",
    "区域级 Alert 放在受影响模块内部或上方。",
    "可关闭 Alert 只用于用户关闭后不影响任务理解的提示。"
   ]
  },
  {
   "id": "badge",
   "name": "Badge 徽标",
   "desc": "用于通知点、未读数或附着在元素上的小型数量提示。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/badge.html",
      "lang": "html",
      "code": "<style>\n.bx{position:relative;width:40px;height:40px;border-radius:var(--r-c);background:#F3F3F3;display:inline-flex;align-items:center;justify-content:center;font-size:18px}\n.bd{position:absolute;top:-6px;right:-8px;min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--err);color:#fff;font-size:11px;display:flex;align-items:center;justify-content:center;border:1.5px solid #fff}\n.dt{position:absolute;top:-2px;right:-2px;width:8px;height:8px;border-radius:50%;background:var(--err);border:1.5px solid #fff}\n.st{display:inline-flex;align-items:center;gap:6px;font-size:14px}.st i{width:6px;height:6px;border-radius:50%}\n</style>\n<div class=\"g\">\n<div class=\"g-sec\"><div class=\"g-label\">数字 / 圆点</div><div class=\"g-row\"><span class=\"bx\">🔔<b class=\"bd\">8</b></span><span class=\"bx\">✉<b class=\"bd\">99+</b></span><span class=\"bx\">⚙<b class=\"dt\"></b></span></div></div>\n<div class=\"g-sec\"><div class=\"g-label\">状态点</div><div class=\"g-row\"><span class=\"st\"><i style=\"background:#09AA71\"></i>运行中</span><span class=\"st\"><i style=\"background:#FCC800\"></i>告警</span><span class=\"st\"><i style=\"background:var(--err)\"></i>离线</span></div></div>\n</div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "类型",
    "规则",
    "Don't"
   ],
   "rules": [
    "Dot badge：只表达“有”。",
    "Number badge：表达数量。",
    "Dot badge 用于未读、待处理、提醒存在性。",
    "Number badge 用于通知数量、待办数量、消息数量；数量过大按组件上限显示。",
    "依附于图标、头像、Tab 或紧凑文本。",
    "大数字按组件能力显示上限，如 `99+`。"
   ]
  },
  {
   "id": "breadcrumb",
   "name": "Breadcrumb 面包屑",
   "desc": "用于展示当前页面在层级结构中的位置，并支持回到上级。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/breadcrumb.html",
      "lang": "html",
      "code": "<style>.bc{font-size:14px;color:#777;display:flex;gap:8px}.bc a{cursor:pointer;color:#777}.bc a:hover{color:var(--p)}.bc b{font-weight:400;color:var(--t1)}</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">面包屑</div><div class=\"bc\"><a>首页</a>/<a>设备管理</a>/<a>核心路由器</a>/<b>HW-ROUTER-0192</b></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "结构",
    "规则",
    "文案",
    "Don't"
   ],
   "rules": [
    "通常放在页面标题或内容区域上方。",
    "视觉权重低于页面标题。",
    "当前页可区分，但不要像按钮。",
    "路径过长时截断、折叠或使用下拉。",
    "详情页、报告页、深层配置页优先使用 Breadcrumb。",
    "一级 Dashboard、工作台、无层级列表页通常不需要 Breadcrumb。"
   ]
  },
  {
   "id": "button",
   "name": "Button 按钮",
   "desc": "按钮用于触发命令和操作，不用于纯信息展示。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/button.html",
      "lang": "html",
      "code": "<style>\n.b{height:32px;padding:0 16px;border-radius:var(--r-a);border:1px solid transparent;font:inherit;font-size:14px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:6px;transition:background .15s,transform .1s,box-shadow .15s;background:var(--p);color:#fff}\n.b[data-color=default]{background:#F3F3F3;color:var(--t1)}.b[data-color=danger]{background:var(--err)}\n.b[data-types=outlined]{background:#fff;border-color:var(--p);color:var(--p)}.b[data-types=outlined][data-color=default]{border-color:#C9C9C9;color:var(--t1)}.b[data-types=outlined][data-color=danger]{border-color:var(--err);color:var(--err)}\n.b[data-types=text],.b[data-types=link]{background:transparent;color:var(--p)}.b[data-types=text][data-color=danger],.b[data-types=link][data-color=danger]{color:var(--err)}.b[data-types=text][data-color=default]{color:var(--t1)}\n.b[data-types=link]{padding:0 4px}.b[data-types=icon]{width:32px;padding:0}.b[data-types=icon] span{display:none}.b[data-types=icon]::after{content:\"＋\";font-size:16px}\n.b[data-size=lg]{height:40px;font-size:16px;padding:0 20px}.b[data-size=lg][data-types=icon]{width:40px;padding:0}.b[data-size=sm]{height:24px;font-size:12px;padding:0 10px}.b[data-size=sm][data-types=icon]{width:24px;padding:0}\n.b:not([data-force]):hover,.b[data-force=hover]{filter:brightness(.92)}.b[data-types=outlined]:not([data-force]):hover,.b[data-types=outlined][data-force=hover],.b[data-types=text]:not([data-force]):hover,.b[data-types=text][data-force=hover]{filter:none;background:#E6F2FD}\n.b[data-types=link]:not([data-force]):hover span,.b[data-types=link][data-force=hover] span{text-decoration:underline}\n.b:not([data-force]):active,.b[data-force=pressed]{filter:brightness(.84);transform:scale(.97)}\n.b:focus-visible,.b[data-force=focus]{outline:none;box-shadow:0 0 0 2px #fff,0 0 0 4px var(--p)}\n.b[data-disabled=true],.b[data-force=disabled]{opacity:.4;cursor:not-allowed;pointer-events:none}.b[data-force]{pointer-events:none}\n.b i{display:none;width:12px;height:12px;border:2px solid currentColor;border-right-color:transparent;border-radius:50%;animation:r 1s linear infinite}@keyframes r{to{transform:rotate(360deg)}}.b[data-loading=true] i{display:inline-block}\n</style>\n<div class=\"g own\"><button class=\"b\" data-c><i></i><span>新建任务</span></button></div>\n"
     }
    ]
   },
   "props": [
    {
     "name": "types",
     "values": "filled | outlined | text | link | icon"
    },
    {
     "name": "color",
     "values": "default | primary | danger"
    },
    {
     "name": "size",
     "values": "lg | md | sm"
    },
    {
     "name": "disabled",
     "values": "boolean"
    },
    {
     "name": "loading",
     "values": "boolean"
    }
   ],
   "sections": [
    "用途",
    "Props",
    "类型",
    "常见用法",
    "尺寸",
    "布局",
    "Do",
    "Don't"
   ],
   "rules": [
    "`filled`：主操作，如新建、提交、保存、确认。每个操作区域最多一个 `filled + primary`。",
    "`outlined`：次要操作，常与 filled 主操作搭配。",
    "`text`：低强调辅助操作。",
    "`link`：表格内文字操作必须使用。",
    "`icon`：工具栏、表格操作列、紧凑操作区的纯图标操作。",
    "普通按钮：用于独立命令，如保存、刷新、导出、删除。"
   ]
  },
  {
   "id": "card",
   "name": "Card 卡片",
   "desc": "用于内容分组、KPI、摘要和主要内容容器。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/card.html",
      "lang": "html",
      "code": "<style>\n.cd{width:240px;background:#fff;border-radius:var(--r-c);box-shadow:var(--sh);padding:16px;transition:box-shadow .15s;cursor:pointer}.cd:hover{box-shadow:0 4px 12px rgba(0,0,0,.16)}\n.cd .l{font-size:12px;color:#777}.cd .v{font-size:28px;font-weight:500;margin-top:4px}.cd .v small{font-size:12px;color:#777;font-weight:400;margin-left:4px}.cd .t{font-size:12px;color:#09AA71;margin-top:4px}\n.cd h4{margin:0 0 8px;font-size:16px;font-weight:500}.cd p{margin:0;font-size:13px;color:#777;line-height:20px}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">指标卡 · 内容卡（悬停加深阴影）</div><div class=\"g-row\">\n<div class=\"cd\"><div class=\"l\">设备总数</div><div class=\"v\">1,286<small>台</small></div><div class=\"t\">较昨日 +12</div></div>\n<div class=\"cd\"><div class=\"l\">在线率</div><div class=\"v\">98.2<small>%</small></div><div class=\"t\">较昨日 +0.3%</div></div>\n<div class=\"cd\"><h4>核心机房</h4><p>北京-亦庄数据中心 · 312 台设备 · 最近巡检 2 小时前</p></div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "规则",
    "内容",
    "Don't"
   ],
   "rules": [
    "使用 `bg-surface-container-highest`。",
    "使用 `rounded-xl`。",
    "使用 `shadow-card`。",
    "有海拔时不加结构性边框。",
    "标题使用 `text-lg`。",
    "内部分割使用 `border-divider`。"
   ]
  },
  {
   "id": "charts",
   "name": "Charts 图表",
   "desc": "用于趋势、比较、组成、分布和状态概览。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/charts.html",
      "lang": "html",
      "code": "<style>\n.ch{width:520px;background:#fff;border-radius:var(--r-c);box-shadow:var(--sh);padding:16px}.ch h4{margin:0 0 12px;font-size:14px;font-weight:500}\n.bars{display:flex;align-items:flex-end;gap:18px;height:140px;border-bottom:1px solid #F3F3F3;padding:0 8px}\n.bar{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;font-size:11px;color:#777;height:100%;justify-content:flex-end}\n.bar i{width:100%;background:var(--p);border-radius:2px 2px 0 0;transition:filter .15s}.bar:hover i{filter:brightness(1.15)}.bar:hover b{opacity:1}.bar b{font-weight:400;color:var(--t1);opacity:0}\n.lg{display:flex;gap:16px;font-size:12px;color:#777;margin-top:10px}.lg span::before{content:\"\";display:inline-block;width:8px;height:8px;border-radius:2px;background:var(--p);margin-right:6px}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">柱状图（悬停显示数值）</div><div class=\"ch\"><h4>近 7 日告警数</h4><div class=\"bars\">\n<div class=\"bar\"><b>32</b><i style=\"height:46%\"></i>周一</div><div class=\"bar\"><b>48</b><i style=\"height:68%\"></i>周二</div><div class=\"bar\"><b>27</b><i style=\"height:38%\"></i>周三</div><div class=\"bar\"><b>60</b><i style=\"height:86%\"></i>周四</div><div class=\"bar\"><b>41</b><i style=\"height:58%\"></i>周五</div><div class=\"bar\"><b>18</b><i style=\"height:26%\"></i>周六</div><div class=\"bar\"><b>22</b><i style=\"height:31%\"></i>周日</div>\n</div><div class=\"lg\"><span>告警数（条）</span></div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "规则",
    "Don't"
   ],
   "rules": [
    "使用图表组件内置图例、单位和坐标轴。",
    "传入数据，不要手动画图表 UI。",
    "数据 key 转中文。",
    "不使用图表 `color` prop。",
    "趋势用折线/面积，比较用柱状，组成用饼/环/堆叠，分布用散点/直方，进度或占比用进度/仪表类组件。",
    "图表旁需要有标题、时间范围、筛选条件或数据口径，不要让用户猜测含义。"
   ]
  },
  {
   "id": "checkbox",
   "name": "Checkbox 复选框",
   "desc": "用于独立二元选择或多选。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/checkbox.html",
      "lang": "html",
      "code": "<style>\n.cb{display:inline-flex;align-items:center;gap:8px;font-size:14px;cursor:pointer}\n.cb i{width:16px;height:16px;border:1px solid #C9C9C9;border-radius:2px;display:inline-flex;align-items:center;justify-content:center;background:#fff;transition:.15s;font-style:normal;color:#fff;font-size:11px}\n.cb:hover i{border-color:var(--p)}.cb.on i{background:var(--p);border-color:var(--p)}.cb.on i::after{content:\"✓\"}\n.cb.half i{background:var(--p);border-color:var(--p)}.cb.half i::after{content:\"\";width:8px;height:2px;background:#fff}\n.cb.dis{opacity:.4;pointer-events:none}\n</style>\n<div class=\"g\">\n<div class=\"g-sec\"><div class=\"g-label\">状态（点击切换）</div><div class=\"g-row\"><label class=\"cb on\" data-toggle><i></i>已选中</label><label class=\"cb\" data-toggle><i></i>未选中</label><label class=\"cb half\"><i></i>半选</label><label class=\"cb on dis\"><i></i>禁用</label><label class=\"cb dis\"><i></i>禁用</label></div></div>\n</div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "类型",
    "规则",
    "Don't"
   ],
   "rules": [
    "支持选择 0 个、1 个或多个。",
    "父子结构中部分子项选中时使用半选态。",
    "选项较多时分组或使用列表结构。",
    "标签应该明确描述被选择的对象或条件。",
    "单个 Checkbox 用于同意、启用附加条件或确认某个独立条件。",
    "Checkbox 组用于筛选、权限、批量选择和多条件配置。"
   ]
  },
  {
   "id": "dialog",
   "name": "Dialog 对话框",
   "desc": "用于需要用户注意的决策、确认、阻断反馈或短表单。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/dialog.html",
      "lang": "html",
      "code": "<style>\n.ov{width:520px;background:rgba(0,0,0,.35);border-radius:var(--r-c);padding:28px;display:flex;justify-content:center}\n.dg{width:400px;background:#fff;border-radius:var(--r-c);box-shadow:0 16px 48px rgba(0,0,0,.16)}\n.dg .h{padding:16px 20px;font-size:16px;font-weight:500;display:flex}.dg .h span{margin-left:auto;color:#777;cursor:pointer}\n.dg .c{padding:0 20px;font-size:14px;color:#777;line-height:22px}.dg .f{padding:16px 20px;display:flex;justify-content:flex-end;gap:8px}\n.b{height:32px;padding:0 16px;border-radius:var(--r-a);font:inherit;font-size:14px;cursor:pointer;border:1px solid #C9C9C9;background:#fff}.b:hover{border-color:var(--p);color:var(--p)}\n.b.p{background:var(--err);border-color:var(--err);color:#fff}.b.p:hover{filter:brightness(.92);color:#fff}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">确认对话框</div><div class=\"ov\"><div class=\"dg\"><div class=\"h\">删除告警规则<span>✕</span></div><div class=\"c\">删除后，关联的 6 台设备将不再触发该规则告警，此操作不可恢复。</div><div class=\"f\"><button class=\"b\">取消</button><button class=\"b p\">删除规则</button></div></div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "类型",
    "常见用法",
    "规则",
    "文案",
    "Don't"
   ],
   "rules": [
    "删除、停用、重置、覆盖等高风险动作使用确认 Dialog。",
    "少量字段的快速创建/编辑可以使用表单 Dialog。",
    "需要展示复杂详情、长表单或多区块内容时使用 Drawer 或页面，不使用 Dialog。",
    "标题、内容、操作区分明。",
    "破坏性主操作使用 danger。",
    "使用 modal 层级阴影。"
   ]
  },
  {
   "id": "drawer",
   "name": "Drawer 抽屉",
   "desc": "用于在保留当前页面上下文的同时完成详情、编辑、筛选或二级流程。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/drawer.html",
      "lang": "html",
      "code": "<style>\n.ov{width:560px;height:220px;background:rgba(0,0,0,.35);border-radius:var(--r-c);position:relative;overflow:hidden}\n.dr{position:absolute;right:0;top:0;bottom:0;width:300px;background:#fff;box-shadow:-8px 0 24px rgba(0,0,0,.16);display:flex;flex-direction:column}\n.dr .h{padding:14px 20px;font-size:16px;font-weight:500;border-bottom:1px solid #F3F3F3}.dr .c{padding:14px 20px;flex:1;font-size:13px;color:#777;line-height:24px}\n.dr .f{padding:12px 20px;display:flex;justify-content:flex-end;gap:8px;border-top:1px solid #F3F3F3}\n.b{height:28px;padding:0 14px;border-radius:var(--r-a);font:inherit;font-size:13px;cursor:pointer;border:1px solid #C9C9C9;background:#fff}.b.p{background:var(--p);border-color:var(--p);color:#fff}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">右侧抽屉</div><div class=\"ov\"><div class=\"dr\"><div class=\"h\">设备详情</div><div class=\"c\">编号：HW-ROUTER-0192<br>位置：北京-亦庄数据中心<br>状态：运行中</div><div class=\"f\"><button class=\"b\">关闭</button><button class=\"b p\">编辑</button></div></div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "规则",
    "Don't"
   ],
   "rules": [
    "右侧 Drawer：详情、编辑、筛选、二级流程。",
    "底部 Drawer：宽而低的流程或移动端式模式。",
    "包含标题、关闭、内容区和操作区。",
    "底部操作靠右并遵循 Button 规则。",
    "长内容在 Drawer 内部滚动。",
    "表格行详情、告警详情、对象配置、筛选面板优先使用右侧 Drawer。"
   ]
  },
  {
   "id": "form",
   "name": "Form 表单",
   "desc": "用于收集、编辑、校验和提交结构化信息。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/form.html",
      "lang": "html",
      "code": "<style>\n.fm{width:460px;display:flex;flex-direction:column;gap:14px}.fi{display:grid;grid-template-columns:96px 1fr;align-items:center;gap:12px;font-size:14px}\n.fi label{color:var(--t1);text-align:right}.fi label i{color:var(--err);font-style:normal;margin-right:2px}\n.in{height:32px;border:1px solid #C9C9C9;border-radius:var(--r-a);padding:0 10px;font:inherit;outline:none}.in:focus,.in:hover{border-color:var(--p)}\n.ft{display:flex;justify-content:flex-end;gap:8px}.b{height:32px;padding:0 16px;border-radius:var(--r-a);font:inherit;cursor:pointer;border:1px solid #C9C9C9;background:#fff}.b.p{background:var(--p);color:#fff;border-color:var(--p)}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">配置表单（标签右对齐）</div><div class=\"fm\">\n<div class=\"fi\"><label><i>*</i>规则名称</label><input class=\"in\" placeholder=\"请输入规则名称\"></div>\n<div class=\"fi\"><label><i>*</i>告警级别</label><select class=\"in\"><option>严重</option><option>警告</option><option>提示</option></select></div>\n<div class=\"fi\"><label>描述</label><input class=\"in\" placeholder=\"选填\"></div>\n<div class=\"ft\"><button class=\"b\">取消</button><button class=\"b p\">保存</button></div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "结构",
    "布局",
    "校验",
    "Don't"
   ],
   "rules": [
    "Label、字段、帮助文本、校验信息对齐。",
    "同一区域字段宽度和列数稳定。",
    "长表单可使用固定底部操作区。",
    "复杂表单可使用分组、分割线或 `surface-variant`。",
    "简单表单使用单列，便于阅读和校验。",
    "信息密度高的配置表单可使用双列，但同一分组内字段高度和基线保持一致。"
   ]
  },
  {
   "id": "header_navigation",
   "name": "Header Navigation 顶部导航",
   "desc": "用于全局导航、产品上下文、工作区切换、搜索、工具入口和账号入口。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/header_navigation.html",
      "lang": "html",
      "code": "<style>\n.hd{width:680px;height:48px;background:#fff;box-shadow:var(--sh);display:flex;align-items:center;padding:0 16px;gap:28px;font-size:14px;border-radius:var(--r-c)}\n.hd b{display:flex;align-items:center;gap:8px}.hd b i{width:20px;height:20px;border-radius:4px;background:var(--p)}\n.hd span{cursor:pointer;color:var(--t1);height:48px;display:flex;align-items:center;position:relative}.hd span:hover{color:var(--p)}\n.hd span.on{color:var(--p);font-weight:500}.hd span.on::after{content:\"\";position:absolute;left:0;right:0;bottom:0;height:2px;background:var(--p)}.hd em{margin-left:auto;font-style:normal;color:#777}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">顶部导航（高度 3rem）</div><div class=\"hd\" data-group><b><i></i>运维中心</b><span class=\"on\" data-item>总览</span><span data-item>设备</span><span data-item>告警</span><span data-item>报表</span><em>管理员 ▾</em></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "结构",
    "规则",
    "Don't"
   ],
   "rules": [
    "高度为 `3rem`。",
    "使用 `bg-surface-container-highest`。",
    "Active、hover、selected、dropdown 状态一致。",
    "导航过长时使用分组或下拉，不要硬塞。",
    "Header 承载全局层级，不承载页面内部的大量筛选或批量操作。",
    "产品标识、一级导航、全局工具和用户区需要形成稳定位置，不随页面内容变化。"
   ]
  },
  {
   "id": "input",
   "name": "Input 输入框",
   "desc": "用于文本、数字、结构化字段、筛选项和设置项录入。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/input.html",
      "lang": "html",
      "code": "<style>\n.in{width:240px;height:32px;border:1px solid #C9C9C9;border-radius:var(--r-a);padding:0 10px;font:inherit;font-size:14px;color:var(--t1);background:#fff;outline:none;transition:border-color .15s}\n.in:hover{border-color:var(--p)}.in:focus{border-color:var(--p);box-shadow:0 0 0 2px #E6F2FD}\n.in.err{border-color:var(--err)}.in:disabled{background:#F3F3F3;color:#C9C9C9;cursor:not-allowed}\n.lg{height:40px}.sm{height:24px;font-size:12px}\n.tip{font-size:12px;color:var(--err);margin-top:4px}\n</style>\n<div class=\"g\">\n<div class=\"g-sec\"><div class=\"g-label\">尺寸 size</div><div class=\"g-row\"><input class=\"in lg\" placeholder=\"大 · 请输入名称\"><input class=\"in\" placeholder=\"中 · 请输入名称\"><input class=\"in sm\" placeholder=\"小 · 请输入名称\"></div></div>\n<div class=\"g-sec\"><div class=\"g-label\">状态</div><div class=\"g-row\"><input class=\"in\" value=\"已填写的内容\"><div><input class=\"in err\" value=\"名称重复\"><div class=\"tip\">名称已存在，请重新输入</div></div><input class=\"in\" placeholder=\"禁用\" disabled></div></div>\n</div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "结构",
    "常见用法",
    "状态",
    "文案",
    "布局",
    "Don't"
   ],
   "rules": [
    "Placeholder",
    "基础输入：用于名称、描述、关键字等普通文本。",
    "前缀/后缀输入：用于单位、协议、搜索图标、清除按钮、密码可见性等辅助信息。",
    "文本域：用于多行说明、备注、描述；需要明确高度、字数统计和超长处理。",
    "只读输入：用于展示不可编辑但需要复制/查看的值。",
    "组合输入：用于 IP/端口、范围、时间区间等结构化内容；各字段需要清晰分隔和统一校验。"
   ]
  },
  {
   "id": "link",
   "name": "Link 文字链接",
   "desc": "用于跳转、引用、详情查看、下载和轻量操作。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/link.html",
      "lang": "html",
      "code": "<style>.lk{font-size:14px;color:var(--p);cursor:pointer}.lk:hover{text-decoration:underline}.lk.d{color:var(--err)}.lk.dis{color:#C9C9C9;cursor:not-allowed;text-decoration:none}</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">文字链接</div><div class=\"g-row\"><span class=\"lk\">查看详情</span><span class=\"lk\">下载报告 ↓</span><span class=\"lk d\">删除</span><span class=\"lk dis\">禁用</span></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "类型",
    "常见用法",
    "文案",
    "状态",
    "Don't"
   ],
   "rules": [
    "跳转详情：如资源名称、任务名称、报告标题。",
    "下载/复制/引用：轻量辅助动作。",
    "表格行内操作：使用按钮的 `types=link` 形态，保持操作列一致。",
    "外部链接：需要通过文案或图标说明跳出当前系统。",
    "链接文案要说明目标或动作。",
    "避免“点击这里”“查看”等脱离上下文的文案。"
   ]
  },
  {
   "id": "numeric",
   "name": "Numeric 计数器",
   "desc": "用于通过输入或步进调整数字。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/numeric.html",
      "lang": "html",
      "code": "<style>\n.n{display:inline-flex;height:32px;border:1px solid #C9C9C9;border-radius:var(--r-a);overflow:hidden}\n.n button{width:32px;border:0;background:#F3F3F3;cursor:pointer;font-size:16px;color:var(--t1)}.n button:hover{background:#E6F2FD;color:var(--p)}\n.n input{width:60px;border:0;text-align:center;font:inherit;outline:none}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">计数器（可点击增减）</div><div class=\"g-row\"><div class=\"n\"><button onclick=\"var i=this.nextElementSibling;i.value=Math.max(0,+i.value-1)\">−</button><input value=\"12\"><button onclick=\"var i=this.previousElementSibling;i.value=+i.value+1\">＋</button></div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "结构",
    "规则",
    "Don't"
   ],
   "rules": [
    "达到 min/max 时禁用对应按钮。",
    "校验 min、max、精度和非法输入。",
    "用于数量、阈值、重试次数、并发数、容量上限等可步进数值。",
    "步长需要符合业务单位，不要默认假设步长为 1。",
    "范围型数值优先使用两个输入框或专用范围组件，不要用单个 Numeric 表达复杂范围。",
    "不要自定义无关的步进按钮样式。"
   ]
  },
  {
   "id": "pagination",
   "name": "Pagination 分页器",
   "desc": "用于大数据集、表格、穿梭列表和分页结果组。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/pagination.html",
      "lang": "html",
      "code": "<style>\n.pg{display:flex;gap:6px;align-items:center;font-size:13px}.pg span{min-width:28px;height:28px;border:1px solid #C9C9C9;border-radius:var(--r-a);display:inline-flex;align-items:center;justify-content:center;cursor:pointer;padding:0 6px}\n.pg span:hover{border-color:var(--p);color:var(--p)}.pg span.on{background:var(--p);border-color:var(--p);color:#fff}.pg em{font-style:normal;color:#777;margin-right:8px}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">分页（点击切换）</div><div class=\"pg\" data-group><em>共 128 条</em><span>‹</span><span class=\"on\" data-item>1</span><span data-item>2</span><span data-item>3</span><span data-item>…</span><span data-item>13</span><span>›</span></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "结构",
    "规则",
    "Don't"
   ],
   "rules": [
    "表格分页放在表格容器底部。",
    "通常右对齐或与表格工具区一致。",
    "数据规模大时显示总数和 page-size。",
    "切换页码时保留筛选、搜索和排序条件。",
    "表格、列表、查询结果页使用分页时，应与数据容器保持视觉归属。",
    "跳页输入需要处理空值、非数字、超范围和回车确认。"
   ]
  },
  {
   "id": "radio",
   "name": "Radio 单选框",
   "desc": "用于从少量互斥选项中选择一个。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/radio.html",
      "lang": "html",
      "code": "<style>\n.rd{display:inline-flex;align-items:center;gap:8px;font-size:14px;cursor:pointer}\n.rd i{width:16px;height:16px;border:1px solid #C9C9C9;border-radius:50%;background:#fff;transition:.15s;box-sizing:border-box}\n.rd:hover i{border-color:var(--p)}.rd.on i{border:5px solid var(--p)}.rd.dis{opacity:.4;pointer-events:none}\n.bt{display:inline-flex;border:1px solid #C9C9C9;border-radius:var(--r-a);overflow:hidden}.bt span{padding:5px 14px;font-size:14px;cursor:pointer;border-left:1px solid #C9C9C9}.bt span:first-child{border-left:0}\n.bt span.on{background:#E6F2FD;color:var(--p)}.bt span:hover{color:var(--p)}\n</style>\n<div class=\"g\">\n<div class=\"g-sec\"><div class=\"g-label\">单选（点击切换）</div><div class=\"g-row\" data-group><label class=\"rd on\" data-item><i></i>实时</label><label class=\"rd\" data-item><i></i>近 1 小时</label><label class=\"rd\" data-item><i></i>近 24 小时</label><label class=\"rd dis\"><i></i>禁用</label></div></div>\n<div class=\"g-sec\"><div class=\"g-label\">按钮式</div><div class=\"g-row\"><div class=\"bt\" data-group><span class=\"on\" data-item>列表</span><span data-item>拓扑</span><span data-item>地图</span></div></div></div>\n</div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "类型",
    "规则",
    "Don't"
   ],
   "rules": [
    "有明确互斥关系时使用。",
    "选项数量少且可直接比较时使用。",
    "标签长或需要说明时使用纵向布局。",
    "选项短且数量少时可横向布局。",
    "有安全默认值时设置默认选中。",
    "选项需要补充解释时，使用带描述单选。"
   ]
  },
  {
   "id": "search",
   "name": "Search 搜索框",
   "desc": "用于检索表格、列表、全局内容或指定范围的数据。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/search.html",
      "lang": "html",
      "code": "<style>\n.s{width:260px;height:32px;border:1px solid #C9C9C9;border-radius:var(--r-a);display:flex;align-items:center;gap:6px;padding:0 10px;background:#fff;transition:border-color .15s}\n.s:hover,.s:focus-within{border-color:var(--p)}.s input{border:0;outline:0;flex:1;font:inherit;font-size:14px;color:var(--t1);background:none}\n.s i{font-style:normal;color:#777}.s.fill{background:#F3F3F3;border-color:transparent}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">默认 / 填充</div><div class=\"g-row\"><label class=\"s\"><i>⌕</i><input placeholder=\"搜索设备名称 / 编号\"></label><label class=\"s fill\"><i>⌕</i><input placeholder=\"搜索\"></label></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "结构",
    "使用",
    "交互",
    "Don't"
   ],
   "rules": [
    "Placeholder",
    "表格工具栏中搜索框保持紧凑。",
    "页面主要任务是搜索时，可以使用更宽搜索框。",
    "如果搜索范围不明确，应提供范围选择或提示。",
    "复杂条件不要塞进搜索框，放入筛选面板或高级筛选。",
    "全局搜索放在 Header 或页面顶部，但只在搜索是高频任务时出现。"
   ]
  },
  {
   "id": "side_navigation",
   "name": "Side Navigation 侧边导航",
   "desc": "用于产品分区、模块入口和工作区级导航。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/side_navigation.html",
      "lang": "html",
      "code": "<style>\n.sd{width:248px;background:#fff;box-shadow:var(--sh);border-radius:var(--r-c);padding:8px;font-size:14px}\n.sd div{height:40px;display:flex;align-items:center;gap:10px;padding:0 12px;border-radius:var(--r-a);cursor:pointer}.sd div:hover{background:#F3F3F3}\n.sd div.on{background:#E6F2FD;color:var(--p);font-weight:500}.sd .sub{padding-left:36px;font-size:13px;height:34px}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">侧边导航（宽 15.5rem）</div><div class=\"sd\" data-group><div data-item>▣ 总览</div><div class=\"on\" data-item>▤ 设备管理</div><div class=\"sub\" data-item>路由器</div><div class=\"sub\" data-item>交换机</div><div data-item>△ 告警中心</div><div data-item>☰ 工单</div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "规则",
    "布局",
    "Don't"
   ],
   "rules": [
    "默认宽度：`15.5rem`。",
    "折叠宽度：`3rem`。",
    "使用 `bg-surface-container-highest`。",
    "支持图标、文本、分组、层级、折叠。",
    "Active 状态清晰但克制。",
    "展开态用于多模块管理、运维后台、配置平台等需要长期导航的页面。"
   ]
  },
  {
   "id": "switch",
   "name": "Switch 开关",
   "desc": "用于立即生效的开/关设置。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/switch.html",
      "lang": "html",
      "code": "<style>\n.sw{width:36px;height:20px;border-radius:10px;background:#C9C9C9;position:relative;cursor:pointer;transition:background .2s;display:inline-block}\n.sw::after{content:\"\";position:absolute;left:2px;top:2px;width:16px;height:16px;border-radius:50%;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.2);transition:left .2s}\n.sw.on{background:var(--p)}.sw.on::after{left:18px}.sw:hover{filter:brightness(.95)}\n.sw.dis{opacity:.4;pointer-events:none}.sw.sm{width:28px;height:16px}.sw.sm::after{width:12px;height:12px}.sw.sm.on::after{left:14px}\n.lb{display:inline-flex;align-items:center;gap:8px;font-size:14px}\n</style>\n<div class=\"g\">\n<div class=\"g-sec\"><div class=\"g-label\">状态（点击切换）</div><div class=\"g-row\"><span class=\"sw on\" data-toggle></span><span class=\"sw\" data-toggle></span><span class=\"sw on dis\"></span><span class=\"sw dis\"></span></div></div>\n<div class=\"g-sec\"><div class=\"g-label\">尺寸 · 带文字</div><div class=\"g-row\"><span class=\"sw sm on\" data-toggle></span><label class=\"lb\"><span class=\"sw on\" data-toggle></span>自动告警</label></div></div>\n</div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "规则",
    "Don't"
   ],
   "rules": [
    "适合 enable/disable、on/off、open/closed。",
    "异步切换需要 loading 或反馈。",
    "文案不明确时必须有 Label。",
    "设置项列表中 Switch 通常放在行尾，Label 和说明放在行首。",
    "批量或高风险开关切换后，应提示影响范围。",
    "如果切换需要先填写其他字段，不要使用立即生效 Switch，改用表单提交。"
   ]
  },
  {
   "id": "table",
   "name": "Table 表格",
   "desc": "用于密集、可比较、基于行的企业数据。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/table.html",
      "lang": "html",
      "code": "<style>\n.tw{width:640px;background:#fff;border-radius:var(--r-c);box-shadow:var(--sh);padding:12px 16px}\ntable{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;font-weight:500;color:#777;background:#F3F3F3;height:40px;padding:0 12px}\ntd{height:44px;padding:0 12px;border-bottom:1px solid #F3F3F3}tr:hover td{background:#F7FAFE}\ntd a{color:var(--p);margin-right:12px;cursor:pointer}.st{display:inline-flex;align-items:center;gap:6px}.st i{width:6px;height:6px;border-radius:50%}\n.pg{display:flex;justify-content:flex-end;gap:6px;margin-top:10px;font-size:12px}.pg span{min-width:24px;height:24px;border:1px solid #C9C9C9;border-radius:var(--r-a);display:flex;align-items:center;justify-content:center}.pg .on{background:var(--p);color:#fff;border-color:var(--p)}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">数据表格（放在卡片容器内，行悬停高亮）</div><div class=\"tw\"><table>\n<tr><th>设备编号</th><th>类型</th><th>状态</th><th>操作</th></tr>\n<tr><td>HW-ROUTER-0192</td><td>核心路由器</td><td><span class=\"st\"><i style=\"background:#09AA71\"></i>运行中</span></td><td><a>详情</a><a>编辑</a></td></tr>\n<tr><td>HW-SWITCH-2048</td><td>汇聚交换机</td><td><span class=\"st\"><i style=\"background:#FCC800\"></i>告警</span></td><td><a>详情</a><a>编辑</a></td></tr>\n<tr><td>HW-FW-0778</td><td>防火墙</td><td><span class=\"st\"><i style=\"background:var(--err)\"></i>离线</span></td><td><a>详情</a><a>编辑</a></td></tr>\n</table><div class=\"pg\"><span>‹</span><span class=\"on\">1</span><span>2</span><span>›</span></div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "容器",
    "列宽",
    "操作",
    "Don't"
   ],
   "rules": [
    "必须放在 `bg-surface-container-highest` 内。",
    "不要直接放在页面最低层画布上。",
    "表格内容使用 `text-md`。",
    "默认有分页；分页未显式控制时需要保留下方间距。",
    "只有冻结列可设置 `width`。",
    "长文本列可设置 `minWidth`。"
   ]
  },
  {
   "id": "tabs",
   "name": "Tabs 页签",
   "desc": "用于同一上下文中同级内容切换。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/tabs.html",
      "lang": "html",
      "code": "<style>\n.tb{display:flex;gap:24px;border-bottom:1px solid #F3F3F3;width:420px}.tb span{padding:8px 0;font-size:14px;color:#777;cursor:pointer;position:relative}\n.tb span:hover{color:var(--t1)}.tb span.on{color:var(--p);font-weight:500}.tb span.on::after{content:\"\";position:absolute;left:0;right:0;bottom:-1px;height:2px;background:var(--p)}\n.cp{display:inline-flex;background:#F3F3F3;border-radius:var(--r-a);padding:2px}.cp span{padding:4px 14px;font-size:13px;border-radius:var(--r-a);cursor:pointer;color:#777}.cp span.on{background:#fff;color:var(--t1);box-shadow:0 1px 3px rgba(0,0,0,.08)}\n</style>\n<div class=\"g\">\n<div class=\"g-sec\"><div class=\"g-label\">线条页签 line</div><div class=\"tb\" data-group><span class=\"on\" data-item>概览</span><span data-item>告警 12</span><span data-item>日志</span><span data-item>配置</span></div></div>\n<div class=\"g-sec\"><div class=\"g-label\">胶囊页签 capsule</div><div class=\"cp\" data-group><span class=\"on\" data-item>日</span><span data-item>周</span><span data-item>月</span></div></div>\n</div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "类型",
    "规则",
    "文案",
    "Don't"
   ],
   "rules": [
    "Line Tabs：标准内容分区。",
    "Button/Segmented Tabs：紧凑模式切换。",
    "Card/Container Tabs：需要强分组的内容区域。",
    "Tabs 靠近其控制内容。",
    "Active 状态在 tab 组内最强。",
    "Hover、disabled、overflow 状态明确。"
   ]
  },
  {
   "id": "tag",
   "name": "Tag 标签",
   "desc": "用于分类、属性、轻量状态或筛选条件。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/tag.html",
      "lang": "html",
      "code": "<style>\n.tg{height:24px;padding:0 8px;border-radius:var(--r-a);font-size:12px;display:inline-flex;align-items:center;gap:4px}\n.tg.i{background:#E6F2FD;color:var(--p)}.tg.s{background:#E7FBF2;color:#09AA71}.tg.w{background:#FEFCE0;color:#A27F00}.tg.c{background:#FEF5E8;color:#F4840C}.tg.e{background:#FEE7E8;color:var(--err)}.tg.d{background:#F3F3F3;color:#777}\n.tg.o{background:#fff;border:1px solid #C9C9C9;color:var(--t1)}.tg .x{cursor:pointer;opacity:.6}.tg .x:hover{opacity:1}\n.tg.sm{height:20px;font-size:11px;padding:0 6px}\n</style>\n<div class=\"g\">\n<div class=\"g-sec\"><div class=\"g-label\">语义 color</div><div class=\"g-row\"><span class=\"tg i\">进行中</span><span class=\"tg s\">已完成</span><span class=\"tg w\">待处理</span><span class=\"tg c\">严重</span><span class=\"tg e\">异常</span><span class=\"tg d\">已关闭</span></div></div>\n<div class=\"g-sec\"><div class=\"g-label\">可关闭 · 尺寸</div><div class=\"g-row\"><span class=\"tg o\">北京机房<span class=\"x\" onclick=\"this.parentNode.remove()\">✕</span></span><span class=\"tg o\">上海机房<span class=\"x\" onclick=\"this.parentNode.remove()\">✕</span></span><span class=\"tg i sm\">sm</span></div></div>\n</div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "文案",
    "类型",
    "规则",
    "Don't"
   ],
   "rules": [
    "中文标签通常控制在 10 个字以内。",
    "长含义应改写为短标签，并在详情或 Tooltip 中解释。",
    "只读 Tag 用于展示属性、分类、环境、版本、状态等短信息。",
    "可选 Tag 用于筛选条件或轻量选择。",
    "可关闭 Tag 用于已选条件、已添加对象、可移除属性。",
    "语义色只在表达状态时使用。"
   ]
  },
  {
   "id": "timeline",
   "name": "Timeline 时间轴",
   "desc": "用于时间顺序事件、操作历史、流程记录和状态流转。",
   "source": {
    "status": "generated",
    "expected": [],
    "files": [
     {
      "path": "generated/timeline.html",
      "lang": "html",
      "code": "<style>\n.tl{width:360px;font-size:14px}.it{display:flex;gap:12px;position:relative;padding-bottom:16px}.it:not(:last-child)::before{content:\"\";position:absolute;left:5px;top:16px;bottom:0;width:1px;background:#F3F3F3}\n.it i{width:11px;height:11px;border-radius:50%;border:2px solid var(--p);background:#fff;margin-top:5px;flex-shrink:0;box-sizing:border-box}.it.ok i{border-color:#09AA71}.it.er i{border-color:var(--err)}\n.it small{display:block;color:#777;font-size:12px}\n</style>\n<div class=\"g\"><div class=\"g-sec\"><div class=\"g-label\">时间轴</div><div class=\"tl\">\n<div class=\"it ok\"><i></i><div>工单已关闭<small>2026-10-28 10:24 · 张工</small></div></div>\n<div class=\"it\"><i></i><div>已派单至一线运维<small>2026-10-28 09:10</small></div></div>\n<div class=\"it er\"><i></i><div>检测到链路中断<small>2026-10-28 08:52</small></div></div></div></div></div>\n"
     }
    ]
   },
   "props": [],
   "sections": [
    "用途",
    "规则",
    "Don't"
   ],
   "rules": [
    "时间、标题、描述、状态对齐。",
    "历史和流程日志使用纵向布局。",
    "事件状态有意义时才使用语义色。",
    "类型复杂时可使用图标或语义标记。",
    "操作记录、审批流、部署进度、故障处理过程适合 Timeline。",
    "当前进行中的节点需要清晰标识，已完成和未开始节点弱化。"
   ]
  }
 ]
}
```

## 资产 {#assets}

> 未定义：规范 Skill 中没有提取到这部分内容。

## 布局 Pattern {#patterns}

> 未定义：规范 Skill 中没有提取到这部分内容。

## Pixso 映射 {#mapping}

> 未定义：规范 Skill 中没有提取到这部分内容。
