import { render, act, fireEvent, screen, waitFor } from "@testing-library/react";
import App from "./src/App";
import axios from "axios";
import * as giftless from "giftless-client";

jest.mock("axios");
let mockedAPI = undefined;

const searchResultsForNorth = {
    help: "http://adr.local/api/3/action/help_show?name=resource_autocomplete",
    success: true,
    result: [
        {
            id: "6b856313-6fee-489d-be27-cd8159effb4c",
            name: "north-pole-christmas-lists",
            title: "2021 Santa Claus Lists",
            owner_org: "North Pole",
            match: true,
            resources: [
                {
                    id: "94f4192b-5ed5-4b0e-88b3-bb66166edab1",
                    name: "2021 Naughty List",
                    format: "JSON",
                    filename: "naughty_list.json",
                    last_modified: "4 hours ago",
                    match: false,
                },
                {
                    id: "1efb4b14-42c7-42eb-9b24-874590e5f9a2",
                    name: "2021 Nice List",
                    format: "JSON",
                    filename: "nice_list.json",
                    last_modified: "4 hours ago",
                    match: false,
                },
            ],
        },
        {
            id: "0fd93a1e-261e-45d1-8d5d-a11a7d174940",
            name: "germany-country-estimates-2022",
            title: "Germany HIV Estimates 2022",
            owner_org: "North Pole",
            match: false,
            resources: [
                {
                    id: "535778a3-9aba-4358-848c-ad52c80f9019",
                    name: "Survey Data",
                    format: "CSV",
                    filename: "survey.csv",
                    last_modified: "4 hours ago",
                    match: false,
                },
                {
                    id: "01f08e0b-f2a8-41a3-b273-187bd9f0bdb1",
                    name: "Geographic Data",
                    format: "GeoJSON",
                    filename: "geographic.geojson",
                    last_modified: "4 hours ago",
                    match: false,
                },
                {
                    id: "ac2436d2-35f0-464c-a109-8e2ec9200e1c",
                    name: "Population Data",
                    format: "CSV",
                    filename: "population.csv",
                    last_modified: "4 hours ago",
                    match: false,
                },
            ],
        },
    ],
};

const searchResultsForNorthNice = {
    help: "http://adr.local/api/3/action/help_show?name=resource_autocomplete",
    success: true,
    result: [
        {
            id: "6b856313-6fee-489d-be27-cd8159effb4c",
            name: "north-pole-christmas-lists",
            title: "2021 Santa Claus Lists",
            owner_org: "North Pole",
            match: false,
            resources: [
                {
                    id: "94f4192b-5ed5-4b0e-88b3-bb66166edab1",
                    name: "2021 Naughty List",
                    format: "JSON",
                    filename: "naughty_list.json",
                    last_modified: "20 hours ago",
                    match: false,
                },
                {
                    id: "1efb4b14-42c7-42eb-9b24-874590e5f9a2",
                    name: "2021 Nice List",
                    format: "JSON",
                    filename: "nice_list.json",
                    last_modified: "20 hours ago",
                    match: false,
                },
            ],
        },
    ],
};

function setupMocks() {
    jest.clearAllMocks();
    giftless.Client = jest.fn(() => ({
        default: jest.fn(),
        upload: jest.fn(() => Promise.resolve()),
    }));
    mockedAPI = axios.post.mockImplementation((url) => {
        switch (url) {
            case "/api/3/action/authz_authorize":
                return Promise.resolve({
                    status: 200,
                    data: { result: { token: "MockedToken" } },
                });
            case "/api/3/action/resource_autocomplete":
                return Promise.resolve({
                    status: 200,
                    data: searchResultsForNorth,
                });
            case "/api/3/action/restricted_check_access":
                return Promise.resolve({
                    status: 200,
                    data: { result: { success: true } },
                });
        }
    });
}

async function renderAppComponent(existingResourceData) {
    await act(async () => {
        const mockedAppProps = {
            lfsServer: "mockedLfsServer",
            orgId: "mockedOrgId",
            datasetName: "mockedDatasetName",
            existingResourceData: existingResourceData,
        };
        render(<App {...mockedAppProps} />);
    });
}

