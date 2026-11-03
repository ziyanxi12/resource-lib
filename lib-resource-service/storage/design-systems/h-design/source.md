---
format: octo-design-md/1
id: h-design
name: "H Design 官网设计规范"
author: "罗唯"
cover: cover-blue.jpg
usage: 143
order: 1
source_skill: "H Design 官网设计规范"
adapter: token-json
source_files: "1126"
source_size: "18.6 MB"
source_entry: "04-quality-verification/shadcn-verification/references"
---

# H Design 官网设计规范

> 由 spec-skill-to-design-system 从规范 Skill 转换生成。每个区块的正文是说明和使用规则，`json design` 数据块供管理页渲染；
> 标注「未定义」的区块表示规范里没有提取到这部分内容。

## 概览 {#overview}

面向华为官网 UI 设计规范的 AI Skills 工程包，用于指导 AI 基于 H Design 设计系统生成、还原、维护和验证官网页面、组件与楼层，适用于 Pixso 设计稿转组件、Storybook 预览、页面原型生成、设计规范校验和设计到开发交付协作。

## 颜色 {#color}

82 个颜色 token，按用途分组。

```json design
{
 "title": "语义色",
 "themes": [
  "light",
  "dark"
 ],
 "groups": [
  {
   "title": "品牌色",
   "desc": "品牌主色，用于主操作、选中与强调",
   "kind": "cards",
   "tokens": [
    {
     "name": "brand",
     "token": "--harmony-brand",
     "value": "rgba(10, 89, 247, 1)",
     "dark": "rgba(31, 113, 255, 1)"
    }
   ]
  },
  {
   "title": "功能色",
   "desc": "警示、警告、确认等状态反馈",
   "kind": "cards",
   "tokens": [
    {
     "name": "alert",
     "token": "--harmony-alert",
     "value": "rgba(237, 111, 33, 1)",
     "dark": "rgba(237, 111, 33, 1)"
    },
    {
     "name": "confirm",
     "token": "--harmony-confirm",
     "value": "rgba(100, 187, 92, 1)",
     "dark": "rgba(100, 187, 92, 1)"
    },
    {
     "name": "warning",
     "token": "--harmony-warning",
     "value": "rgba(232, 64, 38, 1)",
     "dark": "rgba(232, 64, 38, 1)"
    }
   ]
  },
  {
   "title": "背景色",
   "desc": "页面与容器的层级背景",
   "kind": "cards",
   "tokens": [
    {
     "name": "background-emphasize",
     "token": "--harmony-background-emphasize",
     "value": "rgba(10, 89, 247, 1)",
     "dark": "rgba(31, 113, 255, 1)"
    },
    {
     "name": "background-fourth",
     "token": "--harmony-background-fourth",
     "value": "rgba(209, 209, 214, 1)",
     "dark": "rgba(46, 48, 51, 1)"
    },
    {
     "name": "background-primary",
     "token": "--harmony-background-primary",
     "value": "rgba(255, 255, 255, 1)",
     "dark": "rgba(229, 229, 229, 1)"
    },
    {
     "name": "background-secondary",
     "token": "--harmony-background-secondary",
     "value": "rgba(241, 243, 245, 1)",
     "dark": "rgba(25, 26, 28, 1)"
    },
    {
     "name": "background-tertiary",
     "token": "--harmony-background-tertiary",
     "value": "rgba(229, 229, 234, 1)",
     "dark": "rgba(32, 34, 36, 1)"
    }
   ]
  },
  {
   "title": "文本色",
   "desc": "不同层级的文字颜色",
   "kind": "cards",
   "tokens": [
    {
     "name": "font-emphasize",
     "token": "--harmony-font-emphasize",
     "value": "rgba(10, 89, 247, 1)",
     "dark": "rgba(94, 161, 255, 1)"
    },
    {
     "name": "font-fourth",
     "token": "--harmony-font-fourth",
     "value": "rgba(0, 0, 0, 0.2)",
     "dark": "rgba(255, 255, 255, 0.2)"
    },
    {
     "name": "font-on-fourth",
     "token": "--harmony-font-on-fourth",
     "value": "rgba(255, 255, 255, 0.2)",
     "dark": "rgba(255, 255, 255, 0.2)"
    },
    {
     "name": "font-on-primary",
     "token": "--harmony-font-on-primary",
     "value": "rgba(255, 255, 255, 1)",
     "dark": "rgba(255, 255, 255, 1)"
    },
    {
     "name": "font-on-secondary",
     "token": "--harmony-font-on-secondary",
     "value": "rgba(255, 255, 255, 0.6)",
     "dark": "rgba(255, 255, 255, 0.662745)"
    },
    {
     "name": "font-on-tertiary",
     "token": "--harmony-font-on-tertiary",
     "value": "rgba(255, 255, 255, 0.4)",
     "dark": "rgba(255, 255, 255, 0.4)"
    },
    {
     "name": "font-primary",
     "token": "--harmony-font-primary",
     "value": "rgba(0, 0, 0, 0.898039)",
     "dark": "rgba(255, 255, 255, 1)"
    },
    {
     "name": "font-secondary",
     "token": "--harmony-font-secondary",
     "value": "rgba(0, 0, 0, 0.6)",
     "dark": "rgba(255, 255, 255, 0.662745)"
    },
    {
     "name": "font-tertiary",
     "token": "--harmony-font-tertiary",
     "value": "rgba(0, 0, 0, 0.4)",
     "dark": "rgba(255, 255, 255, 0.4)"
    }
   ]
  },
  {
   "title": "图标色",
   "desc": "不同层级的图标颜色",
   "kind": "cards",
   "tokens": [
    {
     "name": "icon-emphasize",
     "token": "--harmony-icon-emphasize",
     "value": "rgba(10, 89, 247, 1)",
     "dark": "rgba(94, 161, 255, 1)"
    },
    {
     "name": "icon-fourth",
     "token": "--harmony-icon-fourth",
     "value": "rgba(0, 0, 0, 0.2)",
     "dark": "rgba(255, 255, 255, 0.2)"
    },
    {
     "name": "icon-on-fourth",
     "token": "--harmony-icon-on-fourth",
     "value": "rgba(255, 255, 255, 0.2)",
     "dark": "rgba(255, 255, 255, 0.2)"
    },
    {
     "name": "icon-on-primary",
     "token": "--harmony-icon-on-primary",
     "value": "rgba(255, 255, 255, 1)",
     "dark": "rgba(255, 255, 255, 1)"
    },
    {
     "name": "icon-on-secondary",
     "token": "--harmony-icon-on-secondary",
     "value": "rgba(255, 255, 255, 0.662745)",
     "dark": "rgba(255, 255, 255, 0.662745)"
    },
    {
     "name": "icon-on-tertiary",
     "token": "--harmony-icon-on-tertiary",
     "value": "rgba(255, 255, 255, 0.4)",
     "dark": "rgba(255, 255, 255, 0.4)"
    },
    {
     "name": "icon-primary",
     "token": "--harmony-icon-primary",
     "value": "rgba(0, 0, 0, 0.898039)",
     "dark": "rgba(255, 255, 255, 1)"
    },
    {
     "name": "icon-secondary",
     "token": "--harmony-icon-secondary",
     "value": "rgba(0, 0, 0, 0.662745)",
     "dark": "rgba(255, 255, 255, 0.662745)"
    },
    {
     "name": "icon-sub-emphasize",
     "token": "--harmony-icon-sub-emphasize",
     "value": "rgba(10, 89, 127, 0.4)",
     "dark": "rgba(94, 161, 255, 0.4)"
    },
    {
     "name": "icon-tertiary",
     "token": "--harmony-icon-tertiary",
     "value": "rgba(0, 0, 0, 0.4)",
     "dark": "rgba(255, 255, 255, 0.4)"
    }
   ]
  },
  {
   "title": "组件色",
   "desc": "组件背景、描边、分割线与聚焦态",
   "kind": "cards",
   "tokens": [
    {
     "name": "comp-background-emphasize",
     "token": "--harmony-comp-background-emphasize",
     "value": "rgba(10, 89, 247, 1)",
     "dark": "rgba(31, 113, 255, 1)"
    },
    {
     "name": "comp-background-focus",
     "token": "--harmony-comp-background-focus",
     "value": "rgba(241, 243, 245, 1)",
     "dark": "rgba(0, 0, 0, 1)"
    },
    {
     "name": "comp-background-gray",
     "token": "--harmony-comp-background-gray",
     "value": "rgba(241, 243, 245, 1)",
     "dark": "rgba(229, 229, 234, 1)"
    },
    {
     "name": "comp-background-material-tabs",
     "token": "--harmony-comp-background-material-tabs",
     "value": "rgba(241, 243, 245, 0.8)",
     "dark": "rgba(25, 26, 28, 0.8)"
    },
    {
     "name": "comp-background-neutral",
     "token": "--harmony-comp-background-neutral",
     "value": "rgba(0, 0, 0, 1)",
     "dark": "rgba(255, 255, 255, 1)"
    },
    {
     "name": "comp-background-primary",
     "token": "--harmony-comp-background-primary",
     "value": "rgba(255, 255, 255, 1)",
     "dark": "rgba(32, 34, 36, 1)"
    },
    {
     "name": "comp-background-primary-contrary",
     "token": "--harmony-comp-background-primary-contrary",
     "value": "rgba(255, 255, 255, 1)",
     "dark": "rgba(229, 229, 229, 1)"
    },
    {
     "name": "comp-background-secondary",
     "token": "--harmony-comp-background-secondary",
     "value": "rgba(0, 0, 0, 0.098039)",
     "dark": "rgba(255, 255, 255, 0.098039)"
    },
    {
     "name": "comp-background-tertiary",
     "token": "--harmony-comp-background-tertiary",
     "value": "rgba(0, 0, 0, 0.047059)",
     "dark": "rgba(255, 255, 255, 0.047059)"
    },
    {
     "name": "comp-common-contrary",
     "token": "--harmony-comp-common-contrary",
     "value": "rgba(255, 255, 255, 1)",
     "dark": "rgba(0, 0, 0, 1)"
    },
    {
     "name": "comp-divider",
     "token": "--harmony-comp-divider",
     "value": "rgba(0, 0, 0, 0.2)",
     "dark": "rgba(255, 255, 255, 0.2)"
    },
    {
     "name": "comp-emphasize-secondary",
     "token": "--harmony-comp-emphasize-secondary",
     "value": "rgba(10, 89, 247, 0.2)",
     "dark": "rgba(31, 113, 255, 0.2)"
    },
    {
     "name": "comp-emphasize-tertiary",
     "token": "--harmony-comp-emphasize-tertiary",
     "value": "rgba(10, 89, 247, 0.098039)",
     "dark": "rgba(31, 113, 255, 0.098039)"
    },
    {
     "name": "comp-focused-primary",
     "token": "--harmony-comp-focused-primary",
     "value": "rgba(0, 0, 0, 0.898039)",
     "dark": "rgba(255, 255, 255, 0.898039)"
    },
    {
     "name": "comp-focused-secondary",
     "token": "--harmony-comp-focused-secondary",
     "value": "rgba(0, 0, 0, 0.6)",
     "dark": "rgba(255, 255, 255, 0.6)"
    },
    {
     "name": "comp-focused-tertiary",
     "token": "--harmony-comp-focused-tertiary",
     "value": "rgba(0, 0, 0, 0.4)",
     "dark": "rgba(255, 255, 255, 0.4)"
    },
    {
     "name": "comp-foreground-primary",
     "token": "--harmony-comp-foreground-primary",
     "value": "rgba(0, 0, 0, 1)",
     "dark": "rgba(229, 229, 229, 1)"
    }
   ]
  },
  {
   "title": "交互色",
   "desc": "悬停、按压、聚焦、选中等交互态",
   "kind": "cards",
   "tokens": [
    {
     "name": "interactive-active",
     "token": "--harmony-interactive-active",
     "value": "rgba(10, 89, 247, 1)",
     "dark": "rgba(49, 122, 247, 1)"
    },
    {
     "name": "interactive-click",
     "token": "--harmony-interactive-click",
     "value": "rgba(0, 0, 0, 0.098039)",
     "dark": "rgba(255, 255, 255, 0.098039)"
    },
    {
     "name": "interactive-focus",
     "token": "--harmony-interactive-focus",
     "value": "rgba(10, 89, 247, 1)",
     "dark": "rgba(49, 122, 247, 1)"
    },
    {
     "name": "interactive-hover",
     "token": "--harmony-interactive-hover",
     "value": "rgba(0, 0, 0, 0.047059)",
     "dark": "rgba(255, 255, 255, 0.047059)"
    },
    {
     "name": "interactive-pressed",
     "token": "--harmony-interactive-pressed",
     "value": "rgba(0, 0, 0, 0.098039)",
     "dark": "rgba(255, 255, 255, 0.098039)"
    },
    {
     "name": "interactive-select",
     "token": "--harmony-interactive-select",
     "value": "rgba(10, 89, 247, 0.2)",
     "dark": "rgba(49, 122, 247, 0.2)"
    }
   ]
  },
  {
   "title": "材质色",
   "desc": "毛玻璃与浮层材质",
   "kind": "cards",
   "tokens": [
    {
     "name": "COMPONENT_ULTRA_THICK_fill",
     "token": "--COMPONENT_ULTRA_THICK_fill",
     "value": "rgba(255, 255, 255, 0.9)",
     "dark": "rgba(46, 48, 51, 0.9)"
    },
    {
     "name": "FLOATING_ULTRA_THICK_fill",
     "token": "--FLOATING_ULTRA_THICK_fill",
     "value": "rgba(241, 243, 245, 0.9)",
     "dark": "rgba(32, 34, 36, 0.9)"
    },
    {
     "name": "FloatingSegmented-activated_fill",
     "token": "--FloatingSegmented-activated_fill",
     "value": "rgba(0, 0, 0, 0.047059)",
     "dark": "rgba(255, 255, 255, 0.047059)"
    },
    {
     "name": "Floating_background_line_fill",
     "token": "--Floating_background_line_fill",
     "value": "rgba(0, 0, 0, 0.1)",
     "dark": "rgba(255, 255, 255, 0.1)"
    },
    {
     "name": "Navigation_THIN_fill",
     "token": "--Navigation_THIN_fill",
     "value": "rgba(0, 0, 0, 0.2)",
     "dark": null
    },
    {
     "name": "comp_background_color_floating_smooth_fill",
     "token": "--comp_background_color_floating_smooth_fill",
     "value": "rgba(241, 243, 245, 0.95)",
     "dark": "rgba(48, 49, 49, 0.95)"
    },
    {
     "name": "comp_background_gradient_smooth_fill",
     "token": "--comp_background_gradient_smooth_fill",
     "value": "rgba(241, 243, 245, 0.95)",
     "dark": "rgba(0, 0, 0, 0.6)"
    },
    {
     "name": "slider-bubble",
     "token": "--slider-harmony-bubble",
     "value": "#5a5a5a",
     "dark": "rgba(255, 255, 255, 0.28)"
    }
   ]
  },
  {
   "title": "遗留色",
   "desc": "历史版本保留色值，新设计不建议使用",
   "kind": "cards",
   "tokens": [
    {
     "name": "x-legacy-brand-008",
     "token": "--harmony-x-legacy-brand-008",
     "value": "rgba(10, 89, 247, 0.08)",
     "dark": "rgba(10, 89, 247, 0.08)"
    },
    {
     "name": "x-legacy-brand-035",
     "token": "--harmony-x-legacy-brand-035",
     "value": "rgba(10, 89, 247, 0.35)",
     "dark": "rgba(10, 89, 247, 0.35)"
    },
    {
     "name": "x-legacy-brand-075",
     "token": "--harmony-x-legacy-brand-075",
     "value": "rgba(10, 89, 247, 0.75)",
     "dark": "rgba(10, 89, 247, 0.75)"
    },
    {
     "name": "x-legacy-brand-old",
     "token": "--harmony-x-legacy-brand-old",
     "value": "rgba(0, 125, 255, 1)",
     "dark": "rgba(0, 125, 255, 1)"
    },
    {
     "name": "x-legacy-cyan-accent",
     "token": "--harmony-x-legacy-cyan-accent",
     "value": "rgba(70, 177, 227, 0.4)",
     "dark": "rgba(70, 177, 227, 0.4)"
    },
    {
     "name": "x-legacy-frosted-surface",
     "token": "--harmony-x-legacy-frosted-surface",
     "value": "rgba(255, 255, 255, 0.9)",
     "dark": "rgba(255, 255, 255, 0.9)"
    },
    {
     "name": "x-legacy-meta-text",
     "token": "--harmony-x-legacy-meta-text",
     "value": "rgba(87, 93, 108, 1)",
     "dark": "rgba(87, 93, 108, 1)"
    },
    {
     "name": "x-legacy-orange-bg",
     "token": "--harmony-x-legacy-orange-bg",
     "value": "rgba(251, 101, 34, 0.1)",
     "dark": "rgba(251, 101, 34, 0.1)"
    },
    {
     "name": "x-legacy-orange-solid",
     "token": "--harmony-x-legacy-orange-solid",
     "value": "rgba(251, 101, 34, 1)",
     "dark": "rgba(251, 101, 34, 1)"
    },
    {
     "name": "x-legacy-orange-text",
     "token": "--harmony-x-legacy-orange-text",
     "value": "rgba(245, 101, 34, 1)",
     "dark": "rgba(245, 101, 34, 1)"
    },
    {
     "name": "x-legacy-overlay-004",
     "token": "--harmony-x-legacy-overlay-004",
     "value": "rgba(0, 0, 0, 0.04)",
     "dark": "rgba(0, 0, 0, 0.04)"
    },
    {
     "name": "x-legacy-overlay-005",
     "token": "--harmony-x-legacy-overlay-005",
     "value": "rgba(0, 0, 0, 0.05)",
     "dark": "rgba(0, 0, 0, 0.05)"
    },
    {
     "name": "x-legacy-overlay-006",
     "token": "--harmony-x-legacy-overlay-006",
     "value": "rgba(0, 0, 0, 0.06)",
     "dark": "rgba(0, 0, 0, 0.06)"
    },
    {
     "name": "x-legacy-overlay-008",
     "token": "--harmony-x-legacy-overlay-008",
     "value": "rgba(0, 0, 0, 0.08)",
     "dark": "rgba(0, 0, 0, 0.08)"
    },
    {
     "name": "x-legacy-overlay-010",
     "token": "--harmony-x-legacy-overlay-010",
     "value": "rgba(0, 0, 0, 0.1)",
     "dark": "rgba(0, 0, 0, 0.1)"
    },
    {
     "name": "x-legacy-overlay-012",
     "token": "--harmony-x-legacy-overlay-012",
     "value": "rgba(0, 0, 0, 0.12)",
     "dark": "rgba(0, 0, 0, 0.12)"
    },
    {
     "name": "x-legacy-overlay-016",
     "token": "--harmony-x-legacy-overlay-016",
     "value": "rgba(0, 0, 0, 0.16)",
     "dark": "rgba(0, 0, 0, 0.16)"
    },
    {
     "name": "x-legacy-overlay-020",
     "token": "--harmony-x-legacy-overlay-020",
     "value": "rgba(0, 0, 0, 0.2)",
     "dark": "rgba(0, 0, 0, 0.2)"
    },
    {
     "name": "x-legacy-page-bg",
     "token": "--harmony-x-legacy-page-bg",
     "value": "rgba(243, 245, 248, 1)",
     "dark": "rgba(243, 245, 248, 1)"
    },
    {
     "name": "x-legacy-panel-border",
     "token": "--harmony-x-legacy-panel-border",
     "value": "rgba(223, 225, 230, 1)",
     "dark": "rgba(223, 225, 230, 1)"
    },
    {
     "name": "x-legacy-stroke-mid",
     "token": "--harmony-x-legacy-stroke-mid",
     "value": "rgba(173, 176, 184, 1)",
     "dark": "rgba(173, 176, 184, 1)"
    },
    {
     "name": "x-legacy-title-text",
     "token": "--harmony-x-legacy-title-text",
     "value": "rgba(37, 43, 58, 1)",
     "dark": "rgba(37, 43, 58, 1)"
    },
    {
     "name": "x-legacy-white-085",
     "token": "--harmony-x-legacy-white-085",
     "value": "rgba(255, 255, 255, 0.85)",
     "dark": "rgba(255, 255, 255, 0.85)"
    }
   ]
  }
 ]
}
```

