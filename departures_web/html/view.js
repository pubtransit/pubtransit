
function View() {
    this.map = null;
    this.stopMarkers = [];
    this.model = new Model();
    this.presenter = new Presenter(this, this.model);
};

View.prototype.centerCurrentPosition = function () {
    this.presenter.centerCurrentPosition();
}

View.prototype.centerPosition = function () {
    if (this.map) {
        this.map.setCenter(this.model.position)
    }
}

View.prototype.initMap = function() {
    this.map = new google.maps.Map(
        document.getElementById('map'),
        {center: this.model.position, zoom: 15}
    );

    var self = this;
    this.map.addListener('center_changed', function() {
        window.setTimeout(
            function () {
                var position = self.map.getCenter().toJSON();
                self.presenter.setPosition(position);
            },
            1000.
        );
    });
    this.map.addListener('zoom_changed', function() {
        window.setTimeout(
            function () {
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
            },
            1000.
        );
    });
}

View.prototype.dropStopMarker = function(stop) {
    if (!this.stopMarkers[stop.stopId]) {
        log.debug("Drop new stop marker:", stop);
        var self = this;
        function dropMarker() {
            if (!self.stopMarkers[stop.stopId]){
                marker = new google.maps.Marker({
                    position: stop, map: view.map,
                    animation: google.maps.Animation.DROP});

                // marker.addListener(
                //    'click', function() {refreshBuses(stopIndex);});
                view.stopMarkers[stop.stopId] = marker;
            }
        }
        window.setTimeout(dropMarker, Math.random() * 1000.);
    }
}


//function showBusesWindow() {
//    closeBusesWindow();
//    busesInfo = [];
//    buses = getBuses()
//    for (var i = 0; i < buses.length; i++) {
//        bus = buses[i]
//        busesInfo.push(JSON.stringify(bus))
//    }
//
//    view.busesWindow = win = new google.maps.InfoWindow();
//    win.setContent(busesInfo.join('<br>'));
//    win.setPosition(getCurrentStopPosition());
//    win.open(view.map);
//}
//
//function closeBusesWindow() {
//    win = view.busesWindow;
//    if (win) {
//        win.close();
//        view.busesWindow = null;
//    }
//}
