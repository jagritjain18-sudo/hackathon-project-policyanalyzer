import os
import PyPDF2
from typing import Optional, List

# Prefer google.genai when available; otherwise fall back to google.generativeai
try:
    import google.genai as genai
except ImportError:
    import google.generativeai as genai

# Load environment variables safely
try:
    from dotenv import load_dotenv
    load_dotenv(encoding='utf-8-sig')
except Exception:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

class NotebookLMHandler:
    """Handler for PDF summarization and Q&A using Google Generative AI (NotebookLM-like functionality)"""
    
    def __init__(self):
        """Initialize the NotebookLM handler with API key"""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set. Get one from https://makersuite.google.com/app/apikey")
        
        self.use_new_api = hasattr(genai, 'Client') and not hasattr(genai, 'configure')
        self.model_name = None
        self.model = None
        self.conversation_history = []
        self.pdf_text = ""
        self.pdf_name = ""
        
        if self.use_new_api:
            self.client = genai.Client(api_key=api_key)
        else:
            genai.configure(api_key=api_key)
            self.client = None
        
        models_to_try = [
            'gemini-2.5-flash',
            'gemini-flash-latest',
            'gemini-2.5-pro',
            'gemini-pro-latest',
            'gemini-2.0-flash',
        ]
        
        for model_name in models_to_try:
            if self._test_model(model_name):
                self.model_name = model_name
                print(f"Using model: {model_name}")
                break
        
        if self.model_name is None:
            try:
                if self.use_new_api:
                    model_iter = self.client.models.list()
                else:
                    model_iter = genai.list_models()
                for model in model_iter:
                    model_name = getattr(model, 'name', '')
                    if not model_name:
                        continue
                    model_name = model_name.replace('models/', '')
                    if 'gemini' not in model_name:
                        continue
                    if any(block in model_name for block in ['image', 'tts', 'bidi']):
                        continue
                    if self._test_model(model_name):
                        self.model_name = model_name
                        print(f"Using available model: {model_name}")
                        break
            except Exception as e:
                raise ValueError(f"Could not find a compatible Gemini model. Check your API key and available models. ({e})")
        
        if self.model_name is None:
            raise ValueError("Could not find a compatible Gemini model. Check your API key and available models.")
    
    def _test_model(self, model_name: str) -> bool:
        try:
            if self.use_new_api:
                response = self.client.models.generate_content(model=model_name, contents="test")
                return hasattr(response, 'text')
            else:
                self.model = genai.GenerativeModel(model_name)
                response = self.model.generate_content("test")
                return hasattr(response, 'text')
        except Exception:
            return False
    
    def _generate_text(self, prompt: str):
        if self.use_new_api:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            return response.text
        else:
            response = self.model.generate_content(prompt)
            return response.text
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page.extract_text()
            
            self.pdf_text = text
            self.pdf_name = os.path.basename(pdf_path)
            self.conversation_history = []  # Reset history for new PDF
            
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def generate_summary(self, summary_type: str = "brief") -> str:
        """
        Generate summary of the PDF
        
        Args:
            summary_type: "brief" (100-150 words), "detailed" (300-500 words), or "key_points" (bullet points)
        
        Returns:
            Summary of the PDF content
        """
        if not self.pdf_text:
            return "Error: No PDF loaded. Please extract PDF text first."
        
        summary_prompts = {
            "brief": "Provide a brief summary (100-150 words) of this document:",
            "detailed": "Provide a detailed summary (300-500 words) of this document, covering all major points:",
            "key_points": "Extract the 10 most important key points from this document as bullet points:"
        }
        
        prompt = summary_prompts.get(summary_type, summary_prompts["brief"])
        
        try:
            return self._generate_text(f"{prompt}\n\n{self.pdf_text}")
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def ask_question(self, question: str) -> str:
        """
        Ask a question about the PDF content
        
        Args:
            question: The question to ask about the PDF
        
        Returns:
            Answer based on the PDF content
        """
        if not self.pdf_text:
            return "Error: No PDF loaded. Please extract PDF text first."
        
        # Add question to history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        
        # Build context with conversation history
        history_context = ""
        for item in self.conversation_history[:-1]:  # Exclude current question
            history_context += f"\nPrevious Q&A:\nQ: {item['content']}\n"
        
        system_prompt = f"""You are a helpful assistant that answers questions about a document. 
You have access to the following document content:

{self.pdf_text}

Instructions:
1. Answer questions directly from the document content
2. Be specific and cite relevant sections when applicable
3. If the answer is not in the document, clearly state that
4. Maintain context from previous questions in the conversation
5. Be concise but thorough
"""
        
        try:
            answer = self._generate_text(f"{system_prompt}\n{history_context}\n\nQuestion: {question}")
            
            # Add answer to history
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })
            
            return answer
        except Exception as e:
            return f"Error answering question: {str(e)}"
    
    def get_conversation_history(self) -> List[dict]:
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_conversation(self) -> None:
        """Clear conversation history while keeping PDF"""
        self.conversation_history = []
    
    def reset(self) -> None:
        """Reset everything (PDF and conversation)"""
        self.pdf_text = ""
        self.pdf_name = ""
        self.conversation_history = []
    
    def extract_topics(self) -> str:
        """Extract main topics/sections from the document"""
        if not self.pdf_text:
            return "Error: No PDF loaded."
        
        prompt = """Analyze this document and extract:
1. Main topics covered
2. Key concepts
3. Overall structure/organization

Format as a structured outline:"""
        
        try:
            return self._generate_text(f"{prompt}\n\n{self.pdf_text}")
        except Exception as e:
            return f"Error extracting topics: {str(e)}"
    
    def compare_sections(self, section1: str, section2: str) -> str:
        """Compare two concepts or sections mentioned in the document"""
        if not self.pdf_text:
            return "Error: No PDF loaded."
        
        prompt = f"""Based on the document provided, compare and contrast:
1. {section1}
2. {section2}

Provide a detailed comparison:"""
        
        try:
            return self._generate_text(f"{prompt}\n\n{self.pdf_text}")
        except Exception as e:
            return f"Error comparing sections: {str(e)}"
