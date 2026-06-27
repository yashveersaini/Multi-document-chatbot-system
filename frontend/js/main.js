// Auto-resize textarea as user types
const messageInput = document.getElementById('messageInput');
if (messageInput) {
  messageInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
  });

  // Send on Enter (Shift+Enter for new line)
  messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      console.log('Send triggered — wiring up on Day 7+');
    }
  });
}

// New Chat button placeholder
const newChatBtn = document.getElementById('newChatBtn');
if (newChatBtn) {
  newChatBtn.addEventListener('click', () => {
    console.log('New chat — wiring up on Day 6+');
  });
}

// Send button placeholder
const sendBtn = document.getElementById('sendBtn');
if (sendBtn) {
  sendBtn.addEventListener('click', () => {
    console.log('Send — wiring up on Day 15+');
  });
}

console.log('PDFChat JS loaded ✓');