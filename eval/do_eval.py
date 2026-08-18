import os
import json
import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import context_precision, context_recall, faithfulness, answer_relevancy
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import CohereEmbeddings
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context

from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.cohere import CohereEmbedding

def run_eval():
    print("Parsing Apple 10-K PDF...")
    parser = LlamaParse(result_type="markdown", api_key=os.environ.get("LLAMA_CLOUD_API_KEY"))
    docs = parser.load_data("c24e7a28-5254-4dfa-9447-62aaa3c24bb1.pdf")
    
    print("Configuring LlamaIndex...")
    Settings.llm = Gemini(model="models/gemini-1.5-flash", api_key=os.environ.get("GEMINI_API_KEY"))
    Settings.embed_model = CohereEmbedding(model_name="embed-english-v3.0", cohere_api_key=os.environ.get("COHERE_API_KEY"))
    
    print("Creating in-memory index...")
    index = VectorStoreIndex.from_documents(docs)
    query_engine = index.as_query_engine(similarity_top_k=3)
    
    from langchain_core.documents import Document as LCDocument
    langchain_docs = [LCDocument(page_content=d.text) for d in docs]
    
    print("Setting up LLMs for Ragas...")
    eval_llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash")
    eval_embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=os.environ.get("COHERE_API_KEY"))
    
    print("Generating Synthetic Testset (3 questions)...")
    generator = TestsetGenerator.from_langchain(
        generator_llm=eval_llm,
        critic_llm=eval_llm,
        embeddings=eval_embeddings
    )
    
    testset = generator.generate_with_langchain_docs(
        langchain_docs[:3], 
        test_size=3, 
        distributions={simple: 1.0}
    )
    test_df = testset.to_pandas()
    
    answers = []
    contexts_list = []
    
    print("Querying the RAG engine...")
    for q in test_df['question']:
        response = query_engine.query(q)
        answers.append(str(response))
        contexts = [node.node.get_content() for node in response.source_nodes]
        contexts_list.append(contexts)
        
    data = {
        "question": test_df['question'].tolist(),
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": test_df['ground_truth'].tolist()
    }
    
    dataset = Dataset.from_dict(data)
    
    print("Evaluating...")
    result = evaluate(
        dataset,
        metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
        llm=eval_llm,
        embeddings=eval_embeddings
    )
    
    print("\n--- RESULTS ---")
    print(result)
    
    with open("eval_results.json", "w") as f:
        f.write(json.dumps({k: float(v) for k, v in result.items()}, indent=2))
        
if __name__ == "__main__":
    run_eval()
