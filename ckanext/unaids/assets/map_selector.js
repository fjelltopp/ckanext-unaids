// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('map_selector', function ($) {
    return {
        options: {
            configurl: "/map-options/"
        },
        initialize: function () {
            var mapElementID = this.el.attr('id');
            $.getJSON({
                url: this.options.configurl
            }).done(function( data ) {
                new svgMap({
                    targetElementID: mapElementID,
                    data: data,
                    mouseWheelZoomWithKey: true,
                    initialZoom: 1.9,
                    initialPan: {x:0, y:0}
                });
            });
        }
    };
});