## 字体 {#typography}

15 级字号，字体家族 HarmonyHeiTi / Geist Variable。

### 使用规则

- 字体家族必须在 allowedFontFamilies 内
- 字号必须在 allowedFontSizes 内
- 字重必须在 allowedFontWeights 内
- 行高必须在 allowedLineHeights 内

```json design
{
 "title": "字体层级",
 "families": [
  "HarmonyHeiTi",
  "Geist Variable"
 ],
 "weights": [
  300,
  400,
  500,
  700
 ],
 "scale": [
  {
   "name": "display_l_light",
   "token": "--harmony-font-size-display-l",
   "family": "HarmonyHeiTi",
   "size": 56,
   "lineHeight": 67,
   "weight": 300
  },
  {
   "name": "display_m_light",
   "token": "--harmony-font-size-display-m",
   "family": "HarmonyHeiTi",
   "size": 48,
   "lineHeight": 58,
   "weight": 300
  },
  {
   "name": "display_s_light",
   "token": "--harmony-font-size-display-s",
   "family": "HarmonyHeiTi",
   "size": 38,
   "lineHeight": 46,
   "weight": 300
  },
  {
   "name": "title_l_bold",
   "token": "--harmony-font-size-title-l",
   "family": "HarmonyHeiTi",
   "size": 30,
   "lineHeight": 40,
   "weight": 700
  },
  {
   "name": "title_m_bold",
   "token": "--harmony-font-size-title-m",
   "family": "HarmonyHeiTi",
   "size": 24,
   "lineHeight": 32,
   "weight": 700
  },
  {
   "name": "title_s_bold",
   "token": "--harmony-font-size-title-s",
   "family": "HarmonyHeiTi",
   "size": 20,
   "lineHeight": 27,
   "weight": 700
  },
  {
   "name": "subtitle_l_medium",
   "token": "--harmony-font-size-subtitle-l",
   "family": "HarmonyHeiTi",
   "size": 18,
   "lineHeight": 26,
   "weight": 500
  },
  {
   "name": "subtitle_m_medium",
   "token": "--harmony-font-size-subtitle-m",
   "family": "HarmonyHeiTi",
   "size": 16,
   "lineHeight": 23,
   "weight": 500
  },
  {
   "name": "subtitle_s_medium",
   "token": "--harmony-font-size-subtitle-s",
   "family": "HarmonyHeiTi",
   "size": 14,
   "lineHeight": 20,
   "weight": 500
  },
  {
   "name": "body_l_regular",
   "token": "--harmony-font-size-body-l",
   "family": "HarmonyHeiTi",
   "size": 16,
   "lineHeight": 24,
   "weight": 400
  },
  {
   "name": "body_m_regular",
   "token": "--harmony-font-size-body-m",
   "family": "HarmonyHeiTi",
   "size": 14,
   "lineHeight": 21,
   "weight": 400
  },
  {
   "name": "body_s_regular",
   "token": "--harmony-font-size-body-s",
   "family": "HarmonyHeiTi",
   "size": 12,
   "lineHeight": 18,
   "weight": 400
  },
  {
   "name": "caption_l_medium",
   "token": "--harmony-font-size-caption-l",
   "family": "HarmonyHeiTi",
   "size": 12,
   "lineHeight": 20,
   "weight": 500
  },
  {
   "name": "caption_m_medium",
   "token": "--harmony-font-size-caption-m",
   "family": "HarmonyHeiTi",
   "size": 10,
   "lineHeight": 17,
   "weight": 500
  },
  {
   "name": "caption_s_medium",
   "token": "--harmony-font-size-caption-s",
   "family": "HarmonyHeiTi",
   "size": 8,
   "lineHeight": 13,
   "weight": 500
  }
 ]
}
```

## 间距 {#spacing}

33 个基础间距 token，场景 token 通过 ref 引用基础值。

### 使用规则

- 所有 spacing（padding/margin/gap）取值必须在 allowedValues 内
- allowedValues 等价于：4 或 8 的倍数（4~128），例外 2
- token.value 必须与 allowedValues 一致；场景 token 通过 ref 引用 global token

```json design
{
 "title": "间距",
 "unit": "px",
 "tokens": [
  {
   "name": "space-0_5x",
   "value": 2,
   "desc": "0.5 倍基础间距（例外值）"
  },
  {
   "name": "space-base",
   "value": 4,
   "desc": "基础间距 4px"
  },
  {
   "name": "space-2x",
   "value": 8,
   "desc": "2 倍基础间距 8px"
  },
  {
   "name": "space-3x",
   "value": 12,
   "desc": "3 倍基础间距 12px"
  },
  {
   "name": "space-4x",
   "value": 16,
   "desc": "4 倍基础间距 16px"
  },
  {
   "name": "space-5x",
   "value": 20,
   "desc": "5 倍基础间距 20px"
  },
  {
   "name": "space-6x",
   "value": 24,
   "desc": "6 倍基础间距 24px"
  },
  {
   "name": "space-7x",
   "value": 28,
   "desc": "7 倍基础间距 28px"
  },
  {
   "name": "space-8x",
   "value": 32,
   "desc": "8 倍基础间距 32px"
  },
  {
   "name": "space-9x",
   "value": 36,
   "desc": "9 倍基础间距 36px"
  },
  {
   "name": "space-10x",
   "value": 40,
   "desc": "10 倍基础间距 40px"
  },
  {
   "name": "space-11x",
   "value": 44,
   "desc": "11 倍基础间距 44px"
  },
  {
   "name": "space-12x",
   "value": 48,
   "desc": "12 倍基础间距 48px"
  },
  {
   "name": "space-13x",
   "value": 52,
   "desc": "13 倍基础间距 52px"
  },
  {
   "name": "space-14x",
   "value": 56,
   "desc": "14 倍基础间距 56px"
  },
  {
   "name": "space-15x",
   "value": 60,
   "desc": "15 倍基础间距 60px"
  },
  {
   "name": "space-16x",
   "value": 64,
   "desc": "16 倍基础间距 64px"
  },
  {
   "name": "space-17x",
   "value": 68,
   "desc": "17 倍基础间距 68px"
  },
  {
   "name": "space-18x",
   "value": 72,
   "desc": "18 倍基础间距 72px"
  },
  {
   "name": "space-19x",
   "value": 76,
   "desc": "19 倍基础间距 76px"
  },
  {
   "name": "space-20x",
   "value": 80,
   "desc": "20 倍基础间距 80px"
  },
  {
   "name": "space-21x",
   "value": 84,
   "desc": "21 倍基础间距 84px"
  },
  {
   "name": "space-22x",
   "value": 88,
   "desc": "22 倍基础间距 88px"
  },
  {
   "name": "space-23x",
   "value": 92,
   "desc": "23 倍基础间距 92px"
  },
  {
   "name": "space-24x",
   "value": 96,
   "desc": "24 倍基础间距 96px"
  },
  {
   "name": "space-25x",
   "value": 100,
   "desc": "25 倍基础间距 100px"
  },
  {
   "name": "space-26x",
   "value": 104,
   "desc": "26 倍基础间距 104px"
  },
  {
   "name": "space-27x",
   "value": 108,
   "desc": "27 倍基础间距 108px"
  },
  {
   "name": "space-28x",
   "value": 112,
   "desc": "28 倍基础间距 112px"
  },
  {
   "name": "space-29x",
   "value": 116,
   "desc": "29 倍基础间距 116px"
  },
  {
   "name": "space-30x",
   "value": 120,
   "desc": "30 倍基础间距 120px"
  },
  {
   "name": "space-31x",
   "value": 124,
   "desc": "31 倍基础间距 124px"
  },
  {
   "name": "space-32x",
   "value": 128,
   "desc": "32 倍基础间距 128px"
  }
 ],
 "scenes": [
  {
   "title": "elements",
   "tokens": [
    {
     "name": "elements-horizon-sm",
     "value": 4,
     "ref": "space-base",
     "desc": "elements-horizon-sm | 引用 space-base | 4px"
    },
    {
     "name": "elements-horizon-base",
     "value": 8,
     "ref": "space-2x",
     "desc": "elements-horizon-base | 引用 space-2x | 8px"
    },
    {
     "name": "elements-horizon-md",
     "value": 12,
     "ref": "space-3x",
     "desc": "elements-horizon-md | 引用 space-3x | 12px"
    },
    {
     "name": "elements-horizon-lg",
     "value": 16,
     "ref": "space-4x",
     "desc": "elements-horizon-lg | 引用 space-4x | 16px"
    },
    {
     "name": "elements-horizon-xl",
     "value": 24,
     "ref": "space-6x",
     "desc": "elements-horizon-xl | 引用 space-6x | 24px"
    },
    {
     "name": "elements-vertical-sm",
     "value": 4,
     "ref": "space-base",
     "desc": "elements-vertical-sm | 引用 space-base | 4px"
    },
    {
     "name": "elements-vertical-base",
     "value": 8,
     "ref": "space-2x",
     "desc": "elements-vertical-base | 引用 space-2x | 8px"
    },
    {
     "name": "elements-vertical-md",
     "value": 12,
     "ref": "space-3x",
     "desc": "elements-vertical-md | 引用 space-3x | 12px"
    },
    {
     "name": "elements-vertical-lg",
     "value": 16,
     "ref": "space-4x",
     "desc": "elements-vertical-lg | 引用 space-4x | 16px"
    },
    {
     "name": "elements-vertical-xl",
     "value": 24,
     "ref": "space-6x",
     "desc": "elements-vertical-xl | 引用 space-6x | 24px"
    },
    {
     "name": "elements-vertical-2xl",
     "value": 32,
     "ref": "space-8x",
     "desc": "elements-vertical-2xl | 引用 space-8x | 32px"
    }
   ]
  },
  {
   "title": "components",
   "tokens": [
    {
     "name": "components-horizon-sm",
     "value": 4,
     "ref": "space-base",
     "desc": "components-horizon-sm | 引用 space-base | 4px"
    },
    {
     "name": "components-horizon-base",
     "value": 8,
     "ref": "space-2x",
     "desc": "components-horizon-base | 引用 space-2x | 8px"
    },
    {
     "name": "components-horizon-md",
     "value": 12,
     "ref": "space-3x",
     "desc": "components-horizon-md | 引用 space-3x | 12px"
    },
    {
     "name": "components-horizon-lg",
     "value": 16,
     "ref": "space-4x",
     "desc": "components-horizon-lg | 引用 space-4x | 16px"
    },
    {
     "name": "components-vertical-sm",
     "value": 4,
     "ref": "space-base",
     "desc": "components-vertical-sm | 引用 space-base | 4px"
    },
    {
     "name": "components-vertical-base",
     "value": 8,
     "ref": "space-2x",
     "desc": "components-vertical-base | 引用 space-2x | 8px"
    },
    {
     "name": "components-vertical-md",
     "value": 12,
     "ref": "space-3x",
     "desc": "components-vertical-md | 引用 space-3x | 12px"
    },
    {
     "name": "components-vertical-lg",
     "value": 16,
     "ref": "space-4x",
     "desc": "components-vertical-lg | 引用 space-4x | 16px"
    }
   ]
  },
  {
   "title": "layout",
   "tokens": [
    {
     "name": "layout-horizon-sm",
     "value": 16,
     "ref": "space-4x",
     "desc": "layout-horizon-sm | 引用 space-4x | 16px"
    },
    {
     "name": "layout-horizon-base",
     "value": 24,
     "ref": "space-6x",
     "desc": "layout-horizon-base | 引用 space-6x | 24px"
    },
    {
     "name": "layout-horizon-md",
     "value": 32,
     "ref": "space-8x",
     "desc": "layout-horizon-md | 引用 space-8x | 32px"
    },
    {
     "name": "layout-horizon-lg",
     "value": 40,
     "ref": "space-10x",
     "desc": "layout-horizon-lg | 引用 space-10x | 40px"
    },
    {
     "name": "layout-horizon-xl",
     "value": 48,
     "ref": "space-12x",
     "desc": "layout-horizon-xl | 引用 space-12x | 48px"
    },
    {
     "name": "layout-vertical-sm",
     "value": 16,
     "ref": "space-4x",
     "desc": "layout-vertical-sm | 引用 space-4x | 16px"
    },
    {
     "name": "layout-vertical-base",
     "value": 24,
     "ref": "space-6x",
     "desc": "layout-vertical-base | 引用 space-6x | 24px"
    },
    {
     "name": "layout-vertical-md",
     "value": 32,
     "ref": "space-8x",
     "desc": "layout-vertical-md | 引用 space-8x | 32px"
    },
    {
     "name": "layout-vertical-lg",
     "value": 40,
     "ref": "space-10x",
     "desc": "layout-vertical-lg | 引用 space-10x | 40px"
    },
    {
     "name": "layout-vertical-xl",
     "value": 48,
     "ref": "space-12x",
     "desc": "layout-vertical-xl | 引用 space-12x | 48px"
    }
   ]
  }
 ]
}
```

## 圆角 {#radius}

10 个基础圆角 token，场景 token 通过 ref 引用基础值。

### 使用规则

- 所有圆角（border radius）取值必须在 allowedValues 内
- allowedValues 等价于：4 或 8 的倍数（4~96），例外 0 与 9999
- token.value 必须与 allowedValues 一致；场景 token 通过 ref 引用 global token

```json design
{
 "title": "圆角",
 "tokens": [
  {
   "name": "radius-none",
   "value": 0,
   "desc": "无圆角"
  },
  {
   "name": "radius-xs",
   "value": 4,
   "desc": "超小圆角"
  },
  {
   "name": "radius-base",
   "value": 4,
   "desc": "基础圆角"
  },
  {
   "name": "radius-md",
   "value": 8,
   "desc": "中等圆角"
  },
  {
   "name": "radius-lg",
   "value": 12,
   "desc": "大圆角"
  },
  {
   "name": "radius-xl",
   "value": 16,
   "desc": "超大圆角"
  },
  {
   "name": "radius-2xl",
   "value": 24,
   "desc": "2 倍超大圆角"
  },
  {
   "name": "radius-3xl",
   "value": 32,
   "desc": "3 倍超大圆角"
  },
  {
   "name": "radius-4xl",
   "value": 48,
   "desc": "4 倍超大圆角"
  },
  {
   "name": "radius-full",
   "value": 9999,
   "desc": "完全圆角（胶囊形）"
  }
 ],
 "scenes": [
  {
   "title": "scene",
   "tokens": [
    {
     "name": "radius-checkbox-base",
     "value": 4,
     "ref": "radius-xs",
     "desc": "复选框圆角"
    },
    {
     "name": "radius-search-base",
     "value": 4,
     "ref": "radius-base",
     "desc": "搜索框圆角"
    },
    {
     "name": "radius-dropdown-base",
     "value": 8,
     "ref": "radius-md",
     "desc": "下拉菜单圆角"
    },
    {
     "name": "radius-popup-base",
     "value": 12,
     "ref": "radius-lg",
     "desc": "弹出层圆角"
    },
    {
     "name": "radius-button-base",
     "value": 4,
     "ref": "radius-base",
     "desc": "按钮圆角"
    },
    {
     "name": "radius-button-full",
     "value": 9999,
     "ref": "radius-full",
     "desc": "按钮完全圆角"
    },
    {
     "name": "radius-card-sm",
     "value": 4,
     "ref": "radius-xs",
     "desc": "小卡片圆角"
    },
    {
     "name": "radius-card-base",
     "value": 8,
     "ref": "radius-md",
     "desc": "基础卡片圆角"
    },
    {
     "name": "radius-card-mg",
     "value": 12,
     "ref": "radius-lg",
     "desc": "中等卡片圆角"
    },
    {
     "name": "radius-card-lg",
     "value": 16,
     "ref": "radius-xl",
     "desc": "大卡片圆角"
    }
   ]
  }
 ]
}
```

