const pdfInput = document.getElementById('pdf-input');
const fileNameLabel = document.getElementById('file-name');
const statusTitle = document.getElementById('status-title');
const statusDetail = document.getElementById('status-detail');
const generateSummaryBtn = document.getElementById('generate-summary');
const generateSnapshotBtn = document.getElementById('generate-snapshot');
const summaryContent = document.getElementById('summary-content');
const coveredCard = document.getElementById('covered-card');
const notCoveredCard = document.getElementById('not-covered-card');
const benefitsCard = document.getElementById('benefits-card');
const scenariosCard = document.getElementById('scenarios-card');
const sendChatBtn = document.getElementById('send-chat');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const uploadCard = document.querySelector('.upload-card');

let selectedPdfFile = null;
let isProcessing = false;

// Check server connectivity on page load
document.addEventListener('DOMContentLoaded', async () => {
  if (window.location.protocol === 'file:') {
    try {
      const response = await fetch('http://localhost:8000/api/health', { method: 'GET' });
      if (!response.ok) {
        showErrorMessage('Server not responding. Please start the server with: python policypirates_api.py');
      }
    } catch (error) {
      showErrorMessage('Cannot connect to server. Please start the server with: python policypirates_api.py');
    }
  }
});
let chatHistory = [];

// Enhanced keyboard navigation
document.addEventListener('keydown', (e) => {
  // Skip link activation
  if (e.key === 'Tab' && e.shiftKey === false) {
    const skipLink = document.querySelector('.skip-link');
    if (skipLink && document.activeElement === document.body) {
      e.preventDefault();
      skipLink.focus();
    }
  }

  // Enter key for chat input
  if (e.key === 'Enter' && !e.shiftKey && document.activeElement === chatInput) {
    e.preventDefault();
    sendChatBtn.click();
  }
});

// Enhanced drag and drop functionality with better feedback
uploadCard.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadCard.classList.add('dragover');
  uploadCard.setAttribute('aria-describedby', 'upload-instructions');
});

uploadCard.addEventListener('dragleave', (e) => {
  e.preventDefault();
  uploadCard.classList.remove('dragover');
});

uploadCard.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadCard.classList.remove('dragover');

  const files = e.dataTransfer.files;
  if (files.length > 0 && files[0].type === 'application/pdf') {
    handleFileSelection(files[0]);
  } else {
    showErrorMessage('Please drop a valid PDF file.');
  }
});

// Click to upload
uploadCard.addEventListener('click', () => {
  pdfInput.value = '';
  pdfInput.click();
});

uploadCard.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    pdfInput.value = '';
    pdfInput.click();
  }
});

pdfInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  handleFileSelection(file);
});

function handleFileSelection(file) {
  selectedPdfFile = file;
  fileNameLabel.textContent = file.name;
  statusTitle.textContent = 'PDF uploaded successfully';
  statusDetail.textContent = `Ready to analyze ${file.name}. Click "Generate Snapshot" to start processing.`;

  // Enhanced success animation
  uploadCard.style.animation = 'successPulse 0.6s ease';
  setTimeout(() => {
    uploadCard.style.animation = '';
  }, 600);

  // Update UI states
  summaryContent.innerHTML = '<p class="summary-placeholder">Upload complete! Now click Generate Summary to see AI insights.</p>';
  updateChatMessages([{ type: 'bot', content: 'PDF uploaded successfully! Generating snapshot and summary automatically.' }]);

  // Enable buttons
  generateSummaryBtn.disabled = false;
  generateSnapshotBtn.disabled = false;
  sendChatBtn.disabled = false;

  // Announce to screen readers
  announceToScreenReader('PDF uploaded successfully. Ready for analysis.');

  // Automatically start snapshot and summary generation
  processUploadedPDF(true);
}

function announceToScreenReader(message) {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'assertive');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.style.width = '1px';
  announcement.style.height = '1px';
  announcement.style.overflow = 'hidden';
  announcement.textContent = message;
  document.body.appendChild(announcement);
  setTimeout(() => document.body.removeChild(announcement), 1000);
}

