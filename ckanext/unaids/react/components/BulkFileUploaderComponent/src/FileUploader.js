import React from 'react';
import { useDropzone } from 'react-dropzone'

export const dropzoneTypes = {
    fullPageDropzone: 'fullPageDropzone',
    modalDropzone: 'modalDropzone'
}

export default function FileUploader({ modalElementId, maxResourceSize, setPendingFiles, getDefaultUploadAction, dropzoneType }) {

    const openModalUsingJquery = () => {
        if (dropzoneType === dropzoneTypes.fullPageDropzone) {
            $(`#${modalElementId}`).modal('show');
        }
    }
    const handleDropAccepted = acceptedFiles => {
        acceptedFiles = acceptedFiles.map(acceptedFile =>
            Object.assign(acceptedFile, {
                uploadAction:
                    JSON.stringify(getDefaultUploadAction(acceptedFile))
            })
        );
        setPendingFiles(pendingFiles => [...pendingFiles, ...acceptedFiles]);
    };
    const handleDropRejected = rejections => {
        const errorMessage = rejection => {
            if (JSON.stringify(rejection).includes('file-too-large')) {
                return ckan.i18n._(`Error: Resources cannot be larger than ${maxResourceSize} megabytes.`);
            } else {
                console.warn('Unhandled dropzone error', rejection.errors);
                return ckan.i18n._('Error: Unable To Load File.');
            }
        };
        rejections = rejections.map(rejection =>
            Object.assign(rejection.file, { error: errorMessage(rejection) })
        );
        setPendingFiles(pendingFiles => [...pendingFiles, ...rejections]);
    };

    const { getRootProps, getInputProps, open, isDragActive } = useDropzone({
        noClick: true,
        maxSize: maxResourceSize * 1000000,
        onDrop: React.useCallback(openModalUsingJquery),
        onDropAccepted: React.useCallback(handleDropAccepted),
        onDropRejected: React.useCallback(handleDropRejected),
    });

    const className = [dropzoneType, isDragActive ? 'active' : ''].join(' ');
    return (
        <div {...getRootProps({ className })} data-testid={dropzoneType}        >
            {dropzoneType === dropzoneTypes.fullPageDropzone
                ? (
                    <>
                        <div id="DropzoneContainer"></div>
                        {isDragActive &&
                            <div className="drag-files-instructions-wrapper">
                                <div className="drag-files-instructions">
                                    <h3><i className="fa fa-upload"></i></h3>
                                    <h3>{ckan.i18n._('Drop files to upload them')}</h3>
                                </div>
                            </div>
                        }
                    </>
                )
                : (
                    <>
                        <input {...getInputProps()} data-testid="BulkFileUploaderInput" />
                        <p>{ckan.i18n._('Drop files here to upload them to the dataset')}</p>
                        <div className="btn-group">
                            <button
                                className="btn btn-success"
                                onClick={open}
                            >
                                <i className="fa fa-plus"></i>
                                {ckan.i18n._('Add files')}
                            </button>
                        </div>
                    </>
                )
            }
        </div>
    )

}
