import React from 'react';

export default function ProgressBar({ uploadProgress }) {

    const percent = Math.round(
        (uploadProgress.loaded / uploadProgress.total) * 100
    );

    const threashold = 10;
    const preparing = percent < threashold;

    return (
        <div className="form-group controls progress progress-striped active">
            <div
                className="progress-bar"
                style={{ width: `${preparing ? threashold : percent}%` }}
            >
                <span>{preparing ? ckan.i18n._('Loading') : `${percent}%`}</span>
            </div>
        </div>
    )

}
