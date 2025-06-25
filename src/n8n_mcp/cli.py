import argparse
import json
from pathlib import Path
from src.workflow_validator import validate_workflow
from src.n8n_api_client import N8nApiClient
import asyncio
from src.utils.file_utils import read_json_file

def show_help():
    print("""
n8n Workflow Validator and Importer CLI

Usage:
  python -m src.cli [command] [options]

Commands:
  validate                  Validate a workflow
  import                    Import a workflow to n8n

Options:
  -h, --help                Show this help message
  -s, --strictness LEVEL    Set validation strictness (low, medium, high)
  -v, --validators LIST     Comma-separated list of validators to run
  -f, --file PATH           Path to a workflow file
  --id ID                   ID of the workflow

Examples:
  python -m src.cli validate --id 123456
  python -m src.cli validate --file ./workflows/workflow.json
  python -m src.cli import --file ./workflows/workflow.json
    """)

def validate_local_workflow(file_path: str, options: argparse.Namespace):
    try:
        print(f"Validating workflow file: {file_path}")
        
        with open(file_path, 'r') as f:
            workflow_data = json.load(f)
            
        workflow = workflow_data.get("originalWorkflow", workflow_data)
        
        validation_results = validate_workflow(workflow, {
            "validators": options.validators,
            "strictness": options.strictness
        })
        
        print("\nWorkflow Validation Results:")
        print("==========================")
        print(f"Workflow: {validation_results['workflow'].get('name', file_path)}")
        print(f"Strictness: {validation_results['strictness']}")
        print(f"Passed: {'Yes' if validation_results['passed'] else 'No'}")
        print(f"Total Issues: {validation_results['totalIssues']}")
        
        for category, result in validation_results['results'].items():
            print(f"\n{category.capitalize()}:")
            print(f"  Passed: {'Yes' if result['passed'] else 'No'}")
            
            if result['issues']:
                print("  Issues:")
                for issue in result['issues']:
                    print(f"    - {issue}")
            
            if result['suggestions']:
                print("  Suggestions:")
                for suggestion in result['suggestions']:
                    print(f"    - {suggestion}")
                    
    except Exception as e:
        print(f"Error validating workflow file: {e}")

def import_workflow(file_path: str):
    print(f"Importing workflow from: {file_path}")
    client = N8nApiClient()
    
    workflow_data = read_json_file(file_path)
    workflow = workflow_data.get("originalWorkflow", workflow_data)

    created_workflow = client.create_workflow(workflow)
    if created_workflow:
        print("Workflow imported successfully!")
        print(f"Workflow ID: {created_workflow.get('id')}")

def main():
    parser = argparse.ArgumentParser(description="n8n Workflow CLI", add_help=False)
    parser.add_argument("command", nargs="?", help="Command to execute (validate, import)")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message")
    parser.add_argument("-s", "--strictness", default="medium", choices=["low", "medium", "high"], help="Validation strictness level")
    parser.add_argument("-v", "--validators", type=lambda s: s.split(','), default=['naming', 'errorHandling', 'security', 'performance', 'documentation'], help="Comma-separated list of validators")
    parser.add_argument("-f", "--file", help="Path to a local workflow file")
    parser.add_argument("--id", help="ID of the workflow")
    
    args = parser.parse_args()
    
    if args.help or not args.command:
        show_help()
        return
        
    if args.command == "validate":
        if args.file:
            validate_local_workflow(args.file, args)
        elif args.id:
            # The original script for validating n8n workflow is not fully implemented in Python yet.
            print("Validating from n8n by ID is not yet supported in this version.")
        else:
            print("Please provide a file path or an ID to validate.")
    elif args.command == "import":
        if args.file:
            import_workflow(args.file)
        else:
            print("Please provide a file path to import.")

if __name__ == "__main__":
    main()
