$(document).ready(function(){
  // TODO this part should be done byusing get request
  // get the color from get request from the server
  var inputJson;

  // set up the canvas size
  var cellWidth = 10;
  var cellHeight = 10;

  // canvas col and row num
  var dataX;
  var dataY;
  // original fire code
  var fireOrigin;
  // current fire code
  var fireCurrent;
  // elevation information for all HRU cells
  var elevationInfo;

  var canvasWidth;
  var canvasHeight;
  var canvasHandle;
  var canvas2DContext;

  // this is for define color for the cells
  var colorScale;

  // define google map with map
  var map;
  // this is for image overlay
  var imgOverlay;
  var imageBounds;
  // url for overlay image
  var imgURL;
  // map center
  var center;

  // this is for mouse dragging
  var isDragging = false;
  var isMousePressing = false;
  var firstPosition;
  var secondPosition;

  var currentTime = 0;

  var backgroundMap = new Image();
  var canvasSize = [];

  var paramMin;
  var paramMax;

  var chosenParam;
  var currentLoadFrameNum = 0;
  var frameBuffer = [];
  var frameJSON;
  var totalFrameNum;

  var setIntervalID;
  var frameStep;

  var currentFrameNum;

  var scenarioID = $('#scenarioIDParagraph').text();
  
  $('#confirmParamButtonID').on("click", function() {
      chosenParam = $( "#paramSelectBoxID" ).val();
      var metadataURL = '/api/get_chosen_metadata/'+chosenParam+'/'+scenarioID;
      // init frame with the first 10 frames
      var frameURL = '/api/get_chosen_data_by_frame/'+chosenParam+'/0/9/'+scenarioID;
      frameStep = 10;
      frameBuffer = [];
      currentFrameNum = 0;
      // console.log(metadataURL);
      // console.log(frameURL);
      $.get(metadataURL, function(metadata){
        // test if it is json
        var metadataJSON = JSON.parse(metadata);
        totalFrameNum = parseFloat(metadataJSON['total_num']);
        paramMax = parseFloat(metadataJSON['param_max']);
        paramMin = parseFloat(metadataJSON['param_min']);
        var scaleSize = Math.floor(paramMax-paramMin)+1;
        colorScale = chroma.scale(['blue','red']).colors(scaleSize);

        dataX = metadataJSON['col_num'];
        dataY = metadataJSON['row_num'];

        canvasWidth = cellWidth*dataX;
        canvasHeight = cellHeight*dataY;

        // add legend squares here
        $('.legendCanvas').attr('width',canvasWidth.toString()+'px');
        $('.legendCanvas').attr('height',cellHeight);
        var tempCanvasHandle = document.getElementById("legendCanvas");
        var tempCanvas2DContext = tempCanvasHandle.getContext("2d");
        for(var i=0; i<dataX; i++)
        {
          tempCanvas2DContext.fillStyle = colorScale[parseInt(scaleSize*i/dataX)];
          tempCanvas2DContext.fillRect(cellWidth*i,0,cellWidth,cellHeight);
          tempCanvas2DContext.rect(cellWidth*i,cellHeight,cellWidth,cellHeight);
        }
        tempCanvas2DContext.stroke();

        $('#legendExplainID').append('min (all the frames) is: '+paramMin.toString()+'; max (all the frames) is: '+paramMax.toString());


        $('.mapCanvas').attr('width',canvasWidth.toString()+'px');
        $('.mapCanvas').attr('height',canvasHeight.toString()+'px');

        canvasHandle = document.getElementById("myCanvas");
        canvas2DContext = canvasHandle.getContext("2d");
        // initial frameJson
        $.get(frameURL, function(frameData){
          frameJSON = JSON.parse(frameData);
          // combine two arrays
          frameBuffer = frameBuffer.concat(frameJSON['param_data']);
          // .shift get the array first element and remove it
          if(frameBuffer.length != 0)
          {
            updateCanvas(frameBuffer.shift());
          }

        });

        $('#nextFrameID').on("click", function() {
            if(frameBuffer.length != 0)
            {
              updateCanvas(frameBuffer.shift());
            }
        });

        // keep pushing more frames into var frameJSON buffer
        $('#playFrameID').on("click", function() {
          // every 1 sec update frame
          setIntervalID = setInterval(updateNextFrame, 1000);

          $('#stopFrameID').on("click", function() {
            clearInterval(setIntervalID);
          });
          
        });

      });
  });

  
  function updateNextFrame()
  {
    if(totalFrameNum>(currentLoadFrameNum+frameStep))
    {
      var frameURL;
      currentLoadFrameNum = currentLoadFrameNum + frameStep;
      if(totalFrameNum>(currentLoadFrameNum+frameStep))
      {
        frameURL = '/api/get_chosen_data_by_frame/'+chosenParam+'/'+currentLoadFrameNum.toString()+'/'+(currentLoadFrameNum+frameStep).toString()+'/'+scenarioID;
      }
      else
      {
        frameURL = '/api/get_chosen_data_by_frame/'+chosenParam+'/'+currentLoadFrameNum.toString()+'/'+totalFrameNum.toString()+'/'+scenarioID;  
      }
      
      $.get(frameURL, function(frameData){
        frameJSON = JSON.parse(frameData);
        frameBuffer = frameBuffer.concat(frameJSON['param_data']);
        //frameBuffer.push(frameJSON['param_data']);
      });
    }
    
    // check if buffer array is empty
    if(frameBuffer.length != 0)
    {
      updateCanvas(frameBuffer.shift());
    }
  }


  function setupBackgroundMap()
  {
    // backgroundMap.onload = function(){
    //   canvas2DContext.globalAlpha = 1.0;
    //   canvas2DContext.drawImage(backgroundMap, 0, 0);
    // }
    
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


  // this function is used to update canvas (fire cell) with the current fire code
  function updateCanvas(input2DArray)
  {
      $( "#frameParagraphID" ).text('This is day '+currentFrameNum.toString());
      currentFrameNum = currentFrameNum + 1;
      //canvas2DContext.globalAlpha = 0.5;

      for(var m=0 ; m<dataY ; m++)
      {
        for(var i=0 ; i<dataX ; i++)
        {

          canvas2DContext.fillStyle = colorScale[Math.floor(input2DArray[m][i]-paramMin)+1];
          //                          start x,     y,            width,    height
          canvas2DContext.fillRect(cellWidth*i,cellHeight*m,cellWidth,cellHeight);
          // draw lines to separate cell
          canvas2DContext.rect(cellWidth*i,cellHeight*m,cellWidth,cellHeight);
          
        }
      }
      canvas2DContext.stroke();
      // currentTime = currentTime + 1;

      // setupBackgroundMap();

  }


  Array.prototype.max = function() {
    return Math.max.apply(null, this);
  };

  Array.prototype.min = function() {
    return Math.min.apply(null, this);
  };



});
