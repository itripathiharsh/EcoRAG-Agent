import gradio as gr
import os
from knowledge_base import KnowledgeBase
from agent import QAAgent
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RAGChatbot:
    def __init__(self):
        self.kb = None
        self.agent = None
        self.initialized = False
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize knowledge base and agent with multiple API key support"""
        try:
            # Initialize knowledge base
            self.kb = KnowledgeBase()
            self.kb.load_sample_data()
            
            # Get multiple API keys from environment
            groq_api_keys = [
                os.getenv("GROQ_API_KEY"),
                os.getenv("GROQ_API_KEY_2"),
                os.getenv("GROQ_API_KEY_3")
            ]
            
            gemini_api_keys = [
                os.getenv("GEMINI_API_KEY"),
                os.getenv("GEMINI_API_KEY_2"), 
                os.getenv("GEMINI_API_KEY_3")
            ]
            
            # Filter out None values
            groq_api_keys = [key for key in groq_api_keys if key]
            gemini_api_keys = [key for key in gemini_api_keys if key]
            
            if not groq_api_keys and not gemini_api_keys:
                raise ValueError("Please set at least one GROQ_API_KEY or GEMINI_API_KEY in environment variables")
            
            print(f"Loaded {len(groq_api_keys)} Groq API keys and {len(gemini_api_keys)} Gemini API keys")
            
            # Initialize agent with API keys
            self.agent = QAAgent(self.kb, groq_api_keys, gemini_api_keys)
            self.initialized = True
            print("RAG Chatbot initialized successfully!")
            
            # Show API health status
            health = self.agent.check_api_health()
            print(f"API Health: {health['overall_status']}")
            
        except Exception as e:
            print(f"Initialization failed: {e}")
            self.initialized = False
    
    def process_question(self, question: str):
        """Process question and return formatted response"""
        if not self.initialized:
            return "System not initialized. Please check API keys and try again."
        
        if not question.strip():
            return "Please enter a question."
        
        try:
            # Process the question
            start_time = time.time()
            result = self.agent.ask_question(question)
            processing_time = time.time() - start_time
            
            # Get API health for status display
            health = self.agent.check_api_health()
            
            # Format response with professional styling
            response = f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; color: white; margin-bottom: 20px;">
    <h2 style="margin: 0; font-size: 20px; font-weight: 600;">Question</h2>
    <p style="margin: 10px 0 0 0; font-size: 16px;">{question}</p>
</div>

<div style="background: var(--background-fill-secondary); padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid var(--border-color-primary);">
    <h3 style="color: #28a745; margin-top: 0; display: flex; align-items: center; font-size: 18px;">
        Answer
        <span style="margin-left: auto; font-size: 12px; background: #28a745; color: white; padding: 4px 10px; border-radius: 12px;">
            {result.get('current_provider', 'Unknown')}
        </span>
    </h3>
    <div style="font-size: 14px; line-height: 1.6; color: var(--body-text-color);">
        {result['answer']}
    </div>
</div>

<div style="background: var(--background-fill-secondary); padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid var(--border-color-primary);">
    <h3 style="color: #856404; margin-top: 0; font-size: 18px;">
        Quality Evaluation
    </h3>
    <div style="font-size: 14px; line-height: 1.6; color: var(--body-text-color);">
        {result['reflection']}
    </div>
</div>

<div style="background: var(--background-fill-secondary); padding: 20px; border-radius: 8px; border-left: 4px solid #17a2b8; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid var(--border-color-primary);">
    <h4 style="color: #0c5460; margin-top: 0; font-size: 16px;">
        Performance Metrics
    </h4>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px;">
        <div style="background: var(--background-fill-primary); padding: 12px; border-radius: 6px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.1); border: 1px solid var(--border-color-primary);">
            <div style="font-size: 18px; font-weight: bold; color: #28a745;">{processing_time:.2f}s</div>
            <div style="font-size: 11px; color: var(--body-text-color); opacity: 0.7;">Processing Time</div>
        </div>
        <div style="background: var(--background-fill-primary); padding: 12px; border-radius: 6px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.1); border: 1px solid var(--border-color-primary);">
            <div style="font-size: 18px; font-weight: bold; color: #17a2b8;">{len(result['retrieved_documents'])}</div>
            <div style="font-size: 11px; color: var(--body-text-color); opacity: 0.7;">Documents Retrieved</div>
        </div>
        <div style="background: var(--background-fill-primary); padding: 12px; border-radius: 6px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.1); border: 1px solid var(--border-color-primary);">
            <div style="font-size: 18px; font-weight: bold; color: {'#28a745' if result['is_answer_relevant'] else '#dc3545'};">
                {'Yes' if result['is_answer_relevant'] else 'No'}
            </div>
            <div style="font-size: 11px; color: var(--body-text-color); opacity: 0.7;">Relevant Answer</div>
        </div>
        <div style="background: var(--background-fill-primary); padding: 12px; border-radius: 6px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.1); border: 1px solid var(--border-color-primary);">
            <div style="font-size: 18px; font-weight: bold; color: {'#28a745' if result['needs_retrieval'] else '#6c757d'};">
                {'Yes' if result['needs_retrieval'] else 'No'}
            </div>
            <div style="font-size: 11px; color: var(--body-text-color); opacity: 0.7;">Retrieval Used</div>
        </div>
    </div>
    
    <div style="background: var(--background-fill-primary); padding: 15px; border-radius: 6px; margin-top: 10px; border: 1px solid var(--border-color-primary);">
        <h5 style="margin: 0 0 10px 0; color: var(--body-text-color); font-weight: 600; font-size: 14px;">System Configuration</h5>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px;">
            <div style="color: var(--body-text-color);">
                <strong style="color: var(--body-text-color);">AI Provider:</strong> {result.get('current_provider', 'Unknown')}
            </div>
            <div style="color: var(--body-text-color);">
                <strong style="color: var(--body-text-color);">API Health:</strong> 
                <span style="color: {'#28a745' if health['overall_status'] == 'Excellent' else '#ffc107' if health['overall_status'] == 'Good' else '#dc3545'}">
                    {health['overall_status']}
                </span>
            </div>
            <div style="color: var(--body-text-color);">
                <strong style="color: var(--body-text-color);">Groq Keys:</strong> 
                <span style="color: {'#28a745' if sum(1 for item in health['groq'] if item['status'] == 'Healthy') == 3 else '#ffc107' if sum(1 for item in health['groq'] if item['status'] == 'Healthy') >= 1 else '#dc3545'}">
                    {sum(1 for item in health['groq'] if item['status'] == 'Healthy')}/{len(health['groq'])} active
                </span>
            </div>
            <div style="color: var(--body-text-color);">
                <strong style="color: var(--body-text-color);">Gemini Keys:</strong> 
                <span style="color: {'#28a745' if sum(1 for item in health['gemini'] if item['status'] == 'Healthy') == 3 else '#ffc107' if sum(1 for item in health['gemini'] if item['status'] == 'Healthy') >= 1 else '#dc3545'}">
                    {sum(1 for item in health['gemini'] if item['status'] == 'Healthy')}/{len(health['gemini'])} active
                </span>
            </div>
        </div>
    </div>
</div>
"""
            
            return response
            
        except Exception as e:
            error_response = f"""
<div style="background: var(--background-fill-secondary); padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; color: var(--body-text-color); margin: 20px 0; border: 1px solid #f5c6cb;">
    <h3 style="margin-top: 0; font-size: 16px;">
        System Error
    </h3>
    <div style="background: var(--background-fill-primary); padding: 12px; border-radius: 4px; margin-top: 10px; border: 1px solid #f5c6cb;">
        <strong>Error Details:</strong><br>
        <code style="color: #dc3545; word-break: break-word; font-size: 12px;">{str(e)}</code>
    </div>
    <div style="margin-top: 12px; font-size: 13px;">
        Check your API keys, internet connection, and try again.
    </div>
</div>
"""
            return error_response

