import tempfile
from flask import Flask, request, jsonify, render_template
from controller import run_linter
import requests
import re

app = Flask(__name__)

def is_url(text):
  """simple check to see if string is valid-looking URL"""
  text = text.strip()
  return text.startswith('http://') or text.startswith('https://')

def check_merge_variables(text):
  """
  Scans HTML for Lob merge variable issues:
  1. Incorrect delimiter usage (<> or [] vs {{}})
  2. invalid characters inside {{}}
  3. whitespace inside {{}}
  """
  errors = []

  # defined allowlist of safe HTML tags to ignore as bad merge variables
  VALID_HTML_TAGS = {
    'html', 'head', 'body', 'title', 'meta', 'link', 'style', 'script', 'noscript', 'div', 'span', 'p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'dl', 'dt', 'dd', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col', 'a', 'img', 'b', 'i', 'u', 'strong', 'em', 'small', 'big', 'strike', 'blockquote', 'code', 'pre', 'form', 'input', 'textarea', 'button', 'select', 'option', 'label', 'fieldset', 'legend', 'iframe', 'header', 'footer', 'nav', 'section', 'article', 'aside', 'main', 'figure', 'figcaption', '!doctype'
  }

  # incorrect delimiter usage, smarter check for html tags
  for match in re.finditer(r'<([^>]+)>', text):
    print(match)
    full_match = match.group(0) # e.g. "<First Name>" or "<div class='row'"
    inner_content = match.group(1).strip() # e.g. "First Name" or "div class='row'"

    # skip comments
    if inner_content.startswith('<!--'):
      continue

    # extract tag name to check validity
    # get first word (eg "div class='row'" -> "div", "First Name" -> "first")
    first_word = inner_content.split()[0].lower()

    # remove starting slash (closing tags)
    if first_word.startswith('/'):
      first_word = first_word[1:]

    # remove trailing slash (self-closing tags)
    first_word = first_word.rstrip('/')

    # is this a known HTML tag?
    if first_word in VALID_HTML_TAGS:
      continue # ignore bc it's real HTML

    # if not known HTML, it's a bad merge variable :)
    errors.append(f"Incorrect delimiter usage: found {full_match} but expected {{{{{inner_content}}}}}")

  # check for square bracket merge variables - catch [name] but not CSS/code like [type="text"] or array[0]
  for match in re.finditer(r'\[.*?\]', text):
    full_match = match.group(0) #e.g. "[name]" or "[type="text"]"
    inner_content = match.group(1) # e.g. "name" or "type="text""

    # if it contains quotes, equals, or parentheses, it's likely a CSS/code thing
    if any(char in inner_content for char in ['"', '=', '(', ')', '"']):
      continue

    partial_match = full_match.strip('[]')
    errors.append(f"Incorrect delimiter usage: found {full_match} but expected {{{{{partial_match}}}}}")

  # invalid characters inside {{}}
  forbidden_pattern = re.compile(r'[\s!"#%\'()*+,/;<=>@[\\\]^`{|}~]')

  for match in re.finditer(r'\{\{(.*?)\}\}', text):
    original_text = match.group(0) # eg "{{ my variable }}"
    inner_content = match.group(1) # eg " my variable "

    #is it empty?
    if not inner_content:
      errors.append(f"Empty merge variable found: {original_text}")
      continue

    #check for forbidden chars or whitespace
    bad_chars = forbidden_pattern.findall(inner_content)
    if bad_chars:
      unique_bad = sorted(list(set(bad_chars))) # remove duplicates and sort
      clean_bad_display = ' '.join([f"'{c}'" if c != ' ' else "'whitespace'" for c in unique_bad])
      errors.append(f"Invalid merge variable {original_text}: contains {clean_bad_display}")
    return errors

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
    mv_errors = check_merge_variables(content_to_write.decode('utf-8'))
    errors.extend(mv_errors)
    if errors:
      return jsonify({'errors': errors}), 400
    else:
      return jsonify({'message': 'No errors found'}), 200

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')
