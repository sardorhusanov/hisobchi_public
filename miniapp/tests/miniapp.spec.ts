import { test, expect } from "@playwright/test";

test("real API flows and mobile layouts", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("https://telegram.org/js/telegram-web-app.js", (route) =>
    route.fulfill({ body: "" }),
  );
  await page.addInitScript(() => {
    const listeners: Record<string, () => void> = {};
    window.Telegram = {
      WebApp: {
        initData: "",
        colorScheme: "light",
        ready() {},
        expand() {},
        onEvent(event, cb) {
          listeners[event] = cb;
        },
        offEvent(event) {
          delete listeners[event];
        },
        BackButton: { show() {}, hide() {}, onClick() {}, offClick() {} },
      },
    };
  });
  const suffix = Date.now().toString().slice(-6);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Salom/ })).toBeVisible();
  expect(
    await page.evaluate(() =>
      performance
        .getEntriesByType("resource")
        .some((entry) => entry.name.includes("FinanceCharts")),
    ),
  ).toBe(false);
  await page.goto("/workers");
  await page.getByRole("button", { name: "Qo'shish", exact: true }).click();
  await page.getByLabel("Ism", { exact: true }).fill("Ali " + suffix);
  await page.getByLabel("Oylik, so'm", { exact: true }).fill("6 000 000");
  await page.getByRole("button", { name: "Saqlash", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("link")
    .filter({
      has: page.getByRole("heading", { name: "Ali " + suffix, exact: true }),
    })
    .click();
  await expect(
    page.getByRole("heading", { name: "Ali " + suffix, exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Avans berish", exact: true }).click();
  await page.getByLabel("Summa, so'm", { exact: true }).fill("50 000");
  await page.getByRole("button", { name: "Saqlash", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.goto("/attendance");
  await page
    .getByRole("button", { name: "Hammasi 1 kun", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Davomatni saqlash", exact: true })
    .click();
  await expect(page.getByText("✓ Davomat saqlandi.")).toBeVisible();
  await page.goto("/partners");
  await page.getByRole("button", { name: "Qo'shish", exact: true }).click();
  await page.getByLabel("Ism", { exact: true }).fill("Hamkor " + suffix);
  await expect(page.getByLabel("Oylik, so'm")).toHaveCount(0);
  await page.getByRole("button", { name: "Saqlash", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.goto("/projects");
  await page.getByRole("button", { name: "Qo'shish", exact: true }).click();
  await page
    .getByLabel("Loyiha nomi", { exact: true })
    .fill("Yangi uy " + suffix);
  await page.getByRole("button", { name: "Saqlash", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("link")
    .filter({
      has: page.getByRole("heading", {
        name: "Yangi uy " + suffix,
        exact: true,
      }),
    })
    .click();
  await page.getByRole("button", { name: "Pul tushumi", exact: true }).click();
  await page.getByLabel("Summa, so'm", { exact: true }).fill("10,000,000");
  await page.getByRole("button", { name: "Saqlash", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("button", { name: "Xarajat", exact: true }).click();
  await page.getByLabel("Summa, so'm", { exact: true }).fill("500 000");
  await page.getByLabel(/Izoh/).fill("Yoqilg'i");
  await page.getByRole("button", { name: "Saqlash", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByText("9 500 000 so'm", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Hisobot", exact: true }).click();
  await expect(page.getByText("Yoqilg'i", { exact: true })).toBeVisible();
  await page.goto("/finance");
  await expect(
    page.getByRole("heading", { name: "Pul harakati", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Chiqim tarkibi", exact: true }),
  ).toBeVisible();
  await page.goto("/settings");
  await page.getByLabel("Rang mavzusi").selectOption("dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByLabel("Rang mavzusi").selectOption("light");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByLabel("Rang mavzusi").selectOption("telegram");
  for (const width of [320, 360, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    for (const route of [
      "/",
      "/attendance",
      "/workers",
      "/partners",
      "/salary",
      "/advances",
      "/projects",
      "/finance",
      "/reports",
      "/more",
      "/settings",
    ]) {
      await page.goto(route);
      await expect(page.locator("main h1")).toBeVisible();
      await expect(page.locator('[aria-label="Yuklanmoqda"]')).toHaveCount(0);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
        `${route} at ${width}`,
      ).toBeTruthy();
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Pul harakati", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/dashboard-390.png",
    fullPage: true,
  });
  await page.evaluate(() => {
    document.documentElement.dataset.theme = "dark";
  });
  await page.screenshot({
    path: "test-results/dashboard-dark-390.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
