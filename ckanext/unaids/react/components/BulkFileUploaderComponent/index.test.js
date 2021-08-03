import { render, act, fireEvent, screen, within } from '@testing-library/react';
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

async function renderAppComponent(
  defaultFields, existingCoreResources = [],
  existingExtraResources = [], missingCoreResources = []
) {
  await act(async () => {
    const mockedAppProps = {
      lfsServer: 'mockedLfsServer',
      maxResourceSize: maxResourceSize,
      orgId: 'mockedOrgId',
      datasetName: 'mockedDatasetName',
      defaultFields: defaultFields,
      existingCoreResources: existingCoreResources,
      existingExtraResources: existingExtraResources,
      missingCoreResources: missingCoreResources
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
    new File(['file'], 'anc_data_file.csv'),
    new File(['file'], 'geographic.json'),
  ];
  const invalidFiles = [];
  await selectFilesToUpload(elementTestId, validFiles);
  await screen.findByText('anc_data_file.csv');
  await screen.findByText('geographic.json');
  await uploadFilesAndCreateResources(validFiles, invalidFiles);
};
const testUploadWithFileTooLarge = async elementTestId => {
  const validFile = new File(['file'], 'anc_data_file.csv');
  const invalidFile = new File(
    [new ArrayBuffer(maxResourceSize * 10000000)], 'geographic.json'
  );
  await selectFilesToUpload(elementTestId, [validFile, invalidFile]);
  await screen.findByText('anc_data_file.csv');
  await screen.findByText('geographic.json');
  await uploadFilesAndCreateResources([validFile], [invalidFile]);
};

describe('test selecting if we want to update an existing resource or upload a new one', () => {

  const stageFileUpload = async (
    existingCoreResources, existingExtraResources, missingCoreResources,
  ) => {
    const elementTestId = 'BulkFileUploaderInput';
    const validFiles = [
      new File(['file'], 'anc_data_file.csv'),
      new File(['file'], 'geographic.json'),
    ];
    const defaultFields = {};
    await renderAppComponent(
      defaultFields, existingCoreResources,
      existingExtraResources, missingCoreResources
    );
    await selectFilesToUpload(elementTestId, validFiles);
  };

  describe('automatically set the uploadAction select value', () => {
    test('if the filename is an exact match', async () => {
      const existingCoreResources = [];
      const existingExtraResources = [
        {
          id: 2,
          name: 'Resource 2',
          resource_type: 'resource_type 2',
          url: 'http://example.com/example.csv'
        },
        {
          id: 1,
          name: 'Resource 1',
          resource_type: 'resource_type 1',
          url: 'http://example.com/anc_data_file.csv'
        }
      ];
      const missingCoreResources = [];
      await stageFileUpload(
        existingCoreResources,
        existingExtraResources,
        missingCoreResources
      );
      const selectValue = screen
        .getAllByTestId('uploadActionSelector')[0].value;
      const selectLabel = JSON.parse(selectValue).optionLabel;
      expect(selectLabel).toEqual('Resource 1');
    });
    test('if the filename does not match', async () => {
      const existingCoreResources = [];
      const existingExtraResources = [
        {
          id: 1,
          name: 'Resource 1',
          resource_type: 'resource_type 1',
          url: 'http://example.com/example.csv'
        }
      ];
      const missingCoreResources = [];
      await stageFileUpload(
        existingCoreResources,
        existingExtraResources,
        missingCoreResources
      );
      const selectValue = screen
        .getAllByTestId('uploadActionSelector')[0].value;
      const selectLabel = JSON.parse(selectValue).optionLabel;
      expect(selectLabel).toEqual('Extra Resource');
    });
    test('if the filename matches multiple existing files', async () => {
      const existingCoreResources = [];
      const existingExtraResources = [
        {
          id: 1,
          name: 'Resource 1',
          resource_type: 'resource_type 1',
          url: 'http://example.com/anc_data_file.csv'
        },
        {
          id: 2,
          name: 'Resource 2',
          resource_type: 'resource_type 2',
          url: 'http://example.com/anc_data_file.csv'
        }
      ];
      const missingCoreResources = [];
      await stageFileUpload(
        existingCoreResources,
        existingExtraResources,
        missingCoreResources
      );
      const selectValue = screen
        .getAllByTestId('uploadActionSelector')[0].value;
      const selectLabel = JSON.parse(selectValue).optionLabel;
      expect(selectLabel).toEqual('Extra Resource');
    });
  });

  test('correct select option labels', async () => {
    const existingCoreResources = [
      {
        id: 1,
        name: 'Resource 1',
        resource_type: 'resource_type 1',
        url: 'http://example.com/resource_1.csv'
      }
    ];
    const existingExtraResources = [
      {
        id: 2,
        name: 'Resource 2',
        resource_type: 'resource_type 2',
        url: 'http://example.com/resource_2.csv'
      }
    ];
    const missingCoreResources = [
      {
        name: 'Resource 3',
        resource_type: 'resource_type 3'
      }
    ];
    await stageFileUpload(
      existingCoreResources,
      existingExtraResources,
      missingCoreResources
    );
    screen.getAllByTestId('uploadActionSelector').map(select => {
      const selectOptionLabels = within(select)
        .getAllByTestId('select-option')
        .map(option => option.text);
      const expectedOptionLabels = [
        'Resource 1', 'Resource 2',
        'Resource 3', 'Extra Resource'
      ]
      expect(expectedOptionLabels).toEqual(selectOptionLabels);
    });
  });

  test('correct select option values', async () => {
    const existingCoreResources = [
      {
        id: 1,
        name: 'Resource 1',
        resource_type: 'resource_type 1',
        url: 'http://example.com/resource_1.csv'
      }
    ];
    const existingExtraResources = [
      {
        id: 2,
        name: 'Resource 2',
        resource_type: 'resource_type 2',
        url: 'http://example.com/resource_2.csv'
      }
    ];
    const missingCoreResources = [
      {
        name: 'Resource 3',
        resource_type: 'resource_type 3'
      }
    ];
    await stageFileUpload(
      existingCoreResources,
      existingExtraResources,
      missingCoreResources
    );
    screen.getAllByTestId('uploadActionSelector').map(select => {
      const selectOptionValues = within(select)
        .getAllByTestId('select-option')
        .map(option => option.value);
      const expectedOptionValues = [
        {
          optionLabel: "Resource 1",
          fileName: "resource_1.csv",
          ckanAction: "resource_patch",
          ckanDataDict: {
            id: 1,
            name: "Resource 1",
            resource_type: "resource_type 1"
          }
        },
        {
          optionLabel: "Resource 2",
          fileName: "resource_2.csv",
          ckanAction: "resource_patch",
          ckanDataDict: {
            id: 2,
            name: "Resource 2",
            resource_type: "resource_type 2"
          }
        },
        {
          optionLabel: "Resource 3",
          ckanAction: "resource_create",
          ckanDataDict: {
            name: "Resource 3",
            resource_type: "resource_type 3"
          }
        },
        {
          optionLabel: "Extra Resource",
          ckanAction: "resource_create",
          ckanDataDict: {}
        }
      ].map(x => JSON.stringify(x));
      expect(expectedOptionValues).toEqual(selectOptionValues);
    });
  });

  describe('when the same option is selected twice', () => {
    beforeEach(async () => {
      const existingCoreResources = [
        {
          id: 1,
          name: 'Resource 1',
          resource_type: 'resource_type 1',
          url: 'http://example.com/resource_1.csv'
        }
      ];
      const existingExtraResources = [];
      const missingCoreResources = [];
      await stageFileUpload(
        existingCoreResources,
        existingExtraResources,
        missingCoreResources
      );
      const duplicateOptionValue = JSON.stringify({
        optionLabel: "Resource 1",
        ckanAction: "resource_patch",
        ckanDataDict: {
          id: 1,
          name: "Resource 1",
          resource_type: "resource_type 1"
        }
      })
      await fireEvent.change(
        screen.getAllByTestId('uploadActionSelector')[0],
        { target: { value: duplicateOptionValue } }
      );
      await fireEvent.change(
        screen.getAllByTestId('uploadActionSelector')[1],
        { target: { value: duplicateOptionValue } }
      );
    });
    test('display a warning', async () => {
      await screen.getAllByText('Duplicate option selected');
    });
    test('disable the upload button', async () => {
      const uploadButtonClass = screen.getByTestId('UploadFilesButton').className;
      expect(uploadButtonClass).toContain('disabled')
    });
  });

});

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
    describe("test popup modal", () => {
      test('successful uploads', async () =>
        await testSuccessfulUpload('modalDropzone')
      );
      test('file too large', async () =>
        await testUploadWithFileTooLarge('modalDropzone')
      );
    });
    describe("test dataset page", () => {
      test('successful uploads', async () =>
        await testSuccessfulUpload('fullPageDropzone')
      );
      test('file too large', async () =>
        await testUploadWithFileTooLarge('fullPageDropzone')
      );
    });
  });
});

describe('test with giftless network error', () => {
  beforeEach(async () => {
    setupMocks({ applyNetworkIssue: 'giftless.upload' });
    await renderAppComponent({ restricted_allowed_orgs: 'unaids' });
  });
  test('uploading file', async () => {
    const files = [new File(['file'], 'anc_data_file.csv')];
    await selectFilesToUpload('BulkFileUploaderInput', files);
    await screen.findByText('anc_data_file.csv');
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
    const files = [new File(['file'], 'anc_data_file.csv')];
    await selectFilesToUpload('BulkFileUploaderInput', files);
    await screen.findByText('anc_data_file.csv');
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
    const files = [new File(['file'], 'anc_data_file.csv')];
    await selectFilesToUpload('BulkFileUploaderInput', files);
    await screen.findByText('anc_data_file.csv');
    fireEvent.click(screen.getByTestId('UploadFilesButton'));
    await screen.findByText('Resource Create Error');
  })
});

