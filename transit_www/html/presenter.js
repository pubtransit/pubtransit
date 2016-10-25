function Presenter(view, model) {
    this.model = model;
    this.view = view;
    this.feed = new FeedClient(model.feed, hanlder = this);
    this._stopRequested = false;
    this._updateCurrentStopRequested = false;
    this._updateCurrentStopUpdated = false;
    this.MIN_ZOOM = 15;
}

Presenter.prototype.centerCurrentPosition = function() {
    if (navigator.geolocation) {
        var self = this;
        log.debug("Get user position...");
        navigator.geolocation.getCurrentPosition(function(position) {
            self.view.centerPosition({
                lat: position.coords.latitude,
                lng: position.coords.longitude
            });
        }, function(msg) {
            log.error("Unable to get user position:", msg);
            self.view.centerPosition(self.model.getCenter());
        });
    } else {
        log.error("Geolocation is not supported by your browser.");
    }
}

Presenter.prototype.setBounds = function(bounds) {
    if (this.model.setBounds(bounds)) {
        if (this.model.zoom >= this.MIN_ZOOM) {
            log.debug("Set bounds:", this.model.bounds);
            if (!this._stopRequested) {
                this._stopRequested = true;
                var self = this;
                window.setTimeout(function() {
                    self.requestStops()
                }, 500.);
            }
        }
    } else {
        log.debug("Same location.");
    }
}

Presenter.prototype.setZoom = function(zoom) {
    if (zoom < this.MIN_ZOOM) {
        this.view.closeStopTimesWindow();
        this.view.removeMarkers();
        this.setCurrentStop(null);
    } else {
        this.updateCurrentStop();
    }
    this.model.setZoom(zoom);
}

Presenter.prototype.requestStops = function() {
    var self = this;
    this.feed.requestStops(this.model.bounds);
    this._stopRequested = false;
}

Presenter.prototype.receiveStops = function(stops) {
    for ( var i in stops) {
        var stop = stops[i];
        this.model.putStop(stop);
        this.dropStopMarker(stop);
    }
}

Presenter.prototype.dropStopMarker = function(stop) {
    var self = this;
    function dropMarker() {
        if (self.model.zoom >= self.MIN_ZOOM) {
            self.view.dropStopMarker(stop);
        }
    }
    window.setTimeout(dropMarker, Math.random() * 1000.);
}

Presenter.prototype.setCurrentStop = function(stopId) {
    if (this.model.setCurrentStop(stopId)) {
        if (stopId) {
            var stop = this.model.getCurrentStop();
            this.feed.requestRoutes(stop);
            this.feed.requestTrips(stop);
            this.feed.requestStopTimes(stop);
        }
        this.updateCurrentStop();
    }
}

Presenter.prototype.receiveStopTimes = function(stopTimes) {
    for ( var i in stopTimes) {
        this.model.putStopTime(stopTimes[i]);
    }
    this.updateCurrentStop();
}

Presenter.prototype.receiveRoutes = function(routes) {
    for ( var i in routes) {
        this.model.putRoute(routes[i]);
    }
    this.updateCurrentStop();
}

Presenter.prototype.receiveTrips = function(trips) {
    for ( var i in trips) {
        this.model.putTrip(trips[i]);
    }
    this.updateCurrentStop();
}

Presenter.prototype.updateCurrentStop = function() {
    this._updateCurrentStopUpdated = false; 
    if (!this._updateCurrentStopRequested) {
        this._updateCurrentStopRequested = true;
        this._updateCurrentStopUpdated = true;
        this.view.updateCurrentStop();
        var self = this;
        window.setTimeout(function() {
            self._updateCurrentStopRequested = false;
            if (!self._updateCurrentStopUpdated) {
                self.updateCurrentStop();
            }
        }, 200);
    }
}