## 阴影 {#shadow}

19 个投影 token。

```json design
{
 "title": "阴影",
 "tokens": [
  {
   "name": "defaultShadowL",
   "token": "--defaultShadowL",
   "value": "0px 20px 60px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 20px 60px 0px rgba(0, 0, 0, 0.2)"
  },
  {
   "name": "defaultShadowM",
   "token": "--defaultShadowM",
   "value": "0px 10px 30px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 10px 30px 0px rgba(0, 0, 0, 0.2)"
  },
  {
   "name": "defaultShadowS",
   "token": "--defaultShadowS",
   "value": "0px 0px 16px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 0px 16px 0px rgba(0, 0, 0, 0.2)"
  },
  {
   "name": "defaultShadowXS",
   "token": "--defaultShadowXS",
   "value": "0px 0px 4px 0px rgba(0, 0, 0, 0.102)",
   "dark": "0px 0px 4px 0px rgba(0, 0, 0, 0.1)"
  },
  {
   "name": "floatingShadowM",
   "token": "--floatingShadowM",
   "value": "0px 20px 60px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 20px 60px 0px rgba(0, 0, 0, 0.2)"
  },
  {
   "name": "floatingShadowS",
   "token": "--floatingShadowS",
   "value": "0px 10px 16px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 10px 16px 0px rgba(0, 0, 0, 0.2)"
  },
  {
   "name": "FABShadow",
   "token": "--FABShadow",
   "value": "0px 25px 30px -6px rgba(10, 89, 247, 0.302)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "FLOATINGshadow",
   "token": "--FLOATINGshadow",
   "value": "0px 8px 48px 0px rgba(0, 0, 0, 0.08)",
   "dark": "0px 8px 48px 0px rgba(0, 0, 0, 0.08)"
  },
  {
   "name": "Navigation_title",
   "token": "--Navigation_title",
   "value": "0px 4px 32px 0px rgba(241, 243, 245, 0.8)",
   "dark": "0px 4px 8px 0px rgba(0, 0, 0, 0.2)"
  },
  {
   "name": "OUTER_DEFAULT_LG",
   "token": "--OUTER_DEFAULT_LG",
   "value": "0px 20px 120px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "OUTER_DEFAULT_MD",
   "token": "--OUTER_DEFAULT_MD",
   "value": "0px 10px 60px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "OUTER_DEFAULT_SM",
   "token": "--OUTER_DEFAULT_SM",
   "value": "0px 10px 16px 0px rgba(0, 0, 0, 0.1)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "OUTER_DEFAULT_XS",
   "token": "--OUTER_DEFAULT_XS",
   "value": "0px 4px 8px 0px rgba(0, 0, 0, 0.1)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "OUTER_FLOATING_MD",
   "token": "--OUTER_FLOATING_MD",
   "value": "0px 20px 160px 0px rgba(0, 0, 0, 0.4)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "OUTER_FLOATING_SM",
   "token": "--OUTER_FLOATING_SM",
   "value": "0px 20px 160px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "Tips",
   "token": "--Tips",
   "value": "0px 0px 60px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "Toast",
   "token": "--Toast",
   "value": "0px 20px 120px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 10px 100px 0px rgba(0, 0, 0, 0.502)"
  },
  {
   "name": "edit-text",
   "token": "--edit-text",
   "value": "0px 0px 60px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  },
  {
   "name": "menu",
   "token": "--menu",
   "value": "0px 0px 60px 0px rgba(0, 0, 0, 0.2)",
   "dark": "0px 1px 3px 0px rgba(0, 0, 0, 0.0)"
  }
 ]
}
```

## 组件 {#components}

6 个已验证组件。有源码的直接渲染，无源码的由 AI 按规范生成参考实现。

```json design
{
 "title": "组件",
 "items": [
  {
   "id": "chipstab",
   "name": "chipstab",
   "desc": "已完成组件级还原验证",
   "score": 80,
   "props": [
    "material",
    "scenario",
    "state"
   ],
   "variants": [
    {
     "props": {
      "state": "activated",
      "material": "材质-弱 / 材质-强 / 材质-标准 / 材质-降档",
      "scenario": "default"
     },
     "image": "assets/components/chipstab/chipstab-state=activated_material=_-_scenario=default-default.png"
    },
    {
     "props": {
      "state": "activated",
      "material": "默认",
      "scenario": "default"
     },
     "image": "assets/components/chipstab/chipstab-state=activated_material=_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "20px"
      },
      "title": {
       "color": "rgb(255, 255, 255)",
       "font-size": "14px",
       "font-weight": "500"
      },
      "num": {
       "color": "rgba(255, 255, 255, 0.4)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "state": "enable",
      "material": "材质-弱 / 材质-强 / 材质-标准 / 材质-降档",
      "scenario": "default"
     },
     "image": "assets/components/chipstab/chipstab-state=enable_material=_-_scenario=default-default.png"
    },
    {
     "props": {
      "state": "enable",
      "material": "默认",
      "scenario": "default"
     },
     "image": "assets/components/chipstab/chipstab-state=enable_material=_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "title": {
       "color": "rgba(0, 0, 0, 0.6)",
       "font-size": "14px",
       "font-weight": "400"
      },
      "num": {
       "color": "rgba(0, 0, 0, 0.4)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    }
   ],
   "interaction": {
    "stateAxis": null,
    "states": {},
    "toggleAxis": "state"
   },
   "source": {
    "status": "generated",
    "expected": [
     "src/components/ChipsTab/chips-tab.tsx",
     "src/components/ChipsTab/chips-tab.css",
     "src/components/HMSymbolIcon/hmsymbol-icon.tsx",
     "src/components/HMSymbolIcon/hmsymbol-icon.constants.ts"
    ],
    "files": [
     {
      "path": "generated/chipstab.html",
      "lang": "html",
      "code": "<style>.ct{position:relative;overflow:hidden}.ct::before{content:\"\";position:absolute;inset:0;border-radius:inherit;background:transparent;transition:background .12s;pointer-events:none}.ct:not([data-force]):hover::before,.ct[data-force=hover]::before{background:rgba(0,0,0,.05)}.ct:not([data-force]):active::before,.ct[data-force=pressed]::before{background:rgba(0,0,0,.1)}.ct:focus-visible,.ct[data-force=focus]{outline:none;box-shadow:0 0 0 2px #fff,0 0 0 4px #0A59F7}.ct[data-force=disabled],.ct:disabled{opacity:.4;cursor:not-allowed}.ct[data-force]{pointer-events:none}\n.ct{height:36px;padding:0 16px;border-radius:20px;border:0;cursor:pointer;display:inline-flex;align-items:center;gap:6px;font-family:HarmonyHeiTi,\"HarmonyOS Sans SC\",sans-serif;background:rgba(0,0,0,.047)}\n.ct b{font-size:14px;font-weight:400;color:rgba(0,0,0,.6)}.ct em{font-style:normal;font-size:12px;color:rgba(0,0,0,.4)}.ct s{text-decoration:none;font-size:14px;color:rgba(0,0,0,.6)}\n.ct[data-state=activated]{background:#0A59F7}.ct[data-state=activated] b{color:#fff;font-weight:500}.ct[data-state=activated] em{color:rgba(255,255,255,.4)}.ct[data-state=activated] s{color:#fff}\n.ct:not([data-material=\"默认\"]){backdrop-filter:blur(20px)}\n</style>\n<div class=\"g own\"><button class=\"ct\" data-c><s>♥</s><b>Title</b><em>999</em></button></div>\n"
     }
    ]
   }
  },
  {
   "id": "radio",
   "name": "radio",
   "desc": "已完成组件级还原验证",
   "score": 81.67,
   "props": [
    "scenario",
    "selected",
    "state"
   ],
   "variants": [
    {
     "props": {
      "selected": "OFF",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/radio/radio-selected=OFF_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "12px"
      },
      "outer": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/radio/radio-selected=OFF_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "12px"
      },
      "outer": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/radio/radio-selected=OFF_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "12px"
      },
      "outer": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/radio/radio-selected=OFF_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "12px"
      },
      "outer": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      },
      "hover-overlay": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "12px"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/radio/radio-selected=ON_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "border-top-left-radius": "12px"
      },
      "outer": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "dot": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/radio/radio-selected=ON_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "border-top-left-radius": "12px"
      },
      "outer": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "dot": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/radio/radio-selected=ON_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "12px"
      },
      "outer": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "dot": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/radio/radio-selected=ON_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "border-top-left-radius": "12px"
      },
      "outer": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "dot": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      },
      "hover-overlay": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "12px"
      }
     }
    }
   ],
   "interaction": {
    "stateAxis": "state",
    "states": {
     "rest": "Enabled",
     "hover": "Hover",
     "focus": "Focus",
     "disabled": "Disabled"
    },
    "toggleAxis": "selected"
   },
   "source": {
    "status": "generated",
    "expected": [
     "src/components/RadioPhone/RadioPhone.tsx",
     "src/components/RadioPhone/radio-phone.css"
    ],
    "files": [
     {
      "path": "generated/radio.html",
      "lang": "html",
      "code": "<style>.hr{position:relative;overflow:hidden}.hr::before{content:\"\";position:absolute;inset:0;border-radius:inherit;background:transparent;transition:background .12s;pointer-events:none}.hr:not([data-force]):hover::before,.hr[data-force=hover]::before{background:rgba(0,0,0,.05)}.hr:not([data-force]):active::before,.hr[data-force=pressed]::before{background:rgba(0,0,0,.1)}.hr:focus-visible,.hr[data-force=focus]{outline:none;box-shadow:0 0 0 2px #fff,0 0 0 4px #0A59F7}.hr[data-force=disabled],.hr:disabled{opacity:.4;cursor:not-allowed}.hr[data-force]{pointer-events:none}\n.hr{width:24px;height:24px;border-radius:12px;border:0;padding:0;background:none;cursor:pointer;display:inline-flex;align-items:center;justify-content:center}\n.hr i{width:20px;height:20px;border-radius:10px;box-sizing:border-box;border:1px solid rgba(0,0,0,.4);background:rgba(255,255,255,.201);display:flex;align-items:center;justify-content:center}\n.hr[data-selected=on] i{background:#0A59F7;border:0}.hr[data-selected=on] i::after{content:\"\";width:8px;height:8px;border-radius:50%;background:#fff}\n</style>\n<div class=\"g own\"><button class=\"hr\" data-c><i></i></button></div>\n"
     }
    ]
   }
  },
  {
   "id": "switchphone",
   "name": "switchphone",
   "desc": "已完成组件级还原验证",
   "score": 76.84,
   "props": [
    "scenario",
    "selected",
    "state"
   ],
   "variants": [
    {
     "props": {
      "selected": "OFF",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=OFF_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.098)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "border-top-left-radius": "9px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=OFF_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.098)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "border-top-left-radius": "9px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=OFF_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.098)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "border-top-left-radius": "9px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=OFF_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.098)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "border-top-left-radius": "9px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=OFF_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.098)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "border-top-left-radius": "9px"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=ON_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-left-radius": "8px"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=ON_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-left-radius": "8px"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=ON_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-left-radius": "8px"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=ON_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-left-radius": "8px"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/switchphone/switchphone-selected=ON_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "12px"
      },
      "thumb": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-left-radius": "8px"
      }
     }
    }
   ],
   "interaction": {
    "stateAxis": "state",
    "states": {
     "rest": "Enabled",
     "hover": "Hover",
     "pressed": "Pressed",
     "focus": "Focus",
     "disabled": "Disabled"
    },
    "toggleAxis": "selected"
   },
   "source": {
    "status": "generated",
    "expected": [
     "src/components/SwitchPhone/SwitchPhone.tsx",
     "src/components/SwitchPhone/switch-phone.css"
    ],
    "files": [
     {
      "path": "generated/switchphone.html",
      "lang": "html",
      "code": "<style>.hs{position:relative;overflow:hidden}.hs::before{content:\"\";position:absolute;inset:0;border-radius:inherit;background:transparent;transition:background .12s;pointer-events:none}.hs:not([data-force]):hover::before,.hs[data-force=hover]::before{background:rgba(0,0,0,.05)}.hs:not([data-force]):active::before,.hs[data-force=pressed]::before{background:rgba(0,0,0,.1)}.hs:focus-visible,.hs[data-force=focus]{outline:none;box-shadow:0 0 0 2px #fff,0 0 0 4px #0A59F7}.hs[data-force=disabled],.hs:disabled{opacity:.4;cursor:not-allowed}.hs[data-force]{pointer-events:none}\n.hs{width:36px;height:20px;border-radius:12px;background:rgba(0,0,0,.098);border:0;padding:0;cursor:pointer;transition:background .2s}\n.hs i{position:absolute;left:1px;top:1px;width:18px;height:18px;border-radius:9px;background:#fff;box-sizing:border-box;border:1px solid rgba(0,0,0,.047);transition:left .2s}\n.hs[data-selected=on]{background:#0A59F7}.hs[data-selected=on] i{left:18px;width:16px;height:16px;top:2px;border:0;border-radius:8px}\n</style>\n<div class=\"g own\"><button class=\"hs\" data-c><i></i></button></div>\n"
     }
    ]
   }
  },
  {
   "id": "checkbox",
   "name": "checkbox",
   "desc": "已完成组件级还原验证",
   "score": 82.8,
   "props": [
    "scenario",
    "selected",
    "state"
   ],
   "variants": [
    {
     "props": {
      "selected": "OFF",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=OFF_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=OFF_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=OFF_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=OFF_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      },
      "hover-overlay": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "12px"
      }
     }
    },
    {
     "props": {
      "selected": "OFF",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=OFF_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgba(255, 255, 255, 0.201)",
       "border-top-color": "rgba(0, 0, 0, 0.4)",
       "border-top-width": "1px",
       "border-top-left-radius": "10px"
      },
      "pressed-overlay": {
       "background-color": "rgba(0, 0, 0, 0.098)",
       "border-top-left-radius": "12px"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=ON_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "checkmark": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=ON_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "checkmark": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=ON_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "checkmark": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=ON_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "checkmark": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      },
      "hover-overlay": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "12px"
      }
     }
    },
    {
     "props": {
      "selected": "ON",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/checkbox/checkbox-selected=ON_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "12px"
      },
      "box": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "10px"
      },
      "checkmark": {
       "background-color": "rgb(255, 255, 255)",
       "border-top-color": "rgba(0, 0, 0, 0.047)",
       "border-top-width": "1px",
       "box-shadow": "rgba(0, 0, 0, 0.102)"
      },
      "pressed-overlay": {
       "background-color": "rgba(0, 0, 0, 0.098)",
       "border-top-left-radius": "12px"
      }
     }
    }
   ],
   "interaction": {
    "stateAxis": "state",
    "states": {
     "rest": "Enabled",
     "hover": "Hover",
     "pressed": "Pressed",
     "focus": "Focus",
     "disabled": "Disabled"
    },
    "toggleAxis": "selected"
   },
   "source": {
    "status": "generated",
    "expected": [
     "src/components/CheckBoxPhone/CheckBoxPhone.tsx",
     "src/components/CheckBoxPhone/check-box-phone.css"
    ],
    "files": [
     {
      "path": "generated/checkbox.html",
      "lang": "html",
      "code": "<style>.hc{position:relative;overflow:hidden}.hc::before{content:\"\";position:absolute;inset:0;border-radius:inherit;background:transparent;transition:background .12s;pointer-events:none}.hc:not([data-force]):hover::before,.hc[data-force=hover]::before{background:rgba(0,0,0,.05)}.hc:not([data-force]):active::before,.hc[data-force=pressed]::before{background:rgba(0,0,0,.1)}.hc:focus-visible,.hc[data-force=focus]{outline:none;box-shadow:0 0 0 2px #fff,0 0 0 4px #0A59F7}.hc[data-force=disabled],.hc:disabled{opacity:.4;cursor:not-allowed}.hc[data-force]{pointer-events:none}\n.hc{width:24px;height:24px;border-radius:12px;border:0;padding:0;background:none;cursor:pointer;display:inline-flex;align-items:center;justify-content:center}\n.hc i{width:20px;height:20px;border-radius:10px;box-sizing:border-box;border:1px solid rgba(0,0,0,.4);background:rgba(255,255,255,.201);display:flex;align-items:center;justify-content:center}\n.hc[data-selected=on] i{background:#0A59F7;border:0}.hc[data-selected=on] i::after{content:\"\";width:8px;height:4px;border-left:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(-45deg) translate(1px,-1px)}\n</style>\n<div class=\"g own\"><button class=\"hc\" data-c><i></i></button></div>\n"
     }
    ]
   }
  },
  {
   "id": "button",
   "name": "button",
   "desc": "已完成组件级还原验证",
   "score": 90,
   "props": [
    "scenario",
    "size",
    "state",
    "type"
   ],
   "variants": [
    {
     "props": {
      "size": "Medium",
      "type": "Emphasized",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Emphasized_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Emphasized",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Emphasized_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Emphasized",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Emphasized_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Emphasized",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Emphasized_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Emphasized",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Emphasized_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Emphasized",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Emphasized_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Normal",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Normal_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Normal",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Normal_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Normal",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Normal_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Normal",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Normal_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Normal",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Normal_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Normal",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Normal_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Selected",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Selected_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Selected",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Selected_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Selected",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Selected_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Selected",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Selected_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Selected",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Selected_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Selected",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Selected_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Text",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Text_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Text",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Text_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Text",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Text_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Text",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Text_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Text",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Text_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Text",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Text_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Unselected",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Unselected_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Unselected",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Unselected_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Unselected",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Unselected_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Unselected",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Unselected_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Unselected",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Unselected_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Unselected",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Unselected_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "12px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Warning",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Warning_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Warning",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Warning_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Warning",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Warning_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Warning",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Warning_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Warning",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Warning_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "type": "Warning",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Medium_type=Warning_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Emphasized",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Emphasized_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Emphasized",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Emphasized_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Emphasized",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Emphasized_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Emphasized",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Emphasized_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Emphasized",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Emphasized_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Emphasized",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Emphasized_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgb(10, 89, 247)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(255, 255, 255)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Normal",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Normal_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Normal",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Normal_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Normal",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Normal_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Normal",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Normal_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Normal",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Normal_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Normal",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Normal_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Selected",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Selected_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Selected",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Selected_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Selected",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Selected_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Selected",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Selected_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Selected",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Selected_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Selected",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Selected_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(10, 89, 247, 0.2)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Text",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Text_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Text",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Text_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Text",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Text_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Text",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Text_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Text",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Text_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Text",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Text_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(10, 89, 247)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Unselected",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Unselected_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Unselected",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Unselected_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Unselected",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Unselected_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Unselected",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Unselected_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Unselected",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Unselected_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Unselected",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Unselected_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "400"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Warning",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Warning_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Warning",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Warning_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Warning",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Warning_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Warning",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Warning_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Warning",
      "state": "Loading",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Warning_state=Loading_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "type": "Warning",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/button/button-size=Small_type=Warning_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "14px"
      },
      "label": {
       "color": "rgb(232, 64, 38)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    }
   ],
   "interaction": {
    "stateAxis": "state",
    "states": {
     "rest": "Enabled",
     "hover": "Hover",
     "pressed": "Pressed",
     "focus": "Focus",
     "disabled": "Disabled"
    },
    "toggleAxis": null
   },
   "source": {
    "status": "generated",
    "expected": [
     "src/components/Button/button.tsx",
     "src/components/Button/button.css"
    ],
    "files": [
     {
      "path": "generated/button.html",
      "lang": "html",
      "code": "<style>.hb{position:relative;overflow:hidden}.hb::before{content:\"\";position:absolute;inset:0;border-radius:inherit;background:transparent;transition:background .12s;pointer-events:none}.hb:not([data-force]):hover::before,.hb[data-force=hover]::before{background:rgba(0,0,0,.05)}.hb:not([data-force]):active::before,.hb[data-force=pressed]::before{background:rgba(0,0,0,.1)}.hb:focus-visible,.hb[data-force=focus]{outline:none;box-shadow:0 0 0 2px #fff,0 0 0 4px #0A59F7}.hb[data-force=disabled],.hb:disabled{opacity:.4;cursor:not-allowed}.hb[data-force]{pointer-events:none}\n.hb{border:0;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:6px;height:40px;min-width:120px;padding:0 16px;border-radius:20px;font:500 16px HarmonyHeiTi,\"HarmonyOS Sans SC\",sans-serif;background:#0A59F7;color:#fff}\n.hb[data-size=small]{height:28px;min-width:72px;border-radius:14px;font-size:14px;padding:0 12px}\n.hb[data-type=normal]{background:rgba(0,0,0,.047);color:#0A59F7}.hb[data-type=warning]{background:rgba(0,0,0,.047);color:#E84026}\n.hb[data-type=text]{background:transparent;color:#0A59F7}.hb[data-type=selected]{background:rgba(10,89,247,.2);color:rgba(0,0,0,.898);font-weight:400}\n.hb[data-type=unselected]{background:rgba(0,0,0,.047);color:rgba(0,0,0,.898);font-weight:400}\n.hb i{display:none;width:14px;height:14px;border:2px solid currentColor;border-right-color:transparent;border-radius:50%;animation:r 1s linear infinite}@keyframes r{to{transform:rotate(360deg)}}\n.hb[data-force=loading] i{display:inline-block}.hb[data-force=loading] span::after{content:\"中\"}\n</style>\n<div class=\"g own\"><button class=\"hb\" data-c><i></i><span>按钮</span></button></div>\n"
     }
    ]
   }
  },
  {
   "id": "selectphone",
   "name": "selectphone",
   "desc": "已完成组件级还原验证",
   "score": 97.69,
   "props": [
    "scenario",
    "size",
    "state"
   ],
   "variants": [
    {
     "props": {
      "size": "Medium",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Medium_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Medium_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Medium_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Medium_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Medium",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Medium_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "16px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "state": "Disabled",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Small_state=Disabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "state": "Enabled",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Small_state=Enabled_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "state": "Focus",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Small_state=Focus_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-color": "rgb(10, 89, 247)",
       "border-top-width": "2px",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "state": "Hover",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Small_state=Hover_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    },
    {
     "props": {
      "size": "Small",
      "state": "Pressed",
      "scenario": "default"
     },
     "image": "assets/components/selectphone/select-phone-size=Small_state=Pressed_scenario=default-default.png",
     "styles": {
      "root": {
       "background-color": "rgba(0, 0, 0, 0.047)",
       "border-top-left-radius": "20px"
      },
      "label": {
       "color": "rgba(0, 0, 0, 0.898)",
       "font-size": "14px",
       "font-weight": "500"
      }
     }
    }
   ],
   "interaction": {
    "stateAxis": "state",
    "states": {
     "rest": "Enabled",
     "hover": "Hover",
     "pressed": "Pressed",
     "focus": "Focus",
     "disabled": "Disabled"
    },
    "toggleAxis": null
   },
   "source": {
    "status": "generated",
    "expected": [
     "src/components/SelectPhone/SelectPhone.tsx",
     "src/components/SelectPhone/select-phone.css"
    ],
    "files": [
     {
      "path": "generated/selectphone.html",
      "lang": "html",
      "code": "<style>.sp{position:relative;overflow:hidden}.sp::before{content:\"\";position:absolute;inset:0;border-radius:inherit;background:transparent;transition:background .12s;pointer-events:none}.sp:not([data-force]):hover::before,.sp[data-force=hover]::before{background:rgba(0,0,0,.05)}.sp:not([data-force]):active::before,.sp[data-force=pressed]::before{background:rgba(0,0,0,.1)}.sp:focus-visible,.sp[data-force=focus]{outline:none;box-shadow:0 0 0 2px #fff,0 0 0 4px #0A59F7}.sp[data-force=disabled],.sp:disabled{opacity:.4;cursor:not-allowed}.sp[data-force]{pointer-events:none}\n.sp{height:40px;padding:0 16px;border-radius:20px;border:0;cursor:pointer;display:inline-flex;align-items:center;gap:8px;background:rgba(0,0,0,.047);color:rgba(0,0,0,.898);font:500 16px HarmonyHeiTi,\"HarmonyOS Sans SC\",sans-serif}\n.sp::after{content:\"\";border:5px solid transparent;border-top:6px solid currentColor;margin-top:5px}\n.sp[data-size=small]{height:28px;font-size:14px;padding:0 12px}\n</style>\n<div class=\"g own\"><button class=\"sp\" data-c>Select</button></div>\n"
     }
    ]
   }
  }
 ]
}
```

