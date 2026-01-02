import subprocess

def test_command(command):
    result = subprocess.run(
        ["python", "1pass_no_prompts.py"] + command,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Test failed: {result.stderr}")
    else:
        print(result.stdout)

if __name__ == "__main__":
    test_command(["account", "list"])
    test_command(["item", "get", "--vault", "your_vault_name", "your_item_id"])
