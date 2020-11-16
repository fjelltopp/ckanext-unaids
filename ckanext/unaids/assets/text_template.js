// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('text_template', function ($) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      this._setup();
      $("form :input:not(#field-title, #field-name)").change(this._onChange);
      $(this.options.update).keyup(this._onKeyup);
      console.log(this.options.template);
    },
    _form: {},
    _onChange: function (event) {
      event.preventDefault();
      this._form[$(event.target).attr("name")] = $(event.target).val();
      this._updateInput(event.target);
    },
    _setup: function () {
      var form = {}
      $.each($('form').serializeArray(), function(_, kv) {
        form[kv.name] = kv.value;
      });
      this._form = form;
      var text = this._format(this.options.template, this._form)
      $(this.el).text(text);
    },
    _onKeyup: function (){
      $(this.el).text($(this.options.update).val());
    },
    _updateInput: function (el) {
      var text = this._format(this.options.template, this._form)
      $(this.options.update).val(text);
      $(this.options.update).keyup();
    },
    _format: function (string, variables) {
      $.each( variables, function(i, v) {
        string = string.replace(new RegExp('\\{' + i + '\\}', 'gm'), v);
      });
      return string;
    }
  };
});
