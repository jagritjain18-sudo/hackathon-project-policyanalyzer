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
const chatResponse = document.getElementById('chat-response');
const uploadCard = document.querySelector('.upload-card');

let selectedPdfFile = null;
let isProcessing = false;

// Enhanced drag and drop functionality
uploadCard.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadCard.classList.add('dragover');
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

pdfInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  handleFileSelection(file);
});

function handleFileSelection(file) {
  selectedPdfFile = file;
  fileNameLabel.textContent = file.name;
  statusTitle.textContent = 'PDF uploaded';
  statusDetail.textContent = `Processing ${file.name} automatically...`;

  // Add success animation
  uploadCard.style.animation = 'successPulse 0.6s ease';
  setTimeout(() => {
    uploadCard.style.animation = '';
  }, 600);

  summaryContent.innerHTML = '<p class="summary-placeholder">Now click Generate Summary to see the AI highlight preview.</p>';
  chatResponse.innerHTML = '<p class="summary-placeholder">Your question answer will appear here.</p>';

  // Automatically generate snapshot on upload
  setTimeout(() => processUploadedPDF(), 1000);
}

function showErrorMessage(message) {
  // Remove existing messages
  const existingMessage = document.querySelector('.message-overlay');
  if (existingMessage) {
    existingMessage.remove();
  }

  const messageDiv = document.createElement('div');
  messageDiv.className = 'message-overlay error';
  messageDiv.innerHTML = `
    <div class="message-content">
      <div class="message-icon">✕</div>
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
  try {
    const response = await fetch(url, {
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

async function processUploadedPDF() {
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
});

generateSnapshotBtn.addEventListener('click', async () => {
  await processUploadedPDF();
});

sendChatBtn.addEventListener('click', async () => {
  const question = chatInput.value.trim();
  if (!question) return;
  if (!selectedPdfFile) {
    chatResponse.innerHTML = '<p class="summary-placeholder">Upload a PDF first to chat about it.</p>';
    return;
  }

  chatResponse.innerHTML = '<p class="summary-placeholder">Thinking...</p>';

  const formData = new FormData();
  formData.append('pdf', selectedPdfFile);
  formData.append('question', question);

  const result = await postPdfAction('/api/chat', formData);
  if (result.error) {
    chatResponse.innerHTML = `<p class="summary-placeholder">${result.error}</p>`;
    return;
  }

  chatResponse.innerHTML = `
    <div class="chat-message bot">
      <div class="avatar">🤖</div>
      <div>
        <p class="message-title">Answer</p>
        <p>${result.answer}</p>
      </div>
    </div>
  `;
});
