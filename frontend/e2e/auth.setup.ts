import { test as setup, expect } from "@playwright/test";

const TEST_USER = {
  email: "e2e-test@opensns.dev",
  password: "TestPassword123!",
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const AUTH_FILE = "playwright/.auth/user.json";

setup("authenticate", async ({ page }) => {
  let token: string | null = null;

  try {
    const loginResponse = await page.request.post(`${API_URL}/auth/login`, {
      form: {
        username: TEST_USER.email,
        password: TEST_USER.password,
      },
    });

    if (loginResponse.ok()) {
      const data = await loginResponse.json();
      token = data.access_token;
    }
  } catch {
    // Login failed, try to register
  }

  if (!token) {
    try {
      const registerResponse = await page.request.post(
        `${API_URL}/auth/register`,
        {
          data: {
            email: TEST_USER.email,
            password: TEST_USER.password,
          },
        }
      );

      if (!registerResponse.ok()) {
        const error = await registerResponse.text();
        if (!error.includes("already registered")) {
          throw new Error(`Failed to register: ${error}`);
        }
      }

      const loginResponse = await page.request.post(`${API_URL}/auth/login`, {
        form: {
          username: TEST_USER.email,
          password: TEST_USER.password,
        },
      });

      expect(loginResponse.ok()).toBeTruthy();
      const data = await loginResponse.json();
      token = data.access_token;
    } catch (error) {
      throw new Error(`Auth setup failed: ${error}`);
    }
  }

  expect(token).toBeTruthy();

  await page.goto("/");
  await page.evaluate((t) => {
    localStorage.setItem("token", t);
  }, token!);

  await page.context().storageState({ path: AUTH_FILE });
});
