import os
from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import context_precision, context_recall, faithfulness, answer_relevancy
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import CohereEmbeddings
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context

from app.services.rag import get_index, get_vector_store
from llama_index.core import VectorStoreIndex

def run_evaluation():
    print("Setting up LLM for Ragas evaluation (using LangChain wrapper for Gemini)...")
    eval_llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash")
    eval_embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=os.environ.get("COHERE_API_KEY"))
    
    print("Connecting to Vector Store to fetch documents...")
    index = get_index()
    if index is None:
        print("Error: No index found. Please ingest documents first.")
        return
        
    # We need to extract the raw text from the index to generate synthetic questions.
    # LlamaIndex nodes can be extracted directly.
    nodes = index.docstore.docs.values()
    if not nodes:
        print("Error: No documents found in the docstore.")
        return
        
    # Convert LlamaIndex nodes to Langchain documents for Ragas TestsetGenerator
    from langchain_core.documents import Document as LCDocument
    langchain_docs = [LCDocument(page_content=n.get_content()) for n in nodes]
    
    # Take a small sample of documents to avoid huge API bills/rate limits during synthetic generation
    sample_docs = langchain_docs[:20] 

    print("Generating Synthetic Test Dataset (this may take a minute)...")
    generator = TestsetGenerator.from_langchain(
        generator_llm=eval_llm,
        critic_llm=eval_llm,
        embeddings=eval_embeddings
    )
    
    # Generate 5 questions. (You can increase this to 50 for a full enterprise evaluation, 
    # but be aware of API rate limits on free tiers)
    testset = generator.generate_with_langchain_docs(
        sample_docs, 
        test_size=5, 
        distributions={simple: 0.5, reasoning: 0.25, multi_context: 0.25}
    )
    
    test_df = testset.to_pandas()
    print("\nGenerated Questions:")
    for i, q in enumerate(test_df['question']):
        print(f"{i+1}. {q}")
        
    print("\nRetrieving answers and contexts from RAG pipeline...")
    # Create the advanced query engine with Cohere Reranking
    from llama_index.postprocessor.cohere_rerank import CohereRerank
    from llama_index.core.postprocessor import MetadataReplacementPostProcessor
    
    cohere_rerank = CohereRerank(api_key=os.environ.get("COHERE_API_KEY"), top_n=3)
    metadata_replacement = MetadataReplacementPostProcessor(target_metadata_key="window")
    
    query_engine = index.as_query_engine(
        similarity_top_k=10,
        node_postprocessors=[metadata_replacement, cohere_rerank]
    )
    
    answers = []
    contexts_list = []
    
    for q in test_df['question']:
        response = query_engine.query(q)
        answers.append(str(response))
        # Extract source nodes as context
        contexts = [node.node.get_content() for node in response.source_nodes]
        contexts_list.append(contexts)
        
    data = {
        "question": test_df['question'].tolist(),
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": test_df['ground_truth'].tolist()
    }
    
    dataset = Dataset.from_dict(data)
    
    print("\nRunning Ragas Evaluation (Faithfulness, Relevance, Precision, Recall)...")
    metrics = [
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy
    ]
    
    result = evaluate(
        dataset,
        metrics=metrics,
        llm=eval_llm,
        embeddings=eval_embeddings
    )
    
    print("\n--- Evaluation Results ---")
    print(result)
    
if __name__ == "__main__":
    run_evaluation()
