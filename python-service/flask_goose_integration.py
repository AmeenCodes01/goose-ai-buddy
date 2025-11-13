"""
Flask Integration Example for Goose Client

This demonstrates how to integrate the Goose client into a Flask application
for URL logging and task automation productivity features.

Example usage:
    python flask_goose_integration.py
"""

from flask import Flask, request, jsonify, render_template_string
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

# Import our Goose client
from goose_integration import GooseClient, quick_task, analyze_logs, create_productivity_recipe

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Goose client
goose_client = None
executor = ThreadPoolExecutor(max_workers=4)

def init_goose():
    """Initialize Goose client with error handling."""
    global goose_client
    try:
        goose_client = GooseClient()
        logger.info(f"Goose client initialized. Version: {goose_client.get_version()}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Goose client: {e}")
        return False

@app.route('/')
def index():
    """Main dashboard."""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Goose Productivity Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .button { background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
            .button:hover { background-color: #45a049; }
            .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
            .success { background-color: #d4edda; color: #155724; }
            .error { background-color: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <h1>Goose Productivity Dashboard</h1>
        
        <div class="card">
            <h2>System Status</h2>
            <div id="status">
                {% if goose_available %}
                    <div class="status success">✓ Goose CLI is available</div>
                    <p>Version: {{ version }}</p>
                {% else %}
                    <div class="status error">✗ Goose CLI not available</div>
                {% endif %}
            </div>
        </div>

        <div class="card">
            <h2>Quick Actions</h2>
            <a href="/sessions" class="button">View Sessions</a>
            <a href="/recipes" class="button">View Recipes</a>
            <a href="/schedules" class="button">View Schedules</a>
        </div>

        <div class="card">
            <h2>URL Logging & Analysis</h2>
            <form action="/analyze-urls" method="post">
                <textarea name="urls" placeholder="Paste URLs here (one per line)" rows="5" cols="60"></textarea><br><br>
                <input type="submit" value="Analyze URLs" class="button">
            </form>
        </div>

        <div class="card">
            <h2>Quick Task</h2>
            <form action="/quick-task" method="post">
                <textarea name="instructions" placeholder="Enter task instructions..." rows="3" cols="60"></textarea><br><br>
                <input type="submit" value="Run Task" class="button">
            </form>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(
        template, 
        goose_available=goose_client is not None,
        version=goose_client.get_version() if goose_client else "N/A"
    )

@app.route('/api/status')
def api_status():
    """Get system status."""
    if not goose_client:
        return jsonify({"status": "error", "message": "Goose client not initialized"})
    
    try:
        info = goose_client.get_system_info()
        return jsonify({
            "status": "ok",
            "version": goose_client.get_version(),
            "info": info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/sessions')
def api_sessions():
    """List all Goose sessions."""
    if not goose_client:
        return jsonify({"error": "Goose client not available"})
    
    try:
        sessions = goose_client.list_sessions(format_type="json")
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/sessions')
def sessions():
    """Sessions page."""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Goose Sessions</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .back-link { display: inline-block; margin-bottom: 20px; text-decoration: none; color: #4CAF50; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Back to Dashboard</a>
        <h1>Goose Sessions</h1>
        <div id="sessions-content">Loading...</div>
        
        <script>
            fetch('/api/sessions')
                .then(response => response.json())
                .then(data => {
                    const content = document.getElementById('sessions-content');
                    if (data.error) {
                        content.innerHTML = '<p>Error: ' + data.error + '</p>';
                        return;
                    }
                    
                    if (data.sessions && data.sessions.length > 0) {
                        let html = '<table><tr><th>Session Info</th></tr>';
                        data.sessions.forEach(session => {
                            html += '<tr><td>' + JSON.stringify(session, null, 2) + '</td></tr>';
                        });
                        html += '</table>';
                        content.innerHTML = html;
                    } else {
                        content.innerHTML = '<p>No sessions found.</p>';
                    }
                });
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

@app.route('/api/recipes')
def api_recipes():
    """List available recipes."""
    if not goose_client:
        return jsonify({"error": "Goose client not available"})
    
    try:
        recipes = goose_client.list_recipes(format_type="json")
        return jsonify({"recipes": recipes})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/recipes')
def recipes():
    """Recipes page."""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Goose Recipes</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .back-link { display: inline-block; margin-bottom: 20px; text-decoration: none; color: #4CAF50; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Back to Dashboard</a>
        <h1>Available Recipes</h1>
        <div id="recipes-content">Loading...</div>
        
        <script>
            fetch('/api/recipes')
                .then(response => response.json())
                .then(data => {
                    const content = document.getElementById('recipes-content');
                    if (data.error) {
                        content.innerHTML = '<p>Error: ' + data.error + '</p>';
                        return;
                    }
                    
                    if (data.recipes && data.recipes.length > 0) {
                        let html = '<table><tr><th>Recipe Info</th></tr>';
                        data.recipes.forEach(recipe => {
                            html += '<tr><td>' + JSON.stringify(recipe, null, 2) + '</td></tr>';
                        });
                        html += '</table>';
                        content.innerHTML = html;
                    } else {
                        content.innerHTML = '<p>No recipes found.</p>';
                    }
                });
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

@app.route('/api/schedules')
def api_schedules():
    """List scheduled jobs."""
    if not goose_client:
        return jsonify({"error": "Goose client not available"})
    
    try:
        schedules = goose_client.list_scheduled_jobs()
        return jsonify({"schedules": schedules})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/schedules')
def schedules():
    """Schedules page."""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Scheduled Jobs</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .back-link { display: inline-block; margin-bottom: 20px; text-decoration: none; color: #4CAF50; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Back to Dashboard</a>
        <h1>Scheduled Jobs</h1>
        <div id="schedules-content">Loading...</div>
        
        <script>
            fetch('/api/schedules')
                .then(response => response.json())
                .then(data => {
                    const content = document.getElementById('schedules-content');
                    if (data.error) {
                        content.innerHTML = '<p>Error: ' + data.error + '</p>';
                        return;
                    }
                    
                    if (data.schedules && data.schedules.length > 0) {
                        let html = '<table><tr><th>Schedule Info</th></tr>';
                        data.schedules.forEach(schedule => {
                            html += '<tr><td>' + JSON.stringify(schedule, null, 2) + '</td></tr>';
                        });
                        html += '</table>';
                        content.innerHTML = html;
                    } else {
                        content.innerHTML = '<p>No scheduled jobs found.</p>';
                    }
                });
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

@app.route('/quick-task', methods=['POST'])
def quick_task_handler():
    """Handle quick task execution."""
    if not goose_client:
        return jsonify({"error": "Goose client not available"})
    
    instructions = request.form.get('instructions', '').strip()
    if not instructions:
        return jsonify({"error": "No instructions provided"})
    
    try:
        # Run task in background thread to avoid blocking
        def run_task():
            return goose_client.run_task(
                instructions=instructions,
                extensions=["developer"],
                no_session=True,
                max_turns=10  # Limit turns for quick tasks
            )
        
        future = executor.submit(run_task)
        result = future.result(timeout=120)  # 2 minute timeout
        
        # Return simple HTML response
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Task Result</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .back-link { display: inline-block; margin-bottom: 20px; text-decoration: none; color: #4CAF50; }
                .result { background-color: #f8f9fa; padding: 15px; border-radius: 4px; white-space: pre-wrap; }
                .success { border-left: 4px solid #28a745; }
                .error { border-left: 4px solid #dc3545; }
            </style>
        </head>
        <body>
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>Task Result</h1>
            <p><strong>Instructions:</strong> {{ instructions }}</p>
            {% if result.success %}
                <div class="result success">{{ result.output }}</div>
            {% else %}
                <div class="result error">Error: {{ result.error }}</div>
            {% endif %}
            <p><small>Executed at: {{ result.timestamp }}</small></p>
        </body>
        </html>
        """
        
        return render_template_string(template, instructions=instructions, result=result)
        
    except Exception as e:
        return jsonify({"error": f"Task execution failed: {str(e)}"})

@app.route('/analyze-urls', methods=['POST'])
def analyze_urls():
    """Analyze URLs for productivity insights."""
    if not goose_client:
        return jsonify({"error": "Goose client not available"})
    
    urls_text = request.form.get('urls', '').strip()
    if not urls_text:
        return jsonify({"error": "No URLs provided"})
    
    urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
    
    try:
        # Create analysis instructions
        instructions = f"""
        Analyze the following URLs for productivity insights:
        
        URLs:
        {chr(10).join(urls)}
        
        Please provide:
        1. Categorization of URLs (work, social media, news, documentation, etc.)
        2. Time-wasting vs productive content assessment
        3. Patterns in browsing behavior
        4. Recommendations for better productivity
        5. Any security or privacy concerns with the domains
        
        Format the response in a clear, structured way.
        """
        
        def run_analysis():
            return goose_client.run_task(
                instructions=instructions,
                extensions=["developer"],
                session_name=f"url_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_turns=15
            )
        
        future = executor.submit(run_analysis)
        result = future.result(timeout=180)  # 3 minute timeout
        
        # Return analysis results
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>URL Analysis Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .back-link { display: inline-block; margin-bottom: 20px; text-decoration: none; color: #4CAF50; }
                .result { background-color: #f8f9fa; padding: 15px; border-radius: 4px; white-space: pre-wrap; }
                .success { border-left: 4px solid #28a745; }
                .error { border-left: 4px solid #dc3545; }
                .url-list { background-color: #e9ecef; padding: 10px; border-radius: 4px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>URL Analysis Results</h1>
            
            <h2>Analyzed URLs:</h2>
            <div class="url-list">{{ urls|join('<br>')|safe }}</div>
            
            {% if result.success %}
                <h2>Analysis:</h2>
                <div class="result success">{{ result.output }}</div>
            {% else %}
                <div class="result error">Error: {{ result.error }}</div>
            {% endif %}
            
            <p><small>Analysis completed at: {{ result.timestamp }}</small></p>
        </body>
        </html>
        """
        
        return render_template_string(template, urls=urls, result=result)
        
    except Exception as e:
        return jsonify({"error": f"URL analysis failed: {str(e)}"})

@app.route('/api/task', methods=['POST'])
def api_run_task():
    """API endpoint for running tasks."""
    if not goose_client:
        return jsonify({"error": "Goose client not available"})
    
    data = request.get_json()
    if not data or 'instructions' not in data:
        return jsonify({"error": "Instructions required"})
    
    try:
        result = goose_client.run_task(
            instructions=data['instructions'],
            extensions=data.get('extensions', ['developer']),
            session_name=data.get('session_name'),
            no_session=data.get('no_session', True),
            max_turns=data.get('max_turns', 10)
        )
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/recipe/run', methods=['POST'])
def api_run_recipe():
    """API endpoint for running recipes."""
    if not goose_client:
        return jsonify({"error": "Goose client not available"})
    
    data = request.get_json()
    if not data or 'recipe_path' not in data:
        return jsonify({"error": "Recipe path required"})
    
    try:
        result = goose_client.run_recipe(
            recipe_path=data['recipe_path'],
            session_name=data.get('session_name'),
            max_turns=data.get('max_turns', 20)
        )
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/schedule/add', methods=['POST'])
def api_add_schedule():
    """API endpoint for adding scheduled jobs."""
    if not goose_client:
        return jsonify({"error": "Goose client not available"})
    
    data = request.get_json()
    required_fields = ['schedule_id', 'cron_expression', 'recipe_path']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": f"Required fields: {required_fields}"})
    
    try:
        result = goose_client.add_scheduled_job(
            schedule_id=data['schedule_id'],
            cron_expression=data['cron_expression'],
            recipe_path=data['recipe_path']
        )
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/logs/analyze', methods=['POST'])
def api_analyze_logs():
    """API endpoint for log analysis."""
    data = request.get_json()
    if not data or 'log_path' not in data:
        return jsonify({"error": "Log path required"})
    
    try:
        result = analyze_logs(
            log_path=data['log_path'],
            session_name=data.get('session_name')
        )
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    # Initialize Goose client
    if init_goose():
        print("Starting Flask app with Goose integration...")
        print("Visit http://localhost:5000 for the dashboard")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to initialize Goose client. Please check your installation.")
        print("Install Goose CLI: https://github.com/block/goose")
