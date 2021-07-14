import ReactDOM from 'react-dom';
import React from 'react';
import App from './src/App';

const componentElementId = 'BulkFileUploaderComponent';
const modalElementId = 'BulkFileUploaderComponentModal';

const componentElement =
  document.getElementById(componentElementId);
const getAttr = key => {
  const val = componentElement.getAttribute(`data-${key}`);
  return ['None', ''].includes(val) ? null : val;
};
const
  lfsServer = getAttr('lfsServer'),
  maxResourceSize = getAttr('maxResourceSize'),
  orgId = getAttr('orgId'),
  datasetName = getAttr('datasetName'),
  defaultFields = JSON.parse(getAttr('defaultFields'));

const loadCkan = callback => {
  if (
    typeof ckan === 'undefined' ||
    typeof ckan.i18n === 'undefined' ||
    typeof ckan.i18n._ === 'undefined') {
    setTimeout(() => loadCkan(callback), 10);
  } else {
    callback();
  }
};
const moveDatasetPageIntoDropzoneArea = () => {
  var fragment = document.createDocumentFragment();
  fragment.appendChild(document.getElementById('ContentToMoveInsideDropzone'));
  document.getElementById('DropzoneContainer').appendChild(fragment);
};

loadCkan(() => {
  ReactDOM.render(
    <App {...{
      modalElementId, lfsServer, maxResourceSize,
      orgId, datasetName, defaultFields
    }} />,
    componentElement
  );
  moveDatasetPageIntoDropzoneArea();
});
