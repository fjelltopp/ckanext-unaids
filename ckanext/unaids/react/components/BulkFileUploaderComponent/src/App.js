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

        function strDiff(str1, str2){
            // Get all chars that match at the start of both strings
            var openingMatch = "";
            for(let x = 0; x < str1.length; x++){
                if(str1.charAt(x) == str2.charAt(x)) openingMatch += str1.charAt(x);
                else break;
            }

            // Get all chars that match at the end of both strings
            var str1Reversed = str1.split("").reverse().join("");
            var str2Reversed = str2.split("").reverse().join("");
            var endingMatch = "";
            for(let x = 0; x < str1.length; x++){
                if(str1Reversed.charAt(x) == str2Reversed.charAt(x)) endingMatch += str1Reversed.charAt(x);
                else break;
            }
            endingMatch = endingMatch.split("").reverse().join("");

            // Get the middle non-matching part of each string
            var str1Difference = str1.slice(openingMatch.length, str1.length-endingMatch.length).trim();
            var str2Difference = str2.slice(openingMatch.length, str2.length-endingMatch.length)

            return [openingMatch, endingMatch, str1Difference, str2Difference];
        }

        function filenameMatch(filename1, filename2){
            /* Matches where filenames begin and end with the same three (or more chars) and
               any middle non-matching parts consist only of the following inserted or swapped:
               - a number
               - a number in parenthesis
               - a number after a hyphen
            */
            const regexp = /^$|^[\(-]? ?[0-9]*\)?$/;
            const matches = strDiff(filename1, filename2);
            const completeMatch = matches[0] == matches[1] && matches[0];
            const openingMatch = matches[0].length >= 3;
            const closingMatch = matches[1].length >= 3;
            const regexMatch = matches[2].match(regexp) != null && matches[3].match(regexp) != null;
            const match = completeMatch || openingMatch && closingMatch && regexMatch;
            return match;
        }

        // Find all matched resources
        var matchedResources = []
        for(let x = 0; x<updateResourcesOptions.length; x++){
            if(filenameMatch(file.name, updateResourcesOptions[x].fileName)){
                matchedResources.push(updateResourcesOptions[x]);
            }
        }

        // Set the default upload action only if there is a single matching resource
        var defaultUploadAction = extraResource;
        if(matchedResources.length == 1){
            defaultUploadAction = matchedResources[0];
        }

        return defaultUploadAction;

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