## 资产 {#assets}

444 个 SVG 图标，按目录分组。

```json design
{
 "title": "图标",
 "categories": [
  {
   "title": "图标",
   "subs": [
    {
     "title": "2.5D",
     "items": [
      {
       "name": "ic_public_add_member2",
       "type": "SVG",
       "size": 14716,
       "src": "assets/icons/2.5D/ic_public_add_member2.svg"
      },
      {
       "name": "ic_public_alarmlight2",
       "type": "SVG",
       "size": 14408,
       "src": "assets/icons/2.5D/ic_public_alarmlight2.svg"
      },
      {
       "name": "ic_public_broom2",
       "type": "SVG",
       "size": 7051,
       "src": "assets/icons/2.5D/ic_public_broom2.svg"
      },
      {
       "name": "ic_public_business1",
       "type": "SVG",
       "size": 11559,
       "src": "assets/icons/2.5D/ic_public_business1.svg"
      },
      {
       "name": "ic_public_camera2",
       "type": "SVG",
       "size": 16137,
       "src": "assets/icons/2.5D/ic_public_camera2.svg"
      },
      {
       "name": "ic_public_camera_dome2",
       "type": "SVG",
       "size": 8620,
       "src": "assets/icons/2.5D/ic_public_camera_dome2.svg"
      },
      {
       "name": "ic_public_clock_globe2",
       "type": "SVG",
       "size": 45432,
       "src": "assets/icons/2.5D/ic_public_clock_globe2.svg"
      },
      {
       "name": "ic_public_config_guide1",
       "type": "SVG",
       "size": 14541,
       "src": "assets/icons/2.5D/ic_public_config_guide1.svg"
      },
      {
       "name": "ic_public_mappin_on_map2",
       "type": "SVG",
       "size": 11496,
       "src": "assets/icons/2.5D/ic_public_mappin_on_map2.svg"
      },
      {
       "name": "ic_public_navigate_application_view1",
       "type": "SVG",
       "size": 10766,
       "src": "assets/icons/2.5D/ic_public_navigate_application_view1.svg"
      },
      {
       "name": "ic_public_phone_gear2",
       "type": "SVG",
       "size": 10021,
       "src": "assets/icons/2.5D/ic_public_phone_gear2.svg"
      },
      {
       "name": "ic_public_redcross2",
       "type": "SVG",
       "size": 11445,
       "src": "assets/icons/2.5D/ic_public_redcross2.svg"
      },
      {
       "name": "ic_public_safety_management1",
       "type": "SVG",
       "size": 11174,
       "src": "assets/icons/2.5D/ic_public_safety_management1.svg"
      },
      {
       "name": "ic_public_screen_wifi2",
       "type": "SVG",
       "size": 11681,
       "src": "assets/icons/2.5D/ic_public_screen_wifi2.svg"
      },
      {
       "name": "ic_public_setting_cloudsop",
       "type": "SVG",
       "size": 12257,
       "src": "assets/icons/2.5D/ic_public_setting_cloudsop.svg"
      },
      {
       "name": "ic_public_setting_vds1",
       "type": "SVG",
       "size": 10754,
       "src": "assets/icons/2.5D/ic_public_setting_vds1.svg"
      },
      {
       "name": "ic_public_stop_repair1",
       "type": "SVG",
       "size": 12264,
       "src": "assets/icons/2.5D/ic_public_stop_repair1.svg"
      },
      {
       "name": "ic_public_suitcase_magnifyingglass1",
       "type": "SVG",
       "size": 19472,
       "src": "assets/icons/2.5D/ic_public_suitcase_magnifyingglass1.svg"
      },
      {
       "name": "ic_public_vtep",
       "type": "SVG",
       "size": 9133,
       "src": "assets/icons/2.5D/ic_public_vtep.svg"
      }
     ]
    },
    {
     "title": "basic",
     "items": [
      {
       "name": "ic_bpit_grade",
       "type": "SVG",
       "size": 16153,
       "src": "assets/icons/basic/ic_bpit_grade.svg"
      },
      {
       "name": "ic_digital_bokeh",
       "type": "SVG",
       "size": 47417,
       "src": "assets/icons/basic/ic_digital_bokeh.svg"
      },
      {
       "name": "ic_digital_canceling_a_meeting",
       "type": "SVG",
       "size": 12111,
       "src": "assets/icons/basic/ic_digital_canceling_a_meeting.svg"
      },
      {
       "name": "ic_digital_conference_control",
       "type": "SVG",
       "size": 35337,
       "src": "assets/icons/basic/ic_digital_conference_control.svg"
      },
      {
       "name": "ic_digital_conference_room",
       "type": "SVG",
       "size": 41077,
       "src": "assets/icons/basic/ic_digital_conference_room.svg"
      },
      {
       "name": "ic_digital_id",
       "type": "SVG",
       "size": 14167,
       "src": "assets/icons/basic/ic_digital_id.svg"
      },
      {
       "name": "ic_digital_in_picture",
       "type": "SVG",
       "size": 25483,
       "src": "assets/icons/basic/ic_digital_in_picture.svg"
      },
      {
       "name": "ic_digital_maximize",
       "type": "SVG",
       "size": 9286,
       "src": "assets/icons/basic/ic_digital_maximize.svg"
      },
      {
       "name": "ic_digital_office_business",
       "type": "SVG",
       "size": 10544,
       "src": "assets/icons/basic/ic_digital_office_business.svg"
      },
      {
       "name": "ic_digital_office_call_log",
       "type": "SVG",
       "size": 16033,
       "src": "assets/icons/basic/ic_digital_office_call_log.svg"
      },
      {
       "name": "ic_digital_office_call_record",
       "type": "SVG",
       "size": 19504,
       "src": "assets/icons/basic/ic_digital_office_call_record.svg"
      },
      {
       "name": "ic_digital_office_circulate",
       "type": "SVG",
       "size": 21356,
       "src": "assets/icons/basic/ic_digital_office_circulate.svg"
      },
      {
       "name": "ic_digital_office_cloud_record_on",
       "type": "SVG",
       "size": 15121,
       "src": "assets/icons/basic/ic_digital_office_cloud_record_on.svg"
      },
      {
       "name": "ic_digital_office_cloud_record_pause",
       "type": "SVG",
       "size": 25013,
       "src": "assets/icons/basic/ic_digital_office_cloud_record_pause.svg"
      },
      {
       "name": "ic_digital_office_cloud_recording_enable",
       "type": "SVG",
       "size": 20988,
       "src": "assets/icons/basic/ic_digital_office_cloud_recording_enable.svg"
      },
      {
       "name": "ic_digital_office_cloud_space",
       "type": "SVG",
       "size": 30521,
       "src": "assets/icons/basic/ic_digital_office_cloud_space.svg"
      },
      {
       "name": "ic_digital_office_emoticon_disable",
       "type": "SVG",
       "size": 57858,
       "src": "assets/icons/basic/ic_digital_office_emoticon_disable.svg"
      },
      {
       "name": "ic_digital_office_enterprise",
       "type": "SVG",
       "size": 28527,
       "src": "assets/icons/basic/ic_digital_office_enterprise.svg"
      },
      {
       "name": "ic_digital_office_flip_camera",
       "type": "SVG",
       "size": 55235,
       "src": "assets/icons/basic/ic_digital_office_flip_camera.svg"
      },
      {
       "name": "ic_digital_office_group",
       "type": "SVG",
       "size": 6256,
       "src": "assets/icons/basic/ic_digital_office_group.svg"
      },
      {
       "name": "ic_digital_office_hang_up",
       "type": "SVG",
       "size": 10417,
       "src": "assets/icons/basic/ic_digital_office_hang_up.svg"
      },
      {
       "name": "ic_digital_office_hardware_device",
       "type": "SVG",
       "size": 19608,
       "src": "assets/icons/basic/ic_digital_office_hardware_device.svg"
      },
      {
       "name": "ic_digital_office_industry",
       "type": "SVG",
       "size": 30169,
       "src": "assets/icons/basic/ic_digital_office_industry.svg"
      },
      {
       "name": "ic_digital_office_initiating_a_conference",
       "type": "SVG",
       "size": 27781,
       "src": "assets/icons/basic/ic_digital_office_initiating_a_conference.svg"
      },
      {
       "name": "ic_digital_office_joining_a_conference",
       "type": "SVG",
       "size": 15542,
       "src": "assets/icons/basic/ic_digital_office_joining_a_conference.svg"
      },
      {
       "name": "ic_digital_office_landscape",
       "type": "SVG",
       "size": 77871,
       "src": "assets/icons/basic/ic_digital_office_landscape.svg"
      },
      {
       "name": "ic_digital_office_lay_flat",
       "type": "SVG",
       "size": 21980,
       "src": "assets/icons/basic/ic_digital_office_lay_flat.svg"
      },
      {
       "name": "ic_digital_office_loudspeaker_close",
       "type": "SVG",
       "size": 13601,
       "src": "assets/icons/basic/ic_digital_office_loudspeaker_close.svg"
      },
      {
       "name": "ic_digital_office_mouse",
       "type": "SVG",
       "size": 15313,
       "src": "assets/icons/basic/ic_digital_office_mouse.svg"
      },
      {
       "name": "ic_digital_office_no_chat",
       "type": "SVG",
       "size": 13833,
       "src": "assets/icons/basic/ic_digital_office_no_chat.svg"
      },
      {
       "name": "ic_digital_office_prohibit_share",
       "type": "SVG",
       "size": 48251,
       "src": "assets/icons/basic/ic_digital_office_prohibit_share.svg"
      },
      {
       "name": "ic_digital_office_record_circle_disable",
       "type": "SVG",
       "size": 47517,
       "src": "assets/icons/basic/ic_digital_office_record_circle_disable.svg"
      },
      {
       "name": "ic_digital_office_remote_control",
       "type": "SVG",
       "size": 91192,
       "src": "assets/icons/basic/ic_digital_office_remote_control.svg"
      },
      {
       "name": "ic_digital_office_remotely_control",
       "type": "SVG",
       "size": 24946,
       "src": "assets/icons/basic/ic_digital_office_remotely_control.svg"
      },
      {
       "name": "ic_digital_office_rotate",
       "type": "SVG",
       "size": 22174,
       "src": "assets/icons/basic/ic_digital_office_rotate.svg"
      },
      {
       "name": "ic_digital_office_service_center",
       "type": "SVG",
       "size": 20592,
       "src": "assets/icons/basic/ic_digital_office_service_center.svg"
      },
      {
       "name": "ic_digital_office_share_waite",
       "type": "SVG",
       "size": 45722,
       "src": "assets/icons/basic/ic_digital_office_share_waite.svg"
      },
      {
       "name": "ic_digital_office_signal",
       "type": "SVG",
       "size": 14412,
       "src": "assets/icons/basic/ic_digital_office_signal.svg"
      },
      {
       "name": "ic_digital_office_sort_by_name",
       "type": "SVG",
       "size": 32412,
       "src": "assets/icons/basic/ic_digital_office_sort_by_name.svg"
      },
      {
       "name": "ic_digital_office_spokesmen",
       "type": "SVG",
       "size": 34843,
       "src": "assets/icons/basic/ic_digital_office_spokesmen.svg"
      },
      {
       "name": "ic_digital_office_turn_off_video",
       "type": "SVG",
       "size": 21316,
       "src": "assets/icons/basic/ic_digital_office_turn_off_video.svg"
      },
      {
       "name": "ic_digital_office_unmute",
       "type": "SVG",
       "size": 19454,
       "src": "assets/icons/basic/ic_digital_office_unmute.svg"
      },
      {
       "name": "ic_digital_office_video_call",
       "type": "SVG",
       "size": 12776,
       "src": "assets/icons/basic/ic_digital_office_video_call.svg"
      },
      {
       "name": "ic_digital_office_view_broadcast",
       "type": "SVG",
       "size": 20291,
       "src": "assets/icons/basic/ic_digital_office_view_broadcast.svg"
      },
      {
       "name": "ic_digital_office_vip",
       "type": "SVG",
       "size": 21276,
       "src": "assets/icons/basic/ic_digital_office_vip.svg"
      },
      {
       "name": "ic_digital_office_virtual_background",
       "type": "SVG",
       "size": 70073,
       "src": "assets/icons/basic/ic_digital_office_virtual_background.svg"
      },
      {
       "name": "ic_digital_office_waite",
       "type": "SVG",
       "size": 44047,
       "src": "assets/icons/basic/ic_digital_office_waite.svg"
      },
      {
       "name": "ic_digital_projection",
       "type": "SVG",
       "size": 11509,
       "src": "assets/icons/basic/ic_digital_projection.svg"
      },
      {
       "name": "ic_digital_reshare",
       "type": "SVG",
       "size": 30042,
       "src": "assets/icons/basic/ic_digital_reshare.svg"
      },
      {
       "name": "ic_digital_schedule_conference",
       "type": "SVG",
       "size": 11106,
       "src": "assets/icons/basic/ic_digital_schedule_conference.svg"
      },
      {
       "name": "ic_digital_select_black",
       "type": "SVG",
       "size": 25364,
       "src": "assets/icons/basic/ic_digital_select_black.svg"
      },
      {
       "name": "ic_digital_share_square",
       "type": "SVG",
       "size": 18334,
       "src": "assets/icons/basic/ic_digital_share_square.svg"
      },
      {
       "name": "ic_digital_standalone_window",
       "type": "SVG",
       "size": 22348,
       "src": "assets/icons/basic/ic_digital_standalone_window.svg"
      },
      {
       "name": "ic_digital_verification_code",
       "type": "SVG",
       "size": 21966,
       "src": "assets/icons/basic/ic_digital_verification_code.svg"
      },
      {
       "name": "ic_ict_a_double_solid_line",
       "type": "SVG",
       "size": 18544,
       "src": "assets/icons/basic/ic_ict_a_double_solid_line.svg"
      },
      {
       "name": "ic_ict_allow_line_breaks_within",
       "type": "SVG",
       "size": 21958,
       "src": "assets/icons/basic/ic_ict_allow_line_breaks_within.svg"
      },
      {
       "name": "ic_ict_bottom_border",
       "type": "SVG",
       "size": 24093,
       "src": "assets/icons/basic/ic_ict_bottom_border.svg"
      },
      {
       "name": "ic_ict_breaks_only_at_hyphens",
       "type": "SVG",
       "size": 21276,
       "src": "assets/icons/basic/ic_ict_breaks_only_at_hyphens.svg"
      },
      {
       "name": "ic_ict_cell_column",
       "type": "SVG",
       "size": 8163,
       "src": "assets/icons/basic/ic_ict_cell_column.svg"
      },
      {
       "name": "ic_ict_curve_chart",
       "type": "SVG",
       "size": 18611,
       "src": "assets/icons/basic/ic_ict_curve_chart.svg"
      },
      {
       "name": "ic_ict_default_line_break",
       "type": "SVG",
       "size": 17550,
       "src": "assets/icons/basic/ic_ict_default_line_break.svg"
      },
      {
       "name": "ic_ict_display_as_a_block_level_table",
       "type": "SVG",
       "size": 8779,
       "src": "assets/icons/basic/ic_ict_display_as_a_block_level_table.svg"
      },
      {
       "name": "ic_ict_faster_in_the_middle_slow_at_both_ends",
       "type": "SVG",
       "size": 13800,
       "src": "assets/icons/basic/ic_ict_faster_in_the_middle_slow_at_both_ends.svg"
      },
      {
       "name": "ic_ict_inline_tables",
       "type": "SVG",
       "size": 15064,
       "src": "assets/icons/basic/ic_ict_inline_tables.svg"
      },
      {
       "name": "ic_ict_leave_blank",
       "type": "SVG",
       "size": 37708,
       "src": "assets/icons/basic/ic_ict_leave_blank.svg"
      },
      {
       "name": "ic_ict_left_border",
       "type": "SVG",
       "size": 17537,
       "src": "assets/icons/basic/ic_ict_left_border.svg"
      },
      {
       "name": "ic_ict_long_words_or_url_address_wraps",
       "type": "SVG",
       "size": 19515,
       "src": "assets/icons/basic/ic_ict_long_words_or_url_address_wraps.svg"
      },
      {
       "name": "ic_ict_no_line_breaks_until_br",
       "type": "SVG",
       "size": 41008,
       "src": "assets/icons/basic/ic_ict_no_line_breaks_until_br.svg"
      },
      {
       "name": "ic_ict_no_pointer_is_rendered",
       "type": "SVG",
       "size": 22338,
       "src": "assets/icons/basic/ic_ict_no_pointer_is_rendered.svg"
      },
      {
       "name": "ic_ict_office_brush",
       "type": "SVG",
       "size": 14959,
       "src": "assets/icons/basic/ic_ict_office_brush.svg"
      },
      {
       "name": "ic_ict_only_hyphenate_breaks_are_allowed",
       "type": "SVG",
       "size": 32245,
       "src": "assets/icons/basic/ic_ict_only_hyphenate_breaks_are_allowed.svg"
      },
      {
       "name": "ic_ict_right_border",
       "type": "SVG",
       "size": 17637,
       "src": "assets/icons/basic/ic_ict_right_border.svg"
      },
      {
       "name": "ic_ict_show_as_a_table_cell",
       "type": "SVG",
       "size": 9307,
       "src": "assets/icons/basic/ic_ict_show_as_a_table_cell.svg"
      },
      {
       "name": "ic_ict_show_as_a_table_row",
       "type": "SVG",
       "size": 5690,
       "src": "assets/icons/basic/ic_ict_show_as_a_table_row.svg"
      },
      {
       "name": "ic_ict_show_as_up_and_down_dots",
       "type": "SVG",
       "size": 19440,
       "src": "assets/icons/basic/ic_ict_show_as_up_and_down_dots.svg"
      },
      {
       "name": "ic_ict_similar_to_tbody",
       "type": "SVG",
       "size": 16461,
       "src": "assets/icons/basic/ic_ict_similar_to_tbody.svg"
      },
      {
       "name": "ic_ict_similar_to_tfoot",
       "type": "SVG",
       "size": 16054,
       "src": "assets/icons/basic/ic_ict_similar_to_tfoot.svg"
      },
      {
       "name": "ic_ict_similar_to_thead",
       "type": "SVG",
       "size": 17054,
       "src": "assets/icons/basic/ic_ict_similar_to_thead.svg"
      },
      {
       "name": "ic_ict_this_element_appears_as_a_list",
       "type": "SVG",
       "size": 9163,
       "src": "assets/icons/basic/ic_ict_this_element_appears_as_a_list.svg"
      },
      {
       "name": "ic_ict_top_border",
       "type": "SVG",
       "size": 15002,
       "src": "assets/icons/basic/ic_ict_top_border.svg"
      },
      {
       "name": "ic_nce_close_event",
       "type": "SVG",
       "size": 50034,
       "src": "assets/icons/basic/ic_nce_close_event.svg"
      },
      {
       "name": "ic_nce_fabric_global_resource_pool",
       "type": "SVG",
       "size": 19380,
       "src": "assets/icons/basic/ic_nce_fabric_global_resource_pool.svg"
      },
      {
       "name": "ic_nce_template_management",
       "type": "SVG",
       "size": 43581,
       "src": "assets/icons/basic/ic_nce_template_management.svg"
      },
      {
       "name": "ic_passing_tunnel",
       "type": "SVG",
       "size": 27645,
       "src": "assets/icons/basic/ic_passing_tunnel.svg"
      },
      {
       "name": "ic_public_add_member",
       "type": "SVG",
       "size": 13730,
       "src": "assets/icons/basic/ic_public_add_member.svg"
      },
      {
       "name": "ic_public_adjuvant_template",
       "type": "SVG",
       "size": 12451,
       "src": "assets/icons/basic/ic_public_adjuvant_template.svg"
      },
      {
       "name": "ic_public_airplane_airstrip",
       "type": "SVG",
       "size": 36219,
       "src": "assets/icons/basic/ic_public_airplane_airstrip.svg"
      },
      {
       "name": "ic_public_alarm_clock",
       "type": "SVG",
       "size": 20471,
       "src": "assets/icons/basic/ic_public_alarm_clock.svg"
      },
      {
       "name": "ic_public_alarmlight",
       "type": "SVG",
       "size": 13911,
       "src": "assets/icons/basic/ic_public_alarmlight.svg"
      },
      {
       "name": "ic_public_alert",
       "type": "SVG",
       "size": 16533,
       "src": "assets/icons/basic/ic_public_alert.svg"
      },
      {
       "name": "ic_public_alert_history",
       "type": "SVG",
       "size": 49529,
       "src": "assets/icons/basic/ic_public_alert_history.svg"
      },
      {
       "name": "ic_public_already_screen",
       "type": "SVG",
       "size": 15951,
       "src": "assets/icons/basic/ic_public_already_screen.svg"
      },
      {
       "name": "ic_public_audio_file",
       "type": "SVG",
       "size": 42749,
       "src": "assets/icons/basic/ic_public_audio_file.svg"
      },
      {
       "name": "ic_public_back",
       "type": "SVG",
       "size": 18347,
       "src": "assets/icons/basic/ic_public_back.svg"
      },
      {
       "name": "ic_public_backward",
       "type": "SVG",
       "size": 13350,
       "src": "assets/icons/basic/ic_public_backward.svg"
      },
      {
       "name": "ic_public_bar_chart",
       "type": "SVG",
       "size": 17625,
       "src": "assets/icons/basic/ic_public_bar_chart.svg"
      },
      {
       "name": "ic_public_battery",
       "type": "SVG",
       "size": 8417,
       "src": "assets/icons/basic/ic_public_battery.svg"
      },
      {
       "name": "ic_public_bell_clock",
       "type": "SVG",
       "size": 31153,
       "src": "assets/icons/basic/ic_public_bell_clock.svg"
      },
      {
       "name": "ic_public_bluetooth",
       "type": "SVG",
       "size": 15801,
       "src": "assets/icons/basic/ic_public_bluetooth.svg"
      },
      {
       "name": "ic_public_bolt_circle",
       "type": "SVG",
       "size": 45669,
       "src": "assets/icons/basic/ic_public_bolt_circle.svg"
      },
      {
       "name": "ic_public_book",
       "type": "SVG",
       "size": 13601,
       "src": "assets/icons/basic/ic_public_book.svg"
      },
      {
       "name": "ic_public_book_bag",
       "type": "SVG",
       "size": 17683,
       "src": "assets/icons/basic/ic_public_book_bag.svg"
      },
      {
       "name": "ic_public_bookmark",
       "type": "SVG",
       "size": 17203,
       "src": "assets/icons/basic/ic_public_bookmark.svg"
      },
      {
       "name": "ic_public_box",
       "type": "SVG",
       "size": 21356,
       "src": "assets/icons/basic/ic_public_box.svg"
      },
      {
       "name": "ic_public_box_open",
       "type": "SVG",
       "size": 47280,
       "src": "assets/icons/basic/ic_public_box_open.svg"
      },
      {
       "name": "ic_public_briefcase",
       "type": "SVG",
       "size": 40136,
       "src": "assets/icons/basic/ic_public_briefcase.svg"
      },
      {
       "name": "ic_public_broom",
       "type": "SVG",
       "size": 21253,
       "src": "assets/icons/basic/ic_public_broom.svg"
      },
      {
       "name": "ic_public_brush",
       "type": "SVG",
       "size": 12041,
       "src": "assets/icons/basic/ic_public_brush.svg"
      },
      {
       "name": "ic_public_building",
       "type": "SVG",
       "size": 13435,
       "src": "assets/icons/basic/ic_public_building.svg"
      },
      {
       "name": "ic_public_calculate",
       "type": "SVG",
       "size": 32751,
       "src": "assets/icons/basic/ic_public_calculate.svg"
      },
      {
       "name": "ic_public_calendar",
       "type": "SVG",
       "size": 17685,
       "src": "assets/icons/basic/ic_public_calendar.svg"
      },
      {
       "name": "ic_public_calendar_list",
       "type": "SVG",
       "size": 35673,
       "src": "assets/icons/basic/ic_public_calendar_list.svg"
      },
      {
       "name": "ic_public_camera",
       "type": "SVG",
       "size": 13618,
       "src": "assets/icons/basic/ic_public_camera.svg"
      },
      {
       "name": "ic_public_camera_box",
       "type": "SVG",
       "size": 34872,
       "src": "assets/icons/basic/ic_public_camera_box.svg"
      },
      {
       "name": "ic_public_camera_dome",
       "type": "SVG",
       "size": 63122,
       "src": "assets/icons/basic/ic_public_camera_dome.svg"
      },
      {
       "name": "ic_public_car",
       "type": "SVG",
       "size": 39498,
       "src": "assets/icons/basic/ic_public_car.svg"
      },
      {
       "name": "ic_public_cart",
       "type": "SVG",
       "size": 20655,
       "src": "assets/icons/basic/ic_public_cart.svg"
      },
      {
       "name": "ic_public_chart",
       "type": "SVG",
       "size": 16071,
       "src": "assets/icons/basic/ic_public_chart.svg"
      },
      {
       "name": "ic_public_chart_bar",
       "type": "SVG",
       "size": 14005,
       "src": "assets/icons/basic/ic_public_chart_bar.svg"
      },
      {
       "name": "ic_public_chart_gantt",
       "type": "SVG",
       "size": 25588,
       "src": "assets/icons/basic/ic_public_chart_gantt.svg"
      },
      {
       "name": "ic_public_checkmark",
       "type": "SVG",
       "size": 6143,
       "src": "assets/icons/basic/ic_public_checkmark.svg"
      },
      {
       "name": "ic_public_chevron_down",
       "type": "SVG",
       "size": 8357,
       "src": "assets/icons/basic/ic_public_chevron_down.svg"
      },
      {
       "name": "ic_public_chevron_up",
       "type": "SVG",
       "size": 4945,
       "src": "assets/icons/basic/ic_public_chevron_up.svg"
      },
      {
       "name": "ic_public_circular_template",
       "type": "SVG",
       "size": 7281,
       "src": "assets/icons/basic/ic_public_circular_template.svg"
      },
      {
       "name": "ic_public_clipboard",
       "type": "SVG",
       "size": 44714,
       "src": "assets/icons/basic/ic_public_clipboard.svg"
      },
      {
       "name": "ic_public_clock",
       "type": "SVG",
       "size": 10031,
       "src": "assets/icons/basic/ic_public_clock.svg"
      },
      {
       "name": "ic_public_clock_globe",
       "type": "SVG",
       "size": 51730,
       "src": "assets/icons/basic/ic_public_clock_globe.svg"
      },
      {
       "name": "ic_public_close",
       "type": "SVG",
       "size": 8330,
       "src": "assets/icons/basic/ic_public_close.svg"
      },
      {
       "name": "ic_public_close_circle",
       "type": "SVG",
       "size": 11396,
       "src": "assets/icons/basic/ic_public_close_circle.svg"
      },
      {
       "name": "ic_public_cloud",
       "type": "SVG",
       "size": 26771,
       "src": "assets/icons/basic/ic_public_cloud.svg"
      },
      {
       "name": "ic_public_code",
       "type": "SVG",
       "size": 23215,
       "src": "assets/icons/basic/ic_public_code.svg"
      },
      {
       "name": "ic_public_collecting_files",
       "type": "SVG",
       "size": 15843,
       "src": "assets/icons/basic/ic_public_collecting_files.svg"
      },
      {
       "name": "ic_public_color_palette",
       "type": "SVG",
       "size": 87072,
       "src": "assets/icons/basic/ic_public_color_palette.svg"
      },
      {
       "name": "ic_public_connect_square",
       "type": "SVG",
       "size": 21079,
       "src": "assets/icons/basic/ic_public_connect_square.svg"
      },
      {
       "name": "ic_public_contribution",
       "type": "SVG",
       "size": 24905,
       "src": "assets/icons/basic/ic_public_contribution.svg"
      },
      {
       "name": "ic_public_copy",
       "type": "SVG",
       "size": 12912,
       "src": "assets/icons/basic/ic_public_copy.svg"
      },
      {
       "name": "ic_public_creditcard",
       "type": "SVG",
       "size": 30113,
       "src": "assets/icons/basic/ic_public_creditcard.svg"
      },
      {
       "name": "ic_public_cut",
       "type": "SVG",
       "size": 16038,
       "src": "assets/icons/basic/ic_public_cut.svg"
      },
      {
       "name": "ic_public_dashboard",
       "type": "SVG",
       "size": 36040,
       "src": "assets/icons/basic/ic_public_dashboard.svg"
      },
      {
       "name": "ic_public_data_access",
       "type": "SVG",
       "size": 14510,
       "src": "assets/icons/basic/ic_public_data_access.svg"
      },
      {
       "name": "ic_public_data_statistics",
       "type": "SVG",
       "size": 13067,
       "src": "assets/icons/basic/ic_public_data_statistics.svg"
      },
      {
       "name": "ic_public_deploy",
       "type": "SVG",
       "size": 32492,
       "src": "assets/icons/basic/ic_public_deploy.svg"
      },
      {
       "name": "ic_public_disk",
       "type": "SVG",
       "size": 19441,
       "src": "assets/icons/basic/ic_public_disk.svg"
      },
      {
       "name": "ic_public_doc_clock",
       "type": "SVG",
       "size": 51303,
       "src": "assets/icons/basic/ic_public_doc_clock.svg"
      },
      {
       "name": "ic_public_door",
       "type": "SVG",
       "size": 25712,
       "src": "assets/icons/basic/ic_public_door.svg"
      },
      {
       "name": "ic_public_door_open",
       "type": "SVG",
       "size": 29690,
       "src": "assets/icons/basic/ic_public_door_open.svg"
      },
      {
       "name": "ic_public_doughnut_chart",
       "type": "SVG",
       "size": 17619,
       "src": "assets/icons/basic/ic_public_doughnut_chart.svg"
      },
      {
       "name": "ic_public_download",
       "type": "SVG",
       "size": 24929,
       "src": "assets/icons/basic/ic_public_download.svg"
      },
      {
       "name": "ic_public_drag",
       "type": "SVG",
       "size": 18314,
       "src": "assets/icons/basic/ic_public_drag.svg"
      },
      {
       "name": "ic_public_drag_and_drop",
       "type": "SVG",
       "size": 7136,
       "src": "assets/icons/basic/ic_public_drag_and_drop.svg"
      },
      {
       "name": "ic_public_drink",
       "type": "SVG",
       "size": 26740,
       "src": "assets/icons/basic/ic_public_drink.svg"
      },
      {
       "name": "ic_public_ear",
       "type": "SVG",
       "size": 48077,
       "src": "assets/icons/basic/ic_public_ear.svg"
      },
      {
       "name": "ic_public_earth",
       "type": "SVG",
       "size": 32921,
       "src": "assets/icons/basic/ic_public_earth.svg"
      },
      {
       "name": "ic_public_earth_net",
       "type": "SVG",
       "size": 32102,
       "src": "assets/icons/basic/ic_public_earth_net.svg"
      },
      {
       "name": "ic_public_elevator_person_down",
       "type": "SVG",
       "size": 22917,
       "src": "assets/icons/basic/ic_public_elevator_person_down.svg"
      },
      {
       "name": "ic_public_elevator_person_up",
       "type": "SVG",
       "size": 22098,
       "src": "assets/icons/basic/ic_public_elevator_person_up.svg"
      },
      {
       "name": "ic_public_ellipsis",
       "type": "SVG",
       "size": 5728,
       "src": "assets/icons/basic/ic_public_ellipsis.svg"
      },
      {
       "name": "ic_public_emoji_smile",
       "type": "SVG",
       "size": 15879,
       "src": "assets/icons/basic/ic_public_emoji_smile.svg"
      },
      {
       "name": "ic_public_entertainment",
       "type": "SVG",
       "size": 53273,
       "src": "assets/icons/basic/ic_public_entertainment.svg"
      },
      {
       "name": "ic_public_envelope",
       "type": "SVG",
       "size": 19980,
       "src": "assets/icons/basic/ic_public_envelope.svg"
      },
      {
       "name": "ic_public_equity",
       "type": "SVG",
       "size": 21084,
       "src": "assets/icons/basic/ic_public_equity.svg"
      },
      {
       "name": "ic_public_eraser",
       "type": "SVG",
       "size": 19224,
       "src": "assets/icons/basic/ic_public_eraser.svg"
      },
      {
       "name": "ic_public_exit",
       "type": "SVG",
       "size": 34878,
       "src": "assets/icons/basic/ic_public_exit.svg"
      },
      {
       "name": "ic_public_expand",
       "type": "SVG",
       "size": 17872,
       "src": "assets/icons/basic/ic_public_expand.svg"
      },
      {
       "name": "ic_public_eye",
       "type": "SVG",
       "size": 8945,
       "src": "assets/icons/basic/ic_public_eye.svg"
      },
      {
       "name": "ic_public_eye_close",
       "type": "SVG",
       "size": 12080,
       "src": "assets/icons/basic/ic_public_eye_close.svg"
      },
      {
       "name": "ic_public_feedback",
       "type": "SVG",
       "size": 49999,
       "src": "assets/icons/basic/ic_public_feedback.svg"
      },
      {
       "name": "ic_public_file_car",
       "type": "SVG",
       "size": 33706,
       "src": "assets/icons/basic/ic_public_file_car.svg"
      },
      {
       "name": "ic_public_files",
       "type": "SVG",
       "size": 9683,
       "src": "assets/icons/basic/ic_public_files.svg"
      },
      {
       "name": "ic_public_filter",
       "type": "SVG",
       "size": 24288,
       "src": "assets/icons/basic/ic_public_filter.svg"
      },
      {
       "name": "ic_public_finger",
       "type": "SVG",
       "size": 26330,
       "src": "assets/icons/basic/ic_public_finger.svg"
      },
      {
       "name": "ic_public_fire",
       "type": "SVG",
       "size": 18550,
       "src": "assets/icons/basic/ic_public_fire.svg"
      },
      {
       "name": "ic_public_flash",
       "type": "SVG",
       "size": 8222,
       "src": "assets/icons/basic/ic_public_flash.svg"
      },
      {
       "name": "ic_public_flashlight",
       "type": "SVG",
       "size": 40080,
       "src": "assets/icons/basic/ic_public_flashlight.svg"
      },
      {
       "name": "ic_public_folder",
       "type": "SVG",
       "size": 26789,
       "src": "assets/icons/basic/ic_public_folder.svg"
      },
      {
       "name": "ic_public_folder_file",
       "type": "SVG",
       "size": 38398,
       "src": "assets/icons/basic/ic_public_folder_file.svg"
      },
      {
       "name": "ic_public_fonts",
       "type": "SVG",
       "size": 47646,
       "src": "assets/icons/basic/ic_public_fonts.svg"
      },
      {
       "name": "ic_public_fullscreen",
       "type": "SVG",
       "size": 30569,
       "src": "assets/icons/basic/ic_public_fullscreen.svg"
      },
      {
       "name": "ic_public_funnel",
       "type": "SVG",
       "size": 8307,
       "src": "assets/icons/basic/ic_public_funnel.svg"
      },
      {
       "name": "ic_public_generic_file",
       "type": "SVG",
       "size": 9221,
       "src": "assets/icons/basic/ic_public_generic_file.svg"
      },
      {
       "name": "ic_public_gift",
       "type": "SVG",
       "size": 37992,
       "src": "assets/icons/basic/ic_public_gift.svg"
      },
      {
       "name": "ic_public_hand",
       "type": "SVG",
       "size": 16297,
       "src": "assets/icons/basic/ic_public_hand.svg"
      },
      {
       "name": "ic_public_hand_thumbsdown",
       "type": "SVG",
       "size": 11547,
       "src": "assets/icons/basic/ic_public_hand_thumbsdown.svg"
      },
      {
       "name": "ic_public_hand_thumbsup",
       "type": "SVG",
       "size": 12241,
       "src": "assets/icons/basic/ic_public_hand_thumbsup.svg"
      },
      {
       "name": "ic_public_harddisk_font",
       "type": "SVG",
       "size": 57414,
       "src": "assets/icons/basic/ic_public_harddisk_font.svg"
      },
      {
       "name": "ic_public_head_questionmark",
       "type": "SVG",
       "size": 61005,
       "src": "assets/icons/basic/ic_public_head_questionmark.svg"
      },
      {
       "name": "ic_public_headphones",
       "type": "SVG",
       "size": 11126,
       "src": "assets/icons/basic/ic_public_headphones.svg"
      },
      {
       "name": "ic_public_headphones_mic",
       "type": "SVG",
       "size": 23812,
       "src": "assets/icons/basic/ic_public_headphones_mic.svg"
      },
      {
       "name": "ic_public_headset",
       "type": "SVG",
       "size": 44316,
       "src": "assets/icons/basic/ic_public_headset.svg"
      },
      {
       "name": "ic_public_heart",
       "type": "SVG",
       "size": 15801,
       "src": "assets/icons/basic/ic_public_heart.svg"
      },
      {
       "name": "ic_public_heart_waveform",
       "type": "SVG",
       "size": 35007,
       "src": "assets/icons/basic/ic_public_heart_waveform.svg"
      },
      {
       "name": "ic_public_heat_map",
       "type": "SVG",
       "size": 14222,
       "src": "assets/icons/basic/ic_public_heat_map.svg"
      },
      {
       "name": "ic_public_history_information",
       "type": "SVG",
       "size": 25849,
       "src": "assets/icons/basic/ic_public_history_information.svg"
      },
      {
       "name": "ic_public_home",
       "type": "SVG",
       "size": 11467,
       "src": "assets/icons/basic/ic_public_home.svg"
      },
      {
       "name": "ic_public_home2",
       "type": "SVG",
       "size": 16755,
       "src": "assets/icons/basic/ic_public_home2.svg"
      },
      {
       "name": "ic_public_horizontal_bar_chart",
       "type": "SVG",
       "size": 13184,
       "src": "assets/icons/basic/ic_public_horizontal_bar_chart.svg"
      },
      {
       "name": "ic_public_horn",
       "type": "SVG",
       "size": 22349,
       "src": "assets/icons/basic/ic_public_horn.svg"
      },
      {
       "name": "ic_public_hotspot",
       "type": "SVG",
       "size": 27044,
       "src": "assets/icons/basic/ic_public_hotspot.svg"
      },
      {
       "name": "ic_public_hourglass",
       "type": "SVG",
       "size": 24373,
       "src": "assets/icons/basic/ic_public_hourglass.svg"
      },
      {
       "name": "ic_public_icon_box",
       "type": "SVG",
       "size": 10114,
       "src": "assets/icons/basic/ic_public_icon_box.svg"
      },
      {
       "name": "ic_public_idcard",
       "type": "SVG",
       "size": 30116,
       "src": "assets/icons/basic/ic_public_idcard.svg"
      },
      {
       "name": "ic_public_image",
       "type": "SVG",
       "size": 14782,
       "src": "assets/icons/basic/ic_public_image.svg"
      },
      {
       "name": "ic_public_info",
       "type": "SVG",
       "size": 13708,
       "src": "assets/icons/basic/ic_public_info.svg"
      },
      {
       "name": "ic_public_info_file",
       "type": "SVG",
       "size": 46060,
       "src": "assets/icons/basic/ic_public_info_file.svg"
      },
      {
       "name": "ic_public_inport",
       "type": "SVG",
       "size": 11111,
       "src": "assets/icons/basic/ic_public_inport.svg"
      },
      {
       "name": "ic_public_input",
       "type": "SVG",
       "size": 18638,
       "src": "assets/icons/basic/ic_public_input.svg"
      },
      {
       "name": "ic_public_invoice",
       "type": "SVG",
       "size": 20783,
       "src": "assets/icons/basic/ic_public_invoice.svg"
      },
      {
       "name": "ic_public_italic",
       "type": "SVG",
       "size": 13594,
       "src": "assets/icons/basic/ic_public_italic.svg"
      },
      {
       "name": "ic_public_key",
       "type": "SVG",
       "size": 19274,
       "src": "assets/icons/basic/ic_public_key.svg"
      },
      {
       "name": "ic_public_left_arrow",
       "type": "SVG",
       "size": 11428,
       "src": "assets/icons/basic/ic_public_left_arrow.svg"
      },
      {
       "name": "ic_public_link",
       "type": "SVG",
       "size": 23539,
       "src": "assets/icons/basic/ic_public_link.svg"
      },
      {
       "name": "ic_public_list_bullet",
       "type": "SVG",
       "size": 25196,
       "src": "assets/icons/basic/ic_public_list_bullet.svg"
      },
      {
       "name": "ic_public_lists",
       "type": "SVG",
       "size": 16425,
       "src": "assets/icons/basic/ic_public_lists.svg"
      },
      {
       "name": "ic_public_loading_clockwise",
       "type": "SVG",
       "size": 6413,
       "src": "assets/icons/basic/ic_public_loading_clockwise.svg"
      },
      {
       "name": "ic_public_location",
       "type": "SVG",
       "size": 10851,
       "src": "assets/icons/basic/ic_public_location.svg"
      },
      {
       "name": "ic_public_lock_open",
       "type": "SVG",
       "size": 23176,
       "src": "assets/icons/basic/ic_public_lock_open.svg"
      },
      {
       "name": "ic_public_locked",
       "type": "SVG",
       "size": 34207,
       "src": "assets/icons/basic/ic_public_locked.svg"
      },
      {
       "name": "ic_public_mailing",
       "type": "SVG",
       "size": 35376,
       "src": "assets/icons/basic/ic_public_mailing.svg"
      },
      {
       "name": "ic_public_manage",
       "type": "SVG",
       "size": 12248,
       "src": "assets/icons/basic/ic_public_manage.svg"
      },
      {
       "name": "ic_public_management",
       "type": "SVG",
       "size": 27864,
       "src": "assets/icons/basic/ic_public_management.svg"
      },
      {
       "name": "ic_public_mappin_on_map",
       "type": "SVG",
       "size": 27838,
       "src": "assets/icons/basic/ic_public_mappin_on_map.svg"
      },
      {
       "name": "ic_public_mappin_person",
       "type": "SVG",
       "size": 38735,
       "src": "assets/icons/basic/ic_public_mappin_person.svg"
      },
      {
       "name": "ic_public_menu_collapse",
       "type": "SVG",
       "size": 16911,
       "src": "assets/icons/basic/ic_public_menu_collapse.svg"
      },
      {
       "name": "ic_public_menu_expansion",
       "type": "SVG",
       "size": 17682,
       "src": "assets/icons/basic/ic_public_menu_expansion.svg"
      },
      {
       "name": "ic_public_menul_line",
       "type": "SVG",
       "size": 10498,
       "src": "assets/icons/basic/ic_public_menul_line.svg"
      },
      {
       "name": "ic_public_menusview",
       "type": "SVG",
       "size": 51884,
       "src": "assets/icons/basic/ic_public_menusview.svg"
      },
      {
       "name": "ic_public_message",
       "type": "SVG",
       "size": 58333,
       "src": "assets/icons/basic/ic_public_message.svg"
      },
      {
       "name": "ic_public_message_bubble",
       "type": "SVG",
       "size": 6522,
       "src": "assets/icons/basic/ic_public_message_bubble.svg"
      },
      {
       "name": "ic_public_message_point",
       "type": "SVG",
       "size": 38643,
       "src": "assets/icons/basic/ic_public_message_point.svg"
      },
      {
       "name": "ic_public_mic",
       "type": "SVG",
       "size": 12782,
       "src": "assets/icons/basic/ic_public_mic.svg"
      },
      {
       "name": "ic_public_mic_text",
       "type": "SVG",
       "size": 30661,
       "src": "assets/icons/basic/ic_public_mic_text.svg"
      },
      {
       "name": "ic_public_minus",
       "type": "SVG",
       "size": 4599,
       "src": "assets/icons/basic/ic_public_minus.svg"
      },
      {
       "name": "ic_public_minus_circle",
       "type": "SVG",
       "size": 8716,
       "src": "assets/icons/basic/ic_public_minus_circle.svg"
      },
      {
       "name": "ic_public_mirror",
       "type": "SVG",
       "size": 19116,
       "src": "assets/icons/basic/ic_public_mirror.svg"
      },
      {
       "name": "ic_public_mobilephone",
       "type": "SVG",
       "size": 21904,
       "src": "assets/icons/basic/ic_public_mobilephone.svg"
      },
      {
       "name": "ic_public_money_circle",
       "type": "SVG",
       "size": 14836,
       "src": "assets/icons/basic/ic_public_money_circle.svg"
      },
      {
       "name": "ic_public_moon",
       "type": "SVG",
       "size": 12800,
       "src": "assets/icons/basic/ic_public_moon.svg"
      },
      {
       "name": "ic_public_music_mic",
       "type": "SVG",
       "size": 26888,
       "src": "assets/icons/basic/ic_public_music_mic.svg"
      },
      {
       "name": "ic_public_music_note",
       "type": "SVG",
       "size": 20727,
       "src": "assets/icons/basic/ic_public_music_note.svg"
      },
      {
       "name": "ic_public_network_monitoring",
       "type": "SVG",
       "size": 30470,
       "src": "assets/icons/basic/ic_public_network_monitoring.svg"
      },
      {
       "name": "ic_public_notebook",
       "type": "SVG",
       "size": 12065,
       "src": "assets/icons/basic/ic_public_notebook.svg"
      },
      {
       "name": "ic_public_notes",
       "type": "SVG",
       "size": 26403,
       "src": "assets/icons/basic/ic_public_notes.svg"
      },
      {
       "name": "ic_public_notice",
       "type": "SVG",
       "size": 14799,
       "src": "assets/icons/basic/ic_public_notice.svg"
      },
      {
       "name": "ic_public_office_brush",
       "type": "SVG",
       "size": 25119,
       "src": "assets/icons/basic/ic_public_office_brush.svg"
      },
      {
       "name": "ic_public_paintbrush",
       "type": "SVG",
       "size": 19520,
       "src": "assets/icons/basic/ic_public_paintbrush.svg"
      },
      {
       "name": "ic_public_paperclip",
       "type": "SVG",
       "size": 19559,
       "src": "assets/icons/basic/ic_public_paperclip.svg"
      },
      {
       "name": "ic_public_paperplane",
       "type": "SVG",
       "size": 16959,
       "src": "assets/icons/basic/ic_public_paperplane.svg"
      },
      {
       "name": "ic_public_pause",
       "type": "SVG",
       "size": 10239,
       "src": "assets/icons/basic/ic_public_pause.svg"
      },
      {
       "name": "ic_public_pause2",
       "type": "SVG",
       "size": 10449,
       "src": "assets/icons/basic/ic_public_pause2.svg"
      },
      {
       "name": "ic_public_pause_fresh",
       "type": "SVG",
       "size": 24796,
       "src": "assets/icons/basic/ic_public_pause_fresh.svg"
      },
      {
       "name": "ic_public_pdf_file",
       "type": "SVG",
       "size": 43666,
       "src": "assets/icons/basic/ic_public_pdf_file.svg"
      },
      {
       "name": "ic_public_person",
       "type": "SVG",
       "size": 5396,
       "src": "assets/icons/basic/ic_public_person.svg"
      },
      {
       "name": "ic_public_person_chair",
       "type": "SVG",
       "size": 31852,
       "src": "assets/icons/basic/ic_public_person_chair.svg"
      },
      {
       "name": "ic_public_person_door",
       "type": "SVG",
       "size": 17610,
       "src": "assets/icons/basic/ic_public_person_door.svg"
      },
      {
       "name": "ic_public_phone_counterclock",
       "type": "SVG",
       "size": 51501,
       "src": "assets/icons/basic/ic_public_phone_counterclock.svg"
      },
      {
       "name": "ic_public_phone_gear",
       "type": "SVG",
       "size": 20541,
       "src": "assets/icons/basic/ic_public_phone_gear.svg"
      },
      {
       "name": "ic_public_photo_group",
       "type": "SVG",
       "size": 23696,
       "src": "assets/icons/basic/ic_public_photo_group.svg"
      },
      {
       "name": "ic_public_pic_file",
       "type": "SVG",
       "size": 38428,
       "src": "assets/icons/basic/ic_public_pic_file.svg"
      },
      {
       "name": "ic_public_plane",
       "type": "SVG",
       "size": 20774,
       "src": "assets/icons/basic/ic_public_plane.svg"
      },
      {
       "name": "ic_public_plane_car",
       "type": "SVG",
       "size": 40335,
       "src": "assets/icons/basic/ic_public_plane_car.svg"
      },
      {
       "name": "ic_public_plane_landed",
       "type": "SVG",
       "size": 25859,
       "src": "assets/icons/basic/ic_public_plane_landed.svg"
      },
      {
       "name": "ic_public_plane_takeoff",
       "type": "SVG",
       "size": 19045,
       "src": "assets/icons/basic/ic_public_plane_takeoff.svg"
      },
      {
       "name": "ic_public_plane_waiting",
       "type": "SVG",
       "size": 22304,
       "src": "assets/icons/basic/ic_public_plane_waiting.svg"
      },
      {
       "name": "ic_public_planets",
       "type": "SVG",
       "size": 20802,
       "src": "assets/icons/basic/ic_public_planets.svg"
      },
      {
       "name": "ic_public_play",
       "type": "SVG",
       "size": 10441,
       "src": "assets/icons/basic/ic_public_play.svg"
      },
      {
       "name": "ic_public_play_circle",
       "type": "SVG",
       "size": 18792,
       "src": "assets/icons/basic/ic_public_play_circle.svg"
      },
      {
       "name": "ic_public_plus",
       "type": "SVG",
       "size": 10712,
       "src": "assets/icons/basic/ic_public_plus.svg"
      },
      {
       "name": "ic_public_plus_circle",
       "type": "SVG",
       "size": 11003,
       "src": "assets/icons/basic/ic_public_plus_circle.svg"
      },
      {
       "name": "ic_public_policecar",
       "type": "SVG",
       "size": 47445,
       "src": "assets/icons/basic/ic_public_policecar.svg"
      },
      {
       "name": "ic_public_position",
       "type": "SVG",
       "size": 12551,
       "src": "assets/icons/basic/ic_public_position.svg"
      },
      {
       "name": "ic_public_power",
       "type": "SVG",
       "size": 19898,
       "src": "assets/icons/basic/ic_public_power.svg"
      },
      {
       "name": "ic_public_power_duplicating",
       "type": "SVG",
       "size": 10933,
       "src": "assets/icons/basic/ic_public_power_duplicating.svg"
      },
      {
       "name": "ic_public_power_point_file",
       "type": "SVG",
       "size": 26882,
       "src": "assets/icons/basic/ic_public_power_point_file.svg"
      },
      {
       "name": "ic_public_prediction_line",
       "type": "SVG",
       "size": 19610,
       "src": "assets/icons/basic/ic_public_prediction_line.svg"
      },
      {
       "name": "ic_public_printer",
       "type": "SVG",
       "size": 19705,
       "src": "assets/icons/basic/ic_public_printer.svg"
      },
      {
       "name": "ic_public_prohibit_circle",
       "type": "SVG",
       "size": 7735,
       "src": "assets/icons/basic/ic_public_prohibit_circle.svg"
      },
      {
       "name": "ic_public_prohibit_setting",
       "type": "SVG",
       "size": 22255,
       "src": "assets/icons/basic/ic_public_prohibit_setting.svg"
      },
      {
       "name": "ic_public_projector",
       "type": "SVG",
       "size": 30028,
       "src": "assets/icons/basic/ic_public_projector.svg"
      },
      {
       "name": "ic_public_qrcode",
       "type": "SVG",
       "size": 22050,
       "src": "assets/icons/basic/ic_public_qrcode.svg"
      },
      {
       "name": "ic_public_questionmark",
       "type": "SVG",
       "size": 27645,
       "src": "assets/icons/basic/ic_public_questionmark.svg"
      },
      {
       "name": "ic_public_questionmark_circle",
       "type": "SVG",
       "size": 31539,
       "src": "assets/icons/basic/ic_public_questionmark_circle.svg"
      },
      {
       "name": "ic_public_radiowave",
       "type": "SVG",
       "size": 55663,
       "src": "assets/icons/basic/ic_public_radiowave.svg"
      },
      {
       "name": "ic_public_realtime_traffic",
       "type": "SVG",
       "size": 36569,
       "src": "assets/icons/basic/ic_public_realtime_traffic.svg"
      },
      {
       "name": "ic_public_recall",
       "type": "SVG",
       "size": 8652,
       "src": "assets/icons/basic/ic_public_recall.svg"
      },
      {
       "name": "ic_public_redcross",
       "type": "SVG",
       "size": 25260,
       "src": "assets/icons/basic/ic_public_redcross.svg"
      },
      {
       "name": "ic_public_redo",
       "type": "SVG",
       "size": 10786,
       "src": "assets/icons/basic/ic_public_redo.svg"
      },
      {
       "name": "ic_public_refresh_clockwise",
       "type": "SVG",
       "size": 15853,
       "src": "assets/icons/basic/ic_public_refresh_clockwise.svg"
      },
      {
       "name": "ic_public_remarks",
       "type": "SVG",
       "size": 9074,
       "src": "assets/icons/basic/ic_public_remarks.svg"
      },
      {
       "name": "ic_public_reply",
       "type": "SVG",
       "size": 50657,
       "src": "assets/icons/basic/ic_public_reply.svg"
      },
      {
       "name": "ic_public_reply_all",
       "type": "SVG",
       "size": 65396,
       "src": "assets/icons/basic/ic_public_reply_all.svg"
      },
      {
       "name": "ic_public_resetting",
       "type": "SVG",
       "size": 18698,
       "src": "assets/icons/basic/ic_public_resetting.svg"
      },
      {
       "name": "ic_public_restore",
       "type": "SVG",
       "size": 23516,
       "src": "assets/icons/basic/ic_public_restore.svg"
      },
      {
       "name": "ic_public_right_arrow",
       "type": "SVG",
       "size": 11406,
       "src": "assets/icons/basic/ic_public_right_arrow.svg"
      },
      {
       "name": "ic_public_right_arrow2",
       "type": "SVG",
       "size": 10232,
       "src": "assets/icons/basic/ic_public_right_arrow2.svg"
      },
      {
       "name": "ic_public_rocket",
       "type": "SVG",
       "size": 33608,
       "src": "assets/icons/basic/ic_public_rocket.svg"
      },
      {
       "name": "ic_public_scans",
       "type": "SVG",
       "size": 12860,
       "src": "assets/icons/basic/ic_public_scans.svg"
      },
      {
       "name": "ic_public_scans_person",
       "type": "SVG",
       "size": 32145,
       "src": "assets/icons/basic/ic_public_scans_person.svg"
      },
      {
       "name": "ic_public_scissors_screen",
       "type": "SVG",
       "size": 29635,
       "src": "assets/icons/basic/ic_public_scissors_screen.svg"
      },
      {
       "name": "ic_public_scissors_waveform",
       "type": "SVG",
       "size": 35092,
       "src": "assets/icons/basic/ic_public_scissors_waveform.svg"
      },
      {
       "name": "ic_public_scope_dot",
       "type": "SVG",
       "size": 20017,
       "src": "assets/icons/basic/ic_public_scope_dot.svg"
      },
      {
       "name": "ic_public_screen_wifi",
       "type": "SVG",
       "size": 70484,
       "src": "assets/icons/basic/ic_public_screen_wifi.svg"
      },
      {
       "name": "ic_public_sd",
       "type": "SVG",
       "size": 28702,
       "src": "assets/icons/basic/ic_public_sd.svg"
      },
      {
       "name": "ic_public_search",
       "type": "SVG",
       "size": 17061,
       "src": "assets/icons/basic/ic_public_search.svg"
      },
      {
       "name": "ic_public_security",
       "type": "SVG",
       "size": 24798,
       "src": "assets/icons/basic/ic_public_security.svg"
      },
      {
       "name": "ic_public_select_all",
       "type": "SVG",
       "size": 33941,
       "src": "assets/icons/basic/ic_public_select_all.svg"
      },
      {
       "name": "ic_public_send",
       "type": "SVG",
       "size": 21627,
       "src": "assets/icons/basic/ic_public_send.svg"
      },
      {
       "name": "ic_public_send_a_letter",
       "type": "SVG",
       "size": 50033,
       "src": "assets/icons/basic/ic_public_send_a_letter.svg"
      },
      {
       "name": "ic_public_send_all",
       "type": "SVG",
       "size": 58866,
       "src": "assets/icons/basic/ic_public_send_all.svg"
      },
      {
       "name": "ic_public_serve",
       "type": "SVG",
       "size": 11913,
       "src": "assets/icons/basic/ic_public_serve.svg"
      },
      {
       "name": "ic_public_setting",
       "type": "SVG",
       "size": 17293,
       "src": "assets/icons/basic/ic_public_setting.svg"
      },
      {
       "name": "ic_public_share",
       "type": "SVG",
       "size": 8771,
       "src": "assets/icons/basic/ic_public_share.svg"
      },
      {
       "name": "ic_public_share_arrow",
       "type": "SVG",
       "size": 20138,
       "src": "assets/icons/basic/ic_public_share_arrow.svg"
      },
      {
       "name": "ic_public_shirt",
       "type": "SVG",
       "size": 8678,
       "src": "assets/icons/basic/ic_public_shirt.svg"
      },
      {
       "name": "ic_public_shopping_bag",
       "type": "SVG",
       "size": 26634,
       "src": "assets/icons/basic/ic_public_shopping_bag.svg"
      },
      {
       "name": "ic_public_sim",
       "type": "SVG",
       "size": 30110,
       "src": "assets/icons/basic/ic_public_sim.svg"
      },
      {
       "name": "ic_public_simulcast",
       "type": "SVG",
       "size": 20455,
       "src": "assets/icons/basic/ic_public_simulcast.svg"
      },
      {
       "name": "ic_public_simulcast_english",
       "type": "SVG",
       "size": 29460,
       "src": "assets/icons/basic/ic_public_simulcast_english.svg"
      },
      {
       "name": "ic_public_single_cycle",
       "type": "SVG",
       "size": 29700,
       "src": "assets/icons/basic/ic_public_single_cycle.svg"
      },
      {
       "name": "ic_public_skip",
       "type": "SVG",
       "size": 19460,
       "src": "assets/icons/basic/ic_public_skip.svg"
      },
      {
       "name": "ic_public_smartwatch",
       "type": "SVG",
       "size": 11711,
       "src": "assets/icons/basic/ic_public_smartwatch.svg"
      },
      {
       "name": "ic_public_sort",
       "type": "SVG",
       "size": 12700,
       "src": "assets/icons/basic/ic_public_sort.svg"
      },
      {
       "name": "ic_public_sort_down",
       "type": "SVG",
       "size": 16802,
       "src": "assets/icons/basic/ic_public_sort_down.svg"
      },
      {
       "name": "ic_public_sort_up",
       "type": "SVG",
       "size": 12592,
       "src": "assets/icons/basic/ic_public_sort_up.svg"
      },
      {
       "name": "ic_public_sound",
       "type": "SVG",
       "size": 36922,
       "src": "assets/icons/basic/ic_public_sound.svg"
      },
      {
       "name": "ic_public_speaker",
       "type": "SVG",
       "size": 15427,
       "src": "assets/icons/basic/ic_public_speaker.svg"
      },
      {
       "name": "ic_public_square",
       "type": "SVG",
       "size": 11399,
       "src": "assets/icons/basic/ic_public_square.svg"
      },
      {
       "name": "ic_public_square_add",
       "type": "SVG",
       "size": 43221,
       "src": "assets/icons/basic/ic_public_square_add.svg"
      },
      {
       "name": "ic_public_square_template",
       "type": "SVG",
       "size": 8470,
       "src": "assets/icons/basic/ic_public_square_template.svg"
      },
      {
       "name": "ic_public_star",
       "type": "SVG",
       "size": 8092,
       "src": "assets/icons/basic/ic_public_star.svg"
      },
      {
       "name": "ic_public_star_bookmark",
       "type": "SVG",
       "size": 39343,
       "src": "assets/icons/basic/ic_public_star_bookmark.svg"
      },
      {
       "name": "ic_public_star_circle",
       "type": "SVG",
       "size": 17742,
       "src": "assets/icons/basic/ic_public_star_circle.svg"
      },
      {
       "name": "ic_public_stop_circle",
       "type": "SVG",
       "size": 9223,
       "src": "assets/icons/basic/ic_public_stop_circle.svg"
      },
      {
       "name": "ic_public_stopwatch",
       "type": "SVG",
       "size": 71114,
       "src": "assets/icons/basic/ic_public_stopwatch.svg"
      },
      {
       "name": "ic_public_study",
       "type": "SVG",
       "size": 34600,
       "src": "assets/icons/basic/ic_public_study.svg"
      },
      {
       "name": "ic_public_success",
       "type": "SVG",
       "size": 10526,
       "src": "assets/icons/basic/ic_public_success.svg"
      },
      {
       "name": "ic_public_suitcase",
       "type": "SVG",
       "size": 28069,
       "src": "assets/icons/basic/ic_public_suitcase.svg"
      },
      {
       "name": "ic_public_suitcase_magnifyingglass",
       "type": "SVG",
       "size": 99984,
       "src": "assets/icons/basic/ic_public_suitcase_magnifyingglass.svg"
      },
      {
       "name": "ic_public_sun",
       "type": "SVG",
       "size": 22870,
       "src": "assets/icons/basic/ic_public_sun.svg"
      },
      {
       "name": "ic_public_sweepingrobot",
       "type": "SVG",
       "size": 32419,
       "src": "assets/icons/basic/ic_public_sweepingrobot.svg"
      },
      {
       "name": "ic_public_switchover",
       "type": "SVG",
       "size": 15060,
       "src": "assets/icons/basic/ic_public_switchover.svg"
      },
      {
       "name": "ic_public_system_tree",
       "type": "SVG",
       "size": 18890,
       "src": "assets/icons/basic/ic_public_system_tree.svg"
      },
      {
       "name": "ic_public_tablet",
       "type": "SVG",
       "size": 30246,
       "src": "assets/icons/basic/ic_public_tablet.svg"
      },
      {
       "name": "ic_public_tag",
       "type": "SVG",
       "size": 10309,
       "src": "assets/icons/basic/ic_public_tag.svg"
      },
      {
       "name": "ic_public_teams",
       "type": "SVG",
       "size": 42906,
       "src": "assets/icons/basic/ic_public_teams.svg"
      },
      {
       "name": "ic_public_telephone",
       "type": "SVG",
       "size": 11457,
       "src": "assets/icons/basic/ic_public_telephone.svg"
      },
      {
       "name": "ic_public_textcolor",
       "type": "SVG",
       "size": 25697,
       "src": "assets/icons/basic/ic_public_textcolor.svg"
      },
      {
       "name": "ic_public_textformat",
       "type": "SVG",
       "size": 17307,
       "src": "assets/icons/basic/ic_public_textformat.svg"
      },
      {
       "name": "ic_public_threshold_line",
       "type": "SVG",
       "size": 19620,
       "src": "assets/icons/basic/ic_public_threshold_line.svg"
      },
      {
       "name": "ic_public_toolbox",
       "type": "SVG",
       "size": 26111,
       "src": "assets/icons/basic/ic_public_toolbox.svg"
      },
      {
       "name": "ic_public_transverse_rectangle_template",
       "type": "SVG",
       "size": 8539,
       "src": "assets/icons/basic/ic_public_transverse_rectangle_template.svg"
      },
      {
       "name": "ic_public_trash",
       "type": "SVG",
       "size": 17103,
       "src": "assets/icons/basic/ic_public_trash.svg"
      },
      {
       "name": "ic_public_tray",
       "type": "SVG",
       "size": 10633,
       "src": "assets/icons/basic/ic_public_tray.svg"
      },
      {
       "name": "ic_public_tv",
       "type": "SVG",
       "size": 14100,
       "src": "assets/icons/basic/ic_public_tv.svg"
      },
      {
       "name": "ic_public_tv_mv",
       "type": "SVG",
       "size": 39747,
       "src": "assets/icons/basic/ic_public_tv_mv.svg"
      },
      {
       "name": "ic_public_tv_play",
       "type": "SVG",
       "size": 37392,
       "src": "assets/icons/basic/ic_public_tv_play.svg"
      },
      {
       "name": "ic_public_underline",
       "type": "SVG",
       "size": 14726,
       "src": "assets/icons/basic/ic_public_underline.svg"
      },
      {
       "name": "ic_public_unknown_file",
       "type": "SVG",
       "size": 34897,
       "src": "assets/icons/basic/ic_public_unknown_file.svg"
      },
      {
       "name": "ic_public_update",
       "type": "SVG",
       "size": 31872,
       "src": "assets/icons/basic/ic_public_update.svg"
      },
      {
       "name": "ic_public_upload",
       "type": "SVG",
       "size": 20231,
       "src": "assets/icons/basic/ic_public_upload.svg"
      },
      {
       "name": "ic_public_vertical_rectangle_template",
       "type": "SVG",
       "size": 10034,
       "src": "assets/icons/basic/ic_public_vertical_rectangle_template.svg"
      },
      {
       "name": "ic_public_video",
       "type": "SVG",
       "size": 7814,
       "src": "assets/icons/basic/ic_public_video.svg"
      },
      {
       "name": "ic_public_video_file",
       "type": "SVG",
       "size": 36574,
       "src": "assets/icons/basic/ic_public_video_file.svg"
      },
      {
       "name": "ic_public_videorecorder",
       "type": "SVG",
       "size": 15749,
       "src": "assets/icons/basic/ic_public_videorecorder.svg"
      },
      {
       "name": "ic_public_view_information",
       "type": "SVG",
       "size": 55480,
       "src": "assets/icons/basic/ic_public_view_information.svg"
      },
      {
       "name": "ic_public_view_tasks",
       "type": "SVG",
       "size": 70008,
       "src": "assets/icons/basic/ic_public_view_tasks.svg"
      },
      {
       "name": "ic_public_voice_call",
       "type": "SVG",
       "size": 30580,
       "src": "assets/icons/basic/ic_public_voice_call.svg"
      },
      {
       "name": "ic_public_vr",
       "type": "SVG",
       "size": 24125,
       "src": "assets/icons/basic/ic_public_vr.svg"
      },
      {
       "name": "ic_public_warning",
       "type": "SVG",
       "size": 10826,
       "src": "assets/icons/basic/ic_public_warning.svg"
      },
      {
       "name": "ic_public_weightscale",
       "type": "SVG",
       "size": 19336,
       "src": "assets/icons/basic/ic_public_weightscale.svg"
      },
      {
       "name": "ic_public_wifi",
       "type": "SVG",
       "size": 18777,
       "src": "assets/icons/basic/ic_public_wifi.svg"
      },
      {
       "name": "ic_public_wrench",
       "type": "SVG",
       "size": 20691,
       "src": "assets/icons/basic/ic_public_wrench.svg"
      },
      {
       "name": "ic_public_zip_file",
       "type": "SVG",
       "size": 28074,
       "src": "assets/icons/basic/ic_public_zip_file.svg"
      },
      {
       "name": "ic_public_zoom_in",
       "type": "SVG",
       "size": 31525,
       "src": "assets/icons/basic/ic_public_zoom_in.svg"
      },
      {
       "name": "ic_public_zoom_out",
       "type": "SVG",
       "size": 30553,
       "src": "assets/icons/basic/ic_public_zoom_out.svg"
      },
      {
       "name": "ic_public_zoom_out1",
       "type": "SVG",
       "size": 20395,
       "src": "assets/icons/basic/ic_public_zoom_out1.svg"
      }
     ]
    },
    {
     "title": "quality",
     "items": [
      {
       "name": "ic_enterprise_bg_occupied_conference_room_material",
       "type": "SVG",
       "size": 3547,
       "src": "assets/icons/quality/ic_enterprise_bg_occupied_conference_room_material.svg"
      },
      {
       "name": "ic_huawei_cloud_circulate_material",
       "type": "SVG",
       "size": 3131,
       "src": "assets/icons/quality/ic_huawei_cloud_circulate_material.svg"
      },
      {
       "name": "ic_ict_board_dcm1",
       "type": "SVG",
       "size": 6013,
       "src": "assets/icons/quality/ic_ict_board_dcm1.svg"
      },
      {
       "name": "ic_ict_collecting_files_material",
       "type": "SVG",
       "size": 2577,
       "src": "assets/icons/quality/ic_ict_collecting_files_material.svg"
      },
      {
       "name": "ic_ict_nce_template_management_material",
       "type": "SVG",
       "size": 2852,
       "src": "assets/icons/quality/ic_ict_nce_template_management_material.svg"
      },
      {
       "name": "ic_ict_protect_network_security_material",
       "type": "SVG",
       "size": 4366,
       "src": "assets/icons/quality/ic_ict_protect_network_security_material.svg"
      },
      {
       "name": "ic_nce_close_event_material",
       "type": "SVG",
       "size": 2534,
       "src": "assets/icons/quality/ic_nce_close_event_material.svg"
      },
      {
       "name": "ic_nce_close_event_material1",
       "type": "SVG",
       "size": 6035,
       "src": "assets/icons/quality/ic_nce_close_event_material1.svg"
      },
      {
       "name": "ic_nce_fabric_global_resource_pool_material",
       "type": "SVG",
       "size": 3539,
       "src": "assets/icons/quality/ic_nce_fabric_global_resource_pool_material.svg"
      },
      {
       "name": "ic_nce_template_management_material",
       "type": "SVG",
       "size": 2667,
       "src": "assets/icons/quality/ic_nce_template_management_material.svg"
      },
      {
       "name": "ic_public_add_member1",
       "type": "SVG",
       "size": 3892,
       "src": "assets/icons/quality/ic_public_add_member1.svg"
      },
      {
       "name": "ic_public_alarmlight1",
       "type": "SVG",
       "size": 2430,
       "src": "assets/icons/quality/ic_public_alarmlight1.svg"
      },
      {
       "name": "ic_public_alert2_textured",
       "type": "SVG",
       "size": 1846,
       "src": "assets/icons/quality/ic_public_alert2_textured.svg"
      },
      {
       "name": "ic_public_alert_textured",
       "type": "SVG",
       "size": 1841,
       "src": "assets/icons/quality/ic_public_alert_textured.svg"
      },
      {
       "name": "ic_public_audio_file_textured",
       "type": "SVG",
       "size": 4174,
       "src": "assets/icons/quality/ic_public_audio_file_textured.svg"
      },
      {
       "name": "ic_public_bell_clock_material",
       "type": "SVG",
       "size": 3045,
       "src": "assets/icons/quality/ic_public_bell_clock_material.svg"
      },
      {
       "name": "ic_public_broom1",
       "type": "SVG",
       "size": 2700,
       "src": "assets/icons/quality/ic_public_broom1.svg"
      },
      {
       "name": "ic_public_camera1",
       "type": "SVG",
       "size": 1862,
       "src": "assets/icons/quality/ic_public_camera1.svg"
      },
      {
       "name": "ic_public_camera_dome1",
       "type": "SVG",
       "size": 2185,
       "src": "assets/icons/quality/ic_public_camera_dome1.svg"
      },
      {
       "name": "ic_public_clock_globe1",
       "type": "SVG",
       "size": 4229,
       "src": "assets/icons/quality/ic_public_clock_globe1.svg"
      },
      {
       "name": "ic_public_compressed_file_textured",
       "type": "SVG",
       "size": 2422,
       "src": "assets/icons/quality/ic_public_compressed_file_textured.svg"
      },
      {
       "name": "ic_public_config_guide",
       "type": "SVG",
       "size": 5182,
       "src": "assets/icons/quality/ic_public_config_guide.svg"
      },
      {
       "name": "ic_public_disconnect_cloudsop",
       "type": "SVG",
       "size": 2783,
       "src": "assets/icons/quality/ic_public_disconnect_cloudsop.svg"
      },
      {
       "name": "ic_public_dumping",
       "type": "SVG",
       "size": 3526,
       "src": "assets/icons/quality/ic_public_dumping.svg"
      },
      {
       "name": "ic_public_excle_file_textured",
       "type": "SVG",
       "size": 2999,
       "src": "assets/icons/quality/ic_public_excle_file_textured.svg"
      },
      {
       "name": "ic_public_folder_file_textured",
       "type": "SVG",
       "size": 4065,
       "src": "assets/icons/quality/ic_public_folder_file_textured.svg"
      },
      {
       "name": "ic_public_ic_setting_vtep",
       "type": "SVG",
       "size": 3523,
       "src": "assets/icons/quality/ic_public_ic_setting_vtep.svg"
      },
      {
       "name": "ic_public_infotex_textured",
       "type": "SVG",
       "size": 1663,
       "src": "assets/icons/quality/ic_public_infotex_textured.svg"
      },
      {
       "name": "ic_public_mappin_on_map1",
       "type": "SVG",
       "size": 5066,
       "src": "assets/icons/quality/ic_public_mappin_on_map1.svg"
      },
      {
       "name": "ic_public_navigate_application_view",
       "type": "SVG",
       "size": 3665,
       "src": "assets/icons/quality/ic_public_navigate_application_view.svg"
      },
      {
       "name": "ic_public_pdf_file_textured",
       "type": "SVG",
       "size": 4002,
       "src": "assets/icons/quality/ic_public_pdf_file_textured.svg"
      },
      {
       "name": "ic_public_phone_gear1",
       "type": "SVG",
       "size": 3413,
       "src": "assets/icons/quality/ic_public_phone_gear1.svg"
      },
      {
       "name": "ic_public_pic_file_textured",
       "type": "SVG",
       "size": 3691,
       "src": "assets/icons/quality/ic_public_pic_file_textured.svg"
      },
      {
       "name": "ic_public_power_point_file_textured",
       "type": "SVG",
       "size": 3367,
       "src": "assets/icons/quality/ic_public_power_point_file_textured.svg"
      },
      {
       "name": "ic_public_redcross1",
       "type": "SVG",
       "size": 2033,
       "src": "assets/icons/quality/ic_public_redcross1.svg"
      },
      {
       "name": "ic_public_safety_management",
       "type": "SVG",
       "size": 3938,
       "src": "assets/icons/quality/ic_public_safety_management.svg"
      },
      {
       "name": "ic_public_screen_wifi1",
       "type": "SVG",
       "size": 2847,
       "src": "assets/icons/quality/ic_public_screen_wifi1.svg"
      },
      {
       "name": "ic_public_setting_cloudsop1",
       "type": "SVG",
       "size": 4333,
       "src": "assets/icons/quality/ic_public_setting_cloudsop1.svg"
      },
      {
       "name": "ic_public_setting_material",
       "type": "SVG",
       "size": 2868,
       "src": "assets/icons/quality/ic_public_setting_material.svg"
      },
      {
       "name": "ic_public_setting_vds",
       "type": "SVG",
       "size": 3838,
       "src": "assets/icons/quality/ic_public_setting_vds.svg"
      },
      {
       "name": "ic_public_show_thumbnails",
       "type": "SVG",
       "size": 3535,
       "src": "assets/icons/quality/ic_public_show_thumbnails.svg"
      },
      {
       "name": "ic_public_stop_repair",
       "type": "SVG",
       "size": 3581,
       "src": "assets/icons/quality/ic_public_stop_repair.svg"
      },
      {
       "name": "ic_public_suitcase_magnifyingglass2",
       "type": "SVG",
       "size": 4994,
       "src": "assets/icons/quality/ic_public_suitcase_magnifyingglass2.svg"
      },
      {
       "name": "ic_public_synchronize",
       "type": "SVG",
       "size": 4863,
       "src": "assets/icons/quality/ic_public_synchronize.svg"
      },
      {
       "name": "ic_public_trash_material",
       "type": "SVG",
       "size": 2606,
       "src": "assets/icons/quality/ic_public_trash_material.svg"
      },
      {
       "name": "ic_public_unknown_file_textured",
       "type": "SVG",
       "size": 4840,
       "src": "assets/icons/quality/ic_public_unknown_file_textured.svg"
      },
      {
       "name": "ic_public_video_file_textured",
       "type": "SVG",
       "size": 4153,
       "src": "assets/icons/quality/ic_public_video_file_textured.svg"
      },
      {
       "name": "ic_public_warning_textured",
       "type": "SVG",
       "size": 1484,
       "src": "assets/icons/quality/ic_public_warning_textured.svg"
      },
      {
       "name": "ic_public_word_file_textured",
       "type": "SVG",
       "size": 2466,
       "src": "assets/icons/quality/ic_public_word_file_textured.svg"
      },
      {
       "name": "ic_public_workflow_file_textured",
       "type": "SVG",
       "size": 4962,
       "src": "assets/icons/quality/ic_public_workflow_file_textured.svg"
      }
     ]
    }
   ]
  }
 ]
}
```

