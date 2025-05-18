# Financial Document Analyser

AI-powered tool for automated mining and analysis of large PDF financial documents, featuring semantic search, question-answering, and multi-language translation.

---

## Team - 01 

- **Faisal Budhwani**  
- **Shantanu Joshi**  
- **Siddharth Kulkarni**  

---

## Video Demo
Stored in folder - Video_Demo
<video src="Video_Demo/video1292717714.mp4" width="600" controls></video>  
[Watch the demo video](Video_Demo/video1292717714.mp4).

---

## Features

- **PDF Extraction:** Text, tables, and images from large documents
- **Semantic Search & QA:** Ask questions, get answers with source references
- **AI Analysis:** Key financial metrics, summaries, and risk factors
- **Visualizations:** Interactive charts and dashboards
- **Multi-Language:** Translate documents, preserve formatting

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

## Contributing

Pull requests welcome! For major changes, please open an issue first.

---

## License

MIT License

---

## Acknowledgments

- OpenAI, FAISS, Hugging Face, Streamlit
