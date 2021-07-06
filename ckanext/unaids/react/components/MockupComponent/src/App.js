import React, { useState } from 'react';
import FileUploader from './FileUploader';
import BootstrapModal from './BootstrapModal';

export default function App({ lfsServer, maxResourceSize, orgId, datasetName, defaultFields }) {
    const [draggedFiles, setDraggedFiles] = useState([]);
    const [activeResourceType, setActiveResourceType] = useState([]);

    const resourceTypes = [
        'Geographic Data',
        'ANC Data',
        'ART Data',
        'Population Data',
        'HIV Testing Data'
    ];

    return (
        <>
            {resourceTypes.map(resouceType => <FileUploader {...{
                resouceType, setDraggedFiles, setActiveResourceType
            }} />)}
            <BootstrapModal {...{
                resourceTypes, activeResourceType, draggedFiles
            }} />
        </>
    )

}
