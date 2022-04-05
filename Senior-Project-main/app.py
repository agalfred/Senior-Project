from website import create_app ##folder named website and imports __init__.py

if __name__ == "__main__":##runs this app.py file, not from import
    app = create_app()
    app.run(debug=True)##automatically reruns every changes
