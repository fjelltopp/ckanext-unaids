import ReactDOM from 'react-dom';
import React from 'react';
import App from './src/App';

const componentElement =
  document.getElementById('FileInputComponent');
const getAttr = key => {
  const val = componentElement.getAttribute(`data-${key}`);
  return ['None', ''].includes(val) ? null : val;
};
const
  maxResourceSize = parseInt(getAttr('maxResourceSize')),
  lfsServer = getAttr('lfsServer'),
  orgId = getAttr('orgId'),
  datasetId = getAttr('datasetId');

const existingResourceData = {
  urlType: getAttr('existingUrlType'),
  url: getAttr('existingUrl'),
  sha256: getAttr('existingSha256'),
  fileName: getAttr('existingFileName'),
  size: getAttr('existingSize'),
}

// wait for ckan.i18n to load
window.addEventListener('load', function () {
  ReactDOM.render(
    <App {...{
      maxResourceSize, lfsServer, orgId,
      datasetId, existingResourceData
    }} />,
    componentElement
  );
})
