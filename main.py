import dotenv
import os
import argparse
from typing import TypedDict, Set, List, Optional, Dict, Any, cast
# Import the function that creates the flow
from flow import create_tutorial_flow

dotenv.load_dotenv()

# Default file patterns
DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "Dockerfile",
    "Makefile", "*.yaml", "*.yml",
}

# Text-only mode default patterns
TEXT_ONLY_INCLUDE_PATTERNS = {
    "*.md", "*.txt", "*.rst", "*.markdown", "README*", "documentation/*", "docs/*", "*.html", "*.mdx"
}

DEFAULT_EXCLUDE_PATTERNS = {
    "assets/*", "data/*", "examples/*", "images/*", "public/*", "static/*", "temp/*",
    "docs/*", 
    "venv/*", ".venv/*", "*test*", "tests/*", "docs/*", "examples/*", "v1/*",
    "dist/*", "build/*", "experimental/*", "deprecated/*", "misc/*", 
    "legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*", "obj/*", "bin/*", "node_modules/*", "*.log"
}

# Text-only mode exclude patterns (more permissive with docs)
TEXT_ONLY_EXCLUDE_PATTERNS = {
    "venv/*", ".venv/*", "node_modules/*", ".git/*", ".github/*", ".next/*", ".vscode/*",
    "dist/*", "build/*", "obj/*", "bin/*", "*.log"
}

# Define TypedDict for the 'shared' dictionary
class SharedDict(TypedDict):
    repo_url: Optional[str]
    local_dir: Optional[str]
    project_name: Optional[str]
    github_token: Optional[str]
    output_dir: str
    include_patterns: Set[str]
    exclude_patterns: Set[str]
    max_file_size: int
    language: str
    use_cache: bool
    max_abstraction_num: int
    text_only: bool
    max_tokens: int
    files: List[Any]
    abstractions: List[Any]
    relationships: Dict[Any, Any]
    chapter_order: List[Any]
    chapters: List[Any]
    final_output_dir: Optional[str]

# --- Main Function ---
def main():
    parser = argparse.ArgumentParser(description="Generate a tutorial for a GitHub codebase or local directory.")

    # Create mutually exclusive group for source
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo", help="URL of the public GitHub repository.")
    source_group.add_argument("--dir", help="Path to local directory.")

    parser.add_argument("-n", "--name", help="Project name (optional, derived from repo/directory if omitted).")
    parser.add_argument("-t", "--token", help="GitHub personal access token (optional, reads from GITHUB_TOKEN env var if not provided).")
    parser.add_argument("-o", "--output", default="output", help="Base directory for output (default: ./output).")
    parser.add_argument("-i", "--include", nargs="+", help="Include file patterns (e.g. '*.py' '*.js'). Defaults to common code files if not specified.")
    parser.add_argument("-e", "--exclude", nargs="+", help="Exclude file patterns (e.g. 'tests/*' 'docs/*'). Defaults to test/build directories if not specified.")
    parser.add_argument("-s", "--max-size", type=int, default=100000, help="Maximum file size in bytes (default: 100000, about 100KB).")
    # Add language parameter for multi-language support
    parser.add_argument("--language", default="english", help="Language for the generated tutorial (default: english)")
    # Add use_cache parameter to control LLM caching
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM response caching (default: caching enabled)")
    # Add max_abstraction_num parameter to control the number of abstractions
    parser.add_argument("--max-abstractions", type=int, default=10, help="Maximum number of abstractions to identify (default: 10)")
    # Add text-only mode flag for focusing on text files rather than code
    parser.add_argument("--text-only", action="store_true", help="Enable text-only mode to focus on documentation files (*.md, *.txt) rather than code")
    # Add max_tokens parameter to control the token limit for LLM requests
    parser.add_argument("--max-tokens", type=int, default=30000, help="Maximum tokens per LLM request (default: 30000, adjust based on model limits)")

    args = parser.parse_args()

    # Get GitHub token from argument or environment variable if using repo
    github_token = None
    if args.repo:
        github_token = args.token or os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("Warning: No GitHub token provided. You might hit rate limits for public repositories.")

    # Set include/exclude patterns based on text-only mode if not specified by user
    include_patterns = set(args.include) if args.include else (TEXT_ONLY_INCLUDE_PATTERNS if args.text_only else DEFAULT_INCLUDE_PATTERNS)
    exclude_patterns = set(args.exclude) if args.exclude else (TEXT_ONLY_EXCLUDE_PATTERNS if args.text_only else DEFAULT_EXCLUDE_PATTERNS)

    # Initialize the shared dictionary with inputs
    shared: SharedDict = {
        "repo_url": args.repo,
        "local_dir": args.dir,
        "project_name": args.name, # Can be None, FetchRepo will derive it
        "github_token": github_token,
        "output_dir": args.output, # Base directory for CombineTutorial output

        # Add include/exclude patterns and max file size
        "include_patterns": include_patterns,
        "exclude_patterns": exclude_patterns,
        "max_file_size": args.max_size,

        # Add language for multi-language support
        "language": args.language,
        
        # Add use_cache flag (inverse of no-cache flag)
        "use_cache": not args.no_cache,
        
        # Add max_abstraction_num parameter
        "max_abstraction_num": args.max_abstractions,
        
        # Add text_only flag
        "text_only": args.text_only,
        
        # Add max_tokens parameter for LLM requests
        "max_tokens": args.max_tokens,

        # Outputs will be populated by the nodes
        "files": [],
        "abstractions": [],
        "relationships": {},
        "chapter_order": [],
        "chapters": [],
        "final_output_dir": None
    }

    # Display starting message with repository/directory and language
    print(f"Starting tutorial generation for: {args.repo or args.dir} in {args.language.capitalize()} language")
    print(f"LLM caching: {'Disabled' if args.no_cache else 'Enabled'}")
    print(f"Mode: {'Text-only' if args.text_only else 'Code analysis'}")
    print(f"Max tokens per request: {args.max_tokens}")

    # Create the flow instance
    tutorial_flow = create_tutorial_flow()

    # Run the flow
    tutorial_flow.run(cast(Dict[str, Any], shared)) # type: ignore

if __name__ == "__main__":
    main()
