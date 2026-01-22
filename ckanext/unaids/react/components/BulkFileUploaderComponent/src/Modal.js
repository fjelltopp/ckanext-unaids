import React from 'react';
import ModalBody from './ModalBody';

export default function Modal(props) {
    const allowClosing = !props.uploadsComplete && !props.uploadInProgress;
    const closeButtonAttrs = [];
    return (
        <div className="modal fade" id={props.modalElementId} data-bs-backdrop="static" data-bs-keyboard="false">
            <div className="modal-dialog" role="document">
                <div className="modal-content">
                    <div className="modal-header">
                        <h4 className="modal-title">{ckan.i18n._('Upload Resources')}</h4>
                        <button
                            type="button"
                            className={`btn-close ${!allowClosing && 'disabled'}`}
                            data-bs-dismiss={allowClosing && 'modal'}
                            aria-label="Close"
                        >
                        </button>
                    </div>
                    <div className="modal-body">
                        <ModalBody {...props} />
                    </div>
                </div>
            </div>
        </div>
    )
}
