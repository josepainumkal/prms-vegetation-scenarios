$(document).ready(function(){
  var scenarioID = $('#scenario_id').text();
  var timeArr;
  var paramList;
  $.get('/api/netCDF_stat_basic_data/'+scenarioID, function(data){
    var receivedJSON = JSON.parse(data);
    timeArr = receivedJSON['time'];
    paramList = receivedJSON['param_data'];
  });

});
