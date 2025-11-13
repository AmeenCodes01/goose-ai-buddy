"""
Goose Integration Examples

Comprehensive examples showing how to use the Goose client for various
productivity and automation tasks.

Run this file to see examples in action:
    python goose_examples.py
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path

from goose_integration import (
    GooseClient, 
    quick_task, 
    quick_task_async, 
    analyze_logs, 
    create_productivity_recipe,
    GooseError
)

def example_basic_usage():
    """Basic usage examples."""
    print("=" * 50)
    print("BASIC USAGE EXAMPLES")
    print("=" * 50)
    
    try:
        # Initialize client
        client = GooseClient()
        print(f"✓ Goose client initialized. Version: {client.get_version()}")
        
        # Get system info
        print("\n--- System Information ---")
        info = client.get_system_info()
        print(f"System info retrieved at: {info.get('timestamp')}")
        
        # List sessions
        print("\n--- Sessions ---")
        sessions = client.list_sessions()
        print(f"Found {len(sessions)} sessions")
        
        # List recipes
        print("\n--- Recipes ---")
        recipes = client.list_recipes()
        print(f"Found {len(recipes)} recipes")
        
    except GooseError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

def example_task_execution():
    """Task execution examples."""
    print("\n" + "=" * 50)
    print("TASK EXECUTION EXAMPLES")
    print("=" * 50)
    
    try:
        client = GooseClient()
        
        # Simple task
        print("\n--- Simple Task ---")
        result = client.run_task(
            instructions="What's the current date and time? Format it nicely.",
            extensions=["developer"],
            no_session=True
        )
        
        if result['success']:
            print("✓ Task completed successfully")
            print(f"Output: {result['output'][:200]}...")
        else:
            print(f"✗ Task failed: {result['error']}")
        
        # File analysis task
        print("\n--- File Analysis Task ---")
        # Create a temporary file to analyze
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def hello_world():
    print("Hello, World!")
    return 42

def calculate(x, y):
    return x + y

if __name__ == "__main__":
    hello_world()
    result = calculate(10, 20)
    print(f"Result: {result}")
""")
            temp_file = f.name
        
        result = client.run_task(
            instructions=f"Analyze this Python file: {temp_file}. Provide insights about the code structure, functions, and suggest improvements.",
            extensions=["developer"],
            session_name="code_analysis",
            max_turns=15
        )
        
        if result['success']:
            print("✓ File analysis completed")
            print(f"Analysis: {result['output'][:300]}...")
        else:
            print(f"✗ Analysis failed: {result['error']}")
        
        # Clean up
        Path(temp_file).unlink(missing_ok=True)
        
    except Exception as e:
        print(f"✗ Error in task execution: {e}")

