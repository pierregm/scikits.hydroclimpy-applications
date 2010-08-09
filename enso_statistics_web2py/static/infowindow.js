

// Load the Google Chart API
google.load('visualization', '1', {'packages':['annotatedtimeline', 'columnchart', 'piechart']});


var request_options={"coopid":"UNDEFINED",
                     "observation":"info",
                     "statistic":"averages",
                     "period":"monthly",
                     "season":"JAN",
                     "baseline":"",
                     "ENSOI":"ONI"};


function initialize_obsv_buttons(){
    $("button.observation").click(function(e){
        // Activate all the buttons
        //$("button.observation").attr("disabled", false);
        $("button.observation").removeClass("ui-state-disabled");
        // Deactivate the current one
        //$(this).attr("disabled", true);
        $(this).addClass("ui-state-disabled");
        // Get the value associated with the currently selected button
        var observation = $(this).attr("id");
        // Update the request_options
        request_options.observation = observation;
        if (observation == "info"){
            $("#stats").hide();
        } else {
            $("#stats").show();
        };
        update_request_options();
    });
};


function initialize_stats_tabs(event){
    $("#tab_averages").click(function(e){
        request_options.statistic = "averages";
        // Flag this tab as 'current'
        $("#stats_tabs > li").removeClass("current");
        $(this).addClass("current");
        // Show the corresponding panel and hide the others
        $(".stats_panels").hide();
        $("#panel_averages").show()
        //
        update_request_options();
    });
    $("#tab_distribution").click(function(e){
        request_options.statistic = "distribution";
        // Flag this tab as 'current'
        $("#stats_tabs > li").removeClass("current");
        $(this).addClass("current");
        // Show the corresponding panel and hide the others
        $(".stats_panels").hide();
        $("#panel_seasons").show()
        //
        update_request_options();
    });
    $("#tab_exceedance").click(function(e){
        request_options.statistic = "exceedance";
        // Flag this tab as 'current'
        $("#stats_tabs > li").removeClass("current");
        $(this).addClass("current");
        // Show the corresponding panel and hide the others
        $(".stats_panels").hide();
        $("#panel_seasons").show()
        //
        update_request_options();
    });
    $("#tab_series").click(function(e){
        request_options.statistic = "series";
        // Flag this tab as 'current'
        $("#stats_tabs > li").removeClass("current");
        $(this).addClass("current");
        // Show the corresponding panel and hide the others
        $(".stats_panels").hide();
        //
        update_request_options();
    });
    $("#tab_extras").click(function(e){
        // Flag this tab as 'current'
        $("#stats_tabs > li").removeClass("current");
        $(this).addClass("current");
        // Show the corresponding panel and hide the others
        $(".stats_panels").hide();
        $("#panel_extras").show();
        $("#graph_panel").hide();
        $("#text_panel").show();
        //
        update_request_options();
    });

};


function select_baseline(){
    var selected = "";
    $("#ddaverages option:selected").each(function(){
        selected += $(this).val();
    });
    request_options.baseline = selected;
    update_request_options();
};

function select_period(){
    var selected = "";
    $("#ddperiod option:selected").each(function(){
        selected += $(this).val();
    });
    request_options.period = selected;
    $("#panel_seasons > select").hide();
    switch(selected)
    {
    case "monthly":
        $("#ddseason_monthly").show();
        $("#ddseason_monthly").trigger("change", 0);
        break;
    case "JFM":
        $("#ddseason_JFM").show();
        $("#ddseason_JFM").trigger("change", 0);
        break;
    case "DJF":
        $("#ddseason_DJF").show();
        $("#ddseason_DJF").trigger("change", 0);
        break;
    case "NDJ":
        $("#ddseason_NDJ").show();
        $("#ddseason_NDJ").trigger("change", 0);
        break;    
    };
    update_request_options();
};

function select_ensoi(){
    var selected = "";
    $("#ddensoi option:selected").each(function(){
        selected += $(this).val();
    });
    request_options.ensoi = selected;
    update_request_options();
    
};

function select_season(caller){
	var selected="";
	$(caller).children("option:selected").each(function(){
		selected += $(this).val();
	});
	request_options.season = selected;
	update_request_options();
}


function update_coopid(coopid){
	request_options.coopid = coopid;
	$("#ui-dialog-title-infowindow").text("Station #"+coopid);
	update_request_options();
};


function show_graph_panel(){
	// Show the graph panel, set its size and hide the text panel
	$("#graph_panel").show();
	$("#graph_panel").width("600px");
	$("#graph_panel").height("300px");
	$("#text_panel").hide();
};


