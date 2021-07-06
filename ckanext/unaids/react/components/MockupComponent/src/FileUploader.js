import React, { useState, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';

export default function FileUploader({ resouceType, setDraggedFiles, setActiveResourceType }) {

    const baseStyle = {
        backgroundColor: ''
    };

    const activeStyle = {
        backgroundColor: '#2196f3'
    };

    const acceptStyle = {
        backgroundColor: '#d6e9c6'
    };

    const rejectStyle = {
        // backgroundColor: '#ff1744'
    };

    function StyledDropzone(props) {
        const {
            getRootProps,
            isDragActive,
            isDragAccept,
            isDragReject
        } = useDropzone({
            //maxFiles: 1,
            onDropAccepted: React.useCallback(files => {
                setActiveResourceType(resouceType);
                setDraggedFiles(files);
                console.log(files);
                $('#MockupComponent .modal').modal('show');
            }),
        });

        const style = useMemo(() => ({
            ...baseStyle,
            ...(isDragActive ? activeStyle : {}),
            ...(isDragAccept ? acceptStyle : {}),
            ...(isDragReject ? rejectStyle : {})
        }), [
            isDragActive,
            isDragReject,
            isDragAccept
        ]);

        return (
            <li {...getRootProps({ style })} className="resource-item" data-id="26eab931-2c05-4b7b-baf1-cbc9a866b2a7">
                <div className="resource-title">
                    <div className="resource-title">
                        <a className="heading" href="/inputs-unaids-estimates/cote-d-ivoire-inputs-unaids-estimates-2021/resource/26eab931-2c05-4b7b-baf1-cbc9a866b2a7" title="Geographic Data">
                            {resouceType}<span className="format-label" property="dc:format" data-format="geojson">GeoJSON</span>
                        </a>
                    </div>
                </div>
                <p className="description" title="June 9, 2021, 10:31 (UTC)">
                    {
                        isDragActive
                            ? <><i className="fa fa-upload"></i> Update resource</>
                            : 'Last modified: 3 weeks ago'
                    }
                </p>
                <div className="dropdown btn-group">
                    <a href="#" className="btn btn-primary dropdown-toggle" data-toggle="dropdown">
                        <i className="fa fa-share"></i>
                        Explore
                        <span className="caret"></span>
                    </a>
                    <ul className="dropdown-menu">
                        <li>
                            <a href="/inputs-unaids-estimates/cote-d-ivoire-inputs-unaids-estimates-2021/resource/26eab931-2c05-4b7b-baf1-cbc9a866b2a7">
                                <i className="fa fa-bar-chart-o"></i>
                                Preview
                            </a>
                        </li>
                        <li>
                            <a href="http://dev-adr/dataset/a1130ad9-a534-4466-8f15-10ca020e0609/resource/26eab931-2c05-4b7b-baf1-cbc9a866b2a7/download/geographic.geojson" className="resource-url-analytics" target="_blank">
                                <i className="fa fa-arrow-circle-o-down"></i>
                                Download
                            </a>
                        </li>
                        <li>
                            <a href="/inputs-unaids-estimates/cote-d-ivoire-inputs-unaids-estimates-2021/resource/26eab931-2c05-4b7b-baf1-cbc9a866b2a7/edit">
                                <i className="fa fa-pencil-square-o"></i>
                                Edit
                            </a>
                        </li>
                        <li>
                            <a href="/inputs-unaids-estimates/cote-d-ivoire-inputs-unaids-estimates-2021/resource/26eab931-2c05-4b7b-baf1-cbc9a866b2a7/delete" data-module="confirm-action" data-module-content="Are you sure you want to delete this resource?">
                                <i className="fa fa-times"></i>
                                Delete
                            </a>
                        </li>
                    </ul>
                </div>
            </li>
        );
    }

    return <StyledDropzone />

}
