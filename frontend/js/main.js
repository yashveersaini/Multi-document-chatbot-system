// ─── SIDEBAR TOGGLE (mobile) ───
const sidebar      = document.getElementById("sidebar");
const sidebarOpen  = document.getElementById("sidebarOpen");
const sidebarClose = document.getElementById("sidebarClose");

sidebarOpen?.addEventListener("click",  () => sidebar?.classList.add("open"));
sidebarClose?.addEventListener("click", () => sidebar?.classList.remove("open"));

document.addEventListener("click", (e) => {
  if (sidebar?.classList.contains("open")) {
    if (!sidebar.contains(e.target) && e.target !== sidebarOpen) {
      sidebar.classList.remove("open");
    }
  }
});

// ─── DOCS PANEL ───
const docsPanel     = document.getElementById("docsPanel");
const viewDocsBtn   = document.getElementById("viewDocsBtn");
const closeDocsBtn  = document.getElementById("closeDocs");
const panelBackdrop = document.getElementById("panelBackdrop");

function openDocsPanel()  {
  docsPanel?.classList.add("open");
  panelBackdrop?.classList.remove("d-none");
}
function closeDocsPanel() {
  docsPanel?.classList.remove("open");
  panelBackdrop?.classList.add("d-none");
}

viewDocsBtn?.addEventListener("click",  openDocsPanel);
closeDocsBtn?.addEventListener("click", closeDocsPanel);
panelBackdrop?.addEventListener("click", closeDocsPanel);

// ─── TEXTAREA AUTO-RESIZE ───
const messageInput = document.getElementById("messageInput");
const sendBtn      = document.getElementById("sendBtn");

messageInput?.addEventListener("input", function () {
  this.style.height = "auto";
  this.style.height = Math.min(this.scrollHeight, 140) + "px";
});

messageInput?.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

function handleSend() {
  const text = messageInput?.value.trim();
  if (!text) return;
  console.log("Send (Day 15):", text);
}

sendBtn?.addEventListener("click", handleSend);

// ─── TOAST ───
function showToast(message, type = "default") {
  const toastEl  = document.getElementById("appToast");
  const toastMsg = document.getElementById("toastMessage");
  if (!toastEl || !toastMsg) return;

  toastMsg.textContent = message;
  toastEl.classList.remove("bg-success", "bg-danger");
  if (type === "success") toastEl.classList.add("bg-success");
  if (type === "danger")  toastEl.classList.add("bg-danger");

  new bootstrap.Toast(toastEl, { delay: 3500 }).show();
}
window.showToast = showToast;

console.log("PDFChat UI loaded ✓");