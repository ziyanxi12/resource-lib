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

test.describe('导航栏路由', () => {
  test.beforeEach(async ({ page }) => {
    await injectLogin(page)
  })

  test('根路径 / 重定向到首页 /home', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/#\/home$/)
    await expect(page.locator('.guide-body')).toBeVisible()
  })

  test('点击"数据总览"跳转到 /overview，不跳首页', async ({ page }) => {
    await page.goto('/#/home')
    await expect(page.locator('.guide-body')).toBeVisible()

    // 点击数据总览导航项
    const navItem = page.locator('aside nav').getByText('数据总览')
    await navItem.click()

    // 验证 URL 是 /overview 而不是 /home
    await expect(page).toHaveURL(/#\/overview$/)

    // 验证首页内容消失
    await expect(page.locator('.guide-body')).not.toBeVisible()
  })

  test('点击"组件"跳转到 /component', async ({ page }) => {
    await page.goto('/#/home')
    await page.locator('aside nav').getByText('组件').click()
    await expect(page).toHaveURL(/#\/component$/)
  })

  test('点击"图标"跳转到 /icon', async ({ page }) => {
    await page.goto('/#/home')
    await page.locator('aside nav').getByText('图标').click()
    await expect(page).toHaveURL(/#\/icon$/)
  })

  test('从数据总览返回首页', async ({ page }) => {
    await page.goto('/#/overview')
    await page.locator('aside nav').getByText('首页').click()
    await expect(page).toHaveURL(/#\/home$/)
    await expect(page.locator('.guide-body')).toBeVisible()
  })
})
