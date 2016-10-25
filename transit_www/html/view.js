function View() {
    this.map = null;
    this.stopMarkers = [];
    this.model = new Model();
    this.presenter = new Presenter(this, this.model);
    this.stopTimesWindow = null;
    this.stopTimesContent = "";
    this.pinIcon = null
}

View.prototype.centerCurrentPosition = function() {
    this.presenter.centerCurrentPosition();
}

View.prototype.centerPosition = function(position) {
    if (this.map) {
        this.map.setCenter(position);
    }
}

View.prototype.initMap = function() {
    this.map = new google.maps.Map(document.getElementById('map'), {
        bounds: this.model.bounds,
        zoom: 16
    });

    this.pinIcon = new google.maps.MarkerImage("greenpin.png",
            new google.maps.Size(21, 34), new google.maps.Point(0, 0),
            new google.maps.Point(10, 34));

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

    this.stopTimesWindow = new google.maps.InfoWindow();
    this.stopTimesWindow.addListener('closeclick', function() {
        self.presenter.setCurrentStop(null)
    });

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
            icon: this.pinIcon,
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
    var win = this.stopTimesWindow;
    if (currentStop && win) {
        var stopTimesInfos = [
                "<h3>" + currentStop.name + "</h3>",
                "<table>",
                "<tr>" + "<td><h4>Route</h4></td>"
                        + "<td><h4>Destination</h4></td>"
                        + "<td><h4>Time</h4></td>" + "<tr>", ];

        var stopTimes = this.model.getCurrentStopTimes();
        var entries = []
        var existingEntries = []
        for ( var i in stopTimes) {
            var stopTime = stopTimes[i];
            var trip = this.model.trips[stopTime.tripId];
            var route = this.model.routes[trip.routeId];

            var time = new Date();
            time.setHours(0);
            time.setMinutes(stopTime.departureMinutes);
            time.setSeconds(0);

            var now = new Date();
            var deltaTime = time - now;
            if (deltaTime < 0) {
                // increment the time by one day
                time.setDate(time.getDate() + 1);
                deltaTime = time - now;
            }

            var remainingMinutes = Math.ceil(deltaTime / (1000 * 60));
            if (remainingMinutes < 60.) {
                var timeStamp = [remainingMinutes, "min."].join(" ")
            } else {
                var timeStamp = this.getTimeStamp(time);
            }

            var signature = [route.name, route.name, timeStamp].join('|');
            if (!(signature in existingEntries)) {
                // avoid duplicate entries
                existingEntries[signature] = true;
                entries.push({
                    route: route.name,
                    routeId: route.routeId,
                    trip: trip.name,
                    tripId: trip.tripId,
                    timeStamp: timeStamp,
                    deltaTime: deltaTime,
                    signature: signature
                });
            }
        }
        entries = entries.sort(function(a, b) {
            var diff = a.deltaTime - b.deltaTime;
            if (!diff) {
                diff = a.routeId - b.routeId;
                if (!diff) {
                    diff = a.tripId - b.tripId;
                    if (!diff) {
                        diff = a.signature.localeCompare(b.signature);
                    }
                }
            }
            return diff;
        });
        for ( var i in entries) {
            var row = "<tr>" + "<td><h5>" + entries[i].route + "</h5></td>"
                    + "<td>" + entries[i].trip + "</td>" + "<td><h5>"
                    + entries[i].timeStamp + "</h5></td>" + "<tr>";
            stopTimesInfos.push(row);
        }
        stopTimesInfos.push('</table>');
        var newInfo = stopTimesInfos.join('');
        var oldInfo = this.stopTimesContent;
        if (newInfo.length != oldInfo.length) {
            log.debug('Stop times content has changed:', [oldInfo.length,
                    newInfo.length]);
            this.stopTimesContent = newInfo;
            win.setContent(newInfo);
            win.setPosition(currentStop);
            win.open(this.map);
        }
    } else {
        this.closeStopTimesWindow();
    }
}

View.prototype.getTimeStamp = function(time) {
    var intParts = [time.getHours(), time.getMinutes(), time.getSeconds()];
    var stringParts = [];
    for ( var i in intParts) {
        part = "" + intParts[i];
        while (part.length < 2) {
            part = "0" + part;
        }
        stringParts.push(part);
    }
    return stringParts.join(':');
}

View.prototype.closeStopTimesWindow = function() {
    var win = this.stopTimesWindow;
    if (win) {
        win.close();
    }
    this.stopTimesContent = "";
}
