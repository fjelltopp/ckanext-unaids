// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

// This module will auto-update the value of the format field
// With the best guess taken from the name of the file
// Using the action format_guess on the server
this.ckan.module('format_update', function ($) {
    return {
        options: {
            trigger: 'input[name=url]',
            filename: 'input[name=url]',
            guess_action: 'format_guess'
        },
        initialize: function () {
            $.proxyAll(this, /_on/);
            $(this.options.trigger).change(this._onTrigger);
        },
        _onTrigger: function () {
            setTimeout(this._autofillFormat.bind(this), 500);
        },
        _autofillFormat: function() {
            var filename = $(this.options.filename).val();
            if(filename){
                this.sandbox.client.call(
                    'GET',
                    this.options.guess_action,
                    "?"+$.param({filename: filename}),
                    this._updateFormat.bind(this),
                    function(error){console.error("Error calling api to guess format")}
                );
            }else{
                this._onTrigger();
            }
        },
        _updateFormat: function (json) {
            if('result' in json && 'format' in json.result){
                $(this.el).select2("val", json.result.format);
            }
        }
    };
});
