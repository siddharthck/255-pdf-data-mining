

## Video Demo

Drive Link : https://drive.google.com/file/d/1XyfnSde8UNrIAqKMFGHFyJvyuNGO3WOA/view

Or
### Stored in folder - Video_Demo   
To download the video, right-click the link in a folder and select "Save link as..."
<video src="Video_Demo/video1292717714.mp4" width="600" controls></video>  
Download and [Watch the demo video](Video_Demo/video1292717714.mp4).

---

# Financial Document Analyser

AI-powered tool for automated mining and analysis of large PDF financial documents, featuring semantic search, question-answering, and multi-language translation.

---

## Team - 01

- **Faisal Budhwani**
- **Shantanu Joshi**
- **Siddharth Kulkarni**

---


## Overview

Financial documents like analyst reports, annual filings, and statements are often complex and unstructured, making it difficult and time-consuming to extract actionable insights. Our analyser leverages AI and automation to transform these documents into structured, searchable data—empowering users to quickly find answers, analyze trends, and make better decisions[1][2].

---

## Features

- **Automated PDF Extraction:** Extracts text, tables, images, and complex layouts using AI and OCR[2][5].
- **Semantic Search & QA:** Ask questions in natural language and get accurate answers with source references, powered by vector search and finance-specific language models[3].
- **AI Analysis:** Identifies key financial metrics, summarizes sections, and highlights risk factors for deeper insights[1][2][5].
- **Interactive Visualizations:** Generates charts and dashboards for trends, comparisons, and summaries.
- **Multi-Language Support:** Translates documents while preserving formatting and financial terminology, supporting global teams and compliance needs[4].
- **Integration Ready:** Extracted data can be exported or integrated with databases and analytics tools[2][5].

---

## Quick Start

1. **Clone & Install**
    ```
    git clone https://github.com/siddharthck/255-pdf-data-mining.git
    cd 255-pdf-data-mining
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
2. **Set API Key**
    - Add your OpenAI key to a `.env` file:  
      `OPENAI_API_KEY=your_openai_api_key_here`
3. **Run**
    ```
    streamlit run main.py
    ```
    Access at [http://localhost:8501](http://localhost:8501)

---

## Example Queries

- "Summarize the company’s main revenue sources."
- "What are the key risk factors?"
- "Show revenue trends over the last 3 years."

---

## Why Use This Tool?

- **Faster, More Accurate Analysis:** Automates extraction and reduces human error, delivering insights in seconds[1][2][5].
- **Handles Complex Documents:** Interprets tables, charts, and unstructured text—no manual copy-paste needed[2][3].
- **Supports Multilingual Teams:** Translate and analyze documents for global collaboration and compliance[4].
- **Integration & Scalability:** Ready for integration with your analytics or reporting stack[2][5].

---

## Contributing

Pull requests welcome! For major changes, please open an issue first.

---

## License

MIT License

---

## Acknowledgments

- OpenAI, FAISS, Hugging Face, Streamlit
