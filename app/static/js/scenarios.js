/**
 Module for the scenario upload and insert page of the vw-webapp

 Author: Matthew A. Turner
 Date: Feb 23, 2016
**/


/**
 * Box that contains the scenario list
 */
var ScenarioListBox = React.createClass({

    loadScenariosFromServer: function() {
        $.ajax({
            url: '/api/scenarios',
            dataType: 'json',
            cache: false,
            success: function(data) {
                this.setState({data: data});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
    },

    getInitialState: function() {
        return {
            data: {scenarios: []}
        };
    },

    componentDidMount: function() {
        this.loadScenariosFromServer();
        setInterval(this.loadScenariosFromServer, this.props.pollInterval);
    },

    render: function() {
        return (
            <div className="scenarioBox">
                <ScenarioList data={this.state.data} />
            </div>
        )
    }
});


/**
 * Scenario list contained within the box
 */
var ScenarioList = React.createClass({

    render: function() {

        var displayHydrograph = function(tempScenario) {
            var hydrographURL = '/hydrograph_vis/'+tempScenario._id.$oid;
            window.open(hydrographURL, 'newwindow', 'width=900,height=1200');
        }

        var deleteScenario = function(sc) {
          $.ajax({
              method: 'DELETE',
              url: '/api/scenarios/' + sc._id.$oid
          });
        }
        // <!-- not sure why cannot find time recieved var-->
        // <!-- <td>{new Date(scenario.time_received.$date).toISOString().slice(0,19)}</td>-->
        var tableRows = this.props.data.scenarios.map(function(scenario) {
            return (
                <tr key={scenario._id.$oid}>
                    <td>{scenario.name}</td>

                    <td>{
                           scenario.time_finished ?
                           new Date(scenario.time_finished.$date).toISOString().slice(0,19) :
                           "Pending"
                        }
                    </td>
                    <td>
                        <a href={scenario.inputs ? scenario.inputs.parameter : '#'}>
                            Download Input Parameters
                        </a>
                    </td>
                    <td>
                    <a href={scenario.outputs ? scenario.outputs.statsvar : '#'}>
                            Download Output Data
                        </a>
                    </td>
                    <td className="download-link">
                        <a onClick={displayHydrograph.bind(this,scenario)}>
                          View Hydrograph
                        </a>
                    </td>
                    <td>
                      <div className="delete-scenario" id={"delete-"+scenario._id.$oid}>
                        <span className="glyphicon glyphicon-trash"
                              onClick={deleteScenario.bind(this, scenario)}>
                        </span>
                      </div>
                    </td>
                </tr>
            );
        });

        //<!--//<td><strong>Time Received</strong></td>-->
        var scenarioList =
            <div className="scenarioList">
                <table className="table table-striped">
                    <thead>
                        <tr>
                            <td><strong>Scenario Name</strong></td>
                            <td><strong>Time Finished</strong></td>
                            <td><strong>Download Inputs</strong></td>
                            <td><strong>Download Outputs</strong></td>
                            <td className="download-link"><strong>View Hydrograph</strong></td>
                            <td><strong>Delete Scenario</strong></td>
                        </tr>
                    </thead>
                    <tbody>
                        {tableRows}
                    </tbody>
                </table>
            </div>

        return (
            <div className="scenarioList">
                {scenarioList}
            </div>
        );
    }
});


window.ScenarioListBox = ScenarioListBox;

/**
    Handle Form Submit; React would be overkill, but I do want to prevent
    page reloads for better UX.
**/
var vegChangeIdx = 0;
$('#save-veg-update').click(function(e) {
  e.preventDefault();

  $('#veg-update-list')
      .append('<h4 id="veg-change-' + vegChangeIdx + '">'
                  + 'Yeah added a change to the veg map' +
                      '  <a class="remove-veg-update">x</a>' +
              '</h4>'
      );

  vegChangeIdx++;
});

$('#veg-update-list').on('click', 'a.remove-veg-update', function(e) {
  $(e.toElement.parentElement).remove();
});

$('.delete-scenario').click(function(e) {
  var scenarioId = e.attr('id').replace('delete-', '');
  debugger;
  $.ajax({
      type: 'DELETE',
      url: '/api/scenarios/' + scenarioId
  });
});
