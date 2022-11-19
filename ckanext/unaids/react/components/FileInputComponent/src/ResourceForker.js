import axios from 'axios';
import React, { useEffect, useState, useRef } from 'react';
import parse from 'html-react-parser';

const getSearchResults = (searchQuery, setSearchResults) => {
    if (searchQuery) {
        const body = {
            q: searchQuery,
        };

        const config = {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        };
        axios
            .post('/api/3/action/resource_autocomplete', body, config)
            .then((response) => {
                setSearchResults(response.data.result);
            })
            .catch((error) => console.error(error));
    }
};

const checkResourceAccess = (packageID, resourceID, setResourceAccess) => {
    const body = {
        package_id: packageID,
        resource_id: resourceID,
    };

    const config = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    axios
        .post('/api/3/action/restricted_check_access', body, config)
        .then((response) => {
            if (response.status == 200) {
                setResourceAccess(response.data.result.success);
            } else {
                console.log(`Error: Request failed with status code ` + response.status);
                setResourceAccess(false);
            }
        })
        .catch((error) => {
            console.log(error);
            setResourceAccess(false);
        });
};

const markQuerySubstring = (string, searchQuery) => {
    let newString = string;
    searchQuery.split(' ').map((word) => {
        if (word.length > 0) {
            newString = newString.replaceAll(RegExp(word, 'gi'), `<mark>$&</mark>`);
        }
    });
    return parse(newString);
};

const SearchBar = ({ searchQuery, setSearchQuery }) => {
    const searchInput = useRef(null);

    useEffect(() => {
        searchInput.current.focus();
    }, []);

    return (
        <div className="field">
            <label id="resource-search-label" htmlFor="resource-search" className="btn-search">
                <i className={`fa fa-search`}></i>
            </label>
            <input
                type="text"
                className="form-control"
                aria-label="Search existing resources"
                placeholder="Search existing resources"
                name="resource-search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                    e.key === 'Enter' && e.preventDefault();
                }} // DEVNOTE - not IE compatible
                ref={searchInput}
                data-testid="resource-fork-search-bar"
            />
            <button type="reset" className="btn-reset" onClick={() => setSearchQuery('')}>
                <i className={`fa fa-close`}></i>
            </button>
        </div>
    );
};

const DatasetGroup = ({ dataset, setResourceAndMetadata, searchQuery, currentResourceID }) => {
    const [isCollapsed, setIsCollapsed] = useState(true);

    const markQuerySubstring = (string, searchQuery) => {
        let newString = string;
        searchQuery.split(' ').map((word) => {
            if (word.length > 0) {
                newString = newString.replaceAll(RegExp(word, 'gi'), `<mark>$&</mark>`);
            }
        });
        return parse(newString);
    };

    const getFilteredResources = (resources, searchQuery) => {
        return resources.filter((resource) => {
            return searchQuery
                .toLowerCase()
                .split(' ')
                .filter((word) => word.length > 0)
                .map((word) => resource.name.toLowerCase().includes(word))
                .some((x) => x == true);
        });
    };

    const removeSelfResource = (resources) => {
        return resources.filter((resource) => {
            return resource.id !== currentResourceID;
        });
    };

    const resourcesWithoutSelf = removeSelfResource(dataset.resources);

    return (
        <div className="panel">
            <div className="panel-heading" onClick={() => setIsCollapsed(!isCollapsed)}>
                <p className="heading">{markQuerySubstring(dataset.title, searchQuery)}</p>
                <p className="description">
                    <strong>
                        {markQuerySubstring(dataset.owner_org, searchQuery)}
                        &ensp;|&ensp;
                    </strong>
                    {markQuerySubstring(dataset.name, searchQuery)}
                    <span className="badge">
                        {resourcesWithoutSelf.length} resources&ensp;
                        {resourcesWithoutSelf.length > 0 &&
                            (isCollapsed ? <i className={`fa fa-chevron-down`}></i> : <i className={`fa fa-chevron-up`}></i>)}
                    </span>
                </p>
            </div>
            {resourcesWithoutSelf.length > 0 && !isCollapsed && (
                <ul className="panel-body">
                    {resourcesWithoutSelf.map((resource) => (
                        <ResourceButton
                            key={resource.id}
                            resource={resource}
                            dataset={dataset}
                            setResourceAndMetadata={setResourceAndMetadata}
                            searchQuery={searchQuery}
                        />
                    ))}
                </ul>
            )}
            {resourcesWithoutSelf.length > 0 && isCollapsed && (
                <ul className="panel-body">
                    {getFilteredResources(resourcesWithoutSelf, searchQuery).map((resource) => (
                        <ResourceButton
                            key={resource.id}
                            resource={resource}
                            dataset={dataset}
                            setResourceAndMetadata={setResourceAndMetadata}
                            searchQuery={searchQuery}
                        />
                    ))}
                </ul>
            )}
        </div>
    );
};