describe("upload a new resource", () => {
    beforeEach(async () => {
        setupMocks();
        await renderAppComponent({
            urlType: null,
            url: null,
            sha256: null,
            fileName: null,
            size: null,
            fork_resource: null,
        });
        expect(screen.getByTestId("FileUploaderButton")).toBeInTheDocument();
        expect(screen.getByTestId("UrlUploaderButton")).toBeInTheDocument();
        expect(screen.getByTestId("ResourceForkButton")).toBeInTheDocument();
    });

    test("url upload", async () => {
        fireEvent.click(screen.getByTestId("UrlUploaderButton"));
        expect(screen.getByTestId("UrlUploaderComponent")).toBeInTheDocument();
        expect(screen.getByTestId("UrlInputField")).toBeInTheDocument();
        expect(screen.getByTestId("UrlInputField")).toHaveValue("");
        expect(screen.getByTestId("url_type")).toHaveValue("");
        expect(screen.getByTestId("lfs_prefix")).toHaveValue("");
        expect(screen.getByTestId("sha256")).toHaveValue("");
        expect(screen.getByTestId("size")).toHaveValue("");
        expect(screen.getByTestId("fork_resource")).toHaveValue("");
    });

    describe("file upload", () => {
        const uploadFileToElement = async (elementTestId) => {
            const component = screen.getByTestId(elementTestId);
            const file = new File(["file"], "data.json");
            Object.defineProperty(component, "files", { value: [file] });
            fireEvent.drop(component);
            await screen.findByText("data.json");
            expect(mockedAPI).toHaveBeenCalledTimes(1);
            expect(screen.getByTestId("url_type")).toHaveValue("upload");
            expect(screen.getByTestId("lfs_prefix")).toHaveValue("mockedOrgId/mockedDatasetName");
            expect(screen.getByTestId("sha256")).toHaveValue("mockedSha256");
            expect(screen.getByTestId("size")).toHaveValue("1337");
        };
        test('file upload using the <input type="file" />', async () => {
            await uploadFileToElement("FileUploaderInput");
        });
        test("file upload using drag and drop", async () => {
            await uploadFileToElement("FileUploaderComponent");
        });
    });

    describe("fork resource", () => {
        beforeEach(() => {
            fireEvent.click(screen.getByTestId("ResourceForkButton"));
            expect(screen.getByTestId("ResourceForkComponent")).toBeInTheDocument();
            expect(screen.getByTestId("resource-fork-search-bar")).toBeInTheDocument();
        });

        test("search for matching dataset", async () => {
            fireEvent.change(screen.getByTestId("resource-fork-search-bar"), { target: { value: "north" } });
            await waitFor(() => expect(screen.getByTestId("resource-fork-search-results")).toBeInTheDocument());
            await waitFor(() =>
                expect(screen.getByTestId("resource-fork-search-results").getElementsByClassName("panel")).toHaveLength(2)
            );

            expect(screen.getByText("2021 Santa Claus Lists")).toBeInTheDocument();
            expect(screen.getAllByText("North")[0].tagName).toMatch("MARK");
            expect(
                screen.getByText("2021 Santa Claus Lists").nextElementSibling.children[2].innerHTML.includes("2 resources")
            ).toBe(true);

            expect(
                screen
                    .getByText("2021 Santa Claus Lists")
                    .parentElement.parentElement.getElementsByClassName("list-group-item resource-btn")
            ).toBeEmpty();
            fireEvent.click(screen.getByText("2021 Santa Claus Lists"));
            await waitFor(() =>
                expect(
                    screen
                        .getByText("2021 Santa Claus Lists")
                        .parentElement.parentElement.getElementsByClassName("list-group-item resource-btn")
                ).toHaveLength(2)
            );
        });

        test("search for matching resource", async () => {
            mockedAPI.mockImplementationOnce(() =>
                Promise.resolve({
                    data: searchResultsForNorthNice,
                })
            );
            fireEvent.change(screen.getByTestId("resource-fork-search-bar"), { target: { value: "north nice" } });
            await waitFor(() => expect(screen.getByTestId("resource-fork-search-results")).toBeInTheDocument());
            await waitFor(() =>
                expect(screen.getByTestId("resource-fork-search-results").getElementsByClassName("panel")).toHaveLength(1)
            );

            expect(
                screen
                    .getByText("2021 Santa Claus Lists")
                    .parentElement.parentElement.getElementsByClassName("list-group-item resource-btn")
            ).toHaveLength(1);
            fireEvent.click(screen.getByText("2021 Santa Claus Lists"));
            await waitFor(() =>
                expect(
                    screen
                        .getByText("2021 Santa Claus Lists")
                        .parentElement.parentElement.getElementsByClassName("list-group-item resource-btn")
                ).toHaveLength(2)
            );
        });

        test("select a resource", async () => {
            expect(screen.getByTestId("url_type")).toHaveValue("");
            expect(screen.getByTestId("lfs_prefix")).toHaveValue("");
            expect(screen.getByTestId("sha256")).toHaveValue("");
            expect(screen.getByTestId("size")).toHaveValue("");
            expect(screen.getByTestId("url")).toHaveValue("");
            expect(screen.getByTestId("fork_resource")).toHaveValue("");

            fireEvent.change(screen.getByTestId("resource-fork-search-bar"), { target: { value: "north" } });
            await waitFor(() =>
                expect(screen.getByTestId("resource-fork-search-results").getElementsByClassName("panel")).toHaveLength(2)
            );
            fireEvent.click(screen.getByText("2021 Santa Claus Lists"));

            fireEvent.click(screen.getByText("2021 Nice List"));
            expect(
                screen.getByTestId("ResourceForkComponent").getElementsByClassName("resource-fork-details-tile")
            ).toHaveLength(1);

            expect(screen.getByTestId("url_type")).toHaveValue("");
            expect(screen.getByTestId("lfs_prefix")).toHaveValue("");
            expect(screen.getByTestId("sha256")).toHaveValue("");
            expect(screen.getByTestId("size")).toHaveValue("");
            expect(screen.getByTestId("url")).toHaveValue("nice_list.json");
            expect(screen.getByTestId("fork_resource")).toHaveValue("1efb4b14-42c7-42eb-9b24-874590e5f9a2");
        });
    });
});

