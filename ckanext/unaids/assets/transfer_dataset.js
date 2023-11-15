this.ckan.module('transfer-dataset', function (jQuery) {
  return {
    /* An object of module options */
    options: {
      value: '',
      orgs:[]
    },

    initialize: function () {
      $.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
      this.options.options = '<option value="">' + this._('No Organisation') + '</option>';
      for(org in this.options.orgs){
        let selected = "";
        if(this.options.orgs[org].value == this.options.value){
          selected = " selected ";
        }
        this.options.options = this.options.options +
                               "<option value='" + this.options.orgs[org].value + "'>" +
                               this.options.orgs[org].text +
                               "</option>";
      }
    },

    showModal: function () {
      this.sandbox.body.append(this.createModal());
      this.modal.modal('show');
      // Center the modal in the middle of the screen.
      this.modal.css({
        'margin-top': this.modal.height() * -0.5,
        'top': '50%'
      });
    },

    /* Creates the modal dialog, attaches event listeners and localised
     * strings.
     *
     * Returns the newly created element.
     */
    createModal: function () {
      template = [
        '<div class="modal fade">',
        '<form method="post">',
        '<div class="modal-dialog modal-dialog-centered">',
        '<div class="modal-content">',
        '<div class="modal-header"><h4 class="modal-title">',this._('Transfer Dataset'),'</h4></div>',
        '<div class="modal-body">',
        '<div class="form-group ">',
        '<p class="text-muted">',this._('This feature allows you to transfer ownership of this dataset to another organisation you do not have editor rights for:'),'</p>',
        '<ul><li class="text-muted">',this._('First, select the organisation who will receive the dataset using the dropdown below.'),'</li>',
        '<li class="text-muted">',this._('Upon clicking "Transfer" below, an administrator of the recipient organisation will need to visit the dataset page and accept the transfer.'),'</li>',
        '<li class="text-muted">',this._('You will lose control of the dataset once they have accepted the transfer.'),'</li></ul>',
        '<div class="form-group control-full">',
        '<label class="control-label" for="notes">',this._('Transfer to'),'</label>',
        '<div class="controls ">',
        '<select id="transfer_to" name="transfer_to" tabindex="-1" title="Transfer to">',
        this.options.options, '</select>',
        '</div></div></div>',
        '<div class="modal-footer">',
        '<a href="#"" class="btn btn-default btn-cancel"><span>',this._('Cancel'),'</span></a>',
        '<button type="submit" class="btn btn-primary">', this._('Transfer'),'</button>',
        '</div></div></div></form></div>',
      ].join('\n')
      if (!this.modal) {
        var element = this.modal = jQuery(template);
        element.on('click', '.btn-cancel', this._onCancel);
        element.on('click', '.btn-primary', this._onSubmit);
        element.modal({show: false});
        if(this.options.value){
          element.find('#transfer_to').val(this.options.value);
        }
        element.find('#transfer_to').select2();
      }
      return this.modal;
    },

    /* Event handler that displays the confirm dialog */
    _onClick: function (event) {
      event.preventDefault();
      this.showModal();
    },

    /* Event handler for the cancel event */
    _onCancel: function (event) {
      this.modal.modal('hide');
    },

    /* Event handler for the submit event */
    _onSubmit: function (event) {
      $("#field-org_to_allow_transfer_to").val($("#transfer_to").val());
      $("button[name='save']").click()
      event.preventDefault();
    }
  };
});
