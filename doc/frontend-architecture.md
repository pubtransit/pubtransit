# Frontend System Architecture Design

## Data Flow Overview

<img src="https://cdn.rawgit.com/pubtransit/transit/d9674e671d73312fea1dbfe520456741c919077c/doc/frontend-data-flow.svg" width="40%" align="left">

The frontend side is a javascript based web page. It uses
[geo-localization browser API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/Using_geolocation)
to localize the user device and shows a map centered on
user position using
[Google Maps API](https://developers.google.com/maps/documentation/javascript/).

It dowloads feed files from https://www.pubtransit.org/feed/ folder as specified
in the [backend rest API documentation](backend-architecture.md) and it drops
green marks on the map representing stops. By clicking on one of these
marks a window is shown with scheduled departures for the next 24 hours.

The Javascript application is structured following [Model-View-Presenter](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93presenter) architectural pattern.
The View is connected to GoogleMap view and interact with it giving
rendering instructions and receiving UI events. The view pass these events
to the Presenter that acts as the controller of the application.

The presenter translate these events, it updates the global state throw the model
and by dispatching commands to the feeds client and the view.

The feed client is in charge of asynchronously fetching feed files from
the server on demand, deserialize them as column array tables, and sending
them back to calbacks provided by the presenter.

The presenter receive these tables, translate them to objects, store them
into the model and send notifications to the view to update the grafical
representation after model changes.

In this application all events are handled by the presenter. The model don't
fires notifications. It returns instead to the presenter true value in case
of change and false in case of no change.

This is because the model acts at level of object, that are many, but as 
objects are received as groups (from tables) to limit the number of events
we process only one event for every group of objects to avoid to overcharge
the view.

