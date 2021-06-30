import React from 'react';

export default function ProgressBar({ uploadProgress }) {

    const percent = Math.round(
        (uploadProgress.loaded / uploadProgress.total) * 100
    );

    const threashold = 10;
    const preparing = percent < threashold;
    const completed = percent === 100;

    function ProgressLabel() {
        if (preparing) {
            return <i className="fa fa-spinner fa-spin"></i>
        } else if (completed) {
            return ckan.i18n._('Uploaded');
        } else {
            return `${percent}%`;
        }
    }

    return (
        <div className={`form-group controls progress ${!completed && `progress-striped active`}`}>
            <div
                className="progress-bar"
                style={{ width: `${preparing ? threashold : percent}%` }}
            >
                <span><ProgressLabel /></span>
            </div>
        </div>
    )

}
