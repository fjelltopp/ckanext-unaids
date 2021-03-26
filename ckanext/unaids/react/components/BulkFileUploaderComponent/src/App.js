import React, { useState } from 'react';
import { Promise } from 'bluebird';
import axios from 'axios';
import FileUploader from './FileUploader';

export default function App({ lfsServer, orgId, datasetId, defaultFields }) {

    const [uploadsInProgress, setUploadsInProgress] = useState([]);

    const createResources = files => {
        Promise.mapSeries(files, file => (
            axios({
                method: 'POST',
                url: '/api/3/action/resource_create',
                data: {
                    package_id: datasetId,
                    url_type: 'upload',
                    name: file.name,
                    sha256: file.sha256,
                    size: file.size,
                    url: file.name,
                    lfs_prefix: `${orgId}/${datasetId}`,
                    ...defaultFields
                },
                withCredentials: true
            })
        )).then(() => window.location.replace(window.location.pathname))
    };

    return (
        uploadsInProgress.length
            ? (
                <ul className="list-group">
                    <li className="list-group-item list-group-item-success">
                        <i className="fa fa-spinner fa-spin"></i>
                        &nbsp;
                        {ckan.i18n._('Upload in progress')}
                    </li>
                    {uploadsInProgress.map((file, index) => (
                        <li className="list-group-item" key={index}>
                            <i className="fa fa-file fa-xs"></i>
                            <span> {file.name} </span>
                        </li>
                    ))}
                </ul>
            )
            : (
                <FileUploader {...{
                    lfsServer, orgId, datasetId,
                    createResources, setUploadsInProgress
                }} />
            )
    );
}
