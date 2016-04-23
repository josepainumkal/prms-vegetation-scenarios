$(document).ready(function(){

	var access_token;
	var modelRunServer;

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
		var itemCount = data.num_results;
		for(var i=0; i<itemCount; i++)
		{
			var tempItem = data.objects[i];
			$('#model-run-items').append("<tr key="+tempItem.id.toString()+">" +
											 "<td>"+tempItem.id.toString()+"</td>" +
											 "<td>"+tempItem.created_at+"</td>" +
											 // the button id is modelrunID
											 "<td><button class='modelRunChosenButton' id='"+tempItem.id.toString()+"' >Choose Me</button>"+"</td>" +
										 "</tr>");
		}
	}

	// $('.modelRunChosenButton').click will not work
	// should use the following method
    $(document).on("click", ".modelRunChosenButton" , function() {
    	// get the current button id
    	var modelRunID = $(this).attr('id');
    	$('#step-2-title-id').empty();
    	$('#step-2-title-id').append("<h5>2. Modify The Chosen Model Run</h5>");
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
	});

	function importChosenModelRun(data)
	{
		// initalize step 2 div
		$('#step-2-content-id').empty();

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
		}

		var jsonStr =	'{ "model_run" : [' +
							'{ "control_url":"'+controlURL+'" , "data_url":"'+dataURL+'", "param_url":"'+paramURL+'" }' +
						']}';
		var metaJSON = JSON.parse(jsonStr);

		// send the meta data to server to download the files
        $.ajax({
		    type : "POST",
		    url : "/api/scenarios/download_input_files",
		    //data: JSON.stringify(inputJson, null, '\t'),
		    data: jsonStr,
		  	contentType: 'application/json',
		    success: function(result) {
		    }
		});


	}



});


