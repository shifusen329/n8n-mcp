from typing import Any, Dict, List, Set

def validate_naming(workflow: Dict[str, Any], strictness: str = "medium") -> Dict[str, Any]:
    issues: List[str] = []
    suggestions: List[str] = []

    if not workflow.get("name"):
        issues.append("Workflow name is missing")
        suggestions.append("Add a descriptive name to the workflow")
    elif len(workflow.get("name", "")) < 5 and strictness != "low":
        issues.append("Workflow name is too short")
        suggestions.append("Use a more descriptive name that indicates the workflow's purpose")

    if isinstance(workflow.get("nodes"), list):
        default_node_names: Set[str] = set()
        duplicate_node_names: Set[str] = set()
        node_names: List[str] = [node.get("name") for node in workflow["nodes"] if node.get("name")]

        for node in workflow["nodes"]:
            if node.get("name") and node.get("type"):
                node_type_name = node["type"].split(".")[-1]
                if node_type_name in node["name"]:
                    default_node_names.add(node["name"])
            
            if node.get("name") and node_names.count(node["name"]) > 1:
                duplicate_node_names.add(node["name"])

        if default_node_names and strictness != "low":
            issues.append(f"{len(default_node_names)} nodes have default names")
            suggestions.append("Rename nodes to better describe their purpose in the workflow")

        if duplicate_node_names:
            issues.append(f"Found {len(duplicate_node_names)} duplicate node names")
            suggestions.append("Ensure each node has a unique name to avoid confusion")

    return {
        "category": "naming",
        "passed": not issues,
        "issues": issues,
        "suggestions": suggestions,
    }

def validate_error_handling(workflow: Dict[str, Any], strictness: str = "medium") -> Dict[str, Any]:
    issues: List[str] = []
    suggestions: List[str] = []

    has_error_trigger = any(
        node.get("type") == "n8n-nodes-base.errorTrigger"
        for node in workflow.get("nodes", [])
    )
    has_error_workflow = workflow.get("settings", {}).get("errorWorkflow")

    if not has_error_trigger and not has_error_workflow and strictness != "low":
        issues.append("No error handling found in workflow")
        suggestions.append("Add an Error Trigger node or set an error workflow in the settings")

    return {
        "category": "errorHandling",
        "passed": not issues,
        "issues": issues,
        "suggestions": suggestions,
    }

def validate_security(workflow: Dict[str, Any], strictness: str = "medium") -> Dict[str, Any]:
    issues: List[str] = []
    suggestions: List[str] = []

    if isinstance(workflow.get("nodes"), list):
        nodes_with_potential_hardcoded_credentials = [
            node for node in workflow["nodes"]
            if "parameters" in node and any(
                keyword in str(node["parameters"]).lower()
                for keyword in ["api", "key", "token", "secret", "password", "auth"]
            )
        ]
        if nodes_with_potential_hardcoded_credentials and strictness != "low":
            issues.append(f"{len(nodes_with_potential_hardcoded_credentials)} nodes potentially contain hard-coded credentials")
            suggestions.append("Use credential objects instead of hard-coding sensitive information")

    return {
        "category": "security",
        "passed": not issues,
        "issues": issues,
        "suggestions": suggestions,
    }

def validate_performance(workflow: Dict[str, Any], strictness: str = "medium") -> Dict[str, Any]:
    issues: List[str] = []
    suggestions: List[str] = []

    if isinstance(workflow.get("nodes"), list):
        if len(workflow["nodes"]) > 50 and strictness != "low":
            issues.append(f"Workflow has {len(workflow['nodes'])} nodes, which may impact performance")
            suggestions.append("Consider breaking down complex workflows into smaller sub-workflows")

    return {
        "category": "performance",
        "passed": not issues,
        "issues": issues,
        "suggestions": suggestions,
    }

def validate_documentation(workflow: Dict[str, Any], strictness: str = "medium") -> Dict[str, Any]:
    issues: List[str] = []
    suggestions: List[str] = []

    if not workflow.get("description") and strictness != "low":
        issues.append("Workflow description is missing")
        suggestions.append("Add a detailed description explaining the workflow's purpose and functionality")

    sticky_notes = [
        node for node in workflow.get("nodes", []) if node.get("type") == "n8n-nodes-base.stickyNote"
    ]
    if not sticky_notes and len(workflow.get("nodes", [])) > 10 and strictness != "low":
        issues.append("No sticky notes found in a complex workflow")
        suggestions.append("Add sticky notes to document workflow sections and complex logic")

    if not workflow.get("tags"):
        issues.append("No tags defined for the workflow")
        suggestions.append("Add relevant tags to make the workflow more discoverable")

    return {
        "category": "documentation",
        "passed": not issues,
        "issues": issues,
        "suggestions": suggestions,
    }

def validate_workflow(workflow: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
    if options is None:
        options = {}
        
    validators_to_run = options.get(
        "validators", ["naming", "errorHandling", "security", "performance", "documentation"]
    )
    strictness = options.get("strictness", "medium")
    
    results = {}
    total_issues = 0
    
    validation_functions = {
        "naming": validate_naming,
        "errorHandling": validate_error_handling,
        "security": validate_security,
        "performance": validate_performance,
        "documentation": validate_documentation,
    }
    
    for validator in validators_to_run:
        if validator in validation_functions:
            result = validation_functions[validator](workflow, strictness)
            results[validator] = result
            total_issues += len(result["issues"])
            
    return {
        "workflow": {"id": workflow.get("id"), "name": workflow.get("name")},
        "passed": total_issues == 0,
        "totalIssues": total_issues,
        "strictness": strictness,
        "results": results,
    }
