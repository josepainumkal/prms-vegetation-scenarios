$(document).ready(function(){
	var inputJson;
	var chartData=[];

	// Load the Visualization API and the chart package.
	google.charts.load('current', {'packages':['corechart']});
	


	// get data from /api/scenarios
	$.get('/api/scenarios', function(data){
		inputJson = data;

		// get data into an array
		// each element is number
		var dataArray = inputJson["scenarios"][0]["hydrograph"]['streamflow_array'];
		// get timestamps into an array
		// each element is obj, need to use timestampsArray[0]['$date'] to extract date data, the date is number
		var timestampsArray = inputJson["scenarios"][0]["hydrograph"]['time_array'];

		// for most cases the data length should be the same with timestamps length
		var tempArray;
		if(dataArray.length == timestampsArray.length)
		{
			// prepare data to draw chart
			for(var i=0; i<dataArray.length; i++)
			{
				// tow columns for the current version, time and data
				tempArray = [timestampsArray[i]['$date'],dataArray[i]];
				chartData.push(tempArray);
			}
		}
		else
		{
			console.log("Time array and data array are not the same length");
		}

		// draw line chart here
		google.charts.setOnLoadCallback(drawChart);
	});

	function drawChart() {
		var data = new google.visualization.DataTable();
		data.addColumn('number','Time');
		data.addColumn('number','Hydro');

		data.addRows(chartData);


		var options = {
	        chart: {
	          title: 'Prototype Hydrograph',
	        },
	        width: 800,
	        height: 600
		};

		var chart = new google.visualization.LineChart(document.getElementById('hydrographDiv'));

		chart.draw(data, options);
	}

});


