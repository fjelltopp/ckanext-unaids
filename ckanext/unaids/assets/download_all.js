// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('download_all', function ($) {
  return {
    options:{
      files: '[]'
    },
    initialize: function () {
      $.proxyAll(this, /_on/);
      // CKAN's module system auto-parses data-module-* attributes via jQuery.parseJSON,
      // so this.options.files is already an array. We keep an Array.isArray guard as a
      // safety net in case of unexpected environments.
      // Pre-existing regression fix (ADX-227): the condition was accidentally changed from
      // >= 1 to > 1, hiding the button when only one file was accessible.
      var files = Array.isArray(this.options.files) ? this.options.files : [];
      if (files.length >= 1) {
        $(this.el).removeClass('hidden');
        this.el.on('click', function(event) {
          event.preventDefault();
          this.downloadAll(files);
        }.bind(this));
      } else {
        $(this.el).addClass('hidden');
      }
    },
    downloadAll: async function (urls) {
      var count = 0;
      for (var i = 0; i < urls.length; i++) {
        // Client-side scheme guard (defence-in-depth): skip anything that isn't
        // http(s) or a root-relative path. Must run before new URL() to avoid
        // TypeError on malformed/dangerous URLs.
        if (!/^(https?:\/\/|\/)/.test(urls[i]) && urls[i].indexOf(':') !== -1) {
          continue;
        }
        var name = decodeURIComponent(new URL(urls[i], window.location.origin).pathname.split('/').pop());
        var link = document.createElement('a');
        link.setAttribute('target', "_blank");
        link.setAttribute('href', urls[i]);
        link.setAttribute('download', name);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        if (++count >= 10) {
          // need to pause every 10 files for Google Chrome to work
          await new Promise(r => setTimeout(r, 2000));
          count = 0;
        }
      }
    }
  };
});
