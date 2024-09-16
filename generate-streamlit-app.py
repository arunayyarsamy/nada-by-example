import questionary
from pathlib import Path
import os
import yaml
import subprocess
import shutil
import sys

STREAMLIT_APP_TEMPLATE = '''# This file was automatically generated by the generate-streamlit-app script.

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit_app

program_name = "{program_name}"
program_test_name = "{program_test_name}"

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path_nada_bin = os.path.join(current_dir, "compiled_nada_programs", f"{{program_name}}.nada.bin")
    path_nada_json = os.path.join(current_dir, "compiled_nada_programs", f"{{program_name}}.nada.json")

    if not os.path.exists(path_nada_bin):
        raise FileNotFoundError(f"Add `{{program_name}}.nada.bin` to the compiled_nada_programs folder.")
    if not os.path.exists(path_nada_json):
        raise FileNotFoundError(f"Run nada build --mir-json and add `{{program_name}}.nada.json` to the compiled_nada_programs folder.")

    streamlit_app.main(program_test_name, path_nada_bin, path_nada_json)

if __name__ == "__main__":
    main()
'''

def get_programs(directory):
    return sorted([f.stem for f in Path(directory).glob('*.py') if f.is_file()])

def get_test_files(directory, program_name):
    matching_files = []
    for file in Path(directory).glob('*.yaml'):
        try:
            with open(file, 'r') as f:
                test_data = yaml.safe_load(f)
                if test_data and 'program' in test_data and test_data['program'] == program_name:
                    matching_files.append(file)
        except yaml.YAMLError:
            print(f"Error reading {file}. Skipping.")
        except Exception as e:
            print(f"Unexpected error reading {file}: {e}. Skipping.")
    return matching_files

def select_program_and_test():
    programs = get_programs('src')
    if not programs:
        print("No Python programs found in 'src' directory.")
        return None, None

    selected_program = questionary.select(
        "Select an existing program to create a streamlit app demo:",
        choices=programs
    ).ask()

    test_files = get_test_files('tests', selected_program)
    if not test_files:
        print(f"No test files found for '{selected_program}' in 'tests' directory.")
        return selected_program, None

    selected_test = questionary.select(
        "Select a test file for starting input values:",
        choices=[f.name for f in test_files]
    ).ask()

    return selected_program, selected_test

def build_nada_program(program_name):
    try:
        subprocess.run(['nada', 'build', program_name, '--mir-json'], check=True)
        print(f"Successfully built {program_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building {program_name}: {e}")
        return False
    except FileNotFoundError:
        print("Error: 'nada' command not found. Make sure it's installed and in your PATH.")
        return False

def copy_nada_files(program_name):
    source_dir = Path('target')
    dest_dir = Path('streamlit_demo_apps/compiled_nada_programs')
    
    for ext in ['.nada.json', '.nada.bin']:
        source_file = source_dir / f"{program_name}{ext}"
        dest_file = dest_dir / f"{program_name}{ext}"
        
        if source_file.exists():
            shutil.copy2(source_file, dest_file)
            print(f"Copied {source_file} to {dest_file}")
        else:
            print(f"Warning: {source_file} not found")

def create_streamlit_app(program_name, test_name):
    try:
        app_content = STREAMLIT_APP_TEMPLATE.format(
            program_name=program_name,
            program_test_name=test_name
        )
        
        app_file_path = Path('streamlit_demo_apps') / f"app_{program_name}.py"
        print(f"Attempting to create file at: {app_file_path.absolute()}")
        
        # Ensure the directory exists
        app_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(app_file_path, 'w') as f:
            f.write(app_content)
        print(f"Created Streamlit app file: {app_file_path}")
        
        if app_file_path.exists():
            print(f"Streamlit app file successfully created at {app_file_path}")
            return app_file_path
        else:
            print(f"Error: File creation verified failed for {app_file_path}")
            return None
    except Exception as e:
        print(f"Error creating Streamlit app file: {e}")
        return None

def run_streamlit_app(app_path):
    try:
        print(f"Attempting to run Streamlit app: {app_path}")
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', str(app_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {e}")
    except Exception as e:
        print(f"Unexpected error running Streamlit app: {e}")

def main():
    program, test = select_program_and_test()
    
    if program:
        print(f"Selected program: {program}")
        if test:
            print(f"Selected test file: {test}")
            
            with open(os.path.join('tests', test), 'r') as file:
                test_data = yaml.safe_load(file)
                print("\nTest file contents:")
                print(yaml.dump(test_data, default_flow_style=False))
        
        if build_nada_program(program):
            copy_nada_files(program)
            app_path = create_streamlit_app(program, os.path.splitext(test)[0] if test else '')
            if app_path:
                run_streamlit_app(app_path)
    else:
        print("No program selected.")

if __name__ == "__main__":
    main()