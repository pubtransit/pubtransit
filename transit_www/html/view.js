function View() {
    this.map = null;
    this.stopMarkers = [];
    this.model = new Model();
    this.presenter = new Presenter(this, this.model);
    this.latitude = document.getElementById('latitude');
    this.longitude = document.getElementById('longitude');
    this.zoom = document.getElementById('zoom');
    this.busWindow = null;
    this.pinImages = null
}

View.prototype.centerCurrentPosition = function() {
    this.presenter.centerCurrentPosition();
}

View.prototype.centerPosition = function(position) {
    if (this.map) {
        this.map.setCenter(position);
    }
}

View.prototype.updateCenter = function() {
    if (this.map) {
        var center = this.model.getCenter();
        this.latitude.value = center.lat;
        this.longitude.value = center.lng;
    }
}

View.prototype.updateZoom = function() {
    if (this.map) {
        this.zoom.value = this.model.zoom;
    }
}

View.prototype.initMap = function() {
    this.map = new google.maps.Map(document.getElementById('map'), {
        bounds: this.model.bounds,
        zoom: 16
    });

    this.pinIcons = {
        transit: new google.maps.MarkerImage(
                "http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|"
                        + "FE7569", new google.maps.Size(21, 34),
                new google.maps.Point(0, 0), new google.maps.Point(10, 34)),

        feed: new google.maps.MarkerImage(
                "http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|"
                        + "75FE69", new google.maps.Size(21, 34),
                new google.maps.Point(0, 0), new google.maps.Point(10, 34)),
    }

    var self = this;

    function boundsChanged() {
        var bounds = self.map.getBounds().toJSON();
        if (!isNaN(bounds.south) && !isNaN(bounds.north)
                && !isNaN(bounds.east) && !isNaN(bounds.west)) {
            self.presenter.setBounds(bounds);
        }
    }
    this.map.addListener('bounds_changed', boundsChanged);

    function zoomChanged() {
        self.presenter.setZoom(self.map.getZoom());
    }
    zoomChanged();
    this.map.addListener('zoom_changed', zoomChanged);

    var busWindowClosed = function() {
        self.presenter.setCurrentStop(null)
    }
    this.busWindow = new google.maps.InfoWindow();
    this.busWindow.addListener('closeclick', busWindowClosed);

    view.centerCurrentPosition();
}

View.prototype.dropStopMarker = function(stop) {
    var marker = this.stopMarkers[stop.stopId]
    if (!marker) {
        // log.debug("Drop new stop marker:", stop);
        this.stopMarkers[stop.stopId] = marker = new google.maps.Marker({
            position: this.model.stops[stop.stopId],
            map: view.map,
            animation: google.maps.Animation.DROP,
            icon: this.pinIcons[stop.provider],
        });
        var self = this;
        marker.addListener('click', function() {
            self.presenter.setCurrentStop(stop.stopId);
        });
    }
}

View.prototype.removeMarkers = function() {
    oldMarkers = this.stopMarkers;
    this.stopMarkers = {};
    for (i in oldMarkers) {
        oldMarkers[i].setMap(null);
    }
}

View.prototype.updateCurrentStop = function() {
    var currentStop = this.model.getCurrentStop();
    var win = this.busWindow;
    if (currentStop && win) {
        var busInfos = [
                "<h3>" + currentStop.name + "</h3>",
                "<table>",
                "<tr>" + "<td><h4>Route</h4></td>"
                        + "<td><h4>Destination</h4></td>"
                        + "<td><h4>Time</h4></td>" + "<tr>", ];
        for ( var busId in this.model.buses) {
            var bus = this.model.buses[busId];
            var route = this.model.routes[bus.routeId];
            if (route) {
                var routeName = route.name;
                var routeStops = route.stops;
            } else {
                var routeName = bus.routeId.split('-')[2];
                var routeStops = null;
            }

            if (routeStops && routeStops.length > 0) {
                departureIndex = routeStops.indexOf(currentStop.stopId);
                destinationIndex = routeStops.indexOf(bus.destinationId);
                if (departureIndex > destinationIndex) {
                    var finalDestinationId = routeStops[0];
                } else {
                    var finalDestinationId = routeStops[routeStops.length - 1];
                }
            } else {
                finalDestinationId = bus.destinationId;
            }

            var destinationStop = this.model.stops[finalDestinationId];
            if (destinationStop) {
                var destinationName = destinationStop.name;
            } else {
                var destinationName = finalDestinationId.split('-')[2];
            }
            var remainingMinutes = Math.ceil(bus.deltaTime / (1000 * 60));
            if (remainingMinutes < 60.) {
                var time = [remainingMinutes, "min."].join(" ")
            } else {
                var time = [bus.time.getHours(), bus.time.getSeconds(),
                        bus.time.getMinutes()].join(':');
            }
            var row = "<tr>" + "<td><h5>" + routeName + "</h5></td>" + "<td>"
                    + destinationName + "</td>" + "<td><h5>" + time
                    + "</h5></td>" + "<tr>";
            busInfos.push(row);
        }
        busInfos.push('</table>');
        var newContent = busInfos.join('');
        var oldContent = win.getContent();
        if (newContent != oldContent) {
            win.setContent(newContent);
            win.setPosition(currentStop);
            win.open(this.map);
        }
    }
}

function closeBusesWindow() {
    var win = this.busWindow;
    if (win) {
        win.close();
    }
}
