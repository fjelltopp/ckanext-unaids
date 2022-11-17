import React, { useState, useEffect } from "react";
import axios from "axios";
import ProgressBar from "./ProgressBar";
import DisplayUploadedFile from "./DisplayUploadedFile";
import UrlUploader from "./UrlUploader";
import FileUploader from "./FileUploader";
import ResourceForker from "./ResourceForker";
import HiddenFormInputs from "./HiddenFormInputs";

const getExistingResourceDetails = async (resourceID) => {
    const config = {
        headers: {
            "Content-Type": "application/json",
        },
    };

    let body = JSON.stringify({
        id: resourceID,
    });
    let resourceRespone = await axios.post("/api/3/action/resource_show", body, config);

    body = JSON.stringify({
        name_or_id: resourceRespone.data.result.package_id,
    });
    let datasetRespone = await axios.post("/api/3/action/package_show", body, config);

    return [resourceRespone.data.result, datasetRespone.data.result]
};

export default function App({ loadingHtml, maxResourceSize, lfsServer, orgId, datasetName, existingResourceData }) {
    const defaultUploadProgress = { loaded: 0, total: 0 };
    const [uploadMode, setUploadMode] = useState();
    const [uploadProgress, setUploadProgress] = useState(defaultUploadProgress);
    const [uploadfileName, setUploadFileName] = useState();
    const [linkUrl, setLinkUrl] = useState();
    const [hiddenInputs, _setHiddenInputs] = useState({});
    const [uploadError, setUploadError] = useState(false);
    const [useEffectCompleted, setUseEffectCompleted] = useState(false);
    const [selectedResource, setSelectedResource] = useState({
        resource: null,
        dataset: null,
        synced: null,
    });

    const setHiddenInputs = (newUploadMode, metadata) => {
        setUploadMode(newUploadMode);
        let fileFormatField = document.getElementById("field-format");
        _setHiddenInputs(() => {
            switch (newUploadMode) {
                case "file":
                    return {
                        url_type: "upload",
                        lfs_prefix: `${orgId}/${datasetName}`,
                        sha256: metadata.sha256,
                        size: metadata.size,
                        url: metadata.url,
                        fork_resource: null,
                        fork_activity: null,
                    };
                case "url":
                    if (fileFormatField) fileFormatField.value = "url";
                    return {
                        url_type: null,
                        lfs_prefix: null,
                        sha256: null,
                        size: null,
                        fork_resource: null,
                        fork_activity: null,
                        // url field is handled by input field in UI
                    };
                case "resource":
                    if (fileFormatField) fileFormatField.value = metadata.format;
                    return {
                        url_type: null,
                        lfs_prefix: null,
                        sha256: null,
                        size: null,
                        url: metadata.filename,
                        fork_resource: metadata.fork_resource,
                        fork_activity: metadata.fork_activity || null,
                    };
                default:
                    return {
                        url_type: null,
                        lfs_prefix: null,
                        sha256: null,
                        size: null,
                        url: null,
                        fork_resource: null,
                        fork_activity: null,
                    };
            }
        });
    };

    useEffect(() => {
        const data = existingResourceData;
        if (data.urlType === "upload" && !data.forkResource) {
            // resource already has a file and it is not a forked resource
            setUploadFileName(data.fileName);
            setUploadProgress({
                ...defaultUploadProgress,
                loaded: data.size,
                total: data.size,
            });
            setHiddenInputs("file", {
                sha256: data.sha256,
                size: data.size,
                url: data.url,
            });
        } else if (data.urlType === "upload" && data.forkResource) {
            // resource is an existing forked resource
            setUploadFileName(data.fileName);
            setHiddenInputs("resource", {
                fork_resource: data.forkResource,
            });
            setHiddenInputs("resource", {
                // format: resource.format,
                filename: data.filename,
                fork_resource: data.forkResource,
                fork_activity: data.forkActivity,
            });
            getExistingResourceDetails(data.forkResource).then((response) => {
                setSelectedResource({
                    resource: response[0],
                    dataset: response[1],
                    synced: data.forkSynced,
                });
            });
        } else if (data.url) {
            // resource already has a url
            setHiddenInputs("url", {});
            setLinkUrl(data.url);
        } else {
            // resource has no file or link
            setHiddenInputs(null, {});
        }
        setUseEffectCompleted(true);
    }, []);

    if (!useEffectCompleted) {
        return <div dangerouslySetInnerHTML={{ __html: loadingHtml }}></div>;
    }

    if (uploadError)
        return (
            <div className="alert alert-danger">
                <p>
                    <i className="fa fa-exclamation-triangle"></i> {uploadError.error}
                </p>
                <p>
                    <span>{uploadError.description}</span>
                    <br />
                    <span>{ckan.i18n._("Please refresh this page and try again.")}</span>
                </p>
            </div>
        );

    function UploaderComponent() {
        const resetComponent = (e) => {
            setHiddenInputs(null, {});
            setUploadProgress(defaultUploadProgress);
            e.preventDefault();
        };
        if (uploadProgress.total) {
            const loaded = uploadProgress.loaded == uploadProgress.total && uploadfileName;
            return loaded ? (
                <DisplayUploadedFile
                    {...{
                        fileName: uploadfileName,
                        resetComponent: resetComponent,
                    }}
                />
            ) : (
                <ProgressBar {...{ uploadProgress }} />
            );
        } else if (uploadMode === "url") {
            return <UrlUploader {...{ linkUrl, resetComponent }} />;
        } else if (uploadMode === "resource") {
            return (
                <ResourceForker
                    selectedResource={selectedResource}
                    setSelectedResource={setSelectedResource}
                    setHiddenInputs={setHiddenInputs}
                />
            );
        } else if (uploadMode === "file" || uploadMode === null) {
            return (
                <FileUploader
                    {...{
                        maxResourceSize,
                        lfsServer,
                        orgId,
                        datasetName,
                        setUploadProgress,
                        setUploadFileName,
                        setHiddenInputs,
                        setUploadError,
                    }}
                />
            );
        } else {
            return (
                <div className="alert alert-danger">
                    <p>
                        <i className="fa fa-exclamation-triangle"></i> {ckan.i18n._("Resource Create Error")}
                    </p>
                    <p>
                        <span>{ckan.i18n._("Please refresh this page and try again.")}</span>
                    </p>
                </div>
            );
        }
    }
    return (
        <React.StrictMode>
            <UploaderComponent />
            <HiddenFormInputs {...{ hiddenInputs }} />
        </React.StrictMode>
    );
}
