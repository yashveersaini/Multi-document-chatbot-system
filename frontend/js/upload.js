let selectedFiles   = [];   // files chosen in the upload modal
let currentDocs     = [];   // documents already uploaded to this chat

// ─────────────────────────────────────────────
// LOAD DOCUMENTS FOR CURRENT CHAT
// Called when user selects a chat (from chat.js)
// ─────────────────────────────────────────────
async function loadDocuments(chatId) {
  if (!chatId) return;

  const docsListEl = document.getElementById("docsList");
  if (docsListEl) {
    docsListEl.innerHTML = `
      <div class="text-center py-4 text-secondary small">
        <div class="spinner-border spinner-border-sm me-2"></div>
        Loading documents...
      </div>
    `;
  }

  try {
    const data = await authFetch(`/chats/${chatId}/documents`);
    currentDocs = data.documents || [];
    renderDocsList();
    updateDocCount(currentDocs.length);
  } catch (err) {
    console.error("Failed to load documents:", err.message);
    if (docsListEl) {
      docsListEl.innerHTML = `
        <div class="text-center py-4 text-secondary small">
          <i class="bi bi-exclamation-circle d-block fs-3 mb-2 text-danger opacity-75"></i>
          Failed to load documents.
        </div>
      `;
    }
  }
}

// ─────────────────────────────────────────────
// RENDER DOCS PANEL LIST
// ─────────────────────────────────────────────
function renderDocsList() {
  const docsListEl = document.getElementById("docsList");
  if (!docsListEl) return;

  if (currentDocs.length === 0) {
    docsListEl.innerHTML = `
      <div class="text-center py-4 text-secondary small">
        <i class="bi bi-file-earmark d-block fs-3 mb-2 opacity-50"></i>
        No documents uploaded yet.
      </div>
    `;
    return;
  }

  docsListEl.innerHTML = currentDocs.map(doc => `
    <div class="doc-item" data-doc-id="${doc.id}">
      <div class="doc-icon">
        <i class="bi bi-file-earmark-pdf-fill text-danger"></i>
      </div>
      <div class="doc-info">
        <div class="doc-name" title="${escapeHtml(doc.filename)}">
          ${escapeHtml(doc.filename)}
        </div>
        <div class="doc-meta">
          ${formatBytes(doc.file_size || 0)}
          ${doc.page_count ? ` · ${doc.page_count} pages` : ""}
          · <span class="${doc.is_processed ? "text-success" : "text-warning"}">
              ${doc.is_processed ? "✓ Indexed" : "⏳ Processing"}
            </span>
        </div>
      </div>
      <button
        class="btn-icon text-danger flex-shrink-0 delete-doc-btn"
        data-doc-id="${doc.id}"
        data-doc-name="${escapeHtml(doc.filename)}"
        title="Remove document"
      >
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `).join("");

  // Wire delete buttons
  docsListEl.querySelectorAll(".delete-doc-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const docId   = btn.dataset.docId;
      const docName = btn.dataset.docName;
      confirmDeleteDocument(docId, docName);
    });
  });
}

// ─────────────────────────────────────────────
// UPDATE DOC COUNT IN TOPBAR
// ─────────────────────────────────────────────
function updateDocCount(count) {
  const el = document.getElementById("chatDocCount");
  if (el) el.textContent = `${count} document${count !== 1 ? "s" : ""}`;
}

// ─────────────────────────────────────────────
// FILE SELECTION — drop zone + browse button
// ─────────────────────────────────────────────
function initUploadModal() {
  const dropZone     = document.getElementById("dropZone");
  const fileInput    = document.getElementById("fileInput");
  const browseBtn    = document.getElementById("browseBtn");
  const clearFilesBtn = document.getElementById("clearFilesBtn");
  const uploadSubmitBtn = document.getElementById("uploadSubmitBtn");

  if (!dropZone) return;

  // Click browse button
  browseBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput?.click();
  });

  // Click anywhere on drop zone
  dropZone.addEventListener("click", () => fileInput?.click());

  // File input change
  fileInput?.addEventListener("change", (e) => {
    addFilesToSelection(Array.from(e.target.files));
    fileInput.value = ""; // reset so same file triggers change again
  });

  // Drag events
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const files = Array.from(e.dataTransfer.files).filter(
      f => f.type === "application/pdf"
    );
    addFilesToSelection(files);
  });

  // Clear all button
  clearFilesBtn?.addEventListener("click", () => {
    selectedFiles = [];
    renderSelectedFiles();
  });

  // Upload button
  uploadSubmitBtn?.addEventListener("click", handleUpload);

  // Reset modal when closed
  document.getElementById("uploadModal")?.addEventListener("hidden.bs.modal", () => {
    selectedFiles = [];
    renderSelectedFiles();
    resetUploadProgress();
  });
}

