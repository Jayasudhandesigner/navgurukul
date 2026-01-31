from app.services.context_engine import context_engine

def test_context_engine():
    print("Testing Context Engine Logic...")
    
    # 1. Test Transcript Update
    context_engine.update_transcript("I am building a backend with Python and FastAPI.")
    ctx = context_engine.get_context()
    print(f"Transcript Context: {ctx}")
    
    if "python" in ctx["keywords"] and "fastapi" in ctx["keywords"]:
        print("[PASS] Transcript Keywords Detected")
    else:
        print("[FAIL] Transcript Keywords Missing")
        
    # 2. Test Visual Update
    context_engine.update_visuals("Architecture Diagram\nUsing React and AWS")
    ctx = context_engine.get_context()
    print(f"Visual Context: {ctx}")
    
    if "react" in ctx["keywords"] and "aws" in ctx["keywords"]:
         print("[PASS] Visual Keywords Detected")
    else:
         print("[FAIL] Visual Keywords Missing")
         
    if "Architecture Diagram" in ctx["topics"]:
         print("[PASS] Topic Detected (Heuristic)")
    else:
         print("[FAIL] Topic Missing")

if __name__ == "__main__":
    test_context_engine()
