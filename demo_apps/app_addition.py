import sys
import os
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit_app  

def main():
    program_name = 'addition'
    program_test_name = 'addition_test'

    current_dir = os.path.dirname(os.path.abspath(__file__))
    compiled_nada_program_path = os.path.join(current_dir, "compiled_nada_programs", f"{program_name}.nada.bin")

    streamlit_app.main(program_test_name, compiled_nada_program_path)

if __name__ == "__main__":
    main()