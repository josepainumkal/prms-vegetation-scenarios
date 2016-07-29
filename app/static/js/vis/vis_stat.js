$(document).ready(function(){
  // not sure why this (get scenario id) does not work
  // var scenarioID = $('#scenario_id').text();
  var currentURL = window.location.href.split('/');
  var scenarioID = currentURL[currentURL.length-1]; 
  var timeArr;
  var paramList;

  // line chart part
  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawChart);
  var lineChartData = [];
  var lineChartName = ['Time'];

  $.get('/api/netCDF_stat_basic_data/'+scenarioID, function(data){
    var receivedJSON = JSON.parse(data);
    timeArr = receivedJSON['time'];
    paramList = receivedJSON['param_data'];
    var nameListLen = paramList.length;
    for(var i=0; i<nameListLen; i++)
    {
      $('#paramSelectBoxID').append('<option value='+paramList[i]+'>'+paramList[i]+'</option>'); 
    }

    $('#confirmParamButtonID').on('click',function(){
      $.get('/api/netCDF_stat_data/'+scenarioID+'/'+$('paramSelectBoxID').val(),function(paramData){
        var receivedParamJson = JSON.parse(paramData);
        var paramDataArr = receivedParamJson['param_data'];
        lineChartName.append($('paramSelectBoxID').val());
        lineChartData.append(lineChartName);

        for(var i=0; i<nameListLen; i++)
        {
          lineChartData.append([timeArr[i],paramData[i]]);
        }

      });
    });
    
  });

  function drawChart() {
    var data = google.visualization.arrayToDataTable([lineChartData]);

    var options = {
      title: 'Stats data',
      curveType: 'function',
      legend: { position: 'bottom' }
    };

    var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

    chart.draw(data, options);
  }


});
