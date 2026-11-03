---
format: octo-design-md/1
id: text-to-ui
name: "HarmonyOS PC 客户端规范（text-to-ui-html）"
author: "ahai66666"
cover: cover-cyan.jpg
usage: 0
order: 7
source_skill: "HarmonyOS PC 客户端规范（text-to-ui-html）"
adapter: text-to-ui-html
source_files: "585"
source_size: "5.1 MB"
source_entry: "apps/component-gallery（组件预览页）+ pattern-contracts.json"
---

# HarmonyOS PC 客户端规范（text-to-ui-html）

> 由 spec-skill-to-design-system 从规范 Skill 转换生成。每个区块的正文是说明和使用规则，`json design` 数据块供管理页渲染；
> 标注「未定义」的区块表示规范里没有提取到这部分内容。

## 概览 {#overview}

用于生成和修改 HarmonyOS PC 动态 HTML 页面，或把已确认的交互 Demo 规范化为标准组件、Pattern 和 Token 的实现。交付物包括独立的组件与 CSS、浏览器验证截图，以及带版本号的交接包。

### 设计原则

> 来源：references/interaction-spec.md「Official Platform Principles」

- 支持与设备相匹配的多模态输入，在 HarmonyOS PC 上包括鼠标、触控板和键盘。
- 交互与当前状态保持一致，并符合用户熟悉的输入习惯。
- 在适用时考虑自由窗口、全屏、分屏、悬浮窗、多任务和窗口拖拽等场景。
- 在支持的各种窗口模式和尺寸下，保持布局质量和任务连续性。
- 通过响应式和自适应能力重新组织内容，而不是简单地拉伸。
- 用动效说明状态变化、引导下一步操作，并缓解等待时的不适感。
- 当声音反馈能改善信息传达时，考虑加入声音反馈。
- 在交互设计中纳入无障碍需求。
- 适用时优先使用 HarmonyOS 系统组件、窗口模式、系统资源和平台能力。

## 颜色 {#color}

153 个颜色 token：7 组基础色阶 + 97 个语义色。

### 使用规则

- 语义色只引用基础色阶（如 `text → neutral-dark.90`），页面和组件使用语义 token，不写死色值。
- 带透明度的色阶（05~90）用于叠加层与弱化背景，100 为实色。

```json design
{
 "title": "语义色",
 "themes": [
  "light"
 ],
 "palettes": [
  {
   "title": "品牌蓝 brand",
   "steps": [
    {
     "name": "brand-05",
     "value": "#0A59F70C",
     "token": "--color-brand-05"
    },
    {
     "name": "brand-10",
     "value": "#0A59F719",
     "token": "--color-brand-10"
    },
    {
     "name": "brand-15",
     "value": "#0A59F726",
     "token": "--color-brand-15"
    },
    {
     "name": "brand-20",
     "value": "#0A59F733",
     "token": "--color-brand-20"
    },
    {
     "name": "brand-30",
     "value": "#0A59F74D",
     "token": "--color-brand-30"
    },
    {
     "name": "brand-40",
     "value": "#0A59F766",
     "token": "--color-brand-40"
    },
    {
     "name": "brand-50",
     "value": "#0A59F77F",
     "token": "--color-brand-50"
    },
    {
     "name": "brand-60",
     "value": "#0A59F799",
     "token": "--color-brand-60"
    },
    {
     "name": "brand-70",
     "value": "#0A59F7B2",
     "token": "--color-brand-70"
    },
    {
     "name": "brand-80",
     "value": "#0A59F7CC",
     "token": "--color-brand-80"
    },
    {
     "name": "brand-90",
     "value": "#0A59F7E5",
     "token": "--color-brand-90"
    },
    {
     "name": "brand-100",
     "value": "#0A59F7FF",
     "token": "--color-brand-100"
    }
   ]
  },
  {
   "title": "深色中性 neutral-dark",
   "steps": [
    {
     "name": "neutral-dark-05",
     "value": "#0000000C",
     "token": "--color-neutral-dark-05"
    },
    {
     "name": "neutral-dark-10",
     "value": "#00000019",
     "token": "--color-neutral-dark-10"
    },
    {
     "name": "neutral-dark-15",
     "value": "#00000026",
     "token": "--color-neutral-dark-15"
    },
    {
     "name": "neutral-dark-20",
     "value": "#00000033",
     "token": "--color-neutral-dark-20"
    },
    {
     "name": "neutral-dark-30",
     "value": "#0000004D",
     "token": "--color-neutral-dark-30"
    },
    {
     "name": "neutral-dark-40",
     "value": "#00000066",
     "token": "--color-neutral-dark-40"
    },
    {
     "name": "neutral-dark-50",
     "value": "#0000007F",
     "token": "--color-neutral-dark-50"
    },
    {
     "name": "neutral-dark-60",
     "value": "#00000099",
     "token": "--color-neutral-dark-60"
    },
    {
     "name": "neutral-dark-70",
     "value": "#000000B2",
     "token": "--color-neutral-dark-70"
    },
    {
     "name": "neutral-dark-80",
     "value": "#000000CC",
     "token": "--color-neutral-dark-80"
    },
    {
     "name": "neutral-dark-90",
     "value": "#000000E5",
     "token": "--color-neutral-dark-90"
    },
    {
     "name": "neutral-dark-100",
     "value": "#000000FF",
     "token": "--color-neutral-dark-100"
    }
   ]
  },
  {
   "title": "浅色中性 neutral-light",
   "steps": [
    {
     "name": "neutral-light-05",
     "value": "#FFFFFF0C",
     "token": "--color-neutral-light-05"
    },
    {
     "name": "neutral-light-10",
     "value": "#FFFFFF19",
     "token": "--color-neutral-light-10"
    },
    {
     "name": "neutral-light-15",
     "value": "#FFFFFF26",
     "token": "--color-neutral-light-15"
    },
    {
     "name": "neutral-light-20",
     "value": "#FFFFFF33",
     "token": "--color-neutral-light-20"
    },
    {
     "name": "neutral-light-30",
     "value": "#FFFFFF4D",
     "token": "--color-neutral-light-30"
    },
    {
     "name": "neutral-light-40",
     "value": "#FFFFFF66",
     "token": "--color-neutral-light-40"
    },
    {
     "name": "neutral-light-50",
     "value": "#FFFFFF7F",
     "token": "--color-neutral-light-50"
    },
    {
     "name": "neutral-light-60",
     "value": "#FFFFFF99",
     "token": "--color-neutral-light-60"
    },
    {
     "name": "neutral-light-70",
     "value": "#FFFFFFB2",
     "token": "--color-neutral-light-70"
    },
    {
     "name": "neutral-light-80",
     "value": "#FFFFFFCC",
     "token": "--color-neutral-light-80"
    },
    {
     "name": "neutral-light-90",
     "value": "#FFFFFFE5",
     "token": "--color-neutral-light-90"
    },
    {
     "name": "neutral-light-100",
     "value": "#FFFFFFFF",
     "token": "--color-neutral-light-100"
    }
   ]
  },
  {
   "title": "功能色 success",
   "steps": [
    {
     "name": "success-10",
     "value": "#64BB5C19"
    },
    {
     "name": "success-20",
     "value": "#64BB5C33"
    },
    {
     "name": "success-100",
     "value": "#64BB5CFF"
    }
   ]
  },
  {
   "title": "功能色 warning",
   "steps": [
    {
     "name": "warning-10",
     "value": "#ED6F2119",
     "token": "--color-warning-10"
    },
    {
     "name": "warning-20",
     "value": "#ED6F2133",
     "token": "--color-warning-20"
    },
    {
     "name": "warning-100",
     "value": "#ED6F21FF"
    }
   ]
  },
  {
   "title": "功能色 danger",
   "steps": [
    {
     "name": "danger-10",
     "value": "#E8402619"
    },
    {
     "name": "danger-20",
     "value": "#E8402633"
    },
    {
     "name": "danger-100",
     "value": "#E84026FF"
    }
   ]
  },
  {
   "title": "多彩色 multi",
   "steps": [
    {
     "name": "multi-01",
     "value": "#564AF7",
     "token": "--color-multi-01"
    },
    {
     "name": "multi-02",
     "value": "#46B1E3",
     "token": "--color-multi-02"
    },
    {
     "name": "multi-03",
     "value": "#61CFBE",
     "token": "--color-multi-03"
    },
    {
     "name": "multi-04",
     "value": "#A5D61D",
     "token": "--color-multi-04"
    },
    {
     "name": "multi-05",
     "value": "#AC49F5",
     "token": "--color-multi-05"
    },
    {
     "name": "multi-06",
     "value": "#E64566",
     "token": "--color-multi-06"
    },
    {
     "name": "multi-07",
     "value": "#F9A01E",
     "token": "--color-multi-07"
    },
    {
     "name": "multi-08",
     "value": "#F7CE00",
     "token": "--color-multi-08"
    },
    {
     "name": "multi-09",
     "value": "#64BB5C",
     "token": "--color-multi-09"
    },
    {
     "name": "multi-10",
     "value": "#E84026",
     "token": "--color-multi-10"
    },
    {
     "name": "multi-11",
     "value": "#ED6F21",
     "token": "--color-multi-11"
    }
   ]
  }
 ],
 "groups": [
  {
   "title": "品牌与状态色",
   "desc": "主色、焦点与成功 / 警告 / 危险 / 信息",
   "kind": "cards",
   "tokens": [
    {
     "name": "accent",
     "token": "--color-accent",
     "value": "#0A59F7FF",
     "ref": "brand.100"
    },
    {
     "name": "focus-ring",
     "token": "--color-focus-ring",
     "value": "#0A59F7FF",
     "ref": "brand.100"
    },
    {
     "name": "primary",
     "token": "--color-primary",
     "value": "#0A59F7FF",
     "ref": "brand.100"
    },
    {
     "name": "primary-text",
     "token": "--color-primary-text",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "success",
     "token": "--color-success",
     "value": "#64BB5CFF",
     "ref": "function.success.100"
    },
    {
     "name": "success-subtle",
     "token": "--color-success-subtle",
     "value": "#64BB5C19",
     "ref": "function.success.10"
    },
    {
     "name": "warning",
     "token": "--color-warning",
     "value": "#ED6F21FF",
     "ref": "function.warning.100"
    },
    {
     "name": "warning-subtle",
     "token": "--color-warning-subtle",
     "value": "#ED6F2119",
     "ref": "function.warning.10"
    },
    {
     "name": "danger",
     "token": "--color-danger",
     "value": "#E84026FF",
     "ref": "function.danger.100"
    },
    {
     "name": "danger-subtle",
     "token": "--color-danger-subtle",
     "value": "#E8402619",
     "ref": "function.danger.10"
    },
    {
     "name": "info",
     "token": "--color-info",
     "value": "#0A59F7FF",
     "ref": "brand.100"
    },
    {
     "name": "info-subtle",
     "token": "--color-info-subtle",
     "value": "#0A59F719",
     "ref": "brand.10"
    }
   ]
  },
  {
   "title": "背景与表面",
   "desc": "页面、容器、浮层的层级背景",
   "kind": "cards",
   "tokens": [
    {
     "name": "bg",
     "token": "--color-bg",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "bg-subtle",
     "token": "--color-bg-subtle",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "surface",
     "token": "--color-surface",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "surface-raised",
     "token": "--color-surface-raised",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "surface-muted",
     "token": "--color-surface-muted",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "overlay",
     "token": "--color-overlay",
     "value": "#00000066",
     "ref": "neutral-dark.40"
    },
    {
     "name": "dialog-bg",
     "token": "--color-dialog-bg",
     "value": "#FFFFFFFF",
     "ref": "surface-raised"
    },
    {
     "name": "modal-bg-white",
     "token": "--color-modal-bg-white",
     "value": "#FFFFFFFF",
     "ref": "surface-raised"
    },
    {
     "name": "modal-bg-gray",
     "token": "--color-modal-bg-gray",
     "value": "#0000000C",
     "ref": "surface-muted"
    },
    {
     "name": "secondary",
     "token": "--color-secondary",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "secondary-hover",
     "token": "--color-secondary-hover",
     "value": "#00000019",
     "ref": "neutral-dark.10"
    }
   ]
  },
  {
   "title": "文字与图标",
   "desc": "正文、次要、弱化、反白文字与图标",
   "kind": "cards",
   "tokens": [
    {
     "name": "icon-text-button-ghost-bg",
     "token": "--color-icon-text-button-ghost-bg",
     "value": "transparent",
     "ref": "transparent"
    },
    {
     "name": "icon-text-button-ghost-hover-bg",
     "token": "--color-icon-text-button-ghost-hover-bg",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "icon-text-button-ghost-content",
     "token": "--color-icon-text-button-ghost-content",
     "value": "#000000E5",
     "ref": "neutral-dark.90"
    },
    {
     "name": "text",
     "token": "--color-text",
     "value": "#000000E5",
     "ref": "neutral-dark.90"
    },
    {
     "name": "text-muted",
     "token": "--color-text-muted",
     "value": "#00000099",
     "ref": "neutral-dark.60"
    },
    {
     "name": "text-subtle",
     "token": "--color-text-subtle",
     "value": "#00000066",
     "ref": "neutral-dark.40"
    },
    {
     "name": "text-inverse",
     "token": "--color-text-inverse",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "text-brand",
     "token": "--color-text-brand",
     "value": "#0A59F7FF",
     "ref": "brand.100"
    },
    {
     "name": "link",
     "token": "--color-link",
     "value": "#000000FF",
     "ref": "neutral-dark.100"
    },
    {
     "name": "icon",
     "token": "--color-icon",
     "value": "#000000E5",
     "ref": "neutral-dark.90"
    },
    {
     "name": "icon-muted",
     "token": "--color-icon-muted",
     "value": "#00000099",
     "ref": "neutral-dark.60"
    },
    {
     "name": "primary-level-unselected",
     "token": "--color-primary-level-unselected",
     "value": "#00000066",
     "ref": "icon-subtle"
    },
    {
     "name": "icon-subtle",
     "token": "--color-icon-subtle",
     "value": "#00000066",
     "ref": "neutral-dark.40"
    },
    {
     "name": "icon-inverse",
     "token": "--color-icon-inverse",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    }
   ]
  },
  {
   "title": "描边与分割",
   "desc": "描边、分割线",
   "kind": "cards",
   "tokens": [
    {
     "name": "border",
     "token": "--color-border",
     "value": "#00000019",
     "ref": "neutral-dark.10"
    },
    {
     "name": "divider",
     "token": "--color-divider",
     "value": "#00000033",
     "ref": "neutral-dark.20"
    }
   ]
  },
  {
   "title": "交互状态层",
   "desc": "悬停、按下、选中、聚焦叠加层",
   "kind": "cards",
   "tokens": [
    {
     "name": "state-layer-hover",
     "token": "--color-state-layer-hover",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "state-layer-pressed",
     "token": "--color-state-layer-pressed",
     "value": "#00000019",
     "ref": "neutral-dark.10"
    },
    {
     "name": "state-layer-selected",
     "token": "--color-state-layer-selected",
     "value": "#00000019",
     "ref": "neutral-dark.10"
    },
    {
     "name": "state-layer-focus",
     "token": "--color-state-layer-focus",
     "value": "#0A59F719",
     "ref": "brand.10"
    }
   ]
  },
  {
   "title": "组件色",
   "desc": "按钮、输入框、页签、侧栏、提示等组件专用色",
   "kind": "cards",
   "tokens": [
    {
     "name": "titlebar-normal-bg",
     "token": "--color-titlebar-normal-bg",
     "value": "transparent",
     "ref": "transparent"
    },
    {
     "name": "titlebar-unfocus-bg",
     "token": "--color-titlebar-unfocus-bg",
     "value": "transparent",
     "ref": "transparent"
    },
    {
     "name": "button-secondary-bg",
     "token": "--color-button-secondary-bg",
     "value": "#0000000C",
     "ref": "secondary"
    },
    {
     "name": "button-secondary-hover-bg",
     "token": "--color-button-secondary-hover-bg",
     "value": "#00000019",
     "ref": "secondary-hover"
    },
    {
     "name": "button-secondary-text",
     "token": "--color-button-secondary-text",
     "value": "#000000E5",
     "ref": "text"
    },
    {
     "name": "button-ghost-bg",
     "token": "--color-button-ghost-bg",
     "value": "transparent",
     "ref": "transparent"
    },
    {
     "name": "button-ghost-hover-bg",
     "token": "--color-button-ghost-hover-bg",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "button-ghost-text",
     "token": "--color-button-ghost-text",
     "value": "#0A59F7FF",
     "ref": "brand.100"
    },
    {
     "name": "button-danger-bg",
     "token": "--color-button-danger-bg",
     "value": "#0000000C",
     "ref": "secondary"
    },
    {
     "name": "button-danger-hover-bg",
     "token": "--color-button-danger-hover-bg",
     "value": "#00000019",
     "ref": "secondary-hover"
    },
    {
     "name": "button-danger-text",
     "token": "--color-button-danger-text",
     "value": "#E84026FF",
     "ref": "function.danger.100"
    },
    {
     "name": "sidebar-bg",
     "token": "--color-sidebar-bg",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "sidebar-accent",
     "token": "--color-sidebar-accent",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "sidebar-accent-text",
     "token": "--color-sidebar-accent-text",
     "value": "#0A59F7FF",
     "ref": "brand.100"
    },
    {
     "name": "sidebar-selected",
     "token": "--color-sidebar-selected",
     "value": "#0A59F719",
     "ref": "brand.10"
    },
    {
     "name": "sidebar-selected-text",
     "token": "--color-sidebar-selected-text",
     "value": "#0A59F7FF",
     "ref": "brand.100"
    },
    {
     "name": "tab-list-bg",
     "token": "--color-tab-list-bg",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "tab-text",
     "token": "--color-tab-text",
     "value": "#00000099",
     "ref": "neutral-dark.60"
    },
    {
     "name": "tab-hover-bg",
     "token": "--color-tab-hover-bg",
     "value": "#00000019",
     "ref": "neutral-dark.10"
    },
    {
     "name": "tab-selected-bg",
     "token": "--color-tab-selected-bg",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "tab-selected-text",
     "token": "--color-tab-selected-text",
     "value": "#000000E5",
     "ref": "neutral-dark.90"
    },
    {
     "name": "tooltip-bg",
     "token": "--color-tooltip-bg",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "tooltip-text",
     "token": "--color-tooltip-text",
     "value": "#000000E5",
     "ref": "neutral-dark.90"
    },
    {
     "name": "input-bg",
     "token": "--color-input-bg",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "input-border",
     "token": "--color-input-border",
     "value": "transparent",
     "ref": "transparent"
    },
    {
     "name": "input-bg-on-default",
     "token": "--color-input-bg-on-default",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "input-hover-bg",
     "token": "--color-input-hover-bg",
     "value": "#00000019",
     "ref": "neutral-dark.10"
    },
    {
     "name": "input-hover-bg-on-default",
     "token": "--color-input-hover-bg-on-default",
     "value": "#00000019",
     "ref": "neutral-dark.10"
    },
    {
     "name": "input-focus-bg",
     "token": "--color-input-focus-bg",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "input-focus-bg-on-default",
     "token": "--color-input-focus-bg-on-default",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "input-error-bg",
     "token": "--color-input-error-bg",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "input-error-bg-on-default",
     "token": "--color-input-error-bg-on-default",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "input-bg-on-subtle",
     "token": "--color-input-bg-on-subtle",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "input-hover-border-on-subtle",
     "token": "--color-input-hover-border-on-subtle",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "input-focus-bg-on-subtle",
     "token": "--color-input-focus-bg-on-subtle",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "input-error-bg-on-subtle",
     "token": "--color-input-error-bg-on-subtle",
     "value": "#FFFFFFFF",
     "ref": "neutral-light.100"
    },
    {
     "name": "input-error-border",
     "token": "--color-input-error-border",
     "value": "#E84026FF",
     "ref": "function.danger.100"
    },
    {
     "name": "alert-neutral",
     "token": "--color-alert-neutral",
     "value": "#00000099",
     "ref": "text-muted"
    },
    {
     "name": "alert-neutral-subtle",
     "token": "--color-alert-neutral-subtle",
     "value": "#0000000C",
     "ref": "neutral-dark.05"
    },
    {
     "name": "badge-neutral-text",
     "token": "--color-badge-neutral-text",
     "value": "#00000099",
     "ref": "text-muted"
    },
    {
     "name": "badge-neutral-bg",
     "token": "--color-badge-neutral-bg",
     "value": "#00000019",
     "ref": "neutral-dark.10"
    },
    {
     "name": "badge-info-text",
     "token": "--color-badge-info-text",
     "value": "#0A59F7FF",
     "ref": "info"
    },
    {
     "name": "badge-info-bg",
     "token": "--color-badge-info-bg",
     "value": "#0A59F719",
     "ref": "brand.10"
    },
    {
     "name": "badge-success-text",
     "token": "--color-badge-success-text",
     "value": "#64BB5CFF",
     "ref": "function.success.100"
    },
    {
     "name": "badge-success-bg",
     "token": "--color-badge-success-bg",
     "value": "#64BB5C19",
     "ref": "function.success.10"
    },
    {
     "name": "badge-warning-text",
     "token": "--color-badge-warning-text",
     "value": "#ED6F21FF",
     "ref": "function.warning.100"
    },
    {
     "name": "badge-warning-bg",
     "token": "--color-badge-warning-bg",
     "value": "#ED6F2119",
     "ref": "function.warning.10"
    },
    {
     "name": "badge-danger-text",
     "token": "--color-badge-danger-text",
     "value": "#E84026FF",
     "ref": "function.danger.100"
    },
    {
     "name": "badge-danger-bg",
     "token": "--color-badge-danger-bg",
     "value": "#E8402619",
     "ref": "function.danger.10"
    }
   ]
  },
  {
   "title": "图表色",
   "desc": "数据可视化分类色",
   "kind": "cards",
   "tokens": [
    {
     "name": "chart-1",
     "token": "--color-chart-1",
     "value": "#564AF7",
     "ref": "multi.01"
    },
    {
     "name": "chart-2",
     "token": "--color-chart-2",
     "value": "#46B1E3",
     "ref": "multi.02"
    },
    {
     "name": "chart-3",
     "token": "--color-chart-3",
     "value": "#61CFBE",
     "ref": "multi.03"
    },
    {
     "name": "chart-4",
     "token": "--color-chart-4",
     "value": "#A5D61D",
     "ref": "multi.04"
    },
    {
     "name": "chart-5",
     "token": "--color-chart-5",
     "value": "#AC49F5",
     "ref": "multi.05"
    }
   ]
  }
 ]
}
```

