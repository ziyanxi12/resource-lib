#!/usr/bin/env node

const fs = require('fs')
const path = require('path')

const VALID_TYPES = ['component', 'icon', 'illus', 'template', 'image', 'file']
const MAX_UPLOAD_COUNT = 500
const MAX_ZIP_SIZE_MB = 100

function validateConfig(config, zipFiles = null) {
  const errors = []

  if (!config.meta) {
    errors.push({ field: 'meta', message: '缺少 meta 字段' })
    return errors
  }

  if (!VALID_TYPES.includes(config.meta.type)) {
    errors.push({
      field: 'meta.type',
      message: `type 必须是 ${VALID_TYPES.join('/')} 之一，当前为: ${config.meta.type}`,
    })
  }

  if (typeof config.meta.source_id !== 'number' || config.meta.source_id <= 0) {
    errors.push({
      field: 'meta.source_id',
      message: 'source_id 必须为正整数',
    })
  }

  if (!Array.isArray(config.data)) {
    errors.push({ field: 'data', message: 'data 必须为数组' })
    return errors
  }

  if (config.data.length === 0) {
    errors.push({ field: 'data', message: 'data 数组不能为空' })
    return errors
  }

  // 校验条目数量
  if (config.data.length > MAX_UPLOAD_COUNT) {
    errors.push({
      field: 'data',
      message: `单次上传最多 ${MAX_UPLOAD_COUNT} 条，当前 ${config.data.length} 条`,
    })
  }

  config.data.forEach((item, index) => {
    const prefix = `[第${index + 1}条]`

    if (!item.name || typeof item.name !== 'string' || !item.name.trim()) {
      errors.push({ index, field: 'name', message: `${prefix} name: 名称不能为空` })
    }

    if (item.group_id === undefined || item.group_id === null) {
      errors.push({ index, field: 'group_id', message: `${prefix} group_id: 分组ID不能为空` })
    }

    if (typeof item.width !== 'number' || item.width <= 0) {
      errors.push({ index, field: 'width', message: `${prefix} width: 宽度必须为正数` })
    }

    if (typeof item.height !== 'number' || item.height <= 0) {
      errors.push({ index, field: 'height', message: `${prefix} height: 高度必须为正数` })
    }

    const hasFilePath = item.file_path && typeof item.file_path === 'string' && item.file_path.trim()
    const hasFileUrl = item.file_url && typeof item.file_url === 'string' && item.file_url.trim()
    if (!hasFilePath && !hasFileUrl) {
      errors.push({
        index,
        field: 'file',
        message: `${prefix} file_path/file_url: 文件路径或链接至少填一个`,
      })
    }

    if (!item.thumbnail_path || typeof item.thumbnail_path !== 'string' || !item.thumbnail_path.trim()) {
      errors.push({ index, field: 'thumbnail_path', message: `${prefix} thumbnail_path: 缩略图路径不能为空` })
    }

    if (item.raw_data !== undefined) {
      if (typeof item.raw_data !== 'object' || item.raw_data === null || Array.isArray(item.raw_data)) {
        errors.push({ index, field: 'raw_data', message: `${prefix} raw_data: 必须为对象` })
      }
    }

    if (zipFiles) {
      if (hasFilePath && !zipFiles.includes(item.file_path)) {
        errors.push({
          index,
          field: 'file_path',
          message: `${prefix} file_path: 文件不存在于 ZIP 包中 (${item.file_path})`,
        })
      }
      if (item.thumbnail_path && item.thumbnail_path.trim() && !zipFiles.includes(item.thumbnail_path)) {
        errors.push({
          index,
          field: 'thumbnail_path',
          message: `${prefix} thumbnail_path: 文件不存在于 ZIP 包中 (${item.thumbnail_path})`,
        })
      }
    }
  })

  return errors
}

function formatErrors(errors) {
  return errors.map((e) => e.message).join('\n')
}

async function validateJson(jsonPath) {
  if (!fs.existsSync(jsonPath)) {
    console.error(`✗ 文件不存在: ${jsonPath}`)
    process.exit(1)
  }

  let config
  try {
    const content = fs.readFileSync(jsonPath, 'utf-8')
    config = JSON.parse(content)
  } catch (e) {
    console.error(`✗ JSON 解析失败: ${e.message}`)
    process.exit(1)
  }

  const errors = validateConfig(config)

  if (errors.length > 0) {
    console.error('✗ 验证失败\n')
    console.error(formatErrors(errors))
    console.error(`\n共 ${errors.length} 条错误`)
    process.exit(1)
  }

  console.log('✓ config.json 格式正确')
  console.log(`✓ 共 ${config.data.length} 条记录，全部通过验证`)
}

async function validateZip(zipPath, JSZip) {
  if (!fs.existsSync(zipPath)) {
    console.error(`✗ 文件不存在: ${zipPath}`)
    process.exit(1)
  }

  if (path.extname(zipPath).toLowerCase() !== '.zip') {
    console.error(`✗ 文件不是 ZIP 格式: ${zipPath}`)
    process.exit(1)
  }

  // 校验 ZIP 包大小
  const stats = fs.statSync(zipPath)
  const zipSizeMB = stats.size / 1024 / 1024
  if (zipSizeMB > MAX_ZIP_SIZE_MB) {
    console.error(`✗ ZIP 包大小超过限制 (${MAX_ZIP_SIZE_MB}MB)，当前 ${zipSizeMB.toFixed(1)}MB`)
    process.exit(1)
  }

  const zipBuffer = fs.readFileSync(zipPath)
  let zip
  try {
    zip = await JSZip.loadAsync(zipBuffer)
  } catch (e) {
    console.error(`✗ ZIP 解压失败: ${e.message}`)
    process.exit(1)
  }

  const configFile = zip.file('config.json')
  if (!configFile) {
    console.error('✗ ZIP 包中缺少 config.json 文件')
    process.exit(1)
  }

  let config
  try {
    const configText = await configFile.async('string')
    config = JSON.parse(configText)
  } catch (e) {
    console.error(`✗ config.json 解析失败: ${e.message}`)
    process.exit(1)
  }

  const zipFiles = Object.keys(zip.files).filter((f) => !zip.files[f].dir)

  const errors = validateConfig(config, zipFiles)

  if (errors.length > 0) {
    console.error('✗ 验证失败\n')
    console.error(formatErrors(errors))
    console.error(`\n共 ${errors.length} 条错误`)
    process.exit(1)
  }

  console.log('✓ ZIP 包大小正确')
  console.log('✓ ZIP 包结构正确')
  console.log('✓ config.json 格式正确')
  console.log(`✓ 共 ${config.data.length} 条记录，全部通过验证`)
}

async function main() {
  const args = process.argv.slice(2)

  if (args.length < 2) {
    console.log('用法:')
    console.log('  node validate.bundle.js --json <config.json路径>')
    console.log('  node validate.bundle.js --zip <zip包路径>')
    process.exit(1)
  }

  const mode = args[0]
  const target = args[1]

  if (mode === '--json') {
    await validateJson(target)
  } else if (mode === '--zip') {
    const JSZip = require('jszip')
    await validateZip(target, JSZip)
  } else {
    console.error(`未知模式: ${mode}`)
    console.error('请使用 --json 或 --zip')
    process.exit(1)
  }
}

main().catch((e) => {
  console.error('✗ 执行失败:', e.message)
  process.exit(1)
})