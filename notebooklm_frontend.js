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

let selectedPdfFile = null;

pdfInput.addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (!file) return;
  selectedPdfFile = file;
  fileNameLabel.textContent = file.name;
  statusTitle.textContent = 'PDF uploaded';
  statusDetail.textContent = `Ready to analyze ${file.name}.`;
  summaryContent.innerHTML = '<p class="summary-placeholder">Now click Generate Summary to see the AI highlight preview.</p>';
  coveredCard.textContent = 'Ready to extract covered topics from the uploaded document.';
  notCoveredCard.textContent = 'Ready to identify missing policy gaps.';
  benefitsCard.textContent = 'Ready to summarize benefits from the policy.';
  scenariosCard.textContent = 'Ready to generate real world claim scenarios.';
  chatResponse.innerHTML = '<p class="summary-placeholder">Your question answer will appear here.</p>';
});

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
  if (!selectedPdfFile) {
    coveredCard.textContent = 'Please upload a PDF to generate snapshot content.';
    notCoveredCard.textContent = 'Please upload a PDF to generate snapshot content.';
    benefitsCard.textContent = 'Please upload a PDF to generate snapshot content.';
    scenariosCard.textContent = 'Please upload a PDF to generate snapshot content.';
    return;
  }

  coveredCard.textContent = 'Generating snapshot...';
  notCoveredCard.textContent = 'Generating snapshot...';
  benefitsCard.textContent = 'Generating snapshot...';
  scenariosCard.textContent = 'Generating snapshot...';

  const formData = new FormData();
  formData.append('pdf', selectedPdfFile);

  const result = await postPdfAction('/api/snapshot', formData);
  if (result.error) {
    coveredCard.textContent = result.error;
    notCoveredCard.textContent = result.error;
    benefitsCard.textContent = result.error;
    scenariosCard.textContent = result.error;
    return;
  }

  coveredCard.textContent = result.covered || 'No covered topics detected.';
  notCoveredCard.textContent = result.not_covered || 'No missing topics detected.';
  benefitsCard.textContent = result.benefits || 'No benefits detected.';
  scenariosCard.textContent = result.scenarios || 'No scenarios detected.';
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
