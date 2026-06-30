// frontend/js/auth.js

const CLERK_PUBLISHABLE_KEY = "pk_test_ZGl2aW5lLXdhbGxleWUtMzYuY2xlcmsuYWNjb3VudHMuZGV2JA"; 

const API_BASE = "http://127.0.0.1:8000";

// ─────────────────────────────────────────────
// Load Clerk and initialize
// ─────────────────────────────────────────────
async function loadClerk() {
  // Return cached instance if already loaded
  if (window.__clerk) return window.__clerk;

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");

    // Use the older stable CDN format that exposes window.Clerk as constructor
    script.setAttribute("data-clerk-publishable-key", CLERK_PUBLISHABLE_KEY);
    script.src = "https://cdn.jsdelivr.net/npm/@clerk/clerk-js@5/dist/clerk.browser.js";
    script.crossOrigin = "anonymous";

    script.addEventListener("load", async () => {
      try {
        // In Clerk JS v5, Clerk is exposed directly on window after script loads
        // We just need to call load() on it
        await window.Clerk.load();
        window.__clerk = window.Clerk;
        resolve(window.__clerk);
      } catch (err) {
        reject(err);
      }
    });

    script.addEventListener("error", () => {
      reject(new Error("Failed to load Clerk script"));
    });

    document.head.appendChild(script);
  });
}

// ─────────────────────────────────────────────
// Get JWT token for backend requests
// ─────────────────────────────────────────────
async function getToken() {
  const clerk = window.__clerk;
  if (!clerk || !clerk.session) return null;
  return await clerk.session.getToken();
}

// ─────────────────────────────────────────────
// Protect chat page — redirect if not logged in
// ─────────────────────────────────────────────
async function requireAuth() {
  const clerk = await loadClerk();
  if (!clerk.user) {
    window.location.href = "index.html";
    return null;
  }
  await syncUserToBackend(clerk);
  return clerk.user;
}

// ─────────────────────────────────────────────
// Sync user to our Supabase database
// ─────────────────────────────────────────────
async function syncUserToBackend(clerk) {
  try {
    const token = await getToken();
    if (!token) return;
    await fetch(`${API_BASE}/auth/sync`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
  } catch (err) {
    console.warn("User sync failed (non-critical):", err.message);
  }
}

// ─────────────────────────────────────────────
// Landing page — show Sign In / Sign Up buttons
// ─────────────────────────────────────────────
async function initLandingPage() {
  try {
    const clerk = await loadClerk();

    const signInBtn  = document.getElementById("clerkSignIn");
    const signUpBtn  = document.getElementById("clerkSignUp");
    const userWidget = document.getElementById("clerkUserWidget");

    if (clerk.user) {
      // Already logged in
      signInBtn?.classList.add("d-none");
      signUpBtn?.classList.add("d-none");
      userWidget?.classList.remove("d-none");

      const mountPoint = document.getElementById("clerkUserButtonMount");
      if (mountPoint) clerk.mountUserButton(mountPoint);
    }

    // Sign In button
    signInBtn?.addEventListener("click", () => {
      clerk.openSignIn({
        afterSignInUrl: "chat.html",
        afterSignUpUrl: "chat.html",
      });
    });

    // Sign Up button
    signUpBtn?.addEventListener("click", () => {
      clerk.openSignUp({
        afterSignInUrl: "chat.html",
        afterSignUpUrl: "chat.html",
      });
    });

    // Hero / CTA buttons
    document.getElementById("heroSignUp")?.addEventListener("click", () => {
      clerk.openSignUp({ afterSignUpUrl: "chat.html", afterSignInUrl: "chat.html" });
    });
    document.getElementById("ctaSignUp")?.addEventListener("click", () => {
      clerk.openSignUp({ afterSignUpUrl: "chat.html", afterSignInUrl: "chat.html" });
    });

  } catch (err) {
    console.error("Clerk failed to load:", err.message);
  }
}

// ─────────────────────────────────────────────
// Chat page — check auth + fill user info
// ─────────────────────────────────────────────
async function initChatPage() {
  try {
    const user = await requireAuth();
    if (!user) return;

    const fullName = [user.firstName, user.lastName].filter(Boolean).join(" ") || "User";
    const email    = user.primaryEmailAddress?.emailAddress || "";
    const initial  = fullName.charAt(0).toUpperCase();

    const nameEl    = document.getElementById("sidebarUserName");
    const emailEl   = document.getElementById("sidebarUserEmail");
    const initEl    = document.getElementById("sidebarUserInitial");
    const logoutBtn = document.getElementById("logoutBtn");

    if (nameEl)  nameEl.textContent  = fullName;
    if (emailEl) emailEl.textContent = email;
    if (initEl)  initEl.textContent  = initial;

    logoutBtn?.addEventListener("click", async () => {
      await window.__clerk.signOut();
      window.location.href = "index.html";
    });

  } catch (err) {
    console.error("Auth error:", err.message);
    window.location.href = "index.html";
  }
}

// ─────────────────────────────────────────────
// Authenticated fetch helper for backend calls
// ─────────────────────────────────────────────
async function authFetch(path, options = {}) {
  const token = await getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Expose globally
window.authFetch       = authFetch;
window.getToken        = getToken;
window.requireAuth     = requireAuth;
window.initChatPage    = initChatPage;
window.initLandingPage = initLandingPage;