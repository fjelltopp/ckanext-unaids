import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ProgressBar from './ProgressBar';
import DisplayUploadedFile from './DisplayUploadedFile';
import UrlUploader from './UrlUploader';
import FileUploader from './FileUploader';
import HiddenFormInputs from './HiddenFormInputs';

export default function App({ loadingHtml, maxResourceSize, lfsServer, orgId, datasetName, existingResourceData }) {

    const defaultUploadProgress = { loaded: 0, total: 0 };
    const [uploadMode, setUploadMode] = useState();
    const [uploadProgress, setUploadProgress] = useState(defaultUploadProgress);
    const [uploadfileName, setUploadFileName] = useState();
    const [linkUrl, setLinkUrl] = useState();
    const [hiddenInputs, _setHiddenInputs] = useState({});
    const [uploadError, setUploadError] = useState(false);
    const [useEffectCompleted, setUseEffectCompleted] = useState(false);

    const setHiddenInputs = (newUploadMode, metadata) => {
        setUploadMode(newUploadMode);
        _setHiddenInputs(() => {
            switch (newUploadMode) {
                case 'file':
                    return {
                        url_type: 'upload',
                        lfs_prefix: `${orgId}/${datasetName}`,
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
                size: data.size,
                url: data.url
            })
        } else if (data.url) {
            // resource already has a url
            setHiddenInputs('url', {})
            setLinkUrl(data.url)
        } else {
            // resource has no file or link
            setHiddenInputs(null, {});
        };
        setUseEffectCompleted(true);
    }, []);

    if (!useEffectCompleted) {
        return <div dangerouslySetInnerHTML={{ __html: loadingHtml }}></div>
    }

    if (uploadError) return (
        <div className="alert alert-danger">
            <p><i className="fa fa-exclamation-triangle"></i> {uploadError.error}</p>
            <p>
                <span>{uploadError.description}</span>
                <br />
                <span>{ckan.i18n._('Please refresh this page and try again.')}</span>
            </p>
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
            [undefined, null, 'file'].includes(uploadMode)
                ? <FileUploader {...{
                    maxResourceSize, lfsServer, orgId, datasetName,
                    setUploadProgress, setUploadFileName,
                    setHiddenInputs, setUploadError
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
