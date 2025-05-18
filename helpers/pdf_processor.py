import PyPDF2
import re
from io import BytesIO
from database import save_extracted_text

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.read()))
        full_text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 50:  # Only include pages with substantial content
                full_text += f"\n--- Page {page_num + 1} ---\n{text}"
        
        return full_text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def identify_10k_sections(text):
    sections = {}
    
    # More comprehensive section patterns that look for actual content, not just headers
    section_patterns = {
        "business_overview": [
            r"ITEM\s*1\s*[.\-]*\s*BUSINESS\s*\n(.*?)(?=ITEM\s*1A|ITEM\s*2|$)",
            r"Part\s*I.*Item\s*1.*Business\s*\n(.*?)(?=Item\s*1A|Item\s*2|$)",
            r"BUSINESS\s*OVERVIEW\s*\n(.*?)(?=RISK|ITEM|$)"
        ],
        "risk_factors": [
            r"ITEM\s*1A\s*[.\-]*\s*RISK\s*FACTORS\s*\n(.*?)(?=ITEM\s*1B|ITEM\s*2|$)",
            r"Part\s*I.*Item\s*1A.*Risk\s*Factors\s*\n(.*?)(?=Item\s*1B|Item\s*2|$)",
            r"RISK\s*FACTORS\s*\n(.*?)(?=ITEM|Part|$)"
        ],
        "financial_data": [
            r"ITEM\s*8\s*[.\-]*\s*FINANCIAL\s*STATEMENTS\s*\n(.*?)(?=ITEM\s*9|$)",
            r"Part\s*II.*Item\s*8.*Financial\s*Statements\s*\n(.*?)(?=Item\s*9|$)",
            r"CONSOLIDATED\s*STATEMENTS\s*\n(.*?)(?=ITEM|Part|$)"
        ],
        "management_discussion": [
            r"ITEM\s*7\s*[.\-]*\s*MANAGEMENT'S\s*DISCUSSION\s*(.*?)(?=ITEM\s*7A|ITEM\s*8|$)",
            r"Part\s*II.*Item\s*7.*Management.*Discussion\s*(.*?)(?=Item\s*7A|Item\s*8|$)",
            r"MD&A\s*(.*?)(?=ITEM|Part|$)"
        ],
        "properties": [
            r"ITEM\s*2\s*[.\-]*\s*PROPERTIES\s*\n(.*?)(?=ITEM\s*3|$)",
            r"Part\s*I.*Item\s*2.*Properties\s*\n(.*?)(?=Item\s*3|$)"
        ],
        "legal_proceedings": [
            r"ITEM\s*3\s*[.\-]*\s*LEGAL\s*PROCEEDINGS\s*\n(.*?)(?=ITEM\s*4|$)",
            r"Part\s*I.*Item\s*3.*Legal\s*Proceedings\s*\n(.*?)(?=Item\s*4|$)"
        ]
    }
    
    # Clean the text first - remove excessive whitespace but preserve structure
    cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    for section_name, patterns in section_patterns.items():
        section_content = ""
        
        for pattern in patterns:
            matches = re.finditer(pattern, cleaned_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match.groups()) > 0:
                    # Get the content group, not just the header
                    content = match.group(1)
                else:
                    # If no groups, get everything after the header
                    start_pos = match.end()
                    # Find next section or end of document
                    next_section_patterns = [
                        r'ITEM\s*\d+[A-Z]*\s*[.\-]*\s*[A-Z\s]+',
                        r'Part\s*[IVX]+',
                        r'SIGNATURES',
                        r'EXHIBITS'
                    ]
                    
                    end_pos = len(cleaned_text)
                    for next_pattern in next_section_patterns:
                        next_matches = list(re.finditer(next_pattern, cleaned_text[start_pos:], re.IGNORECASE))
                        if next_matches:
                            end_pos = min(end_pos, start_pos + next_matches[0].start())
                    
                    content = cleaned_text[start_pos:end_pos]
                
                # Clean and validate the content
                content = clean_section_text(content)
                
                # Only use if we have substantial content (not just table of contents)
                if (len(content) > 500 and 
                    not is_table_of_contents(content) and
                    not is_mostly_page_numbers(content)):
                    section_content = content
                    break
        
        if section_content:
            sections[section_name] = section_content
    
    # If we didn't get much content, try a different approach - extract by page ranges
    if not sections or all(len(content) < 1000 for content in sections.values()):
        sections.update(extract_content_by_keywords(cleaned_text))
    
    return sections

