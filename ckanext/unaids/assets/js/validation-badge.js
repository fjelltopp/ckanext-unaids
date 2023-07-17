this.ckan.module('validation-badge', function (jQuery) {
    return{
        options: {
          resource: null,
          status: 'created',
          url: null
        },
        initialize: function () {
          $.proxyAll(this, /_on/);
          this._poll();
          this.options.url = $(this.el).attr('href');
          $(this.el).removeAttr('href');
        },
        _poll: function() {
            var module = this;
            $.ajax({
                url: "/api/3/action/resource_validation_show?resource_id=" + this.options.resource,
                type: "GET",
                success: function(data){module._success(data);},
                error: function(XMLHttpRequest, textStatus, errorThrown){module._error(XMLHttpRequest, textStatus, errorThrown);},
                dataType: "json",
                complete: setTimeout(function(){module._complete();}, 5000),
                timeout: 2000
            });
        },
        _success: function(data) {
            this.options.status = data.result.status;
            if(this.options.status != 'running' && this.options.status != 'created'){
                this._update_badge();
                $(this.el).attr('href', this.options.url);
                if( this.options.status == 'failure' || this.options.status == 'error' ){
                    $(this.el).find('.badge-link').removeClass('hidden');
                }
            }
        },
        _error: function(XMLHttpRequest, textStatus, errorThrown) {
            this.options.status = 'error';
            this._update_badge();
            var message = 'No server connection. Please refresh your page.';
            $(this.el).attr('title', message );
            $(this.el).find('img').attr('title', message );
        },
        _complete: function() {
            if(this.options.status == 'running' || this.options.status == 'created'){
                this._poll();
            }
        },
        _update_badge: function(){
            var src = $('a.validation-badge').find('img').attr('src');
            var src = src.split('-')[0] + "-" + this.options.status + '.gif';
            $(this.el).find('img').attr('src', src);
        }

    }
});
