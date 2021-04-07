import React from 'react';
import { useDropzone } from 'react-dropzone'

export default function FileUploader({ setPendingFiles }) {

    const { getRootProps, getInputProps, open } = useDropzone({
        noClick: true,
        onDrop: React.useCallback(acceptedFiles => {
            setPendingFiles(prev => [...prev, ...acceptedFiles]);
        })
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