## 字体 {#typography}

13 级文字样式，字体家族 HarmonyOS Sans。

### 使用规则

- 组件通过 `data-typography-role` 引用文字样式（如 body-l / subtitle-m），不直接写字号。

```json design
{
 "title": "字体层级",
 "families": [
  "HarmonyOS Sans",
  "HarmonyOS Sans SC"
 ],
 "weights": [
  400,
  500,
  700
 ],
 "scale": [
  {
   "name": "display-l",
   "token": "--type-display-l",
   "size": 56,
   "lineHeight": 66,
   "weight": 400,
   "family": "HarmonyOS Sans",
   "desc": "展示类标题 · 大号展示标题"
  },
  {
   "name": "display-m",
   "token": "--type-display-m",
   "size": 48,
   "lineHeight": 58,
   "weight": 400,
   "family": "HarmonyOS Sans",
   "desc": "展示类标题 · 中号展示标题"
  },
  {
   "name": "display-s",
   "token": "--type-display-s",
   "size": 38,
   "lineHeight": 44,
   "weight": 400,
   "family": "HarmonyOS Sans",
   "desc": "展示类标题 · 小号展示标题"
  },
  {
   "name": "title-l",
   "token": "--type-title-l",
   "size": 30,
   "lineHeight": 36,
   "weight": 700,
   "family": "HarmonyOS Sans",
   "desc": "主标题 · 页面主标题"
  },
  {
   "name": "title-m",
   "token": "--type-title-m",
   "size": 24,
   "lineHeight": 28,
   "weight": 700,
   "family": "HarmonyOS Sans",
   "desc": "主标题 · 标题栏文本"
  },
  {
   "name": "title-s",
   "token": "--type-title-s",
   "size": 20,
   "lineHeight": 24,
   "weight": 700,
   "family": "HarmonyOS Sans",
   "desc": "主标题 · 卡片标题、半模态弹窗标题、弹窗标题"
  },
  {
   "name": "subtitle-l",
   "token": "--type-subtitle-l",
   "size": 18,
   "lineHeight": 22,
   "weight": 500,
   "family": "HarmonyOS Sans",
   "desc": "次标题 · 普通内容子标题、菜单标题"
  },
  {
   "name": "subtitle-m",
   "token": "--type-subtitle-m",
   "size": 16,
   "lineHeight": 20,
   "weight": 500,
   "family": "HarmonyOS Sans",
   "desc": "次标题 · 标题辅助文本、列表文本、气泡提示主标题"
  },
  {
   "name": "subtitle-s",
   "token": "--type-subtitle-s",
   "size": 14,
   "lineHeight": 16,
   "weight": 500,
   "family": "HarmonyOS Sans",
   "desc": "次标题 · 列表子标题、普通副标题"
  },
  {
   "name": "body-l",
   "token": "--type-body-l",
   "size": 16,
   "lineHeight": 20,
   "weight": 400,
   "family": "HarmonyOS Sans",
   "desc": "主文本 · 客户端默认正文、Sidebar、表格单元格、列表主文本、40px 菜单与操作控件"
  },
  {
   "name": "body-m",
   "token": "--type-body-m",
   "size": 14,
   "lineHeight": 16,
   "weight": 400,
   "family": "HarmonyOS Sans",
   "desc": "副文本 · 列表摘要与时间、普通描述、Toast、Tabs 与 28px Small Button"
  },
  {
   "name": "body-s",
   "token": "--type-body-s",
   "size": 12,
   "lineHeight": 14,
   "weight": 400,
   "family": "HarmonyOS Sans",
   "desc": "小号正文 · 辅助文本、次要说明"
  },
  {
   "name": "caption-m",
   "token": "--type-caption-m",
   "size": 10,
   "lineHeight": 12,
   "weight": 400,
   "family": "HarmonyOS Sans",
   "desc": "小号说明 · 极小字号的辅助说明"
  }
 ]
}
```

## 间距 {#spacing}

8 个基础间距 token，53 个场景 token 通过 ref 引用基础值。

### 使用规则

- 间距由父容器的 gap 负责，子元素不加 margin。
- 固定高度的控件只使用水平内边距，高度由尺寸 token 决定。
- 默认密度：compact。

```json design
{
 "title": "间距",
 "unit": "px",
 "tokens": [
  {
   "name": "space-0",
   "value": 0,
   "raw": "0px"
  },
  {
   "name": "space-1",
   "value": 2,
   "raw": "2px"
  },
  {
   "name": "space-2",
   "value": 4,
   "raw": "4px"
  },
  {
   "name": "space-3",
   "value": 8,
   "raw": "8px"
  },
  {
   "name": "space-4",
   "value": 12,
   "raw": "12px"
  },
  {
   "name": "space-5",
   "value": 16,
   "raw": "16px"
  },
  {
   "name": "space-6",
   "value": 24,
   "raw": "24px"
  },
  {
   "name": "space-7",
   "value": 32,
   "raw": "32px"
  }
 ],
 "scenes": [
  {
   "title": "gap",
   "tokens": [
    {
     "name": "gap-list-item",
     "value": 2,
     "ref": "space-1"
    },
    {
     "name": "gap-selection-option",
     "value": 2,
     "ref": "space-1"
    },
    {
     "name": "gap-tabs-list",
     "value": 2,
     "ref": "space-1"
    },
    {
     "name": "gap-menu-item",
     "value": 2,
     "ref": "space-1"
    },
    {
     "name": "gap-nav-item",
     "value": 2,
     "ref": "space-1"
    },
    {
     "name": "gap-button-icon-label",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "gap-button-group",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "gap-menu-item-content",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "gap-breadcrumb-item",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "gap-subtab-item",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "gap-alert-content",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "gap-field-label",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "gap-form-field",
     "value": 16,
     "ref": "space-5"
    },
    {
     "name": "gap-choice-label",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "gap-titlebar-brand",
     "value": 12,
     "ref": "space-4"
    },
    {
     "name": "gap-cross-group-control",
     "value": 16,
     "ref": "space-5"
    },
    {
     "name": "gap-menu-section",
     "value": 24,
     "ref": "space-6"
    },
    {
     "name": "gap-page-section",
     "value": 32,
     "ref": "space-7"
    }
   ]
  },
  {
   "title": "padding",
   "tokens": [
    {
     "name": "padding-segmented-control",
     "value": 2,
     "ref": "space-1"
    },
    {
     "name": "padding-popup-menu",
     "value": 4,
     "ref": "space-2"
    },
    {
     "name": "padding-list-card",
     "value": 4,
     "ref": "space-2"
    },
    {
     "name": "padding-tooltip",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-alert",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-alert-left",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-alert-right",
     "value": 4,
     "ref": "space-2"
    },
    {
     "name": "padding-selection-option",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-tab-x",
     "value": 12,
     "ref": "space-4"
    },
    {
     "name": "padding-tab-panel",
     "value": 16,
     "ref": "space-5"
    },
    {
     "name": "padding-titlebar-leading",
     "value": 24,
     "ref": "space-6"
    },
    {
     "name": "padding-titlebar-trailing-s",
     "value": 0,
     "ref": "space-0"
    },
    {
     "name": "padding-titlebar-trailing-m",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-titlebar-trailing-l",
     "value": 12,
     "ref": "space-4"
    },
    {
     "name": "padding-titlebar-trailing-xl",
     "value": 16,
     "ref": "space-5"
    },
    {
     "name": "padding-button-sm-x",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-split-button-main-x",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-split-button-trigger",
     "value": 0,
     "ref": "space-0"
    },
    {
     "name": "padding-list",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-tag-x",
     "value": 12,
     "ref": "space-4"
    },
    {
     "name": "padding-select-x",
     "value": 12,
     "ref": "space-4"
    },
    {
     "name": "padding-textarea-x",
     "value": 12,
     "ref": "space-4"
    },
    {
     "name": "padding-textarea-y",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-search-x",
     "value": 12,
     "ref": "space-4"
    },
    {
     "name": "padding-menu-item-x",
     "value": 12,
     "ref": "space-4"
    },
    {
     "name": "padding-button-x",
     "value": 16,
     "ref": "space-5"
    },
    {
     "name": "padding-card",
     "value": 24,
     "ref": "space-6"
    },
    {
     "name": "padding-table",
     "value": 24,
     "ref": "space-6"
    },
    {
     "name": "padding-dialog",
     "value": 24,
     "ref": "space-6"
    },
    {
     "name": "padding-dialog-content",
     "value": 24,
     "ref": "space-6"
    },
    {
     "name": "padding-modal-content-x",
     "value": 24,
     "ref": "space-6"
    },
    {
     "name": "padding-modal-content-y",
     "value": 0,
     "ref": "space-0"
    },
    {
     "name": "padding-modal-header-top",
     "value": 8,
     "ref": "space-3"
    },
    {
     "name": "padding-modal-header-x",
     "value": 24,
     "ref": "space-6"
    },
    {
     "name": "padding-modal-footer-x",
     "value": 24,
     "ref": "space-6"
    }
   ]
  }
 ]
}
```

