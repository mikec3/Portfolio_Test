from flask import Flask, redirect, url_for, request, render_template
import os
from google.cloud import bigquery
import pandas as pd
from random import random
import plotly.graph_objects as go
from plotly.offline import plot
import graphlab
from datetime import date, timedelta


# The below lines allow for file paths to be shared on localhost and pythonanywhere server __file__ is a python majic variable 
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
my_file = os.path.join(THIS_FOLDER,"../dev-smoke-278920-cb67e104d184.json")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = my_file

client = bigquery.Client()	# start bigquery

app = Flask(__name__)

# Main page. index.html must be in templates folder
@app.route('/')
def hello_world():

	return render_template('/index.html') # returns index.html

# test post in url
@app.route('/hello/<name>')
def hello_name(name):
	namely = name +"yoouuu!!!!"
	return '<h1> Hello %s!</h1>' % namely

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

# get data from google-cloud-bigquery and graph it
# All US states on a line graph
@app.route('/cloudGraph')
def cloudGraph():

	# Google BigQuery Query
	query = """
		SELECT * FROM bigquery-public-data.covid19_usafacts.confirmed_cases
		"""
	query_job = client.query(query)  # call query to bigquery
	casesdf = query_job.to_dataframe() # convert results into dataframe

	#Group the county level into states, sum all counties, then transpose so dates are index
	state_levelDf = casesdf.groupby(['state']).sum().T

	#Use state level df to create a total column, will be used for line graph of all states
	state_levelDf['Total'] = state_levelDf.sum(axis=1)

	
	# Chop off the first character of the index, then replace all underscores with slashes, then convert to date
	# and assign the date back to the index.
	state_levelDf.index = pd.to_datetime(state_levelDf.index.str[1:].str.replace('_','/'))
	Xaxis = state_levelDf.index	#set x axis to df index (dates)
	Yaxis = state_levelDf['Total'] # set y axis to values in king county column

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
		y=-.45
		)],
	# title = 'Total US COVID cases',
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

	line_graph_div = plot(fig, include_plotlyjs=False, output_type = 'div')    # output graph object as plotly div, must have link in html to plotlyjs

	# Create mapDiv - a choropleth of the states cumulative total
	# Keep only columns and last row (running total)
	state_levelDf = casesdf.groupby(['state']).sum().T
	state_levelDf_total = state_levelDf.iloc[[-1]]

	#Transpose back to states and total in rows
	statesDf = state_levelDf_total.T

	#Rename total column
	statesDf.columns = ['Total']

	#Get the date of the last record and convert to date appearance
	lastUpdated = list(casesdf.columns)[-1][1:].replace('_','/')

	mapFig = go.Figure(data=go.Choropleth(
		locations=statesDf.index,
		z=statesDf['Total'],
		locationmode='USA-states',
		colorscale='Reds',
		colorbar_title='Positive Cases',
		# text="yooo",    # Hover Text
	))
	mapFig.update_layout(
		title={
		'text':'Total Positive COVID cases per state as of {}'.format(lastUpdated),
		# 'pad': dict(t=-300,b=-200),
		# 'yanchor':'top',
		},
		# margin= dict(t=200,r=200),
		# title_text = 'Total Positive COVID cases per state as of {}'.format(lastUpdated),
		geo_scope='usa',

		)
	mapDiv = plot(mapFig, include_plotlyjs=False, output_type='div')

	print('this shows up in the terminal where the server is started!!')
	return render_template('/graph.html', pltDiv=line_graph_div, mapDiv=mapDiv)    # render /graph.html with graph as plt_div

# ---------------------- TESTING ----------------------------------------------------------------
# ---------------------- TESTING ----------------------------------------------------------------
@app.route('/Select_dates')
def Select_dates():
	return render_template('/Select_Dates.html')

@app.route('/Predict_Seattle_Weather', methods=['POST', 'GET'])
def Predict_Seattle_Weather():
		if request.method == 'POST':
			date=request.form['date']
		else:
			date=request.args.get('date')

		# Load the linear regression model, predicts TMAX for Seattle based on week of year and year.
		weather_model = graphlab.load_model('Seattle_Weather_Linear_Regression_Model')

		# Prepare the Input, add week of year as a string (_coef) and year from the date column
		input_string = date
		inputdf = pd.DataFrame({"DATE":[input_string]})
		inputdf['DATE'] = pd.to_datetime(inputdf['DATE'])
		inputdf['YEAR'] = inputdf['DATE'].dt.year
		inputdf['WEEK'] = inputdf['DATE'].dt.week.astype(str)

		# Make the TMAX prediction on the date given
		prediction = weather_model.predict(graphlab.SFrame(inputdf))

		#Store the success and results in a string for display
		prediction_string = " The max temp On {} will be {}.".format(date, prediction)

		#Make prediction plot--------------------------------------------------------
		days_before_after = 120

		#Initialize the inputdf with the requested date
		inputdf = pd.DataFrame({"DATE":[input_string]})
		inputdf['DATE'] = pd.to_datetime(inputdf['DATE'])

		# Start the dataframe at n days before the input date
		inputdf['DATE'] = (inputdf['DATE']-timedelta(days=days_before_after))

		# Create a list of dates that are before and after the input date
		for i in range(1,(days_before_after*2)):
			new_day = (inputdf['DATE'].iloc[i-1]+timedelta(days=1))
			inputdf = inputdf.append({'DATE':new_day}, ignore_index=True)
		
		# Create the Year and Week columns from the DATE column (Year and Week are model features)
		inputdf['YEAR'] = inputdf['DATE'].dt.year
		inputdf['WEEK'] = inputdf['DATE'].dt.week.astype(str)

		# Build the prediction column for the whole dataframe of dates before and after requested date
		inputdf['Predicted_TMAX'] = weather_model.predict(graphlab.SFrame(inputdf))

		fig=go.Figure(data=go.Scatter(x=inputdf['DATE'], y=inputdf['Predicted_TMAX']))		# create plotly graph object

		# Add range slider
		fig.update_layout(

		# Add data source citation at bottom right of graph
		annotations = [dict(text='Training Data Source: https://www.kaggle.com/rtatman/did-it-rain-in-seattle-19482017',
			showarrow=False,
			xref='paper',
			yref='paper',
			x=1,
			y=-.45
			)],
		# title = 'Total US COVID cases',
		xaxis_title='Date',
		yaxis_title='Predicted Max Temperature (F)',
		title = "Predicting Seattle's Max Temperature On Any Given Date Using Linear Regression",
		xaxis=dict(
			rangeselector=dict(
				buttons=list([
					dict(count=2,
						label="1m",
						step="month",
						stepmode="backward"),
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
	
		fig.add_annotation(x=inputdf['DATE'].iloc[days_before_after], y=inputdf['Predicted_TMAX'].iloc[days_before_after],
				text="Predicted Max Temp on {} is {}*F".format(input_string, int(inputdf['Predicted_TMAX'].iloc[days_before_after])),
				showarrow=True,
				arrowhead=5,
				yshift=10)

		weather_graph_div = plot(fig, include_plotlyjs=False, output_type='div')

		# Redirect browser back to the select_dates page, use  thecreated plot to show the results------
		return render_template('/Select_Dates.html', weather_prediction_graph_div=weather_graph_div)

# ---------------------- END_TESTING ----------------------------------------------------------------
# ---------------------- END_TESTING ----------------------------------------------------------------

# DONT NEED TO ADD THIS TO WEB SERVER---------
if __name__ == '__main__':
   app.run()