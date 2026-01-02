#!/usr/bin/env python3

from subprocess import run, PIPE

def main():
    command = ["python", "1pass_no_prompts.py", "account", "list"]
    result = run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Test failed: {result.stderr}")
    else:
        print(result.stdout)

if __name__ == "__main__":
    main()