## 圆角 {#radius}

7 个基础圆角 token，30 个组件圆角通过 ref 引用基础值。

```json design
{
 "title": "圆角",
 "tokens": [
  {
   "name": "radius-0",
   "value": 0,
   "raw": "0px"
  },
  {
   "name": "radius-1",
   "value": 4,
   "raw": "4px"
  },
  {
   "name": "radius-2",
   "value": 6,
   "raw": "6px"
  },
  {
   "name": "radius-3",
   "value": 8,
   "raw": "8px"
  },
  {
   "name": "radius-4",
   "value": 12,
   "raw": "12px"
  },
  {
   "name": "radius-5",
   "value": 16,
   "raw": "16px"
  },
  {
   "name": "radius-full",
   "value": 999,
   "raw": "999px"
  }
 ],
 "scenes": [
  {
   "title": "component",
   "tokens": [
    {
     "name": "radius-popup-menu-item",
     "value": 4,
     "ref": "radius-1"
    },
    {
     "name": "radius-checkbox",
     "value": 4,
     "ref": "radius-1"
    },
    {
     "name": "radius-subtab",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-sidebar-nav-item",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-button",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-icon-text-button",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-icon-button",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-status-button",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-dropdown-button",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-alert",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-select",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-input",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-textarea",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-tooltip",
     "value": 6,
     "ref": "radius-2"
    },
    {
     "name": "radius-search",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-number-input",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-tag",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-selection-block",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-selection-option",
     "value": 6,
     "ref": "radius-2"
    },
    {
     "name": "radius-tab",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-list",
     "value": 12,
     "ref": "radius-4"
    },
    {
     "name": "radius-list-item",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-badge",
     "value": 999,
     "ref": "radius-full"
    },
    {
     "name": "radius-progress",
     "value": 999,
     "ref": "radius-full"
    },
    {
     "name": "radius-avatar",
     "value": 999,
     "ref": "radius-full"
    },
    {
     "name": "radius-card",
     "value": 12,
     "ref": "radius-4"
    },
    {
     "name": "radius-table",
     "value": 12,
     "ref": "radius-4"
    },
    {
     "name": "radius-pagination-item",
     "value": 8,
     "ref": "radius-3"
    },
    {
     "name": "radius-dialog",
     "value": 16,
     "ref": "radius-5"
    },
    {
     "name": "radius-modal",
     "value": 16,
     "ref": "radius-5"
    }
   ]
  }
 ]
}
```

## 阴影 {#shadow}

6 级投影 token。

### 使用规则

- 只有浮层类组件使用投影：Snackbar、Tooltip、Popover、Hover Card、Dialog、Alert Dialog、Semi-modal、Dropdown Menu、Context Menu。
- 其余场景默认不加投影，用描边或表面色对比区分层级。

```json design
{
 "title": "阴影",
 "tokens": [
  {
   "name": "shadow-1",
   "token": "--shadow-1",
   "value": "0 0 4px 0 rgb(0 0 30 / 15%)",
   "desc": "用于 snackbar / tooltip"
  },
  {
   "name": "shadow-2",
   "token": "--shadow-2",
   "value": "0 0 20px 0 rgb(0 0 30 / 8%)",
   "desc": "用于 popover / hover-card / dropdown-menu"
  },
  {
   "name": "shadow-3",
   "token": "--shadow-3",
   "value": "0 10px 50px 0 rgb(0 0 30 / 15%)",
   "desc": "用于 context-menu"
  },
  {
   "name": "shadow-4",
   "token": "--shadow-4",
   "value": "0 10px 50px 0 rgb(0 0 30 / 30%)",
   "desc": "用于 dialog / alert-dialog"
  },
  {
   "name": "shadow-5",
   "token": "--shadow-5",
   "value": "0 10px 55px 0 rgb(0 0 30 / 25%)",
   "desc": "用于 semi-modal"
  },
  {
   "name": "shadow-6",
   "token": "--shadow-6",
   "value": "0 10px 70px 0 rgb(0 0 30 / 45%)",
   "desc": "暂未分配"
  }
 ]
}
```

## 组件 {#components}

49 个 HTML 组件契约，49 个按规范自带的组件预览页渲染。

