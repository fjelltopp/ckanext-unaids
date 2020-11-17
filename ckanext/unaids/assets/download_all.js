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
      if(this.options.files.length > 1){
        $(this.el).removeClass('hidden');
        this.el.on('click', this._onClick);
      }else{
        $(this.el).addClass('hidden');
      }
    },
    _onClick: function (event) {
      event.preventDefault();
      this.downloadAll(this.options.files);
    },
    downloadAll: async function (urls) {
      var link = document.createElement('a');
      link.setAttribute('target', "_blank");
      link.style.display = 'none';
      var count = 0;
      document.body.appendChild(link);
      for (var i = 0; i < urls.length; i++) {
        var name = urls[i].split('/');
        name = name[name.length - 1];
        link.setAttribute('href', urls[i]);
        link.setAttribute('download', name);
        link.click();
        if (++count >= 10) {
          // need to pause every 10 files for Google Chrome to work
          await new Promise(r => setTimeout(r, 2000));
          count = 0;
        }
      }
      document.body.removeChild(link);
    }
  };
});