describe("view/edit an existing url upload", () => {
    const existingResourceData = {
        urlType: "", // empty string indicates url upload
        url: "existingUrl",
    };

    test("view resource", async () => {
        await renderAppComponent(existingResourceData);
        expect(screen.getByTestId("url_type")).toHaveValue(existingResourceData.urlType);
        expect(screen.getByTestId("UrlInputField")).toHaveValue(existingResourceData.url);
        // no need to assert anything else as ckan backend will
        // ignore all the other fields like sha256, size etc
    });

    test("remove url and reset component", async () => {
        await renderAppComponent(existingResourceData);
        fireEvent.click(screen.getByText("Remove"));
        expect(screen.getByTestId("url_type")).toHaveValue("");
        expect(screen.getByTestId("lfs_prefix")).toHaveValue("");
        expect(screen.getByTestId("sha256")).toHaveValue("");
        expect(screen.getByTestId("size")).toHaveValue("");
        expect(screen.getByTestId("url")).toHaveValue("");
        expect(screen.getByTestId("fork_resource")).toHaveValue("");
    });
});

describe("view/edit an existing file upload", () => {
    const existingResourceData = {
        urlType: "upload", // 'upload' indicates file upload
        url: "existingUrl",
        sha256: "existingSha256",
        fileName: "existingFileName",
        size: "existingSize",
    };

    test("view resource", async () => {
        await renderAppComponent(existingResourceData);
        expect(screen.getByTestId("url_type")).toHaveValue(existingResourceData.urlType);
        expect(screen.getByTestId("lfs_prefix")).toHaveValue("mockedOrgId/mockedDatasetName");
        expect(screen.getByTestId("sha256")).toHaveValue(existingResourceData.sha256);
        expect(screen.getByTestId("url")).toHaveValue(existingResourceData.url);
        expect(screen.getByTestId("size")).toHaveValue(existingResourceData.size);
    });

    test("remove file and reset component", async () => {
        await renderAppComponent(existingResourceData);
        fireEvent.click(screen.getByTestId("RemoveFileButton"));
        expect(screen.getByTestId("url_type")).toHaveValue("");
        expect(screen.getByTestId("lfs_prefix")).toHaveValue("");
        expect(screen.getByTestId("sha256")).toHaveValue("");
        expect(screen.getByTestId("size")).toHaveValue("");
        expect(screen.getByTestId("url")).toHaveValue("");
        expect(screen.getByTestId("fork_resource")).toHaveValue("");
    });
});
