import os
import pandas as pd
import phoenix as px
from phoenix.evals import (
    evaluate_dataframe
)
from phoenix.evals.metrics import HallucinationEvaluator
# CorrectnessEvaluator is the new QAEvaluator
from phoenix.evals.metrics import CorrectnessEvaluator
from phoenix.evals.models import LiteLLMModel
from phoenix.session.evaluation import get_qa_with_reference
from dotenv import load_dotenv

load_dotenv()

def run_phoenix_evals():
    print("Connecting to local Phoenix instance...")
    client = px.Client(endpoint="http://localhost:6006")
    
    print("Extracting QA pairs and references from traces...")
    # This extracts all traces of queries and the contexts retrieved
    try:
        queries_df = get_qa_with_reference(client)
        if queries_df.empty:
            print("No trace data found. Please ask some questions in the UI first.")
            return
    except Exception as e:
        print(f"Error fetching traces: {e}")
        print("Please ensure you have asked some questions in the UI before running evaluations.")
        return

    print(f"Found {len(queries_df)} queries to evaluate.")

    # We need an LLM to act as the evaluator. 
    # Since we have Gemini API Key, we can use LiteLLMModel to route to Gemini.
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment. Evaluation requires an LLM API key.")
        return
        
    print("Setting up Evaluator LLM (Gemini 2.5 Flash)...")
    # LiteLLM allows using any model
    eval_model = LiteLLMModel(
        model="gemini/gemini-2.5-flash",
        api_key=api_key,
        temperature=0.0
    )

    print("Running Hallucination Evaluator...")
    hallucination_evaluator = HallucinationEvaluator(model=eval_model)
    
    print("Running QA Correctness Evaluator...")
    qa_evaluator = CorrectnessEvaluator(model=eval_model)

    # Run the evaluations
    results = evaluate_dataframe(
        dataframe=queries_df,
        evaluators=[hallucination_evaluator, qa_evaluator],
        provide_explanation=True,
    )

    print("\n--- Evaluation Complete ---")
    
    # Extract results
    hallucination_results = results[0]
    qa_results = results[1]
    
    print(f"\nHallucination Results (Is the answer hallucinated?):")
    print(hallucination_results['label'].value_counts())
    
    print(f"\nQA Correctness Results (Is the answer correct?):")
    print(qa_results['label'].value_counts())

    print("\nLogs have been pushed to Phoenix. Open http://localhost:6006 to view the evaluation traces.")
    
    # Log the evaluations back to Phoenix to view them in the UI
    try:
        px.Client().log_evaluations(
            HallucinationEval=hallucination_results,
            QACorrectnessEval=qa_results,
        )
        print("Successfully logged evaluation results back to Phoenix!")
    except Exception as e:
        print(f"Could not log back to Phoenix: {e}")

if __name__ == "__main__":
    run_phoenix_evals()