// ─────────────────────────────────────────────
// ADD FILES TO SELECTION LIST
// ─────────────────────────────────────────────
function addFilesToSelection(newFiles) {
  const MAX_SIZE = 50 * 1024 * 1024; // 50 MB

  newFiles.forEach(file => {
    // Validate type
    if (file.type !== "application/pdf") {
      showToast(`"${file.name}" is not a PDF`, "danger");
      return;
    }
    // Validate size
    if (file.size > MAX_SIZE) {
      showToast(`"${file.name}" exceeds 50 MB`, "danger");
      return;
    }
    // Avoid duplicates
    const alreadyAdded = selectedFiles.some(f => f.name === file.name && f.size === file.size);
    if (alreadyAdded) {
      showToast(`"${file.name}" already selected`, "danger");
      return;
    }

    selectedFiles.push(file);
  });

  renderSelectedFiles();
}

// ─────────────────────────────────────────────
// RENDER SELECTED FILES LIST (inside modal)
// ─────────────────────────────────────────────
function renderSelectedFiles() {
  const listEl      = document.getElementById("selectedFilesList");
  const containerEl = document.getElementById("filesContainer");
  const submitBtn   = document.getElementById("uploadSubmitBtn");

  if (!containerEl) return;

  if (selectedFiles.length === 0) {
    listEl?.classList.add("d-none");
    if (submitBtn) submitBtn.disabled = true;
    return;
  }

  listEl?.classList.remove("d-none");
  if (submitBtn) submitBtn.disabled = false;

  containerEl.innerHTML = selectedFiles.map((f, i) => `
    <div class="file-item">
      <i class="bi bi-file-earmark-pdf-fill text-danger"></i>
      <span class="file-item-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</span>
      <span class="file-item-size">${formatBytes(f.size)}</span>
      <button class="btn-icon" onclick="removeSelectedFile(${i})" title="Remove">
        <i class="bi bi-x"></i>
      </button>
    </div>
  `).join("");
}

// Remove one file from selection
window.removeSelectedFile = function(index) {
  selectedFiles.splice(index, 1);
  renderSelectedFiles();
};

// ─────────────────────────────────────────────
// HANDLE UPLOAD — send files to backend
// ─────────────────────────────────────────────
async function handleUpload() {
  const chatId = window.getCurrentChatId ? window.getCurrentChatId() : null;

  if (!chatId) {
    showToast("Please select a chat first", "danger");
    return;
  }
  if (selectedFiles.length === 0) {
    showToast("No files selected", "danger");
    return;
  }

  const submitBtn    = document.getElementById("uploadSubmitBtn");
  const progressArea = document.getElementById("uploadProgressArea");
  const progressBar  = document.getElementById("uploadProgressBar");
  const progressText = document.getElementById("uploadProgressText");
  const dropZone     = document.getElementById("dropZone");
  const filesList    = document.getElementById("selectedFilesList");

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Uploading...`;
  }
  progressArea?.classList.remove("d-none");
  dropZone?.classList.add("d-none");
  filesList?.classList.add("d-none");

  const total = selectedFiles.length;
  let succeeded = 0;
  let failed    = 0;

  for (let i = 0; i < selectedFiles.length; i++) {
    const file = selectedFiles[i];

    const percent = Math.round((i / total) * 100);
    if (progressBar)  progressBar.style.width   = `${percent}%`;
    if (progressText) progressText.textContent  = `Uploading ${i + 1} of ${total}: ${file.name}`;

    try {
      // ✅ FIX 1 — get token BEFORE building FormData
      const token = await getToken();
      if (!token) throw new Error("Not authenticated — please log in again");

      // ✅ FIX 2 — send ALL files in ONE request (not one per file)
      // This matches FastAPI's  List[UploadFile]  parameter
      const formData = new FormData();
      formData.append("files", file);

      // ✅ FIX 3 — do NOT set Content-Type header at all
      // Let the browser set it automatically with the correct multipart boundary
      const response = await fetch(
        `http://127.0.0.1:8000/chats/${chatId}/documents`,
        {
          method: "POST",
          headers: {
            // ONLY Authorization — no Content-Type!
            "Authorization": `Bearer ${token}`,
          },
          body: formData,
        }
      );

      // ✅ FIX 4 — better error reading
      if (!response.ok) {
        let errorMsg = `HTTP ${response.status}`;
        try {
          const errBody = await response.json();
          errorMsg = errBody.detail?.message || errBody.detail || errorMsg;
        } catch (_) {}
        throw new Error(errorMsg);
      }

      const uploaded = await response.json();
      if (Array.isArray(uploaded)) {
        currentDocs = [...uploaded, ...currentDocs];
      }

      succeeded++;

    } catch (err) {
      console.error(`Upload failed for ${file.name}:`, err.message);
      failed++;
    }
  }

  // 100%
  if (progressBar)  progressBar.style.width  = "100%";
  if (progressText) progressText.textContent = `Done! ${succeeded} uploaded${failed > 0 ? `, ${failed} failed` : ""}.`;

  await new Promise(r => setTimeout(r, 800));

  bootstrap.Modal.getInstance(document.getElementById("uploadModal"))?.hide();

  renderDocsList();
  updateDocCount(currentDocs.length);
  if (window.refreshChatDocCount) window.refreshChatDocCount(chatId, currentDocs.length);

  if (failed === 0) {
    showToast(`${succeeded} PDF${succeeded !== 1 ? "s" : ""} uploaded ✓`, "success");
  } else if (succeeded > 0) {
    showToast(`${succeeded} uploaded, ${failed} failed`, "danger");
  } else {
    showToast("All uploads failed. Check console for details.", "danger");
  }

  selectedFiles = [];
  resetUploadProgress();
}

