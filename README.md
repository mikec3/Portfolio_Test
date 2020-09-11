# Portfolio_Test
Python with Flask web app portfolio practice
this is a test site using python 2.7 and flask

DEPENDENCIES
flask installed via venv "pip install flask"
pandas installed via venv
plotly installed via venv
pip install google-cloud-bigquery via venv


TO START

navigate to this directory and use command

% source bin/activate         // activates virtual environment

flask_app.py is the main python file. To run on local server nagivate to this directory and use command

% python flask_app.py
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

now type the http address into web browser to test

% CTRL+C 			// to exit the server
% deactivate		// to exit the venv

PAGES
-http://127.0.0.1:5000/			//navigates to home page

---WEB DEPLOYMENT - michaelcouch.pythonanywhere.com
-add files to /mysite/ directory
-add google cloud bigquery key.json file to folder before /mysite/ titled michaelcouch
-open BASH console and $ pip install plotly==4.8.1 --user
	-pip install google-cloud-bigquery --user