def create_gradio_interface():
    """Create and launch professional Gradio interface"""
    chatbot = RAGChatbot()
    
    # Sample questions data
    sample_questions = [
        "What are the benefits of renewable energy?",
        "How does climate change affect biodiversity?",
        "Explain the three pillars of sustainability",
        "What is the cost trend for solar power?",
        "How does wind energy work?",
        "What are the main causes of climate change?",
        "Compare solar and wind energy advantages",
        "What is environmental sustainability?",
        "How does hydroelectric power generation work?",
        "What are the economic impacts of renewable energy?"
    ]
    
    with gr.Blocks(
        title="RAG AI Agent - Professional",
        theme=gr.themes.Soft(),
        css="""
        /* Use Gradio's built-in theme variables for better light/dark support */
        .gradio-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--background-fill-primary);
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 8px;
            color: white;
            margin-bottom: 20px;
            border: none;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        }

        .sidebar {
            background: var(--background-fill-secondary);
            padding: 18px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color-primary);
        }

        .main-content {
            background: var(--background-fill-secondary);
            padding: 22px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color-primary);
        }

        .question-btn {
            width: 100%;
            text-align: left;
            margin: 4px 0;
            padding: 10px 12px;
            background: var(--button-secondary-background-fill);
            border: 1px solid var(--border-color-primary);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 13px;
            color: var(--button-secondary-text-color);
        }
        .question-btn:hover {
            background: #007bff;
            color: white;
            border-color: #007bff;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,123,255,0.2);
        }

        .status-card {
            background: var(--background-fill-secondary);
            padding: 18px;
            border-radius: 6px;
            border-left: 4px solid #28a745;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color-primary);
        }

        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 6px 0;
            color: var(--body-text-color);
            font-size: 13px;
        }
        .status-label {
            font-weight: 600;
        }
        .status-value {
            font-weight: 600;
            color: #28a745;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 14px;
            color: white;
        }
        .btn-secondary {
            background: var(--button-secondary-background-fill);
            border: 1px solid var(--border-color-primary);
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            color: var(--button-secondary-text-color);
        }

        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 6px;
            color: white;
            font-weight: 500;
        }

        /* Dark Mode Adjustments */
        @media (prefers-color-scheme: dark) {
            .header {
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            }
            .sidebar,
            .main-content,
            .status-card {
                background: #1f2937 !important;
                border-color: #374151 !important;
            }
            .question-btn {
                background: #2d3748;
                color: #e2e8f0;
                border-color: #4a5568;
            }
            .question-btn:hover {
                background: #007bff;
                color: white;
            }
            .status-label {
                color: #e2e8f0;
            }
            .footer {
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .gradio-container {
                padding: 8px;
            }
            .header h1 {
                font-size: 1.6em;
            }
        }
        """
    ) as demo:
        
        # Header Section
        gr.HTML("""
        <div class="header">
            <h1 style="margin: 0; font-size: 2.2em; font-weight: 600;">RAG AI Agent</h1>
            <p style="margin: 12px 0 0 0; font-size: 1.1em; opacity: 0.95; font-weight: 300;">
                Enterprise Question Answering with Multi-LLM Fallback
            </p>
            <div style="margin-top: 20px; display: flex; gap: 12px; flex-wrap: wrap;">
                <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-weight: 500; font-size: 13px;">Smart Retrieval</span>
                <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-weight: 500; font-size: 13px;">Multi-API Fallback</span>
                <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-weight: 500; font-size: 13px;">Quality Evaluation</span>
            </div>
        </div>
        """)
        
        with gr.Row(equal_height=False):
            # Left Sidebar - Sample Questions
            with gr.Column(scale=1, min_width=320):
                with gr.Group(elem_classes=["sidebar"]):
                    gr.Markdown("### Sample Questions")
                    gr.Markdown("Click any question below to try the system:")
                    
                    # Create clickable question buttons
                    question_components = []
                    for i, question in enumerate(sample_questions):
                        btn = gr.Button(
                            question,
                            size="sm",
                            variant="secondary",
                            elem_classes=["question-btn"],
                            min_width=280
                        )
                        question_components.append(btn)
                
                # System Architecture
                with gr.Group(elem_classes=["sidebar"]):
                    gr.Markdown("### System Architecture")
                    gr.Markdown("""
                    **Multi-LLM Providers:**
                    - Groq (3 keys) - High performance
                    - Gemini (3 keys) - Advanced reasoning
                    
                    **Processing Pipeline:**
                    1. Plan - Query analysis
                    2. Retrieve - Knowledge base search
                    3. Generate - Multi-LLM response
                    4. Evaluate - Quality assessment
                    """, elem_classes=["dark-text"])
                
                # Live Status
                with gr.Group(elem_classes=["sidebar"]):
                    gr.Markdown("### System Status")
                    status_html = gr.HTML(
                        value="<div class='status-card'><h4 style='color: var(--body-text-color); font-size: 15px;'>System Status</h4><p style='color: var(--body-text-color); opacity: 0.7; font-size: 13px;'>Initializing...</p></div>"
                    )
            
            # Main Content Area
            with gr.Column(scale=2):
                with gr.Group(elem_classes=["main-content"]):
                    gr.Markdown("### Ask Your Question")
                    
                    question_input = gr.Textbox(
                        label="",
                        placeholder="Enter your question about renewable energy, climate change, sustainability, or environmental topics...",
                        lines=3,
                        show_label=False,
                        elem_id="question-input"
                    )
                    
                    with gr.Row():
                        submit_btn = gr.Button(
                            "Generate Answer", 
                            variant="primary", 
                            elem_id="submit-btn"
                        )
                        clear_btn = gr.Button("Clear", variant="secondary")
                        status_btn = gr.Button("Check Health", variant="secondary")
                
                with gr.Group(elem_classes=["main-content"]):
                    gr.Markdown("### Response")
                    output = gr.HTML(
                        value="""
                        <div style='text-align: center; padding: 40px 20px; color: var(--body-text-color); opacity: 0.7;'>
                            <h3 style='color: var(--body-text-color); margin-bottom: 12px;'>Ready for Your Question</h3>
                            <p style='margin-bottom: 16px;'>Ask anything about renewable energy, climate change, or sustainability</p>
                            <div style='display: flex; justify-content: center; gap: 8px; margin-top: 16px; flex-wrap: wrap;'>
                                <span style='background: var(--background-fill-primary); color: var(--body-text-color); padding: 6px 12px; border-radius: 16px; font-size: 12px; border: 1px solid var(--border-color-primary);'>Smart Retrieval</span>
                                <span style='background: var(--background-fill-primary); color: var(--body-text-color); padding: 6px 12px; border-radius: 16px; font-size: 12px; border: 1px solid var(--border-color-primary);'>Quality Evaluation</span>
                                <span style='background: var(--background-fill-primary); color: var(--body-text-color); padding: 6px 12px; border-radius: 16px; font-size: 12px; border: 1px solid var(--border-color-primary);'>Fast Response</span>
                            </div>
                        </div>
                        """
                    )
        
        # Footer
        gr.HTML("""
        <div class="footer">
            <p style="margin: 0; font-size: 14px;">
                Built with LangGraph • ChromaDB • Groq • Gemini
            </p>
            <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">
                6 API Keys Load Balancing | Automatic Failover | Performance Analytics
            </p>
        </div>
        """)
        
        # Update status function
        def update_status():
            if chatbot.initialized and chatbot.agent:
                health = chatbot.agent.check_api_health()
                groq_healthy = sum(1 for item in health['groq'] if item['status'] == 'Healthy')
                gemini_healthy = sum(1 for item in health['gemini'] if item['status'] == 'Healthy')
                
                status_color = "#28a745" if health['overall_status'] == 'Excellent' else "#ffc107" if health['overall_status'] == 'Good' else "#dc3545"
                
                status_html = f"""
                <div class="status-card">
                    <h4 style="margin: 0 0 16px 0; color: {status_color}; font-size: 15px;">
                        System Status: {health['overall_status']}
                    </h4>
                    <div style="display: grid; gap: 10px;">
                        <div class="status-item">
                            <span class="status-label">Groq API Keys:</span>
                            <span class="status-value">{groq_healthy}/3 active</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Gemini API Keys:</span>
                            <span class="status-value">{gemini_healthy}/3 active</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Knowledge Base:</span>
                            <span class="status-value">Ready</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Agent Workflow:</span>
                            <span class="status-value">Active</span>
                        </div>
                    </div>
                </div>
                """
                return status_html
            else:
                return """
                <div class="status-card">
                    <h4 style="margin: 0 0 12px 0; color: #dc3545; font-size: 15px;">System Offline</h4>
                    <p style="margin: 0; color: var(--body-text-color); opacity: 0.7; font-size: 13px;">Please check system initialization</p>
                </div>
                """
        
        # Function to handle sample question clicks
        def handle_question_click(question):
            return question
        
        # Connect all sample question buttons
        for btn in question_components:
            btn.click(
                fn=handle_question_click,
                inputs=[btn],
                outputs=[question_input]
            )
        
        # Event handlers
        submit_btn.click(
            fn=chatbot.process_question,
            inputs=[question_input],
            outputs=[output]
        )
        
        clear_btn.click(
            fn=lambda: ("", """
            <div style='text-align: center; padding: 40px 20px; color: var(--body-text-color); opacity: 0.7;'>
                <h3 style='color: var(--body-text-color); margin-bottom: 12px;'>Ready for Your Question</h3>
                <p style='margin-bottom: 16px;'>Ask anything about renewable energy, climate change, or sustainability</p>
                <div style='display: flex; justify-content: center; gap: 8px; margin-top: 16px; flex-wrap: wrap;'>
                    <span style='background: var(--background-fill-primary); color: var(--body-text-color); padding: 6px 12px; border-radius: 16px; font-size: 12px; border: 1px solid var(--border-color-primary);'>Smart Retrieval</span>
                    <span style='background: var(--background-fill-primary); color: var(--body-text-color); padding: 6px 12px; border-radius: 16px; font-size: 12px; border: 1px solid var(--border-color-primary);'>Quality Evaluation</span>
                    <span style='background: var(--background-fill-primary); color: var(--body-text-color); padding: 6px 12px; border-radius: 16px; font-size: 12px; border: 1px solid var(--border-color-primary);'>Fast Response</span>
                </div>
            </div>
            """),
            inputs=[],
            outputs=[question_input, output]
        )
        
        status_btn.click(
            fn=update_status,
            inputs=[],
            outputs=[status_html]
        )
        
        question_input.submit(
            fn=chatbot.process_question,
            inputs=[question_input],
            outputs=[output]
        )
        
        demo.load(
            fn=update_status,
            inputs=[],
            outputs=[status_html]
        )
    
    return demo

if __name__ == "__main__":
    print("Starting Advanced RAG AI Agent...")
    print("Knowledge Base: Loading...")
    print("AI Agent: Initializing with Multi-LLM Fallback...") 
    print("Web Interface: Starting...")
    
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
        inbrowser=True
    )