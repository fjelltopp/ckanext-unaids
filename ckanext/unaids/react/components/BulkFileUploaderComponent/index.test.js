import { render, act, fireEvent, screen } from '@testing-library/react';
import App from './src/App';
import axios from 'axios';
import * as giftless from "giftless-client";

jest.mock('axios');
const maxResourceSize = 1
const requestAuthTokenUrl = '/api/3/action/authz_authorize';
const requestCreateResourceUrl = '/api/3/action/resource_create';
let mockedAxiosPost = undefined;

function setupMocks({ applyNetworkIssue }) {
  jest.clearAllMocks();
  giftless.Client = jest.fn(() => ({
    default: jest.fn(),
    upload: applyNetworkIssue == 'giftless.upload'
      ? jest.fn(() => Promise.reject('Mocked Promise Rejection'))
      : jest.fn(() => Promise.resolve())
  }));
  mockedAxiosPost = axios.post.mockImplementation(url => {
    switch (url) {
      case requestAuthTokenUrl:
        return applyNetworkIssue == 'ckan.api.authz_authorize'
          ? Promise.reject('Mocked Promise Rejection')
          : Promise.resolve({
            data: { result: { token: 'MockedToken' } }
          })
      case requestCreateResourceUrl:
        return applyNetworkIssue == 'ckan.api.resource_create'
          ? Promise.reject('Mocked Promise Rejection')
          : Promise.resolve()
      default:
        throw `No axios mockImplementation is set up for url: ${url}`;
    };
  });
}

async function renderAppComponent(defaultFields) {
  await act(async () => {
    const mockedAppProps = {
      lfsServer: 'mockedLfsServer',
      maxResourceSize: maxResourceSize,
      orgId: 'mockedOrgId',
      datasetName: 'mockedDatasetName',
      defaultFields: defaultFields
    };
    render(<App {...mockedAppProps} />);
  })
};

const selectFilesToUpload = async (elementTestId, files) => {
  const component = screen.getByTestId(elementTestId);
  Object.defineProperty(component, 'files', { value: files });
  await act(async () => {
    fireEvent.drop(component);
  });
}
const uploadFilesAndCreateResources = async (validFileUploads, invalidFileUpload) => {
  fireEvent.click(screen.getByTestId('UploadFilesButton'));
  await screen.findByText('Uploads Complete');
  const filesUploaded = await screen.findAllByText('Uploaded');
  expect(filesUploaded).toHaveLength(validFileUploads.length);
  const expectedAuthTokenRequests =
    validFileUploads.length + invalidFileUpload.length;
  const expectedCreateResourceRequests =
    expectedAuthTokenRequests - invalidFileUpload.length;
  const authTokenRequests = mockedAxiosPost.mock.calls
    .filter(mock => mock[0] === requestAuthTokenUrl).length;
  const createResourceRequests = mockedAxiosPost.mock.calls
    .filter(mock => mock[0] === requestCreateResourceUrl).length;
    expect(expectedAuthTokenRequests).toEqual(authTokenRequests);
    expect(expectedCreateResourceRequests).toEqual(createResourceRequests);
}

const testSuccessfulUpload = async elementTestId => {
  const validFiles = [
    new File(['file'], 'file_1.json'),
    new File(['file'], 'file_2.json'),
  ];
  const invalidFiles = [];
  await selectFilesToUpload(elementTestId, validFiles);
  await screen.findByText('file_1.json');
  await screen.findByText('file_2.json');
  await uploadFilesAndCreateResources(validFiles, invalidFiles);
};
const testUploadWithFileTooLarge = async elementTestId => {
  const validFile = new File(['file'], 'file_1.json');
  const invalidFile = new File(
    [new ArrayBuffer(maxResourceSize * 10000000)], 'file_2.json'
  );
  await selectFilesToUpload(elementTestId, [validFile, invalidFile]);
  await screen.findByText('file_1.json');
  await screen.findByText('file_2.json');
  await uploadFilesAndCreateResources([validFile], [invalidFile]);
};

describe('test without network issues', () => {
  beforeEach(async () => {
    setupMocks({ applyNetworkIssue: null });
    await renderAppComponent({
      restricted_allowed_orgs: 'unaids'
    });
  });
  describe('test file uploads using the <input type="file" />', () => {
    test('successful uploads', async () =>
      await testSuccessfulUpload('BulkFileUploaderInput')
    );
    test('file too large', async () =>
      await testUploadWithFileTooLarge('BulkFileUploaderInput')
    );
  });
  describe("test file uploads using drag and drop", () => {
    test('successful uploads', async () =>
      await testSuccessfulUpload('BulkFileUploaderComponent')
    );
    test('file too large', async () =>
      await testUploadWithFileTooLarge('BulkFileUploaderComponent')
    );
  });
});

describe('test with giftless network error', () => {
  beforeEach(async () => {
    setupMocks({ applyNetworkIssue: 'giftless.upload' });
    await renderAppComponent({ restricted_allowed_orgs: 'unaids' });
  });
  test('uploading file', async () => {
    const files = [new File(['file'], 'file_1.json')];
    await selectFilesToUpload('BulkFileUploaderInput', files);
    await screen.findByText('file_1.json');
    fireEvent.click(screen.getByTestId('UploadFilesButton'));
    await screen.findByText('File Upload Error');
  })
});

describe('test with ckan authz_authorize network error', () => {
  beforeEach(async () => {
    setupMocks({ applyNetworkIssue: 'ckan.api.authz_authorize' });
    await renderAppComponent({ restricted_allowed_orgs: 'unaids' });
  });
  test('uploading file', async () => {
    const files = [new File(['file'], 'file_1.json')];
    await selectFilesToUpload('BulkFileUploaderInput', files);
    await screen.findByText('file_1.json');
    fireEvent.click(screen.getByTestId('UploadFilesButton'));
    await screen.findByText('Authorisation Error');
  })
});

describe('test with ckan authz_authorize network error', () => {
  beforeEach(async () => {
    setupMocks({ applyNetworkIssue: 'ckan.api.resource_create' });
    await renderAppComponent({ restricted_allowed_orgs: 'unaids' });
  });
  test('uploading file', async () => {
    const files = [new File(['file'], 'file_1.json')];
    await selectFilesToUpload('BulkFileUploaderInput', files);
    await screen.findByText('file_1.json');
    fireEvent.click(screen.getByTestId('UploadFilesButton'));
    await screen.findByText('Resource Create Error');
  })
});
