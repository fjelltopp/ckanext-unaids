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
            .post("/api/3/action/resource_autocomplete", body, config) // QUERY why does this need to be POST?
            .then((response) => {
                setSearchResults(response.data.result);
            })
            .catch((error) => console.error(error));
    }
};

const markQuerySubstring = (string, searchQuery) => {
    let newString = string;
    searchQuery.split(" ").map((word) => {
        if (word.length > 0) {
            newString = newString.replaceAll(
                RegExp(word, "gi"),
                `<mark>$&</mark>`
            );
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
            <label
                id="resource-search-label"
                htmlFor="resource-search"
                className="btn-search"
            >
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
                ref={searchInput}
            />
            {/* <span className="input-group-btn"> */}
            <button
                type="reset"
                className="btn-reset"
                onClick={() => setSearchQuery("")}
            >
                <i className={`fa fa-close`}></i>
            </button>
            {/* </span> */}
        </div>
    );
};

const DatasetGroup = ({ dataset, setResourceAndMetadata, searchQuery }) => {
    const [isCollapsed, setIsCollapsed] = useState(true);
    const [isFiltered, setIsFiltered] = useState(false);

    useEffect(() => {
        setIsFiltered(!dataset.match);
    }, []);

    const getFilteredResources = (resources, searchQuery) => {
        return resources.filter((r) =>
            r.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
    };

    return (
        <div className="panel">
            <div
                className="panel-heading"
                onClick={() => setIsCollapsed(!isCollapsed)}
            >
                <p className="heading">
                    {markQuerySubstring(dataset.title, searchQuery)}
                </p>
                <p className="description">
                    <strong>
                        {markQuerySubstring(dataset.owner_org, searchQuery)}
                        &ensp;|&ensp;
                    </strong>
                    {markQuerySubstring(dataset.name, searchQuery)}
                    <span className="badge">
                        {dataset.resources.length} resources&ensp;
                        {dataset.resources.length > 0 &&
                            (isCollapsed ? (
                                <i className={`fa fa-chevron-down`}></i>
                            ) : (
                                <i className={`fa fa-chevron-up`}></i>
                            ))}
                    </span>
                </p>
            </div>
            {dataset.resources.length > 0 && !isCollapsed && (
                <ul className="panel-body">
                    {dataset.resources.length > 0 &&
                        dataset.resources.map((resource) => (
                            <ResourceButton
                                resource={resource}
                                dataset={dataset}
                                setResourceAndMetadata={setResourceAndMetadata}
                                searchQuery={searchQuery}
                            />
                        ))}
                </ul>
            )}
            {dataset.resources.length > 0 && isCollapsed && isFiltered && (
                <>
                    <ul className="panel-body">
                        {dataset.resources.length > 0 &&
                            getFilteredResources(
                                dataset.resources,
                                searchQuery
                            ).map((resource) => (
                                <ResourceButton
                                    resource={resource}
                                    dataset={dataset}
                                    setResourceAndMetadata={
                                        setResourceAndMetadata
                                    }
                                    searchQuery={searchQuery}
                                />
                            ))}
                    </ul>
                    <footer
                        className="text-center small"
                        onClick={() => setIsCollapsed(!isCollapsed)}
                    >
                        ... and{" "}
                        {dataset.resources.length -
                            getFilteredResources(dataset.resources, searchQuery)
                                .length}{" "}
                        non-matching resources (click to see them).
                    </footer>
                </>
            )}
        </div>
    );
};

const ResourceButton = ({
    resource,
    dataset,
    setResourceAndMetadata,
    searchQuery,
}) => (
    <li
        className="list-group-item resource-btn"
        onClick={() => setResourceAndMetadata(resource, dataset)}
    >
        <p className="heading">
            {markQuerySubstring(resource.name, searchQuery)}
        </p>
        <p className="description">
            <strong>
                Modified {resource.last_modified}
                &ensp;|&ensp;
            </strong>
            {resource.id.split("-")[0]}
        </p>
    </li>
);

const ResourceWithDatasetInfoTile = ({ resource, dataset }) => (
    <div className="resource-fork-details-tile">
        <p className="heading">{resource.name}</p>
        <p className="description">
            <strong>
                {dataset.owner_org}
                &ensp;|&ensp;
            </strong>
            {dataset.name}
            <br />
            <strong>
                Modified {resource.last_modified}
                &ensp;|&ensp;
            </strong>
            {resource.id.split("-")[0]}
        </p>
    </div>
);

export default function ResourceForker({
    selectedResource,
    setSelectedResource,
    setHiddenInputs,
}) {
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState("");

    useEffect(() => {
        getSearchResults(searchQuery, setSearchResults);
    }, [searchQuery]);

    const setResourceAndMetadata = (resource, dataset) => {
        setSelectedResource({
            resource: resource,
            dataset: dataset,
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
        });
        if (completeRestart) {
            setHiddenInputs(null, {});
        } else {
            setHiddenInputs("resource", {});
        }
    };

    return (
        <div
            className="resource-fork-component"
            data-testid="ResourceForkComponent"
        >
            <header>
                <p>Import data from another resource:</p>
                <span
                    className="resource-fork-escape"
                    onClick={() => clearResourceAndMetadata(true)}
                >
                    <i className={`fa fa-close`}></i>
                </span>
            </header>
            {!selectedResource.resource && (
                <SearchBar
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                />
            )}
            {searchResults && !selectedResource.resource && (
                <div className="resource-fork-search-results">
                    <header className="small">
                        Found {searchResults.length} datasets with matching
                        resources. Keeping typing to refine these results.
                    </header>
                    <div className="scroll">
                        {searchResults.map((dataset) => (
                            <DatasetGroup
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
                    <ResourceWithDatasetInfoTile
                        resource={selectedResource.resource}
                        dataset={selectedResource.dataset}
                    />
                    <footer className="text-right">
                        <button
                            className="btn btn-default"
                            onClick={() => clearResourceAndMetadata(false)}
                        >
                            <i className={`fa fa-search`}></i>&ensp;
                            <span>Choose Again</span>
                        </button>
                    </footer>
                </>
            )}
        </div>
    );
}
