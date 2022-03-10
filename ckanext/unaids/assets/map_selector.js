// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('map_selector', function ($) {
	return {
        options: {
        	configurl: "/api/3/action/unaids_map_config"
        },
        initialize: function () {
            new svgMap({
            	targetElementID: this.el.attr('id'),
            	data: this._getConfiguration()
            });
        },
        _getConfiguration: function () {
        	return  {
			    data: {
					gdp: {
						name: "GDP per capita",
						format: "{0} USD",
						thousandSeparator: ',',
						thresholdMax: 1,
						thresholdMin: 0
					},
					change: {
						name: 'Change to year before',
						format: '{0} %'
					}
			    },
			    touchLink: true,
			    applyData: 'gdp',
			    values: {
					ES: {gdp: 0, change: 4.73, link: 'https://adr.unaids.org' },
					AL: {gdp: 1, change: 11.09},
					GB: {gdp: 1, change: 10.01}
			    }
			};
        }
    };
});
