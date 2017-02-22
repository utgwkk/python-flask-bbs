from flask import Flask, request, render_template, redirect, url_for
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/threads/create', methods=['GET', 'POST'])
def create_thread():
    if request.method == 'GET':
        return render_template('create_thread.html')
    elif request.method == 'POST':
        return redirect(url_for('create_thread'))


if __name__ == '__main__':
    app.run()
