
function deg2rad(x){
	return x*Math.PI/180.
};
function rad2deg(x){
	return x*180/Math.PI;
};

function circle_getPath(center, radius){
	// Get the path of the circle of radius radius centered on center
	// @param {LatLng} center
	// @param {number} radius (in m)
	path = [];
	//
	var clat = deg2rad(center.lat());
	var clng = deg2rad(center.lng());
	// Angular distance (using the equatorial radius)
	var angd = (radius/6378137);
	var cx = Math.sin(clat)*Math.cos(angd);
	var cy = Math.cos(clat)*Math.sin(angd);
	for (i=0; i<72; i++){
		var ii = i*5.*Math.PI/180.;
		var rlat = Math.asin(cx+cy*Math.cos(ii));
		var rlon = Math.atan2(Math.sin(ii)*cy, 
							  Math.cos(angd)-Math.sin(clat)*Math.sin(rlat)) + clng;
		var current = new google.maps.LatLng(rad2deg(rlat),
											 rad2deg(rlon));
		path.push(current);
	};
	return new google.maps.MVCArray(path);
}

function window_getPath(){
	// Get the path of the current window
	var bounds = map.getBounds();
	var SW = bounds.getSouthWest();
	var NE = bounds.getNorthEast();
	return new google.maps.MVCArray([SW, new google.maps.LatLng(SW.lat(),NE.lng()),
									 NE, new google.maps.LatLng(NE.lat(),SW.lng()),]);
}



//google.load("maps", "3", {other_params:"sensor=false"});
var center_icon_url = "http://www.google.com/intl/en_us/mapfiles/ms/micons/orange.png";

// Global definitions
var geocoder;
var map;
var selection_center;
var selection_radius;
var selection_path = new google.maps.MVCArray([]);
var spotlight = new google.maps.Polygon();
var markers_list = [];



var base_icon_url = "http://www.google.com/intl/en_us/mapfiles/ms/micons/blue.png";
var selected_icon_url = "http://www.google.com/intl/en_us/mapfiles/ms/micons/red-dot.png";
var shadow_url = "http://www.google.com/mapfiles/shadow50.png";
//
var center_icon = new google.maps.MarkerImage(center_icon_url);
var base_icon = new google.maps.MarkerImage(base_icon_url);
var selected_icon = new google.maps.MarkerImage(selected_icon_url);
var shadow_icon = new google.maps.MarkerImage(shadow_url);


function create_marker(lat, lon, coopid){
	// Create a marker at (lat, lon) for station `coopid`
    var latlon = new google.maps.LatLng(lat,lon);
    var marker = new google.maps.Marker({
        position: latlon,
        title: "COOP" + coopid,
        clickable: true,
        icon: base_icon,
        visible: true,
        zindex: 5
    });
    // Switch to a new icon on mouseover
    google.maps.event.addListener(marker, "mouseover", function(){
        marker.setIcon(selected_icon);
    });
    // Revert to the original icon on mouseover
    google.maps.event.addListener(marker, "mouseout", function(){
        marker.setIcon(base_icon);
    });
    // Display our InfoWindow on a click
    google.maps.event.addListener(marker, "click", function(){
        load_infowindow(coopid);
        marker.setIcon(selected_icon);
        // marker.icon.shadow = shadow_url;
        map.panTo(latlon);
    });
    return marker;
};


function load_infowindow(coopid){
    $("#infowindow").dialog('open');
    update_coopid(coopid);
};


function reset_center(zipcode){
	if (geocoder){
		geocoder.geocode({"address": zipcode}, function(results, status){
			if (status == google.maps.GeocoderStatus.OK) {
				// Retrieve the new map center
				map_center = results[0].geometry.location;
				// Move to the new center
				map.panTo(map_center);
				map.setCenter(map_center);
				log_message("Map center set at: "+map_center);
				//
				reset_radius(map_center);
				//
				var marker = new google.maps.Marker({
					map: map, 
					position: map_center,
					title: zipcode,
					icon: center_icon,
					visible: true,
					zindex: 1
				});
			} else {
				log_message("Error in retrieving the map center: "+status);
	        }
		})
	}
	else{
		log_message("Geocoder *NOT* activated.");
	};
};


