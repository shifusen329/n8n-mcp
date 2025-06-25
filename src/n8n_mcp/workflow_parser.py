import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Configuration
WORKFLOWS_DIR = Path(__file__).parent.parent.parent / "workflows"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "processed-workflows"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_category(filename: str) -> str:
    """Extract category from filename."""
    parts = filename.split(":")
    return parts[0] if len(parts) > 1 else "uncategorized"

def extract_name(filename: str) -> str:
    """Extract name from filename."""
    parts = filename.split(":")
    if len(parts) > 1:
        return parts[1].replace(".json", "")
    return filename.replace(".json", "")

def get_node_type_str(node: Dict[str, Any]) -> Optional[str]:
    """Get the node type as a string, handling both string and dict types."""
    node_type = node.get("type")
    if not isinstance(node_type, (str, bytes)):
        try:
            return json.dumps(node_type)
        except TypeError:
            return str(node_type)
    return node_type

def generate_description(workflow: Dict[str, Any]) -> str:
    """Generate a description for a workflow based on its content."""
    description = []
    
    if workflow.get("name"):
        description.append(f"Workflow Name: {workflow['name']}\n")
    
    node_types: Dict[str, int] = {}
    node_names: Set[str] = set()
    
    if isinstance(workflow.get("nodes"), list):
        for node in workflow["nodes"]:
            node_type = get_node_type_str(node)
            if node_type:
                node_types[node_type] = node_types.get(node_type, 0) + 1
            if node.get("name"):
                node_names.add(node["name"])
    
    if node_types:
        description.append("Node Types:")
        for type, count in node_types.items():
            description.append(f"- {type}: {count}")
    
    if node_names:
        description.append("\nNode Names:")
        for name in sorted(list(node_names)):
            description.append(f"- {name}")
            
    sticky_notes = [
        node for node in workflow.get("nodes", []) if node.get("type") == "n8n-nodes-base.stickyNote"
    ]
    if sticky_notes:
        description.append("\nWorkflow Documentation:")
        for note in sticky_notes:
            if note.get("parameters", {}).get("content"):
                description.append(note["parameters"]["content"])
                
    return "\n".join(description)

def extract_tags(workflow: Dict[str, Any]) -> List[str]:
    """Extract tags from a workflow."""
    tags: Set[str] = set()
    
    if isinstance(workflow.get("tags"), list):
        for tag in workflow["tags"]:
            if isinstance(tag, dict) and "name" in tag:
                tags.add(tag["name"])
            elif isinstance(tag, str):
                tags.add(tag)
            
    if isinstance(workflow.get("nodes"), list):
        for node in workflow["nodes"]:
            node_type = get_node_type_str(node)
            if node_type:
                base_type = node_type.split(".")[-1]
                if base_type:
                    tags.add(base_type)
                
                service_tags = [
                    "gmail", "google", "openai", "langchain", "webhook",
                    "http", "database", "postgres", "supabase"
                ]
                for service in service_tags:
                    if service in node_type:
                        tags.add(service)
                        
    return sorted(list(tags))

def analyze_complexity(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze workflow complexity."""
    metrics = {
        "nodeCount": 0,
        "connectionCount": 0,
        "uniqueNodeTypes": 0,
        "complexity": "simple",
    }
    
    if isinstance(workflow.get("nodes"), list):
        metrics["nodeCount"] = len(workflow["nodes"])
        
        node_type_set = {get_node_type_str(node) for node in workflow["nodes"] if get_node_type_str(node)}
        metrics["uniqueNodeTypes"] = len(node_type_set)
        
    if isinstance(workflow.get("connections"), dict):
        connection_count = 0
        for conn in workflow["connections"].values():
            if isinstance(conn.get("main"), list):
                for main_conn in conn["main"]:
                    if isinstance(main_conn, list):
                        connection_count += len(main_conn)
        metrics["connectionCount"] = connection_count
        
    if metrics["nodeCount"] > 15 or metrics["connectionCount"] > 20:
        metrics["complexity"] = "complex"
    elif metrics["nodeCount"] > 7 or metrics["connectionCount"] > 10:
        metrics["complexity"] = "moderate"
        
    return metrics

def process_workflow(file_path: Path) -> Optional[Dict[str, Any]]:
    """Process a single workflow file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content:
                print(f"Warning: Skipping empty file {file_path}")
                return None
            workflow = json.loads(content)
            
        filename = file_path.name
        category = extract_category(filename)
        name = extract_name(filename)
        description = generate_description(workflow)
        tags = extract_tags(workflow)
        complexity = analyze_complexity(workflow)
        
        enriched_workflow = {
            "id": workflow.get("id") or f"generated-{int(Path.stat(file_path).st_ctime)}",
            "originalFilename": filename,
            "category": category,
            "name": name,
            "description": description,
            "tags": tags,
            "complexity": complexity,
            "originalWorkflow": workflow,
        }
        
        return enriched_workflow
    except Exception as e:
        print(f"Error processing workflow {file_path}: {e}")
        return None

def process_all_workflows():
    """Main function to process all workflows."""
    try:
        workflow_files = [f for f in WORKFLOWS_DIR.glob("*.json")]
        print(f"Found {len(workflow_files)} workflow files to process")
        
        processed_workflows = []
        for file_path in workflow_files:
            processed_workflow = process_workflow(file_path)
            
            if processed_workflow:
                processed_workflows.append(processed_workflow)
                
                output_path = OUTPUT_DIR / f"{processed_workflow['id']}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(processed_workflow, f, indent=2)
                    
        summary_path = OUTPUT_DIR / "workflows-summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(processed_workflows, f, indent=2)
            
        print(f"Successfully processed {len(processed_workflows)} workflows")
        print(f"Results saved to {OUTPUT_DIR}")
        
        return processed_workflows
    except Exception as e:
        print(f"Error processing workflows: {e}")
        return []

if __name__ == "__main__":
    process_all_workflows()
