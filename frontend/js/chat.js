// frontend/js/chat.js

// ─────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────
let currentChatId = null;
let allChats = [];
let chatPendingDelete = null;

// ── Expose active chat ID for upload.js
window.getCurrentChatId = () => currentChatId;

// ── Called by upload.js after upload to refresh sidebar count
window.refreshChatDocCount = function(chatId, count) {
  const idx = allChats.findIndex(c => c.id === chatId);
  if (idx !== -1) allChats[idx].document_count = count;
  renderChatList();
};

// ─────────────────────────────────────────────
// LOAD ALL CHATS
// ─────────────────────────────────────────────
async function loadChats() {
  const loadingEl = document.getElementById("chatListLoading");
  const emptyEl   = document.getElementById("chatListEmpty");

  loadingEl?.classList.remove("d-none");
  emptyEl?.classList.add("d-none");

  try {
    const data = await authFetch("/chats");
    allChats = data.chats;

    loadingEl?.classList.add("d-none");

    if (allChats.length === 0) {
      emptyEl?.classList.remove("d-none");
      showWelcomeState();
      return;
    }

    emptyEl?.classList.add("d-none");
    renderChatList();

    if (!currentChatId && allChats.length > 0) {
      selectChat(allChats[0].id);
    }

  } catch (err) {
    loadingEl?.classList.add("d-none");
    showToast("Failed to load chats: " + err.message, "danger");
  }
}

// ─────────────────────────────────────────────
// RENDER CHAT LIST
// ─────────────────────────────────────────────
function renderChatList() {
  const listEl = document.getElementById("chatList");
  if (!listEl) return;

  listEl.querySelectorAll(".chat-item").forEach(item => item.remove());

  allChats.forEach(chat => {
    const item = document.createElement("div");
    item.className = "chat-item" + (chat.id === currentChatId ? " active" : "");
    item.dataset.chatId = chat.id;

    item.innerHTML = `
      <i class="bi bi-chat-text text-secondary me-2 flex-shrink-0"></i>
      <span class="chat-item-title">${escapeHtml(chat.title)}</span>
      <div class="chat-item-actions">
        <button class="btn-icon rename-btn" title="Rename">
          <i class="bi bi-pencil"></i>
        </button>
        <button class="btn-icon text-danger delete-btn" title="Delete">
          <i class="bi bi-trash"></i>
        </button>
      </div>
    `;

    item.addEventListener("click", (e) => {
      if (e.target.closest(".chat-item-actions")) return;
      selectChat(chat.id);
    });

    item.querySelector(".rename-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      openRenameModal(chat.id, chat.title);
    });

    item.querySelector(".delete-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      openDeleteModal(chat.id, chat.title);
    });

    listEl.appendChild(item);
  });
}

// ─────────────────────────────────────────────
// SELECT A CHAT
// ─────────────────────────────────────────────
function selectChat(chatId) {
  currentChatId = chatId;

  const chat = allChats.find(c => c.id === chatId);
  if (!chat) return;

  document.querySelectorAll(".chat-item").forEach(item => {
    item.classList.toggle("active", item.dataset.chatId === chatId);
  });

  const titleEl    = document.getElementById("chatTitle");
  const docCountEl = document.getElementById("chatDocCount");
  if (titleEl)    titleEl.textContent    = chat.title;
  if (docCountEl) docCountEl.textContent = `${chat.document_count} document${chat.document_count !== 1 ? "s" : ""}`;

  const messageInput = document.getElementById("messageInput");
  const sendBtn      = document.getElementById("sendBtn");
  if (messageInput) messageInput.disabled = false;
  if (sendBtn)      sendBtn.disabled      = false;

  hideWelcomeState();

  // ── Load documents for this chat (upload.js)
  if (window.loadDocuments) window.loadDocuments(chatId);

  document.getElementById("sidebar")?.classList.remove("open");
}