const ResourceButton = ({ resource, dataset, setResourceAndMetadata, searchQuery }) => {
    const [resourceAccess, setResourceAccess] = useState();

    useEffect(() => {
        checkResourceAccess(dataset.id, resource.id, setResourceAccess);
    }, []);

    return (
        <li
            className={`list-group-item resource-btn ` + (!resourceAccess && 'disabled')}
            key={resource.id}
            onClick={() => setResourceAndMetadata(resource, dataset)}
        >
            <div className="resource-icon">
                <span className="format-label" property="dc:format" data-format={resource.format.toLowerCase() || 'data'}>
                    {resource.format}
                </span>
            </div>
            <div className="resource-metadata">
                <p className={`heading ` + (resourceAccess == false && "restricted-item")}>
                    {markQuerySubstring(resource.name, searchQuery)}
                </p>
                <p className="description">
                    <strong>
                        Modified {resource.last_modified}
                        &ensp;|&ensp;
                    </strong>
                    {resource.id}
                </p>
            </div>
            <div className="dropdown btn-group">
                {resourceAccess == null && (
                    <p>
                        <span className="spin"></span>Checking access...
                    </p>
                )}
                {resourceAccess == false && (
                    <a href={`/dataset/` + dataset.name + `/restricted_request_access/` + resource.id} className="btn">
                        <i className="fa fa-icon fa-unlock-alt"></i>Request Access
                    </a>
                )}
            </div>
        </li>
    );
};

const timeAgoFromTimestamp = async (timestamp, setlastModified) => {
    const body = {
        timestamp: timestamp,
    };

    const config = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    axios
        .post('/api/3/action/time_ago_from_timestamp', body, config)
        .then((response) => setlastModified(response.data.result))
        .catch((error) => {
            console.error(error);
        });
};

const ResourceWithDatasetInfoTile = ({ resource, dataset, synced }) => {
    const [lastModified, setlastModified] = useState();

    useEffect(() => {
        if (!resource.last_modified) {
            return;
        }
        if (resource.last_modified.match(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?/)) {
            timeAgoFromTimestamp(resource.last_modified, setlastModified);
        } else {
            setlastModified(resource.last_modified);
        }
    }, []);

    return (
        <div className="resource-fork-details-tile">
            <p className="heading">{resource.name}</p>
            <p className="description">
                <strong>
                    {dataset.organization ? dataset.organization.title : dataset.owner_org}
                    &ensp;|&ensp;
                </strong>
                {dataset.name}
                <br />
                <strong>
                    Modified&nbsp;{lastModified}
                    &ensp;|&ensp;
                </strong>
                {resource.id}
            </p>
            {!synced && (
                <span className="label label-warning data-out-of-sync-label">
                    <i className="fa fa-warning"></i>&ensp; Data out of date
                </span>
            )}
        </div>
    );
};

export default function ResourceForker({ selectedResource, setSelectedResource, setHiddenInputs, currentResourceID }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);

    useEffect(() => {
        getSearchResults(searchQuery, setSearchResults);
    }, [searchQuery]);

    const setResourceAndMetadata = (resource, dataset) => {
        setSelectedResource({
            resource: resource,
            dataset: dataset,
            synced: true,
        });
        setHiddenInputs('resource', {
            format: resource.format,
            filename: resource.filename,
            fork_resource: resource.id,
        });
    };

    const clearResourceAndMetadata = (completeRestart) => {
        setSelectedResource({
            resource: null,
            dataset: null,
            synced: null,
        });
        if (completeRestart) {
            setHiddenInputs(null, {});
        } else {
            setHiddenInputs('resource', {});
        }
    };

    const synchroniseResourceAndMetadata = (resource, dataset) => {
        // const config = {
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        // };

        // const body = JSON.stringify({
        //     id: resource.id,
        // });
        // axios
        //     .post('/api/3/action/resource_show', body, config)
        //     .then((response) => {
        //         setResourceAndMetadata(response.data.result, dataset);
        //     })
        //     .catch((error) => {
        //         console.error(error);
        //     });
        // FIXME the above post fails because, somehow, it calls a Flask View
        // as a temporary fix, set the last_modified to a useful message
        // this means the user still gets informative feedback
        resource.last_modified = 'just now';
        setResourceAndMetadata(resource, dataset);
    };

    return (
        <div className="resource-fork-component" data-testid="ResourceForkComponent">
            <header>
                <p>Import data from another resource:</p>
                <span className="resource-fork-escape" onClick={() => clearResourceAndMetadata(true)}>
                    <i className={`fa fa-close`}></i>
                </span>
            </header>
            {!selectedResource.resource && <SearchBar searchQuery={searchQuery} setSearchQuery={setSearchQuery} />}
            {searchResults && !selectedResource.resource && (
                <div className="resource-fork-search-results" data-testid="resource-fork-search-results">
                    <div className="scroll">
                        {searchResults.map((dataset) => (
                            <DatasetGroup
                                key={dataset.id}
                                dataset={dataset}
                                setResourceAndMetadata={setResourceAndMetadata}
                                searchQuery={searchQuery}
                                currentResourceID={currentResourceID}
                            />
                        ))}
                    </div>
                </div>
            )}
            {selectedResource.resource && (
                <>
                    <ResourceWithDatasetInfoTile
                        resource={selectedResource.resource}
                        dataset={selectedResource.dataset}
                        synced={selectedResource.synced}
                    />
                    <footer className="text-right">
                        <div className="btn-group">
                            {!selectedResource.synced && (
                                <button
                                    className="btn btn-default"
                                    onClick={() =>
                                        synchroniseResourceAndMetadata(selectedResource.resource, selectedResource.dataset)
                                    }
                                >
                                    <i className={`fa fa-refresh`}></i>&ensp; Import Latest Data
                                </button>
                            )}
                            <button className="btn btn-default" onClick={() => clearResourceAndMetadata(false)}>
                                <i className={`fa fa-search`}></i>&ensp;
                                <span>Select Different Resource</span>
                            </button>
                        </div>
                    </footer>
                </>
            )}
        </div>
    );
}
