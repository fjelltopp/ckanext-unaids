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
      console.log(this.options.files)
      if(this.options.files.length > 1){
        console.log("Removing hidden");
        console.log(this.options.files.length);
        $(this.el).removeClass('hidden');
        this.el.on('click', this._onClick);
      }else{
        console.log("Adding hidden");
        $(this.el).addClass('hidden');
      }
    },
    _onClick: function (event) {
      event.preventDefault();
      this.downloadAll(this.options.files);

    },
    downloadAll: function (urls) {
      var link = document.createElement('a');
      link.setAttribute('target', "_blank");
      link.style.display = 'none';
      document.body.appendChild(link);
      for (var i = 0; i < urls.length; i++) {
        var name = urls[i].split('/');
        name = name[name.length - 1];
        link.setAttribute('href', urls[i]);
        link.setAttribute('download', name)
        link.click();
      }
      document.body.removeChild(link);
    }
  };
});
