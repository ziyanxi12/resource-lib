---
name: split-html
description: "Use when the user wants to split an HTML page into block-level chunks based on x/y/w/h coordinates. Triggers on keywords like 拆分HTML, 区块提取, split html, extract blocks, 提取区块. Input: HTML file path + JSON coordinates array. Output: standalone HTML files per block."
---

# HTML 区块拆分 Skill

## 功能

将一个完整的 HTML 页面，根据 JSON 坐标（x/y/w/h）拆分成多个独立的区块 HTML 文件。

## 输入

1. **HTML 文件路径**（必填）：要拆分的 HTML 文件
2. **JSON 坐标数组**（必填）：每个区块的坐标和名称
3. **输出目录**（可选，默认 `./output`）

JSON 格式：
```json
[
  {"x": 0, "y": 0, "w": 1920, "h": 200, "name": "导航栏"},
  {"x": 0, "y": 200, "w": 1920, "h": 800, "name": "Hero区域"}
]
```

- `x`, `y`, `w`, `h` 为像素坐标，基于 1920×1080 视口
- `name` 为区块名称，用于生成文件名（可选，但建议填写）

## 执行命令

```bash
node .opencode/skills/split-html/split.mjs <html-path> '<json-string|json-file-path>' [output-dir]
```

### 示例

```bash
# 直接传 JSON 字符串
node .opencode/skills/split-html/split.mjs test-html/shop.html '[{"x":0,"y":0,"w":1920,"h":200,"name":"导航栏"},{"x":0,"y":200,"w":1920,"h":800,"name":"块"}]' ./output

# 传 JSON 文件路径
node .opencode/skills/split-html/split.mjs test-html/shop.html coords.json ./output
```

## 工作原理

1. 启动 Puppeteer 无头浏览器，设置视口 1920×1080
2. 加载 HTML 文件，等待页面渲染完成（含 Vue/React 等框架）
3. 对每个 JSON 坐标，遍历 DOM 元素计算重叠面积
4. 评分公式：`score = coverageOfTarget×0.5 + coverageOfElement×0.3 + sizeSimilarity×0.2`
   - 完全在目标框内的元素加分（`covElement >= 0.95` → +0.1）
   - 框顶部中心点探针：`elementFromPoint` 找到语义化标签祖先加分（+0.15）
   - 只占目标区域很小部分的元素惩罚（`covTarget < 0.15` → 降分）
5. 已匹配的元素不会重复使用（`usedElements` 去重）
6. 提取匹配元素的 `outerHTML`，包裹原始页面的样式和脚本
7. 每个区块输出一个独立的 `.html` 文件

## 输出

- 文件命名：`block-{index}-{name}.html`
- 每个文件包含原始页面的所有 `<style>`、`<link>`、`<script>` 引用
- 文件可独立在浏览器中打开渲染

## 依赖

- `puppeteer`：需要已安装（`npm install puppeteer`）

## 注意事项

- 视口固定为 1920×1080，坐标基于此视口
- 页面渲染等待时间为 2 秒（加载完成后）
- Canvas/SVG 内容不含绘制结果（仅含 HTML 结构）
- 匹配失败的区块会在控制台标记 ❌
