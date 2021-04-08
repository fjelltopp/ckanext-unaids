import React from 'react';
import { useDropzone } from 'react-dropzone'

export default function FileUploader({ maxResourceSize, setPendingFiles }) {

    const { getRootProps, getInputProps, open } = useDropzone({
        noClick: true,
        maxSize: maxResourceSize * 1000000,
        onDropAccepted: React.useCallback(files => {
            setPendingFiles(prev => [...prev, ...files]);
        }),
        onDropRejected: React.useCallback(rejections => {
            const errorMessage = rejection => {
                if (JSON.stringify(rejection).includes('file-too-large')) {
                    return ckan.i18n._(`Error: Resources cannot be larger than ${maxResourceSize} megabytes.`);
                } else {
                    console.warn('Unhandled dropzone error', rejection.errors);
                    return ckan.i18n._('Error: Unable To Load File.');
                }
            };
            let rejectedFiled = rejections.map(rejection => {
                let rejectedFile = rejection.file;
                rejectedFile.error = errorMessage(rejection);
                return rejectedFile;
            });
            setPendingFiles(prev => [...prev, ...rejectedFiled]);
        }),
    });

    return (
        <div {...getRootProps({ className: 'dropzone' })}>
            <input {...getInputProps()} />
            <p>{ckan.i18n._('Drag & Drop files here to initiate bulk upload')}</p>
            <div className="btn-group">
                <button
                    className="btn btn-success"
                    onClick={open}
                >
                    <i className="fa fa-plus"></i>
                    {ckan.i18n._('Add files')}
                </button>
            </div>
        </div>
    )

}
