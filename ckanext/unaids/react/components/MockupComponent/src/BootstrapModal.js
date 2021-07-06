import React from 'react';

export default function BootstrapModal({ resourceTypes, activeResourceType, draggedFiles }) {
    const generalDataType = 'Extra Resource';

    const takenResourceTypes = [];
    const getSelectValue = () => {
        if (draggedFiles.length === 1) {
            if (!takenResourceTypes.includes(activeResourceType)) {
                takenResourceTypes.push(activeResourceType)
                return activeResourceType;
            }
        }
        return generalDataType;
    }

    const onchange = e => {
        if (takenResourceTypes.includes(e.target.value)) {
            alert(`${e.target.value} is already taken by another resource`);
        }
    }

    return (
        <div className="modal fade">
            <div className="modal-dialog">
                <div className="modal-content">
                    <div className="modal-header">
                        <button type="button" className="close" data-dismiss="modal">&times;</button>
                        <h4 className="modal-title">Upload Resources</h4>
                    </div>
                    <div className="modal-body">
                        <ul className="list-group">
                            {draggedFiles.map(file => (
                                <li key={file.name} className="list-group-item">
                                    <span>Upload </span>
                                    <span className="badge">{file.name}</span>
                                    <span> as </span>
                                    <span>
                                        <select defaultValue={getSelectValue()} onChange={onchange}>
                                            {resourceTypes.map(x => <option key={x}>{x}</option>)}
                                            <option>{generalDataType}</option>
                                        </select>
                                        <span class="label pull-right">Population Data is selected twice</span>                                        
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default" data-dismiss="modal">Cancel</button>
                        <button type="button" className="btn btn-primary"><i className="fa fa-upload"></i> Upload Files</button>
                    </div>
                </div>
            </div>
        </div>
    )
}