```json design
{
 "title": "组件",
 "items": [
  {
   "id": "titlebar",
   "name": "Titlebar",
   "desc": "导航类 · Titlebar/Default",
   "props": [
    {
     "name": "variant",
     "values": "small | medium | large | xlarge"
    },
    {
     "name": "state",
     "values": "default | unfocus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 10,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "typography.subtitle-m",
    "typography.title-s",
    "spacing.component-gap"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "unfocus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=titlebar]",
      "lang": "html",
      "code": {
       "$file": "components/titlebar.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/titlebar.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "primary-navigation-item",
   "name": "Primary Navigation Item",
   "desc": "导航类 · Primary Navigation Item/Level 1",
   "props": [
    {
     "name": "variant",
     "values": "default | selected"
    },
    {
     "name": "state",
     "values": "default | hover | pressed | focus | selected | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 11,
   "tokenRoles": [
    "color.primary-level-unselected",
    "color.sidebar-accent",
    "color.sidebar-selected-text",
    "color.focus-ring",
    "size.icon-button",
    "icon-size-lg",
    "radius.icon-button"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "pressed",
    "focus",
    "selected",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=primary-navigation-item]",
      "lang": "html",
      "code": {
       "$file": "components/primary-navigation-item.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/primary-navigation-item.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "sidebar",
   "name": "Sidebar Item",
   "desc": "导航类 · Sidebar Item/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | selected | collapsed"
    },
    {
     "name": "state",
     "values": "default | hover | pressed | focus | selected | disabled"
    }
   ],
   "rules": [
    "每个 Sidebar Item 按钮独立拥有 sidebar / Sidebar Item/Default 身份；nav 与组容器只负责布局。批量 items/groups 一次调用可产生多个实例。Pixso 仅保留已核实的 logical-mapping，不扩大变体覆盖声明。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 12,
   "tokenRoles": [
    "color.sidebar-bg",
    "color.sidebar-selected",
    "color.text",
    "color.primary",
    "size.list-item-height",
    "radius.list-item",
    "typography.body-l"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "pressed",
    "focus",
    "selected",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=sidebar]",
      "lang": "html",
      "code": {
       "$file": "components/sidebar.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/sidebar.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "tabs",
   "name": "Tabs",
   "desc": "导航类 · Tabs/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | selected"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 13,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "color.primary"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "selected"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=tabs]",
      "lang": "html",
      "code": {
       "$file": "components/tabs.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/tabs.css"
      }
     }
    ]
   },
   "missingStates": [
    "focus",
    "disabled"
   ]
  },
  {
   "id": "sub-tabs",
   "name": "Sub Tabs",
   "desc": "导航类 · Sub Tabs/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | selected | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 13.5,
   "tokenRoles": [
    "color.neutral-dark-05",
    "color.text-muted",
    "color.brand-10",
    "color.brand-100",
    "spacing.gap-subtab-item",
    "spacing.space-5",
    "radius.subtab",
    "size.size-10",
    "typography.subtitle-m"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "focus",
    "selected",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=sub-tabs]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-runtime-sub-tabs-sizes\"><div><span class=\"tui-runtime-surface-label\">默认尺寸</span><div class=\"tui-component tui-sub-tabs\" data-component=\"sub-tabs\" data-renderer-key=\"sub-tabs\" data-logical-component=\"Sub Tabs/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" data-size=\"default\"><div class=\"tui-sub-tabs__list\" role=\"tablist\" aria-label=\"子页签\"><button type=\"button\" role=\"tab\" id=\"sub-tab-overview\" aria-controls=\"sub-tabs-panel\" aria-selected=\"true\" tabindex=\"0\" class=\"is-selected\" data-tab=\"overview\" data-typography-role=\"subtitle-m\">概览</button><button type=\"button\" role=\"tab\" id=\"sub-tab-activity\" aria-controls=\"sub-tabs-panel\" aria-selected=\"false\" tabindex=\"-1\" data-tab=\"activity\" data-typography-role=\"body-l\">活动</button><button type=\"button\" role=\"tab\" id=\"sub-tab-settings\" aria-controls=\"sub-tabs-panel\" aria-selected=\"false\" tabindex=\"-1\" data-tab=\"settings\" data-typography-role=\"body-l\">设置</button></div><div class=\"tui-sub-tabs__panel\" id=\"sub-tabs-panel\" role=\"tabpanel\" aria-labelledby=\"sub-tab-overview\" data-tab-panel=\"overview\" data-slot=\"content\" data-typography-role=\"body-l\">项目概览</div></div></div><div><span class=\"tui-runtime-surface-label\">小尺寸 · 28px</span><div class=\"tui-component tui-sub-tabs\" data-component=\"sub-tabs\" data-renderer-key=\"sub-tabs\" data-logical-component=\"Sub Tabs/Default\" data-variant=\"small\" data-state=\"default\" data-framework=\"html\" data-size=\"small\"><div class=\"tui-sub-tabs__list\" role=\"tablist\" aria-label=\"子页签\"><button type=\"button\" role=\"tab\" id=\"sub-tab-small-overview\" aria-controls=\"sub-tabs-small-panel\" aria-selected=\"true\" tabindex=\"0\" class=\"is-selected\" data-tab=\"overview\" data-typography-role=\"body-m\">概览</button><button type=\"button\" role=\"tab\" id=\"sub-tab-small-activity\" aria-controls=\"sub-tabs-small-panel\" aria-selected=\"false\" tabindex=\"-1\" data-tab=\"activity\" data-typography-role=\"body-m\">活动</button><button type=\"button\" role=\"tab\" id=\"sub-tab-small-settings\" aria-controls=\"sub-tabs-small-panel\" aria-selected=\"false\" tabindex=\"-1\" data-tab=\"settings\" data-typography-role=\"body-m\">设置</button></div><div class=\"tui-sub-tabs__panel\" id=\"sub-tabs-small-panel\" role=\"tabpanel\" aria-labelledby=\"sub-tab-small-overview\" data-tab-panel=\"overview\" data-slot=\"content\" data-typography-role=\"body-l\">项目概览</div></div></div></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/sub-tabs.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "breadcrumb",
   "name": "Breadcrumb",
   "desc": "导航类 · Breadcrumb/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 14,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=breadcrumb]",
      "lang": "html",
      "code": {
       "$file": "components/breadcrumb.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/breadcrumb.css"
      }
     }
    ]
   },
   "missingStates": [
    "focus",
    "disabled"
   ]
  },
  {
   "id": "tree-view",
   "name": "Tree View",
   "desc": "导航类 · Tree View/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | selected | expanded | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 14.5,
   "tokenRoles": [
    "color.text",
    "color.text-muted",
    "color.surface",
    "color.border",
    "color.primary",
    "spacing.menu-item-content",
    "size.tree-item-height",
    "radius.subtab",
    "typography.body-l",
    "typography.body-m"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "focus",
    "selected",
    "expanded",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=tree-view]",
      "lang": "html",
      "code": {
       "$file": "components/tree-view.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/tree-view.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "menubar",
   "name": "Menubar",
   "desc": "导航类 · Menubar/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 16,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "icon-size-lg",
    "spacing.menu-item-content"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=menubar]",
      "lang": "html",
      "code": {
       "$file": "components/menubar.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/menubar.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "pagination",
   "name": "Pagination",
   "desc": "导航类 · Pagination/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 17,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "spacing.content-inset"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=pagination]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><nav class=\"tui-component tui-pagination\" data-component=\"pagination\" data-renderer-key=\"pagination\" data-logical-component=\"Pagination/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" aria-label=\"分页\"><button class=\"tui-icon-button\" type=\"button\" data-page=\"prev\" aria-label=\"上一页\"><svg class=\"tui-icon tui-icon--regular\" viewBox=\"0 0 24 24\" width=\"20\" height=\"20\" data-icon-alias=\"navigation/back\" data-icon-size=\"20\" data-display-size-token=\"size/20\" data-icon-kind=\"regular\" data-icon-source=\"lucide@1.24.0\" aria-hidden=\"true\"><path d=\"m12 19-7-7 7-7\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path><path d=\"M19 12H5\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg></button><button type=\"button\" data-page=\"1\" aria-current=\"page\" data-typography-role=\"body-l\">1</button><button type=\"button\" data-page=\"2\" data-typography-role=\"body-l\">2</button><button type=\"button\" data-page=\"3\" data-typography-role=\"body-l\">3</button><button class=\"tui-icon-button\" type=\"button\" data-page=\"next\" aria-label=\"下一页\"><svg class=\"tui-icon tui-icon--regular\" viewBox=\"0 0 24 24\" width=\"20\" height=\"20\" data-icon-alias=\"navigation/forward\" data-icon-size=\"20\" data-display-size-token=\"size/20\" data-icon-kind=\"regular\" data-icon-source=\"lucide@1.24.0\" aria-hidden=\"true\"><path d=\"M5 12h14\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path><path d=\"m12 5 7 7-7 7\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg></button></nav></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/pagination.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "accordion",
   "name": "Accordion",
   "desc": "导航类 · Accordion/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | open"
    },
    {
     "name": "state",
     "values": "default | unfocus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 18,
   "tokenRoles": [
    "color.text-muted",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "unfocus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=accordion]",
      "lang": "html",
      "code": {
       "$file": "components/accordion.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/accordion.css"
      }
     }
    ]
   },
   "missingStates": [
    "unfocus",
    "disabled"
   ]
  },
  {
   "id": "collapsible",
   "name": "Collapsible",
   "desc": "导航类 · Collapsible/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | open"
    },
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "导航类",
   "order": 19,
   "tokenRoles": [
    "color.text-muted",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "navigation",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=collapsible]",
      "lang": "html",
      "code": {
       "$file": "components/collapsible.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/collapsible.css"
      }
     }
    ]
   },
   "missingStates": [
    "focus",
    "disabled"
   ]
  },
  {
   "id": "button",
   "name": "Button",
   "desc": "操作类 · Button/Primary/Default",
   "props": [
    {
     "name": "variant",
     "values": "primary | secondary | ghost | danger"
    },
    {
     "name": "size",
     "values": "standard | small"
    },
    {
     "name": "mode",
     "values": "text | icon-text | icon | split-dropdown"
    },
    {
     "name": "state",
     "values": "default | hover | pressed | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "操作类",
   "order": 110,
   "tokenRoles": [
    "color.primary",
    "color.primary-text",
    "color.text",
    "size.button-height",
    "size.button-sm-height",
    "radius.button",
    "spacing.padding-button-x",
    "spacing.padding-button-sm-x",
    "typography.body-m",
    "typography.body-l"
   ],
   "categoryId": "actions",
   "states": [
    "default",
    "hover",
    "pressed",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=button]",
      "lang": "html",
      "code": {
       "$file": "components/button.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/button.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "chips",
   "name": "Chips",
   "desc": "操作类 · Chips/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | with-icon | closable"
    },
    {
     "name": "state",
     "values": "default | hover | pressed | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "操作类",
   "order": 111,
   "tokenRoles": [
    "color.text",
    "color.surface-muted",
    "color.state-layer-hover",
    "color.state-layer-pressed",
    "size.tag-height",
    "spacing.padding-tag-x",
    "typography.body-m",
    "radius.tag"
   ],
   "categoryId": "actions",
   "states": [
    "default",
    "hover",
    "pressed",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=chips]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-runtime-chips-gallery\" data-runtime-component=\"chips\"><span class=\"tui-component tui-chip\" data-component=\"chips\" data-renderer-key=\"chips\" data-logical-component=\"Chips/Default\" data-variant=\"with-icon-closable\" data-state=\"default\" data-framework=\"html\"><span class=\"tui-chip__leading\" data-slot=\"leading\"><svg class=\"tui-icon tui-icon--regular\" viewBox=\"0 0 24 24\" width=\"16\" height=\"16\" data-icon-alias=\"action/mark-important\" data-icon-size=\"16\" data-display-size-token=\"size/16\" data-icon-kind=\"regular\" data-icon-source=\"lucide@1.24.0\" aria-hidden=\"true\"><path d=\"M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg></span><span class=\"tui-chip__label\" data-slot=\"label\" data-typography-role=\"body-m\">操作块</span><button class=\"tui-chip__close\" data-slot=\"close\" type=\"button\" aria-label=\"移除 操作块\"><svg class=\"tui-icon tui-icon--regular\" viewBox=\"0 0 24 24\" width=\"16\" height=\"16\" data-icon-alias=\"action/close\" data-icon-size=\"16\" data-display-size-token=\"size/16\" data-icon-kind=\"regular\" data-icon-source=\"lucide@1.24.0\" aria-hidden=\"true\"><path d=\"M18 6 6 18\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path><path d=\"m6 6 12 12\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg></button></span></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/chips.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "context-menu",
   "name": "Context Menu",
   "desc": "操作类 · Context Menu/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "操作类",
   "order": 112,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "shadow.overlay",
    "radius.card"
   ],
   "categoryId": "actions",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=context-menu]",
      "lang": "html",
      "code": {
       "$file": "components/context-menu.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/context-menu.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "dropdown-menu",
   "name": "Dropdown Menu",
   "desc": "操作类 · Dropdown Menu/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "操作类",
   "order": 113,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "shadow.overlay",
    "radius.card"
   ],
   "categoryId": "actions",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=dropdown-menu]",
      "lang": "html",
      "code": {
       "$file": "components/dropdown-menu.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/dropdown-menu.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "alert",
   "name": "Alert",
   "desc": "展示类 · Alert/Default",
   "props": [
    {
     "name": "variant",
     "values": "info | success | warning | danger | neutral"
    },
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 210,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.subtitle-s",
    "typography.body-m",
    "spacing.component-gap",
    "spacing.padding-alert-left",
    "spacing.padding-alert-right",
    "spacing.padding-button-sm-x",
    "size.button-sm-height",
    "size.icon-md",
    "size.icon-sm",
    "color.icon",
    "color.primary"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=alert]",
      "lang": "html",
      "code": {
       "$file": "components/alert.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/alert.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "snackbar",
   "name": "Snackbar",
   "desc": "展示类 · Snackbar/Default",
   "props": [
    {
     "name": "variant",
     "values": "title-only | title-subtitle"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 211,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "typography.subtitle-s",
    "typography.body-s",
    "typography.body-m",
    "spacing.component-gap",
    "color.primary",
    "shadow.3",
    "radius.5"
   ],
   "categoryId": "display",
   "states": [
    "default"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=snackbar]",
      "lang": "html",
      "code": {
       "$file": "components/snackbar.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/snackbar.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "tooltip",
   "name": "Tooltip",
   "desc": "展示类 · Tooltip/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 212,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.padding-tooltip",
    "shadow.1",
    "radius.tooltip"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=tooltip]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-component tui-tooltip\" data-component=\"tooltip\" data-renderer-key=\"tooltip\" data-logical-component=\"Tooltip/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\"><button class=\"tui-button tui-button--ghost\" type=\"button\" data-variant=\"ghost\" data-typography-role=\"body-l\">刷新列表</button><span class=\"tui-tooltip__panel\" role=\"tooltip\" data-slot=\"content\" data-typography-role=\"body-l\">刷新列表</span></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/tooltip.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "popover",
   "name": "Popover",
   "desc": "展示类 · Popover/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 213,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "shadow.overlay",
    "radius.card"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=popover]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--overlay\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-component tui-advanced-popover\" data-component=\"popover\" data-renderer-key=\"popover\" data-logical-component=\"Popover/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\"><button class=\"tui-button\" type=\"button\" data-variant=\"ghost\" data-typography-role=\"body-l\" aria-expanded=\"false\">筛选条件</button><div class=\"tui-advanced-popover__panel\" role=\"dialog\" hidden=\"\"><strong data-typography-role=\"title-s\">筛选条件</strong><span data-typography-role=\"body-m\">状态、负责人、更新时间</span></div></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/popover.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "hover-card",
   "name": "Hover Card",
   "desc": "展示类 · Hover Card/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 214,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "shadow.overlay",
    "radius.card"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=hover-card]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--overlay\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-component tui-advanced-hover-card\" data-component=\"hover-card\" data-renderer-key=\"hover-card\" data-logical-component=\"Hover Card/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\"><button class=\"tui-button\" type=\"button\" data-variant=\"ghost\" data-typography-role=\"body-l\">组件说明</button><div class=\"tui-advanced-hover-card__panel\" role=\"tooltip\"><strong data-typography-role=\"title-s\">组件说明</strong><span data-typography-role=\"body-m\">查看组件的详细使用规则</span></div></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/hover-card.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "avatar",
   "name": "Avatar",
   "desc": "展示类 · Avatar/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 215,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=avatar]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-runtime-avatar-pair\"><div><span class=\"tui-runtime-surface-label\">32 × 32</span><div class=\"tui-component tui-avatar\" data-component=\"avatar\" data-renderer-key=\"avatar\" data-logical-component=\"Avatar/32/Fallback\" data-variant=\"size-32\" data-state=\"default\" data-framework=\"html\" data-size=\"32\" aria-label=\"HarmonyOS 32\" data-typography-role=\"body-s\">H</div></div><div><span class=\"tui-runtime-surface-label\">40 × 40</span><div class=\"tui-component tui-avatar\" data-component=\"avatar\" data-renderer-key=\"avatar\" data-logical-component=\"Avatar/40/Fallback\" data-variant=\"size-40\" data-state=\"default\" data-framework=\"html\" data-size=\"40\" aria-label=\"HarmonyOS 40\" data-typography-role=\"body-s\">H</div></div></div></div><div class=\"tp-check tp\"><div class=\"tp-sec\"><div class=\"tp-l\">状态检查 <i>按组件契约声明的 state 逐个设置</i></div><div class=\"tp-row\"><div class=\"tp-it\" data-tp-state=\"default\"><div class=\"tui-component tui-avatar\" data-component=\"avatar\" data-renderer-key=\"avatar\" data-logical-component=\"Avatar/32/Fallback\" data-variant=\"size-32\" data-state=\"default\" data-framework=\"html\" data-size=\"32\" aria-label=\"HarmonyOS 32\" data-typography-role=\"body-s\">H</div><span class=\"tp-cap\">默认</span></div><div class=\"tp-it tp-na\" data-tp-state=\"hover\"><div class=\"tui-component tui-avatar\" data-component=\"avatar\" data-renderer-key=\"avatar\" data-logical-component=\"Avatar/32/Fallback\" data-variant=\"size-32\" data-state=\"hover\" data-framework=\"html\" data-size=\"32\" aria-label=\"HarmonyOS 32\" data-typography-role=\"body-s\" data-tp-hover=\"\">H</div><span class=\"tp-cap\">悬停</span></div><div class=\"tp-it tp-na\" data-tp-state=\"focus\"><div class=\"tui-component tui-avatar\" data-component=\"avatar\" data-renderer-key=\"avatar\" data-logical-component=\"Avatar/32/Fallback\" data-variant=\"size-32\" data-state=\"focus\" data-framework=\"html\" data-size=\"32\" aria-label=\"HarmonyOS 32\" data-typography-role=\"body-s\" data-tp-focus=\"\">H</div><span class=\"tp-cap\">聚焦</span></div><div class=\"tp-it tp-na\" data-tp-state=\"disabled\"><div class=\"tui-component tui-avatar\" data-component=\"avatar\" data-renderer-key=\"avatar\" data-logical-component=\"Avatar/32/Fallback\" data-variant=\"size-32\" data-state=\"disabled\" data-framework=\"html\" data-size=\"32\" aria-label=\"HarmonyOS 32\" data-typography-role=\"body-s\" aria-disabled=\"true\">H</div><span class=\"tp-cap\">禁用</span></div></div></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/avatar.css"
      }
     }
    ]
   },
   "missingStates": [
    "hover",
    "focus",
    "disabled"
   ]
  },
  {
   "id": "badge",
   "name": "Badge",
   "desc": "展示类 · Badge/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | info | success | warning | danger | neutral"
    },
    {
     "name": "state",
     "values": "default | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 216,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "color.primary"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=badge]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-badge-group\" aria-label=\"Badge 颜色示例\"><span class=\"tui-component tui-badge tui-badge--info\" data-component=\"badge\" data-renderer-key=\"badge\" data-logical-component=\"Badge/Default\" data-variant=\"info\" data-state=\"default\" data-framework=\"html\" data-typography-role=\"body-s\">进行中</span><span class=\"tui-component tui-badge tui-badge--success\" data-component=\"badge\" data-renderer-key=\"badge\" data-logical-component=\"Badge/Default\" data-variant=\"success\" data-state=\"default\" data-framework=\"html\" data-typography-role=\"body-s\">已完成</span><span class=\"tui-component tui-badge tui-badge--warning\" data-component=\"badge\" data-renderer-key=\"badge\" data-logical-component=\"Badge/Default\" data-variant=\"warning\" data-state=\"default\" data-framework=\"html\" data-typography-role=\"body-s\">待处理</span><span class=\"tui-component tui-badge tui-badge--danger\" data-component=\"badge\" data-renderer-key=\"badge\" data-logical-component=\"Badge/Default\" data-variant=\"danger\" data-state=\"default\" data-framework=\"html\" data-typography-role=\"body-s\">错误</span><span class=\"tui-component tui-badge tui-badge--neutral\" data-component=\"badge\" data-renderer-key=\"badge\" data-logical-component=\"Badge/Default\" data-variant=\"neutral\" data-state=\"default\" data-framework=\"html\" data-typography-role=\"body-s\">未开始</span></div></div><div class=\"tp-check tp\"><div class=\"tp-sec\"><div class=\"tp-l\">状态检查 <i>按组件契约声明的 state 逐个设置</i></div><div class=\"tp-row\"><div class=\"tp-it\" data-tp-state=\"default\"><span class=\"tui-component tui-badge tui-badge--info\" data-component=\"badge\" data-renderer-key=\"badge\" data-logical-component=\"Badge/Default\" data-variant=\"info\" data-state=\"default\" data-framework=\"html\" data-typography-role=\"body-s\">进行中</span><span class=\"tp-cap\">默认</span></div><div class=\"tp-it tp-na\" data-tp-state=\"disabled\"><span class=\"tui-component tui-badge tui-badge--info\" data-component=\"badge\" data-renderer-key=\"badge\" data-logical-component=\"Badge/Default\" data-variant=\"info\" data-state=\"disabled\" data-framework=\"html\" data-typography-role=\"body-s\" aria-disabled=\"true\">进行中</span><span class=\"tp-cap\">禁用</span></div></div></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/badge.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "color-picker",
   "name": "ColorPicker",
   "desc": "展示类 · ColorPicker/Tablet",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 217,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.title-s",
    "typography.body-l",
    "typography.body-m",
    "typography.body-s",
    "spacing.component-gap",
    "radius.card"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=color-picker]",
      "lang": "html",
      "code": {
       "$file": "components/color-picker.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/color-picker.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "table",
   "name": "Table",
   "desc": "展示类 · Table/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | selected"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 218,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "spacing.content-inset"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "selected"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=table]",
      "lang": "html",
      "code": {
       "$file": "components/table.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/table.css"
      }
     }
    ]
   },
   "missingStates": [
    "focus",
    "disabled",
    "selected"
   ]
  },
  {
   "id": "progress",
   "name": "Progress",
   "desc": "展示类 · Progress/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | success | warning | danger | info"
    },
    {
     "name": "state",
     "values": "default | hover | focus | disabled | loading"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "展示类",
   "order": 220,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "color.primary"
   ],
   "categoryId": "display",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "loading"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=progress]",
      "lang": "html",
      "code": {
       "$file": "components/progress.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": ":root{--font-sans:\"HarmonyOS Sans\", \"HarmonyOS Sans SC\", \"PingFang SC\", \"Microsoft YaHei\", sans-serif;--space-0:0px;--radius-2:6px;--space-3:8px;--type-body-l-leading:var(--line-height-20);--line-height-20:20px;--type-body-l-size:var(--font-size-16);--font-size-16:16px;--color-bg-subtle:var(--color-neutral-dark-05);--color-neutral-dark-05:#0000000C;--color-text:var(--color-neutral-dark-90);--color-neutral-dark-90:#000000E5;--color-primary:var(--color-brand-100);--color-brand-100:#0A59F7FF;--radius-progress:var(--radius-full);--radius-full:999px;--height-progress:var(--size-1);--size-1:4px;--space-2:4px}\n:where(.tui-component, .tui-component *) { box-sizing: border-box; }\n:where(.tui-component) { font-family: var(--font-sans); }\n:where(.tui-button, .tui-input, .tui-search, .tui-sidebar-item, .tui-primary-navigation-item, .tui-list-card) { font: inherit; }\n.tui-progress { width: 100%; display: grid; gap: var(--space-2); color: var(--color-text); }\n.tui-progress__track { width: 100%; height: var(--height-progress); overflow: hidden; border-radius: var(--radius-progress); background: var(--color-bg-subtle); }\n.tui-progress__value { display: block; width: var(--progress-value, 0%); height: 100%; border-radius: inherit; background: var(--color-primary); transition: width 0.16s; }\n* { box-sizing: border-box; }\nhtml { min-width: 0px; background: var(--color-bg-subtle); }\nbody { min-width: 0px; min-height: 720px; margin: 0px; color: var(--color-text); background: var(--color-bg-subtle); font-family: var(--font-sans); font-size: var(--type-body-l-size); line-height: var(--type-body-l-leading); }\n.tui-runtime-card__preview { min-width: 0px; min-height: 64px; display: grid; align-content: start; justify-items: start; gap: var(--space-3); padding: var(--space-3); border-radius: var(--radius-2); background: transparent; }\n.tui-runtime-card__preview:has(> .tui-sidebar) { padding: var(--space-0); }\n.tui-runtime-card__preview { container: runtime-preview / inline-size; }\n.tui-runtime-card--intrinsic .tui-runtime-card__preview > * { width: max-content; max-width: 100%; }\n.tui-runtime-card--intrinsic .tui-runtime-card__preview > .tui-progress { width: 100%; }\nhtml, body { margin: 0px !important; padding: 0px !important; display: block !important; min-height: 0px !important; height: auto !important; background: rgb(255, 255, 255) !important; overflow: visible !important; }\n.tp-card { display: block; padding: 12px 16px; }\n.tp { display: flex; flex-direction: column; gap: 22px; font-family: var(--font-sans); }\n.tp-sec { display: flex; flex-direction: column; gap: 10px; max-width: 100%; }\n.tp-l { font-size: 12px; color: rgb(138, 138, 138); }\n.tp-l i { font-style: normal; color: rgb(181, 181, 181); margin-left: 4px; }\n.tp-row { display: flex; flex-wrap: wrap; gap: 16px 24px; align-items: flex-start; }\n.tp-it { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; min-width: 64px; max-width: 100%; }\n.tp-cap { font-size: 11px; color: rgb(154, 154, 154); line-height: 14px; white-space: nowrap; }\n.tp-check { margin-top: 20px; padding: 16px 16px 4px; border-top: 1px dashed rgb(224, 224, 224); }"
     }
    ]
   },
   "missingStates": [
    "hover",
    "focus",
    "disabled",
    "loading"
   ]
  },
  {
   "id": "input",
   "name": "Input",
   "desc": "输入类 · Input/White Surface/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | error | disabled | tag-entry"
    },
    {
     "name": "state",
     "values": "default | hover | focus | disabled | error"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "输入类",
   "order": 310,
   "tokenRoles": [
    "color.input-bg",
    "color.icon",
    "color.text",
    "color.text-muted",
    "color.text-subtle",
    "color.border",
    "size.input-height",
    "radius.input",
    "typography.body-l",
    "typography.body-m"
   ],
   "categoryId": "input",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "error"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=input]",
      "lang": "html",
      "code": {
       "$file": "components/input.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/input.css"
      }
     }
    ]
   },
   "missingStates": [
    "focus"
   ]
  },
  {
   "id": "search",
   "name": "Search",
   "desc": "输入类 · Search/White Surface/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | focused | with-value | advanced-search | scoped-search | scoped-advanced-search"
    },
    {
     "name": "state",
     "values": "default | focus | typing | filled | hover-left | hover-right | pressed-left | pressed-right | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "输入类",
   "order": 311,
   "tokenRoles": [
    "color.input-bg",
    "color.text",
    "color.icon",
    "size.search-height",
    "radius.search",
    "spacing.padding-search-x",
    "typography.body-l"
   ],
   "categoryId": "input",
   "states": [
    "default",
    "focus",
    "typing",
    "filled",
    "hover-left",
    "hover-right",
    "pressed-left",
    "pressed-right",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=search]",
      "lang": "html",
      "code": {
       "$file": "components/search.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/search.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "textarea",
   "name": "Textarea",
   "desc": "输入类 · Textarea/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | error"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "输入类",
   "order": 312,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "input",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "error"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=textarea]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--fill\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-runtime-surface-pair tui-runtime-textarea-pair\"><div data-surface-context=\"white\"><span class=\"tui-runtime-surface-label\">白色内容面 · 灰色输入面</span><label class=\"tui-component tui-textarea\" data-component=\"textarea\" data-renderer-key=\"textarea\" data-logical-component=\"Textarea/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" data-surface=\"white\"><span data-slot=\"label\" data-typography-role=\"body-m\">项目说明</span><textarea data-slot=\"value\" data-typography-role=\"body-l\" rows=\"3\" placeholder=\"请输入内容\">统一 HarmonyOS PC 客户端中的布局、组件与交互规则。</textarea><span data-slot=\"help\" data-typography-role=\"body-s\">支持多行输入，最多 500 字</span></label></div><div data-surface-context=\"gray\"><span class=\"tui-runtime-surface-label\">灰色内容面 · 白色输入面</span><label class=\"tui-component tui-textarea\" data-component=\"textarea\" data-renderer-key=\"textarea\" data-logical-component=\"Textarea/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" data-surface=\"gray\"><span data-slot=\"label\" data-typography-role=\"body-m\">项目说明</span><textarea data-slot=\"value\" data-typography-role=\"body-l\" rows=\"3\" placeholder=\"请输入内容\">统一 HarmonyOS PC 客户端中的布局、组件与交互规则。</textarea><span data-slot=\"help\" data-typography-role=\"body-s\">支持多行输入，最多 500 字</span></label></div></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/textarea.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "field",
   "name": "Field",
   "desc": "输入类 · Field/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | error"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "输入类",
   "order": 313,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "input",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "error"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=field]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><label class=\"tui-component tui-field\" data-component=\"field\" data-renderer-key=\"field\" data-logical-component=\"Field/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" data-surface=\"white\"><span data-slot=\"label\" data-typography-role=\"body-m\">项目名称</span><span class=\"tui-field__control\"><input data-slot=\"value\" data-typography-role=\"body-l\" type=\"text\" value=\"客户端设计系统\"></span><span data-slot=\"help\" data-typography-role=\"body-s\">这是一个必填字段</span></label></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/field.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "label",
   "name": "Label",
   "desc": "输入类 · Label/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "输入类",
   "order": 314,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-m",
    "spacing.component-gap",
    "spacing.padding-tag-x",
    "size.tag-height"
   ],
   "categoryId": "input",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=label]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><label class=\"tui-component tui-label\" data-component=\"label\" data-renderer-key=\"label\" data-logical-component=\"Label/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" for=\"project-name\" data-typography-role=\"body-m\">邮箱</label></div><div class=\"tp-check tp\"><div class=\"tp-sec\"><div class=\"tp-l\">状态检查 <i>按组件契约声明的 state 逐个设置</i></div><div class=\"tp-row\"><div class=\"tp-it\" data-tp-state=\"default\"><label class=\"tui-component tui-label\" data-component=\"label\" data-renderer-key=\"label\" data-logical-component=\"Label/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" for=\"project-name\" data-typography-role=\"body-m\">邮箱</label><span class=\"tp-cap\">默认</span></div><div class=\"tp-it tp-na\" data-tp-state=\"hover\"><label class=\"tui-component tui-label\" data-component=\"label\" data-renderer-key=\"label\" data-logical-component=\"Label/Default\" data-variant=\"default\" data-state=\"hover\" data-framework=\"html\" for=\"project-name\" data-typography-role=\"body-m\" data-tp-hover=\"\">邮箱</label><span class=\"tp-cap\">悬停</span></div><div class=\"tp-it tp-na\" data-tp-state=\"focus\"><label class=\"tui-component tui-label\" data-component=\"label\" data-renderer-key=\"label\" data-logical-component=\"Label/Default\" data-variant=\"default\" data-state=\"focus\" data-framework=\"html\" for=\"project-name\" data-typography-role=\"body-m\" data-tp-focus=\"\">邮箱</label><span class=\"tp-cap\">聚焦</span></div><div class=\"tp-it tp-na\" data-tp-state=\"disabled\"><label class=\"tui-component tui-label\" data-component=\"label\" data-renderer-key=\"label\" data-logical-component=\"Label/Default\" data-variant=\"default\" data-state=\"disabled\" data-framework=\"html\" for=\"project-name\" data-typography-role=\"body-m\" aria-disabled=\"true\">邮箱</label><span class=\"tp-cap\">禁用</span></div></div></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": ":root{--font-sans:\"HarmonyOS Sans\", \"HarmonyOS Sans SC\", \"PingFang SC\", \"Microsoft YaHei\", sans-serif;--space-0:0px;--radius-2:6px;--space-3:8px;--type-body-l-leading:var(--line-height-20);--line-height-20:20px;--type-body-l-size:var(--font-size-16);--font-size-16:16px;--color-bg-subtle:var(--color-neutral-dark-05);--color-neutral-dark-05:#0000000C;--color-text:var(--color-neutral-dark-90);--color-neutral-dark-90:#000000E5;--type-body-m-weight:var(--font-weight-400);--font-weight-400:400;--type-body-m-leading:var(--line-height-16);--line-height-16:16px;--type-body-m-size:var(--font-size-14);--font-size-14:14px;--radius-tag:var(--radius-3);--radius-3:8px;--padding-tag-x:var(--space-4);--space-4:12px;--height-tag:var(--size-8);--size-8:28px}\n:where(.tui-component, .tui-component *) { box-sizing: border-box; }\n:where(.tui-component) { font-family: var(--font-sans); }\n:where(.tui-button, .tui-input, .tui-search, .tui-sidebar-item, .tui-primary-navigation-item, .tui-list-card) { font: inherit; }\n.tui-label { height: var(--height-tag); display: inline-flex; align-items: center; width: max-content; padding-inline: var(--padding-tag-x); border-radius: var(--radius-tag); color: var(--color-text); background: var(--color-neutral-dark-05); font-family: var(--font-sans); font-size: var(--type-body-m-size); line-height: var(--type-body-m-leading); font-weight: var(--type-body-m-weight); white-space: nowrap; }\n.tui-generated [data-typography-role=\"body-m\"], [data-typography-role=\"body-m\"] { font-size: var(--type-body-m-size); line-height: var(--type-body-m-leading); font-weight: var(--type-body-m-weight); }\n* { box-sizing: border-box; }\nhtml { min-width: 0px; background: var(--color-bg-subtle); }\nbody { min-width: 0px; min-height: 720px; margin: 0px; color: var(--color-text); background: var(--color-bg-subtle); font-family: var(--font-sans); font-size: var(--type-body-l-size); line-height: var(--type-body-l-leading); }\n.tui-runtime-card__preview { min-width: 0px; min-height: 64px; display: grid; align-content: start; justify-items: start; gap: var(--space-3); padding: var(--space-3); border-radius: var(--radius-2); background: transparent; }\n.tui-runtime-card__preview:has(> .tui-sidebar) { padding: var(--space-0); }\n.tui-runtime-card__preview { container: runtime-preview / inline-size; }\n.tui-runtime-card--intrinsic .tui-runtime-card__preview > * { width: max-content; max-width: 100%; }\nhtml, body { margin: 0px !important; padding: 0px !important; display: block !important; min-height: 0px !important; height: auto !important; background: rgb(255, 255, 255) !important; overflow: visible !important; }\n.tp-card { display: block; padding: 12px 16px; }\n.tp { display: flex; flex-direction: column; gap: 22px; font-family: var(--font-sans); }\n.tp-sec { display: flex; flex-direction: column; gap: 10px; max-width: 100%; }\n.tp-l { font-size: 12px; color: rgb(138, 138, 138); }\n.tp-l i { font-style: normal; color: rgb(181, 181, 181); margin-left: 4px; }\n.tp-row { display: flex; flex-wrap: wrap; gap: 16px 24px; align-items: flex-start; }\n.tp-it { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; min-width: 64px; max-width: 100%; }\n.tp-cap { font-size: 11px; color: rgb(154, 154, 154); line-height: 14px; white-space: nowrap; }\n.tp-check { margin-top: 20px; padding: 16px 16px 4px; border-top: 1px dashed rgb(224, 224, 224); }"
     }
    ]
   },
   "missingStates": [
    "hover",
    "focus",
    "disabled"
   ]
  },
  {
   "id": "combobox",
   "name": "Combobox",
   "desc": "输入类 · Combobox/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open | error"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "输入类",
   "order": 315,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "input",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open",
    "error"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=combobox]",
      "lang": "html",
      "code": {
       "$file": "components/combobox.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/combobox.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "number-selector",
   "name": "Number Selector",
   "desc": "输入类 · Number Selector/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "输入类",
   "order": 316,
   "tokenRoles": [
    "color.surface",
    "color.text",
    "color.border",
    "color.primary",
    "size.input-height",
    "radius.input",
    "typography.body-l"
   ],
   "categoryId": "input",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=number-selector]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><label class=\"tui-component tui-number-selector\" data-component=\"number-selector\" data-renderer-key=\"number-selector\" data-logical-component=\"Number Selector/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\"><span data-slot=\"label\" data-typography-role=\"body-m\">数量</span><span class=\"tui-number-selector__control\"><input type=\"number\" data-slot=\"value\" data-typography-role=\"body-l\" value=\"1\" min=\"0\" max=\"99\" step=\"1\"><span class=\"tui-number-selector__stepper\" aria-label=\"调整数量\"><button type=\"button\" class=\"tui-number-selector__step\" data-slot=\"increment\" data-direction=\"increment\" aria-label=\"增加数量\"><svg class=\"tui-icon tui-icon--regular\" viewBox=\"0 0 24 24\" width=\"16\" height=\"16\" data-icon-alias=\"navigation/chevron-up\" data-icon-size=\"16\" data-display-size-token=\"size/16\" data-icon-kind=\"regular\" data-icon-source=\"lucide@1.24.0\" aria-hidden=\"true\"><path d=\"m18 15-6-6-6 6\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg></button><button type=\"button\" class=\"tui-number-selector__step\" data-slot=\"decrement\" data-direction=\"decrement\" aria-label=\"减少数量\"><svg class=\"tui-icon tui-icon--regular\" viewBox=\"0 0 24 24\" width=\"16\" height=\"16\" data-icon-alias=\"navigation/chevron-down\" data-icon-size=\"16\" data-display-size-token=\"size/16\" data-icon-kind=\"regular\" data-icon-source=\"lucide@1.24.0\" aria-hidden=\"true\"><path d=\"m6 9 6 6 6-6\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg></button></span></span></label></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/number-selector.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "checkbox",
   "name": "Checkbox",
   "desc": "选择类 · Checkbox/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | selected"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 410,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "selected"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=checkbox]",
      "lang": "html",
      "code": {
       "$file": "components/checkbox.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/checkbox.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "radio",
   "name": "Radio",
   "desc": "选择类 · Radio/Unselected/Default",
   "props": [
    {
     "name": "variant",
     "values": "unselected | selected"
    },
    {
     "name": "state",
     "values": "default | hover | focus | disabled | selected"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 411,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "color.primary",
    "color.primary-text",
    "size.indicator.radio-size",
    "radius.full",
    "spacing.gap.choice-label",
    "typography.body-m"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "selected"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=radio]",
      "lang": "html",
      "code": {
       "$file": "components/radio.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/radio.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "radio-group",
   "name": "Radio Group",
   "desc": "选择类 · Radio Group/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | selected"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 412,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "selected"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=radio-group]",
      "lang": "html",
      "code": {
       "$file": "components/radio-group.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/radio-group.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "switch",
   "name": "Switch",
   "desc": "选择类 · Switch/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | selected"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 413,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "color.primary"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "selected"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=switch]",
      "lang": "html",
      "code": {
       "$file": "components/switch.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/switch.css"
      }
     }
    ]
   },
   "missingStates": [
    "hover",
    "disabled"
   ]
  },
  {
   "id": "segmented-button",
   "name": "Segmented Button",
   "desc": "选择类 · Segmented Button/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | selected | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 414,
   "tokenRoles": [
    "color.surface",
    "color.text",
    "color.primary",
    "radius.tab",
    "spacing.padding-segmented-control",
    "typography.body-m"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "selected",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=segmented-button]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-component tui-segmented-button\" data-component=\"segmented-button\" data-renderer-key=\"segmented-button\" data-logical-component=\"Segmented Button/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" role=\"group\" aria-label=\"视图模式\"><button type=\"button\" class=\"tui-segmented-button__item is-selected\" aria-pressed=\"true\" data-value=\"列表\" data-slot=\"option\" data-typography-role=\"body-m\">列表</button><button type=\"button\" class=\"tui-segmented-button__item\" aria-pressed=\"false\" data-value=\"看板\" data-slot=\"option\" data-typography-role=\"body-m\">看板</button><button type=\"button\" class=\"tui-segmented-button__item\" aria-pressed=\"false\" data-value=\"时间线\" data-slot=\"option\" data-typography-role=\"body-m\">时间线</button></div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/segmented-button.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "select",
   "name": "Select",
   "desc": "选择类 · Select/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open | error"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 415,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open",
    "error"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=select]",
      "lang": "html",
      "code": {
       "$file": "components/select.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/select.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "native-select",
   "name": "Native Select",
   "desc": "选择类 · Native Select/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 416,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=native-select]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><label class=\"tui-component tui-native-select\" data-component=\"native-select\" data-renderer-key=\"native-select\" data-logical-component=\"Native Select/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\" data-surface=\"white\"><span data-slot=\"label\" data-typography-role=\"body-m\">视图</span><span class=\"tui-native-select__control\"><select data-slot=\"value\" data-typography-role=\"body-m\"><option selected=\"\">列表视图</option><option>网格视图</option><option>紧凑视图</option></select><svg class=\"tui-icon tui-icon--regular\" viewBox=\"0 0 24 24\" width=\"16\" height=\"16\" data-icon-alias=\"navigation/chevron-down\" data-icon-size=\"16\" data-display-size-token=\"size/16\" data-icon-kind=\"regular\" data-icon-source=\"lucide@1.24.0\" aria-hidden=\"true\"><path d=\"m6 9 6 6 6-6\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg></span></label></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/native-select.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "slider",
   "name": "Slider",
   "desc": "选择类 · Slider/Default",
   "props": [
    {
     "name": "variant",
     "values": "style-1 | style-2"
    },
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 417,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=slider]",
      "lang": "html",
      "code": {
       "$file": "components/slider.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/slider.css"
      }
     }
    ]
   },
   "missingStates": [
    "hover",
    "focus",
    "disabled"
   ]
  },
  {
   "id": "calendar",
   "name": "Calendar",
   "desc": "选择类 · Calendar/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 419,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "spacing.content-inset"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=calendar]",
      "lang": "html",
      "code": {
       "$file": "components/calendar.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/calendar.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled"
   ]
  },
  {
   "id": "date-picker",
   "name": "Date Picker",
   "desc": "选择类 · Date Picker/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open | error"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 420,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "spacing.content-inset"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open",
    "error"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=date-picker]",
      "lang": "html",
      "code": {
       "$file": "components/date-picker.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/date-picker.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled",
    "error"
   ]
  },
  {
   "id": "time-picker",
   "name": "Time Picker",
   "desc": "选择类 · Time Picker/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled | open | error"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "选择类",
   "order": 421,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "spacing.content-inset"
   ],
   "categoryId": "choices",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled",
    "open",
    "error"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=time-picker]",
      "lang": "html",
      "code": {
       "$file": "components/time-picker.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/time-picker.css"
      }
     }
    ]
   },
   "missingStates": [
    "disabled",
    "error"
   ]
  },
  {
   "id": "form-field",
   "name": "Form Field",
   "desc": "容器类 · Form Field/Default",
   "props": [
    {
     "name": "variant",
     "values": "input | select"
    },
    {
     "name": "state",
     "values": "default | error | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "容器类",
   "order": 509,
   "tokenRoles": [
    "color.text",
    "color.alert",
    "typography.subtitle-s",
    "typography.body-s",
    "spacing.component-gap"
   ],
   "categoryId": "containers",
   "states": [
    "default",
    "error",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=form-field]",
      "lang": "html",
      "code": {
       "$file": "components/form-field.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/form-field.css"
      }
     }
    ]
   },
   "missingStates": [
    "error"
   ]
  },
  {
   "id": "list-card",
   "name": "List Item",
   "desc": "容器类 · List Item/White Surface/Default",
   "props": [
    {
     "name": "variant",
     "values": "default | selected | unread"
    },
    {
     "name": "state",
     "values": "default | hover | pressed | focus | selected | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "容器类",
   "order": 510,
   "tokenRoles": [
    "color.surface",
    "color.sidebar-selected",
    "color.text",
    "color.text-muted",
    "size.list-item-height",
    "radius.list-item",
    "typography.body-l",
    "typography.body-m"
   ],
   "categoryId": "containers",
   "states": [
    "default",
    "hover",
    "pressed",
    "focus",
    "selected",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=list-card]",
      "lang": "html",
      "code": {
       "$file": "components/list-card.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/list-card.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "dialog",
   "name": "Dialog",
   "desc": "容器类 · Dialog/Default",
   "props": [
    {
     "name": "variant",
     "values": "single | double | triple"
    },
    {
     "name": "state",
     "values": "closed | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "容器类",
   "order": 512,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "shadow.overlay",
    "radius.card"
   ],
   "categoryId": "containers",
   "states": [
    "closed",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=dialog]",
      "lang": "html",
      "code": {
       "$file": "components/dialog.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/dialog.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "alert-dialog",
   "name": "Alert Dialog",
   "desc": "容器类 · Alert Dialog/Default",
   "props": [
    {
     "name": "state",
     "values": "closed | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "容器类",
   "order": 513,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "shadow.overlay",
    "radius.card"
   ],
   "categoryId": "containers",
   "states": [
    "closed",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=alert-dialog]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--overlay\"><div class=\"tui-runtime-card__preview\"><div class=\"tui-overlay-example\" data-overlay-example=\"alert-dialog\">\n    <button class=\"tui-button\" type=\"button\" data-variant=\"secondary\" data-overlay-trigger=\"alert-dialog\" data-typography-role=\"body-l\" onclick=\"const l=this.nextElementSibling;l.hidden=false;const d=l.querySelector('.tui-dialog');d.dataset.state='open';d.focus()\">打开删除确认弹窗</button>\n    <div class=\"tui-overlay-layer\" id=\"alert-dialog\" data-overlay-id=\"alert-dialog\" hidden=\"\">\n      <div class=\"tui-overlay-backdrop\" aria-hidden=\"true\"></div>\n      <section class=\"tui-component tui-dialog tui-dialog--alert\" data-component=\"alert-dialog\" data-renderer-key=\"alert-dialog\" data-logical-component=\"Alert Dialog/Default\" data-variant=\"white\" data-state=\"open\" data-framework=\"html\" role=\"alertdialog\" aria-modal=\"true\" aria-labelledby=\"alert-dialog-title\" aria-describedby=\"alert-dialog-description\" tabindex=\"-1\" onkeydown=\"if(event.key==='Escape'){event.preventDefault();const e=this.closest('[data-overlay-example]');this.closest('.tui-overlay-layer').hidden=true;e.querySelector('[data-overlay-trigger]').focus()}\">\n        <header class=\"tui-dialog__header\" data-slot=\"titlebar\"><h4 id=\"alert-dialog-title\" data-slot=\"title\" data-typography-role=\"title-s\">删除项目？</h4></header>\n        <div class=\"tui-dialog__content\"><p id=\"alert-dialog-description\" data-slot=\"description\" data-typography-role=\"body-m\">删除后无法恢复，请确认操作。</p></div>\n        <footer class=\"tui-dialog__actions\" data-slot=\"actions\" data-action-layout=\"double\"><button class=\"tui-button\" type=\"button\" data-variant=\"secondary\" data-overlay-action=\"cancel\" data-typography-role=\"body-l\" onclick=\"const e=this.closest('[data-overlay-example]');this.closest('.tui-overlay-layer').hidden=true;e.querySelector('[data-overlay-trigger]').focus()\">取消</button><button class=\"tui-button\" type=\"button\" data-variant=\"danger\" data-overlay-action=\"confirm\" data-typography-role=\"body-l\" onclick=\"const e=this.closest('[data-overlay-example]');this.closest('.tui-overlay-layer').hidden=true;e.querySelector('[data-overlay-trigger]').focus()\">删除</button></footer>\n      </section>\n    </div>\n  </div></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/alert-dialog.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "semi-modal",
   "name": "Semi-modal",
   "desc": "容器类 · Semi-modal/Default",
   "props": [
    {
     "name": "variant",
     "values": "s | m | l | white | gray | non-modal | modal"
    },
    {
     "name": "state",
     "values": "closed | open"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "容器类",
   "order": 514,
   "tokenRoles": [
    "color.text",
    "color.surface",
    "color.border",
    "typography.body-l",
    "spacing.component-gap",
    "shadow.overlay",
    "radius.card"
   ],
   "categoryId": "containers",
   "states": [
    "closed",
    "open"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=semi-modal]",
      "lang": "html",
      "code": {
       "$file": "components/semi-modal.html"
      }
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/semi-modal.css"
      }
     }
    ]
   },
   "missingStates": []
  },
  {
   "id": "attachment",
   "name": "Attachment",
   "desc": "特殊组件 · Attachment/Default",
   "props": [
    {
     "name": "state",
     "values": "default | hover | focus | disabled"
    }
   ],
   "rules": [
    "已保留当前组件契约；运行时适配器仍需按本组件真实结构、行为和可访问性逐批验收。",
    "成熟度：partial，视觉 / 行为 / 无障碍一致性尚未验收，只能用于快速预览。"
   ],
   "category": "特殊组件",
   "order": 610,
   "tokenRoles": [
    "color.text",
    "color.surface-muted",
    "typography.subtitle-s",
    "typography.body-s",
    "spacing.component-gap"
   ],
   "categoryId": "specialized",
   "states": [
    "default",
    "hover",
    "focus",
    "disabled"
   ],
   "source": {
    "status": "found",
    "adapter": "gallery-render",
    "files": [
     {
      "path": "apps/component-gallery/index.html#runtime-view [data-component-card=attachment]",
      "lang": "html",
      "code": "<style>html,body{margin:0!important;padding:0!important;display:block!important;min-height:0!important;height:auto!important;background:#fff!important;overflow:visible!important}\n.tp-card{display:block;padding:12px 16px}\n.tp{display:flex;flex-direction:column;gap:22px;font-family:var(--font-sans)}\n.tp-sec{display:flex;flex-direction:column;gap:10px;max-width:100%}\n.tp-l{font-size:12px;color:#8a8a8a}.tp-l i{font-style:normal;color:#b5b5b5;margin-left:4px}\n.tp-row{display:flex;flex-wrap:wrap;gap:16px 24px;align-items:flex-start}\n.tp-it{display:flex;flex-direction:column;align-items:flex-start;gap:8px;min-width:64px;max-width:100%}\n.tp-cap{font-size:11px;color:#9a9a9a;line-height:14px;white-space:nowrap}\n.tp-check{margin-top:20px;padding:16px 16px 4px;border-top:1px dashed #e0e0e0}\n.tp-it.tp-na{outline:1px dashed #c4c4c4;outline-offset:6px;border-radius:2px}\n.tp-na .tp-cap::after{content:\"规范未定义样式\";display:block;margin-top:4px;font-size:10px;line-height:14px;color:#999;border:1px dashed #c4c4c4;border-radius:4px;padding:0 4px;width:max-content}</style><div class=\"tp-card tui-runtime-card--intrinsic\"><div class=\"tui-runtime-card__preview\"><article class=\"tui-component tui-attachment\" data-component=\"attachment\" data-renderer-key=\"attachment\" data-logical-component=\"Attachment/Default\" data-variant=\"default\" data-state=\"default\" data-framework=\"html\"><span class=\"tui-attachment__type\" data-slot=\"leading\" data-typography-role=\"body-s\">PDF</span><div data-slot=\"content\"><strong data-slot=\"title\" data-typography-role=\"subtitle-s\">项目说明.pdf</strong><small data-slot=\"description\" data-typography-role=\"body-s\">2.4 MB · 已上传</small></div><span class=\"tui-attachment__actions\" data-slot=\"actions\"><button class=\"tui-icon-button tui-attachment__menu-trigger\" data-slot=\"menu-trigger\" type=\"button\" aria-label=\"打开附件操作菜单\" aria-haspopup=\"menu\" aria-expanded=\"false\"><svg class=\"tui-icon tui-icon--regular\" viewBox=\"0 0 24 24\" width=\"20\" height=\"20\" data-icon-alias=\"navigation/chevron-down\" data-icon-size=\"20\" data-display-size-token=\"size/20\" data-icon-kind=\"regular\" data-icon-source=\"lucide@1.24.0\" aria-hidden=\"true\"><path d=\"m6 9 6 6 6-6\" fill=\"none\" stroke=\"currentColor\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg></button><div class=\"tui-button-dropdown__menu tui-attachment__menu\" data-slot=\"menu\" role=\"menu\" hidden=\"\"><button class=\"tui-button-dropdown__item\" type=\"button\" role=\"menuitem\" data-action=\"preview\" data-typography-role=\"body-l\">预览</button><button class=\"tui-button-dropdown__item\" type=\"button\" role=\"menuitem\" data-action=\"download\" data-typography-role=\"body-l\">下载</button></div></span></article></div></div>"
     },
     {
      "path": "apps/component-gallery/styles/index.css",
      "lang": "css",
      "code": {
       "$file": "components/attachment.css"
      }
     }
    ]
   },
   "missingStates": []
  }
 ],
 "groups": [
  {
   "id": "navigation",
   "label": "导航类",
   "componentIds": [
    "titlebar",
    "primary-navigation-item",
    "sidebar",
    "tabs",
    "sub-tabs",
    "tree-view",
    "breadcrumb",
    "menubar",
    "pagination",
    "accordion",
    "collapsible"
   ]
  },
  {
   "id": "actions",
   "label": "操作类",
   "componentIds": [
    "button",
    "chips",
    "context-menu",
    "dropdown-menu"
   ]
  },
  {
   "id": "display",
   "label": "展示类",
   "componentIds": [
    "alert",
    "snackbar",
    "tooltip",
    "popover",
    "hover-card",
    "avatar",
    "badge",
    "color-picker",
    "table",
    "progress"
   ]
  },
  {
   "id": "input",
   "label": "输入类",
   "componentIds": [
    "input",
    "search",
    "textarea",
    "field",
    "label",
    "combobox",
    "number-selector"
   ]
  },
  {
   "id": "choices",
   "label": "选择类",
   "componentIds": [
    "checkbox",
    "radio",
    "radio-group",
    "switch",
    "segmented-button",
    "select",
    "native-select",
    "slider",
    "calendar",
    "date-picker",
    "time-picker"
   ]
  },
  {
   "id": "containers",
   "label": "容器类",
   "componentIds": [
    "form-field",
    "list-card",
    "dialog",
    "alert-dialog",
    "semi-modal"
   ]
  },
  {
   "id": "specialized",
   "label": "特殊组件",
   "componentIds": [
    "attachment"
   ]
  }
 ]
}
```

