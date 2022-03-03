import React from 'react';
import Modal from './Modal';

export default function App({ datasetReleases }) {

    const actions = [
        {
            type: 'restore',
            title: ckan.i18n._('Make release the latest version'),
            icon: 'fa-refresh',
        },
        {
            type: 'edit',
            title: ckan.i18n._('Edit Release'),
            icon: 'fa-pencil'
        },
        {
            type: 'delete',
            title: ckan.i18n._('Delete Release'),
            icon: 'fa-trash'
        }
    ];

    return (
        <>
            <table>
                <thead>
                    <tr>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {datasetReleases.map(release => (
                        <tr>
                            <td>
                                <div className="row vertical-align">
                                    <div className="col-xs-12 col-md-6">
                                        <div className="release-title"><h4><i className="fa fa-tag text-muted fa-fw"></i><a href={release.url}>{release.name}</a></h4></div>
                                        {release.notes &&
                                            <div className="text-muted release-notes">{release.notes}</div>
                                        }
                                        <div className="release-creator">
                                            {ckan.i18n._('Created by')}
                                            <span> </span>
                                            <span dangerouslySetInnerHTML={{
                                                __html: release.creator_name_as_raw_html
                                            }} />
                                        </div>
                                    </div>
                                    <div className="col-md-3">
                                        <div className="release-date">
                                            <span title={release.created_datetime_string}>{release.created_datetime_ago_string}</span>
                                        </div>
                                    </div>
                                    <div className="col-xs-12 col-md-3">
                                        <div className="release-actions">
                                            <div className="btn-group btn-group-xs">
                                                {actions.map(action =>
                                                    <button
                                                        type="button"
                                                        className="btn btn-default"
                                                        data-toggle="modal"
                                                        data-target={`#${action.type}_release_${release.id}`}
                                                        title={action.title}
                                                    ><i className={`fa ${action.icon}`}></i></button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table >
            {datasetReleases.map(release =>
                actions.map(action => <Modal {...{ release, action }} />)
            )}
        </>
    )

}