function initialize_infowindow(){
	// Initialize the data connection
    initialize_DataConnection();
	// Empty the text panel
	$("#text_panel").html('');
	// Initialize the observation buttons
	initialize_obsv_buttons();
	$("button.observation#info").click();
	// 
	initialize_stats_tabs();
	$("#tab_averages").click();
	// Force a change of ENSOI and period to the first value as default
	$("#ddensoi").trigger("change",0);
	$("#ddperiod").trigger("change",0);
	$("#ddseason_monthly").trigger("change", 0);
	//
	var displayOptions={
		autoOpen: false,
		width: 618,
		modal: true,
		position: 'relative',
		//stack: true
		};
	$("#infowindow").attr("title", "Station #"+request_options.coopid);
	$("#infowindow").dialog(displayOptions);
	//$("#graph_panel").hide();
	// Deactivate the ENSOI selector for now
	$("#ddensoi").attr("disabled", true);
};



function process_stationinfo(coopid){
	// Call the DataController to get the station information with get_stationinfo
	// coopid: a 6-character string corresponding to the station COOP ID
	DataController.get_stationinfo({params:[coopid],
		onSuccess: function(data){
			// Hide the graph panel
			$("#graph_panel").hide();
			// Fill the text panel with the station information
			var info = "<p/><strong>Station name: </strong>" + data.STATION_NAME
			         + "<p/><strong>COOP ID     : </strong>" + data.COOPID
			         + "<p/><strong>Latitude    : </strong>" + data.LATITUDE
			         + "<p/><strong>Longitude   : </strong>" + data.LONGITUDE
			         + "<p/><strong>Altitude    : </strong>" + data.ELEVATION
			         + "<p/><strong>County      : </strong>" + data.COUNTIES;
			$("#text_panel").html(info);
			$("#text_panel").show();
		},
		onException: function(errorObj){
			log_error("Error retrieving the station info: "+errorObj.message);
		},
		// onComplete: function(responseObj){
		// 	alert("Completed process_stationinfo w/ "+responseObj)
		// },
	});
};


function process_averages(options){
	// Plot the averages for the selection with the GoogleCharts API
	// The data are provided through the get_averages method of the DataController
	DataController.get_averages({params:[options],
		onSuccess: function(response){
			// Hide the text panel and display the graph panel
			show_graph_panel();
			// Get the data from the data table
			// We use eval('('+...+')') to force response to a valid JSON string
			var data = new google.visualization.DataTable(eval('('+response+')'), 0.6);
			// Define the container for the plot
			var container = document.getElementById("graph_panel");
			// Initialize the visualization
			var chart = new google.visualization.ColumnChart(container);
			// Define some plotting options
			var averages_options = {colors:['cccccc','6666cc','669933','ffcc33'],
									legend:'bottom',
									//width: 700, height: 432,
									is3D: false,
									legendFontSize: 12,
									axisFontSize: 12};
			// Fix the legend of the Y-axis depending on the data
			switch (options.observation){
				case "rain":
					if (options.baseline == ""){
						averages_options.titleY = "Cum. precipitation (mm = 1/25in)";
					} else {
						averages_options.titleY = "Cum. precipitation anomalies (mm)"
					};
			    	break;
				case "tmin":
					averages_options.titleY = "Min. temperatures (oC)";
				    break;
				case "tmax":
					averages_options.titleY = "Max. temperatures (oC)";
					break;
			};
			// Draw the chart
			chart.draw(data, averages_options);
		},
		onException: function(errorObj){
			log_error("Error retrieving the averages: "+errorObj.message);
		},
		// onComplete: function(responseObj){
		// 	alert("Completed process_averages w/ "+responseObj)
		// }
	});
};



function process_timeseries(options){
	// Plot the averages for the selection with the GoogleCharts API
	// The data are provided through the get_averages method of the DataController
	DataController.get_series({params:[options],
		onSuccess: function(response){
			// Hide the text panel and display the graph panel
			show_graph_panel();
			// Get the data from the data table
			var data = new google.visualization.DataTable(eval('('+response+')'), 0.6);
			// Define the container for the plot
			var container = document.getElementById("graph_panel");
			// Initialize the visualization
			var chart = new google.visualization.AnnotatedTimeLine(container);
			// Draw the chart
			chart.draw(data);
		},
		onException: function(errorObj){
			log_error("Error retrieving the series: "+errorObj.message);
		},
		// onComplete: function(responseObj){
		// 	alert("Completed process_timeseries w/ "+responseObj)
		// }
	});
};


function log_request_options(){
    // 
    var txt = "<strong>Observation: </strong>"+request_options.observation+"<br/>"
             +"<strong>Statistic  : </strong>"+request_options.statistic+"<br/>"
             +"<strong>Period     : </strong>"+request_options.period+"<br/>"
             +"<strong>Season     : </strong>"+request_options.season+"<br/>"
             +"<strong>Baseline   : </strong>"+request_options.baseline+"<br/>"
             +"<strong>ENSOI      : </strong>"+request_options.ensoi+"<br/>"
             +"<strong>COOPID     : </strong>"+request_options.coopid+"<br/>";
    $("#text_panel").html(txt);
};


function update_request_options(){
	log_request_options();
	if (request_options.observation == "info"){
		process_stationinfo(request_options.coopid);
		return;
	};
	switch (request_options.statistic) {
		case "averages":
			process_averages(request_options);
			break;
		case "series":
			process_timeseries(request_options);
			break;
	};
};