## 资产 {#assets}

9 个 SVG 图标，按目录分组。

```json design
{
 "title": "图标",
 "categories": [
  {
   "title": "图标",
   "subs": [
    {
     "title": "状态",
     "items": [
      {
       "name": "danger-circle",
       "type": "SVG",
       "size": 249,
       "src": "assets/icons/status/danger-circle.svg"
      },
      {
       "name": "info-circle",
       "type": "SVG",
       "size": 255,
       "src": "assets/icons/status/info-circle.svg"
      },
      {
       "name": "neutral-circle",
       "type": "SVG",
       "size": 226,
       "src": "assets/icons/status/neutral-circle.svg"
      },
      {
       "name": "success-circle",
       "type": "SVG",
       "size": 240,
       "src": "assets/icons/status/success-circle.svg"
      },
      {
       "name": "warning-circle",
       "type": "SVG",
       "size": 253,
       "src": "assets/icons/status/warning-circle.svg"
      }
     ]
    },
    {
     "title": "标题栏",
     "items": [
      {
       "name": "window-close",
       "type": "SVG",
       "size": 609,
       "src": "assets/icons/titlebar/window-close.svg"
      },
      {
       "name": "window-maximize",
       "type": "SVG",
       "size": 1470,
       "src": "assets/icons/titlebar/window-maximize.svg"
      },
      {
       "name": "window-minimize",
       "type": "SVG",
       "size": 318,
       "src": "assets/icons/titlebar/window-minimize.svg"
      }
     ]
    },
    {
     "title": "components",
     "items": [
      {
       "name": "checkbox-check",
       "type": "SVG",
       "size": 1529,
       "src": "assets/icons/components/checkbox-check.svg"
      }
     ]
    }
   ]
  }
 ]
}
```

