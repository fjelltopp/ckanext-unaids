import React, { useState } from 'react';
// import Fuse from 'fuse.js'
import Modal from './Modal';
import FileUploader, { dropzoneTypes } from './FileUploader';

export default function App(props) {

    const updateResourcesOptions =
        [
            ...props.existingCoreResources,
            ...props.existingExtraResources
        ].map(x => ({
            optionLabel: x.name,
            fileName: (x.url || '').split('/').pop(),
            ckanAction: 'resource_patch',
            ckanDataDict: {
                id: x.id,
                name: x.name,
                resource_type: x.resource_type
            }
        }));
    const createResourcesOptions =
        props.missingCoreResources.map(x => ({
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

    const [pendingFiles, setPendingFiles] = useState([]);
    const [uploadInProgress, setUploadInProgress] = useState(false);
    const [uploadsComplete, setUploadsComplete] = useState(false);
    const [networkError, setNetworkError] = useState(false);

    const getDefaultUploadAction = file => {
        // disabled until we figure out a nicer algorithm
        // const fuzzySearchResults = new Fuse(
        //     updateResourcesOptions,
        //     {
        //         // https://bit.ly/3BTLnWd
        //         includeScore: true,
        //         findAllMatches: false,
        //         keys: ['fileName'],
        //         threshold: 0.3
        //     }
        // ).search(file.name);
        // let defaultUploadAction = extraResource;
        // if (fuzzySearchResults.length === 1) {
        //     defaultUploadAction = fuzzySearchResults[0].item;
        // } else if (fuzzySearchResults.length > 1) {
        //     const firstResult = fuzzySearchResults[0];
        //     const secondResult = fuzzySearchResults[1];
        //     const scroreDiff = firstResult.score - secondResult.score;
        //     if (scroreDiff > 0.05) {
        //         defaultUploadAction = fuzzySearchResults[0].item;
        //     }
        // }
        // return defaultUploadAction;
        const exactMatches = updateResourcesOptions.filter(
            x => x.fileName === file.name
        );
        switch (exactMatches.length) {
            case 1:
                return exactMatches[0];
            default:
                return extraResource;
        }
    }

    const updatedProps = {
        ...props,
        pendingFiles, setPendingFiles,
        uploadInProgress, setUploadInProgress,
        uploadsComplete, setUploadsComplete,
        networkError, setNetworkError,
        updateResourcesOptions, createResourcesOptions,
        extraResource, getDefaultUploadAction
    }

    return (
        <>
            <Modal {...{ ...updatedProps }} />
            <FileUploader {...{
                ...updatedProps,
                dropzoneType: dropzoneTypes.fullPageDropzone
            }} />
        </>
    )

}