function updateChatMessages(messages) {
  chatMessages.innerHTML = '';
  messages.forEach(message => {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${message.type}`;
    messageDiv.setAttribute('role', 'article');
    messageDiv.innerHTML = `
      <div class="avatar" aria-hidden="true">${message.type === 'bot' ? '🤖' : '👤'}</div>
      <div>
        <p class="message-title">${message.type === 'bot' ? 'AI Assistant' : 'You'}</p>
        <p>${message.content}</p>
      </div>
    `;
    chatMessages.appendChild(messageDiv);
  });
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showSuccessMessage(message) {
  // Remove existing messages
  const existingMessage = document.querySelector('.message-overlay');
  if (existingMessage) {
    existingMessage.remove();
  }

  const messageDiv = document.createElement('div');
  messageDiv.className = 'message-overlay success';
  messageDiv.innerHTML = `
    <div class="message-content">
      <div class="message-icon">✓</div>
      <div class="message-text">${message}</div>
    </div>
  `;

  document.body.appendChild(messageDiv);

  // Auto-remove after 4 seconds with fade-out
  setTimeout(() => {
    messageDiv.classList.add('fade-out');
    setTimeout(() => {
      if (messageDiv.parentNode) {
        messageDiv.remove();
      }
    }, 500);
  }, 4000);
}

function addLoadingOverlay(element, message = 'Processing...') {
  const overlay = document.createElement('div');
  overlay.className = 'loading-overlay';
  overlay.innerHTML = `
    <div class="loading-spinner"></div>
    <div class="loading-text">${message}</div>
    <div class="loading-subtext">This may take a few moments</div>
    <div class="progress-bar">
      <div class="progress-fill"></div>
    </div>
  `;
  element.style.position = 'relative';
  element.appendChild(overlay);
  return overlay;
}

function removeLoadingOverlay(element) {
  const overlay = element.querySelector('.loading-overlay');
  if (overlay) {
    overlay.style.animation = 'fadeOut 0.3s ease';
    setTimeout(() => overlay.remove(), 300);
  }
}

async function postPdfAction(url, formData) {
  // Use absolute URL when running from file:// protocol
  const baseUrl = window.location.protocol === 'file:' ? 'http://localhost:8000' : '';
  const fullUrl = baseUrl + url;

  try {
    const response = await fetch(fullUrl, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Server error.');
    }
    return data;
  } catch (error) {
    return { error: error.message };
  }
}

async function processUploadedPDF(autoGenerateSummary = false) {
  if (!selectedPdfFile || isProcessing) return;

  isProcessing = true;
  statusDetail.textContent = 'AI is analyzing your policy document...';

  // Add loading overlays to cards
  const coveredOverlay = addLoadingOverlay(document.querySelector('.card.covered'), 'Analyzing Coverage');
  const notCoveredOverlay = addLoadingOverlay(document.querySelector('.card.not-covered'), 'Finding Gaps');
  const benefitsOverlay = addLoadingOverlay(document.querySelector('.card.benefits'), 'Extracting Benefits');
  const scenariosOverlay = addLoadingOverlay(document.querySelector('.card.scenarios'), 'Generating Scenarios');

  // Add processing class to status card
  document.querySelector('.status-card.accent').classList.add('processing');

  const formData = new FormData();
  formData.append('pdf', selectedPdfFile);

  const result = await postPdfAction('/api/snapshot', formData);

  // Remove loading overlays
  removeLoadingOverlay(document.querySelector('.card.covered'));
  removeLoadingOverlay(document.querySelector('.card.not-covered'));
  removeLoadingOverlay(document.querySelector('.card.benefits'));
  removeLoadingOverlay(document.querySelector('.card.scenarios'));

  // Remove processing class
  document.querySelector('.status-card.accent').classList.remove('processing');

  if (result.error) {
    const errorMsg = 'Error: ' + result.error;
    coveredCard.innerHTML = `<p class="summary-placeholder">${errorMsg}</p>`;
    notCoveredCard.innerHTML = `<p class="summary-placeholder">${errorMsg}</p>`;
    benefitsCard.innerHTML = `<p class="summary-placeholder">${errorMsg}</p>`;
    scenariosCard.innerHTML = `<p class="summary-placeholder">${errorMsg}</p>`;
    statusDetail.textContent = `Error processing ${selectedPdfFile.name}.`;
    showErrorMessage('Failed to process the PDF. Please try again.');
    isProcessing = false;
    return;
  }

  // Access nested snapshot object
  const snapshot = result.snapshot || result;

  coveredCard.innerHTML = formatContent(snapshot.covered, 'covered');
  notCoveredCard.innerHTML = formatContent(snapshot.not_covered, 'not_covered');
  benefitsCard.innerHTML = formatContent(snapshot.benefits, 'benefits');
  scenariosCard.innerHTML = formatContent(snapshot.scenarios, 'scenarios');

  statusDetail.textContent = `${selectedPdfFile.name} processed successfully.`;
  showSuccessMessage('Policy analysis complete! Check the cards below for detailed insights.');
  isProcessing = false;

  if (autoGenerateSummary) {
    await generateSummary();
  }
}

async function generateSummary() {
  if (!selectedPdfFile) {
    summaryContent.innerHTML = '<p class="summary-placeholder">Please upload a PDF first.</p>';
    return;
  }

  summaryContent.innerHTML = '<p class="summary-placeholder">Generating summary...</p>';
  const formData = new FormData();
  formData.append('pdf', selectedPdfFile);
  formData.append('type', 'brief');

  const result = await postPdfAction('/api/summary', formData);
  if (result.error) {
    summaryContent.innerHTML = `<p class="summary-placeholder">${result.error}</p>`;
    return;
  }

  const lines = result.summary.split('\n').filter(Boolean);
  summaryContent.innerHTML = lines
    .map((line) => {
      const lower = line.toLowerCase();
      let type = 'summary-line';
      if (lower.includes('benefit') || lower.includes('advantage')) type += ' highlight-benefits';
      else if (lower.includes('missing') || lower.includes('not covered')) type += ' highlight-missing';
      else if (lower.includes('covered') || lower.includes('includes')) type += ' highlight-covered';
      return `<div class="${type}">${line}</div>`;
    })
    .join('');
}

// Helper function to format content with color coding based on card type
function formatContent(text, cardType) {
  if (!text) return '<p class="summary-placeholder">No content detected.</p>';

  // Define colors based on card type
  let color = '#64748b'; // default gray
  if (cardType === 'covered') color = '#22c55e'; // green
  else if (cardType === 'not_covered') color = '#ef4444'; // red
  else if (cardType === 'benefits') color = '#3b82f6'; // blue

  // Split by newline and create HTML with proper formatting
  return text
    .split('\n')
    .filter(line => line.trim().length > 0)
    .map(line => {
      const trimmed = line.trim();
      // For benefits, don't apply ✓/✗ coloring - keep it all blue
      if (cardType === 'benefits') {
        return `<p style="color: ${color}; margin: 8px 0;">${trimmed}</p>`;
      }
      // For other cards, apply marker-based coloring
      if (trimmed.startsWith('✓')) {
        return `<p style="color: ${color}; margin: 8px 0; font-weight: 500;">${trimmed}</p>`;
      } else if (trimmed.startsWith('✗')) {
        return `<p style="color: ${color}; margin: 8px 0; font-weight: 500;">${trimmed}</p>`;
      } else if (trimmed.startsWith('-')) {
        return `<p style="color: ${color}; margin: 6px 0; margin-left: 12px;">${trimmed}</p>`;
      } else {
        return `<p style="color: ${color}; margin: 8px 0;">${trimmed}</p>`;
      }
    })
    .join('');
}

generateSummaryBtn.addEventListener('click', async () => {
  await generateSummary();
});

generateSnapshotBtn.addEventListener('click', async () => {
  await processUploadedPDF();
});

sendChatBtn.addEventListener('click', async () => {
  const question = chatInput.value.trim();
  if (!question) {
    showErrorMessage('Please enter a question.');
    return;
  }
  if (!selectedPdfFile) {
    updateChatMessages([{ type: 'bot', content: 'Please upload a PDF first before asking questions.' }]);
    return;
  }

  // Add user message to chat
  chatHistory.push({ type: 'user', content: question });
  updateChatMessages(chatHistory);

  // Show typing indicator
  const typingMessage = { type: 'bot', content: 'Thinking...' };
  chatHistory.push(typingMessage);
  updateChatMessages(chatHistory);

  chatInput.value = '';
  chatInput.disabled = true;
  sendChatBtn.disabled = true;

  const formData = new FormData();
  formData.append('pdf', selectedPdfFile);
  formData.append('question', question);

  const result = await postPdfAction('/api/chat', formData);

  // Remove typing indicator
  chatHistory.pop();

  if (result.error) {
    chatHistory.push({ type: 'bot', content: `Error: ${result.error}` });
    showErrorMessage('Failed to get answer. Please try again.');
  } else {
    chatHistory.push({ type: 'bot', content: result.answer });
  }

  updateChatMessages(chatHistory);
  chatInput.disabled = false;
  sendChatBtn.disabled = false;
  chatInput.focus();
});