
import os
import sys
import subprocess
import platform
import venv
import shutil


def print_banner():
    banner = r"""
    Welcome!   
    ╭━━━┳╮╱╱╭┳━━━┳━━━┳━━━┳━━━╮
    ┃╭━╮┃╰╮╭╯┃╭━╮┃╭━╮┃╭━╮┃╭━╮┃
    ┃┃╱╰┻╮┃┃╭┫╰━━┫┃╱┃┃┃╱┃┃╰━━╮
    ┃┃╱╭╮┃╰╯┃╰━━╮┃╰━╯┃╰━╯┣━━╮┃
    ┃╰━╯┃╰╮╭╯┃╰━╯┃╭━╮┃╭━╮┃╰━╯┃
    ╰━━━╯╱╰╯╱╰━━━┻╯╱╰┻╯╱╰┻━━━╯        
    """
    print(banner)

def print_step(message):
    print(f"\n{'='*80}\n- {message}\n{'='*80}")

def run_command(command, cwd=None, in_venv=False):
    try:
        if in_venv:
            # Get the path to the virtual environment's Python interpreter
            if platform.system() == "Windows":
                python_path = os.path.join("venv", "Scripts", "python")
                pip_path = os.path.join("venv", "Scripts", "pip")
            else:
                python_path = os.path.join("venv", "bin", "python")
                pip_path = os.path.join("venv", "bin", "pip")
            
            # Replace python/pip commands with the venv version
            if command.startswith("python "):
                command = f"{python_path} {command[7:]}"
            elif command.startswith("pip "):
                command = f"{pip_path} {command[4:]}"
        
        subprocess.run(command, check=True, shell=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error details: {str(e)}")
        return False

def check_python_version():
    print_step("Checking Python version...")
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)
    print("Python version check passed!")

def create_virtual_env():
    print_step("Creating virtual environment...")
    # Remove existing venv if it exists
    if os.path.exists("venv"):
        print("Removing existing virtual environment...")
        shutil.rmtree("venv")
    
    venv.create("venv", with_pip=True)
    print("Virtual environment created successfully!")

def install_requirements():
    print_step("Installing Python requirements...")
    # Using --no-cache-dir to force fresh install
    run_command("pip install --no-cache-dir -r requirements.txt", in_venv=True)

def setup_tailwind():
    """Setup using npm install"""
    print_step("Setting up Tailwind dependencies...")
    
    if not os.path.exists("tailwindcss"):
        print("Error: tailwindcss directory not found!")
        sys.exit(1)
        
    if not os.path.exists("tailwindcss/package.json"):
        print("Error: package.json not found in tailwindcss directory!")
        sys.exit(1)
    
    # Remove existing node_modules if it exists
    node_modules_path = os.path.join("tailwindcss", "node_modules")
    if os.path.exists(node_modules_path):
        print("Removing existing node_modules...")
        shutil.rmtree(node_modules_path)
    
    # Clear npm cache and install dependencies
    print("Clearing npm cache...")
    run_command("npm cache clean --force", cwd="tailwindcss")
    
    print("Installing npm dependencies (fresh install)...")
    run_command("npm install --no-cache", cwd="tailwindcss")
    
    print("Starting Tailwind build process...")
    run_command("npm run build", cwd="tailwindcss")

def create_env_file():
    print_step("Setting up .env file...")
    
    # Check if .env already exists
    if os.path.exists(".env"):
        while True:
            overwrite = input(".env file already exists. Do you want to overwrite it? (y/n): ").lower()
            if overwrite in ['y', 'n']:
                if overwrite == 'n':
                    print("Skipping .env file creation...")
                    return
                break
    
    print("\nPlease enter your Supabase credentials:")
    print("(You can find these in your Supabase project settings)")
    
    # Get credentials from user
    while True:
        url = input("\nSupabase Project URL: ").strip()
        if url:
            break
        print("Project URL cannot be empty!")

    while True:
        key = input("Supabase Project Key: ").strip()
        if key:
            break
        print("Project Key cannot be empty!")
    
    # Create .env file
    env_content = f"""SUPABASE_URL={url}
SUPABASE_KEY={key}
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("\n.env file created successfully!")

def main():
    print_banner()
    check_python_version()
    create_env_file()
    create_virtual_env()
    install_requirements()
    setup_tailwind()
    

    print_step("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print("   .\\venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("\n2. Start the server:")
    print("   fastapi dev")

if __name__ == "__main__":
    main()