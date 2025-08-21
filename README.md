# ModernPapers, Kevin Bryan, August 2025, MIT License

"Some books are to be tasted; others swallowed; and some few to be chewed and digested." - Bacon. Yet our academic work does not present this way. 

Reading PDFs sucks. Reading static documents sucked. Reading documents you have to Ctrl-F to look things up sucks. But all of our research, especially old research, is in these pdfs. Here's a one file html, using only free tier LLM access, that 1) rips your pdf or latex+bib articles into a standard XML format, 2) creates a clean frontend to display this to readers, 3) uses AI to provide a "short summary" for lay readers, 4) includes a more complex AI to query the document with high quality, quickly, and a clean UI. And it's free, even the AI. **UPDATE - I have now included an auto-image extractor which pulls out both raster and vector images and autotags them (it is 99% good but not perfect so of course check the rendering). Remaining tasks are summaries at various levels for the readers, and a second double-check of table accuracy.**

**NEW in v2.0:** This tool now includes a Python-based backend that automatically creates a local library of your processed papers. When you first run the app, you'll see a list of previously processed papers, and you can upload new ones. After processing, papers are saved to a `papers/` directory for easy access.

You can find examples at https://kevinbryanecon.com/ModernPapers/?data=BryanHoffmanSariri2025/paper.xml and https://kevinbryanecon.com/ModernPapers/?data=BryanGuzman2023/paper.xml.

My other tools are at https://kevinbryanecon.com/tools.html and on this Git. Of course, if you teach at a university, you must check out All Day TA (https://www.alldayta.com) which is this type of AI tool times one thousand.

## How to Set Up and Run Locally

#### 1. API Key
You will need a Google API key with access to the Gemini models. You can get a key from [aistudio.google.com](https://aistudio.google.com/app/apikey) or from a Google Cloud project.

To configure your key for local use:
1. Create a new file named `.env` in the main project directory. (You can copy the `.env.example` file for this).
2. Inside the `.env` file, add the following line, replacing `YOUR_API_KEY_HERE` with your actual key:
   ```
   GEMINI_API_KEY="YOUR_API_KEY_HERE"
   ```
The Python server will automatically load this key. It is not exposed in the browser.

#### 2. Running the Application
To run this locally on your computer:
1.  Navigate to the project folder in your command prompt or terminal.
2.  Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the local server:
    ```bash
    python server.py
    ```
4.  Open your browser and go to `http://localhost:8000`. You will see your paper library and the option to process a new paper.

**Note on Internet Connection:** The figure extraction feature for PDFs relies on the `pdf.js` library, which is loaded from an online CDN. If you are on a network that blocks access to `cdnjs.cloudflare.com`, the figure extraction may fail.

---

### Note for Developers: Using PDM

This project is set up with a standard `requirements.txt` file, but if you prefer to use [PDM](https://pdm-project.org/) for dependency management, you can convert it by following these steps:

1.  Make sure you have PDM installed (`pip install pdm`).
2.  Remove the existing `requirements.txt` file.
3.  Initialize the project with PDM: `pdm init`
4.  Add the dependencies: `pdm add flask requests python-dotenv`
5.  You can then run the server using `pdm run python server.py`.

---

Let me know if you modify and improve (I already have in mind an 'adaptive' paper that goes from 500 words for the public, to 2000 words Quanta magazine style, to a review article description, to full details, with users able to choose and expand at will and AI handling those summarizations). A new way to read academic research is en route.
