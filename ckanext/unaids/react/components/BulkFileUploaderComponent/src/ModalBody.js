import React from 'react';
import { Promise } from 'bluebird';
import axios from 'axios';
import FileUploader, { dropzoneTypes } from './FileUploader';
import { Client } from 'giftless-client';
import ProgressBar from './ProgressBar';

export default function ModalBody({
    modalElementId, lfsServer, maxResourceSize,
    orgId, datasetName, defaultFields, existingCoreResources,
    existingExtraResources, missingCoreResources,
    pendingFiles, setPendingFiles,
    uploadInProgress, setUploadInProgress,
    uploadsComplete, setUploadsComplete,
    networkError, setNetworkError
}) {

    const setFileProgress = (pendingFileIndex, loaded, total) => {
        let _pendingFiles = [...pendingFiles];
        _pendingFiles[pendingFileIndex].progress = { loaded, total };
        setPendingFiles(_pendingFiles);
    }
    const setFileUploadAction = (pendingFileIndex, uploadAction) => {
        let _pendingFiles = [...pendingFiles];
        _pendingFiles[pendingFileIndex].uploadAction = uploadAction;
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
            { scopes: `obj:${orgId}/${datasetName}/*:write` },
            { withCredentials: true }
        )
            .then(res => res.data.result.token)
            .catch(error => handleNetworkError(
                ckan.i18n._('Authorisation Error'), error
            ))
    const uploadFile = (client, index, localFile, setFileProgress) =>
        client.upload(
            localFile, orgId, datasetName,
            ({ loaded, total }) =>
                setFileProgress(index, loaded, total + 1)
        ).catch(error => handleNetworkError(
            ckan.i18n._('File Upload Error'), error
        ));
    const createOrUpdateResource = (action, localFile, extraFields) =>
        axios.post(
            `/api/3/action/${action}`,
            {
                package_id: datasetName,
                url_type: 'upload',
                name: localFile._descriptor.name,
                sha256: localFile._computedHashes.sha256,
                size: localFile._descriptor.size,
                url: localFile._descriptor.name,
                lfs_prefix: `${orgId}/${datasetName}`,
                ...defaultFields, ...extraFields
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
                const { ckanAction, ckanDataDict } =
                    file.uploadAction ? JSON.parse(file.uploadAction) : extraResource;
                await createOrUpdateResource(ckanAction, localFile, ckanDataDict);
                setFileProgress(index, 100, 100);
            }
        }).then(() => setUploadsComplete(true));
    }

    const updateResourcesOptions =
        [
            ...existingCoreResources,
            ...existingExtraResources
        ].map(x => ({
            optionLabel: x.name,
            ckanAction: 'resource_patch',
            ckanDataDict: {
                id: x.id,
                name: x.name,
                resource_type: x.resource_type
            }
        }));
    const createResourcesOptions =
        missingCoreResources.map(x => ({
            optionLabel: x.name,
            ckanAction: 'resource_create',
            ckanDataDict: {
                name: x.name,
                resource_type: x.resource_type
            }
        }))
    const extraResource = {
        optionLabel: ckan.i18n._('Extra Resource'),
        ckanAction: 'resource_create',
        ckanDataDict: {}
    };
    const uploadActionAlreadyTaken = (uploadAction) => {
        if ([undefined, JSON.stringify(extraResource)].includes(uploadAction)) {
            return false;
        } else {
            return pendingFiles
                .filter(x => x.uploadAction === uploadAction)
                .length > 1
        }
    }

    function PendingFilesTable() {
        const label = (file, index) => (
            <>
                <div>
                    <span>{file.name}</span>
                </div>
                {file.error &&
                    <p className="label label-danger">{file.error}</p>
                }
            </>
        )
        const progressBar = file => !file.error && file.progress &&
            <ProgressBar uploadProgress={file.progress} />

        const fileUploadActionSelector = (file, index) => {
            const selectOptions = options =>
                options.map(x => {
                    const uploadAction = JSON.stringify(x);
                    return <option
                        key={uploadAction}
                        value={uploadAction}
                        data-testid="select-option"
                    >{x.optionLabel}</option>
                })
            return (
                <>
                    <select
                        data-testid="uploadActionSelector"
                        onChange={e => setFileUploadAction(index, e.target.value)}
                        value={file.uploadAction || JSON.stringify(extraResource)}
                    >
                        {
                            updateResourcesOptions.length &&
                            <optgroup label={ckan.i18n._('Overwrite Existing Resource')}>
                                {selectOptions(updateResourcesOptions)}
                            </optgroup>
                        }
                        <optgroup label={ckan.i18n._('Upload new resource')}>
                            {
                                createResourcesOptions.length &&
                                <>
                                    {selectOptions(createResourcesOptions)}
                                    <option disabled>----------</option>
                                </>
                            }
                            {selectOptions([extraResource])}
                        </optgroup>
                    </select>
                    {
                        uploadActionAlreadyTaken(file.uploadAction) &&
                        <span className="label label-danger">{ckan.i18n._('Duplicate option selected')}</span>
                    }
                </>
            )
        }
        return (
            <table className="table" data-testid="PendingFilesTable">
                <tbody>
                    {pendingFiles.map((file, index) => (
                        <tr key={index}>
                            <td width={20}><i className="fa fa-file"></i></td>
                            <td>{label(file, index)}</td>
                            <td width={200}>
                                {uploadInProgress
                                    ? progressBar(file)
                                    : fileUploadActionSelector(file, index)
                                }
                            </td>
                            <td width={20}>
                                {!file.progress &&
                                    <i
                                        className="fa fa-close text-danger remove-file-btn"
                                        onClick={() => removeFileFromPendingFiles(index)}
                                    ></i>
                                }
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        )
    }
    function UploadButton() {
        const thereArePendingFiles = pendingFiles.length > 0;
        const noDuplicateUploadActionsSet = pendingFiles
            .map(file => uploadActionAlreadyTaken(file.uploadAction))
            .filter(x => x).length === 0;
        const enableButton = ![
            thereArePendingFiles,
            noDuplicateUploadActionsSet
        ].includes(false);
        return (
            <button
                type="button"
                className={`btn btn-default ${enableButton ? '' : 'disabled'}`}
                data-testid="UploadFilesButton"
                onClick={enableButton ? uploadFiles : null}
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
                <FileUploader {...{
                    modalElementId, maxResourceSize, setPendingFiles,
                    dropzoneType: dropzoneTypes.modalDropzone
                }} />
                <PendingFilesTable />
                <UploadButton />
            </>
        )
    }

}