def extract_content_by_keywords(text):
    """Alternative extraction method that looks for content by keywords rather than strict patterns"""
    sections = {}
    
    # Split text into paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 100]
    
    # Business content keywords
    business_keywords = ['business', 'operations', 'products', 'services', 'customers', 'competition', 'market', 'industry', 'segments']
    risk_keywords = ['risk', 'risks', 'uncertainty', 'factors', 'may affect', 'could impact', 'potential', 'adverse']
    financial_keywords = ['revenue', 'income', 'expenses', 'assets', 'liabilities', 'cash flow', 'financial condition']
    management_keywords = ['management', 'analysis', 'results of operations', 'liquidity', 'capital resources']
    
    # Extract content based on keyword density
    business_content = extract_content_by_keyword_density(paragraphs, business_keywords, min_paragraphs=5)
    risk_content = extract_content_by_keyword_density(paragraphs, risk_keywords, min_paragraphs=3)
    financial_content = extract_content_by_keyword_density(paragraphs, financial_keywords, min_paragraphs=3)
    management_content = extract_content_by_keyword_density(paragraphs, management_keywords, min_paragraphs=3)
    
    if business_content:
        sections['business_overview'] = business_content
    if risk_content:
        sections['risk_factors'] = risk_content
    if financial_content:
        sections['financial_data'] = financial_content
    if management_content:
        sections['management_discussion'] = management_content
    
    return sections

def extract_content_by_keyword_density(paragraphs, keywords, min_paragraphs=3):
    """Extract paragraphs that have high keyword density"""
    scored_paragraphs = []
    
    for para in paragraphs:
        score = 0
        para_lower = para.lower()
        for keyword in keywords:
            score += para_lower.count(keyword.lower())
        
        if score > 0:
            scored_paragraphs.append((score, para))
    
    # Sort by score and take top paragraphs
    scored_paragraphs.sort(reverse=True, key=lambda x: x[0])
    top_paragraphs = [para for score, para in scored_paragraphs[:min_paragraphs * 2]]
    
    if len(top_paragraphs) >= min_paragraphs:
        return '\n\n'.join(top_paragraphs)
    
    return ""

def is_table_of_contents(text):
    """Check if text is primarily a table of contents"""
    toc_indicators = [
        'ITEM', 'Part I', 'Part II', 'Part III', 'Part IV',
        'Page', 'pages', '...', '........', 
        'CONTENTS', 'INDEX', 'TABLE OF CONTENTS'
    ]
    
    lines = text.split('\n')
    toc_line_count = 0
    
    for line in lines:
        line_upper = line.upper()
        if any(indicator in line_upper for indicator in toc_indicators):
            toc_line_count += 1
    
    # If more than 30% of lines look like TOC, it's probably TOC
    return toc_line_count > len(lines) * 0.3

