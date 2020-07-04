from flask import Flask, redirect, url_for, request, render_template
import os
from google.cloud import bigquery
import pandas as pd
from random import random
import plotly.graph_objects as go
from plotly.offline import plot


# The below lines allow for file paths to be shared on localhost and pythonanywhere server __file__ is a python majic variable 
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
my_file = os.path.join(THIS_FOLDER,"../dev-smoke-278920-cb67e104d184.json")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = my_file

client = bigquery.Client()	# start bigquery

app = Flask(__name__)

# Main page. index.html must be in templates folder
@app.route('/')
def hello_world():
	randVar = random()   # create random number, just for funsies
   	return render_template('/index.html', name=randVar) # returns index.html and sets name on html page

# test post in url
@app.route('/hello/<name>')
def hello_name(name):
	namely = name +"yoouuu!!!!"
	return '<h1> Hello %s!</h1>' % namely

# test returning multiple html as a variable
@app.route('/divTest')
def divTest():
	div = '<div> <h1> YOU!! </h1> <p> me! </p> </div>'
	return div


# Login testing - go to /login.html in browser
@app.route('/success/<name>')
def success(name):
	return 'Welcome %s' % name

@app.route('/login', methods=['POST', 'GET'])
def login():
		if request.method == 'POST':
			user=request.form['nm']
			return redirect(url_for('success', name=user))
		else:
			user=request.args.get('nm')
			return redirect(url_for('success', name=user))

@app.route('/login_page')
def login_page():
	return render_template('/login.html')

#Simple graph using hardcoded data here
@app.route('/graph')
def graph():
	fig=go.Figure(data=go.Scatter(x=[1,5,9],y=[2,3,1]))
	plt_div = plot(fig, include_plotlyjs=False, output_type='div')
	return render_template('/graph.html', pltDiv = plt_div)

#get data from google-cloud-bigquery and graph it
@app.route('/cloudGraph')
def cloudGraph():
	query = """
		SELECT * FROM bigquery-public-data.covid19_usafacts.confirmed_cases
		WHERE state='WA'
		"""
	query_job = client.query(query)  # call query to bigquery
	casesdf = query_job.to_dataframe() # convert results into dataframe

	casesDf_transp=casesdf.T   # transpose df to get dates in rows instead of columns
	casesDf_transp.columns = casesDf_transp.loc['county_name']  # set county names as column names
	casesDf_cleaned = casesDf_transp.drop(['county_name', 'state', 'county_fips_code', 'state_fips_code']) # drop rows by name
	
	# Chop off the first character of the index, then replace all underscores with slashes, then convert to date
	# and assign the date back to the index.
	casesDf_cleaned.index = pd.to_datetime(casesDf_cleaned.index.str[1:].str.replace('_','/'))
	Xaxis = casesDf_cleaned.index	#set x axis to df index (dates)
	Yaxis = casesDf_cleaned['King County'] # set y axis to values in king county column

	fig=go.Figure(data=go.Scatter(x=Xaxis, y=Yaxis))		# create plotly graph object
	#fig.update_layout(title='King County Covid Cases', xaxis_title = "Date", yaxis_title="Positive Case Count")
	
	# Add range slider
	fig.update_layout(

		# Add data source citation at bottom right of graph
	annotations = [dict(text='Source: bigquery-public-data.covid19_usafacts.confirmed_cases',
		showarrow=False,
		xref='paper',
		yref='paper',
		x=1,
		y=-.4
		)],
	title = 'King County Covid Cases',
	xaxis_title='Date',
	yaxis_title='Positive Case Count',
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="YTD",
                     step="year",
                     stepmode="todate"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    	)
	)

	plt_div = plot(fig, include_plotlyjs=False, output_type = 'div')    # output graph object as plotly div, must have link in html to plotlyjs


	print('this shows up in the terminal where the server is started!!')
	return render_template('/graph.html', pltDiv=plt_div)    # render /graph.html with graph as plt_div


# DONT NEED TO ADD THIS TO WEB SERVER---------
if __name__ == '__main__':
   app.run()