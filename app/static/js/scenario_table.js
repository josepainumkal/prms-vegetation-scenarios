$(document).ready(function(){
	$('#createScenarioButton').click(function(){
	  window.location='/create_new_scenario';
	});

	/**
	 modified from Matthew's scenarios.js
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
	            window.open(hydrographURL, 'newwindow', 'width=900,height=1100');
	        }

	        var deleteScenario = function(sc) {
	          $.ajax({
	              method: 'DELETE',
	              url: '/api/scenarios/' + sc._id.$oid
	          });
	        }

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

	                    <td className="download-link">
	                        <a onClick={displayHydrograph.bind(this,scenario)}>
	                          View Hydrograph
	                        </a>
	                    </td>

	                    <td>
	                      <div className="download-link">
	                        <a>
	                          Check Details
	                        </a>
	                      </div>
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

	        var scenarioList =
	            <div className="scenarioList">
	                <table className="table table-striped">
	                    <thead>
	                        <tr>
	                            <td><strong>Scenario Name</strong></td>
	                            <td><strong>Time Finished</strong></td>
	                            <td className="download-link"><strong>View Hydrograph</strong></td>
	                            <td className="download-link"><strong>Display Scenario Resources & Modified Veg</strong></td>
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


	$('.delete-scenario').click(function(e) {
	  var scenarioId = e.attr('id').replace('delete-', '');
	  debugger;
	  $.ajax({
	      type: 'DELETE',
	      url: '/api/scenarios/' + scenarioId
	  });
	});
});


