$(document).ready(function(){
  // not sure why this (get scenario id) does not work
  // var scenarioID = $('#scenario_id').text();
  var currentURL = window.location.href.split('/');
  var scenarioID = currentURL[currentURL.length-1]; 
  var timeArr;
  var paramList;
  var paramDataArrLen;

  // line chart part
  google.charts.load('current', {'packages':['corechart']});
  
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
      $.get('/api/netCDF_stat_data/'+scenarioID+'/'+$('#paramSelectBoxID').val(),function(paramData){
        var receivedParamJson = JSON.parse(paramData);
        var paramDataArr = receivedParamJson['param_data'];
        paramDataArrLen = paramDataArr.length;
        // initialize
        lineChartData = [];

        lineChartName.push($('#paramSelectBoxID').val());
        lineChartData.push(lineChartName);

        for(var i=0; i<paramDataArrLen; i++)
        {
          lineChartData.push([parseFloat(timeArr[i]),parseFloat(paramDataArr[i])]);
        }
        // create checkbox for 
        for(var i=0; i<nameListLen; i++)
        {
          if(paramList[i] != $('#paramSelectBoxID').val())
          {
            $('#checkBoxDivID').append("<label class='checkbox-inline'><input type='checkbox' id='"+paramList[i]+"' value='"+paramList[i]+"'>"+paramList[i]+"</label>"); 
          }
        }
        google.charts.setOnLoadCallback(drawChart);
      });
    });
    
  });
  // $(document).on('change','[type=checkbox]',function(){
  $(document).on('change','[type=checkbox]',function(){
    var checkboxID = this.value;
    if($("#"+checkboxID).prop("checked"))
    {
      $.get('/api/netCDF_stat_data/'+scenarioID+'/'+checkboxID,function(chosenParamData){
        var chosenParamJSON = JSON.parse(chosenParamData);
        var chosenParamDataArr = chosenParamJSON['param_data'];
        lineChartName.push(checkboxID);
        for(var i=0; i<paramDataArrLen; i++)
        {
          var tempArr = lineChartData[i+1];
          tempArr.push(parseFloat(chosenParamDataArr[i]));
          lineChartData[i+1] = tempArr;
        }
        google.charts.setOnLoadCallback(drawChart);
      });
    }
    // else remove it
    else
    {
      var chosenParamIndex = lineChartName.indexOf(checkboxID);
      // remove element based on the index
      lineChartName.splice(chosenParamIndex,1);
      for(var i=0; i<paramDataArrLen; i++)
      {
        var tempArr = lineChartData[i+1];
        tempArr.splice(chosenParamIndex,1);
        lineChartData[i+1] = tempArr;
      }
      google.charts.setOnLoadCallback(drawChart);
    }

    
  });

  function drawChart() {
    var data = google.visualization.arrayToDataTable(lineChartData);

    var options = {
      title: 'Stats data',
      curveType: 'function',
      legend: { position: 'bottom' }
    };

    //var chart = new google.visualization.LineChart($('#lineChartDivID'));
    var chart = new google.visualization.LineChart(document.getElementById('lineChartDivID'));

    chart.draw(data, options);
  }


});
