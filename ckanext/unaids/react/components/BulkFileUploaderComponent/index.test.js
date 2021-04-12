import { render, act, fireEvent, screen } from '@testing-library/react';
import App from './src/App';
import axios from 'axios';
import * as giftless from "giftless-client";

jest.mock('axios');
const maxResourceSize = 1
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
      case '/api/3/action/authz_authorize':
        return applyNetworkIssue == 'ckan.api.authz_authorize'
          ? Promise.reject('Mocked Promise Rejection')
          : Promise.resolve({
            data: { result: { token: 'MockedToken' } }
          })
      case '/api/3/action/resource_create':
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
      datasetId: 'mockedDatasetId',
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
const uploadFilesAndCreateResources = async successfulFileUploads => {
  fireEvent.click(screen.getByTestId('UploadFilesButton'));
  await screen.findByText('Uploads Complete');
  const filesUploaded = await screen.findAllByText('Uploaded');
  expect(filesUploaded).toHaveLength(successfulFileUploads.length);
  expect(mockedAxiosPost).toHaveBeenCalledTimes(
    ['get authToken', ...successfulFileUploads].length
  );
}

const testSuccessfulUpload = async elementTestId => {
  const files = [
    new File(['file'], 'file_1.json'),
    new File(['file'], 'file_2.json'),
  ];
  await selectFilesToUpload(elementTestId, files);
  await screen.findByText('file_1.json');
  await screen.findByText('file_2.json');
  await uploadFilesAndCreateResources(files);
};
const testUploadWithFileTooLarge = async elementTestId => {
  const files = [
    new File(['file'], 'file_1.json'),
    new File([new ArrayBuffer(maxResourceSize * 10000000)], 'file_2.json'),
  ];
  await selectFilesToUpload(elementTestId, files);
  await screen.findByText('file_1.json');
  await screen.findByText('file_2.json');
  await uploadFilesAndCreateResources([files[0]]);
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