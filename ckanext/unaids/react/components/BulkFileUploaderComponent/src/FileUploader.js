import React from 'react';
import { useDropzone } from 'react-dropzone'
import { Client } from 'giftless-client';
import axios from 'axios';
import { Promise } from 'bluebird';

export default function FileUploader({
    lfsServer, orgId, datasetId,
    createResources, setUploadsInProgress
}) {

    const getAuthToken = () => (
        axios.post(
            '/api/3/action/authz_authorize',
            { scopes: `obj:ckan/${datasetId}/*:write` },
            { withCredentials: true }
        )
            .then(res => res.data.result.token)
            .catch(error => handleError(ckan.i18n._('Authorisation Error'), error))
    );
    const uploadFile = (client, localFile) => (
        client.upload(localFile, orgId, datasetId)
            .then(() => ({
                name: localFile._descriptor.name,
                sha256: localFile._computedHashes.sha256,
                size: localFile._descriptor.size,
                url: localFile._descriptor.name
            }))
            .catch(error => handleError(ckan.i18n._('Upload Error'), error))
    );
    const handleError = (errorType, error) => {
        console.log(`${errorType}: ${error}`);
        alert(`${errorType}. ${ckan.i18n._('Please refresh this page and try again.')}`);
        window.location.replace(window.location.pathname);
    };

    const { getRootProps, getInputProps, open } = useDropzone({
        noClick: true,
        onDrop: async files => {
            setUploadsInProgress(files);
            const client = new Client(lfsServer, await getAuthToken(), ['basic']);
            Promise.mapSeries(files, async file =>
                await uploadFile(client, data.open(file))
            ).then(files => createResources(files));
        }
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
                    {ckan.i18n._('Add files...')}
                </button>
            </div>
        </div>
    )

}
