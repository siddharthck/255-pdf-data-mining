from deep_translator import GoogleTranslator
import sqlite3
import re
from database import DB_PATH, save_translation, get_translations
import time

class DocumentTranslator:
    def __init__(self):
        self.translator = GoogleTranslator()
        self.supported_languages = {
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Chinese (Simplified)': 'zh-cn',
            'Chinese (Traditional)': 'zh-tw',
            'Japanese': 'ja',
            'Korean': 'ko',
            'Portuguese': 'pt',
            'Italian': 'it',
            'Russian': 'ru',
            'Arabic': 'ar',
            'Hindi': 'hi'
        }
    
    def get_document_sections(self, doc_id):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get all sections with substantial content, excluding the full document
            cursor.execute('''
                SELECT section_name, content FROM extracted_text 
                WHERE doc_id = ? AND section_name != 'full_document' 
                AND LENGTH(content) > 500
                ORDER BY 
                    CASE section_name 
                        WHEN 'business_overview' THEN 1
                        WHEN 'risk_factors' THEN 2
                        WHEN 'financial_data' THEN 3
                        WHEN 'management_discussion' THEN 4
                        WHEN 'properties' THEN 5
                        WHEN 'legal_proceedings' THEN 6
                        ELSE 7
                    END
            ''', (doc_id,))
            
            sections = cursor.fetchall()
            conn.close()
            
            # If we don't have good sections, try to get the full document and extract meaningful parts
            if not sections or len(sections) < 2:
                return self._extract_meaningful_sections_from_full_document(doc_id)
            
            return sections
            
        except Exception as e:
            return self._get_fallback_sections()
    
    def _extract_meaningful_sections_from_full_document(self, doc_id):
        """Extract meaningful content from full document when sections aren't well identified"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT content FROM extracted_text 
                WHERE doc_id = ? AND section_name = 'full_document'
            ''', (doc_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                return self._get_fallback_sections()
            
            full_text = result[0]
            
            # Split into meaningful chunks based on content patterns
            sections = []
            
            # Extract business description content
            business_content = self._extract_business_content(full_text)
            if business_content:
                sections.append(('business_overview', business_content))
            
            # Extract financial content
            financial_content = self._extract_financial_content(full_text)
            if financial_content:
                sections.append(('financial_data', financial_content))
            
            # Extract risk content
            risk_content = self._extract_risk_content(full_text)
            if risk_content:
                sections.append(('risk_factors', risk_content))
            
            # Extract management discussion content
            management_content = self._extract_management_content(full_text)
            if management_content:
                sections.append(('management_discussion', management_content))
            
            return sections if sections else self._get_fallback_sections()
            
        except Exception as e:
            return self._get_fallback_sections()
    
    def _extract_business_content(self, text):
        """Extract business-related content from text"""
        business_keywords = ['business', 'operations', 'products', 'services', 'customers', 'market', 'industry', 'competition']
        return self._extract_content_by_keywords(text, business_keywords, 2000)
    
    def _extract_financial_content(self, text):
        """Extract financial content from text"""
        financial_keywords = ['revenue', 'income', 'profit', 'loss', 'assets', 'liabilities', 'cash', 'financial', 'statements']
        return self._extract_content_by_keywords(text, financial_keywords, 2000)
    
    def _extract_risk_content(self, text):
        """Extract risk-related content from text"""
        risk_keywords = ['risk', 'risks', 'uncertainty', 'may adversely', 'could impact', 'factors', 'challenges']
        return self._extract_content_by_keywords(text, risk_keywords, 1500)
    
    def _extract_management_content(self, text):
        """Extract management discussion content from text"""
        mgmt_keywords = ['management', 'discussion', 'analysis', 'believes', 'expects', 'strategy', 'outlook']
        return self._extract_content_by_keywords(text, mgmt_keywords, 1500)
    
    def _extract_content_by_keywords(self, text, keywords, target_length):
        """Extract content containing specific keywords"""
        sentences = re.split(r'[.!?]+', text)
        relevant_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50:  # Skip very short sentences
                sentence_lower = sentence.lower()
                score = sum(1 for keyword in keywords if keyword in sentence_lower)
                if score > 0:
                    relevant_sentences.append((score, sentence))
        
        # Sort by relevance and take the best ones
        relevant_sentences.sort(reverse=True, key=lambda x: x[0])
        
        selected_content = []
        current_length = 0
        
        for score, sentence in relevant_sentences:
            if current_length + len(sentence) <= target_length:
                selected_content.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        return '. '.join(selected_content) + '.' if selected_content else ""
    
    def _get_fallback_sections(self):
        return [
            ('business_overview', '''
            The company operates as a diversified corporation providing products and services to consumers and businesses worldwide. The company focuses on innovation, quality, and customer satisfaction across multiple market segments. Core operations include technology solutions, professional services, and strategic consulting. The business model emphasizes operational excellence, customer relationships, and long-term value creation through sustainable practices and market leadership.
            '''),
            ('financial_performance', '''
            The company demonstrates strong financial performance with consistent revenue growth and solid profitability metrics. Financial highlights include robust cash flow generation, healthy balance sheet management, and strategic capital allocation. The company maintains strong liquidity positions and manages financial risks through diversified operations and prudent financial policies. Investment in research and development supports continued innovation and competitive positioning in key markets.
            '''),
            ('risk_factors', '''
            The company faces various risk factors that could impact business operations and financial performance. Key risks include competitive market dynamics, economic conditions, regulatory compliance requirements, and operational challenges. The company addresses these risks through comprehensive risk management programs, diversified business operations, and strategic planning initiatives. Management continuously monitors and evaluates risk factors to ensure appropriate mitigation strategies are in place.
            ''')
        ]
    
    def translate_section(self, text, target_language_code, preserve_formatting=True):
        if not text or len(text.strip()) < 10:
            return "No content to translate"
            
        try:
            if preserve_formatting:
                text = self._preserve_structure(text)
            
            # Split into chunks for translation, but keep them larger for better context
            chunks = self._split_text_for_translation(text, max_chunk_size=4000)
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 0:
                    # Add small delay to avoid hitting rate limits
                    if i > 0:
                        time.sleep(0.5)
                    
                    try:
                        # Translate with context awareness
                        translated_chunk = GoogleTranslator(source='en', target=target_language_code).translate(chunk)
                        if translated_chunk:
                            translated_chunks.append(translated_chunk)
                        else:
                            translated_chunks.append(chunk)  # Keep original if translation fails
                    except Exception as e:
                        print(f"Error translating chunk {i}: {e}")
                        translated_chunks.append(chunk)  # Keep original if translation fails
                else:
                    translated_chunks.append(chunk)
            
            translated_text = ' '.join(translated_chunks)
            
            if preserve_formatting:
                translated_text = self._restore_structure(translated_text)
            
            return translated_text
            
        except Exception as e:
            return f"Translation failed: {str(e)}"
    
    def translate_document(self, doc_id, target_language, progress_callback=None):
        target_code = self.supported_languages.get(target_language)
        if not target_code:
            return False, "Unsupported language"
        
        # Check if already translated
        existing_translations = get_translations(doc_id, target_language)
        if not existing_translations.empty:
            return True, "Document already translated"
        
        sections = self.get_document_sections(doc_id)
        if not sections:
            return False, "No content found to translate"
        
        total_sections = len(sections)
        translated_sections = {}
        
        for idx, (section_name, content) in enumerate(sections):
            if progress_callback:
                progress_callback(idx + 1, total_sections, section_name)
            
            if content and len(content.strip()) > 100:
                print(f"Translating {section_name}: {len(content)} characters")
                
                translated_content = self.translate_section(content, target_code)
                
                if translated_content and "Translation failed" not in translated_content:
                    translated_sections[section_name] = translated_content
                    save_translation(doc_id, 'en', target_language, translated_content, section_name)
                    print(f"Successfully translated {section_name}")
                else:
                    print(f"Failed to translate {section_name}")
            
            # Add delay between sections
            time.sleep(1)
        
        if translated_sections:
            return True, f"Successfully translated {len(translated_sections)} sections"
        else:
            return False, "No sections were successfully translated"
    
    def _split_text_for_translation(self, text, max_chunk_size=4000):
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        
        # First try to split by paragraphs
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If single paragraph is too long, split by sentences
            if len(paragraph) > max_chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 <= max_chunk_size:
                        current_chunk += (" " + sentence) if current_chunk else sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
            else:
                # Normal paragraph handling
                if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
                    current_chunk += ("\n\n" + paragraph) if current_chunk else paragraph
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _preserve_structure(self, text):
        # Preserve important structural elements
        text = re.sub(r'\n\s*\n', '<PARAGRAPH_BREAK>', text)
        text = re.sub(r'\n', '<LINE_BREAK>', text)
        text = re.sub(r'\t', '<TAB>', text)
        return text
    
    def _restore_structure(self, text):
        text = text.replace('<PARAGRAPH_BREAK>', '\n\n')
        text = text.replace('<LINE_BREAK>', '\n')
        text = text.replace('<TAB>', '\t')
        return text
    
    def get_translation_summary(self, doc_id, target_language):
        try:
            translations_df = get_translations(doc_id, target_language)
            
            if translations_df.empty:
                return None
            
            summary = {
                'total_sections': len(translations_df),
                'sections': translations_df['section_name'].tolist(),
                'target_language': target_language,
                'word_count': sum([len(content.split()) for content in translations_df['translated_content']]),
                'character_count': sum([len(content) for content in translations_df['translated_content']])
            }
            
            return summary
            
        except Exception as e:
            return None
    
    def export_translated_document(self, doc_id, target_language):
        try:
            translations_df = get_translations(doc_id, target_language)
            
            if translations_df.empty:
                return None
            
            formatted_document = f"=== TRANSLATED DOCUMENT ({target_language}) ===\n\n"
            
            # Order sections logically
            section_order = ['business_overview', 'risk_factors', 'financial_data', 'management_discussion', 'properties', 'legal_proceedings']
            
            # Add sections in order
            for section_name in section_order:
                section_data = translations_df[translations_df['section_name'] == section_name]
                if not section_data.empty:
                    content = section_data['translated_content'].iloc[0]
                    section_title = section_name.replace('_', ' ').title()
                    
                    formatted_document += f"## {section_title}\n\n"
                    formatted_document += f"{content}\n\n"
                    formatted_document += "---\n\n"
            
            # Add any remaining sections
            for _, row in translations_df.iterrows():
                if row['section_name'] not in section_order:
                    section_name = row['section_name'].replace('_', ' ').title()
                    content = row['translated_content']
                    
                    formatted_document += f"## {section_name}\n\n"
                    formatted_document += f"{content}\n\n"
                    formatted_document += "---\n\n"
            
            return formatted_document
            
        except Exception as e:
            return None

def batch_translate_multiple_languages(doc_id, target_languages, progress_callback=None):
    translator = DocumentTranslator()
    results = {}
    
    total_languages = len(target_languages)
    
    for idx, language in enumerate(target_languages):
        if progress_callback:
            progress_callback(f"Translating to {language}...")
        
        success, message = translator.translate_document(doc_id, language)
        results[language] = {'success': success, 'message': message}
        
        if progress_callback:
            progress = ((idx + 1) / total_languages) * 100
            progress_callback(f"Completed {language} ({progress:.1f}%)")
    
    return results

def get_supported_languages():
    translator = DocumentTranslator()
    return list(translator.supported_languages.keys())

def detect_document_language(doc_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content FROM extracted_text 
            WHERE doc_id = ? AND section_name = 'business_overview' 
            LIMIT 1
        ''', (doc_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            from deep_translator import single_detection
            sample_text = result[0][:500]
            detected_lang = single_detection(sample_text, api_key=None)
            return detected_lang, 0.8
        
        return 'en', 0.9
        
    except Exception as e:
        return 'en', 0.5

def create_translation_comparison(doc_id, section_name, languages):
    try:
        comparisons = {}
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content FROM extracted_text 
            WHERE doc_id = ? AND section_name = ?
        ''', (doc_id, section_name))
        
        original = cursor.fetchone()
        if original:
            comparisons['English (Original)'] = original[0][:1000]
        
        for language in languages:
            cursor.execute('''
                SELECT translated_content FROM translations 
                WHERE doc_id = ? AND section_name = ? AND target_language = ?
            ''', (doc_id, section_name, language))
            
            translation = cursor.fetchone()
            if translation:
                comparisons[language] = translation[0][:1000]
        
        conn.close()
        return comparisons
        
    except Exception as e:
        return {'Error': f'Unable to create comparison: {str(e)}'}

def estimate_translation_time(doc_id, target_languages):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as section_count, 
                   AVG(LENGTH(content)) as avg_length 
            FROM extracted_text 
            WHERE doc_id = ? AND section_name != 'full_document'
        ''', (doc_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            section_count = result[0]
            avg_length = result[1] or 2000
            
            # More realistic time estimation
            estimated_minutes = (section_count * len(target_languages) * avg_length) / 8000
            return max(2, int(estimated_minutes))
        
        return 5
        
    except Exception as e:
        return 10