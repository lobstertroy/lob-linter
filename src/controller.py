import subprocess
import sys
import json

def run_linter(filepath):
  '''
  Runs node.js worker script and returns a list of errors
  '''
  # we need to run: node worker.js <filepath>
  # we need to capture standard output (stdout)
  # we want the result as a string, not bytes

  # DONE: fill in the subprocess.run call
  result = subprocess.run(
    ["node", "worker.js", filepath],
    capture_output = True,
    text = True,
  )

  #check if command failed
  if result.returncode != 0:
    print(f"Error running worker:", result.stderr)
    return []

  try:
    return json.loads(result.stdout)
  except json.JSONDecodeError:
    print(f"Error parsing JSON output: {result.stdout}")
    return []

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Usage: python controller.py <path_to_html_file>")
    sys.exit(1)

  filepath = sys.argv[1]
  print(f"Linting {filepath}...")

  output = run_linter(filepath)
  if output:
    for error in output:
      print(f"Error: {error}")
  else:
    print(f"No errors found in {filepath}")