def example_productivity_automation():
    """Productivity automation examples."""
    print("\n" + "=" * 50)
    print("PRODUCTIVITY AUTOMATION EXAMPLES")
    print("=" * 50)
    
    try:
        client = GooseClient()
        
        # URL analysis example
        print("\n--- URL Analysis ---")
        sample_urls = [
            "https://github.com/microsoft/vscode",
            "https://stackoverflow.com/questions/tagged/python",
            "https://news.ycombinator.com",
            "https://docs.python.org/3/",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        url_analysis_instructions = f"""
        Analyze these URLs for productivity insights:
        {chr(10).join(sample_urls)}
        
        Provide:
        1. Category classification
        2. Productivity assessment
        3. Time management recommendations
        """
        
        result = client.run_task(
            instructions=url_analysis_instructions,
            extensions=["developer"],
            session_name="url_productivity_analysis",
            max_turns=10
        )
        
        if result['success']:
            print("✓ URL analysis completed")
            print(f"Analysis: {result['output'][:400]}...")
        
        # Daily routine automation
        print("\n--- Daily Routine Automation ---")
        routine_instructions = """
        Create a daily productivity checklist based on best practices:
        1. Morning routine items
        2. Work focus techniques  
        3. Break recommendations
        4. End-of-day review items
        
        Format as a practical checklist.
        """
        
        result = client.run_task(
            instructions=routine_instructions,
            extensions=["developer"],
            no_session=True,
            max_turns=8
        )
        
        if result['success']:
            print("✓ Daily routine generated")
            print(f"Routine: {result['output'][:300]}...")
        
    except Exception as e:
        print(f"✗ Error in productivity automation: {e}")

def example_recipe_management():
    """Recipe management examples."""
    print("\n" + "=" * 50)
    print("RECIPE MANAGEMENT EXAMPLES")
    print("=" * 50)
    
    try:
        client = GooseClient()
        
        # Create a productivity recipe
        print("\n--- Creating Productivity Recipe ---")
        recipe_path = "productivity_recipe.yaml"
        
        created_recipe = create_productivity_recipe(
            name="Daily Productivity Review",
            description="Analyze and improve daily productivity patterns",
            tasks=[
                "Review completed tasks from today",
                "Identify time-wasting activities",
                "Plan priorities for tomorrow", 
                "Suggest productivity improvements",
                "Create action items for better time management"
            ],
            output_path=recipe_path
        )
        
        print(f"✓ Recipe created at: {created_recipe}")
        
        # Validate the recipe
        print("\n--- Validating Recipe ---")
        validation = client.validate_recipe(recipe_path)
        if validation['valid']:
            print("✓ Recipe is valid")
        else:
            print(f"✗ Recipe validation failed: {validation['error']}")
        
        # List recipes
        print("\n--- Listing Recipes ---")
        recipes = client.list_recipes(verbose=True)
        print(f"Found {len(recipes)} recipes")
        
        # Clean up
        Path(recipe_path).unlink(missing_ok=True)
        
    except Exception as e:
        print(f"✗ Error in recipe management: {e}")

def example_session_management():
    """Session management examples."""
    print("\n" + "=" * 50)
    print("SESSION MANAGEMENT EXAMPLES")
    print("=" * 50)
    
    try:
        client = GooseClient()
        
        # List existing sessions
        print("\n--- Current Sessions ---")
        sessions = client.list_sessions(verbose=True)
        print(f"Found {len(sessions)} sessions")
        
        if sessions:
            # Export a session (if any exist)
            print("\n--- Session Export Example ---")
            first_session = sessions[0]
            
            # Try to export by different methods based on available data
            if isinstance(first_session, dict):
                if 'name' in first_session:
                    exported = client.export_session(
                        name=first_session['name'],
                        format_type="json"
                    )
                elif 'id' in first_session:
                    exported = client.export_session(
                        session_id=first_session['id'],
                        format_type="json"
                    )
                else:
                    exported = "Session export format not supported for this session"
                
                if exported:
                    print(f"✓ Session exported ({len(exported)} characters)")
                    
                    # Save to file
                    export_file = f"session_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(export_file, 'w') as f:
                        f.write(exported)
                    print(f"✓ Export saved to: {export_file}")
                    
                    # Clean up
                    Path(export_file).unlink(missing_ok=True)
        
        # Run a task with session tracking
        print("\n--- Task with Session ---")
        result = client.run_task(
            instructions="Generate a summary of Python best practices for beginners",
            extensions=["developer"],
            session_name=f"python_tips_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            max_turns=10
        )
        
        if result['success']:
            print("✓ Task completed with session tracking")
            print(f"Output length: {len(result['output'])} characters")
        
    except Exception as e:
        print(f"✗ Error in session management: {e}")

async def example_async_operations():
    """Asynchronous operations examples."""
    print("\n" + "=" * 50)
    print("ASYNC OPERATIONS EXAMPLES")
    print("=" * 50)
    
    try:
        # Async task execution
        print("\n--- Async Task ---")
        result = await quick_task_async(
            "List 5 productivity tips for remote workers",
            extensions=["developer"]
        )
        
        if result['success']:
            print("✓ Async task completed")
            print(f"Tips: {result['output'][:300]}...")
        else:
            print(f"✗ Async task failed: {result['error']}")
        
        # Multiple async tasks
        print("\n--- Multiple Async Tasks ---")
        tasks = [
            quick_task_async("What are the benefits of version control?"),
            quick_task_async("Explain the importance of code reviews"),
            quick_task_async("List common debugging techniques")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"✗ Task {i+1} failed: {result}")
            elif result.get('success'):
                print(f"✓ Task {i+1} completed ({len(result['output'])} chars)")
            else:
                print(f"✗ Task {i+1} failed: {result.get('error')}")
        
    except Exception as e:
        print(f"✗ Error in async operations: {e}")

def example_convenience_functions():
    """Convenience functions examples."""
    print("\n" + "=" * 50)
    print("CONVENIENCE FUNCTIONS EXAMPLES")
    print("=" * 50)
    
    try:
        # Quick task
        print("\n--- Quick Task ---")
        result = quick_task(
            "Explain the concept of technical debt in software development",
            extensions=["developer"]
        )
        
        if result['success']:
            print("✓ Quick task completed")
            print(f"Explanation: {result['output'][:250]}...")
        
        # Log analysis (create a sample log file)
        print("\n--- Log Analysis ---")
        sample_log = """
2025-11-11 10:30:15 INFO Starting application
2025-11-11 10:30:16 INFO Database connection established
2025-11-11 10:32:22 WARNING Slow query detected: SELECT * FROM users
2025-11-11 10:35:45 ERROR Failed to connect to external API
2025-11-11 10:35:46 INFO Retrying API connection
2025-11-11 10:35:47 INFO API connection restored
2025-11-11 11:00:12 ERROR Database timeout
2025-11-11 11:00:13 CRITICAL System shutdown initiated
"""
        
        # Create temp log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(sample_log)
            log_file = f.name
        
        result = analyze_logs(log_file)
        
        if result['success']:
            print("✓ Log analysis completed")
            print(f"Analysis: {result['output'][:300]}...")
        
        # Clean up
        Path(log_file).unlink(missing_ok=True)
        
    except Exception as e:
        print(f"✗ Error in convenience functions: {e}")

def example_error_handling():
    """Error handling examples."""
    print("\n" + "=" * 50)
    print("ERROR HANDLING EXAMPLES")
    print("=" * 50)
    
    try:
        client = GooseClient()
        
        # Invalid task
        print("\n--- Invalid Task ---")
        result = client.run_task(
            instructions="",  # Empty instructions
            no_session=True
        )
        
        if not result['success']:
            print(f"✓ Handled invalid task gracefully: {result['error']}")
        
        # Non-existent recipe
        print("\n--- Non-existent Recipe ---")
        result = client.validate_recipe("non_existent_recipe.yaml")
        
        if not result['valid']:
            print(f"✓ Handled missing recipe gracefully: {result['error']}")
        
        # Invalid session operation
        print("\n--- Invalid Session Operation ---")
        try:
            client.remove_session()  # No parameters
        except Exception as e:
            print(f"✓ Handled invalid session operation: {type(e).__name__}")
        
    except Exception as e:
        print(f"✗ Error in error handling examples: {e}")

def main():
    """Run all examples."""
    print("GOOSE INTEGRATION EXAMPLES")
    print("=" * 50)
    print("This script demonstrates various ways to use the Goose client")
    print("for productivity automation and task management.")
    print()
    
    # Check if Goose is available
    try:
        client = GooseClient()
        print(f"✓ Goose CLI is available (version: {client.get_version()})")
    except Exception as e:
        print(f"✗ Goose CLI not available: {e}")
        print("\nPlease install Goose CLI first:")
        print("https://github.com/block/goose")
        return
    
    # Run examples
    example_basic_usage()
    example_task_execution()
    example_productivity_automation()
    example_recipe_management()
    example_session_management()
    example_convenience_functions()
    example_error_handling()
    
    # Run async examples
    print("\nRunning async examples...")
    asyncio.run(example_async_operations())
    
    print("\n" + "=" * 50)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Try the Flask integration: python flask_goose_integration.py")
    print("2. Create your own recipes using create_productivity_recipe()")
    print("3. Integrate the GooseClient into your applications")
    print("4. Set up scheduled tasks for automation")

if __name__ == "__main__":
    main()
