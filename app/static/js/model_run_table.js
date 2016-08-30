$(document).ready(function(){
	// modifier variables start here
	// TODO this part should be done byusing get request
	// get the color from get request from the server
	var inputJson;

	// set up the canvas size
	var cellWidth = 12;
	var cellHeight = 12;

	// canvas col and row num
	var dataX;
	var dataY;
	// original veg code
	var vegOrigin;
	// current veg code
	var vegCurrent;

	// elevation information for all HRU cells
	var elevationInfo;

	var canvasWidth;
	var canvasHeight;
	var canvasHandle;
	var canvas2DContext;

	// this is for define color for the cells
	var colorScale;

	// record the chosen area rec top left
	var firstPoint = {x:-1,y:-1};
	// record the chosen area rec bot right
	var secondPoint = {x:-1,y:-1};
	// record mouse click time
	var clickTime = 0;

	// this var record all the chosen HRU num
	var chosenHRU = [];
	// this struct array records chosen HRU and color
	// [{colorInfo:'#ffffff',HRUInfo:[1,2,3]},{...}]
	var chosenAreaInfo = [];

	// define google map with map
	var map;
	// this is for image overlay
	var imgOverlay;
	var imageBounds;
	// url for overlay image
	var imgURL;

	// this is for mouse dragging
	var isDragging = false;
	var isMousePressing = false;
	var firstPosition;
	var secondPosition;

	var vegCode;
	var vegCodeLookup = {
	0: 'bare_ground',
	1: 'grasses',
	2: 'shrubs',
	3: 'trees',
	4: 'conifers'
	}
	// modifier variables end here

	var access_token;
	var modelRunServer;

	// this record how many model runs current user has
	var itemCount;

	var animationURL;
	var statsURL;
	$.get('/api/access_token', function(token){
		access_token = token;

		modelRunServer = $('#model_run_server_id').text() + '/modelruns';

		$.ajax({
			type: "GET",
			url: modelRunServer,
			contentType: "application/json; charset=utf-8",
			//dataType : 'jsonp',
			beforeSend : function(xhr) {
				// set header
				xhr.setRequestHeader("Authorization", "JWT " + token);
			},
			//data: data,
			error : function() {
			  // error handler
			  console.log('get model run information failed');
			},
			success: function(data) {
			    // success handler
			    listModelRunID(data);
			}
		});

	});

	function listModelRunID(data)
	{
		itemCount = data.num_results;
		if(itemCount != 0)
		{
			for(var i=0; i<itemCount; i++)
			{
				var tempItem = data.objects[i];
				$('#model-run-items').append("<tr key="+tempItem.id.toString()+">" +
												 "<td>"+tempItem.id.toString()+"</td>" +
												 "<td>"+tempItem.title+"</td>" +
												 "<td>"+tempItem.created_at+"</td>" +
												 // the button id is modelrunID
												 "<td><button class='modelRunChosenButton' id='"+tempItem.id.toString()+"' >Choose Me</button>"+"</td>" +
											 "</tr>");
			}
		}
		// there are no model runs in the model runserver
		else
		{
			$('#additional-info').append("<p>You do not have a modelrun in the server, but no worries. We prepare a default model run for you</p>");
			$.ajax({
				type: "GET",
				url: '/api/defaul_model_run',
				error : function() {
				},
				success: function(data) {
					$('#model-run-items').append("<tr key="+(-1).toString()+">" +
													 "<td>default</td>" +
													 "<td>default</td>" +
													 "<td>default</td>" +												 
													 "<td><button class='modelRunChosenButton' id='"+(-1).toString()+"' >Choose Me</button>"+"</td>" +
												 "</tr>");					
				}
			});
		}
	}

	// $('.modelRunChosenButton').click will not work
	// should use the following method
    $(document).on("click", ".modelRunChosenButton" , function() {
    	// get the current button id
    	var modelRunID = $(this).attr('id');
    	$('#step-3-title-id').empty();
    	$('#step-3-title-id').append("<h5>3. Modify The Chosen Model Run Veg</h5>");
    	$('#model-run-list').empty();
    	if(modelRunID != '-1')
    	{
	    	var modelRunURL = modelRunServer + '/' + modelRunID;
	    	// get the model run information
			$.ajax({
				type: "GET",
				url: modelRunURL,
				contentType: "application/json; charset=utf-8",
				//dataType : 'jsonp',
				beforeSend : function(xhr) {
					// set header
					xhr.setRequestHeader("Authorization", "JWT " + access_token);
				},
				//data: data,
				error : function() {
				  // error handler
				  console.log('get model run information failed');
				},
				success: function(data) {
				    // success handler
				    importChosenModelRun(data);
				}
			});
		}
		else
		{
			displayModelModifier();
		}
	});

	function importChosenModelRun(data)
	{
		var controlURL;
		var dataURL;
		var paramURL;
		
		for(var i=0; i<data.resources.length; i++) 
		{
			// for current version I only list the three input files
			if(data.resources[i].resource_type == 'control')
			{
				controlURL = data.resources[i].resource_url;
			}
			else if(data.resources[i].resource_type == 'data')
			{
				dataURL = data.resources[i].resource_url;
			}
			else if(data.resources[i].resource_type == 'param')
			{
				paramURL = data.resources[i].resource_url;
			}
			else if(data.resources[i].resource_type == 'animation')
			{
				animationURL = data.resources[i].resource_url;
			}
			else if(data.resources[i].resource_type == 'statsvar')
			{
				statsURL = data.resources[i].resource_url;
			}
		}

		// need to replace all the / with +++ in the url
		// or it will distract flask server
		controlURL = controlURL.replace(/\//g,'+++');
		dataURL = dataURL.replace(/\//g,'+++');
		paramURL = paramURL.replace(/\//g,'+++');
		animationURL = animationURL.replace(/\//g,'+++');
		statsURL = statsURL.replace(/\//g,'+++');
		// separate url by ---
		var url_info = controlURL + '---' + dataURL + '---' + paramURL;
        $.ajax({
		    type : "GET",
		    url : "/api/scenarios/download_input_files/" + url_info,
		    success: function(result) {
		    	displayModelModifier();
		    	getParameterList();
		    }
		});


	}
    function getParameterList(){
    	$.get('/api/get-parameter-list', function(data){

    		 var jsonData = JSON.parse(data);
            
             // alert(jsonData['param_list']);    
             // alert(jsonData['param_list'].length)
             // alert(jsonData['param_list'][0])

             // var paramList = jsonData['param_list'];

             for(var i=0;i<jsonData['param_list'].length;i++){
             	$('.show-list-param').append('<option value="' + jsonData['param_list'][i] + '">' + jsonData['param_list'][i] + '</option>');
             }

      //        var options = []
      //        $.each(paramList, function(item) {
      //   		options.append($("<option />").val(item).text(item));
    		// });
             // $("#changeParameter").append(options.join(''));
    	});
    }



	// this function is used to display veg modification section
	function vegeModifier()
	{
	  $.get('/api/base-veg-map', function(data){
	  	$('#model-veg-modifier-div-id').css('visibility','visible');
	    inputJson = data;

	    // grab col and row num
	    dataX = inputJson['projection_information']['ncol'];
	    dataY = inputJson['projection_information']['nrow'];
	    

	    vegOrigin = obtainJsoninto1D(inputJson);

	    elevationInfo = inputJson['elevation'].slice();
	    var minElevation = elevationInfo.min();
	    var maxElevation = elevationInfo.max();
	    // append input area and instruction
	    // this part should be dynamically generated
	    $('#elevationInputID').empty();
	    $("#elevationInputID").append("<p>The elevation scale is from "+minElevation.toString()+" to "+maxElevation.toString()+"</p>");
	    $("#elevationInputID").append("<input type='number' min='"+minElevation.toString()+"' max='"+maxElevation.toString()+"' step='0.1' id='elevationSelectorID'>");
	    $("#elevationInputID").append("<input type='button' class='btn btn-sm btn-sm-map' id='confirmElevationButton' value='Update Map by Elevation' />");

	    // should not use var vegCurrent = vegOrigin
	    // coz when we change vegCurrent and then vegOrigin will change too
	    vegCurrent = vegOrigin.slice();

	    canvasWidth = cellWidth*dataX;
	    canvasHeight = cellHeight*dataY;
	    
	    // I am so confusing at this part...
	    // If I change it into $('.mapCanvas').css('width',canvasWidth.toString()+'px');
	    // then it only draw 30 boxes each line
	    $('.mapCanvas').attr('width',canvasWidth.toString()+'px');
	    $('.mapCanvas').attr('height',canvasHeight.toString()+'px');

	    // place mapArray into canvas
	    canvasHandle = document.getElementById("myCanvas");
	    //var canvas2DContext = [];
	    canvas2DContext = canvasHandle.getContext("2d");

	    // this is for define color for the cells
	    //var scaleSize = Object.size(inputJson['vegetation_map']);
	    var scaleSize = 5;
	    colorScale = chroma.scale(['pink','black','blue','red','green']).colors(scaleSize);

	    // this part is used to push data into canvas
	    // and paint color
	    resetCanvas(vegOrigin);

	    // overlay canvas on google map
	    var latLonInformation = inputJson['projection_information'];
	    // TODO map overlay works correctly
	    overlayCanvasonGoogleMap(latLonInformation['xllcorner'],
	        latLonInformation['xurcorner'],
	        latLonInformation['yllcorner'],
	        latLonInformation['yurcorner']);

	    // I am not sure why the radio button does not work automatically, therefore, I need to change it manually
	    $("input[type='radio']").change(function(){
            var tempID = $('#vegetation-type-selector label.active input').val().toString();
            $("#"+tempID).attr('class','btn btn-custom');
            $("#"+this.value.toString()).attr('class','btn btn-custom active');
        });


	    $("#myCanvas")
	    .mousedown(function(evt){
	      isMousePressing = true;
	    })


	    .mousemove(function(evt){
	      // record the first mouse position
	      if(isDragging==false && isMousePressing==true)
	      {
	        // start point
	        clickTime = 1;
	        firstPosition = getMousePos(canvasHandle, evt);
	        isDragging = true;
	        changeCanvasCellColor(firstPosition,"#FFFF00");
	      }
	      else if(isDragging == true && isMousePressing==true)
	      {
	        clickTime = 2;
	        secondPosition = getMousePos(canvasHandle, evt);
	        changeCanvasCellColor(secondPosition,"#FFFF00");
	      }
	    })



	    .mouseup(function(evt){
	      isMousePressing = false;
	      // choose single cell
	      if(isDragging==false)
	      {
	        clickTime = 1;
	        firstPosition = getMousePos(canvasHandle, evt);
	        changeCanvasCellColor(firstPosition,"#FF00FF");
	        secondPosition = firstPosition;
	        clickTime = 2;
	        changeCanvasCellColor(secondPosition,"#FF00FF");


	      }
	      // choose an area
	      else if(isDragging==true)
	      {
	        isDragging = false;
	      }
	       // push the final chosen area into chosenAreaInfo
	      // get the current chosen color number
	      var paramVal = parseFloat($('#changeToValHG').val());
	      var paramName =  $('#changeParameterHG').val();
	      var updateHRU = [];
	      $.each(chosenHRU, function(i, el){
		    if($.inArray(el, updateHRU) === -1) updateHRU.push(el);
		  });
	      console.log(updateHRU);
	      chosenAreaInfo.push({paramName:paramName,paramVal:paramVal,chosenArea:updateHRU});
	      //parseInt($('input[name="vegcode-select"]:checked').val());
	      // chosenAreaInfo.push({colorNum:colorOptNum,chosenArea:chosenHRU});
	      chosenHRU=[];
	    });



        $('#applyGrid').click(function(){

        	if($.trim($('#changeToValHG').val()) == ''){
		        alert('Sorry! Some fields are empty. Please fill and try again.'); 
		        return false; 
	       }

        	
	      	// resetCanvas(vegCurrent);
		    // update map overlay
		    updateMapOverlay();

        	var inputVal = $('#changeToValHG').val();
        	var param = $('#changeParameterHG').val(); 

			var c=document.getElementById("myCanvas");
			var ctx=c.getContext("2d");
			ctx.fillStyle = "#000000"
			ctx.font="10px Georgia";

            for(var i =0; i<chosenAreaInfo.length; i++){
            	if (chosenAreaInfo[i].paramName == param && chosenAreaInfo[i].paramVal == inputVal){
                     for(var q=0; q<chosenAreaInfo[i].chosenArea.length; q++){
                     	var hru = chosenAreaInfo[i].chosenArea[q];
                     	var row = hru/96;
						var col = hru%96;
						// +3 coz of the offset
                        ctx.fillText(inputVal.toString(),3+cellWidth*col,3+cellHeight*row,cellHeight);
                     }
		      			// var hru = chosenAreaInfo[i].chosenArea[0];
		      			// var hru1 = chosenAreaInfo[i].chosenArea[chosenAreaInfo[i].chosenArea.length-1];
		      			// var row = (hru+hru1)/192;
		      			// var col = (parseInt(hru+hru1)/2)%96;
		      			// console.log('jose is panda:'+row.toString());
		      			// console.log('jose is panda1:'+col.toString());
		      			// ctx.fillText(inputVal.toString(),3+10*col,3+10*row);
            	}

            }
            updateMapOverlay();

         });

        $('#saveToFile').click(function(){
	 
	       if($.trim($('#changeToValHG').val()) == ''){
		        alert('Sorry! Some fields are empty. Please fill and try again.'); 
		        return false; 
	       }

	             
	        $.ajax({
		            type : "POST",
		            url : "/api/updateToParamFile",
		            data: JSON.stringify(
		            {
		              chosenAreaInfo: chosenAreaInfo
		            }),
		            //dataType: 'json',
		            contentType: 'application/json',
		            success: function(result) {
		                       $('#saveToFile').text("Saved");
		                       $("#saveToFile").removeClass("btn-warning");
		                       $("#saveToFile").addClass("btn-success");

		                       setTimeout(function() {
								    $('#saveToFile').text("Save To File");
								    $("#saveToFile").removeClass("btn-success");
								    $("#saveToFile").addClass("btn-warning")
								}, 2500); 
		            }
		    });
	    });
        


	   

	    $('#confirmElevationButton').click(function(){
	      changeVegByElevation(vegCurrent, elevationInfo, dataX, dataY);

	      resetCanvas(vegCurrent);

	      // update map overlay
	      updateMapOverlay();
	    });


	    $("#resetCanvasButton").click(function(){
	      resetCanvas(vegOrigin);
	      vegCurrent = vegOrigin.slice();
	      clickTime = 0;
	      chosenHRU = [];
	      chosenArea = [];

	      updateMapOverlay();
	    });

	    $("#save-veg-update").click(function(){

	      $.each(chosenAreaInfo, function(index1, value1) {
	        //var tempColor = value1.colorNum;
	        $.each(value1.chosenArea,function(index2,value2){

	          vegCurrent[value2] = value1.colorNum;

	        });
	      });

	      resetCanvas(vegCurrent);

	      // update map overlay
	      updateMapOverlay();
	    });

	    $("#submitChangetoServerButton").click(function(){
	      // update json file based on the current HRU values
	      updateJson();
	      var scenarioName = $('#scenario-name-input').val();
	      $('#patient-reminder').append("<p>Processing Request ... ...</p>");
	      $('#submitChangetoServerButton').css('visibility','hidden');
	      $.ajax({
	          type : "POST",
	          url : "/api/scenarios",
	          data: JSON.stringify(
	            {
	              veg_map_by_hru: inputJson,
	              name: scenarioName,
	              animation_url: animationURL,
	              stats_url: statsURL
	            }, null, '\t'),
	          contentType: 'application/json',
	          success: function(result) {
	  		      
	          }
	      });

	      // redirect to scenario html page
	      // call this one after 1.5 sec, need give some time for post request and then redirect
	      // coz of js asychronization, without the 1.5 sec delay, it may redirect without send out the request
	      setTimeout(function(){ window.location='/'; }, 10000);
	      //window.location='/scenario_table';
	      
	    });


	    $("#removeOverlayButton").click(function(){
	      removeOverlay();
	    });

	    $("#addOverlayButton").click(function(){
	      addOverlay();
	    });

	    $("#changeOpacityButton").click(function(){
	      changeOverlayOpacity();
	    });


	  });
	}

	// this function is used to display temperature in a line chart
	// and display factor modifier (input box) and confirm button
	function temperatureModifier(data)
	{
		var chartData=[];
		var jsonData = JSON.parse(data);
		var recordNum = jsonData['temperature_values']['tmax'].length;

		google.charts.load('current', {'packages':['corechart']});
		google.charts.setOnLoadCallback(drawChart);

		$('#step-2-title-id').empty();
		$('#step-2-title-id').append("<h5>2. Modify The Chosen Model Run Temperature</h5>");

		$('#confirmTemperatureButton').on("click", function() {







			showParamDetails();
			var inputVal = $('#temperatureModifierID').val();
			// console.log('input value is '+inputVal.toString());
			var tempCondition = $('#selTempCondition').val();
			// console.log('operation is '+tempCondition);

            
            if(tempCondition == 'Multiply by'){
            	for(var i=0; i<recordNum; i++){
            		    if(jsonData['temperature_values']['tmax'][i] != -999)
							jsonData['temperature_values']['tmax'][i] = parseFloat(jsonData['temperature_values']['tmax'][i]) * parseFloat(inputVal);
						if(jsonData['temperature_values']['tmin'][i] != -999)		
						    jsonData['temperature_values']['tmin'][i] = parseFloat(jsonData['temperature_values']['tmin'][i]) * parseFloat(inputVal);			
            	}	
			}else if(tempCondition == 'Divide by'){
				for(var i=0; i<recordNum; i++){
						if(jsonData['temperature_values']['tmax'][i] != -999)
							jsonData['temperature_values']['tmax'][i] = parseFloat(jsonData['temperature_values']['tmax'][i]) / parseFloat(inputVal);
						if(jsonData['temperature_values']['tmin'][i] != -999)		
						    jsonData['temperature_values']['tmin'][i] = parseFloat(jsonData['temperature_values']['tmin'][i]) / parseFloat(inputVal);	
            	}           
			}else if(tempCondition == 'Add by'){
				for(var i=0; i<recordNum; i++){
						if(jsonData['temperature_values']['tmax'][i] != -999)
							jsonData['temperature_values']['tmax'][i] = parseFloat(jsonData['temperature_values']['tmax'][i]) + parseFloat(inputVal);
						if(jsonData['temperature_values']['tmin'][i] != -999)		
						    jsonData['temperature_values']['tmin'][i] = parseFloat(jsonData['temperature_values']['tmin'][i]) + parseFloat(inputVal);	
            	}  				
			}else if(tempCondition == 'Subtract by'){
				for(var i=0; i<recordNum; i++){
						if(jsonData['temperature_values']['tmax'][i] != -999)
							jsonData['temperature_values']['tmax'][i] = parseFloat(jsonData['temperature_values']['tmax'][i]) + parseFloat(inputVal);
						if(jsonData['temperature_values']['tmin'][i] != -999)		
						    jsonData['temperature_values']['tmin'][i] = parseFloat(jsonData['temperature_values']['tmin'][i]) + parseFloat(inputVal);	
            	}       
			}

			// console.log('temperature modification is done, factor is '+ inputVal.toString());

			google.charts.setOnLoadCallback(drawChart);

			$.ajax({
				type : "POST",
				url : "/api/apply_modified_json_temperature",
				//not sure why data:jsonData, does not work
				data: JSON.stringify(
	            {
	              temperature_values: jsonData['temperature_values'],
	              timestep_values: jsonData['timestep_values']
	            }, null, '\t'),
				contentType: 'application/json',
				error : function() {
				  // error handler
				  console.log('temperature modification failed');
				},
				success: function() {
			    	vegeModifier();
				}
			});

		});

		function updateChartValues()
		{
			//initalize chart data
			chartData = [];
			// TODO process all the temperature value, such as tmin_2, tmin_1 ...
			chartData.push(['time','tmax','tmin']);

			if(jsonData['timestep_values'].length != recordNum)
			{
				console.log('Time and temperature array have different lengths.');
			}

			// init it with the same length of hydro
			var timeStr;
			//var splitTimeStr;
			var tempDate;
			var tempTmin;
			var tempTmax;
			


			// if we have too many elements, we will sampling temperature
			if(recordNum >= 1000)
			{
				for(var i=1; i<recordNum; i=i+20)
				{
					tempTmax = jsonData['temperature_values']['tmax'][i];
					tempTmin = jsonData['temperature_values']['tmin'][i];


					timeStr = jsonData['timestep_values'][i];
					//
					//splitTimeStr = timeStr.split(' ');
					tempDate = new Date(timeStr);

					chartData.push([tempDate,tempTmax,tempTmin]);
				}
			}
			else
			{
				for(var i=0; i<recordNum; i++)
				{
					tempTmax = jsonData['temperature_values']['tmax'][i];
					tempTmin = jsonData['temperature_values']['tmin'][i];

					timeStr = jsonData['timestep_values'][i];
					//
					//splitTimeStr = timeStr.split(' ');
					tempDate = new Date(timeStr);

					chartData.push([tempDate,tempTmax,tempTmin]);		
				}
			}
		}

		function drawChart() 
		{
			updateChartValues();

			var options = {
	          title: 'Temperature',
	          curveType: 'function',
	          legend: { position: 'bottom' }
	        };

			var chart = new google.visualization.LineChart(document.getElementById('temperature-line-chart-id'));

			var lineChartData = google.visualization.arrayToDataTable(chartData);

			chart.draw(lineChartData, options);
		}
	}

	function displayModelModifier()
	{
	  // get temperature info
	  // no model run, so use default
	  if(itemCount == 0)
	  {
	  	$.get('/api/get_default_temperature', function(data){
	  		$('#step-2-dive-id').css('visibility','visible');
	  		temperatureModifier(data);
	  	});
	  }
	  else
	  {
	  	$.get('/api/get_temperature', function(data){
	  		$('#step-2-dive-id').css('visibility','visible');
	  		temperatureModifier(data);
	  	});

	  }
	  // get vegetation info
	  
	}


  // this is used to find the length of an obj
  // this is from http://stackoverflow.com/questions/5223/length-of-a-javascript-object-that-is-associative-array
  Object.size = function(obj) {
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
  };

  // this function is used to change json based on vegCurrent
  function updateJson()
  {
    var hruNum;
    var vegType;
    var objSize = Object.size(inputJson['vegetation_map']);
    // this for loop is for initialize the JSON HRU part
    for(var i=0; i<objSize; i++)
    {
      inputJson['vegetation_map'][i.toString()]['HRU_number'] = [];
    }

    // modify JSON HRU part
    for(var m=0 ; m<dataY ; m++)
      {
        for(var i=0 ; i<dataX ; i++)
        {
          hruNum = i + m*dataX;
          vegCode = vegCurrent[hruNum];
          vegType = vegCodeLookup[vegCode];
          inputJson[vegType].push(hruNum);
        }
      }
  
  }


  // this function grab data json input and create a 1D array of hru values
  function obtainJsoninto1D(inputJson)
  {
    var totalHRUNum = 0;

    var outputArr = new Array(dataX*dataY);
    // for this case veg_code is the loop count (from 0), vegCode is str
    // therefore veg_code = i.toString()
    var tempSize;
    $.each(['bare_ground', 'grasses', 'shrubs', 'trees', 'conifers'],
      function(i, cov_type) {
        tempSize = inputJson[cov_type].length;

        totalHRUNum = totalHRUNum + tempSize;

        for(var m=0; m<tempSize; m++ )
        {
          outputArr[inputJson[cov_type][m]] = i;
        }
      }
    );

    // test if the inputJson is valid
    if(totalHRUNum == dataX*dataY)
    {
      return outputArr;  
    }
    else
    {
      console.log('Data from the get request is not right.');
      console.log('HRU number is not consistent.');
      return [];
    }

  }

  // this is from http://www.html5canvastutorials.com/advanced/html5-canvas-mouse-coordinates/
  // get the mouse position, based on px
  function getMousePos(canvas, evt)
  {
    var rect = canvas.getBoundingClientRect();
    return {
      x: evt.clientX - rect.left,
      y: evt.clientY - rect.top
    };
  }

  // this function is used to refresh canvas with the original veg code
  function resetCanvas(colorMatrix)
  {
      for(var m=0 ; m<dataY ; m++)
      {
        for(var i=0 ; i<dataX ; i++)
        {
          canvas2DContext.fillStyle = colorScale[colorMatrix[i+dataX*m]];
          //                          start x,     y,            width,    height
          canvas2DContext.fillRect(cellWidth*i,cellHeight*m,cellWidth,cellHeight);
          // draw lines to separate cell
          canvas2DContext.rect(cellWidth*i,cellHeight*m,cellWidth,cellHeight);
        }
      }
    
      canvas2DContext.stroke();
  }

  // this function requires top left and bot right points for the chosen area
  function showChosenRecArea(input1,input2)
  {
    var p1 = {x:input1.x,y:input1.y};
    var p2 = {x:input2.x,y:input2.y};
    var temp;
    canvas2DContext.fillStyle = "#FFFF00";
    // not the same point
    if(p2.x!=p1.x&&p2.y!=p1.y)
    {
      if(p2.x < p1.x)
      {
        temp = p2.x;
        p2.x = p1.x;
        p1.x = temp;
      }
      if(p2.y < p1.y)
      {
        temp = p2.y;
        p2.y = p1.y;
        p1.y = temp;
      }
      // Here +1 coz need to count the bottom line too
      canvas2DContext.fillRect(p1.x*cellWidth, p1.y*cellHeight, cellWidth*(p2.x-p1.x+1), cellHeight*(p2.y-p1.y+1));
    }
    // two points in the same column
    else if(p2.x==p1.x&&p2.y!=p1.y)
    {
      if(p2.y < p1.y)
      {
        temp = p2.y;
        p2.y = p1.y;
        p1.y = temp;
      }
      // Here +1 coz need to count the bottom line too
      canvas2DContext.fillRect(p1.x*cellWidth, p1.y*cellHeight, cellWidth, cellHeight*(p2.y-p1.y+1));
    }
    // two points in the same row
    else if(p2.x!=p1.x&&p2.y==p1.y)
    {
      if(p2.x < p1.x)
      {
        temp = p2.x;
        p2.x = p1.x;
        p1.x = temp;
      }
      // Here +1 coz need to count the bottom line too
      canvas2DContext.fillRect(p1.x*cellWidth, p1.y*cellHeight, cellWidth*(p2.x-p1.x+1), cellHeight);
    }
    // choose the single cell
    else if(p2.x==p1.x&&p2.y==p1.y)
    {
      canvas2DContext.fillRect(p1.x*cellWidth, p1.y*cellHeight, cellWidth, cellHeight);
    }
    // push chosen HRU cell num
    recordChosenAreaInfo(p1,p2);

  }

  // this function is used to add the chosen cell number into chosenHRU
  // for this function p1.x and p1.y should be =< p2.x and p2.y
  // after this function chosenHRU may have some duplicated elements
  function recordChosenAreaInfo(p1,p2)
  {
    // get the current chosen color number
    // var colorOptNum =
    //       parseInt($('input[name="vegcode-select"]:checked').val());

    // single point
    if(p1.x==p2.x && p1.y==p2.y)
    {
      chosenHRU.push(p1.x+p2.y*dataX);
    }
    else
    {
      for(var m=p1.y; m<=p2.y; m++)
      {
        for(var i=p1.x; i<=p2.x; i++)
        {
          chosenHRU.push(i+m*dataX);
        }
      }
    }
	
  }

  function changeCanvasCellColor(mousePosition,color)
  {
    var startX = Math.floor(mousePosition.x/cellWidth);
    var startY = Math.floor(mousePosition.y/cellHeight);
    canvas2DContext.fillStyle = color;
    canvas2DContext.fillRect(startX*cellWidth, startY*cellHeight, cellWidth, cellHeight);

    if(clickTime == 1)
    {
      firstPoint.x = startX;
      firstPoint.y = startY;
    }
    else if(clickTime == 2)
    {
      secondPoint.x = startX;
      secondPoint.y = startY;

      showChosenRecArea(firstPoint,secondPoint);

    }

  }

  Array.prototype.max = function() {
    return Math.max.apply(null, this);
  };

  Array.prototype.min = function() {
    return Math.min.apply(null, this);
  };

  function changeVegByElevation(inputHRU, inputElevationInfo, inputArrX, inputArrY)
  {
    var hruNum = 0;
    var elevationThreshold = $('#elevationSelectorID').val();
    // get the current chosen color number
    var colorOptNum = parseInt($('#vegetation-type-selector label.active input').val());

    for(var m=0 ; m<inputArrY ; m++)
    {
      for(var i=0 ; i<inputArrX ; i++)
      {
        hruNum = i + m*dataX;
        if(inputElevationInfo[hruNum] >= elevationThreshold)
        {
          inputHRU[hruNum] = colorOptNum;
        }
      }
    }
  
  }





});


