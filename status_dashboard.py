import os
import time
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq
from knowledge_base import KnowledgeBase
from agent import QAAgent

load_dotenv()

class SystemStatusDashboard:
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_response_time': 0,
            'providers_used': {},
            'last_health_check': None
        }
    
    def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'uptime': str(datetime.now() - self.start_time),
            'api_status': self.check_api_status(),
            'knowledge_base_status': self.check_kb_status(),
            'performance_metrics': self.stats,
            'recommendations': self.get_recommendations()
        }
        return status
    
    def check_api_status(self):
        """Check status of all API keys"""
        api_status = {
            'groq': [],
            'gemini': [],
            'overall': 'Unknown'
        }
        
        # Check Groq keys
        groq_keys = [
            ("GROQ_API_KEY", os.getenv("GROQ_API_KEY")),
            ("GROQ_API_KEY_2", os.getenv("GROQ_API_KEY_2")),
            ("GROQ_API_KEY_3", os.getenv("GROQ_API_KEY_3"))
        ]
        
        for key_name, key_value in groq_keys:
            if key_value:
                try:
                    client = Groq(api_key=key_value)
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": "ping"}],
                        max_tokens=5
                    )
                    api_status['groq'].append({
                        'name': key_name,
                        'status': 'Healthy',
                        'response': 'Working'
                    })
                except Exception as e:
                    api_status['groq'].append({
                        'name': key_name,
                        'status': 'Unhealthy',
                        'error': str(e)[:100]
                    })
            else:
                api_status['groq'].append({
                    'name': key_name,
                    'status': 'Not Set',
                    'error': 'Key not configured'
                })
        
        # Check Gemini keys
        gemini_keys = [
            ("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY")),
            ("GEMINI_API_KEY_2", os.getenv("GEMINI_API_KEY_2")),
            ("GEMINI_API_KEY_3", os.getenv("GEMINI_API_KEY_3"))
        ]
        
        for key_name, key_value in gemini_keys:
            if key_value:
                try:
                    genai.configure(api_key=key_value)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    response = model.generate_content("ping")
                    api_status['gemini'].append({
                        'name': key_name,
                        'status': 'Healthy',
                        'response': 'Working'
                    })
                except Exception as e:
                    api_status['gemini'].append({
                        'name': key_name,
                        'status': 'Unhealthy',
                        'error': str(e)[:100]
                    })
            else:
                api_status['gemini'].append({
                    'name': key_name,
                    'status': 'Not Set',
                    'error': 'Key not configured'
                })
        
        # Determine overall status
        healthy_groq = sum(1 for item in api_status['groq'] if 'Healthy' in item['status'])
        healthy_gemini = sum(1 for item in api_status['gemini'] if 'Healthy' in item['status'])
        
        if healthy_groq >= 2 and healthy_gemini >= 1:
            api_status['overall'] = 'Excellent'
        elif healthy_groq >= 1:
            api_status['overall'] = 'Good'
        else:
            api_status['overall'] = 'Critical'
        
        return api_status
    
    def check_kb_status(self):
        """Check knowledge base status"""
        try:
            kb = KnowledgeBase()
            results = kb.search("test", n_results=1)
            return {
                'status': 'Healthy',
                'documents_count': 'Loaded',
                'search_working': True
            }
        except Exception as e:
            return {
                'status': 'Unhealthy',
                'error': str(e),
                'search_working': False
            }
    
    def get_recommendations(self):
        """Get system recommendations"""
        api_status = self.check_api_status()
        recommendations = []
        
        healthy_groq = sum(1 for item in api_status['groq'] if 'Healthy' in item['status'])
        healthy_gemini = sum(1 for item in api_status['gemini'] if 'Healthy' in item['status'])
        
        if healthy_groq == 0:
            recommendations.append("CRITICAL: Add working Groq API keys")
        elif healthy_groq == 1:
            recommendations.append("WARNING: Only 1 Groq key working - add backups")
        
        if healthy_gemini == 0:
            recommendations.append("WARNING: No Gemini keys working - add for backup")
        
        if healthy_groq >= 2 and healthy_gemini >= 1:
            recommendations.append("OPTIMAL: System well configured with fallbacks")
        
        if self.stats['failed_queries'] > self.stats['successful_queries'] * 0.1:
            recommendations.append("HIGH: Query failure rate is high - check logs")
        
        return recommendations
    
    def print_dashboard(self):
        """Print a beautiful status dashboard"""
        status = self.get_system_status()
        
        print("\n" + "="*80)
        print("RAG AI AGENT - SYSTEM STATUS DASHBOARD")
        print("="*80)
        print(f"Last Updated: {status['timestamp']}")
        print(f"System Uptime: {status['uptime']}")
        print(f"Overall API Status: {status['api_status']['overall']}")
        print()
        
        print("API KEY STATUS:")
        print("-" * 40)
        
        print("Groq Keys:")
        for key in status['api_status']['groq']:
            print(f"   {key['name']}: {key['status']}")
        
        print("Gemini Keys:")
        for key in status['api_status']['gemini']:
            print(f"   {key['name']}: {key['status']}")
        
        print()
        print("KNOWLEDGE BASE:")
        print("-" * 40)
        kb_status = status['knowledge_base_status']
        print(f"   Status: {kb_status['status']}")
        print(f"   Search Functional: {kb_status['search_working']}")
        
        print()
        print("PERFORMANCE METRICS:")
        print("-" * 40)
        metrics = status['performance_metrics']
        print(f"   Total Queries: {metrics['total_queries']}")
        print(f"   Successful: {metrics['successful_queries']}")
        print(f"   Failed: {metrics['failed_queries']}")
        success_rate = (metrics['successful_queries'] / metrics['total_queries'] * 100) if metrics['total_queries'] > 0 else 0
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print()
        print("RECOMMENDATIONS:")
        print("-" * 40)
        for rec in status['recommendations']:
            print(f"   {rec}")
        
        print("="*80)
    
    def update_stats(self, success: bool, provider: str, response_time: float):
        """Update performance statistics"""
        self.stats['total_queries'] += 1
        if success:
            self.stats['successful_queries'] += 1
        else:
            self.stats['failed_queries'] += 1
        
        if provider in self.stats['providers_used']:
            self.stats['providers_used'][provider] += 1
        else:
            self.stats['providers_used'][provider] = 1
        
        if self.stats['avg_response_time'] == 0:
            self.stats['avg_response_time'] = response_time
        else:
            self.stats['avg_response_time'] = (self.stats['avg_response_time'] + response_time) / 2
        
        self.stats['last_health_check'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """Run the status dashboard"""
    dashboard = SystemStatusDashboard()
    
    try:
        from agent import QAAgent
        from knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase()
        kb.load_sample_data()
        
        groq_keys = [os.getenv(key) for key in ["GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3"] if os.getenv(key)]
        gemini_keys = [os.getenv(key) for key in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"] if os.getenv(key)]
        
        agent = QAAgent(kb, groq_keys, gemini_keys)
        
        start_time = time.time()
        result = agent.ask_question("What is renewable energy?")
        response_time = time.time() - start_time
        
        dashboard.update_stats(True, result.get('current_provider', 'Unknown'), response_time)
        
    except Exception as e:
        print(f"System test failed: {e}")
        dashboard.update_stats(False, 'Unknown', 0)
    
    dashboard.print_dashboard()

if __name__ == "__main__":
    main()