## 布局 Pattern {#patterns}

这里展示页面组合契约，而不是新的一组组件。Pattern A–D 的区域顺序、栏宽策略、Titlebar 分段、表面、分割线、滚动与 inset owner、最小窗口和动作槽位，统一来自 pattern-contracts.json；HTML 只执行解析后的同一份规则。

```json design
{
 "title": "布局 Pattern",
 "items": [
  {
   "id": "pattern-a-two-pane",
   "name": "Pattern A · 两栏",
   "label": "导航 + 内容　Pattern A: Two-Pane Navigation + Content",
   "workflow": "简单浏览 / 设置 / 内容中心",
   "minWindow": "960 × 640",
   "extends": null,
   "titleLayer": "全局标题层，按栏分段",
   "regions": [
    {
     "id": "primary-navigation",
     "label": "一级导航",
     "width": "固定 240px",
     "px": 240,
     "surface": "浅底 subtle",
     "scroll": "独立滚动"
    },
    {
     "id": "main-content",
     "label": "主内容",
     "width": "自适应",
     "px": null,
     "surface": "白底 surface",
     "scroll": "独立滚动"
    }
   ],
   "slots": [
    {
     "id": "global-primary-action",
     "owner": "一级导航",
     "cardinality": "0..1",
     "allowed": ""
    },
    {
     "id": "primary-navigation-shell",
     "owner": "一级导航",
     "cardinality": "1",
     "allowed": ""
    },
    {
     "id": "primary-navigation-footer",
     "owner": "一级导航",
     "cardinality": "0..1",
     "allowed": "icon-text-ghost"
    },
    {
     "id": "global-title-layer",
     "owner": "整页",
     "cardinality": "1",
     "allowed": ""
    },
    {
     "id": "main-content-title",
     "owner": "主内容",
     "cardinality": "0..1",
     "allowed": ""
    }
   ],
   "tab": "A · 双栏",
   "previewNote": "规范预览页的示例内容"
  },
  {
   "id": "pattern-b-three-pane",
   "name": "Pattern B · 三栏",
   "label": "导航 + 列表 + 详情　Pattern B: Three-Pane Navigation + List + Detail",
   "workflow": "列表 → 详情反复切换",
   "minWindow": "1100 × 720",
   "extends": null,
   "titleLayer": "全局标题层，按栏分段",
   "regions": [
    {
     "id": "primary-navigation",
     "label": "一级导航",
     "width": "固定 240px",
     "px": 240,
     "surface": "浅底 subtle",
     "scroll": "独立滚动"
    },
    {
     "id": "secondary-list",
     "label": "列表",
     "width": "固定 360px",
     "px": 360,
     "surface": "白底 surface",
     "scroll": "独立滚动"
    },
    {
     "id": "main-detail",
     "label": "详情",
     "width": "自适应，至少 500px",
     "px": null,
     "surface": "白底 surface",
     "scroll": "独立滚动"
    }
   ],
   "slots": [
    {
     "id": "primary-navigation-shell",
     "owner": "一级导航",
     "cardinality": "0..1",
     "allowed": ""
    },
    {
     "id": "global-title-layer",
     "owner": "整页",
     "cardinality": "1",
     "allowed": ""
    },
    {
     "id": "global-primary-action",
     "owner": "一级导航",
     "cardinality": "0..1",
     "allowed": ""
    },
    {
     "id": "secondary-navigation-content",
     "owner": "一级导航",
     "cardinality": "0..n",
     "allowed": ""
    },
    {
     "id": "primary-navigation-bottom",
     "owner": "一级导航",
     "cardinality": "0..n",
     "allowed": ""
    },
    {
     "id": "secondary-list-title",
     "owner": "列表",
     "cardinality": "0..1",
     "allowed": "search"
    },
    {
     "id": "main-detail-title",
     "owner": "详情",
     "cardinality": "0..1",
     "allowed": "titlebar"
    },
    {
     "id": "main-detail-actions",
     "owner": "详情",
     "cardinality": "0..n",
     "allowed": "icon / icon-text-ghost"
    }
   ],
   "tab": "B · 三栏",
   "previewNote": "规范预览页的示例内容"
  }
 ],
 "view": {
  "html": {
   "$file": "patterns/view.html"
  },
  "bg": "rgba(0, 0, 0, 0.047)",
  "cards": [
   {
    "id": "pattern-runtime-renderer",
    "axes": [
     [
      "data-runtime-pattern",
      [
       "pattern-a-two-pane",
       "pattern-b-three-pane"
      ]
     ],
     [
      "data-runtime-mode",
      [
       "skeleton",
       "runtime"
      ]
     ]
    ],
    "host": "data-runtime-preview-host",
    "meta": "data-runtime-preview-meta",
    "states": {
     "pattern-a-two-pane|skeleton": {
      "html": "<main class=\"tui-pattern-runtime tui-pattern-runtime--pattern-a-two-pane\" data-tui-pattern=\"pattern-a-two-pane\" data-pattern=\"pattern-a-two-pane\" data-pattern-mode=\"skeleton\" data-pattern-framework=\"html\" data-tui-pane-order=\"primary-navigation main-content\" data-pattern-minimum-window=\"960x640\" data-pattern-authority=\"assets/design-system/pattern-contracts.json\"><header class=\"tui-pattern-runtime__global-title\" data-pattern-slot=\"global-title-layer\" data-pattern-global-title-layer=\"\"><span class=\"tui-pattern-runtime__slot-placeholder\" data-pattern-slot-placeholder=\"global-title-layer\" aria-hidden=\"true\"></span></header><div class=\"tui-pattern-runtime__pane-grid\" data-pattern-pane-grid=\"\"><section class=\"tui-pattern-runtime__pane tui-pattern-runtime__pane--navigation\" data-pattern-region=\"primary-navigation\" data-tui-pane-role=\"primary-navigation\" data-pattern-inset-owner=\"primary-navigation-shell\" data-pattern-scroll-owner=\"primary-navigation\" data-pattern-surface=\"subtle\" data-pattern-width-token=\"layout/sidebar-expanded\" data-pattern-divider-edges=\"right\"><div class=\"tui-pattern-runtime__navigation-top\" data-pattern-shell-slot=\"navigation-top\"></div><div class=\"tui-pattern-runtime__scroll-body\" data-pattern-scroll-body=\"\"><div class=\"tui-pattern-runtime__slot\" data-pattern-slot=\"global-primary-action\"><span class=\"tui-pattern-runtime__slot-placeholder\" data-pattern-slot-placeholder=\"global-primary-action\" aria-hidden=\"true\"></span></div><div class=\"tui-pattern-runtime__slot\" data-pattern-slot=\"primary-navigation-shell\"><span class=\"tui-pattern-runtime__slot-placeholder\" data-pattern-slot-placeholder=\"primary-navigation-shell\" aria-hidden=\"true\"></span></div></div><div class=\"tui-pattern-runtime__slot\" data-pattern-slot=\"primary-navigation-footer\" data-pattern-shell-slot=\"primary-navigation-footer\" data-pattern-shell-placement=\"bottom\"><span class=\"tui-pattern-runtime__slot-placeholder\" data-pattern-slot-placeholder=\"primary-navigation-footer\" aria-hidden=\"true\"></span></div></section><section class=\"tui-pattern-runtime__pane tui-pattern-runtime__pane--content\" data-pattern-region=\"main-content\" data-tui-pane-role=\"main-content\" data-pattern-inset-owner=\"main-content-shell\" data-pattern-scroll-owner=\"main-content\" data-pattern-surface=\"surface\" data-pattern-width-token=\"fill\" data-pattern-divider-edges=\"\"><header class=\"tui-pattern-runtime__pane-title\" data-pattern-title-segment=\"main-content\"><div class=\"tui-pattern-runtime__slot\" data-pattern-slot=\"main-content-title\" data-pattern-shell-slot=\"main-content-title\" data-pattern-shell-placement=\"title\"><span class=\"tui-pattern-runtime__slot-placeholder\" data-pattern-slot-placeholder=\"main-content-title\" aria-hidden=\"true\"></span></div></header><div class=\"tui-pattern-runtime__scroll-body\" data-pattern-scroll-body=\"\"></div></section></div></main>",
      "meta": "pattern-a-two-pane · skeleton · primary-navigation → main-content · min 960×640"
     },
     "pattern-a-two-pane|runtime": {
      "html": {
       "$file": "patterns/view-0-pattern-a-two-pane-runtime.html"
      },
      "meta": "pattern-a-two-pane · runtime · primary-navigation → main-content · min 960×640"
     },
     "pattern-b-three-pane|skeleton": {
      "html": {
       "$file": "patterns/view-0-pattern-b-three-pane-skeleton.html"
      },
      "meta": "pattern-b-three-pane · skeleton · primary-navigation → secondary-list → main-detail · min 1100×720"
     },
     "pattern-b-three-pane|runtime": {
      "html": {
       "$file": "patterns/view-0-pattern-b-three-pane-runtime.html"
      },
      "meta": "pattern-b-three-pane · runtime · primary-navigation → secondary-list → main-detail · min 1100×720"
     }
    }
   },
   {
    "id": "secondary-page-runtime",
    "axes": [
     [
      "data-secondary-runtime-layout",
      [
       "continuation",
       "new-page"
      ]
     ],
     [
      "data-secondary-runtime-mode",
      [
       "skeleton",
       "runtime"
      ]
     ]
    ],
    "host": "data-secondary-runtime-host",
    "meta": "data-secondary-runtime-meta",
    "states": {
     "continuation|skeleton": {
      "html": "<section class=\"tui-secondary-page-runtime tui-secondary-page-runtime--continuation\" data-secondary-page-runtime=\"true\" data-secondary-page-layout=\"continuation\" data-secondary-page-mode=\"skeleton\" data-secondary-page-titlebar-size=\"large\"><aside class=\"tui-secondary-page-runtime__navigation\" data-secondary-page-region=\"navigation\"><span class=\"tui-secondary-page-runtime__slot-placeholder\" data-secondary-page-slot-placeholder=\"navigation\" aria-hidden=\"true\"></span></aside><header class=\"tui-secondary-page-runtime__titlebar\" data-secondary-page-slot=\"titlebar\"><span class=\"tui-secondary-page-runtime__slot-placeholder\" data-secondary-page-slot-placeholder=\"titlebar\" aria-hidden=\"true\"></span></header><main class=\"tui-secondary-page-runtime__content\" data-secondary-page-slot=\"content\"><span class=\"tui-secondary-page-runtime__slot-placeholder\" data-secondary-page-slot-placeholder=\"content\" aria-hidden=\"true\"></span></main></section>",
      "meta": "secondary-page-runtime · skeleton · 返回 + Titlebar_L"
     },
     "continuation|runtime": {
      "html": {
       "$file": "patterns/view-1-continuation-runtime.html"
      },
      "meta": "secondary-page-runtime · runtime · 返回 + Titlebar_L"
     },
     "new-page|skeleton": {
      "html": "<section class=\"tui-secondary-page-runtime tui-secondary-page-runtime--new-page\" data-secondary-page-runtime=\"true\" data-secondary-page-layout=\"new-page\" data-secondary-page-mode=\"skeleton\" data-secondary-page-titlebar-size=\"small\"><header class=\"tui-secondary-page-runtime__titlebar\" data-secondary-page-slot=\"titlebar\"><span class=\"tui-secondary-page-runtime__slot-placeholder\" data-secondary-page-slot-placeholder=\"titlebar\" aria-hidden=\"true\"></span></header><main class=\"tui-secondary-page-runtime__content\" data-secondary-page-slot=\"content\"><span class=\"tui-secondary-page-runtime__slot-placeholder\" data-secondary-page-slot-placeholder=\"content\" aria-hidden=\"true\"></span></main></section>",
      "meta": "secondary-page-runtime · skeleton · Titlebar_S + 上下布局"
     },
     "new-page|runtime": {
      "html": {
       "$file": "patterns/view-1-new-page-runtime.html"
      },
      "meta": "secondary-page-runtime · runtime · Titlebar_S + 上下布局"
     }
    }
   }
  ],
  "css": {
   "$file": "patterns/view.css"
  }
 }
}
```

