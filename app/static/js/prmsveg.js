
// var template0;

$(function(){
   $(".onlyNumeric").ForceNumericOnly();
   var currentCount = $('.repeat-parameter').length;
    $('#totalParams').val(currentCount);
   if(currentCount ==1){
   	   $('#deleteParam').hide();
   	   // template0 = $('.repeat-parameter').first();
   }
   //showParamDetails();

     //on tab change
      $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
              var target = $(e.target).attr("href") // activated tab
              var chosenParamVal;

              if(target == "#hruFromGrid"){
                  chosenParamVal = $('#changeParameterHG').val();
              }else{
                  chosenParamVal = $('#changeParameter').val();
              }
              
              if(chosenParamVal!=null){
                showParamDetailsAjax(chosenParamVal);
              }
      });
});

function forceNumeric() {
     $(".onlyNumeric").ForceNumericOnly();
}


function showParamDetailsAjax(chosenParamVal){

  $.ajax({
            type : "GET",
            url : "/api/get-chosen-parameter-details",
            data:{
              chosenParam: chosenParamVal
            },
            dataType: 'json',
            contentType: 'application/json',
            success: function(result) {
              
               if($('#hruFromParam').attr('class').indexOf('active') == -1){
                    $('#pNameHG').text(result.chosenParam_name)
                    $('#pDescHG').text(result.layer_desc)
                    $('#pMinHG').text(result.chosenParam_minVal)
                    $('#pMaxHG').text(result.chosenParam_maxVal)
               }else{
                    $('#pName').text(result.chosenParam_name)
                    $('#pDesc').text(result.layer_desc)
                    $('#pMin').text(result.chosenParam_minVal)
                    $('#pMax').text(result.chosenParam_maxVal)
               }
            }
         });

}

function showParamDetails(){ 
     var chosenParamVal;
     if($('#hruFromParam').attr('class').indexOf('active') == -1){
          chosenParamVal = $('#changeParameterHG').val();
     }else{
          chosenParamVal = $('#changeParameter').val();
     }
    //chosenParamVal = $('#changeParameterHG').val();
    if(chosenParamVal!=null){
        showParamDetailsAjax(chosenParamVal)
    }
}

$(document).on('click', '#addParam', function () {

   var currentCount = $('.repeat-parameter').length;
   var newCount = currentCount + 1;
   var lastRepeatingGroup = $('.repeat-parameter').last();
   var template = $('.repeat-parameter').first();
   // var template = template0;
   var newSection = template.clone();

   newSection.attr('id',newCount);
   newSection.find(".highValue").remove();
  
   newSection.insertAfter(lastRepeatingGroup).hide().slideDown(250);

   newSection.find("select").each(function (index, input) {
        var i = $(this).attr('id');
        $(this).attr('id', i.split('1')[0] + newCount);
        $(this).attr('name', i.split('1')[0] + newCount);
   });

   newSection.find("input").each(function (index, input) {
        var i = $(this).attr('id');
        $(this).attr('id', i.split('1')[0] + newCount);
        $(this).attr('name', i.split('1')[0] + newCount);
   });


   if(newCount >1){
   	   $('#deleteParam').show();
   }
   $('#totalParams').val(newCount);
   return false;
});


$(document).on('click', '#deleteParam', function () {
   var currentCount = $('.repeat-parameter').length;
   if(currentCount !=1){
		var lastRepeatingGroup = $('.repeat-parameter').last();
   		lastRepeatingGroup.remove();
   }
   var currentCount = $('.repeat-parameter').length;
   $('#totalParams').val(currentCount);
   if (currentCount==1){
   	   $('#deleteParam').hide();
   }
   return false;
});

$(document).on('change', 'select[class="form-control sel_cond"]', function () {
	//var i = $(this).attr('id');
    var rowCount = $(this).parent().parent().attr("id");
    var selectValue = $(this).val();

    if(selectValue =='between'){

          // $(this).parent().after(newSection);
          var lastRepeatingGroup =$(this).parent().parent().children().last();

          if( lastRepeatingGroup.attr('class').indexOf('highValue') == -1){

          	  var template = $(this).parent().parent().children().last();
		          var newSection = template.clone();
		          newSection.insertAfter(lastRepeatingGroup).addClass('col-xs-3 highValue');

                  var lastChild =$(this).parent().parent().children().last();

                  lastChild.find("input").each(function (index, input) {
                  //  var i = $(this).attr('id');
                      // if(rowCount ==1){
                      //   $(this).attr('id', 'h1');
                      //    $(this).attr('name', 'h1');
                      // }else{
                        $(this).attr('id', 'h'+rowCount); 
                        $(this).attr('name', 'h'+rowCount); 
                      //}    
                  });
            }
    }
    else{
        var lastRepeatingGroup =$(this).parent().parent().children().last();
        if( lastRepeatingGroup.attr('class').indexOf('highValue') != -1){
      	    lastRepeatingGroup.remove();
        }
    }

         
});




