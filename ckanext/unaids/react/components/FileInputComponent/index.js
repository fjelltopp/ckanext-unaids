import ReactDOM from 'react-dom';
import React from 'react';
import App from './src/app';

const componentElement =
  document.getElementById('FileInputComponent');
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
  datasetId = requiredString(getAttr('datasetId'));

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
      lfsServer, orgId, datasetId,
      existingResourceData
    }} />,
    componentElement
  );
})
