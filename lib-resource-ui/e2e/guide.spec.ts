import { test, expect, type Page } from '@playwright/test'

async function injectLogin(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('userInfo', JSON.stringify({
      account: 'admin',
      nickName: '测试管理员',
      dept: [], deptCode: [], roleID: '1', roles: [],
      uid: 1, userID: '1',
    }))
  })
}

test.describe('首页使用手册', () => {
  test.beforeEach(async ({ page }) => {
    await injectLogin(page)
  })

  test('首页加载并渲染 Markdown 内容', async ({ page }) => {
    await page.goto('/#/home')
    await expect(page.locator('.guide-body')).toBeVisible()
    await expect(page.locator('.guide-body h1')).toContainText('使用手册')
  })

  test('标题有 id 属性用于锚点定位', async ({ page }) => {
    await page.goto('/#/home')
    // 中文 id 需要用属性选择器
    const h2 = page.locator('.guide-body h2[id="1-系统简介"]')
    await expect(h2).toBeVisible()
  })

  test('点击目录锚点链接后页面滚动，路由不被破坏', async ({ page }) => {
    await page.goto('/#/home')
    await expect(page.locator('.guide-body')).toBeVisible()

    // 记录初始滚动位置
    const scrollBefore = await page.evaluate(() => {
      return document.querySelector('.guide-body')?.parentElement?.scrollTop ?? 0
    })

    // 点击第一个目录链接（指向 #1-系统简介）
    const firstLink = page.locator('.guide-body a[href^="#1-"]').first()
    await firstLink.click()

    // 等待滚动
    await page.waitForTimeout(800)

    // 验证滚动位置变化
    const scrollAfter = await page.evaluate(() => {
      return document.querySelector('.guide-body')?.parentElement?.scrollTop ?? 0
    })
    expect(scrollAfter).toBeGreaterThan(0)

    // 验证路由 hash 未被破坏（仍是 #/home）
    await expect(page).toHaveURL(/#\/home$/)
  })

  test('多个锚点链接均可滚动定位', async ({ page }) => {
    await page.goto('/#/home')
    await expect(page.locator('.guide-body')).toBeVisible()

    const links = page.locator('.guide-body a[href^="#"]')
    const count = await links.count()

    // 测试前 5 个链接
    for (let i = 0; i < Math.min(5, count); i++) {
      await links.nth(i).click()
      await page.waitForTimeout(600)

      const scrollTop = await page.evaluate(() => {
        return document.querySelector('.guide-body')?.parentElement?.scrollTop ?? 0
      })
      expect(scrollTop).toBeGreaterThan(0)

      // 路由始终不变
      await expect(page).toHaveURL(/#\/home$/)
    }
  })

  test('点击正文中"附录 A"链接可跳转', async ({ page }) => {
    await page.goto('/#/home')
    await expect(page.locator('.guide-body')).toBeVisible()

    // 正文中的链接是最后一个匹配项（目录中的在前面）
    const links = page.locator('.guide-body a', { hasText: '附录 A' })
    const count = await links.count()
    const link = links.nth(count - 1)
    await link.click()
    await page.waitForTimeout(800)

    // 验证附录标题进入了视口
    const headingVisible = await page.evaluate(() => {
      const headings = document.querySelectorAll('.guide-body h2')
      const heading = Array.from(headings).find(h => h.textContent?.includes('附录 A：ZIP'))
      if (!heading) return false
      const rect = heading.getBoundingClientRect()
      return rect.top >= 0 && rect.top < window.innerHeight
    })
    expect(headingVisible).toBe(true)
    await expect(page).toHaveURL(/#\/home$/)
  })
})