function set_selection_path(selection_center){
	// Get the radius (in m, from mi)
	selection_radius = $("#radius_selector :selected").val() * 1609;
	// Get the path of a circle centered on the current center
	// map_center = map.getCenter();
	selection_path = circle_getPath(selection_center, selection_radius);
	// Get the new bounds (we assume an equatorial radius of 6378137m)
	var angdistdeg = (selection_radius/6378137)*(180/Math.PI);
	var lat_n = selection_center.lat() + angdistdeg;
	var lat_s = selection_center.lat() - angdistdeg;
	var lon_ne = selection_center.lng() + angdistdeg/Math.cos(lat_n*Math.PI/180.);
	var lon_sw = selection_center.lng() - angdistdeg/Math.cos(lat_s*Math.PI/180.);
	var NEpoint = new google.maps.LatLng(lat_n, lon_ne);
	var SWpoint = new google.maps.LatLng(lat_s, lon_sw);
	map.fitBounds(new google.maps.LatLngBounds(SWpoint, NEpoint));
	//
	return selection_path;
};


function set_spotlight(){
	if (spotlight != undefined){
		spotlight.setMap();
	};
	if (selection_path != undefined){
		spotlight_options = {paths: new google.maps.MVCArray([window_getPath(), 
															  selection_path]),
							 strokeColor: '#333333',
							 strokeWidth: 0.1,
							 fillOpacity: 0.45,
							 map: map}
		spotlight = new google.maps.Polygon(spotlight_options);
	}
};

function set_markers(selection_center){
	radius = $("#radius_selector :selected").val() * 1
	// selection_radius is stored in m, when we need mi for get_region_markers
	DataController.get_region_markers({"params":[selection_center.lat(), 
												 selection_center.lng(), 
												 radius],
		onSuccess: function(response){
			if (response.length > 0){
				// Remove the existing markers
				if (markers_list.length){
					for (var i=0; i<markers_list.length;i++){
						markers_list[i].setMap();
					}
				}
				var errmsg = "Found "+response.length+
					         (response.lenth==1?"  marker ":" markers ")+
							 "in a radius of "+selection_radius/1609+" miles around point "+
							 selection_center+".<br/>"+
							"Click on a marker to display statistics "+
							"relative to the corresponding station.<br/>"+
							"<strong>Note:</strong><br/>"+
							"If the markers are not displayed properly, "+
							"try zooming in or out, or changing the map type.";
				$("#status_panel").html(errmsg);
				for (var i=0; i<response.length; i++){
					var value = response[i];
					var coopid = value[0];
					var lat = value[1];
					var lon = value[2];
					var marker = create_marker(lat, lon, coopid)
					marker.setMap(map);
					markers_list.push(marker);
				};
				// map.fitBounds(map.getBounds());
				//map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
			} else {
				log_message("No marker detected in a "+selection_radius/1609+" around point "+center);
			};
		},
		onException: function(errorObj){
			log_message("Error retrieving the station info: "+errorObj.message);
		},
		// onComplete: function(responseObj){
		// 	alert("Completed process_stationinfo w/ "+responseObj)
		// },
	});
};


function reset_radius(center){
	if (center == undefined){
		center = map.getCenter();
	};
	set_selection_path(center);
	set_spotlight();
	set_markers(center);
};


function select_markers(){
	var zipcode = $("#zipcode").val();
	if (zipcode != ''){
		reset_center(zipcode);
	} else {
		reset_radius(selection_center);
	};
};


function zipcode_keypress(event){
	var ucode = event.keyCode? event.keyCode: event.charCode;
	if (ucode == 13){
		reset_center($("#zipcode").val());
	};
};



function initialize_map(){
    // --- Some generic variables
    map_center = new google.maps.LatLng(+30.42973,-84.309082);
    var map_options ={
        center: map_center,
        zoom: 7,
        mapTypeId: google.maps.MapTypeId.HYBRID,
        navigationControl: true,
        navigationControlOptions: {
            style: google.maps.NavigationControlStyle.DEFAULT,
            position: google.maps.ControlPosition.TOP_LEFT
            },
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            position: google.maps.ControlPosition.TOP_RIGHT
            },
        scaleControl: true,
        scaleControlOptions:{
            position: google.maps.ControlPosition.BOTTOM_RIGHT
            },
        scrollwheel: false,
    };
    // Create a new map object on div "map_canvas"
    map = new google.maps.Map(document.getElementById("map_canvas"), map_options);
    //
    map.setZoom(7);
    google.maps.event.addListener(map, 'bounds_changed', set_spotlight);
    selection_center = map_center;
};