## 布局 Pattern {#patterns}

> 未定义：规范 Skill 中没有提取到这部分内容。

## Pixso 映射 {#mapping}

1 个组件登记了 Pixso 设计组件，其中 0 个有组件链接（已关联），其余显示为未关联。

```json design
{
 "button": {
  "sample": true,
  "pixso": {
   "library": "H Design 组件库",
   "component": "按钮 Button",
   "status": "aligned",
   "props": {
    "type": {
     "label": "类型",
     "values": {
      "Emphasized": "强调",
      "Normal": "普通",
      "Warning": "警示",
      "Text": "文本",
      "Selected": "选中",
      "Unselected": "未选中"
     }
    },
    "size": {
     "label": "尺寸",
     "values": {
      "Medium": "中",
      "Small": "小"
     }
    },
    "state": {
     "label": "状态",
     "values": {
      "Enabled": "默认",
      "Hover": "悬停",
      "Pressed": "按下",
      "Focus": "聚焦",
      "Disabled": "禁用",
      "Loading": "加载中"
     }
    }
   }
  },
  "code": {
   "name": "Button",
   "importLine": "import { Button } from '@h-design/react';",
   "path": "src/components/Button/button.tsx",
   "status": "aligned",
   "props": {
    "type": {
     "prop": "variant",
     "values": {
      "Emphasized": "emphasized",
      "Normal": "normal",
      "Warning": "warning",
      "Text": "text",
      "Selected": "selected",
      "Unselected": "unselected"
     }
    },
    "size": {
     "prop": "size",
     "values": {
      "Medium": "md",
      "Small": "sm"
     }
    },
    "state": {
     "values": {
      "Disabled": "disabled",
      "Loading": "loading"
     }
    }
   }
  },
  "rows": [
   [
    "背景",
    "comp-background-tertiary",
    "comp/background/tertiary",
    "--harmony-comp-background-tertiary",
    "#000000 · 5%"
   ],
   [
    "文字",
    "font-emphasize",
    "font/emphasize",
    "--harmony-font-emphasize",
    "#0A59F7"
   ],
   [
    "圆角",
    "radius-button-full",
    "radius/button/full",
    "--radius-button-full",
    "20px"
   ],
   [
    "字体",
    "subtitle_m_medium",
    "font/subtitle/m",
    "--harmony-font-size-subtitle-m",
    "16px / 500"
   ]
  ]
 }
}
```
