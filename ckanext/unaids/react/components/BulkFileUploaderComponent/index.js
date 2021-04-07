import ReactDOM from 'react-dom';
import React from 'react';
import App from './src/App';

const componentElement =
  document.getElementById('BulkFileUploaderComponent');
const getAttr = key => {
  const val = componentElement.getAttribute(`data-${key}`);
  return ['None', ''].includes(val) ? null : val;
};
const
  lfsServer = getAttr('lfsServer'),
  orgId = getAttr('orgId'),
  datasetId = getAttr('datasetId'),
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
}

loadCkan(() => {
  return (
    ReactDOM.render(
      <App {...{
        lfsServer, orgId, datasetId, defaultFields
      }} />,
      componentElement
    )
  )
});
