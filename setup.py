#!/usr/bin/env python3
import os
import subprocess
import json
import sys
from pathlib import Path
import platform

def run_command(command, cwd=None):
    """Run a shell command and handle errors"""
    try:
        subprocess.run(command, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        exit(1)

def setup_project():
    # Create virtual environment
    print("\nCreating virtual environment...")
    run_command("python -m venv venv")
    
    # Activate virtual environment
    if platform.system() == "Windows":
        activate_script = "venv\\Scripts\\activate"
        # On Windows, we need to modify the PATH to include the virtual environment
        venv_path = os.path.abspath("venv\\Scripts")
        os.environ["PATH"] = venv_path + os.pathsep + os.environ["PATH"]
        # Also activate using the activate.bat script
        run_command(f"{activate_script}.bat")
    else:
        activate_script = "source venv/bin/activate"
        run_command(activate_script)
    
    # Verify we're in the virtual environment
    if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
        print("Failed to activate virtual environment. Please activate it manually:")
        if platform.system() == "Windows":
            print("venv\\Scripts\\activate")
        else:
            print("source venv/bin/activate")
        exit(1)
    
    # Get user input
    project_name = input("Enter project name: ")
    supabase_url = input("Enter SUPABASE_URL: ")
    supabase_key = input("Enter SUPABASE_KEY: ")
    
    # Create .env file
    env_content = f"""SUPABASE_URL={supabase_url}
SUPABASE_KEY={supabase_key}
"""
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Install Python requirements
    print("\nInstalling Python requirements...")
    run_command("pip install -r requirements.txt")
    
    # Setup Tailwind
    print("\nSetting up Tailwind...")
    os.makedirs("tailwindcss", exist_ok=True)
    
    # Initialize npm and install dependencies
    run_command("npm init -y", cwd="tailwindcss")
    run_command("npm install -D tailwindcss@3.4.1", cwd="tailwindcss")
    run_command("npm install -D @tailwindcss/forms", cwd="tailwindcss")
    run_command("npm install preline", cwd="tailwindcss")
    run_command("npx tailwindcss init", cwd="tailwindcss")
    
    # Update tailwind.config.js
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../templates/**/*.{html,js}",
    'node_modules/preline/dist/*.js',
    '../static/js/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('preline/plugin'),
  ],
}"""
    
    with open('tailwindcss/tailwind.config.js', 'w') as f:
        f.write(tailwind_config)
    
    # Copy preline.js to static folder
    print("\nSetting up static files...")
    os.makedirs("static/js", exist_ok=True)
    run_command("cp tailwindcss/node_modules/preline/dist/preline.js static/js/")
    
    print("\nSetup complete! Your virtual environment is activated.")
    print("To start development server, run:")
    print("fastapi dev")
    print("\nIf you open a new terminal, remember to activate the virtual environment first:")
    if platform.system() == "Windows":
        print("venv\\Scripts\\activate")
    else:
        print("source venv/bin/activate")

if __name__ == "__main__":
    setup_project()