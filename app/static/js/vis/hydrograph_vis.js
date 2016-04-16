$(document).ready(function(){
	var chartData=[];
	var hydroJsonData;
	// this list is used to mark which hydro to draw
	var isDrawHydro;
	var hydroNum;
	// this record the chosen ID
	var chosenID;
	var scenarioID = $('#scenario_id').text();

	// Load the Visualization API and the chart package.
	google.charts.load('current', {'packages':['corechart']});



	// get data from /api/scenarios
	$.get('/api/scenarios', function(data){
		// store the whole data here for later use
		hydroJsonData = data;

		hydroNum = data["scenarios"].length;
		// init it with the same length of hydro
		for(var i=0; i<hydroNum; i++)
		{
			chartData.push([]);
		}
		// true means should be drawn, false means should not be drawn
		isDrawHydro = new Array(hydroNum);

		var chosenHydroNum;

		// find the current json file
		for(var i=0; i<hydroNum; i++)
		{
			var tempID = data["scenarios"][i]['_id']['$oid'];
			var tempName = data["scenarios"][i]['name'];
			if(tempID == scenarioID)
			{
				addDataIntoChart(i);
				isDrawHydro[i] = true;
				chosenID = i;
			}
			// if this is not the current chosen scenario
			// create a checkbox for it
			else
			{
				//$("#checkBoxDiv").append("<input type='checkbox' id='"+tempID+"' value='"+tempID+"'>"+tempName);
				$("#tableItemID").append(
					"<tr key="+tempID+">"+
					"<td>"+tempName+"</td>"+
					"<td>"+"<input type='checkbox' id='"+tempID+"' value='"+tempID+"'></td>"+
					"</tr>"
				);
				isDrawHydro[i] = false;
			}
		}


		// draw line chart here
		google.charts.setOnLoadCallback(drawChart);
	});

	// process checkbox click event here
	// this is used for checkbox, if the checkbox is checked then
	// add the line chart to the hydrograph
	$(document).on('change','[type=checkbox]',function(){
		var checkboxID = this.value;
		// if checked add hydrograph
		if($("#"+checkboxID).prop("checked"))
		{
			for(var i=0; i<hydroNum; i++)
			{
				var tempID = hydroJsonData["scenarios"][i]['_id']['$oid'];
				if(tempID == checkboxID)
				{
					isDrawHydro[i] = true;
					addDataIntoChart(i);
				}

			}
		}
		// else remove it
		else
		{
			for(var i=0; i<hydroNum; i++)
			{
				var tempID = hydroJsonData["scenarios"][i]['_id']['$oid'];
				if(tempID == checkboxID)
				{
					isDrawHydro[i] = false;
				}

			}
		}

		// draw line chart here
		google.charts.setOnLoadCallback(drawChart);
	});

	function addDataIntoChart(chosenI)
	{
		var tempJson = hydroJsonData["scenarios"][chosenI];

		// get data into an array
		// each element is number
		var dataArray = tempJson["hydrograph"]['streamflow_array'];
		// get timestamps into an array
		// each element is obj, need to use timestampsArray[0]['$date'] to extract date data, the date is number
		var timestampsArray = tempJson["hydrograph"]['time_array'];

		// for most cases the data length should be the same with timestamps length
		var tempArray;
		// only fill the chartData[chosenI] if that is empty
		if(chartData[chosenI].length == 0)
		{
			if(dataArray.length == timestampsArray.length)
			{
				// prepare data to draw chart
				for(var i=0; i<dataArray.length; i++)
				{
					// tow columns for the current version, time and data
					//tempArray = [new Date(timestampsArray[i]['$date']),dataArray[i]];
					tempArray = [new Date(timestampsArray[i]['$date']),dataArray[i]];
					chartData[chosenI].push(tempArray);
				}
			}
			else
			{
				console.log("Time array and data array are not the same length");
			}
		}
	}


	function drawChart() {
		var data = new google.visualization.DataTable();
		data.addColumn('date','Time');
		var tempName;

		for(var i=0; i<hydroNum; i++)
		{
			if(isDrawHydro[i])
			{
				// get name
				tempName = hydroJsonData["scenarios"][i]['name'];
				data.addColumn('number',tempName);

			}
		}

		// prepare data
		var finalTuple = [];
		var tempTuple;
		var chosenData = chartData[chosenID];
		// use the chosen one to get length
		var tupleNum = chosenData.length;
		for(var m=0; m<tupleNum; m++)
		{
			tempTuple = [];
			// 0 is timestamp and 1 is data
			tempTuple.push(chosenData[m][0]);
			for(var i=0; i<hydroNum; i++)
			{
				if(isDrawHydro[i])
				{
					// 0 is timestamp and 1 is data
					tempTuple.push(chartData[i][m][1]);
				}
			}
			finalTuple.push(tempTuple);
		}

		data.addRows(finalTuple);

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


