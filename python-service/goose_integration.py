"""
Goose CLI Integration Module

A Python wrapper for interacting with Goose CLI programmatically.
Provides methods for session management, task execution, recipe management,
and schedule management with proper error handling and logging.

Author: Goose Integration Module
Created: 2025-11-11
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
#import yaml


class GooseError(Exception):
    """Base exception for Goose CLI errors."""
    pass


class GooseSessionError(GooseError):
    """Exception raised for session-related errors."""
    pass


class GooseRecipeError(GooseError):
    """Exception raised for recipe-related errors."""
    pass


class GooseScheduleError(GooseError):
    """Exception raised for schedule-related errors."""
    pass


class GooseClient:
    """
    A Python client for interacting with Goose CLI programmatically.
    
    This class provides methods for:
    - Session management (create, list, export)
    - Task execution (run instructions/commands)
    - Recipe management (list, validate, run)
    - Schedule management (add, list, remove)
    - System information and configuration
    
    Example:
        client = GooseClient()
        sessions = client.list_sessions()
        result = client.run_task("Analyze the logs in /var/log/app.log")
    """
    
    def __init__(self, goose_command: str = "goose", logger: Optional[logging.Logger] = None):
        """
        Initialize the Goose client.
        
        Args:
            goose_command: Path to goose executable (default: "goose")
            logger: Custom logger instance (optional)
        """
        self.goose_command = goose_command
        self.logger = logger or self._setup_logger()
        
        # Verify goose is available
        try:
            self._run_command(["--version"], timeout=10)
        except subprocess.SubprocessError as e:
            raise GooseError(f"Goose CLI not found or not working: {e}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger for the client."""
        logger = logging.getLogger("goose_client")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _run_command(
        self, 
        args: List[str], 
        input_text: Optional[str] = None,
        timeout: int = 300,
        capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Execute a goose CLI command.
        
        Args:
            args: Command arguments
            input_text: Input to send to the command
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            CompletedProcess object
            
        Raises:
            GooseError: If command fails
        """
        cmd = [self.goose_command] + args
        self.logger.debug(f"Executing: {' '.join(cmd)}")
        print(cmd, " cmd")
        try:
            result = subprocess.run(
                cmd,
                # input=input_text,
                # text=True,
                capture_output=capture_output,
                
            )
            if result.returncode != 0:
                error_msg = f"Command failed with code {result.returncode}: {result.stderr}"
                self.logger.error(error_msg)
                raise GooseError(error_msg)
            
            self.logger.debug(f"Command successful: {result.stdout[:200]}...")
            return result
            
        except subprocess.TimeoutExpired as e:
            raise GooseError(f"Command timed out after {timeout} seconds: {e}")
        except subprocess.SubprocessError as e:
            raise GooseError(f"Command execution failed: {e}")
    
    async def _run_command_async(
        self, 
        args: List[str], 
        input_text: Optional[str] = None,
        timeout: int = 300
    ) -> str:
        """
        Execute a goose CLI command asynchronously.
        
        Args:
            args: Command arguments
            input_text: Input to send to the command
            timeout: Command timeout in seconds
        
        Returns:
            Command output
            
        Raises:
            GooseError: If command fails
        """
        cmd = [self.goose_command] + args
        self.logger.debug(f"Executing async: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if input_text else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_text.encode() if input_text else None),
                timeout=timeout
            )
            
            if process.returncode != 0:
                error_msg = f"Async command failed with code {process.returncode}: {stderr.decode()}"
                self.logger.error(error_msg)
                raise GooseError(error_msg)
            
            return stdout.decode()
            
        except asyncio.TimeoutError:
            raise GooseError(f"Async command timed out after {timeout} seconds")
        except Exception as e:
            raise GooseError(f"Async command execution failed: {e}")
    
    # Session Management Methods
    
    def list_sessions(self, verbose: bool = False, format_type: str = "text") -> List[Dict[str, Any]]:
        """
        List all saved Goose sessions.
        
        Args:
            verbose: Include additional session details
            format_type: Output format ("json" or "text")
        
        Returns:
            List of session dictionaries
            
        Raises:
            GooseSessionError: If listing sessions fails
        """
        try:
            args = ["session", "list", "--format", format_type]
            if verbose:
                args.append("--verbose")
            
            result = self._run_command(args)
            
            if format_type == "json":
                return json.loads(result.stdout) if result.stdout.strip() else []
            else:
                return [{"output": result.stdout}]
                
        except json.JSONDecodeError as e:
            raise GooseSessionError(f"Failed to parse session list: {e}")
        except GooseError as e:
            raise GooseSessionError(f"Failed to list sessions: {e}")
    
    def start_session(
        self, 
        name: Optional[str] = None,
        extensions: Optional[List[str]] = None,
        resume: bool = False,
        session_id: Optional[str] = None,
        max_turns: int = 1000
    ) -> Dict[str, str]:
        """
        Start a new Goose session (non-interactive for programmatic use).
        
        Args:
            name: Session name
            extensions: List of builtin extensions to enable
            resume: Resume previous session
            session_id: Specific session ID to resume
            max_turns: Maximum turns without user input
        
        Returns:
            Dictionary with session information
            
        Note:
            This creates a session file but doesn't start interactive mode.
            Use run_task() to execute commands in the session.
        """
        try:
            args = ["session"]
            
            if name:
                args.extend(["-n", name])
            if resume:
                args.append("--resume")
            if session_id:
                args.extend(["--session-id", session_id])
            if extensions:
                for ext in extensions:
                    args.extend(["--with-builtin", ext])
            
            args.extend(["--max-turns", str(max_turns)])
            
            # We'll use run command instead for non-interactive execution
            return {"message": "Use run_task() method for executing commands programmatically"}
            
        except GooseError as e:
            raise GooseSessionError(f"Failed to start session: {e}")
    
    def export_session(
        self, 
        name: Optional[str] = None,
        session_id: Optional[str] = None,
        output_file: Optional[str] = None,
        format_type: str = "json"
    ) -> str:
        """
        Export a Goose session.
        
        Args:
            name: Session name to export
            session_id: Session ID to export
            output_file: File path to save export (optional)
            format_type: Export format ("json", "yaml", "markdown")
        
        Returns:
            Exported content as string
            
        Raises:
            GooseSessionError: If export fails
        """
        try:
            args = ["session", "export", "--format", format_type]
            
            if name:
                args.extend(["-n", name])
            elif session_id:
                args.extend(["--session-id", session_id])
            
            if output_file:
                args.extend(["-o", output_file])
            
            result = self._run_command(args)
            return result.stdout
            
        except GooseError as e:
            raise GooseSessionError(f"Failed to export session: {e}")
    
    def remove_session(
        self, 
        name: Optional[str] = None,
        session_id: Optional[str] = None,
        regex_pattern: Optional[str] = None
    ) -> bool:
        """
        Remove Goose session(s).
        
        Args:
            name: Session name to remove
            session_id: Session ID to remove
            regex_pattern: Regex pattern for bulk removal
        
        Returns:
            True if successful
            
        Raises:
            GooseSessionError: If removal fails
        """
        try:
            args = ["session", "remove"]
            
            if name:
                args.extend(["-n", name])
            elif session_id:
                args.extend(["--session-id", session_id])
            elif regex_pattern:
                args.extend(["-r", regex_pattern])
            else:
                raise GooseSessionError("Must specify name, session_id, or regex_pattern")
            
            # Note: This might require confirmation in actual CLI
            self._run_command(args)
            return True
            
        except GooseError as e:
            raise GooseSessionError(f"Failed to remove session: {e}")
    
    # Task Execution Methods
    
    def run_task(
        self,
        instructions: Optional[str] = None,
        instructions_file: Optional[str] = None,
        session_name: Optional[str] = None,
        extensions: Optional[List[str]] = None,
        max_turns: int = 1000,
        no_session: bool = False,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a task with Goose.
        
        Args:
            instructions: Direct instruction text
            instructions_file: Path to instruction file
            session_name: Name for the session
            extensions: List of builtin extensions to enable
            max_turns: Maximum turns without user input
            no_session: Run without creating session file
            provider: AI provider to use
            model: AI model to use
        
        Returns:
            Dictionary with execution results
            
        Raises:
            GooseError: If task execution fails
        """
        try:
            args = ["run"]
            
            if instructions:
                args.extend(["-t", instructions])
            elif instructions_file:
                args.extend(["-i", instructions_file])
            else:
                raise GooseError("Must provide either instructions or instructions_file")
            
            if session_name:
                args.extend(["-n", session_name])
            
            if extensions:
                for ext in extensions:
                    args.extend(["--with-builtin", ext])
            
            if no_session:
                args.append("--no-session")
            
            if provider:
                args.extend(["--provider", provider])
                
            if model:
                args.extend(["--model", model])
            
            args.extend(["--max-turns", str(max_turns)])
            
            result = self._run_command(args, timeout=600)  # Longer timeout for tasks
            
            return {
                "success": True,
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            }
            
        except GooseError as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_task_async(
        self,
        instructions: Optional[str] = None,
        instructions_file: Optional[str] = None,
        session_name: Optional[str] = None,
        extensions: Optional[List[str]] = None,
        max_turns: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute a task with Goose asynchronously.
        
        Args:
            instructions: Direct instruction text
            instructions_file: Path to instruction file
            session_name: Name for the session
            extensions: List of builtin extensions to enable
            max_turns: Maximum turns without user input
        
        Returns:
            Dictionary with execution results
        """
        try:
            args = ["run"]
            
            if instructions:
                args.extend(["-t", instructions])
            elif instructions_file:
                args.extend(["-i", instructions_file])
            else:
                raise GooseError("Must provide either instructions or instructions_file")
            
            if session_name:
                args.extend(["-n", session_name])
            
            if extensions:
                for ext in extensions:
                    args.extend(["--with-builtin", ext])
            
            args.extend(["--max-turns", str(max_turns)])
            
            output = await self._run_command_async(args, timeout=600)
            
            return {
                "success": True,
                "output": output,
                "timestamp": datetime.now().isoformat()
            }
            
        except GooseError as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Recipe Management Methods
    
    def list_recipes(self, verbose: bool = False, format_type: str = "json") -> List[Dict[str, Any]]:
        """
        List available Goose recipes.
        
        Args:
            verbose: Include detailed recipe information
            format_type: Output format ("json" or "text")
        
        Returns:
            List of recipe dictionaries
            
        Raises:
            GooseRecipeError: If listing recipes fails
        """
        try:
            args = ["recipe", "list", "--format", format_type]
            if verbose:
                args.append("--verbose")
            
            result = self._run_command(args)
            
            if format_type == "json":
                return json.loads(result.stdout) if result.stdout.strip() else []
            else:
                return [{"output": result.stdout}]
                
        except json.JSONDecodeError as e:
            raise GooseRecipeError(f"Failed to parse recipe list: {e}")
        except GooseError as e:
            raise GooseRecipeError(f"Failed to list recipes: {e}")
    
    def validate_recipe(self, recipe_path: str) -> Dict[str, Any]:
        """
        Validate a Goose recipe file.
        
        Args:
            recipe_path: Path to the recipe file
        
        Returns:
            Dictionary with validation results
            
        Raises:
            GooseRecipeError: If validation fails
        """
        try:
            args = ["recipe", "validate", recipe_path]
            result = self._run_command(args)
            
            return {
                "valid": True,
                "message": "Recipe is valid",
                "output": result.stdout
            }
            
        except GooseError as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def run_recipe(
        self,
        recipe_path: str,
        interactive: bool = False,
        explain: bool = False,
        session_name: Optional[str] = None,
        max_turns: int = 1000
    ) -> Dict[str, Any]:
        """
        Run a Goose recipe.
        
        Args:
            recipe_path: Path to the recipe file
            interactive: Continue in interactive mode after recipe
            explain: Show recipe details instead of running
            session_name: Name for the session
            max_turns: Maximum turns without user input
        
        Returns:
            Dictionary with execution results
        """
        try:
            args = ["run", "--recipe", recipe_path]
            
            if interactive:
                args.append("--interactive")
            
            if explain:
                args.append("--explain")
            
            if session_name:
                args.extend(["-n", session_name])
            
            args.extend(["--max-turns", str(max_turns)])
            
            result = self._run_command(args, timeout=600)
            
            return {
                "success": True,
                "output": result.stdout,
                "recipe_path": recipe_path,
                "timestamp": datetime.now().isoformat()
            }
            
        except GooseError as e:
            return {
                "success": False,
                "error": str(e),
                "recipe_path": recipe_path,
                "timestamp": datetime.now().isoformat()
            }
    
    def create_recipe_from_session(
        self,
        output_path: str = "./recipe.yaml",
        session_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a recipe from current session (requires interactive session).
        
        Args:
            output_path: Path where recipe will be saved
            session_name: Name of session to create recipe from
        
        Returns:
            Dictionary with creation results
            
        Note:
            This method is mainly for reference - recipe creation typically
            happens within interactive sessions using /recipe command.
        """
        return {
            "message": "Recipe creation from sessions requires interactive mode.",
            "suggestion": "Use the /recipe command within an interactive Goose session",
            "output_path": output_path
        }
    
    # Schedule Management Methods
    
    def list_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """
        List all scheduled Goose jobs.
        
        Returns:
            List of scheduled job dictionaries
            
        Raises:
            GooseScheduleError: If listing jobs fails
        """
        try:
            args = ["schedule", "list"]
            result = self._run_command(args)
            
            # Parse the output - this might need adjustment based on actual format
            jobs = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    jobs.append({"output": line})
            
            return jobs
            
        except GooseError as e:
            raise GooseScheduleError(f"Failed to list scheduled jobs: {e}")
    
    def add_scheduled_job(
        self,
        schedule_id: str,
        cron_expression: str,
        recipe_path: str
    ) -> Dict[str, Any]:
        """
        Add a new scheduled job.
        
        Args:
            schedule_id: Unique identifier for the job
            cron_expression: Cron schedule expression
            recipe_path: Path to the recipe file
        
        Returns:
            Dictionary with creation results
            
        Raises:
            GooseScheduleError: If job creation fails
        """
        try:
            args = [
                "schedule", "add",
                "--schedule-id", schedule_id,
                "--cron", cron_expression,
                "--recipe-source", recipe_path
            ]
            
            result = self._run_command(args)
            
            return {
                "success": True,
                "schedule_id": schedule_id,
                "cron": cron_expression,
                "recipe_path": recipe_path,
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            }
            
        except GooseError as e:
            raise GooseScheduleError(f"Failed to add scheduled job: {e}")
    
    def remove_scheduled_job(self, schedule_id: str) -> bool:
        """
        Remove a scheduled job.
        
        Args:
            schedule_id: ID of the job to remove
        
        Returns:
            True if successful
            
        Raises:
            GooseScheduleError: If removal fails
        """
        try:
            args = ["schedule", "remove", "--schedule-id", schedule_id]
            self._run_command(args)
            return True
            
        except GooseError as e:
            raise GooseScheduleError(f"Failed to remove scheduled job: {e}")
    
    def run_scheduled_job_now(self, schedule_id: str) -> Dict[str, Any]:
        """
        Run a scheduled job immediately.
        
        Args:
            schedule_id: ID of the job to run
        
        Returns:
            Dictionary with execution results
        """
        try:
            args = ["schedule", "run-now", "--schedule-id", schedule_id]
            result = self._run_command(args, timeout=600)
            
            return {
                "success": True,
                "schedule_id": schedule_id,
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            }
            
        except GooseError as e:
            return {
                "success": False,
                "schedule_id": schedule_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def list_schedule_sessions(self, schedule_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List sessions created by a scheduled job.
        
        Args:
            schedule_id: ID of the scheduled job
            limit: Maximum number of sessions to return
        
        Returns:
            List of session dictionaries
        """
        try:
            args = ["schedule", "sessions", "--schedule-id", schedule_id, "-l", str(limit)]
            result = self._run_command(args)
            
            # Parse sessions - format may vary
            sessions = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    sessions.append({"output": line})
            
            return sessions
            
        except GooseError as e:
            raise GooseScheduleError(f"Failed to list schedule sessions: {e}")
    
    # System Information Methods
    
    def get_system_info(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Get Goose system information.
        
        Args:
            verbose: Include detailed configuration
        
        Returns:
            Dictionary with system information
        """
        try:
            args = ["info"]
            if verbose:
                args.append("--verbose")
            
            result = self._run_command(args)
            
            return {
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            }
            
        except GooseError as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_version(self) -> str:
        """
        Get Goose version.
        
        Returns:
            Version string
        """
        try:
            result = self._run_command(["--version"])
            return result.stdout.strip()
        except GooseError as e:
            return f"Error getting version: {e}"
    
    def configure_goose(self) -> Dict[str, str]:
        """
        Trigger Goose configuration (interactive).
        
        Returns:
            Dictionary with configuration info
            
        Note:
            This is typically an interactive process
        """
        return {
            "message": "Configuration is typically done interactively",
            "command": "goose configure",
            "suggestion": "Run 'goose configure' in terminal for interactive setup"
        }
    
    # Utility Methods
    
    def create_instruction_file(self, instructions: str, filename: Optional[str] = None) -> str:
        """
        Create a temporary instruction file.
        
        Args:
            instructions: Instruction text
            filename: Optional filename (will create temp file if not provided)
        
        Returns:
            Path to the instruction file
        """
        if filename:
            file_path = filename
        else:
            fd, file_path = tempfile.mkstemp(suffix='.txt', prefix='goose_instructions_')
            import os
            os.close(fd)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        return file_path
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """
        Clean up temporary files.
        
        Args:
            file_paths: List of file paths to remove
        """
        for file_path in file_paths:
            try:
                Path(file_path).unlink(missing_ok=True)
                self.logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up {file_path}: {e}")


# Convenience functions for common use cases

def quick_task(instructions: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Quick way to run a single task with Goose.
    
    Args:
        instructions: Task instructions
        extensions: Optional list of extensions to enable
    
    Returns:
        Task execution results
    """
    client = GooseClient()
    return client.run_task(
        instructions=instructions,
        extensions=extensions or ["developer"],
        no_session=True
    )


async def quick_task_async(instructions: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Quick way to run a single task with Goose asynchronously.
    
    Args:
        instructions: Task instructions
        extensions: Optional list of extensions to enable
    
    Returns:
        Task execution results
    """
    client = GooseClient()
    return await client.run_task_async(
        instructions=instructions,
        extensions=extensions or ["developer"]
    )


def analyze_logs(log_path: str, session_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze log files using Goose.
    
    Args:
        log_path: Path to log file
        session_name: Optional session name
    
    Returns:
        Analysis results
    """
    instructions = f"""
    Analyze the log file at {log_path}:
    1. Identify any errors or warnings
    2. Look for patterns or anomalies
    3. Provide a summary of key findings
    4. Suggest any actions needed
    """
    
    client = GooseClient()
    return client.run_task(
        instructions=instructions,
        extensions=["developer"],
        session_name=session_name or f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )


# def create_productivity_recipe(
#     name: str,
#     description: str,
#     tasks: List[str],
#     output_path: str
# ) -> str:
#     """
#     Create a productivity recipe YAML file.
    
#     Args:
#         name: Recipe name
#         description: Recipe description
#         tasks: List of tasks to include
#         output_path: Where to save the recipe
    
#     Returns:
#         Path to created recipe file
#     """
#     recipe_data = {
#         'name': name,
#         'description': description,
#         'parameters': [],
#         'instructions': '\n'.join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
#     }
    
#     with open(output_path, 'w') as f:
#         yaml.dump(recipe_data, f, default_flow_style=False)
    
#     return output_path


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    def main():
        """Example usage of the Goose client."""
        
        # Initialize client
        client = GooseClient()
        
        # Get system info
        print("=== System Info ===")
        info = client.get_system_info()
        print(info.get('output', 'No info available'))
        
        # List sessions
        print("\n=== Sessions ===")
        try:
            sessions = client.list_sessions()
            print(f"Found {len(sessions)} sessions")
            for session in sessions[:3]:  # Show first 3
                print(f"  - {session}")
        except Exception as e:
            print(f"Error listing sessions: {e}")
        
        # List recipes
        print("\n=== Recipes ===")
        try:
            recipes = client.list_recipes()
            print(f"Found {len(recipes)} recipes")
            for recipe in recipes[:3]:  # Show first 3
                print(f"  - {recipe}")
        except Exception as e:
            print(f"Error listing recipes: {e}")
        
        # Run a simple task
        print("\n=== Running Task ===")
        result = client.run_task(
            instructions="What's the current date and time?",
            extensions=["developer"],
            no_session=True
        )
        print(f"Task result: {result}")
        
        # Quick task example
        print("\n=== Quick Task ===")
        quick_result = quick_task("List the files in the current directory")
        print(f"Quick task result: {quick_result}")
    
    async def async_main():
        """Example async usage."""
        result = await quick_task_async("What's 2 + 2?")
        print(f"Async result: {result}")
    
    # Run examples
    print("Running synchronous examples...")
    main()
    
    print("\nRunning asynchronous example...")
    asyncio.run(async_main())
