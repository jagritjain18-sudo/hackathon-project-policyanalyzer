# Policy Lens

An AI-powered web application that analyzes insurance policy documents using Google's AI technology. Upload PDF policy documents and get comprehensive analysis including summaries, coverage details, exclusions, benefits, and real-world scenarios.

## 🚀 Features

- **PDF Upload & Analysis**: Upload policy documents in PDF format
- **Automatic AI Processing**: Instant analysis using advanced AI models (Gemini)
- **Comprehensive Summary**: AI-generated highlighted summary with key sections
- **4-Card Snapshot Analysis**:
  - **Covered**: What the policy covers with amounts and limits
  - **Not Covered**: Gaps and exclusions compared to typical policies
  - **Benefits**: Extra perks and advantages provided by the insurer
  - **Scenarios**: Real-world examples showing when coverage applies or doesn't
- **Interactive Chat**: Ask questions about the uploaded policy document
- **Modern UI**: Clean, responsive dark-themed interface

## 🛠️ Technologies Used

- **Backend**: Python Flask
- **AI Engine**: Google AI (Gemini) for document analysis
- **PDF Processing**: PyPDF2 for text extraction
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with dark theme and modern design

## 📋 Requirements

- Python 3.8+
- Flask
- PyPDF2
- google-generativeai (or google.genai)
- python-dotenv (optional, for .env file support)
- Modern web browser

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd policy-lens
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google AI API**:
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a `.env` file in the project root:
   ```bash
   GOOGLE_API_KEY=your-api-key-here
   ```
   - Or set the environment variable:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

4. **Run the application**:
   ```bash
   python policylens_api.py
   ```

5. **Open in browser**:
   - Navigate to `http://localhost:8000`

## 📖 Usage

### Basic Workflow

1. **Upload PDF**: Click "Select PDF" and choose your policy document
2. **Automatic Analysis**: The app immediately processes the document
3. **View Results**:
   - **Summary Panel**: AI-highlighted overview with key information
   - **Snapshot Cards**: Four detailed analysis sections
   - **Chat Panel**: Ask specific questions about the policy

### API Endpoints

The application provides REST API endpoints:

- `POST /api/summary`: Generate AI summary of uploaded PDF
  - Parameters: `pdf` (file), `type` (optional: "brief", "detailed", "key_points")
- `POST /api/snapshot`: Create detailed 4-section policy analysis
  - Parameters: `pdf` (file)
- `POST /api/chat`: Ask questions about the uploaded document
  - Parameters: `pdf` (file), `question` (string)

### Example API Usage

```python
import requests

# Upload and analyze PDF
files = {'pdf': open('policy.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/summary', files=files)
summary = response.json()['summary']
```

## 🎨 UI Features

- **Dark Theme**: Modern dark interface for comfortable viewing
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Feedback**: Loading states and progress indicators
- **Color-coded Content**: Green for positive scenarios, red for exclusions
- **Interactive Elements**: Hover effects and smooth transitions

## 🔍 Analysis Features

### Summary Generation
- Extracts key information from policy documents
- Highlights benefits, coverage, and important terms
- Multiple summary types: brief, detailed, or key points

### Snapshot Analysis
- **Covered Section**: Lists all covered services, amounts, limits, and conditions
- **Not Covered Section**: Identifies gaps compared to industry standards
- **Benefits Section**: Extra perks, cashback, wellness programs, etc.
- **Scenarios Section**: Practical examples showing when coverage applies (✓) or doesn't (✗)

### Chat Functionality
- Ask specific questions about policy terms
- Get AI-powered answers based on document content
- Maintains conversation context

## 🏗️ Project Structure

```
policy-lens/
├── policylens_api.py          # Flask API server
├── policylens_handler.py      # AI processing logic
├── policylens_frontend.html   # Main HTML interface
├── policylens_frontend.css    # Styling and themes
├── policylens_frontend.js     # Frontend JavaScript
├── htmlTemplates.py           # HTML template utilities
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
├── logo.png                   # Application logo
├── temp_uploads/              # Temporary upload directory
└── README.md                  # This file
```

## 🔐 Security & Privacy

- Documents are processed locally on your machine
- No data is stored or transmitted to external servers (except Google AI API)
- API keys should be kept secure and not committed to version control
- Temporary files are automatically cleaned up after processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Please check the license file for details.

## 🆘 Troubleshooting

### Common Issues

1. **PDF Upload Fails**: Ensure the PDF is not password-protected and contains text (not just images)

2. **AI Analysis Errors**: Check your Google AI API key and internet connection

3. **Blank Results**: Some PDFs may have complex formatting. Try a different PDF or contact support

4. **Slow Processing**: Large PDFs may take longer to process. Be patient!

### Getting Help

- Check the browser console for error messages
- Ensure all dependencies are installed correctly
- Verify your API key is valid and has sufficient quota

## 🚀 Future Enhancements

- Support for additional document formats (DOCX, TXT)
- Batch processing of multiple documents
- Policy comparison features
- Export analysis results to PDF/Word
- Integration with policy management systems
- User accounts and document history

---

**Built with ❤️ using Flask, Google AI, and modern web technologies**
