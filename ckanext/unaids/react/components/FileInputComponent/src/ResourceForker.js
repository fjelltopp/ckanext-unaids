import axios from "axios";
import React, { useEffect, useState, useRef } from "react";
import parse from "html-react-parser";

const getSearchResults = (searchQuery, setSearchResults) => {
    if (searchQuery) {
        const body = JSON.stringify({
            q: searchQuery,
        });

        const config = {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        };
        axios
            .post("/api/3/action/resource_autocomplete", body, config)
            .then((response) => {
                setSearchResults(response.data.result);
            })
            .catch((error) => console.error(error));
    }
};

const checkResourceAccess = (packageID, resourceID, setResourceAccess) => {
    const body = JSON.stringify({
        package_id: packageID,
        resource_id: resourceID,
    });

    const config = {
        headers: {
            "Content-Type": "application/json",
        },
    };
    axios
        .post("/api/3/action/restricted_check_access", body, config)
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
    searchQuery.split(" ").map((word) => {
        if (word.length > 0) {
            newString = newString.replaceAll(RegExp(word, "gi"), `<mark>$&</mark>`);
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
                    e.key === "Enter" && e.preventDefault();
                }} // DEVNOTE - not IE compatible
                ref={searchInput}
                data-testid="resource-fork-search-bar"
            />
            <button type="reset" className="btn-reset" onClick={() => setSearchQuery("")}>
                <i className={`fa fa-close`}></i>
            </button>
        </div>
    );
};

const DatasetGroup = ({ dataset, setResourceAndMetadata, searchQuery }) => {
    const [isCollapsed, setIsCollapsed] = useState(true);

    const markQuerySubstring = (string, searchQuery) => {
        let newString = string;
        searchQuery.split(" ").map((word) => {
            if (word.length > 0) {
                newString = newString.replaceAll(RegExp(word, "gi"), `<mark>$&</mark>`);
            }
        });
        return parse(newString);
    };

    const getFilteredResources = (resources, searchQuery) => {
        return resources.filter((resource) => {
            return searchQuery
                .toLowerCase()
                .split(" ")
                .filter((word) => word.length > 0)
                .map((word) => resource.name.toLowerCase().includes(word))
                .some((x) => x == true);
        });
    };

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
                        {dataset.resources.length} resources&ensp;
                        {dataset.resources.length > 0 &&
                            (isCollapsed ? <i className={`fa fa-chevron-down`}></i> : <i className={`fa fa-chevron-up`}></i>)}
                    </span>
                </p>
            </div>
            {dataset.resources.length > 0 && !isCollapsed && (
                <ul className="panel-body">
                    {dataset.resources.map((resource) => (
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
            {dataset.resources.length > 0 && isCollapsed && (
                <ul className="panel-body">
                    {getFilteredResources(dataset.resources, searchQuery).map((resource) => (
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
            className={`list-group-item resource-btn ` + (!resourceAccess && "disabled")}
            key={resource.id}
            onClick={() => setResourceAndMetadata(resource, dataset)}
        >
            <p className={`heading ` + (resourceAccess == false && "restricted-item")}>
                {markQuerySubstring(resource.name, searchQuery)}
            </p>
            <p className="description">
                <strong>
                    Modified {resource.last_modified}
                    &ensp;|&ensp;
                </strong>
                {resource.id.split("-")[0]}
            </p>
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
    const body = JSON.stringify({
        timestamp: timestamp,
    });

    const config = {
        headers: {
            "Content-Type": "application/json",
        },
    };

    axios
        .post("/api/3/action/time_ago_from_timestamp", body, config)
        .then((response) => setlastModified(response.data.result))
        .catch((error) => {});
};

const ResourceWithDatasetInfoTile = ({ resource, dataset }) => {
    const [lastModified, setlastModified] = useState();

    useEffect(() => {
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
                {resource.id.split("-")[0]}
            </p>
        </div>
    );
};

export default function ResourceForker({ selectedResource, setSelectedResource, setHiddenInputs }) {
    const [searchQuery, setSearchQuery] = useState("");
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
        setHiddenInputs("resource", {
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
            setHiddenInputs("resource", {});
        }
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
                            />
                        ))}
                    </div>
                </div>
            )}
            {selectedResource.resource && (
                <>
                    <ResourceWithDatasetInfoTile resource={selectedResource.resource} dataset={selectedResource.dataset} />
                    <footer className="text-right">
                        <div className="btn-group">
                            {!selectedResource.synced && (
                                <>
                                    <header className="small">Data out of sync since imported</header>
                                    <button
                                        className="btn btn-default"
                                        onClick={() =>
                                            setResourceAndMetadata(selectedResource.resource, selectedResource.dataset)
                                        }
                                    >
                                        Synchronise Now
                                    </button>
                                </>
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
