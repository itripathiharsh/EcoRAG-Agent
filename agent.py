import os
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
import google.generativeai as genai
from groq import Groq
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    question: str
    needs_retrieval: bool
    retrieved_documents: List[Dict[str, Any]]
    context: str
    answer: str
    reflection: str
    is_answer_relevant: bool

class QAAgent:
    def __init__(self, knowledge_base, groq_api_keys: List[str] = None, gemini_api_keys: List[str] = None):
        self.kb = knowledge_base
        self.current_provider = "Unknown"
        
        # Initialize API clients with multiple keys
        self.groq_clients = self._initialize_groq_clients(groq_api_keys)
        self.gemini_models = self._initialize_gemini_models(gemini_api_keys)
        
        # Track API health
        self.api_health = {
            'groq': True,
            'gemini': True
        }
        
        # Build the graph
        self.graph = self._build_graph()
        logger.info(f"Agent initialized with {len(self.groq_clients)} Groq keys and {len(self.gemini_models)} Gemini keys")
    
    def _initialize_groq_clients(self, api_keys: List[str]) -> List[Groq]:
        """Initialize multiple Groq clients"""
        clients = []
        if api_keys:
            for i, key in enumerate(api_keys):
                try:
                    client = Groq(api_key=key)
                    # Test the connection
                    client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    clients.append(client)
                    logger.info(f"Groq API key {i+1} initialized successfully")
                except Exception as e:
                    logger.warning(f"Groq API key {i+1} failed: {e}")
        return clients
    
    def _initialize_gemini_models(self, api_keys: List[str]) -> List[Any]:
        """Initialize multiple Gemini models with correct model names"""
        models = []
        if api_keys:
            for i, key in enumerate(api_keys):
                try:
                    genai.configure(api_key=key)
                    
                    # Try different model names - including new Gemini 2.5 models
                    model_names = [
                        "gemini-2.5-flash",   # New fast model
                        "gemini-2.5-pro",     # New pro model  
                        "gemini-1.5-pro",     # Previous version
                        "gemini-1.5-flash",   # Previous fast version
                    ]
                    working_model = None
                    
                    for model_name in model_names:
                        try:
                            logger.info(f"Trying Gemini model: {model_name}")
                            model = genai.GenerativeModel(model_name)
                            # Test the connection
                            test_response = model.generate_content("test")
                            if test_response.text:
                                working_model = model_name
                                logger.info(f"Gemini model {model_name} works!")
                                break
                            else:
                                logger.warning(f"Gemini model {model_name} no response")
                        except Exception as model_error:
                            logger.warning(f"Gemini model {model_name} failed: {str(model_error)[:100]}")
                            continue
                    
                    if working_model:
                        model = genai.GenerativeModel(working_model)
                        models.append(model)
                        logger.info(f"Gemini API key {i+1} initialized with model: {working_model}")
                    else:
                        logger.warning(f"Gemini API key {i+1}: No working model found")
                        
                except Exception as e:
                    logger.warning(f"Gemini API key {i+1} failed: {e}")
        return models
    
    def _call_llm_with_fallback(self, messages: List[Dict], prompt: str = None) -> str:
        """Call LLM with automatic fallback between providers and keys"""
        providers = []
        
        # Add available providers
        if self.groq_clients and self.api_health['groq']:
            providers.append('groq')
        if self.gemini_models and self.api_health['gemini']:
            providers.append('gemini')
        
        if not providers:
            return "Error: No working AI providers available. Please check API keys."
        
        # Try providers in random order for load balancing
        random.shuffle(providers)
        
        for provider in providers:
            try:
                if provider == 'groq':
                    # Try all Groq keys
                    for i, client in enumerate(self.groq_clients):
                        try:
                            response = client.chat.completions.create(
                                model="llama-3.1-8b-instant",
                                messages=messages,
                                temperature=0.1,
                                max_tokens=1024
                            )
                            self.current_provider = f"Groq-{i+1}"
                            self.api_health['groq'] = True
                            return response.choices[0].message.content
                        except Exception as e:
                            logger.warning(f"Groq key {i+1} failed: {e}")
                            continue
                
                elif provider == 'gemini':
                    # Try all Gemini keys
                    for i, model in enumerate(self.gemini_models):
                        try:
                            if prompt:
                                response = model.generate_content(prompt)
                            else:
                                # Convert messages to prompt
                                conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                                response = model.generate_content(conversation)
                            
                            if response.text:
                                self.current_provider = f"Gemini-{i+1}"
                                self.api_health['gemini'] = True
                                return response.text
                            else:
                                logger.warning(f"Gemini key {i+1} returned no text")
                                continue
                                
                        except Exception as e:
                            logger.warning(f"Gemini key {i+1} failed: {e}")
                            continue
                
            except Exception as e:
                logger.error(f"{provider} provider failed: {e}")
                self.api_health[provider] = False
                continue
        
        return "Error: All AI providers failed. Please check API keys and try again."
    
    def plan_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyze the question and decide if retrieval is needed"""
        question = state["question"]
        logger.info(f"Planning for question: {question}")
        
        planning_prompt = f"""
        Analyze the following question and determine if it requires retrieving information from a knowledge base about renewable energy, climate change, or sustainability.
        
        Question: {question}
        
        Return only 'YES' or 'NO'. Questions about facts, definitions, comparisons, or specific information need retrieval.
        Simple greetings or general questions don't need retrieval.
        """
        
        decision = self._call_llm_with_fallback([
            {"role": "system", "content": "You are a planning assistant. Analyze if a question needs information retrieval from a knowledge base."},
            {"role": "user", "content": planning_prompt}
        ])
        
        needs_retrieval = "YES" in decision.upper()
        logger.info(f"Planning decision: Retrieval needed = {needs_retrieval}")
        return {"needs_retrieval": needs_retrieval}
    
    def retrieve_node(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve relevant documents from knowledge base"""
        if not state["needs_retrieval"]:
            logger.info("Skipping retrieval")
            return {"retrieved_documents": [], "context": ""}
        
        question = state["question"]
        logger.info(f"Retrieving documents for: {question}")
        
        documents = self.kb.search(question, n_results=3)
        logger.info(f"Retrieved {len(documents)} documents")
        
        # Format context
        context = "\n\n".join([f"Source: {doc['metadata'].get('source', 'unknown')}\nContent: {doc['content']}" 
                              for doc in documents])
        
        for i, doc in enumerate(documents):
            logger.info(f"Document {i+1}: {doc['content'][:100]}...")
        
        return {"retrieved_documents": documents, "context": context}
    
    def answer_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate answer using retrieved context"""
        question = state["question"]
        context = state["context"]
        needs_retrieval = state["needs_retrieval"]
        
        logger.info(f"Generating answer using {self.current_provider}...")
        
        if needs_retrieval and context:
            prompt = f"""Based on the following context, please answer the question comprehensively. If the context doesn't contain relevant information, clearly state that.

