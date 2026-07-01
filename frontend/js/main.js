// ─── SIDEBAR TOGGLE (mobile) ───
const sidebar       = document.getElementById('sidebar');
const sidebarOpen   = document.getElementById('sidebarOpen');
const sidebarClose  = document.getElementById('sidebarClose');

if (sidebarOpen)  sidebarOpen.addEventListener('click',  () => sidebar.classList.add('open'));
if (sidebarClose) sidebarClose.addEventListener('click', () => sidebar.classList.remove('open'));

document.addEventListener('click', (e) => {
  if (sidebar && sidebar.classList.contains('open')) {
    if (!sidebar.contains(e.target) && e.target !== sidebarOpen) {
      sidebar.classList.remove('open');
    }
  }
});


// ─── DOCS PANEL ───
const docsPanel      = document.getElementById('docsPanel');
const viewDocsBtn    = document.getElementById('viewDocsBtn');
const closeDocsBtn   = document.getElementById('closeDocs');
const panelBackdrop  = document.getElementById('panelBackdrop');

function openDocsPanel() {
  docsPanel?.classList.add('open');
  panelBackdrop?.classList.remove('d-none');
}
function closeDocsPanel() {
  docsPanel?.classList.remove('open');
  panelBackdrop?.classList.add('d-none');
}

viewDocsBtn?.addEventListener('click', openDocsPanel);
closeDocsBtn?.addEventListener('click', closeDocsPanel);
panelBackdrop?.addEventListener('click', closeDocsPanel);


// ─── TEXTAREA AUTO-RESIZE ───
const messageInput = document.getElementById('messageInput');
const sendBtn      = document.getElementById('sendBtn');

if (messageInput) {
  messageInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 140) + 'px';
  });

  messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(); // wired fully on Day 15
    }
  });
}

function handleSend() {
  const text = messageInput?.value.trim();
  if (!text) return;
  console.log('Send message (Day 15):', text);
}

sendBtn?.addEventListener('click', handleSend);


// ─── FILE UPLOAD UI ───
const dropZone          = document.getElementById('dropZone');
const fileInput         = document.getElementById('fileInput');
const browseBtn         = document.getElementById('browseBtn');
const selectedFilesList = document.getElementById('selectedFilesList');
const filesContainer    = document.getElementById('filesContainer');
const clearFilesBtn     = document.getElementById('clearFilesBtn');
const uploadSubmitBtn   = document.getElementById('uploadSubmitBtn');

let selectedFiles = [];

browseBtn?.addEventListener('click', () => fileInput?.click());

dropZone?.addEventListener('click', (e) => {
  if (e.target !== browseBtn) fileInput?.click();
});

fileInput?.addEventListener('change', (e) => {
  addFiles(Array.from(e.target.files));
  fileInput.value = '';
});

dropZone?.addEventListener('dragover',  (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone?.addEventListener('dragleave', ()  => dropZone.classList.remove('dragover'));
dropZone?.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
  addFiles(files);
});

function addFiles(newFiles) {
  const valid = newFiles.filter(f => {
    if (f.type !== 'application/pdf') { showToast(`${f.name} is not a PDF`, 'danger'); return false; }
    if (f.size > 50 * 1024 * 1024)   { showToast(`${f.name} exceeds 50 MB`,  'danger'); return false; }
    return true;
  });

  selectedFiles = [...selectedFiles, ...valid];
  renderFileList();
}

function renderFileList() {
  if (!filesContainer) return;

  if (selectedFiles.length === 0) {
    selectedFilesList?.classList.add('d-none');
    if (uploadSubmitBtn) uploadSubmitBtn.disabled = true;
    return;
  }

  selectedFilesList?.classList.remove('d-none');
  if (uploadSubmitBtn) uploadSubmitBtn.disabled = false;

  filesContainer.innerHTML = selectedFiles.map((f, i) => `
    <div class="file-item">
      <i class="bi bi-file-earmark-pdf-fill text-danger"></i>
      <span class="file-item-name" title="${f.name}">${f.name}</span>
      <span class="file-item-size">${formatBytes(f.size)}</span>
      <button class="btn-icon" onclick="removeFile(${i})" title="Remove">
        <i class="bi bi-x"></i>
      </button>
    </div>
  `).join('');
}

window.removeFile = function(index) {
  selectedFiles.splice(index, 1);
  renderFileList();
};

clearFilesBtn?.addEventListener('click', () => {
  selectedFiles = [];
  renderFileList();
});

uploadSubmitBtn?.addEventListener('click', () => {
  if (selectedFiles.length === 0) return;
  console.log('Uploading files (Day 8):', selectedFiles.map(f => f.name));
  showToast('Upload coming on Day 8!', 'success');
});

document.getElementById('uploadModal')?.addEventListener('hidden.bs.modal', () => {
  selectedFiles = [];
  renderFileList();
});


// ─── TOAST NOTIFICATIONS ───
function showToast(message, type = 'default') {
  const toastEl  = document.getElementById('appToast');
  const toastMsg = document.getElementById('toastMessage');
  if (!toastEl || !toastMsg) return;

  toastMsg.textContent = message;
  toastEl.classList.remove('bg-success', 'bg-danger');
  if (type === 'success') toastEl.classList.add('bg-success');
  if (type === 'danger')  toastEl.classList.add('bg-danger');

  const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
  toast.show();
}
window.showToast = showToast;


// ─── UTILITY ───
function formatBytes(bytes) {
  if (bytes < 1024)        return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

console.log('PDFChat UI loaded ✓');