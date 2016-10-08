
function View() {
    this.map = null;
    this.stopMarkers = [];
    this.model = new Model();
    this.presenter = new Presenter(this, this.model);
    this.latitude = document.getElementById('latitude');
    this.longitude = document.getElementById('longitude');
    this.radius = document.getElementById('radius');
};

View.prototype.centerCurrentPosition = function () {
    this.presenter.centerCurrentPosition();
}

View.prototype.updatePosition = function () {
    if (this.map) {
        this.map.setCenter(this.model.position);
    }
    this.latitude.value = this.model.position.lat;
    this.longitude.value = this.model.position.lng;
}

View.prototype.updateRadius = function () {
    this.radius.value = this.model.radius;
    if (radius > 1000.) {
        this.radius["border-color"] = "red";
    } else {
        this.radius["border-color"] = "black";
   }
}

View.prototype.initMap = function() {
    this.map = new google.maps.Map(
        document.getElementById('map'),
        {center: this.model.position, zoom: 16}
    );

    var self = this;
    this.map.addListener('center_changed', function() {
        var position = self.map.getCenter().toJSON();
        self.presenter.setPosition(position);
    });
    this.map.addListener('zoom_changed', function() {
        var zoom = self.map.getZoom() - 15;
        var radius = 1000.;
        while (zoom > 0) {
            zoom--;
            radius *= 0.5
        }
        while (zoom < 0) {
            zoom++;
            radius *= 2.
        }
        self.presenter.setRadius(radius);
    });
}

View.prototype.dropStopMarker = function(stopId) {
    if (!this.stopMarkers[stopId]) {
        var self = this;
        function dropMarker() {
            log.debug("Drop new stop marker:", stopId);
            marker = self.stopMarkers[stopId]
            if (!marker){
                marker = new google.maps.Marker({
                    position: self.model.stops[stopId], map: view.map,
                    animation: google.maps.Animation.DROP});
                marker.addListener(
                    'click', function() {
                        self.presenter.setCurrentStop(stopId);
                    });
                view.stopMarkers[stopId] = marker;
            }
        }
        window.setTimeout(dropMarker, Math.random() * 1000.);
    }
}

View.prototype.updateCurrentStop = function() {
    var win = this.busWindow;
    if(!win) {
        this.busWindow = win = new google.maps.InfoWindow();
    }

    var busInfos = [
        "<h3>"+ this.model.getCurrentStop().name + "</h3>",
        "<table>",
        "<tr>" +
            "<td><h4>Route</h4></td>" +
            "<td><h4>Destination</h4></td>" +
            "<td><h4>Time</h4></td>" +
        "<tr>",
    ];
    for (var busId in this.model.buses) {
        var bus = this.model.buses[busId];
        var route = bus.routeId.split('-')[2];
        if (!route) {
            route = bus.routeId;
        }
        var destinationStop = this.model.stops[bus.destinationId];
        if (destinationStop) {
            var destinationName = destinationStop.name;
        } else {
            var destinationName = bus.destinationId;
        }
        var time = bus.time.join(':');
        var row = "<tr>" +
            "<td><h5>" + route + "</h5></td>" +
            "<td>" + destinationName + "</td>" +
            "<td>" + time + "</td>" +
        "<tr>";
        busInfos.push(row);
    }
    busInfos.push('</table>');
    win.setContent(busInfos.join(''));
    win.setPosition(this.model.getCurrentStop());
    win.open(this.map);
}

function closeBusesWindow() {
    var win = this.busWindow;
    if (win) {
        win.close();
    }
}