// ─────────────────────────────────────────────
// CREATE A NEW CHAT
// ─────────────────────────────────────────────
async function createNewChat() {
  const btn = document.getElementById("newChatBtn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Creating...`;
  }

  try {
    const newChat = await authFetch("/chats", {
      method: "POST",
      body: JSON.stringify({ title: "New Chat" }),
    });

    allChats.unshift(newChat);
    document.getElementById("chatListEmpty")?.classList.add("d-none");
    renderChatList();
    selectChat(newChat.id);
    showToast("New chat created!", "success");

  } catch (err) {
    showToast("Failed to create chat: " + err.message, "danger");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i class="bi bi-plus-lg"></i> New Chat`;
    }
  }
}

// ─────────────────────────────────────────────
// RENAME MODAL
// ─────────────────────────────────────────────
let chatPendingRename = null;

function openRenameModal(chatId, currentTitle) {
  chatPendingRename = chatId;
  const input = document.getElementById("renameChatInput");
  if (input) input.value = currentTitle;
  const modal = new bootstrap.Modal(document.getElementById("renameModal"));
  modal.show();
  setTimeout(() => input?.focus(), 300);
}

async function confirmRename() {
  const input    = document.getElementById("renameChatInput");
  const newTitle = input?.value.trim();
  if (!newTitle)          { showToast("Chat name cannot be empty", "danger"); return; }
  if (!chatPendingRename) return;

  try {
    const updated = await authFetch(`/chats/${chatPendingRename}`, {
      method: "PATCH",
      body: JSON.stringify({ title: newTitle }),
    });

    const idx = allChats.findIndex(c => c.id === chatPendingRename);
    if (idx !== -1) allChats[idx].title = updated.title;

    renderChatList();

    if (currentChatId === chatPendingRename) {
      const titleEl = document.getElementById("chatTitle");
      if (titleEl) titleEl.textContent = updated.title;
    }

    bootstrap.Modal.getInstance(document.getElementById("renameModal"))?.hide();
    showToast("Chat renamed", "success");

  } catch (err) {
    showToast("Failed to rename: " + err.message, "danger");
  } finally {
    chatPendingRename = null;
  }
}

// ─────────────────────────────────────────────
// DELETE MODAL
// ─────────────────────────────────────────────
function openDeleteModal(chatId, title) {
  chatPendingDelete = chatId;
  const nameEl = document.getElementById("deleteChatName");
  if (nameEl) nameEl.textContent = `"${title}"`;

  // Make sure confirm button deletes a CHAT (not a doc)
  const confirmBtn = document.getElementById("deleteChatConfirm");
  confirmBtn.onclick = confirmDelete;

  new bootstrap.Modal(document.getElementById("deleteModal")).show();
}

async function confirmDelete() {
  if (!chatPendingDelete) return;

  try {
    await authFetch(`/chats/${chatPendingDelete}`, { method: "DELETE" });

    allChats = allChats.filter(c => c.id !== chatPendingDelete);
    renderChatList();

    if (currentChatId === chatPendingDelete) {
      currentChatId = null;
      if (allChats.length > 0) {
        selectChat(allChats[0].id);
      } else {
        showWelcomeState();
        document.getElementById("chatListEmpty")?.classList.remove("d-none");
        const titleEl    = document.getElementById("chatTitle");
        const docCountEl = document.getElementById("chatDocCount");
        if (titleEl)    titleEl.textContent    = "Select a chat";
        if (docCountEl) docCountEl.textContent = "No documents";
        const messageInput = document.getElementById("messageInput");
        const sendBtn      = document.getElementById("sendBtn");
        if (messageInput) messageInput.disabled = true;
        if (sendBtn)      sendBtn.disabled      = true;
      }
    }

    bootstrap.Modal.getInstance(document.getElementById("deleteModal"))?.hide();
    showToast("Chat deleted", "success");

  } catch (err) {
    showToast("Failed to delete: " + err.message, "danger");
  } finally {
    chatPendingDelete = null;
  }
}

// ─────────────────────────────────────────────
// WELCOME STATE
// ─────────────────────────────────────────────
function showWelcomeState() {
  document.getElementById("welcomeState")?.classList.remove("d-none");
}
function hideWelcomeState() {
  document.getElementById("welcomeState")?.classList.add("d-none");
}

// ─────────────────────────────────────────────
// UTILITY
// ─────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ─────────────────────────────────────────────
// EVENT LISTENERS
// ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("newChatBtn")?.addEventListener("click", createNewChat);
  document.getElementById("renameChatConfirm")?.addEventListener("click", confirmRename);
  document.getElementById("deleteChatConfirm")?.addEventListener("click", confirmDelete);

  document.getElementById("renameChatInput")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); confirmRename(); }
  });
});

window.loadChats = loadChats;