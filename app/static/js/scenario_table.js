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
	            url: '/api/scenarios/metadata',
	            dataType: 'json',
	            cache: false,
	            success: function(data) {
	                this.setState({data: data});
	                //console.log(data.length);
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

	        var downloadHydroAsCSV = function(tempScenario) {
	        	var downloadURL = '/api/return_hydro_info/' + tempScenario._id.$oid; 
	        	window.open(downloadURL);
	        }

	        var visAnimation = function(tempScenario) {
	        	var animationURL = "/api/netCDF_url/" + tempScenario._id.$oid;
	        	window.open(animationURL, 'newwindow', 'width=900,height=1100');
	        }

	        var visStats = function(tempScenario) {
	        	var statsURL = "/api/netCDF_stat_url/" + tempScenario._id.$oid;
	        	window.open(statsURL, 'newwindow', 'width=900,height=1100');
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
	                           scenario.time_finished != "None" ?
	                           scenario.time_finished :
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
	                        <a onClick={downloadHydroAsCSV.bind(this,scenario)}>
	                          Download Hydrograph as a CSV File
	                        </a>
	                      </div>
	                    </td>

	                    <td className="download-link">
	                        <a onClick={visAnimation.bind(this,scenario)}>
	                          Visualize Animation File
	                        </a>
	                    </td>

	                    <td className="download-link">
	                        <a onClick={visStats.bind(this,scenario)}>
	                          Visualize Stats File
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

	        var scenarioList =
	            <div className="scenarioList">
	                <table className="table table-striped">
	                    <thead>
	                        <tr>
	                            <td><strong>Scenario Name</strong></td>
	                            <td><strong>Time Finished</strong></td>
	                            <td className="download-link"><strong>View Hydrograph</strong></td>
	                            <td className="download-link"><strong>Download Hydrograph CSV File</strong></td>
	                            <td className="download-link"><strong>Visualize Animation File</strong></td>
	                            <td className="download-link"><strong>Visualize Stats File</strong></td>
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


