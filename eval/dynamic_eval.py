import os
import json
import time
import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
load_dotenv()

from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.core.evaluation import (
    FaithfulnessEvaluator,
    RelevancyEvaluator,
    DatasetGenerator
)

def evaluate_document(file_path: str, doc_name: str, num_questions: int = 5):
    print(f"\n--- Evaluating {doc_name} ---")
    
    # 1. Parse Document
    print(f"Parsing {doc_name}...")
    parser = LlamaParse(result_type="markdown", api_key=os.environ.get("LLAMA_CLOUD_API_KEY"))
    docs = parser.load_data(file_path)
    
    # We only take the first few documents to save tokens and avoid rate limits during generation
    docs = docs[:5]

    # 2. Configure Settings
    print("Configuring LlamaIndex with Gemini 2.5 Flash as Judge...")
    eval_llm = Gemini(model="models/gemini-2.5-flash", api_key=os.environ.get("GEMINI_API_KEY"))
    Settings.llm = eval_llm
    Settings.embed_model = CohereEmbedding(model_name="embed-english-v3.0", cohere_api_key=os.environ.get("COHERE_API_KEY"))
    
    # 3. Create Index and Query Engine
    print("Creating in-memory index...")
    index = VectorStoreIndex.from_documents(docs)
    query_engine = index.as_query_engine(similarity_top_k=2)

    # 4. Generate Synthetic Questions
    print(f"Generating {num_questions} synthetic questions from {doc_name} chunks...")
    data_generator = DatasetGenerator.from_documents(
        docs, 
        llm=eval_llm,
        num_questions_per_chunk=1,
        show_progress=True
    )
    
    questions = data_generator.generate_questions_from_nodes()
    # Limit to num_questions
    questions = questions[:num_questions]
    
    print("\nGenerated Questions:")
    for i, q in enumerate(questions):
        print(f"{i+1}. {q}")
        
    # 5. Initialize Evaluators
    faithfulness_evaluator = FaithfulnessEvaluator(llm=eval_llm)
    relevancy_evaluator = RelevancyEvaluator(llm=eval_llm)

    faithfulness_results = []
    relevancy_results = []
    evaluation_details = []

    print("\nRunning Evaluation...")
    for query in questions:
        print(f"\nQuery: {query}")
        try:
            # Query the RAG engine
            response = query_engine.query(query)
            
            # Rate limiting delay
            time.sleep(2)
            
            # Evaluate Faithfulness
            faith_eval = faithfulness_evaluator.evaluate_response(query=query, response=response)
            faithfulness_results.append(faith_eval.passing)
            
            # Rate limiting delay
            time.sleep(2)
            
            # Evaluate Relevancy
            rel_eval = relevancy_evaluator.evaluate_response(query=query, response=response)
            relevancy_results.append(rel_eval.passing)
            
            print(f" -> Faithfulness: {'PASS' if faith_eval.passing else 'FAIL'}")
            print(f" -> Relevancy:    {'PASS' if rel_eval.passing else 'FAIL'}")
            
            evaluation_details.append({
                "query": query,
                "response": str(response),
                "faithfulness": bool(faith_eval.passing),
                "relevancy": bool(rel_eval.passing)
            })
            
        except Exception as e:
            print(f"Error evaluating query: {e}")
            
    # 6. Calculate Metrics
    faithfulness_score = sum(faithfulness_results) / len(faithfulness_results) if faithfulness_results else 0
    relevancy_score = sum(relevancy_results) / len(relevancy_results) if relevancy_results else 0

    results = {
        "document": doc_name,
        "metrics": {
            "faithfulness_score": faithfulness_score,
            "relevancy_score": relevancy_score,
            "total_questions": len(questions)
        },
        "details": evaluation_details
    }
    
    return results

def run_eval():
    print("Starting Comprehensive RAG Evaluation...\n")
    
    # Evaluate Ford 10-K
    # Assuming c24e7a28-5254-4dfa-9447-62aaa3c24bb1.pdf is the Ford document based on previous run traces
    ford_results = evaluate_document("c24e7a28-5254-4dfa-9447-62aaa3c24bb1.pdf", "Ford 10-K", num_questions=5)
    
    # Evaluate Apple 10-K
    apple_results = evaluate_document("data/apple_10k.pdf", "Apple 10-K", num_questions=5)
    
    final_report = {
        "overall_summary": "Comprehensive RAG Evaluation on Multiple Documents",
        "evaluations": [ford_results, apple_results]
    }
    
    # Save the output
    output_path = "eval/eval_results.json"
    with open(output_path, "w") as f:
        f.write(json.dumps(final_report, indent=2))
        
    print(f"\nEvaluation Complete! Results saved to {output_path}")

if __name__ == "__main__":
    run_eval()
