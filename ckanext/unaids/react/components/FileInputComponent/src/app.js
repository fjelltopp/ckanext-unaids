import React, { useState, useEffect } from 'react';
import axios from "axios";
import ProgressBar from "../components/ProgressBar";
import DisplayUploadedFile from "../components/DisplayUploadedFile";
import UrlUploader from "../components/UrlUploader";
import FileUploader from "../components/FileUploader";
import HiddenFormInputs from "../components/HiddenFormInputs";

export default function App({ lfsServer, orgId, datasetId, existingResourceData }) {

    const defaultUploadProgress = { loaded: 0, total: 0 };
    const [authToken, setAuthToken] = useState();
    const [uploadMode, setUploadMode] = useState();
    const [uploadProgress, setUploadProgress] = useState(defaultUploadProgress);
    const [uploadfileName, setUploadFileName] = useState();
    const [linkUrl, setLinkUrl] = useState();
    const [hiddenInputs, _setHiddenInputs] = useState();
    const [uploadFailed, setUploadFailed] = useState(false);

    const setHiddenInputs = (newUploadMode, metadata) => {
        setUploadMode(newUploadMode);
        _setHiddenInputs(() => {
            switch (newUploadMode) {
                case 'file':
                    return {
                        url_type: 'upload',
                        lfs_prefix: [orgId, datasetId].join('/'),
                        sha256: metadata.sha256,
                        size: metadata.size,
                        url: metadata.url
                    }
                case 'url':
                    const fileFormatField = document.getElementById('field-format');
                    if (fileFormatField) fileFormatField.value = 'url';
                    return {
                        url_type: null,
                        lfs_prefix: null,
                        sha256: null,
                        size: null,
                        // url field is handled by input field in UI
                    }
                default:
                    return {
                        url_type: null,
                        lfs_prefix: null,
                        sha256: null,
                        size: null,
                        url: null
                    }
            }
        });
    }

    useEffect(() => {
        axios.post(
            '/api/3/action/authz_authorize',
            { scopes: `obj:ckan/${datasetId}/*:write` },
            { withCredentials: true }
        )
            .then(res => setAuthToken(res.data.result.token))
            .catch(error => {
                console.log(`authz_authorize error: ${error}`);
                setAuthToken('error')
            })
        const data = existingResourceData;
        if (data.urlType === 'upload') {
            // resource already has a file
            setUploadFileName(data.fileName)
            setUploadProgress({
                ...defaultUploadProgress,
                loaded: data.size,
                total: data.size
            })
            setHiddenInputs('file', {
                sha256: data.sha256,
                size: data.size
            })
        } else if (data.url) {
            // resource already has a url
            setHiddenInputs('url', {})
            setLinkUrl(data.url)
        } else {
            // resource has no file or link
            setHiddenInputs(null, {});
        };
    }, []);

    if (!authToken) {
        return ckan.i18n._('Loading');
    } else if (authToken === 'error') {
        return ckan.i18n._('Authentication Error: Failed to load file uploader');
    }

    if (uploadFailed) return (
        <div className="alert alert-danger">
            <p><i className="fa fa-exclamation-triangle"></i> Upload Error</p>
            <p>Please refresh this page and try again</p>
        </div>
    )

    function UploaderComponent() {
        const resetComponent = e => {
            setHiddenInputs(null, {});
            setUploadProgress(defaultUploadProgress);
            e.preventDefault();
        }
        if (uploadProgress.total) {
            const loaded =
                uploadProgress.loaded == uploadProgress.total
                && uploadfileName;
            return (
                loaded
                    ? <DisplayUploadedFile {...{
                        fileName: uploadfileName,
                        resetComponent: resetComponent
                    }} />
                    : <ProgressBar {...{ uploadProgress }} />
            )
        }
        return (
            [null, 'file'].includes(uploadMode)
                ? <FileUploader {...{
                    lfsServer, orgId, datasetId, authToken,
                    setUploadProgress, setUploadFileName, setHiddenInputs,
                    setUploadFailed
                }} />
                : <UrlUploader {...{ linkUrl, resetComponent }} />
        )
    }
    return (
        <>
            <UploaderComponent />
            <HiddenFormInputs {...{ hiddenInputs }} />
        </>
    )

}
