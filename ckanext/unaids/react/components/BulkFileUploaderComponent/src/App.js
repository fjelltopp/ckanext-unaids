import React, { useState } from 'react';
import Modal from './Modal';
import FileUploader, { dropzoneTypes } from './FileUploader';

export default function App(props) {

    const [pendingFiles, setPendingFiles] = useState([]);
    const [uploadInProgress, setUploadInProgress] = useState(false);
    const [uploadsComplete, setUploadsComplete] = useState(false);
    const [networkError, setNetworkError] = useState(false);
    const updatedProps = {
        ...props,
        pendingFiles, setPendingFiles,
        uploadInProgress, setUploadInProgress,
        uploadsComplete, setUploadsComplete,
        networkError, setNetworkError
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
