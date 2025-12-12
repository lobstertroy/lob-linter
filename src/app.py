import tempfile
from flask import Flask, request, jsonify, render_template
from controller import run_linter
import requests

app = Flask(__name__)

def is_url(text):
  """simple check to see if string is valid-looking URL"""
  text = text.strip()
  return text.startswith('http://') or text.startswith('https://')

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/lint', methods=['POST'])
def lint():
  content_to_write = b"" # initialize as bytes

  if 'html_file' in request.files:
    html_file = request.files['html_file']
    if html_file and html_file.filename != '':
      content_to_write = html_file.read()

  if not content_to_write:
    return jsonify({'errors': ['No file or content provided']}), 400

  try:
    decoded_text = content_to_write.decode('utf-8').strip()

    #if it looks like a URL and not like HTML
    if is_url(decoded_text) and "<html" not in decoded_text.lower():
      print(f"URL detected: {decoded_text}")
      try:
        response = requests.get(decoded_text, timeout=10)
        if response.status_code == 200:
          content_to_write = response.content #content -> downloaded HTML
          print("Download successful.")
        else:
          return jsonify({'errors': [f"Could not download URL. Status: {response.status_code}"]}), 400
      except Exception as e:
        return jsonify({'errors': [f"URL Fetch failed: {str(e)}"]}), 400
  except UnicodeDecodeError:
    #if we can't decode it, it's probably a binary file
    pass

  #delete = True means file will be deleted after the block ends
  with tempfile.NamedTemporaryFile(mode='wb+', delete=True, suffix='.html') as temp:
    #write incoming data to temp file
    temp.write(content_to_write)
    temp.flush() #ensure data is written to disk immediately
    print(f"Temp file created at {temp.name}")
    #run linter
    errors = run_linter(temp.name)
    if errors:
      return jsonify({'errors': errors}), 400
    else:
      return jsonify({'message': 'No errors found'}), 200

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')