Context:
{context}

Question: {question}

Please provide a detailed, accurate, and well-structured answer:"""
        else:
            prompt = f"""Please answer the following question based on your general knowledge:

Question: {question}

Please provide a helpful and accurate answer:"""
        
        answer = self._call_llm_with_fallback([
            {"role": "system", "content": "You are a helpful AI assistant that provides accurate and comprehensive answers."},
            {"role": "user", "content": prompt}
        ], prompt)
        
        logger.info(f"Generated answer: {answer[:100]}...")
        return {"answer": answer}
    
    def reflect_node(self, state: AgentState) -> Dict[str, Any]:
        """Reflect on the answer's relevance and quality"""
        question = state["question"]
        answer = state["answer"]
        context = state["context"]
        
        logger.info("Reflecting on answer quality...")
        
        reflection_prompt = f"""Evaluate the following Q&A pair for relevance, accuracy, and completeness:

Question: {question}
Answer: {answer}
Context Used: {context if context else "No specific context used"}

Please provide a comprehensive evaluation with:
1. Relevance score (1-10): How well the answer addresses the question
2. Accuracy score (1-10): How factually correct the answer is based on context
3. Completeness score (1-10): How comprehensive the answer is
4. Specific feedback on improvements needed
5. Overall assessment

Format your response clearly:"""
        
        reflection = self._call_llm_with_fallback([
            {"role": "system", "content": "You are an evaluation assistant that critically analyzes answer quality for relevance, accuracy, and completeness."},
            {"role": "user", "content": reflection_prompt}
        ], reflection_prompt)
        
        # Simple relevance check
        is_relevant = len(answer) > 20 and not answer.startswith("Error")
        
        logger.info(f"Reflection completed. Relevant: {is_relevant}")
        return {"reflection": reflection, "is_answer_relevant": is_relevant}
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("plan", self.plan_node)
        workflow.add_node("retrieve", self.retrieve_node)
        workflow.add_node("answer", self.answer_node)
        workflow.add_node("reflect", self.reflect_node)
        
        # Define edges
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "retrieve")
        workflow.add_edge("retrieve", "answer")
        workflow.add_edge("answer", "reflect")
        workflow.add_edge("reflect", END)
        
        return workflow.compile()
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Main method to ask a question"""
        logger.info(f"Starting agent workflow for: {question}")
        
        initial_state = {
            "question": question,
            "needs_retrieval": False,
            "retrieved_documents": [],
            "context": "",
            "answer": "",
            "reflection": "",
            "is_answer_relevant": False
        }
        
        # Execute the graph
        result = self.graph.invoke(initial_state)
        result['current_provider'] = self.current_provider
        
        logger.info("Agent workflow completed")
        return result
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check health of all API keys"""
        health_report = {
            'groq': [],
            'gemini': [],
            'overall_status': 'Unknown'
        }
        
        # Test Groq keys
        for i, client in enumerate(self.groq_clients):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": "Health check"}],
                    max_tokens=5
                )
                health_report['groq'].append({
                    'key_index': i + 1,
                    'status': 'Healthy',
                    'provider': 'Groq'
                })
            except Exception as e:
                health_report['groq'].append({
                    'key_index': i + 1,
                    'status': 'Unhealthy',
                    'error': str(e),
                    'provider': 'Groq'
                })
        
        # Test Gemini keys
        for i, model in enumerate(self.gemini_models):
            try:
                response = model.generate_content("Health check")
                health_report['gemini'].append({
                    'key_index': i + 1,
                    'status': 'Healthy',
                    'provider': 'Gemini'
                })
            except Exception as e:
                health_report['gemini'].append({
                    'key_index': i + 1,
                    'status': 'Unhealthy',
                    'error': str(e),
                    'provider': 'Gemini'
                })
        
        # Determine overall status
        healthy_groq = sum(1 for item in health_report['groq'] if item['status'] == 'Healthy')
        healthy_gemini = sum(1 for item in health_report['gemini'] if item['status'] == 'Healthy')
        
        if healthy_groq > 0 and healthy_gemini > 0:
            health_report['overall_status'] = 'Excellent'
        elif healthy_groq > 0 or healthy_gemini > 0:
            health_report['overall_status'] = 'Good'
        else:
            health_report['overall_status'] = 'Critical'
        
        return health_report