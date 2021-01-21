const WebSocket = require('ws');
const Pbf = require('pbf');
const messages = require("./messages.js");
const geobuf = require("geobuf");

// use the geobuf encoder/decoder for geobuf submessages
messages.Data.read = geobuf.decode;
messages.Data.write = geobuf.encode;


var args = process.argv.slice(2);
var uri = args[0];

function subscribe(topics) {
    var req = messages.ClientContainer;
    let pbf = new Pbf();
    req.write({
        typ: "MT_SUBSCRIBE",
        topics: topics
    }, pbf);
    let buffer = pbf.finish();
    ws.send(buffer);
}

// call this on pan/zoom
function update_bbox(minlat, maxlat, minlon, maxlon) {
    var req = messages.ClientContainer;
    let pbf = new Pbf();
    req.write({
        typ: "MT_UPDATE_BBOX",
        bbox: {
            min_latitude: minlat,
            max_latitude: maxlat,
            min_longitude: minlon,
            max_longitude: maxlon
        },
    }, pbf);
    let buffer = pbf.finish();
    ws.send(buffer);
}

const ws = new WebSocket(uri, ['sonde-geobuf']);
ws.binaryType = "arraybuffer";

ws.on('open', function open() {
    subscribe(['sondes', 'madis', 'dwd']);
    update_bbox(45, 48, 10, 17);
});

ws.on('message', function incoming(data) {

    var container = messages.ServerContainer;
    var c = container.read(new Pbf(data));

    // updates are GeoJSON features/points
    c.sonde_updates.forEach(function(s, index) {
        console.log("update", index,
            s.properties.serial, s.geometry.coordinates,
            s.properties.temp, s.properties.humidity, s.properties.pressure);
    });

    // paths are GeoJSON featurecollections of points
    c.sonde_paths.forEach(function(sonde, index) {
        console.log("sonde: ", sonde.serial);
        sonde.features.forEach(function(f, index) {
            console.log("path feature", index, f.geometry.coordinates,
            f.properties.temp, f.properties.humidity, f.properties.pressure);
        })
    });

});
