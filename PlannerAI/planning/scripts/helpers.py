import json
from typing import Dict, List, Any, Optional


def load_plan(file_path: str) -> Dict[str, Any]:
    """
    Load and parse a plan JSON file.
    
    Args:
        file_path: Path to the JSON plan file
        
    Returns:
        Dict containing the parsed plan data
    """
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading plan: {e}")
        return {}


def get_milestones(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract milestone information from the plan.
    
    Args:
        plan: Parsed plan dictionary
        
    Returns:
        List of milestone dictionaries containing id, name, description, and status
    """
    milestones = []
    for milestone in plan.get('milestones', []):
        milestones.append({
            'id': milestone.get('id', ''),
            'name': milestone.get('name', ''),
            'description': milestone.get('description', ''),
            'status': milestone.get('status', 'pending')
        })
    return milestones


def get_milestone_steps(plan: Dict[str, Any], milestone_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract steps from the specified milestone or all milestones.
    
    Args:
        plan: Parsed plan dictionary
        milestone_id: Optional milestone ID to filter steps
        
    Returns:
        List of step dictionaries
    """
    steps = []
    
    for milestone in plan.get('milestones', []):
        # If milestone_id is provided, only get steps from that milestone
        if milestone_id and milestone.get('id') != milestone_id:
            continue
            
        for step in milestone.get('steps', []):
            steps.append({
                'id': step.get('id', ''),
                'title': step.get('title', ''),
                'description': step.get('description', ''),
                'reasoning': step.get('reasoning', ''),
                'layer': step.get('layer', ''),
                'tags': step.get('tags', []),
                'acceptance': step.get('acceptance', ''),
                'deliverables': step.get('deliverables', []),
                'dependencies': step.get('dependencies', []),
                'status': step.get('status', 'pending'),
                'resources': step.get('resources', []),
                'milestone_id': milestone.get('id', '')  # Include parent milestone ID for reference
            })
    
    return steps


def get_success_criteria(plan: Dict[str, Any]) -> List[str]:
    """
    Extract success criteria from the plan.
    
    Args:
        plan: Parsed plan dictionary
        
    Returns:
        List of success criteria strings
    """
    return plan.get('success_criteria', [])


def get_risks(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract risks from the plan.
    
    Args:
        plan: Parsed plan dictionary
        
    Returns:
        List of risk dictionaries
    """
    risks = []
    
    for risk in plan.get('risks', []):
        risks.append({
            'description': risk.get('description', ''),
            'reasoning': risk.get('reasoning', ''),
            'impact': risk.get('impact', ''),
            'likelihood': risk.get('likelihood', ''),
            'mitigation': risk.get('mitigation', []),
            'affects_steps': risk.get('affects_steps', [])
        })
    
    return risks

def main():
    plan = load_plan('/home/zanederrod/planner_ai/PlannerAI/planning/plans/personal_budget_tracker_full_plan_20250612_140954.json')
    milestones = get_milestones(plan)
    steps = get_milestone_steps(plan)
    success_criteria = get_success_criteria(plan)
    risks = get_risks(plan)
    print(milestones)
    print(steps)
    print(success_criteria)
    print(risks)
    
if __name__ == "__main__":
    main()
