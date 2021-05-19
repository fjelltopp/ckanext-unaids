import React from 'react';

export default function DisplayUploadedFile({
    fileName, resetComponent
}) {

    return (
        <h3>
            <i className="fa fa-file"></i>
            {` ${fileName} `}
            <i
                className="fa fa-close text-danger"
                style={{ cursor: 'pointer' }}
                title={ckan.i18n._('Remove')}
                onClick={resetComponent}
                data-testid="RemoveFileButton"
            ></i>
        </h3>
    )

}
