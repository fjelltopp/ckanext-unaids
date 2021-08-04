import React from 'react';
import ModalBody from './ModalBody';

export default function Modal(props) {
    return (
        <div className="modal fade" id={props.modalElementId} data-backdrop="static" data-keyboard="false">
            <div className="modal-dialog" role="document">
                <div className="modal-content">
                    <div className="modal-header">
                        {!props.uploadsComplete &&
                            (
                                <button type="button" className="close" data-dismiss="modal">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            )
                        }
                        <h4 className="modal-title">{ckan.i18n._('Upload Resources')}</h4>
                    </div>
                    <div className="modal-body">
                        <ModalBody {...props} />
                    </div>
                </div>
            </div>
        </div>
    )
}
