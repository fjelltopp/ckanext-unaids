import React, { useState, useEffect } from 'react';
import { Promise } from 'bluebird';
import axios from 'axios';
import FileUploader from './FileUploader';
import { Client } from 'giftless-client';
import ProgressBar from './ProgressBar';

export default function App({ lfsServer, maxResourceSize, orgId, datasetId, defaultFields }) {

    const [pendingFiles, setPendingFiles] = useState([]);
    const [uploadInProgress, setUploadInProgress] = useState(false);
    const [uploadsComplete, setUploadsComplete] = useState(false);
    const [networkError, setNetworkError] = useState(false);

    const setFileProgress = (pendingFileIndex, loaded, total) => {
        let _pendingFiles = [...pendingFiles];
        _pendingFiles[pendingFileIndex].progress = { loaded, total };
        setPendingFiles(_pendingFiles);
    }
    const removeFileFromPendingFiles = index => {
        let _pendingFiles = [...pendingFiles];
        _pendingFiles.splice(index, 1)
        setPendingFiles(_pendingFiles);
    }
    const handleNetworkError = (errorType, error) => {
        setNetworkError(errorType);
        console.error(error);
    };

    const getAuthToken = () =>
        axios.post(
            '/api/3/action/authz_authorize',
            { scopes: `obj:${orgId}/${datasetId}/*:write` },
            { withCredentials: true }
        )
            .then(res => res.data.result.token)
            .catch(error => handleNetworkError(
                ckan.i18n._('Authorisation Error'), error
            ))
    const uploadFile = (client, index, localFile, setFileProgress) =>
        client.upload(
            localFile, orgId, datasetId,
            ({ loaded, total }) =>
                setFileProgress(index, loaded, total + 1)
        ).catch(error => handleNetworkError(
            ckan.i18n._('File Upload Error'), error
        ));
    const createResource = localFile =>
        axios.post(
            '/api/3/action/resource_create',
            {
                package_id: datasetId,
                url_type: 'upload',
                name: localFile._descriptor.name,
                sha256: localFile._computedHashes.sha256,
                size: localFile._descriptor.size,
                url: localFile._descriptor.name,
                lfs_prefix: `${orgId}/${datasetId}`,
                ...defaultFields
            },
            { withCredentials: true }
        ).catch(error => handleNetworkError(
            ckan.i18n._('Resource Create Error'), error
        ));

    const uploadFiles = () => {
        setUploadInProgress(true);
        Promise.mapSeries(pendingFiles, async (file, index) => {
            if (networkError) return;
            const authToken = await getAuthToken();
            const client = new Client(lfsServer, authToken, ['basic']);
            if (!file.error) {
                const localFile = data.open(file);
                setFileProgress(index, 0, 100);
                await uploadFile(client, index, localFile, setFileProgress);
                await createResource(localFile);
                setFileProgress(index, 100, 100);
            }
        }).then(() => setUploadsComplete(true));
    }

    function PendingFilesTable() {
        const label = (file, index) => (
            <>
                <div>
                    <span>{file.name}</span>
                    {!file.progress &&
                        <i
                            className="fa fa-close text-danger remove-file-btn"
                            onClick={() => removeFileFromPendingFiles(index)}
                        ></i>
                    }
                </div>
                {file.error &&
                    <p className="label label-danger">{file.error}</p>
                }
            </>
        )
        const progressBar = file => !file.error && file.progress &&
            <ProgressBar uploadProgress={file.progress} />
        return (
            <table className="table">
                <tbody>
                    {pendingFiles.map((file, index) => (
                        <tr key={index}>
                            <td width={20}><i className="fa fa-file"></i></td>
                            <td width={400}>{label(file, index)}</td>
                            <td>{progressBar(file)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        )
    }
    function UploadButton() {
        const classes = `btn btn-default ${!pendingFiles.length && 'disabled'}`;
        return (
            <button
                type="button"
                className={classes}
                data-testid="UploadFilesButton"
                onClick={pendingFiles.length ? uploadFiles : null}
            >
                <i className="fa fa-upload"></i>
                {ckan.i18n._('Upload Files')}
            </button>
        )
    }
    function FinishUploadButton() {
        const handleClick = () =>
            window.location.replace(window.location.pathname)
        return (
            <button
                type="button"
                className="btn btn-default"
                onClick={handleClick}
            >
                <i className="fa fa-check"></i>
                {ckan.i18n._('Finish')}
            </button>
        )
    }
    const Header = (label, color, icon) => (
        <h1 className={`text-center ${color}`}>
            <i className={`fa ${icon}`}></i>
            <span>{label}</span>
        </h1>
    )

    if (networkError) {
        return (
            <>
                {Header(
                    networkError,
                    'text-danger',
                    'fa-exclamation-triangle'
                )}
                <hr />
                <h3 className="text-center">
                    {ckan.i18n._('Please refresh this page and try again')}
                </h3>
            </>
        )
    } else if (uploadsComplete) {
        return (
            <>
                {Header(
                    'Uploads Complete',
                    'text-success',
                    'fa-check-circle'
                )}
                <PendingFilesTable />
                <FinishUploadButton />
            </>
        )
    } else if (uploadInProgress) {
        return (
            <>
                {Header(
                    'Uploading...',
                    'text-muted',
                    'fa-spinner fa-spin'
                )}
                <PendingFilesTable />
                <UploadButton />
            </>
        )
    } else {
        return (
            <>
                <FileUploader {...{ maxResourceSize, setPendingFiles }} />
                <PendingFilesTable />
                <UploadButton />
            </>
        )
    }

}
