import React from 'react';

export default function Modal({ release, action }) {

    function RestoreOrDeleteReleaseContainer(modalText) {
        return (
            <>
                <div>{modalText}</div>
                <br />
                <div id="RestoreOrDeleteReleaseContainer" className="thumbnail alert-info">
                    <div className="row">
                        <div className="col-md-3 text-right">
                            <i className="fa fa-code-fork fa-3x"></i>
                        </div>
                        <div className="col-md-9">
                            <h3>{release.name}</h3>
                            <div>Description: {release.notes || ckan.i18n._('Not Set')}</div>
                        </div>
                    </div>
                </div>
            </>
        )
    };

    function EditReleaseContainer() {
        return (
            <>
                <div>
                    <label className="control-label" for="name">
                        <span title="This field is required" className="control-required">*</span>
                        <span> Name</span>
                    </label>
                    <input
                        type="text"
                        id="name"
                        className="form-control"
                        placeholder={ckan.i18n._('Version 1.1')}
                        required
                    />
                </div>
                <br />
                <div>
                    <label className="control-label" for="notes">Description</label>
                    <textarea
                        id="notes"
                        className="form-control"
                        placeholder={ckan.i18n._('Description')}
                        rows="3"
                    >
                        {release.notes && release.notes}
                    </textarea>
                </div>
            </>
        )
    };

    function ModalBody() {
        if (action.type === 'restore') {
            return RestoreOrDeleteReleaseContainer(
                ckan.i18n._('Are you sure you want to restore the following release?')
            );
        } else if (action.type === 'edit') {
            return EditReleaseContainer();
        } else if (action.type === 'delete') {
            return RestoreOrDeleteReleaseContainer(
                ckan.i18n._('Are you sure you want to delete the following release?')
            );
        } else {
            throw `Unhandled action.type: ${action.type}`;
        }
    };

    return (
        <>
            <div className="modal fade dataset-release-modal" id={`${action.type}_release_${release.id}`} tabindex="-1" role="dialog">
                <div className="modal-dialog" role="document">
                    <form className="modal-content">
                        <div className="modal-header">
                            <button type="button" className="close" data-dismiss="modal"><span>&times;</span></button>
                            <h4 className="modal-title">{action.title}</h4>
                        </div>
                        <div className="modal-body">
                            <ModalBody />
                        </div>
                        <div className="modal-footer">
                            <button type="button" className="btn btn-default" data-dismiss="modal">Close</button>
                            <button type="button" className="btn btn-primary">Save changes</button>
                        </div>
                    </form>
                </div>
            </div>
        </>
    )
}
