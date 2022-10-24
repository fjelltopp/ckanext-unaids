import React from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { Client } from 'giftless-client';

export default function ResourceForker({
    maxResourceSize,
    lfsServer,
    orgId,
    datasetName,
    setUploadProgress,
    setUploadFileName,
    setHiddenInputs,
    setUploadError,
}) {
    const getAuthToken = () =>
        axios
            .post(
                '/api/3/action/authz_authorize',
                { scopes: `obj:${orgId}/${datasetName}/*:write` },
                { withCredentials: true }
            )
            .then((res) => res.data.result.token)
            .catch((error) => {
                setUploadError({
                    error: ckan.i18n._('Authorisation Error'),
                    description: ckan.i18n._(
                        'You are not authorized to upload this resource.'
                    ),
                });
                throw error;
            });
    const uploadFile = (client, file) =>
        client
            .upload(file, orgId, datasetName, (progress) =>
                setUploadProgress({
                    loaded: progress.loaded,
                    total: progress.total,
                })
            )
            .catch((error) => {
                setUploadError({
                    error: ckan.i18n._('Server Error'),
                    description: ckan.i18n._(
                        'An unknown server error has occurred.'
                    ),
                });
                throw error;
            });

    const handleFileSelected = async (inputFile) => {
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
            url: file._descriptor.name,
        });
    };

    const uploadOptions = [
        {
            name: 'ResourceForkButton',
            label: ckan.i18n._('Import from another dataset'),
            icon: 'fa-copy',
            onClick: (e) => {
                setHiddenInputs('resource', {});
                e.preventDefault();
            },
        },
    ];

    return (
        <div
            data-testid="ResourceForkerComponent"
        >
            <div className="btn-group">
                {uploadOptions.map((option) => (
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
    );
}
