import React from "react";

global.React = React;

// mock ckan
global.ckan = {
  // i18n transations
  i18n: {
    _: str => str
  }
};

// mock frictionless-js
global.data = {
  // file upload
  open: uploadedFile => ({
    _descriptor: {
      name: uploadedFile.path,
      size: 1337
    },
    _computedHashes: {
      sha256: 'mockedSha256'
    }
  })
};

// mock jquery
global.$ = () => {
  // bootstrap modal actions
  return { modal: () => null }
}