// ─────────────────────────────────────────────
// RESET UPLOAD PROGRESS UI
// ─────────────────────────────────────────────
function resetUploadProgress() {
  const progressArea = document.getElementById("uploadProgressArea");
  const progressBar  = document.getElementById("uploadProgressBar");
  const progressText = document.getElementById("uploadProgressText");
  const dropZone     = document.getElementById("dropZone");
  const submitBtn    = document.getElementById("uploadSubmitBtn");

  progressArea?.classList.add("d-none");
  dropZone?.classList.remove("d-none");
  if (progressBar)  progressBar.style.width = "0%";
  if (progressText) progressText.textContent = "Uploading...";
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="bi bi-upload me-1"></i> Upload`;
  }
}

// ─────────────────────────────────────────────
// DELETE A SINGLE DOCUMENT
// ─────────────────────────────────────────────
let docPendingDelete = null;

function confirmDeleteDocument(docId, docName) {
  docPendingDelete = docId;

  // Reuse the existing delete modal with a custom message
  const modal = document.getElementById("deleteModal");
  const nameEl = document.getElementById("deleteChatName");
  const confirmBtn = document.getElementById("deleteChatConfirm");

  if (nameEl) nameEl.textContent = `"${docName}"`;

  // Temporarily override confirm button to delete doc instead of chat
  const originalHandler = confirmBtn.onclick;
  confirmBtn.onclick = async () => {
    await deleteDocument(docId);
    bootstrap.Modal.getInstance(modal)?.hide();
    confirmBtn.onclick = originalHandler; // restore
  };

  new bootstrap.Modal(modal).show();
}

async function deleteDocument(docId) {
  const chatId = window.getCurrentChatId ? window.getCurrentChatId() : null;
  if (!chatId || !docId) return;

  try {
    await authFetch(`/chats/${chatId}/documents/${docId}`, { method: "DELETE" });

    // Remove from local list
    currentDocs = currentDocs.filter(d => d.id !== docId);
    renderDocsList();
    updateDocCount(currentDocs.length);

    if (window.refreshChatDocCount) window.refreshChatDocCount(chatId, currentDocs.length);

    showToast("Document removed", "success");

  } catch (err) {
    showToast("Failed to delete: " + err.message, "danger");
  }
}

// ─────────────────────────────────────────────
// DELETE ALL DOCUMENTS FOR CURRENT CHAT
// ─────────────────────────────────────────────
async function deleteAllDocuments() {
  const chatId = window.getCurrentChatId ? window.getCurrentChatId() : null;
  if (!chatId || currentDocs.length === 0) return;

  if (!confirm(`Remove all ${currentDocs.length} documents from this chat?`)) return;

  let deleted = 0;
  for (const doc of currentDocs) {
    try {
      await authFetch(`/chats/${chatId}/documents/${doc.id}`, { method: "DELETE" });
      deleted++;
    } catch (err) {
      console.error(`Failed to delete ${doc.filename}:`, err.message);
    }
  }

  currentDocs = [];
  renderDocsList();
  updateDocCount(0);
  if (window.refreshChatDocCount) window.refreshChatDocCount(chatId, 0);
  showToast(`${deleted} document${deleted !== 1 ? "s" : ""} removed`, "success");
}

// ─────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  if (bytes < 1024)          return bytes + " B";
  if (bytes < 1024 * 1024)   return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

// ─────────────────────────────────────────────
// WIRE UP EVENT LISTENERS ON DOM READY
// ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initUploadModal();

  // "Remove All" button in docs panel
  document.getElementById("deleteAllDocsBtn")?.addEventListener("click", deleteAllDocuments);
});

// ─────────────────────────────────────────────
// EXPOSE GLOBALLY (used by chat.js)
// ─────────────────────────────────────────────
window.loadDocuments  = loadDocuments;
window.renderDocsList = renderDocsList;