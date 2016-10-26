# Frontend System Architecture Design

## Data Flow Overview

The frontend side is a javascript based web page. It uses
[geo-localization browser API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/Using_geolocation)
to localize the user device and shows a map centered on
user position using
[Google Maps API](https://developers.google.com/maps/documentation/javascript/).

It dowloads feed files from https://www.pubtransit.org/feed/ folder as specified
in the [backend rest API documentation](backend-architecture.md) and it drops
green marks on the map representing stops. By clicking on one of these
marks a window is shown with expected departures for the next 24 hours.



