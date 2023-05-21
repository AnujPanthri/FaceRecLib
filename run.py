from app import create_app

app=create_app()
app.run(debug=True)
# app.run(debug=True,host='192.168.43.94') # Nokia 6.1
# app.run(debug=True,host='192.168.43.76')