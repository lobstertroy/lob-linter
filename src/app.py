import tempfile
from flask import Flask, request, jsonify
from controller import run_linter

app = Flask(__name__)

@app.route('/lint', methods=['POST'])
def lint():
  html_file = request.files['html_file']
  #delete = True means file will be deleted after the block ends
  with tempfile.NamedTemporaryFile(mode='wb+', delete=True, suffix='.html') as temp:
    #write incoming data to temp file
    temp.write(html_file.read())
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
