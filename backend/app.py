from flask import Flask, request, jsonify

def get_data():
    try:
        with open('names.txt', 'r', encoding='utf-8') as file:
            # read lines, strip whitespace, ignore empty lines
            names = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        names = []
    return names

app = Flask(__name__)


@app.route('/')
def welcome():
    return "Welcome to the Flask App!"


@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'GET':
        data = get_data()
        return jsonify({"data": data})

    # POST: accept JSON or form data with a `name` field and append to names.txt
    payload = request.get_json(silent=True) or request.form
    name = payload.get('name') if payload else None
    if not name:
        return jsonify({"error": "'name' is required"}), 400

    # append name to names.txt in a robust way
    try:
        # if file exists and not empty, prefix a newline before appending
        try:
            with open('names.txt', 'rb') as check:
                check.seek(0, 2)
                is_empty = check.tell() == 0
        except FileNotFoundError:
            is_empty = True

        with open('names.txt', 'a', encoding='utf-8') as f:
            if not is_empty:
                f.write('\n')
            f.write(name.strip())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"success": True, "name": name}), 201


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)