import { render, act, fireEvent, screen } from '@testing-library/react';
import App from './src/App';
import axios from 'axios';
import * as giftless from "giftless-client";

jest.mock('axios');
let mockedAuthTokenRequest = undefined;

function setupMocks() {
  jest.clearAllMocks();
  giftless.Client = jest.fn(() => ({
    default: jest.fn(),
    upload: jest.fn(() => Promise.resolve())
  }));
  mockedAuthTokenRequest = axios.post.mockImplementation(
    () => Promise.resolve({
      data: { result: { token: 'MockedToken' } }
    })
  );
}

async function renderAppComponent(existingResourceData) {
  await act(async () => {
    const mockedAppProps = {
      lfsServer: 'mockedLfsServer',
      orgId: 'mockedOrgId',
      datasetName: 'mockedDatasetName',
      existingResourceData: existingResourceData
    };
    render(<App {...mockedAppProps} />);
  })
};

describe('upload a new resource', () => {

  beforeEach(async () => {
    setupMocks();
    await renderAppComponent({
      urlType: null,
      url: null,
      sha256: null,
      fileName: null,
      size: null,
    });
    expect(screen.getByTestId('FileUploaderButton')).toBeInTheDocument();
    expect(screen.getByTestId('UrlUploaderButton')).toBeInTheDocument();
  });

  test('url upload', async () => {
    fireEvent.click(screen.getByTestId('UrlUploaderButton'));
    expect(screen.getByTestId('UrlUploaderComponent')).toBeInTheDocument();
    expect(screen.getByTestId('UrlInputField')).toBeInTheDocument();
    expect(screen.getByTestId('UrlInputField')).toHaveValue('');
    expect(screen.getByTestId('url_type')).toHaveValue('');
    expect(screen.getByTestId('lfs_prefix')).toHaveValue('');
    expect(screen.getByTestId('sha256')).toHaveValue('');
    expect(screen.getByTestId('size')).toHaveValue('');
  });

  describe('file upload', () => {
    const uploadFileToElement = async elementTestId => {
      const component = screen.getByTestId(elementTestId);
      const file = new File(['file'], 'data.json');
      Object.defineProperty(component, 'files', { value: [file] });
      fireEvent.drop(component);
      await screen.findByText('data.json');
      expect(mockedAuthTokenRequest).toHaveBeenCalledTimes(1);
      expect(screen.getByTestId('url_type')).toHaveValue('upload');
      expect(screen.getByTestId('lfs_prefix')).toHaveValue('mockedOrgId/mockedDatasetName');
      expect(screen.getByTestId('sha256')).toHaveValue('mockedSha256');
      expect(screen.getByTestId('size')).toHaveValue('1337');
    }
    test('file upload using the <input type="file" />', async () => {
      await uploadFileToElement('FileUploaderInput');
    });
    test('file upload using drag and drop', async () => {
      await uploadFileToElement('FileUploaderComponent');
    });
  });

});

describe('view/edit an existing url upload', () => {

  const existingResourceData = {
    urlType: '', // empty string indicates url upload
    url: 'existingUrl',
  };

  test('view resource', async () => {
    await renderAppComponent(existingResourceData);
    expect(screen.getByTestId('url_type')).toHaveValue(existingResourceData.urlType);
    expect(screen.getByTestId('UrlInputField')).toHaveValue(existingResourceData.url);
    // no need to assert anything else as ckan backend will
    // ignore all the other fields like sha256, size etc
  });

  test('remove url and reset component', async () => {
    await renderAppComponent(existingResourceData);
    fireEvent.click(screen.getByText('Remove'));
    expect(screen.getByTestId('url_type')).toHaveValue('');
    expect(screen.getByTestId('lfs_prefix')).toHaveValue('');
    expect(screen.getByTestId('sha256')).toHaveValue('');
    expect(screen.getByTestId('size')).toHaveValue('');
    expect(screen.getByTestId('url')).toHaveValue('');
  });

});

describe('view/edit an existing file upload', () => {

  const existingResourceData = {
    urlType: 'upload', // 'upload' indicates file upload
    url: 'existingUrl',
    sha256: 'existingSha256',
    fileName: 'existingFileName',
    size: 'existingSize',
  };

  test('view resource', async () => {
    await renderAppComponent(existingResourceData);
    expect(screen.getByTestId('url_type')).toHaveValue(existingResourceData.urlType);
    expect(screen.getByTestId('lfs_prefix')).toHaveValue('mockedOrgId/mockedDatasetName');
    expect(screen.getByTestId('sha256')).toHaveValue(existingResourceData.sha256);
    expect(screen.getByTestId('url')).toHaveValue(existingResourceData.url);
    expect(screen.getByTestId('size')).toHaveValue(existingResourceData.size);
  });

  test('remove file and reset component', async () => {
    await renderAppComponent(existingResourceData);
    fireEvent.click(screen.getByTestId('RemoveFileButton'));
    expect(screen.getByTestId('url_type')).toHaveValue('');
    expect(screen.getByTestId('lfs_prefix')).toHaveValue('');
    expect(screen.getByTestId('sha256')).toHaveValue('');
    expect(screen.getByTestId('size')).toHaveValue('');
    expect(screen.getByTestId('url')).toHaveValue('');
  });

});
