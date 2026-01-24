
import sys
import os

# Add service root to path
sys.path.append(os.path.join(os.getcwd(), 'services/titan-core'))

from ai_council.director_agent import DirectorAgentV2

def test_director_learning():
    print("🧪 Testing Director Agent Learning Loop...")
    
    # Set path to mock data
    os.environ["META_INSIGHTS_PATH"] = "services/titan-core/data/meta_insights.json"
    
    agent = DirectorAgentV2()
    
    # Check if the test winner hook is present
    test_template = "TEST_WINNER: {pain_point}"
    found = any(t["template"] == test_template for t in agent.hook_templates)
    
    if found:
        print("✅ SUCCESS: Director loaded winning pattern from JSON!")
        return True
    else:
        print("❌ FAILURE: Director did not load external patterns.")
        return False

if __name__ == "__main__":
    test_director_learning()
