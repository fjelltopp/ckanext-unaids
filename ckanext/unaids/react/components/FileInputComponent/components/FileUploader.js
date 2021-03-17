import React from 'react';
import { useDropzone } from 'react-dropzone'
import { Client } from "giftless-client";

export default function FileUploader({
    lfsServer, orgId, datasetId, authToken,
    setUploadProgress, setUploadFileName, setHiddenInputs,
    setUploadFailed
}) {

    const handleFileSelected = async inputFile => {
        if (!inputFile) return;
        setUploadProgress({ loaded: 0, total: 1 });
        const file = data.open(inputFile);
        const client = new Client(lfsServer, authToken, ['basic']);
        await client.upload(file, orgId, datasetId, progress => {
            setUploadProgress({
                loaded: progress.loaded,
                total: progress.total
            });
        }).catch(error => {
            setUploadFailed(true);
            throw error;
        });
        setUploadProgress({ loaded: 100, total: 100 });
        setUploadFileName(file._descriptor.name);
        setHiddenInputs('file', {
            sha256: file._computedHashes.sha256,
            size: file._descriptor.size,
            url: file._descriptor.name
        })
    }

    const { getRootProps, getInputProps, open } = useDropzone({
        multiple: false,
        noClick: true,
        onDrop: acceptedFiles =>
            handleFileSelected(acceptedFiles[0]),
        onDropRejected: rejectedFiles =>
            handleFileSelected(rejectedFiles[0].file),
    })

    const uploadOptions = [
        {
            name: 'FileUploaderButton',
            label: ckan.i18n._('Upload a file'),
            icon: 'fa-cloud-upload',
            onClick: e => {
                open(e);
                e.preventDefault();
            }
        },
        {
            name: 'UrlUploaderButton',
            label: ckan.i18n._('Link'),
            icon: 'fa-globe',
            onClick: e => {
                setHiddenInputs('url', {});
                e.preventDefault();
            }
        }
    ]

    return (
        <div {...getRootProps({ className: 'dropzone' })} data-testid="FileUploaderComponent">
            <input {...getInputProps()} data-testid="FileUploaderInput" />
            <p>{ckan.i18n._('Drag a file into this box or')}</p>
            <div className="btn-group">
                {uploadOptions.map(option => (
                    <button
                        key={option.name}
                        data-testid={option.name}
                        className="btn btn-default"
                        onClick={option.onClick}
                    >
                        <i className={`fa ${option.icon}`}></i>
                        {option.label}
                    </button>
                ))}
            </div>
        </div>
    )

}
