import React from 'react';
import { useDropzone } from 'react-dropzone'
import axios from 'axios';
import { Client } from "giftless-client";

export default function FileUploader({
    maxResourceSize, lfsServer, orgId, datasetName,
    setUploadProgress, setUploadFileName, setHiddenInputs,
    setUploadError
}) {

    const getAuthToken = () =>
        axios.post(
            '/api/3/action/authz_authorize',
            { scopes: `obj:${orgId}/${datasetName}/*:write` },
            { withCredentials: true }
        )
            .then(res => res.data.result.token)
            .catch(error => {
                setUploadError({
                    error: ckan.i18n._('Authorisation Error'),
                    description: ckan.i18n._('You are not authorized to upload this resource.')
                });
                throw error;
            });
    const uploadFile = (client, file) =>
        client.upload(file, orgId, datasetName, progress =>
            setUploadProgress({
                loaded: progress.loaded,
                total: progress.total
            })
        )
            .catch(error => {
                setUploadError({
                    error: ckan.i18n._('Server Error'),
                    description: ckan.i18n._('An unknown server error has occurred.')
                });
                throw error;
            });

    const handleFileSelected = async inputFile => {
        if (!inputFile) return;
        setUploadProgress({ loaded: 0, total: 1 });
        const file = data.open(inputFile);
        const authToken = await getAuthToken();
        const client = new Client(lfsServer, authToken, ['basic']);
        await uploadFile(client, file);
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
        maxSize: maxResourceSize * 1000000,
        onDrop: acceptedFiles =>
            handleFileSelected(acceptedFiles[0]),
        onDropRejected: rejectedFiles => {
            if (rejectedFiles.length > 1) {
                setUploadError({
                    error: ckan.i18n._('Too many files'),
                    description: ckan.i18n._('You can only upload one file for each resource.')
                });
            } else if (JSON.stringify(rejectedFiles).includes('file-too-large')) {
                setUploadError({
                    error: ckan.i18n._('File Too Large'),
                    description: ckan.i18n._(`Resources cannot be larger than ${maxResourceSize} megabytes.`)
                });
            } else {
                setUploadError({
                    error: ckan.i18n._('Unknown Error'),
                    description: ckan.i18n._('An unknown error has occurred.')
                });
                throw rejectedFiles;
            };
        },
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
