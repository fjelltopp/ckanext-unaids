import ReactDOM from 'react-dom';
import React from 'react';
import App from './src/App';

const componentElement =
  document.getElementById('BulkFileUploaderComponent');
const getAttr = key => {
  const val = componentElement.getAttribute(`data-${key}`);
  return ['None', ''].includes(val) ? null : val;
};
const requiredString = str => {
  console.assert(str.length);
  return str;
}
const
  lfsServer = requiredString(getAttr('lfsServer')),
  orgId = requiredString(getAttr('orgId')),
  datasetId = requiredString(getAttr('datasetId')),
  defaultFields = JSON.parse(requiredString(getAttr('defaultFields')));

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
