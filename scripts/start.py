import sys

def main():
    print("=============================================")
    print(" Support Ticket AI - Quick Start Guide")
    print("=============================================\n")
    print("To run the application, you will need two separate terminal windows.")
    print("\nTerminal 1: Start the FastAPI Backend")
    print("---------------------------------------------")
    print(".venv\\Scripts\\python.exe -m uvicorn app.main:app --reload\n")
    
    print("Terminal 2: Start the Streamlit UI")
    print("---------------------------------------------")
    print(".venv\\Scripts\\streamlit.exe run ui\\streamlit_app.py\n")
    
    print("Notes:")
    print("- Ensure your local Ollama instance is running at http://localhost:11434 before testing RAG queries.")
    print("- Backend runs at: http://127.0.0.1:8000")
    print("- Streamlit UI runs at: http://localhost:8501 (by default)\n")

if __name__ == "__main__":
    main()
