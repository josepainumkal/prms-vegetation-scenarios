$(document).ready(function(){
	$.get('/api/scenarios/finished_modelruns', function(data){
		var temp = jQuery.parseJSON(data);
		for(var i=0; i<temp.length; i++)
		{
			$('#scenario-list').append("<p>"+temp[i]['id'].toString()+"</p>");
		}
	});
});