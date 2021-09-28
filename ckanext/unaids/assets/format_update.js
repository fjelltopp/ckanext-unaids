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
    _onTrigger: function (event) {
      event.preventDefault();
      var filename = $(this.options.filename).val();
      this.sandbox.client.call(
          'GET',
          this.options.guess_action,
          $.param({filename: filename}),
          this._updateFormat,
          function(error){console.log("Error guessing format")}
      );
    },
    _updateFormat: function (json) {
      $(this.el).select2("val", format);
    }
  };
});
