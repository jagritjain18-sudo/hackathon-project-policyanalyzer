import os
import json
import PyPDF2
import time
import re
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

class PolicyLensHandler:
    """Handler for PDF summarization and Q&A using Google Generative AI (Policy Lens functionality)"""
    
    def __init__(self):
        """Initialize the Policy Lens handler with API key"""
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
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.use_new_api:
                    response = self.client.models.generate_content(model=self.model_name, contents=prompt)
                    return response.text
                else:
                    response = self.model.generate_content(prompt)
                    return response.text
            except Exception as e:
                error_str = str(e).lower()
                if '503' in error_str or 'unavailable' in error_str or 'high demand' in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1  # Exponential backoff: 1, 3, 7 seconds
                        print(f"Model experiencing high demand. Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise e  # Re-raise after max retries
                else:
                    raise e  # Re-raise non-503 errors immediately

    def _extract_json_from_text(self, text: str) -> dict:
        """Try to recover JSON from a model response that may include extra text."""
        # First, try direct parsing
        try:
            return json.loads(text.strip())
        except Exception:
            pass
        
        # Try to find JSON between ```json and ```
        json_match = re.search(r'```(?:json)?\s*(\{[^`]*\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass
        
        # Try to find JSON between { and } (greedy approach with brace matching)
        start = text.find('{')
        if start != -1:
            brace_count = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i
                        break
            
            if end != -1:
                candidate = text[start:end+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    fixed = self._fix_json_string(candidate)
                    try:
                        return json.loads(fixed)
                    except Exception:
                        pass
        
        # Try to clean up common issues
        cleaned = re.sub(r'```(?:json)?|```', '', text).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            fixed = self._fix_json_string(cleaned)
            try:
                return json.loads(fixed)
            except Exception:
                pass
        
        return {}
    
    def _fix_json_string(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues."""
        json_str = re.sub(r'^```json\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)
        json_str = json_str.strip()
        # Remove trailing commas
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        return json_str

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
    
    def generate_snapshot(self) -> str:
        """Generate a structured snapshot JSON of the policy document with comprehensive analysis."""
        if not self.pdf_text:
            return json.dumps({"covered": "Error: No PDF loaded.", "not_covered": "", "benefits": "", "scenarios": ""})

        prompt = f"""You are analyzing a policy PDF to create 4 snapshot sections.
Return ONLY valid JSON that can be parsed by JSON.parse(). No other text before or after.

IMPORTANT DEFINITIONS - BE VERY DETAILED:

1. "covered": Extract EVERY SINGLE service, condition, item, benefit, coverage, limit, and feature THIS SPECIFIC POLICY COVERS
   Include ALL of these details:
   - Medical services (doctor visits, hospital stays, surgeries, etc.)
   - Coverage amounts, limits, deductibles, co-pays, percentages
   - Time periods, waiting periods, coverage duration
   - Specific conditions, treatments, medications
   - Emergency services, preventive care, diagnostic tests
   - Network restrictions, in-network vs out-of-network
   - Age limits, eligibility criteria
   - Pre-existing conditions coverage
   Format as detailed bullet points starting with "-"
   Minimum 15-20 bullet points. Be exhaustive!

2. "not_covered": List items that TYPICAL COMPETING POLICIES offer but THIS SPECIFIC POLICY DOES NOT COVER (gaps and exclusions)
   Compare to standard industry policies and identify what's missing:
   - Services not included (dental, vision, mental health, etc.)
   - Coverage limitations or exclusions
   - Higher deductibles or co-pays than competitors
   - Shorter coverage periods
   - More restrictive eligibility
   - Pre-authorization requirements
   Format as bullet points starting with "-"
   Minimum 8-10 bullet points showing competitive disadvantages.

3. "benefits": Extract EVERY benefit, perk, reward, and extra value provided by the POLICY COMPANY (beyond basic coverage)
   Include ALL of these:
   - Cashback, rewards, loyalty programs
   - Free services, checkups, consultations
   - Wellness programs, fitness benefits
   - 24/7 support, concierge services
   - Mobile apps, online tools, telemedicine
   - Family coverage options, dependent benefits
   - Premium discounts, multi-policy savings
   - Claim processing speed, ease of use
   Format as bullet points starting with "-"
   Minimum 10-15 bullet points.

4. "scenarios": Create 15-20 real-world, specific situations showing when a POLICY HOLDER would BENEFIT (✓) or NOT BENEFIT (✗)
   Use actual amounts, percentages, and details from the policy document.
   Make scenarios very specific and practical:
   
   EXAMPLES of good detailed scenarios:
   ✓ If a policyholder needs emergency appendectomy surgery costing $15,000, they pay $0 out-of-pocket (100% covered after $500 deductible)
   ✓ If a policyholder visits their primary care doctor for routine checkup, they pay $25 co-pay and get full coverage for lab tests
   ✓ If a policyholder has a baby delivered in-network, they get $2,500 maternity benefit + 100% hospital coverage
   ✓ If a policyholder needs MRI scan for diagnosis, it's 90% covered with $200 deductible
   ✗ If a policyholder goes to out-of-network specialist, they only get 60% reimbursement instead of 100%
   ✗ If a policyholder had diabetes before policy purchase, it's excluded for first 12 months
   ✗ If a policyholder needs cosmetic surgery for vanity purposes, it's not covered at all
   ✗ If a policyholder exceeds $10,000 annual limit, they pay 100% of additional costs
   ✗ If a policyholder travels internationally, emergency coverage is limited to $5,000

   Include specific dollar amounts, percentages, and policy details in EVERY scenario!

JSON FORMAT RULES:
- Return ONLY the JSON object, nothing else
- Use double quotes for all strings
- Escape newlines as \\n and quotes as \\"
- No trailing commas anywhere
- All fields must be strings or empty strings ""
- Valid JSON that passes JSON.parse()

JSON template:
{{
  "covered": "- Emergency room visits: 100% covered after $300 deductible\\n- Hospital stays: $2,500 per day up to 30 days\\n- Doctor office visits: $25 co-pay\\n- Preventive care: 100% covered annually\\n- Prescription drugs: 80% covered after $500 deductible\\n- [Continue with 15+ detailed items]",
  "not_covered": "- Dental care: Not covered (competitors offer)\\n- Vision care: Not covered\\n- Mental health therapy: Limited to 10 sessions\\n- Chiropractic care: Not covered\\n- [Continue with 8+ competitive gaps]",
  "benefits": "- 5% cashback on all claims paid\\n- Free annual physical exam\\n- 24/7 nurse hotline\\n- Mobile app for claims\\n- Family plan discounts\\n- [Continue with 10+ benefits]",
  "scenarios": "✓ If a policyholder breaks their arm and needs surgery costing $8,000, they pay $300 deductible then 100% covered\\n✓ If a policyholder has routine blood work, it's 100% covered with no co-pay\\n✓ If a policyholder delivers a baby, they receive $3,000 maternity benefit\\n✗ If a policyholder needs knee replacement surgery, they pay 20% co-insurance above $5,000\\n✗ If a policyholder has pre-existing back pain, physical therapy is not covered\\n✗ If a policyholder exceeds $100,000 lifetime limit, all costs become out-of-pocket\\n[Continue with 15+ specific scenarios]"
}}

POLICY DOCUMENT:
{self.pdf_text}

Return ONLY the JSON object (valid, parseable, comprehensive):
"""
        try:
            response_text = self._generate_text(prompt)
            parsed = self._extract_json_from_text(response_text)
            
            # Validate parsed result has all required keys
            required_keys = ["covered", "not_covered", "benefits", "scenarios"]
            if parsed and all(key in parsed for key in required_keys):
                # Ensure all values are strings
                for key in required_keys:
                    if not isinstance(parsed[key], str):
                        parsed[key] = str(parsed[key]) if parsed[key] else ""
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            
            # If parsing failed but got something, fill with what we have
            if parsed:
                result = {key: "" for key in required_keys}
                for key in result:
                    if key in parsed:
                        result[key] = str(parsed[key]) if isinstance(parsed[key], str) else str(parsed[key])
                return json.dumps(result, indent=2, ensure_ascii=False)
            
            # Last resort: return error in valid JSON format
            return json.dumps({
                "covered": "Unable to parse policy document",
                "not_covered": "",
                "benefits": "",
                "scenarios": ""
            }, indent=2, ensure_ascii=False)
        except Exception as e:
            # Always return valid JSON, even on error
            return json.dumps({
                "covered": f"Error: {str(e)}",
                "not_covered": "",
                "benefits": "",
                "scenarios": ""
            }, indent=2, ensure_ascii=False)

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
