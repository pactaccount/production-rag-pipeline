import os
import json
import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
load_dotenv()

from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.cohere import CohereEmbedding

from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator

def run_eval():
    print("Parsing Apple 10-K PDF...")
    parser = LlamaParse(result_type="markdown", api_key=os.environ.get("LLAMA_CLOUD_API_KEY"))
    docs = parser.load_data("c24e7a28-5254-4dfa-9447-62aaa3c24bb1.pdf")
    
    # Just take the first few documents to save API tokens and time
    docs = docs[:5]

    print("Configuring LlamaIndex...")
    eval_llm = Gemini(model="models/gemini-2.5-flash", api_key=os.environ.get("GEMINI_API_KEY"))
    Settings.llm = eval_llm
    Settings.embed_model = CohereEmbedding(model_name="embed-english-v3.0", cohere_api_key=os.environ.get("COHERE_API_KEY"))
    
    print("Creating in-memory index...")
    index = VectorStoreIndex.from_documents(docs)
    query_engine = index.as_query_engine(similarity_top_k=2)

    queries = [
        "What is Apple's primary business strategy according to the document?",
        "What are the major risk factors mentioned regarding supply chain?",
        "How does Apple handle its intellectual property rights?"
    ]
    
    print("\nGenerated Questions:")
    for i, q in enumerate(queries):
        print(f"{i+1}. {q}")
        
    faithfulness_evaluator = FaithfulnessEvaluator(llm=eval_llm)
    relevancy_evaluator = RelevancyEvaluator(llm=eval_llm)

    faithfulness_results = []
    relevancy_results = []

    import time
    print("\nRunning Evaluation...")
    for query in queries:
        response = query_engine.query(query)
        
        # Evaluate Faithfulness (Hallucination check)
        faith_eval = faithfulness_evaluator.evaluate_response(query=query, response=response)
        faithfulness_results.append(faith_eval.passing)
        time.sleep(5)
        
        # Evaluate Relevancy (Answer relevance check)
        rel_eval = relevancy_evaluator.evaluate_response(query=query, response=response)
        relevancy_results.append(rel_eval.passing)
        print(f"Evaluated '{query}': Faithfulness={faith_eval.passing}, Relevancy={rel_eval.passing}")
        time.sleep(15)

    faithfulness_score = sum(faithfulness_results) / len(faithfulness_results) if faithfulness_results else 0
    relevancy_score = sum(relevancy_results) / len(relevancy_results) if relevancy_results else 0

    results = {
        "faithfulness": faithfulness_score,
        "relevancy": relevancy_score,
        "total_questions": len(queries)
    }

    print("\n--- RESULTS ---")
    print(json.dumps(results, indent=2))
    
    with open("eval_results.json", "w") as f:
        f.write(json.dumps(results, indent=2))
        
if __name__ == "__main__":
    run_eval()