## Pixso 映射 {#mapping}

26 个组件登记了 Pixso 设计组件，其中 25 个有组件链接（已关联），其余显示为未关联。

```json design
{
 "accordion": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Accordion",
   "status": "aligned",
   "logicalName": "Accordion/Default",
   "verification": "linked",
   "props": {
    "state": {
     "label": "State",
     "values": {
      "collapsed": "Collapsed",
      "expanded": "Expanded"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1009",
   "componentKey": "abc055b6305310e4424328bd49589d9a551726af",
   "variants": 2,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1009"
  },
  "rows": [
   [
    "color.text-muted",
    "--color-text-muted",
    "neutral-dark/60",
    "",
    "#00000099"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ]
  ]
 },
 "alert": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Alert",
   "status": "aligned",
   "logicalName": "Alert/Default",
   "verification": "linked",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:969",
   "componentKey": "3e8e25653dc41fd19a5c3e0c1561d8ca8514c6e7",
   "variants": 5,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A969"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "color.icon",
    "--color-icon",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ]
  ]
 },
 "badge": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Badge",
   "status": "aligned",
   "logicalName": "Badge/Default",
   "verification": "linked",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:931",
   "componentKey": "271b9c0c5f2a76afdc99ed43adfd653074e72b86",
   "variants": 5,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A931"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ]
  ]
 },
 "breadcrumb": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Breadcrumb",
   "status": "aligned",
   "logicalName": "Breadcrumb/Default",
   "verification": "linked",
   "props": {
    "level": {
     "label": "level",
     "values": {
      "2": "2",
      "3": "3",
      "4": "4"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:994",
   "componentKey": "602f9fc0be76438b984fef6e2396bbb3b7bbf177",
   "variants": 3,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A994"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ]
  ]
 },
 "button": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Button",
   "status": "aligned",
   "logicalName": "Button/Primary/Default",
   "verification": "linked",
   "props": {
    "type": {
     "label": "type",
     "values": {
      "primary": "Primary",
      "secondary": "Secondary",
      "ghost": "Ghost",
      "danger": "Danger"
     }
    },
    "size": {
     "label": "size",
     "values": {
      "medium": "Medium",
      "small": "Small"
     }
    },
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "hover": "Hover",
      "pressed": "Pressed",
      "focus": "Focus",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:820",
   "componentKey": "16f8c5796d802294cdb6e3a756ece48b281e0aa4",
   "variants": 40,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A820"
  },
  "rows": [
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "color.primary-text",
    "--color-primary-text",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "radius.button",
    "--radius-button",
    "radius/08",
    "",
    "8px"
   ]
  ]
 },
 "checkbox": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "CheckBox",
   "status": "aligned",
   "logicalName": "Checkbox/Default",
   "verification": "linked",
   "props": {
    "checked": {
     "label": "checked",
     "values": {
      "false": "false",
      "true": "true"
     }
    },
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "hover": "Hover",
      "focus": "Focus",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:853",
   "componentKey": "76896a75aedd66db6ffcc8d41f3c681c0b1826fb",
   "variants": 8,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A853"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ]
  ]
 },
 "chips": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Chips",
   "status": "aligned",
   "logicalName": "Chips/Default",
   "verification": "linked",
   "props": {
    "状态": {
     "label": "状态",
     "values": {
      "default": "Default",
      "hover": "Hover",
      "pressed": "Pressed",
      "selected": "Selected",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:920",
   "componentKey": "e10d89af4c740ae765998ce4e0bcab812faa900d",
   "variants": 5,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A920"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface-muted",
    "--color-surface-muted",
    "neutral-dark/05",
    "",
    "#0000000C"
   ],
   [
    "color.state-layer-hover",
    "--state-layer-hover",
    "neutral-dark/05",
    "",
    "#0000000C"
   ],
   [
    "color.state-layer-pressed",
    "--state-layer-pressed",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "radius.tag",
    "--radius-tag",
    "radius/08",
    "",
    "8px"
   ]
  ]
 },
 "radio": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Radio",
   "status": "aligned",
   "logicalName": "Radio/Unselected/Default",
   "verification": "linked",
   "props": {
    "checked": {
     "label": "checked",
     "values": {
      "false": "false",
      "true": "true"
     }
    },
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "hover": "Hover",
      "focus": "Focus",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:882",
   "componentKey": "23507f88ebf7c709c516976c8326c06af7a3baeb",
   "variants": 8,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A882"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "color.primary-text",
    "--color-primary-text",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "size.indicator.radio-size",
    "--radio-size",
    "size/20",
    "",
    "20px"
   ],
   [
    "radius.full",
    "--radius-full",
    "radius/full",
    "",
    "999px"
   ],
   [
    "spacing.gap.choice-label",
    "--gap-choice-label",
    "space/3",
    "",
    "8px"
   ]
  ]
 },
 "collapsible": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Collapsible",
   "status": "aligned",
   "logicalName": "Collapsible/Default",
   "verification": "linked",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1022",
   "componentKey": "91bf0fecc5392a85e5389bbed83216deb0a82df3",
   "variants": 2,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1022"
  },
  "rows": [
   [
    "color.text-muted",
    "--color-text-muted",
    "neutral-dark/60",
    "",
    "#00000099"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ]
  ]
 },
 "dialog": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Dialog-2in1",
   "status": "aligned",
   "logicalName": "Dialog/Default",
   "verification": "linked",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1353",
   "componentKey": "4c92f02362eebe905c22fefdd063d8e7fb09e098",
   "variants": 3,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1353"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "radius.card",
    "--radius-card",
    "radius/12",
    "",
    "12px"
   ]
  ]
 },
 "form-field": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Form Field",
   "status": "aligned",
   "logicalName": "Form Field/Default",
   "verification": "linked",
   "props": {
    "surface": {
     "label": "surface",
     "values": {
      "white": "White",
      "gray": "Gray"
     }
    },
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "error": "Error",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1158",
   "componentKey": "77365411276f911241898145feabe092e54e9ccd",
   "variants": 6,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1158"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.alert",
    "--color-alert",
    "—",
    "",
    "#E84026FF"
   ]
  ]
 },
 "input": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Input",
   "status": "aligned",
   "logicalName": "Input/White Surface/Default",
   "verification": "linked",
   "props": {
    "surface": {
     "label": "surface",
     "values": {
      "bg-white": "bg-white",
      "bg-gray": "bg-gray"
     }
    },
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "hover": "Hover",
      "focus": "Focus",
      "error": "Error",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1045",
   "componentKey": "58ea61eefbd31a5b0eccf9cfc10bd79b400d2758",
   "variants": 10,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1045"
  },
  "rows": [
   [
    "color.input-bg",
    "--color-input-bg",
    "neutral-dark/05",
    "",
    "#0000000C"
   ],
   [
    "color.icon",
    "--color-icon",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.text-muted",
    "--color-text-muted",
    "neutral-dark/60",
    "",
    "#00000099"
   ],
   [
    "color.text-subtle",
    "--color-text-subtle",
    "neutral-dark/40",
    "",
    "#00000066"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "radius.input",
    "--radius-input",
    "radius/08",
    "",
    "8px"
   ]
  ]
 },
 "menubar": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Menubar",
   "status": "aligned",
   "logicalName": "Menubar/Default",
   "verification": "linked",
   "props": {
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "hover": "Hover",
      "open": "Open",
      "disabled": "Disabled"
     }
    },
    "surface": {
     "label": "surface",
     "values": {
      "bg-white": "bg-white",
      "bg-gray": "bg-gray"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1253",
   "componentKey": "6c42321b8dc58e666f58f09913adbe7a012e7a6c",
   "variants": 8,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1253"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "icon-size-lg",
    "--icon-size-lg",
    "size/24",
    "",
    "24px"
   ]
  ]
 },
 "number-selector": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Number Selector/Default",
   "status": "aligned",
   "logicalName": "Number Selector/Default",
   "verification": "linked",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1354",
   "componentKey": "65299ab1337a0acf2f8c7b2b68cdb3dec9f70a0f",
   "variants": 1,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1354"
  },
  "rows": [
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "radius.input",
    "--radius-input",
    "radius/08",
    "",
    "8px"
   ]
  ]
 },
 "pagination": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Pagination/Default",
   "status": "aligned",
   "logicalName": "Pagination/Default",
   "verification": "linked",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1363",
   "componentKey": "22b1646fda4a5cd530f6db96b4deee355a099329",
   "variants": 1,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1363"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ]
  ]
 },
 "progress": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Progress/Default",
   "status": "aligned",
   "logicalName": "Progress/Default",
   "verification": "linked",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1384",
   "componentKey": "6e0c3d645518ea407c45bfb7d49a35091f47aaf3",
   "variants": 1,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1384"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ]
  ]
 },
 "search": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Search",
   "status": "aligned",
   "logicalName": "Search/White Surface/Default",
   "verification": "linked",
   "props": {
    "surface": {
     "label": "surface",
     "values": {
      "bg-white": "bg-white",
      "bg-gray": "bg-gray"
     }
    },
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "focus": "Focus",
      "filled": "Filled",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1127",
   "componentKey": "874971c12cb20aab5f8711d447a030113f16fc95",
   "variants": 8,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1127"
  },
  "rows": [
   [
    "color.input-bg",
    "--color-input-bg",
    "neutral-dark/05",
    "",
    "#0000000C"
   ],
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.icon",
    "--color-icon",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "radius.search",
    "--radius-search",
    "radius/08",
    "",
    "8px"
   ]
  ]
 },
 "segmented-button": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Segmented Button",
   "status": "aligned",
   "logicalName": "Segmented Button/Default",
   "verification": "linked",
   "props": {
    "count": {
     "label": "count",
     "values": {
      "2": "2",
      "3": "3",
      "4": "4"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1275",
   "componentKey": "405e197efe366458c982a92d7e6b4924a91fc901",
   "variants": 3,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1275"
  },
  "rows": [
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "radius.tab",
    "--radius-tab",
    "radius/08",
    "",
    "8px"
   ]
  ]
 },
 "sidebar": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Sidebar Item",
   "status": "aligned",
   "logicalName": "Sidebar Item/Default",
   "verification": "linked",
   "props": {
    "state": {
     "label": "state",
     "values": {
      "default": "default",
      "hover": "hover",
      "selected": "selected",
      "disabled": "disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1292",
   "componentKey": "2eddafe7fd3458ce2aed776b5e6889f741099eaf",
   "variants": 4,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1292"
  },
  "rows": [
   [
    "color.sidebar-bg",
    "--color-sidebar-bg",
    "neutral-dark/05",
    "",
    "#0000000C"
   ],
   [
    "color.sidebar-selected",
    "--color-sidebar-selected",
    "brand/10",
    "",
    "#0A59F719"
   ],
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "radius.list-item",
    "--radius-list-item",
    "radius/08",
    "",
    "8px"
   ]
  ]
 },
 "slider": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Slider",
   "status": "aligned",
   "logicalName": "Slider/Default",
   "verification": "linked",
   "props": {
    "style": {
     "label": "style",
     "values": {
      "style-1": "style-1",
      "style-2": "style-2"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1313",
   "componentKey": "922ea7ecf6ba23d82c0d21adb7e81ddd4b17e99e",
   "variants": 2,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1313"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ]
  ]
 },
 "color-picker": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Snackbar/ColorPicker-Tablet",
   "status": "aligned",
   "logicalName": "ColorPicker/Tablet",
   "verification": "linked",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1390",
   "componentKey": "dcdcffec5996cc3f4790995ed8c927151acc4597",
   "variants": 1,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1390"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "radius.card",
    "--radius-card",
    "radius/12",
    "",
    "12px"
   ]
  ]
 },
 "switch": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Switch",
   "status": "aligned",
   "logicalName": "Switch/Default",
   "verification": "linked",
   "props": {
    "checked": {
     "label": "checked",
     "values": {
      "false": "false",
      "true": "true"
     }
    },
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "hover": "Hover",
      "focus": "Focus",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:899",
   "componentKey": "b1a55c3adff1addec077ed24827c3f8e3cfa1fee",
   "variants": 8,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A899"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ]
  ]
 },
 "sub-tabs": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Sub Tabs Item",
   "status": "aligned",
   "logicalName": "Sub Tabs/Default",
   "verification": "linked",
   "props": {
    "state": {
     "label": "state",
     "values": {
      "unselected": "Unselected",
      "hover": "Hover",
      "selected": "Selected",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1301",
   "componentKey": "0b2971aa5bf7decbfb844ffe334e3313ae5e60f6",
   "variants": 4,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1301"
  },
  "rows": [
   [
    "color.neutral-dark-05",
    "--color-neutral-dark-05",
    "neutral-dark/05",
    "",
    "#0000000C"
   ],
   [
    "color.text-muted",
    "--color-text-muted",
    "neutral-dark/60",
    "",
    "#00000099"
   ],
   [
    "color.brand-10",
    "--color-brand-10",
    "brand/10",
    "",
    "#0A59F719"
   ],
   [
    "color.brand-100",
    "--color-brand-100",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "radius.subtab",
    "--radius-subtab",
    "radius/08",
    "",
    "8px"
   ]
  ]
 },
 "textarea": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Textarea",
   "status": "aligned",
   "logicalName": "Textarea/Default",
   "verification": "linked",
   "props": {
    "surface": {
     "label": "surface",
     "values": {
      "bg-white": "bg-white",
      "bg-gray": "bg-gray"
     }
    },
    "state": {
     "label": "state",
     "values": {
      "default": "Default",
      "hover": "Hover",
      "focus": "Focus",
      "error": "Error",
      "disabled": "Disabled"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1076",
   "componentKey": "2eeeb3af381c00c58626e166823eefd085a04ca6",
   "variants": 10,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1076"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.border",
    "--color-border",
    "neutral-dark/10",
    "",
    "#00000019"
   ]
  ]
 },
 "snackbar": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Snackbar",
   "status": "aligned",
   "logicalName": "Snackbar/Default",
   "verification": "linked",
   "props": {
    "左侧区域": {
     "label": "左侧区域",
     "values": {
      "1": "1",
      "2": "2"
     }
    }
   },
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供",
   "fileKey": "ktaB_h0CgSfZUkSOoPua7Q",
   "nodeId": "2:1329",
   "componentKey": "69d6e31205f3a1815ce5b7adced14552b35dca3a",
   "variants": 2,
   "url": "https://pixso.cn/app/design/ktaB_h0CgSfZUkSOoPua7Q?item-id=2%3A1329"
  },
  "rows": [
   [
    "color.text",
    "--color-text",
    "neutral-dark/90",
    "",
    "#000000E5"
   ],
   [
    "color.surface",
    "--color-surface",
    "neutral-light/100",
    "",
    "#FFFFFFFF"
   ],
   [
    "color.primary",
    "--color-primary",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "shadow.3",
    "--shadow-3",
    "—",
    "",
    "0 10px 50px 0 rgb(0 0 30 / 15%)"
   ],
   [
    "radius.5",
    "--radius-5",
    "radius/16",
    "",
    "16px"
   ]
  ]
 },
 "primary-navigation-item": {
  "pixso": {
   "library": "text-to-ui-pixso 已登记组件",
   "component": "Primary Navigation Item icon",
   "status": "partial",
   "logicalName": "Primary Navigation Item/Level 1",
   "verification": "registered",
   "props": {},
   "propsNote": "变体对应关系在 text-to-ui-pixso 仓库，本仓未提供"
  },
  "rows": [
   [
    "color.primary-level-unselected",
    "--color-primary-level-unselected",
    "neutral-dark/40",
    "",
    "#00000066"
   ],
   [
    "color.sidebar-accent",
    "--color-sidebar-accent",
    "neutral-dark/05",
    "",
    "#0000000C"
   ],
   [
    "color.sidebar-selected-text",
    "--color-sidebar-selected-text",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "color.focus-ring",
    "--color-focus-ring",
    "brand/100",
    "",
    "#0A59F7FF"
   ],
   [
    "size.icon-button",
    "--size-icon-button",
    "size/40",
    "",
    "40px"
   ],
   [
    "icon-size-lg",
    "--icon-size-lg",
    "size/24",
    "",
    "24px"
   ],
   [
    "radius.icon-button",
    "--radius-icon-button",
    "radius/08",
    "",
    "8px"
   ]
  ]
 }
}
```