def is_mostly_page_numbers(text):
    """Check if text is mostly just page numbers and headers"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) == 0:
        return True
    
    short_lines = sum(1 for line in lines if len(line) < 50)
    return short_lines > len(lines) * 0.7

def clean_section_text(text):
    if not text:
        return ""
    
    # Remove excessive whitespace but preserve paragraph structure
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove page headers/footers (lines that are very short or just numbers)
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip very short lines, pure numbers, or typical headers/footers
        if (len(line) > 20 and 
            not re.match(r'^\d+$', line) and  # Not just a number
            not re.match(r'^Page \d+', line, re.IGNORECASE) and  # Not page header
            not re.match(r'^--- Page \d+ ---', line)):  # Not our page marker
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\$\%\(\)\-\:\;\"\'\n]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def process_pdf_and_store(pdf_file, doc_id):
    full_text = extract_text_from_pdf(pdf_file)
    
    if "Error" in full_text:
        return False, full_text
    
    sections = identify_10k_sections(full_text)
    
    save_extracted_text(doc_id, "full_document", full_text)
    
    for section_name, section_content in sections.items():
        if section_content and len(section_content) > 100:
            save_extracted_text(doc_id, section_name, section_content)
    
    return True, f"Extracted {len(sections)} sections from PDF"

def get_company_name_from_text(text):
    # Enhanced company name extraction with multiple patterns
    patterns = [
        # SEC form headers
        r'UNITED\s+STATES[^0-9]+SECURITIES\s+AND\s+EXCHANGE\s+COMMISSION[^0-9]+Washington[^0-9]+D\.C[^0-9]+FORM\s+10-K[^0-9]+ANNUAL\s+REPORT[^0-9]+FOR\s+THE\s+FISCAL\s+YEAR[^0-9]+([A-Z][A-Za-z\s&\.,\-]+?)(?:\s+\([^)]+\)|\s+Form\s+10-K|\s+Commission|\s+File)',
        
        # Company name in parentheses
        r'(?:COMMISSION\s+FILE|File\s+Number)[^0-9]+(?:\d+[^0-9]+)?([A-Z][A-Za-z\s&\.,\-]+?)\s+\([^)]*Exact\s+name',
        
        # Direct company name patterns
        r'(?:COMPANY|CORPORATION|REGISTRANT):\s*([A-Z][A-Za-z\s&\.,\-]+?)(?:\s|$)',
        r'(?:REGISTRANT|ISSUER):\s*([A-Z][A-Za-z\s&\.,\-]+?)(?:\s|$)',
        
        # Form 10-K specific patterns
        r'FORM\s+10-K\s+FOR\s+THE\s+FISCAL\s+YEAR[^0-9]+([A-Z][A-Za-z\s&\.,\-]+?)(?:\s+\([^)]+\)|\s+Form|\s+Commission)',
        
        # Common corporate patterns
        r'^([A-Z][A-Za-z\s&\.,\-]+?(?:\s+Inc\.?|\s+Corp\.?|\s+Corporation|\s+Company|\s+LLC|\s+Ltd\.?))\s*$',
        
        # Alternative patterns for different formats
        r'([A-Z][A-Za-z\s&\.,\-]{5,50})\s+\(Exact\s+name',
        r'([A-Z][A-Za-z\s&\.,\-]{5,50})\s+FORM\s+10-K',
        
        # Fallback pattern for beginning of document
        r'^([A-Z][A-Za-z\s&\.,\-]{10,60})\s*ANNUAL\s+REPORT',
        
        # Pattern for cover page
        r'COVER\s+PAGE[^0-9]+([A-Z][A-Za-z\s&\.,\-]+?)(?:\s+\([^)]+\)|\s+Form)',
        
        # Pattern for document title
        r'SECURITIES\s+AND\s+EXCHANGE\s+COMMISSION[^0-9]+([A-Z][A-Za-z\s&\.,\-]+?)(?:\s+\([^)]+\)|\s+Form)',
    ]
    
    # First try with the first 5000 characters for better accuracy
    search_text = text[:5000]
    
    for pattern in patterns:
        matches = re.finditer(pattern, search_text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            company_name = match.group(1).strip()
            
            # Clean up the company name
            company_name = re.sub(r'\s+', ' ', company_name)
            company_name = re.sub(r'^[^A-Za-z]+', '', company_name)
            company_name = re.sub(r'[^A-Za-z\s&\.,\-]+$', '', company_name)
            
            # Validate company name
            if (len(company_name) > 5 and 
                len(company_name) < 100 and
                not re.match(r'^(FORM|COMMISSION|FILE|UNITED|STATES|SECURITIES|EXCHANGE|WASHINGTON|ANNUAL|REPORT|THE|FOR|FISCAL|YEAR)$', company_name.upper()) and
                re.search(r'[A-Za-z]{3,}', company_name)):  # Must contain at least 3 consecutive letters
                
                # Clean common suffixes/prefixes that get caught
                company_name = re.sub(r'^(THE\s+|A\s+)', '', company_name, flags=re.IGNORECASE)
                company_name = re.sub(r'\s+(FORM\s+10-K|ANNUAL\s+REPORT|COMMISSION\s+FILE).*$', '', company_name, flags=re.IGNORECASE)
                
                return company_name.strip()
    
    # If no pattern matches, try a more general approach
    lines = text.split('\n')[:50]  # Check first 50 lines
    for line in lines:
        line = line.strip()
        if (len(line) > 10 and 
            len(line) < 80 and 
            re.search(r'[A-Z][a-z]+.*[A-Z][a-z]+', line) and  # Mixed case pattern
            ('Inc' in line or 'Corp' in line or 'Company' in line or 'LLC' in line or 'Ltd' in line)):
            
            # Clean the line
            clean_line = re.sub(r'[^A-Za-z\s&\.,\-]', ' ', line)
            clean_line = re.sub(r'\s+', ' ', clean_line).strip()
            
            if len(clean_line) > 5 and len(clean_line) < 100:
                return clean_line
    
    return "Unknown Company"

def get_fiscal_year_from_text(text):
    patterns = [
        r'FOR\s+THE\s+FISCAL\s+YEAR\s+ENDED\s+[A-Za-z\s,]*(\d{4})',
        r'YEAR\s+ENDED\s+[A-Za-z\s,]*(\d{4})',
        r'ANNUAL\s+REPORT[^0-9]*(\d{4})',
        r'FORM\s+10-K[^0-9]*(\d{4})',
        r'FISCAL\s+YEAR[^0-9]*(\d{4})',
        r'PERIOD\s+ENDED[^0-9]*(\d{4})',
        r'December\s+31,\s+(\d{4})',
        r'September\s+30,\s+(\d{4})',
        r'June\s+30,\s+(\d{4})',
        r'March\s+31,\s+(\d{4})'
    ]
    
    # Search in first 5000 characters
    search_text = text[:5000]
    
    for pattern in patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            year = int(match)
            if 2015 <= year <= 2025:  # Reasonable range for 10-K filings
                return str(year)
    
    # Default to most recent completed fiscal year if nothing found
    return "2023"

def chunk_text_for_analysis(text, max_chars=8000):
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1
        if current_length + word_length > max_chars and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks