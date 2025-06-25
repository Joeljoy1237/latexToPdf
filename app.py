import os
import subprocess
from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
TEMPLATE_PATH = 'templates/biodata.tex'
GENERATED_FOLDER = 'generated'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# HTML form for the frontend
def get_form_html():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Bio Creator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            form { max-width: 500px; margin: auto; }
            label { display: block; margin-top: 15px; }
            input, textarea { width: 100%; padding: 8px; margin-top: 5px; }
            button { margin-top: 20px; padding: 10px 20px; }
        </style>
    </head>
    <body>
        <h2>Create Your Biodata PDF</h2>
        <form method="POST" action="/generate" enctype="multipart/form-data">
            <label>Name <input name="name" required></label>
            <label>Date of Birth <input name="dob" required></label>
            <label>Blood Group <input name="blood" required></label>
            <label>Address <input name="address" required></label>
            <label>Years of Experience <input name="experience" required></label>
            <label>Educational Qualification <input name="education" required></label>
            <label>Assigned Class <input name="assignedclass" required></label>
            <label>Other Duties <input name="duties" required></label>
            <label>Phone Number <input name="phone" required></label>
            <label>Email ID <input name="email" type="email" required></label>
            <label>Profile Image <input name="profileimage" type="file" accept="image/*" required></label>
            <button type="submit">Generate PDF</button>
        </form>
    </body>
    </html>
    '''

@app.route('/', methods=['GET'])
def index():
    return get_form_html()

@app.route('/generate', methods=['POST'])
def generate():
    # Get form data
    fields = [
        'name', 'dob', 'blood', 'address', 'experience', 'education',
        'assignedclass', 'duties', 'phone', 'email'
    ]
    data = {field: request.form.get(field, '') for field in fields}

    # Handle image upload
    image = request.files['profileimage']
    if image:
        image_filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)
        data['profileimage'] = image_filename
    else:
        data['profileimage'] = ''

    # Read LaTeX template
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        tex_template = f.read()

    # Replace variables in LaTeX template
    for key, value in data.items():
        tex_template = tex_template.replace(f'\\newcommand{{\\{key}}}', f'\\newcommand{{\\{key}}}{{{value}}}')

    # Save filled LaTeX to file
    safe_name = secure_filename(data['name']) or 'biodata'
    tex_filename = f'{safe_name}.tex'
    tex_path = os.path.join(app.config['GENERATED_FOLDER'], tex_filename)
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex_template)

    # Copy image to generated folder (for pdflatex to find it)
    gen_image_path = os.path.join(app.config['GENERATED_FOLDER'], data['profileimage'])
    if os.path.exists(image_path):
        with open(image_path, 'rb') as src, open(gen_image_path, 'wb') as dst:
            dst.write(src.read())

    # Run pdflatex
    pdf_filename = f'{safe_name}.pdf'
    pdf_path = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)
    try:
        subprocess.run([
            'pdflatex',
            '-interaction=nonstopmode',
            '-output-directory', app.config['GENERATED_FOLDER'],
            tex_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return f"LaTeX Error: {e.stderr.decode('utf-8')}", 500

    # Return PDF for download
    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)

if __name__ == '__main__':
    app.run(debug=True) 