export type E2ERole = "admin" | "teacher" | "student";

export type E2ECredentials = {
  email: string;
  password: string;
};

const LOCAL_FRONTEND_URL = "http://127.0.0.1:3000";
const LOCAL_API_URL = "http://127.0.0.1:8000/api";

function env(name: string, fallback = "") {
  return process.env[name] || fallback;
}

function normalizeUrl(url: string) {
  return url.replace(/\/+$/, "");
}

export const frontendBaseUrl = normalizeUrl(
  env("E2E_FRONTEND_BASE_URL", env("E2E_BASE_URL", LOCAL_FRONTEND_URL))
);

export const backendApiUrl = normalizeUrl(
  env("E2E_BACKEND_API_URL", env("E2E_API_BASE_URL", LOCAL_API_URL))
);

export const allowProduction =
  env("E2E_ALLOW_PRODUCTION", "false").toLowerCase() === "true";

export const credentials: Record<E2ERole, E2ECredentials> = {
  admin: {
    email: env("E2E_ADMIN_EMAIL", "admin@masterygrid.demo"),
    password: env("E2E_ADMIN_PASSWORD", "Password123!")
  },
  teacher: {
    email: env("E2E_TEACHER_EMAIL", "teacher@masterygrid.demo"),
    password: env("E2E_TEACHER_PASSWORD", "Password123!")
  },
  student: {
    email: env("E2E_STUDENT_EMAIL", "student1@masterygrid.demo"),
    password: env("E2E_STUDENT_PASSWORD", "Password123!")
  }
};

export const testPassword = env("E2E_TEST_PASSWORD", "Password123!");

export function looksLikeLocalUrl(url: string) {
  try {
    const hostname = new URL(url).hostname;
    return ["localhost", "127.0.0.1", "0.0.0.0"].includes(hostname);
  } catch {
    return false;
  }
}

export function looksLikeProductionUrl(url: string) {
  if (looksLikeLocalUrl(url)) {
    return false;
  }

  try {
    const hostname = new URL(url).hostname;
    return (
      hostname.includes("vercel.app") ||
      hostname.includes("onrender.com") ||
      hostname.includes("masterygrid")
    );
  } catch {
    return false;
  }
}

export function assertProductionAllowedForMutatingTests() {
  if (
    !allowProduction &&
    (looksLikeProductionUrl(frontendBaseUrl) || looksLikeProductionUrl(backendApiUrl))
  ) {
    throw new Error(
      "Refusing to run mutating E2E tests against a production-like URL. " +
        "Use staging/demo data or set E2E_ALLOW_PRODUCTION=true intentionally."
    );
  }
}