$(document).on('change', 'select[class="form-control show-list-param"]', function () {
      showParamDetails();
  });






$(document).on('click', '#submitParams', function () {

      var flag = true;
      var template = $('#hruFromParam');
      template.find("input").each(function (index, input) {
          if(!$(this).val()){
               flag = false;
           }
       });
 
      if (flag == false){
        alert('Sorry! Some fields are empty. Please fill and try again.'); 
        return false; 
      }
         

      // var data =  $("#mform").serialize();
       var currentCount = $('.repeat-parameter').length;
       var changeParam = $('#changeParameter').val();
       var changeToVal = $('#changeToVal').val();
       var paramList = []

       for(i=1;i<=currentCount;i++){
           selectParameter = $("#selectParameter"+i).val();
           selectCondition = $("#selectCondition"+i).val();
           l = $("#l"+i).val();
           h = $("#h"+i).val();
           var obj = new Object;
           obj.paramName = selectParameter
           obj.lowLimit = l
           obj.highLimit = h
           obj.condition = selectCondition
           paramList.push(obj)
       } 

        $.ajax({
            type : "POST",
            url : "/api/prmsparam_submit",
            data: JSON.stringify(
            {
              changeParam: changeParam,
              changeToVal: changeToVal,
              paramList:paramList
            }),
            dataType: 'json',
            contentType: 'application/json',
            success: function(result) {
               // var tempJSON = JSON.parse(result);
                var paramName = result.param_name;
                var modified_handle = result.modified_handle;
                var param_min = result.param_min
                var param_max = result.param_max
                var scaleSize = Math.floor(param_max-param_min)+1;
                colorScale = chroma.scale(['blue','red']).colors(scaleSize);


                var cellWidth = 12;
                var cellHeight = 12;
                var dataX = 96;
                var dataY = 49;
                canvasWidth = cellWidth*dataX;
                canvasHeight = cellHeight*dataY;

                $('.mapCanvas').attr('width',canvasWidth.toString()+'px');
                $('.mapCanvas').attr('height',canvasHeight.toString()+'px');
                canvasHandle = document.getElementById("myCanvas");
                canvas2DContext = canvasHandle.getContext("2d");

               
                // updateCanvas(frameBuffer.shift(), dataX, dataY, cellHeight, cellWidth, colorScale,param_min);
                input2DArray = modified_handle;
                for(var m=0 ; m<dataY ; m++)
                {
                    for(var i=0 ; i<dataX ; i++)
                    {

                      canvas2DContext.fillStyle = colorScale[Math.floor(input2DArray[m][i]-param_min)];
                      //                          start x,     y,            width,    height
                      canvas2DContext.fillRect(cellWidth*i,cellHeight*m,cellWidth,cellHeight);
                      // draw lines to separate cell
                      canvas2DContext.rect(cellWidth*i,cellHeight*m,cellWidth,cellHeight);
                      
                    }
                }
                canvas2DContext.stroke();
            
                updateMapOverlay();

              
                // $('#outText').val(tempJSON['name']+' will hold a '+tempJSON['event']);
                // $('#outText').val();
            }
         });
});


jQuery.fn.ForceNumericOnly = function()
{
    return this.each(function()
    {
        $(this).keydown(function(e)
        {
            var key = e.charCode || e.keyCode || 0;
            // allow backspace, tab, delete, enter, arrows, numbers and keypad numbers ONLY
            // home, end, period, and numpad decimal
            return (
                key == 8 || 
                key == 9 ||
                key == 13 ||
                key == 46 ||
                key == 110 ||
                key == 190 ||
                (key >= 35 && key <= 40) ||
                (key >= 48 && key <= 57) ||
                (key >= 96 && key <= 105));
        });
    });
};
