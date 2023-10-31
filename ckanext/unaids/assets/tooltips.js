// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('tooltips', function ($) {
  return {
    options:{},
    initialize: function () {
      $.proxyAll(this, /_on/);
      $(this.el).tooltip();
      console.log($(this.el));
    }
  };
});
